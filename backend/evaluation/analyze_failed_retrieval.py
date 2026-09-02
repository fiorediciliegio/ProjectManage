
import argparse
import json
from pathlib import Path
from collections import Counter, defaultdict

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = BASE_DIR / 'rag_eval_dataset_official_v1_50.jsonl'
DEFAULT_DETAILS = BASE_DIR / 'reports' / 'rag_eval_details.jsonl'
DEFAULT_CHUNKS = BASE_DIR / 'chunks_export.jsonl'
DEFAULT_OUTPUT_DIR = BASE_DIR / 'reports'


def zh(text):
    return json.loads('"' + text + '"')


def load_jsonl(path):
    rows = []
    with Path(path).open('r', encoding='utf-8') as file:
        for line_no, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row['_line_no'] = line_no
            rows.append(row)
    return rows


def normalize_key(raw_key):
    if raw_key is None:
        return None
    if isinstance(raw_key, tuple) and len(raw_key) == 2:
        return (int(raw_key[0]), int(raw_key[1]))
    if isinstance(raw_key, list) and len(raw_key) == 2:
        return (int(raw_key[0]), int(raw_key[1]))
    return None


def normalize_key_list(raw_keys):
    keys = []
    for raw_key in raw_keys or []:
        key = normalize_key(raw_key)
        if key is not None:
            keys.append(key)
    return keys


def build_dataset_map(dataset_rows):
    return {row.get('id'): row for row in dataset_rows}


def build_chunk_map(chunk_rows):
    chunk_map = {}
    file_chunk_counter = Counter()
    for row in chunk_rows:
        file_id = row.get('file_id')
        chunk_index = row.get('chunk_index')
        if file_id is None or chunk_index is None:
            continue
        key = (int(file_id), int(chunk_index))
        chunk_map[key] = row
        file_chunk_counter[file_id] += 1
    return chunk_map, file_chunk_counter


def clean_text(text):
    lines = []
    for raw_line in str(text or '').splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(zh(r'\u8bf4\u660e\uff1a')):
            continue
        if line.startswith(zh(r'\u5185\u5bb9\u7c7b\u578b\uff1a')):
            continue
        lines.append(line)
    return '\n'.join(lines)


