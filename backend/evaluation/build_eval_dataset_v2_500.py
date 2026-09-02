
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHUNKS_PATH = BASE_DIR / 'chunks_export.jsonl'
OUT_JSONL = BASE_DIR / 'rag_eval_dataset_v2_500.jsonl'
OUT_JSON = BASE_DIR / 'rag_eval_dataset_v2_500.json'
OUT_SUMMARY = BASE_DIR / 'rag_eval_dataset_v2_500_summary.md'
OUT_CANDIDATES = BASE_DIR / 'selected_candidate_chunks_v2_500.jsonl'

TARGET_COUNT = 500
MAX_PER_FILE = 45
MAX_RELEVANT_CHUNKS = 5
NEIGHBOR_WINDOW = 2
LEXICAL_RELATED_LIMIT = 2

QUESTION_TYPE_QUOTAS = {
    'safety_management': 120,
    'table_lookup': 120,
    'quality_supervision': 100,
    'fact_lookup': 80,
    'cost_contract': 40,
    'schedule_plan': 40,
}

ZH_STOPWORDS = {
    '\u8bf4\u660e', '\u5185\u5bb9', '\u7c7b\u578b', '\u6587\u4ef6', '\u9879\u76ee', '\u5de5\u7a0b',
    '\u4e00\u3001', '\u4e8c\u3001', '\u4e09\u3001', '\u56db\u3001', '\u4e94\u3001', '\u516d\u3001',
    '\u7b2c', '\u9875', '\u8d44\u6599', '\u60c5\u51b5', '\u76f8\u5173', '\u8981\u6c42', '\u8fdb\u884c',
    '\u5e94\u5f53', '\u6309\u7167', '\u4ee5\u4e0b', '\u4ee5\u4e0a', '\u4e2d', '\u7684', '\u548c',
    '\u4ee5\u53ca', '\u5bf9', '\u4e0e', '\u5728', '\u4e3a', '\u6309', '\u5c06', '\u672c', '\u5404',
}

TYPE_KEYWORDS = {
    'safety_management': [
        '\u5b89\u5168', '\u9690\u60a3', '\u6d88\u9632', '\u811a\u624b\u67b6', '\u6a21\u677f\u652f\u6491',
        '\u5371\u5927', '\u4e34\u65f6\u7528\u7535', '\u6574\u6539', '\u9632\u62a4', '\u8d77\u91cd',
        '\u5b89\u5168\u7ba1\u7406', '\u6587\u660e\u65bd\u5de5',
    ],
    'quality_supervision': [
        '\u8d28\u91cf', '\u9a8c\u6536', '\u76d1\u7406', '\u68c0\u67e5', '\u68c0\u9a8c',
        '\u68c0\u6d4b', '\u8bd5\u9a8c', '\u6df7\u51dd\u571f', '\u94a2\u7b4b', '\u57fa\u5751',
        '\u8d28\u91cf\u95ee\u9898', '\u5de5\u7a0b\u5b9e\u4f53',
    ],
    'cost_contract': [
        '\u5408\u540c', '\u6295\u6807', '\u62db\u6807', '\u9020\u4ef7', '\u9884\u7b97', '\u8d39\u7528',
        '\u4ef7\u6b3e', '\u652f\u4ed8', '\u7ed3\u7b97', '\u627f\u5305', '\u62a5\u4ef7',
    ],
    'schedule_plan': [
        '\u8fdb\u5ea6', '\u5de5\u671f', '\u8ba1\u5212', '\u8282\u70b9', '\u5f00\u5de5', '\u7ae3\u5de5',
        '\u65bd\u5de5\u7ec4\u7ec7', '\u603b\u8fdb\u5ea6', '\u65f6\u95f4',
    ],
}


BAD_TOPIC_TERMS = {
    '\u8be6\u89c1\u9644\u5f55', '\u4e0b\u5217\u6587\u4ef6', '\u672c\u6587\u4ef6', '\u672c\u9879\u76ee',
    '\u9002\u7528\u4e8e', '\u89c4\u8303\u6027\u5f15\u7528', '\u672f\u8bed\u548c\u5b9a\u4e49',
    '\u6ca1\u6709\u627e\u5230', '\u4e3b\u8981\u5185\u5bb9', '\u5173\u952e\u4fe1\u606f',
}

