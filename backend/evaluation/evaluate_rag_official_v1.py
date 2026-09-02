
import argparse
import csv
import json
import math
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Make this script runnable from backend/evaluation or backend root.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Projectmanagement.settings')

import django

django.setup()

from app01.services.langchain_rag_service import answer_question_with_rag, hybrid_search_file_chunks

DEFAULT_DATASET = Path(__file__).resolve().parent / 'rag_eval_dataset_official_v1_50.jsonl'
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / 'reports'
DEFAULT_K_VALUES = [1, 3, 5, 8]


def load_dataset(dataset_path):
    rows = []
    with Path(dataset_path).open('r', encoding='utf-8') as file:
        for line_no, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            item['_line_no'] = line_no
            rows.append(item)
    return rows


def chunk_keys_from_label(label):
    keys = set()
    file_id = label.get('file_id')
    chunk_index = label.get('chunk_index')
    if file_id is not None and chunk_index is not None:
        keys.add((int(file_id), int(chunk_index)))
    for merged_index in label.get('merged_chunk_indexes') or []:
        if file_id is not None and merged_index is not None:
            keys.add((int(file_id), int(merged_index)))
    return keys


def relevant_keys(sample):
    keys = set()
    for label in sample.get('relevant_chunks') or []:
        keys.update(chunk_keys_from_label(label))
    return keys


def result_keys(result):
    keys = set()
    file_id = result.get('file_id')
    chunk_index = result.get('chunk_index')
    if file_id is not None and chunk_index is not None:
        keys.add((int(file_id), int(chunk_index)))
    for merged_index in result.get('merged_chunk_indexes') or []:
        if file_id is not None and merged_index is not None:
            keys.add((int(file_id), int(merged_index)))
    return keys


def is_relevant_result(result, relevant):
    return bool(result_keys(result) & relevant)


def dcg(binary_relevances):
    score = 0.0
    for rank, relevance in enumerate(binary_relevances, start=1):
        if relevance:
            score += 1.0 / math.log2(rank + 1)
    return score


def ndcg_at_k(results, relevant, k):
    binary = [1 if is_relevant_result(item, relevant) else 0 for item in results[:k]]
    actual_dcg = dcg(binary)
    ideal_hits = min(len(relevant), k)
    ideal_dcg = dcg([1] * ideal_hits)
    if ideal_dcg == 0:
        return 0.0
    return actual_dcg / ideal_dcg


def retrieval_metrics_for_sample(results, relevant, k_values):
    metrics = {}
    for k in k_values:
        top_k = results[:k]
        hit_count = sum(1 for item in top_k if is_relevant_result(item, relevant))
        metrics[f'recall@{k}'] = hit_count / len(relevant) if relevant else 0.0
        metrics[f'precision@{k}'] = hit_count / k if k else 0.0
        metrics[f'hit_rate@{k}'] = 1.0 if hit_count > 0 else 0.0
        metrics[f'ndcg@{k}'] = ndcg_at_k(results, relevant, k)
    return metrics


def tokenize_for_eval(text):
    text = str(text or '').lower()
    return re.findall(r'[a-z][a-z0-9_\-/.]*|[\u4e00-\u9fff]{2,}|\d+(?:\.\d+)?', text)


def char_bigrams(text):
    compact = re.sub(r'\s+', '', str(text or ''))
    if len(compact) <= 1:
        return set(compact) if compact else set()
    return {compact[index:index + 2] for index in range(len(compact) - 1)}


def f1_score(predicted_items, gold_items):
    predicted = set(predicted_items)
    gold = set(gold_items)
    if not predicted and not gold:
        return 1.0
    if not predicted or not gold:
        return 0.0
    overlap = len(predicted & gold)
    precision = overlap / len(predicted)
    recall = overlap / len(gold)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def answer_relevance_score(answer, expected_answer):
    # Measures whether the generated answer says the same important content as the reference answer.
    token_f1 = f1_score(tokenize_for_eval(answer), tokenize_for_eval(expected_answer))
    bigram_f1 = f1_score(char_bigrams(answer), char_bigrams(expected_answer))
    return 0.45 * token_f1 + 0.55 * bigram_f1