def snippet(text, max_chars=320):
    text = clean_text(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + '...'


def get_chunk_info(chunk_map, key):
    item = chunk_map.get(key)
    if not item:
        return {
            'file_id': key[0],
            'chunk_index': key[1],
            'missing': True,
            'file_name': '',
            'block_type': '',
            'page': None,
            'text': '',
            'snippet': '',
        }
    return {
        'file_id': item.get('file_id'),
        'file_name': item.get('file_name'),
        'chunk_index': item.get('chunk_index'),
        'page': item.get('page'),
        'sheet_name': item.get('sheet_name'),
        'block_type': item.get('block_type'),
        'title_path': item.get('title_path'),
        'text_length': len(clean_text(item.get('text') or '')),
        'text': clean_text(item.get('text') or ''),
        'snippet': snippet(item.get('text') or ''),
        'missing': False,
    }


def relevant_keys_from_sample(sample):
    keys = []
    for label in sample.get('relevant_chunks') or []:
        file_id = label.get('file_id')
        chunk_index = label.get('chunk_index')
        if file_id is not None and chunk_index is not None:
            keys.append((int(file_id), int(chunk_index)))
        for merged_index in label.get('merged_chunk_indexes') or []:
            if file_id is not None and merged_index is not None:
                keys.append((int(file_id), int(merged_index)))
    return sorted(set(keys))


def parse_retrieved_results(detail_row):
    results = []
    retrieved_chunks = detail_row.get('retrieved_chunks') or []
    retrieved_file_names = detail_row.get('retrieved_file_names') or []
    for rank, raw_key_group in enumerate(retrieved_chunks, start=1):
        keys = normalize_key_list(raw_key_group)
        file_name = retrieved_file_names[rank - 1] if rank - 1 < len(retrieved_file_names) else ''
        results.append({
            'rank': rank,
            'keys': keys,
            'file_name': file_name,
        })
    return results


def classify_failure(sample, relevant_infos, retrieved_infos):
    question_type = sample.get('question_type')
    relevant_block_types = {info.get('block_type') for info in relevant_infos if info}
    same_file_count = 0
    relevant_file_ids = {info.get('file_id') for info in relevant_infos if info}
    for result in retrieved_infos:
        for info in result.get('chunks') or []:
            if info.get('file_id') in relevant_file_ids:
                same_file_count += 1
                break

    if question_type == 'table_lookup' or any('table' in str(block_type or '') for block_type in relevant_block_types):
        return zh(r'\u8868\u683c\u7c7b\u95ee\u9898\uff1a\u4f18\u5148\u68c0\u67e5 ES \u5173\u952e\u8bcd\u53ec\u56de\u3001\u8868\u683c\u5207\u5206\u548c rerank \u662f\u5426\u5c06\u8868\u683c\u964d\u6743\u3002')
    if any('ocr' in str(block_type or '') for block_type in relevant_block_types):
        return zh(r'OCR \u7c7b\u95ee\u9898\uff1a\u4f18\u5148\u68c0\u67e5 OCR \u6587\u672c\u8d28\u91cf\u3001\u6362\u884c\u65ad\u53e5\u548c\u5173\u952e\u8bcd\u662f\u5426\u88ab\u5206\u6563\u3002')
    if same_file_count > 0:
        return zh(r'\u540c\u6587\u4ef6\u672a\u547d\u4e2d\u6807\u6ce8 chunk\uff1a\u53ef\u80fd\u662f\u5207\u7247\u8fc7\u7ec6\u3001\u6807\u6ce8\u8fc7\u7a84\u6216 rerank \u6392\u5e8f\u504f\u79fb\u3002')
    return zh(r'\u8de8\u6587\u4ef6\u53ec\u56de\u9519\u8bef\uff1a\u4f18\u5148\u68c0\u67e5\u67e5\u8be2\u6539\u5199\u3001\u5173\u952e\u8bcd\u68c0\u7d22\u548c\u5019\u9009\u96c6\u5927\u5c0f\u3002')


def analyze(args):
    dataset_rows = load_jsonl(args.dataset)
    detail_rows = load_jsonl(args.details)
    chunk_rows = load_jsonl(args.chunks)

    dataset_map = build_dataset_map(dataset_rows)
    chunk_map, _ = build_chunk_map(chunk_rows)

    metric_name = f'hit_rate@{args.k}'
    failed = []
    for detail in detail_rows:
        if float(detail.get(metric_name, 0.0)) == 0.0:
            sample_id = detail.get('id')
            sample = dataset_map.get(sample_id, {})
            relevant_keys = relevant_keys_from_sample(sample)
            relevant_infos = [get_chunk_info(chunk_map, key) for key in relevant_keys]

            retrieved_results = parse_retrieved_results(detail)[:args.k]
            retrieved_infos = []
            for result in retrieved_results:
                chunk_infos = [get_chunk_info(chunk_map, key) for key in result.get('keys') or []]
                retrieved_infos.append({
                    'rank': result['rank'],
                    'file_name': result.get('file_name'),
                    'keys': result.get('keys'),
                    'chunks': chunk_infos,
                })

            failed.append({
                'id': sample_id,
                'line_no': detail.get('_line_no'),
                'question': sample.get('question') or detail.get('question'),
                'question_type': sample.get('question_type') or detail.get('question_type'),
                'difficulty': sample.get('difficulty') or detail.get('difficulty'),
                'expected_answer': sample.get('expected_answer'),
                'relevant_chunks': relevant_infos,
                'retrieved_top_k': retrieved_infos,
                'diagnosis_hint': classify_failure(sample, relevant_infos, retrieved_infos),
            })

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_jsonl = output_dir / f'failed_retrieval_hit_rate_at_{args.k}.jsonl'
    output_md = output_dir / f'failed_retrieval_hit_rate_at_{args.k}.md'

    with output_jsonl.open('w', encoding='utf-8', newline='\n') as file:
        for item in failed:
            file.write(json.dumps(item, ensure_ascii=False) + '\n')

    question_type_counter = Counter(item.get('question_type') for item in failed)
    block_type_counter = Counter()
    for item in failed:
        for info in item.get('relevant_chunks') or []:
            block_type_counter[info.get('block_type')] += 1

    lines = []
    lines.append('# Failed Retrieval Analysis')
    lines.append('')
    lines.append(f'- Metric: hit_rate@{args.k} = 0')
    lines.append(f'- Failed samples: {len(failed)}')
    lines.append(f'- Detail source: {args.details}')
    lines.append('')
    lines.append('## Failure Distribution')
    lines.append('')
    lines.append('### By Question Type')
    lines.append('')
    for key, value in question_type_counter.most_common():
        lines.append(f'- {key}: {value}')
    lines.append('')
    lines.append('### By Gold Chunk Block Type')
    lines.append('')
    for key, value in block_type_counter.most_common():
        lines.append(f'- {key}: {value}')
    lines.append('')
    lines.append('## Failed Samples')
    lines.append('')

    for item in failed:
        lines.append(f'### {item["id"]} | {item.get("question_type")} | {item.get("difficulty")}')
        lines.append('')
        lines.append(f'**Question:** {item.get("question")}')
        lines.append('')
        lines.append(f'**Diagnosis hint:** {item.get("diagnosis_hint")}')
        lines.append('')
        lines.append('**Gold relevant chunks:**')
        lines.append('')
        for info in item.get('relevant_chunks') or []:
            lines.append(f'- file_id={info.get("file_id")}, chunk={info.get("chunk_index")}, page={info.get("page")}, block={info.get("block_type")}, file={info.get("file_name")}')
            lines.append('')
            lines.append('```text')
            lines.append(info.get('snippet') or '')
            lines.append('```')
            lines.append('')
        lines.append(f'**Actual Top {args.k}:**')
        lines.append('')
        for result in item.get('retrieved_top_k') or []:
            lines.append(f'- Rank {result.get("rank")}: {result.get("file_name")}')
            for info in result.get('chunks') or []:
                lines.append(f'  - file_id={info.get("file_id")}, chunk={info.get("chunk_index")}, page={info.get("page")}, block={info.get("block_type")}')
                lines.append('')
                lines.append('```text')
                lines.append(info.get('snippet') or '')
                lines.append('```')
                lines.append('')
        lines.append('---')
        lines.append('')

    output_md.write_text('\n'.join(lines), encoding='utf-8', newline='\n')

    print(zh(r'\u5206\u6790\u5b8c\u6210'))
    print(f'failed_count={len(failed)}')
    print(f'markdown={output_md}')
    print(f'jsonl={output_jsonl}')
    print('question_type_distribution=', dict(question_type_counter))
    print('gold_block_type_distribution=', dict(block_type_counter))


def parse_args():
    parser = argparse.ArgumentParser(description='Analyze failed RAG retrieval samples from evaluation details.')
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--details', type=Path, default=DEFAULT_DETAILS)
    parser.add_argument('--chunks', type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--k', type=int, default=8)
    return parser.parse_args()


if __name__ == '__main__':
    analyze(parse_args())