PREFERRED_TOPIC_TERMS = {
    'safety_management': [
        '\u5b89\u5168\u7ba1\u7406\u53f0\u8d26', '\u5e73\u5b89\u5de5\u5730', '\u5b89\u5168\u751f\u4ea7',
        '\u5371\u5927\u5de5\u7a0b', '\u6a21\u677f\u652f\u6491', '\u811a\u624b\u67b6', '\u4e34\u65f6\u7528\u7535',
        '\u6d88\u9632\u5b89\u5168', '\u8d77\u91cd\u673a\u68b0', '\u5b89\u5168\u9690\u60a3', '\u6574\u6539\u901a\u77e5',
    ],
    'quality_supervision': [
        '\u8d28\u91cf\u68c0\u67e5', '\u8d28\u91cf\u9a8c\u6536', '\u5de5\u7a0b\u5b9e\u4f53\u8d28\u91cf',
        '\u65bd\u5de5\u8d28\u91cf', '\u8d28\u91cf\u7ba1\u63a7', '\u81ea\u68c0', '\u4e92\u68c0', '\u4ea4\u63a5\u68c0',
        '\u68c0\u6d4b\u62a5\u544a', '\u6df7\u51dd\u571f', '\u94a2\u7b4b', '\u57fa\u5751\u652f\u62a4',
    ],
    'cost_contract': [
        '\u5408\u540c\u4ef7\u6b3e', '\u6295\u6807\u62a5\u4ef7', '\u5de5\u7a0b\u9020\u4ef7', '\u7ed3\u7b97',
        '\u652f\u4ed8', '\u627f\u5305', '\u62db\u6807\u6587\u4ef6', '\u5408\u540c', '\u9020\u4ef7',
    ],
    'schedule_plan': [
        '\u603b\u8fdb\u5ea6\u8ba1\u5212', '\u65bd\u5de5\u8fdb\u5ea6', '\u5de5\u671f', '\u8282\u70b9',
        '\u5f00\u5de5', '\u7ae3\u5de5', '\u65bd\u5de5\u7ec4\u7ec7', '\u65f6\u95f4\u5b89\u6392',
    ],
    'table_lookup': [
        '\u68c0\u67e5\u8868', '\u6e05\u5355', '\u53f0\u8d26', '\u8868\u683c', '\u8bb0\u5f55', '\u7edf\u8ba1',
    ],
}

QUESTION_TEMPLATES = {
    'safety_management': [
        '\u8d44\u6599\u4e2d\u5173\u4e8e\u201c{topic}\u201d\u7684\u5b89\u5168\u7ba1\u7406\u6216\u6574\u6539\u8981\u6c42\u662f\u4ec0\u4e48\uff1f',
        '\u6839\u636e\u300a{file_title}\u300b\uff0c\u4e0e\u201c{topic}\u201d\u76f8\u5173\u7684\u5b89\u5168\u68c0\u67e5\u91cd\u70b9\u6709\u54ea\u4e9b\uff1f',
    ],
    'quality_supervision': [
        '\u8d44\u6599\u4e2d\u5bf9\u201c{topic}\u201d\u7684\u8d28\u91cf\u68c0\u67e5\u6216\u9a8c\u6536\u8981\u6c42\u662f\u4ec0\u4e48\uff1f',
        '\u6839\u636e\u300a{file_title}\u300b\uff0c\u201c{topic}\u201d\u76f8\u5173\u7684\u8d28\u91cf\u7ba1\u63a7\u8981\u70b9\u662f\u4ec0\u4e48\uff1f',
    ],
    'table_lookup': [
        '\u8bf7\u6839\u636e\u8d44\u6599\u8bf4\u660e\u201c{topic}\u201d\u76f8\u5173\u8868\u683c\u6216\u6e05\u5355\u8bb0\u5f55\u4e86\u54ea\u4e9b\u5173\u952e\u4fe1\u606f\uff1f',
        '\u300a{file_title}\u300b\u4e2d\u4e0e\u201c{topic}\u201d\u76f8\u5173\u7684\u8868\u683c\u6570\u636e\u8981\u70b9\u662f\u4ec0\u4e48\uff1f',
    ],
    'cost_contract': [
        '\u8d44\u6599\u4e2d\u5173\u4e8e\u201c{topic}\u201d\u7684\u5408\u540c\u3001\u9020\u4ef7\u6216\u652f\u4ed8\u8981\u6c42\u662f\u4ec0\u4e48\uff1f',
        '\u6839\u636e\u300a{file_title}\u300b\uff0c\u201c{topic}\u201d\u76f8\u5173\u7684\u5546\u52a1\u6761\u6b3e\u8981\u70b9\u662f\u4ec0\u4e48\uff1f',
    ],
    'schedule_plan': [
        '\u8d44\u6599\u4e2d\u5173\u4e8e\u201c{topic}\u201d\u7684\u8fdb\u5ea6\u3001\u5de5\u671f\u6216\u8282\u70b9\u5b89\u6392\u662f\u4ec0\u4e48\uff1f',
        '\u6839\u636e\u300a{file_title}\u300b\uff0c\u201c{topic}\u201d\u76f8\u5173\u7684\u65f6\u95f4\u6216\u8ba1\u5212\u8981\u70b9\u662f\u4ec0\u4e48\uff1f',
    ],
    'fact_lookup': [
        '\u8d44\u6599\u4e2d\u5173\u4e8e\u201c{topic}\u201d\u7684\u4e3b\u8981\u5185\u5bb9\u662f\u4ec0\u4e48\uff1f',
        '\u6839\u636e\u300a{file_title}\u300b\uff0c\u201c{topic}\u201d\u7684\u5173\u952e\u8bf4\u660e\u662f\u4ec0\u4e48\uff1f',
    ],
}