def context_relevance_score(retrieval_metrics, max_k):
    # Uses retrieval recall and NDCG as a proxy for whether the model received useful context.
    recall = retrieval_metrics.get(f'recall@{max_k}', 0.0)
    ndcg = retrieval_metrics.get(f'ndcg@{max_k}', 0.0)
    return 0.6 * recall + 0.4 * ndcg


def extract_answer_citation_indexes(answer):
    indexes = set()
    for value in re.findall(r'\[\s*??\s*(\d+)\s*\]', str(answer or '')):
        try:
            indexes.add(int(value))
        except ValueError:
            pass
    return indexes


def citation_accuracy_score(sources, relevant):
    if not sources:
        return 0.0
    correct = 0
    for source in sources:
        if result_keys(source) & relevant:
            correct += 1
    return correct / len(sources)


def faithfulness_score(answer, expected_answer, cited_sources, relevant):
    # A conservative offline proxy: answers are more faithful when they are close to the reference
    # and cite sources that match the gold relevant chunks.
    relevance = answer_relevance_score(answer, expected_answer)
    citation = citation_accuracy_score(cited_sources, relevant) if cited_sources else 0.0
    if '???????????' in str(answer):
        return 1.0 if not expected_answer else 0.0
    if cited_sources:
        return 0.7 * relevance + 0.3 * citation
    return 0.7 * relevance


def collect_stream_answer(question, project_id, limit, history=None):
    answer_parts = []
    sources = []
    error = None
    try:
        for event in answer_question_with_rag(
            question=question,
            project_id=project_id,
            limit=limit,
            history=history,
        ):
            event_type = event.get('type')
            if event_type == 'delta':
                answer_parts.append(event.get('content') or '')
            elif event_type == 'done':
                sources = event.get('sources') or []
            elif event_type == 'error':
                error = event.get('message') or str(event)
    except Exception as exc:
        error = str(exc)
    return ''.join(answer_parts), sources, error


def average_metric(rows, metric_name):
    values = [row[metric_name] for row in rows if metric_name in row]
    return statistics.mean(values) if values else 0.0


def group_average(rows, group_key, metric_names):
    groups = defaultdict(list)
    for row in rows:
        groups[row.get(group_key, 'unknown')].append(row)
    result = {}
    for group, items in groups.items():
        result[group] = {metric: average_metric(items, metric) for metric in metric_names}
        result[group]['count'] = len(items)
    return result


