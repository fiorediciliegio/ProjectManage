import argparse
import csv
import json
import math
import os
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

DEFAULT_DATASET = Path(__file__).resolve().parent / 'rag_eval_dataset_official_v2_clean_500.jsonl'
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / 'reports' / 'ragas_official_v2_clean_500'
DEFAULT_K_VALUES = [1, 3, 5, 8]
DEFAULT_RAGAS_METRICS = ['faithfulness', 'answer_relevancy', 'context_recall']


def load_dataset(dataset_path):
    rows = []
    with Path(dataset_path).open('r', encoding='utf-8') as file:
        for line_no, line in enumerate(file, start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            item['_line_no'] = line_no
            rows.append(item)
    return rows


def limit_dataset(rows, sample_limit=None):
    if sample_limit is None or sample_limit <= 0:
        return rows
    return rows[:sample_limit]


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


def prefix_metrics(metrics, prefix):
    return {f'{prefix}_{key}': value for key, value in metrics.items()}


def average_metric(rows, metric_name):
    values = [row[metric_name] for row in rows if isinstance(row.get(metric_name), (int, float))]
    return statistics.mean(values) if values else 0.0


def group_average(rows, group_key, metric_names):
    groups = defaultdict(list)
    for row in rows:
        groups[row.get(group_key, 'unknown')].append(row)

    grouped = {}
    for group, items in groups.items():
        grouped[group] = {
            metric: average_metric(items, metric)
            for metric in metric_names
        }
        grouped[group]['count'] = len(items)
    return grouped


def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Projectmanagement.settings')
    import django

    django.setup()


def collect_answer(question, project_id, limit):
    from app01.services.langchain_rag_service import answer_question_with_rag

    answer_parts = []
    sources = []
    error = ''
    try:
        for event in answer_question_with_rag(question=question, project_id=project_id, limit=limit):
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


def collect_retrieval(question, project_id, max_k):
    from app01.services.langchain_rag_service import hybrid_search_file_chunks
    from app01.services.rag.compression import contextual_compress_search_results
    from app01.services.rag.context import expand_search_results_with_neighbors, pack_rag_context

    started_at = time.perf_counter()
    candidates = hybrid_search_file_chunks(question=question, project_id=project_id, final_limit=max_k)
    retrieval_ms = (time.perf_counter() - started_at) * 1000

    context_started_at = time.perf_counter()
    context_candidates = expand_search_results_with_neighbors(
        candidates,
        neighbor_size=1,
        allowed_extensions={'.pdf'},
    )
    context_candidates = contextual_compress_search_results(context_candidates, question=question)
    _, packed_results = pack_rag_context(context_candidates, question=question)
    context_ms = (time.perf_counter() - context_started_at) * 1000

    return {
        'candidates': candidates,
        'contexts': packed_results,
        'retrieval_ms': retrieval_ms,
        'context_ms': context_ms,
    }


def safe_text(item):
    return str(item.get('text') or '').strip()


def build_ragas_row(sample, detail):
    return {
        'user_input': sample.get('question') or '',
        'response': detail.get('answer') or '',
        'retrieved_contexts': detail.get('retrieved_contexts') or [],
        'reference': sample.get('expected_answer') or sample.get('reference') or '',
    }


def metric_names_for_k(k_values):
    names = []
    for prefix in ('candidate', 'context'):
        for k in k_values:
            names.extend([
                f'{prefix}_recall@{k}',
                f'{prefix}_precision@{k}',
                f'{prefix}_hit_rate@{k}',
                f'{prefix}_ndcg@{k}',
            ])
    return names


def ragas_available_metrics(metric_names):
    from ragas.metrics import answer_correctness, answer_relevancy, context_precision, context_recall, faithfulness

    registry = {
        'faithfulness': faithfulness,
        'answer_relevancy': answer_relevancy,
        'context_precision': context_precision,
        'context_recall': context_recall,
        'answer_correctness': answer_correctness,
    }
    return [registry[name] for name in metric_names if name in registry]


def build_ragas_llm_kwargs(settings):
    return {
        'model': settings.RAG_CHAT_MODEL,
        'api_key': settings.RAG_CHAT_API_KEY,
        'base_url': settings.RAG_CHAT_BASE_URL,
        'temperature': 0,
        'max_tokens': getattr(settings, 'RAGAS_EVAL_MAX_TOKENS', 4096),
        'timeout': getattr(settings, 'RAG_CHAT_TIMEOUT', 45),
        'n': getattr(settings, 'RAGAS_EVAL_N', 1),
        'extra_body': {
            'enable_thinking': getattr(settings, 'RAGAS_EVAL_ENABLE_THINKING', False),
        },
    }


def build_ragas_run_config_kwargs(settings):
    return {
        'timeout': getattr(settings, 'RAGAS_EVAL_TIMEOUT', 240),
        'max_retries': getattr(settings, 'RAGAS_EVAL_MAX_RETRIES', 1),
    }


def run_ragas_evaluation(ragas_rows, metric_names, batch_size):
    from datasets import Dataset
    import httpx
    from langchain_openai import ChatOpenAI
    from ragas import evaluate as ragas_evaluate
    from ragas.run_config import RunConfig

    from app01.services.rag.vector_store import DashScopeTextEmbeddings
    from django.conf import settings

    if not ragas_rows:
        return {}, []
    if not getattr(settings, 'RAG_CHAT_API_KEY', ''):
        raise RuntimeError('RAG_CHAT_API_KEY is required for Ragas LLM metrics')

    llm = ChatOpenAI(
        **build_ragas_llm_kwargs(settings),
        http_client=httpx.Client(trust_env=False),
        http_async_client=httpx.AsyncClient(trust_env=False),
    )
    embeddings = DashScopeTextEmbeddings()
    metrics = ragas_available_metrics(metric_names)
    dataset = Dataset.from_list(ragas_rows)

    result = ragas_evaluate(
        dataset,
        metrics=metrics,
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=False,
        show_progress=True,
        batch_size=batch_size,
        run_config=RunConfig(**build_ragas_run_config_kwargs(settings)),
    )

    rows = []
    if hasattr(result, 'to_pandas'):
        rows = result.to_pandas().to_dict(orient='records')
    summary = {}
    try:
        summary = dict(result)
    except Exception:
        summary = {
            name: average_metric(rows, name)
            for name in metric_names
        }
    return summary, rows


def write_jsonl(path, rows):
    with Path(path).open('w', encoding='utf-8', newline='\n') as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + '\n')