DIFFICULTY_BY_TYPE = {
    'table_lookup': 'medium',
    'safety_management': 'medium',
    'quality_supervision': 'medium',
    'fact_lookup': 'easy',
    'cost_contract': 'medium',
    'schedule_plan': 'medium',
}


def load_chunks(path):
    chunks = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            item['chunk_index'] = int(item.get('chunk_index') or 0)
            item['text'] = item.get('text') or ''
            item['text_length'] = int(item.get('text_length') or len(item['text']))
            chunks.append(item)
    return chunks


def strip_extension(file_name):
    return re.sub(r'\.[A-Za-z0-9]+$', '', file_name or '')


def normalize_text(text):
    text = text or ''
    text = re.sub(r'\r\n?', '\n', text)
    lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('\u8bf4\u660e\uff1a'):
            continue
        if stripped.startswith('\u5185\u5bb9\u7c7b\u578b\uff1a'):
            continue
        lines.append(stripped)
    cleaned = '\n'.join(lines)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


def is_table_like(item):
    text = item.get('text') or ''
    block_type = item.get('block_type') or ''
    return 'table' in block_type or text.count('|') >= 6 or re.search(r'\|\s*---\s*\|', text) is not None


def is_noisy(item):
    text = normalize_text(item.get('text'))
    if len(text) < 80:
        return True
    if len(text) > 3500:
        return True
    if (item.get('block_type') or '') in {'pdf_title', 'title'} and len(text) < 120:
        return True
    chars = len(text)
    if chars:
        symbol_count = sum(1 for ch in text if not ch.isalnum() and not ('\u4e00' <= ch <= '\u9fff') and not ch.isspace())
        if symbol_count / chars > 0.45:
            return True
    return False


def extract_terms(text, max_terms=8):
    text = normalize_text(text)
    raw_terms = re.findall(r'[A-Za-z][A-Za-z0-9_\-/.]*|[\u4e00-\u9fff]{2,12}|\d+(?:\.\d+)?', text)
    terms = []
    for term in raw_terms:
        term = term.strip()
        if not term:
            continue
        if term in ZH_STOPWORDS or term in BAD_TOPIC_TERMS:
            continue
        if re.fullmatch(r'[A-Za-z0-9_\-/.]+', term) and len(term) > 32:
            continue
        if len(term) == 1:
            continue
        if term.isdigit() and len(term) < 3:
            continue
        terms.append(term)
    counts = Counter(terms)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))
    return [term for term, _ in ranked[:max_terms]]


def keyword_hits(text, keywords):
    return sum(1 for keyword in keywords if keyword in text)