def evaluate(args):
    dataset = load_dataset(args.dataset)
    k_values = sorted(set(args.k_values))
    max_k = max(k_values)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    detail_rows = []
    retrieval_metric_names = []
    for k in k_values:
        retrieval_metric_names.extend([f'recall@{k}', f'precision@{k}', f'hit_rate@{k}', f'ndcg@{k}'])

    for index, sample in enumerate(dataset, start=1):
        sample_id = sample.get('id') or f'row_{index}'
        question = sample.get('question') or ''
        project_id = sample.get('metadata', {}).get('project_id')
        expected_answer = sample.get('expected_answer') or ''
        relevant = relevant_keys(sample)

        print(f'[{index}/{len(dataset)}] {sample_id} retrieval...')
        results = hybrid_search_file_chunks(
            question=question,
            project_id=project_id,
            final_limit=max_k,
        )
        retrieval_metrics = retrieval_metrics_for_sample(results, relevant, k_values)

        row = {
            'id': sample_id,
            'question_type': sample.get('question_type'),
            'difficulty': sample.get('difficulty'),
            'question': question,
            'project_id': project_id,
            'relevant_chunks': sorted(list(relevant)),
            'retrieved_chunks': [sorted(list(result_keys(item))) for item in results],
            'retrieved_file_names': [item.get('file_name') for item in results],
            **retrieval_metrics,
        }

        if args.with_generation:
            print(f'[{index}/{len(dataset)}] {sample_id} generation...')
            answer, sources, error = collect_stream_answer(
                question=question,
                project_id=project_id,
                limit=max_k,
                history=None,
            )
            row['answer'] = answer
            row['generation_error'] = error or ''
            row['answer_relevance'] = answer_relevance_score(answer, expected_answer) if not error else 0.0
            row['context_relevance'] = context_relevance_score(retrieval_metrics, max_k)
            row['citation_accuracy'] = citation_accuracy_score(sources, relevant) if not error else 0.0
            row['faithfulness'] = faithfulness_score(answer, expected_answer, sources, relevant) if not error else 0.0
            row['cited_sources'] = sources
            row['cited_source_indexes_in_answer'] = sorted(extract_answer_citation_indexes(answer))

        detail_rows.append(row)

    generation_metric_names = ['faithfulness', 'answer_relevance', 'context_relevance', 'citation_accuracy']
    active_generation_metrics = generation_metric_names if args.with_generation else []
    all_metric_names = retrieval_metric_names + active_generation_metrics

    summary = {
        'dataset': str(args.dataset),
        'sample_count': len(dataset),
        'with_generation': args.with_generation,
        'k_values': k_values,
        'overall': {metric: average_metric(detail_rows, metric) for metric in all_metric_names},
        'by_question_type': group_average(detail_rows, 'question_type', all_metric_names),
        'by_difficulty': group_average(detail_rows, 'difficulty', all_metric_names),
    }

    detail_jsonl = output_dir / 'rag_eval_details.jsonl'
    summary_json = output_dir / 'rag_eval_summary.json'
    summary_md = output_dir / 'rag_eval_summary.md'
    detail_csv = output_dir / 'rag_eval_details.csv'

    with detail_jsonl.open('w', encoding='utf-8', newline='\n') as file:
        for row in detail_rows:
            file.write(json.dumps(row, ensure_ascii=False) + '\n')

    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    csv_fields = ['id', 'question_type', 'difficulty', 'question'] + all_metric_names + ['generation_error']
    with detail_csv.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=csv_fields, extrasaction='ignore')
        writer.writeheader()
        for row in detail_rows:
            writer.writerow(row)

    lines = []
    lines.append('# RAG Evaluation Summary')
    lines.append('')
    lines.append(f'- Dataset: {args.dataset}')
    lines.append(f'- Samples: {len(dataset)}')
    lines.append(f'- With generation: {args.with_generation}')
    lines.append(f'- K values: {k_values}')
    lines.append('')
    lines.append('## Overall Metrics')
    lines.append('')
    for metric, value in summary['overall'].items():
        lines.append(f'- {metric}: {value:.4f}')
    lines.append('')
    lines.append('## By Question Type')
    lines.append('')
    for group, values in summary['by_question_type'].items():
        metric_text = ', '.join(
            f'{metric}={value:.4f}'
            for metric, value in values.items()
            if metric != 'count'
        )
        lines.append(f'- {group} (n={values["count"]}): {metric_text}')
    lines.append('')
    lines.append('## Output Files')
    lines.append('')
    lines.append(f'- Detail JSONL: {detail_jsonl}')
    lines.append(f'- Detail CSV: {detail_csv}')
    lines.append(f'- Summary JSON: {summary_json}')
    summary_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print('\nEvaluation complete.')
    print(f'Summary: {summary_md}')
    print(f'Details: {detail_jsonl}')
    print(json.dumps(summary['overall'], ensure_ascii=False, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate ProjectManage RAG with the official dataset.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--k-values', type=int, nargs='+', default=DEFAULT_K_VALUES)
    parser.add_argument('--with-generation', action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    evaluate(parse_args())