def write_csv(path, rows, fieldnames):
    with Path(path).open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_summary_markdown(path, summary, detail_path, csv_path):
    lines = [
        '# RAGAS RAG Evaluation Summary',
        '',
        f'- Dataset: {summary["dataset"]}',
        f'- Samples: {summary["sample_count"]}',
        f'- Full dataset samples: {summary["full_dataset_count"]}',
        f'- Generation enabled: {summary["with_generation"]}',
        f'- Ragas enabled: {summary["with_ragas"]}',
        f'- K values: {summary["k_values"]}',
        f'- Ragas metrics: {summary["ragas_metric_names"]}',
        '',
        '## Overall Retrieval Metrics',
        '',
    ]
    for metric, value in summary['overall'].items():
        lines.append(f'- {metric}: {value:.4f}' if isinstance(value, (int, float)) else f'- {metric}: {value}')

    if summary.get('ragas_overall'):
        lines.extend(['', '## Overall Ragas Metrics', ''])
        for metric, value in summary['ragas_overall'].items():
            lines.append(f'- {metric}: {value:.4f}' if isinstance(value, (int, float)) else f'- {metric}: {value}')

    lines.extend(['', '## By Question Type', ''])
    for group, values in summary['by_question_type'].items():
        metric_text = ', '.join(
            f'{metric}={value:.4f}'
            for metric, value in values.items()
            if metric != 'count' and isinstance(value, (int, float))
        )
        lines.append(f'- {group} (n={values["count"]}): {metric_text}')

    if summary.get('error_count'):
        lines.extend(['', '## Errors', ''])
        lines.append(f'- Error count: {summary["error_count"]}')

    lines.extend([
        '',
        '## Output Files',
        '',
        f'- Detail JSONL: {detail_path}',
        f'- Detail CSV: {csv_path}',
        f'- Summary JSON: {path.with_suffix(".json")}',
    ])
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def evaluate(args):
    setup_django()

    full_dataset = load_dataset(args.dataset)
    dataset = limit_dataset(full_dataset, args.sample_limit)
    k_values = sorted(set(args.k_values))
    max_k = max(k_values)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    retrieval_metric_names = metric_names_for_k(k_values)
    detail_rows = []
    ragas_rows = []
    errors = []

    for index, sample in enumerate(dataset, start=1):
        sample_id = sample.get('id') or f'row_{index}'
        question = sample.get('question') or ''
        project_id = sample.get('metadata', {}).get('project_id')
        relevant = relevant_keys(sample)
        print(f'[{index}/{len(dataset)}] {sample_id} retrieval...')

        row_started_at = time.perf_counter()
        try:
            retrieval = collect_retrieval(question, project_id, max_k)
            candidates = retrieval['candidates']
            contexts = retrieval['contexts']
            candidate_metrics = prefix_metrics(
                retrieval_metrics_for_sample(candidates, relevant, k_values),
                'candidate',
            )
            context_metrics = prefix_metrics(
                retrieval_metrics_for_sample(contexts, relevant, k_values),
                'context',
            )
            error = ''
        except Exception as exc:
            candidates = []
            contexts = []
            candidate_metrics = prefix_metrics(retrieval_metrics_for_sample([], relevant, k_values), 'candidate')
            context_metrics = prefix_metrics(retrieval_metrics_for_sample([], relevant, k_values), 'context')
            retrieval = {'retrieval_ms': 0, 'context_ms': 0}
            error = str(exc)
            errors.append({'id': sample_id, 'stage': 'retrieval', 'error': error})

        answer = ''
        sources = []
        generation_error = ''
        if args.with_generation and not error:
            print(f'[{index}/{len(dataset)}] {sample_id} generation...')
            answer, sources, generation_error = collect_answer(question, project_id, max_k)
            if generation_error:
                errors.append({'id': sample_id, 'stage': 'generation', 'error': generation_error})

        total_ms = (time.perf_counter() - row_started_at) * 1000
        detail = {
            'id': sample_id,
            'question_type': sample.get('question_type'),
            'difficulty': sample.get('difficulty'),
            'question': question,
            'project_id': project_id,
            'relevant_chunks': sorted(list(relevant)),
            'candidate_chunks': [sorted(list(result_keys(item))) for item in candidates],
            'context_chunks': [sorted(list(result_keys(item))) for item in contexts],
            'candidate_file_names': [item.get('file_name') for item in candidates],
            'context_file_names': [item.get('file_name') for item in contexts],
            'retrieved_contexts': [safe_text(item) for item in contexts],
            'answer': answer,
            'generation_error': generation_error,
            'retrieval_error': error,
            'retrieval_ms': round(retrieval.get('retrieval_ms', 0), 2),
            'context_ms': round(retrieval.get('context_ms', 0), 2),
            'total_ms': round(total_ms, 2),
            **candidate_metrics,
            **context_metrics,
        }
        detail_rows.append(detail)

        if args.with_ragas and args.with_generation and not error and not generation_error:
            ragas_rows.append(build_ragas_row(sample, detail))

    ragas_summary = {}
    ragas_detail_rows = []
    if args.with_ragas:
        if not args.with_generation:
            errors.append({'id': 'global', 'stage': 'ragas', 'error': '--with-ragas requires --with-generation'})
        elif ragas_rows:
            print(f'Running Ragas metrics for {len(ragas_rows)} samples...')
            try:
                ragas_summary, ragas_detail_rows = run_ragas_evaluation(
                    ragas_rows=ragas_rows,
                    metric_names=args.ragas_metrics,
                    batch_size=args.ragas_batch_size,
                )
            except Exception as exc:
                errors.append({'id': 'global', 'stage': 'ragas', 'error': str(exc)})

    if ragas_detail_rows:
        ragas_metrics = [
            key
            for key in args.ragas_metrics
            if any(key in row for row in ragas_detail_rows)
        ]
        detail_index = 0
        for row in detail_rows:
            if row.get('answer') and not row.get('generation_error') and detail_index < len(ragas_detail_rows):
                for metric in ragas_metrics:
                    row[f'ragas_{metric}'] = ragas_detail_rows[detail_index].get(metric)
                detail_index += 1

    active_ragas_metric_names = [
        f'ragas_{name}'
        for name in args.ragas_metrics
        if any(f'ragas_{name}' in row for row in detail_rows)
    ]
    all_metric_names = retrieval_metric_names + active_ragas_metric_names

    summary = {
        'dataset': str(args.dataset),
        'full_dataset_count': len(full_dataset),
        'sample_count': len(dataset),
        'with_generation': args.with_generation,
        'with_ragas': args.with_ragas,
        'k_values': k_values,
        'ragas_metric_names': args.ragas_metrics if args.with_ragas else [],
        'overall': {metric: average_metric(detail_rows, metric) for metric in retrieval_metric_names},
        'ragas_overall': {
            metric.replace('ragas_', ''): average_metric(detail_rows, metric)
            for metric in active_ragas_metric_names
        } or ragas_summary,
        'by_question_type': group_average(detail_rows, 'question_type', all_metric_names),
        'by_difficulty': group_average(detail_rows, 'difficulty', all_metric_names),
        'error_count': len(errors),
        'errors': errors,
    }

    detail_jsonl = output_dir / 'ragas_eval_details.jsonl'
    detail_csv = output_dir / 'ragas_eval_details.csv'
    summary_json = output_dir / 'ragas_eval_summary.json'
    summary_md = output_dir / 'ragas_eval_summary.md'
    ragas_input_jsonl = output_dir / 'ragas_input.jsonl'

    write_jsonl(detail_jsonl, detail_rows)
    write_jsonl(ragas_input_jsonl, ragas_rows)
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    csv_fields = [
        'id', 'question_type', 'difficulty', 'question',
        *all_metric_names,
        'retrieval_ms', 'context_ms', 'total_ms', 'retrieval_error', 'generation_error',
    ]
    write_csv(detail_csv, detail_rows, csv_fields)
    write_summary_markdown(summary_md, summary, detail_jsonl, detail_csv)

    print('\nEvaluation finished.')
    print(f'Summary: {summary_md}')
    print(f'Details: {detail_jsonl}')
    print(json.dumps({'overall': summary['overall'], 'ragas_overall': summary['ragas_overall'], 'errors': errors}, ensure_ascii=False, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate ProjectManage RAG with retrieval metrics and optional Ragas metrics.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--sample-limit', type=int, default=10, help='Limit samples to control API cost. Use 0 for the full dataset.')
    parser.add_argument('--k-values', type=int, nargs='+', default=DEFAULT_K_VALUES)
    parser.add_argument('--with-generation', action='store_true', help='Run the real RAG answer generation chain.')
    parser.add_argument('--with-ragas', action='store_true', help='Run Ragas metrics. Requires --with-generation.')
    parser.add_argument(
        '--ragas-metrics',
        nargs='+',
        default=DEFAULT_RAGAS_METRICS,
    )
    parser.add_argument('--ragas-batch-size', type=int, default=2)
    return parser.parse_args()


if __name__ == '__main__':
    evaluate(parse_args())