def classify_question_type(item):
    text = normalize_text(item.get('text'))
    if is_table_like(item):
        return 'table_lookup'
    scores = {
        qtype: keyword_hits(text, keywords)
        for qtype, keywords in TYPE_KEYWORDS.items()
    }
    best_type, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score > 0:
        return best_type
    return 'fact_lookup'


def candidate_score(item):
    text = normalize_text(item.get('text'))
    length = len(text)
    score = 0
    if 220 <= length <= 1400:
        score += 5
    elif 140 <= length < 220 or 1400 < length <= 2200:
        score += 3
    else:
        score += 1
    block_type = item.get('block_type') or ''
    if 'paragraph_semantic' in block_type:
        score += 5
    if 'ocr_text_semantic' in block_type:
        score += 4
    if 'table' in block_type:
        score += 5
    if 'title' in block_type:
        score -= 2
    if len(extract_terms(text, 12)) >= 4:
        score += 3
    qtype = classify_question_type(item)
    if qtype != 'fact_lookup':
        score += 2
    return score


def make_relevant_entry(item, reason):
    return {
        'file_id': item.get('file_id'),
        'file_name': item.get('file_name'),
        'chunk_index': item.get('chunk_index'),
        'page': item.get('page'),
        'sheet_name': item.get('sheet_name'),
        'block_type': item.get('block_type'),
        'title_path': item.get('title_path') or [],
        'label_reason': reason,
        'text_preview': normalize_text(item.get('text'))[:260],
    }


def token_set(text):
    return set(extract_terms(text, 30))


def related_score(seed, other):
    seed_terms = token_set(seed.get('text'))
    other_terms = token_set(other.get('text'))
    if not seed_terms or not other_terms:
        return 0.0
    overlap = len(seed_terms & other_terms)
    return overlap / math.sqrt(len(seed_terms) * len(other_terms))


def build_relevant_chunks(seed, chunks_by_file):
    relevant = [make_relevant_entry(seed, 'seed')]
    used = {(seed.get('file_id'), seed.get('chunk_index'))}
    file_items = chunks_by_file[seed.get('file_id')]
    by_index = {item.get('chunk_index'): item for item in file_items}
    seed_index = seed.get('chunk_index')
    seed_type = classify_question_type(seed)

    for offset in range(1, NEIGHBOR_WINDOW + 1):
        for neighbor_index, label in ((seed_index - offset, f'neighbor_-{offset}'), (seed_index + offset, f'neighbor_+{offset}')):
            neighbor = by_index.get(neighbor_index)
            if not neighbor:
                continue
            key = (neighbor.get('file_id'), neighbor.get('chunk_index'))
            if key in used or is_noisy(neighbor):
                continue
            same_page = seed.get('page') is not None and neighbor.get('page') == seed.get('page')
            similarity = related_score(seed, neighbor)
            if seed_type == 'table_lookup' or same_page or similarity >= 0.22:
                relevant.append(make_relevant_entry(neighbor, label))
                used.add(key)
            if len(relevant) >= MAX_RELEVANT_CHUNKS:
                return relevant

    related = []
    for other in file_items:
        key = (other.get('file_id'), other.get('chunk_index'))
        if key in used or is_noisy(other):
            continue
        score = related_score(seed, other)
        if score >= 0.25:
            related.append((score, other))
    related.sort(key=lambda kv: (-kv[0], abs((kv[1].get('chunk_index') or 0) - seed_index)))
    for score, other in related[:LEXICAL_RELATED_LIMIT]:
        relevant.append(make_relevant_entry(other, f'lexical_{score:.3f}'))
        used.add((other.get('file_id'), other.get('chunk_index')))
        if len(relevant) >= MAX_RELEVANT_CHUNKS:
            break
    return relevant


def build_expected_answer(seed, relevant_chunks):
    parts = []
    for entry in relevant_chunks[:3]:
        text = entry.get('text_preview') or ''
        if text:
            parts.append(text)
    body = '\n'.join(parts)
    body = re.sub(r'\s+', ' ', body).strip()
    if len(body) > 700:
        body = body[:700].rstrip() + '...'
    return body



def choose_topic(seed, qtype):
    text = normalize_text(seed.get('text'))
    preferred = PREFERRED_TOPIC_TERMS.get(qtype, []) + PREFERRED_TOPIC_TERMS.get('table_lookup', [])
    for term in sorted(preferred, key=len, reverse=True):
        if term in text:
            return term
    for term in extract_terms(text, 12):
        if term not in BAD_TOPIC_TERMS and len(term) <= 18:
            return term
    return strip_extension(seed.get('file_name'))


def build_question(seed, qtype, seq):
    terms = extract_terms(seed.get('text'), 8)
    topic = choose_topic(seed, qtype)
    file_title = strip_extension(seed.get('file_name'))
    templates = QUESTION_TEMPLATES.get(qtype) or QUESTION_TEMPLATES['fact_lookup']
    template = templates[seq % len(templates)]
    return template.format(topic=topic, file_title=file_title)


def build_candidates(chunks):
    candidates = []
    for item in chunks:
        if is_noisy(item):
            continue
        score = candidate_score(item)
        qtype = classify_question_type(item)
        item = dict(item)
        item['_candidate_score'] = score
        item['_question_type'] = qtype
        item['_terms'] = extract_terms(item.get('text'), 8)
        candidates.append(item)
    candidates.sort(key=lambda item: (-item['_candidate_score'], item.get('file_name') or '', item.get('chunk_index') or 0))
    return candidates


def select_candidates(candidates):
    selected = []
    per_file = Counter()
    per_type = Counter()
    used = set()

    by_type = defaultdict(list)
    for item in candidates:
        by_type[item['_question_type']].append(item)

    for qtype, quota in QUESTION_TYPE_QUOTAS.items():
        for item in by_type.get(qtype, []):
            if len(selected) >= TARGET_COUNT or per_type[qtype] >= quota:
                break
            key = (item.get('file_id'), item.get('chunk_index'))
            if key in used:
                continue
            if per_file[item.get('file_name')] >= MAX_PER_FILE:
                continue
            selected.append(item)
            used.add(key)
            per_file[item.get('file_name')] += 1
            per_type[qtype] += 1

    if len(selected) < TARGET_COUNT:
        for item in candidates:
            if len(selected) >= TARGET_COUNT:
                break
            key = (item.get('file_id'), item.get('chunk_index'))
            if key in used:
                continue
            if per_file[item.get('file_name')] >= MAX_PER_FILE:
                continue
            selected.append(item)
            used.add(key)
            per_file[item.get('file_name')] += 1
            per_type[item['_question_type']] += 1

    return selected[:TARGET_COUNT]


def build_dataset(selected, chunks_by_file):
    dataset = []
    for idx, seed in enumerate(selected, start=1):
        qtype = seed['_question_type']
        relevant_chunks = build_relevant_chunks(seed, chunks_by_file)
        item = {
            'id': f'q{idx:03d}',
            'question': build_question(seed, qtype, idx),
            'question_type': qtype,
            'difficulty': DIFFICULTY_BY_TYPE.get(qtype, 'medium'),
            'expected_answer': build_expected_answer(seed, relevant_chunks),
            'relevant_chunks': relevant_chunks,
            'metadata': {
                'project_id': seed.get('project_id'),
                'project_name': seed.get('project_name'),
                'source_text_length': len(normalize_text(seed.get('text'))),
                'candidate_score': seed.get('_candidate_score'),
                'topic_terms': seed.get('_terms'),
                'generation_method': 'rule_based_multi_chunk_expansion',
                'needs_spot_check': True,
                'dataset_version': 'v2_500_multi_chunk',
                'dataset_status': 'expanded',
                'review_status': 'auto_expanded_from_chunks',
                'relevant_chunk_count': len(relevant_chunks),
                'evaluation_focus': [
                    'retrieval_recall',
                    'retrieval_precision',
                    'hit_rate',
                    'ndcg',
                    'faithfulness',
                    'answer_relevance',
                    'context_relevance',
                    'citation_accuracy',
                ],
            },
        }
        dataset.append(item)
    return dataset


def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def write_summary(dataset, candidates):
    qtype_counts = Counter(item['question_type'] for item in dataset)
    difficulty_counts = Counter(item['difficulty'] for item in dataset)
    file_counts = Counter(rel['file_name'] for item in dataset for rel in item['relevant_chunks'][:1])
    block_counts = Counter(rel['block_type'] for item in dataset for rel in item['relevant_chunks'])
    relevant_counts = Counter(len(item['relevant_chunks']) for item in dataset)
    avg_relevant = sum(len(item['relevant_chunks']) for item in dataset) / len(dataset)

    lines = []
    lines.append('# ProjectManage RAG Evaluation Dataset v2 500')
    lines.append('')
    lines.append('This dataset is an expanded multi-chunk evaluation set generated from the indexed Qdrant chunks.')
    lines.append('It does not overwrite official_v1_50. It is intended for retrieval and generation evaluation with spot checking.')
    lines.append('')
    lines.append('## Files')
    lines.append('')
    lines.append('- rag_eval_dataset_v2_500.jsonl')
    lines.append('- rag_eval_dataset_v2_500.json')
    lines.append('- selected_candidate_chunks_v2_500.jsonl')
    lines.append('')
    lines.append('## Size')
    lines.append('')
    lines.append(f'- questions: {len(dataset)}')
    lines.append(f'- candidate chunks considered: {len(candidates)}')
    lines.append(f'- average relevant chunks per question: {avg_relevant:.2f}')
    lines.append('')
    lines.append('## Question types')
    lines.append('')
    for key, value in qtype_counts.most_common():
        lines.append(f'- {key}: {value}')
    lines.append('')
    lines.append('## Difficulty')
    lines.append('')
    for key, value in difficulty_counts.most_common():
        lines.append(f'- {key}: {value}')
    lines.append('')
    lines.append('## Relevant chunk count')
    lines.append('')
    for key, value in sorted(relevant_counts.items()):
        lines.append(f'- {key}: {value}')
    lines.append('')
    lines.append('## Relevant block types')
    lines.append('')
    for key, value in block_counts.most_common():
        lines.append(f'- {key}: {value}')
    lines.append('')
    lines.append('## File coverage')
    lines.append('')
    for key, value in file_counts.most_common():
        lines.append(f'- {key}: {value}')
    lines.append('')
    lines.append('## Notes')
    lines.append('')
    lines.append('- v2 adds multiple relevant chunks per question to avoid overly strict exact-chunk labels.')
    lines.append('- Labels are generated by seed chunk, neighboring chunks, and lexical overlap within the same file.')
    lines.append('- Please spot-check table and OCR questions before using generation metrics as final interview evidence.')

    OUT_SUMMARY.write_text('\n'.join(lines), encoding='utf-8')


def validate_outputs(dataset):
    if len(dataset) != TARGET_COUNT:
        raise RuntimeError(f'expected {TARGET_COUNT} items, got {len(dataset)}')
    for item in dataset:
        if not item.get('question'):
            raise RuntimeError(f'missing question: {item.get("id")}')
        if not item.get('relevant_chunks'):
            raise RuntimeError(f'missing relevant chunks: {item.get("id")}')
        for rel in item['relevant_chunks']:
            if rel.get('chunk_index') is None or rel.get('file_id') is None:
                raise RuntimeError(f'invalid relevant chunk: {item.get("id")}')


def main():
    chunks = load_chunks(CHUNKS_PATH)
    chunks_by_file = defaultdict(list)
    for chunk in chunks:
        chunks_by_file[chunk.get('file_id')].append(chunk)
    for file_id in chunks_by_file:
        chunks_by_file[file_id].sort(key=lambda item: item.get('chunk_index') or 0)

    candidates = build_candidates(chunks)
    selected = select_candidates(candidates)
    dataset = build_dataset(selected, chunks_by_file)
    validate_outputs(dataset)

    write_jsonl(OUT_JSONL, dataset)
    OUT_JSON.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding='utf-8')
    write_jsonl(OUT_CANDIDATES, selected)
    write_summary(dataset, candidates)

    qtype_counts = Counter(item['question_type'] for item in dataset)
    relevant_counts = Counter(len(item['relevant_chunks']) for item in dataset)
    print(f'wrote {len(dataset)} evaluation items')
    print('question_types:', dict(qtype_counts))
    print('relevant_chunk_counts:', dict(sorted(relevant_counts.items())))
    print('jsonl:', OUT_JSONL)
    print('summary:', OUT_SUMMARY)


if __name__ == '__main__':
    main()
