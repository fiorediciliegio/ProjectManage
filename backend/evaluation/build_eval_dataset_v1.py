
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

BASE = Path(r'D:\ProjectManage\backend\evaluation')
INPUT = BASE / 'chunks_export.jsonl'
REPORT = BASE / 'chunk_quality_report.md'
CANDIDATES = BASE / 'selected_candidate_chunks_v1.jsonl'
DATASET = BASE / 'rag_eval_dataset_v1_50.jsonl'

META_LINE_RE = re.compile(r'^(\u8bf4\u660e\uff1a|\u5185\u5bb9\u7c7b\u578b\uff1a).*$')
PAGE_ONLY_RE = re.compile(r'^\s*\d{1,5}\s*$')

SAFETY_TERMS = ['\u5b89\u5168', '\u9690\u60a3', '\u6d88\u9632', '\u811a\u624b\u67b6', '\u4e34\u8fb9', '\u6d1e\u53e3', '\u7528\u7535', '\u8d77\u91cd', '\u6a21\u677f\u652f\u6491', '\u6587\u660e\u65bd\u5de5', '\u626c\u5c18', '\u4e13\u9879\u65bd\u5de5']
QUALITY_TERMS = ['\u8d28\u91cf', '\u9a8c\u6536', '\u68c0\u6d4b', '\u68c0\u9a8c', '\u76d1\u7406', '\u5141\u8bb8\u504f\u5dee', '\u6574\u6539', '\u8bd5\u9a8c', '\u6750\u6599', '\u65bd\u5de5\u8d28\u91cf']
COST_TERMS = ['\u9020\u4ef7', '\u5408\u540c\u4ef7', '\u91d1\u989d', '\u62db\u6807\u63a7\u5236\u4ef7', '\u6295\u6807\u62a5\u4ef7', '\u8d39\u7528']
TABLE_TERMS = ['\u6761\u6b3e', '\u7f16\u5217', '\u5e8f\u53f7', '\u9879\u76ee\u540d\u79f0', '\u5355\u4f4d', '\u8d1f\u8d23\u4eba', '\u6570\u91cf', '\u91d1\u989d', '\u65e5\u671f', '\u68c0\u67e5\u9879\u76ee']


def load_chunks():
    rows = []
    with INPUT.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def clean_text(text):
    lines = []
    for raw in (text or '').splitlines():
        line = raw.strip()
        if not line:
            continue
        if META_LINE_RE.match(line):
            continue
        if PAGE_ONLY_RE.match(line):
            continue
        lines.append(line)
    return '\n'.join(lines).strip()


def chinese_ratio(text):
    if not text:
        return 0
    zh = len(re.findall(r'[\u4e00-\u9fff]', text))
    return zh / max(len(text), 1)


def looks_noisy(text):
    if not text:
        return True
    compact = re.sub(r'\s+', '', text)
    if len(compact) < 35:
        return True
    if re.search(r'[\ufffd]|\\x[0-9a-fA-F]{2}|\\u[0-9a-fA-F]{4}', text):
        return True
    symbol_ratio = len(re.findall(r'[^\w\s\u4e00-\u9fff?????????????%/\-.\[\]~??+]', text)) / max(len(text), 1)
    if symbol_ratio > 0.20:
        return True
    return False


def infer_topic(item, text):
    title_path = item.get('title_path') or []
    if isinstance(title_path, list) and title_path:
        title = ' > '.join(str(x).strip() for x in title_path if str(x).strip())
        if 3 <= len(title) <= 100:
            return title[:80]
    for line in text.splitlines()[:10]:
        line = line.strip(' \uff1a:;\uff1b|')
        if 4 <= len(line) <= 70 and not PAGE_ONLY_RE.match(line):
            if line.count('|') <= 2:
                return line[:80]
    return '\u76f8\u5173\u5185\u5bb9'


def classify_question_type(item, text):
    bt = item.get('block_type') or ''
    if 'table' in bt:
        return 'table_lookup'
    safety_hits = sum(1 for t in SAFETY_TERMS if t in text)
    quality_hits = sum(1 for t in QUALITY_TERMS if t in text)
    cost_hits = sum(1 for t in COST_TERMS if t in text)
    if safety_hits >= max(1, quality_hits, cost_hits):
        return 'safety_management'
    if quality_hits >= max(1, safety_hits, cost_hits):
        return 'quality_supervision'
    if cost_hits >= 1:
        return 'fact_lookup'
    return 'fact_lookup'


def candidate_score(item):
    text = clean_text(item.get('text') or '')
    length = len(text)
    if looks_noisy(text):
        return -999
    score = 0
    bt = item.get('block_type') or ''
    if 220 <= length <= 1000:
        score += 5
    elif 100 <= length < 220 or 1000 < length <= 1400:
        score += 3
    elif 60 <= length < 100:
        score += 1
    else:
        score -= 3
    if 'table' in bt:
        score += 4
    if 'paragraph_semantic' in bt or 'ocr_text_semantic' in bt:
        score += 4
    if bt == 'pdf_title':
        score -= 4
    if chinese_ratio(text) > 0.30:
        score += 2
    if any(term in text for term in SAFETY_TERMS + QUALITY_TERMS + COST_TERMS + TABLE_TERMS):
        score += 3
    words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9\-_/\.]*|\d+(?:\.\d+)?', text))
    if len(words) >= 12:
        score += 1
    return score


def build_expected_answer(text, max_len=620):
    cleaned = clean_text(text)
    if len(cleaned) <= max_len:
        return cleaned
    cut = cleaned[:max_len]
    for sep in ['\u3002', '\uff1b', '\n']:
        pos = cut.rfind(sep)
        if pos > max_len * 0.55:
            return cut[:pos + 1]
    return cut.rstrip() + '...'


def short_file_name(file_name):
    short_file = file_name or '\u8be5\u6587\u4ef6'
    for suffix in ['.pdf', '.PDF', '.docx', '.xlsx', '.doc', '.xls']:
        short_file = short_file.replace(suffix, '')
    if len(short_file) > 42:
        short_file = short_file[:42] + '...'
    return short_file


def build_question(item, qtype, text):
    short_file = short_file_name(item.get('file_name'))
    topic = infer_topic(item, text)
    if qtype == 'table_lookup':
        if any(t in text for t in ['\u4e34\u65f6\u7528\u7535', '\u5916\u7535\u7ebf\u8def', '\u6d88\u9632', '\u811a\u624b\u67b6', '\u4e13\u9879\u65bd\u5de5']):
            return f'\u6839\u636e\u300a{short_file}\u300b\u4e2d\u7684\u8868\u683c\uff0c\u5b89\u5168\u68c0\u67e5\u6216\u4e13\u9879\u65bd\u5de5\u76f8\u5173\u8981\u6c42\u662f\u4ec0\u4e48\uff1f'
        if '\u68c0\u67e5\u9879\u76ee' in text and ('\u6263\u5206' in text or '\u8bc4\u5206\u6807\u51c6' in text):
            return f'\u6839\u636e\u300a{short_file}\u300b\u4e2d\u7684\u8868\u683c\uff0c\u68c0\u67e5\u9879\u76ee\u3001\u8bc4\u5206\u6807\u51c6\u6216\u6263\u5206\u8981\u6c42\u662f\u4ec0\u4e48\uff1f'
        if '\u6295\u6807\u4eba\u987b\u77e5' in text or '\u7f16\u5217\u5185\u5bb9' in text or '\u6761\u6b3e\u53f7' in text:
            return f'\u6839\u636e\u300a{short_file}\u300b\u4e2d\u7684\u8868\u683c\uff0c\u6295\u6807\u4eba\u987b\u77e5\u6216\u6761\u6b3e\u7f16\u5217\u5185\u5bb9\u6709\u54ea\u4e9b\u8981\u6c42\uff1f'
        if any(t in text for t in ['\u8d44\u8d28', '\u9879\u76ee\u7ecf\u7406', '\u8d44\u683c']):
            return f'\u6839\u636e\u300a{short_file}\u300b\u4e2d\u7684\u8868\u683c\uff0c\u6295\u6807\u4eba\u3001\u4eba\u5458\u6216\u8d44\u8d28\u6761\u4ef6\u662f\u4ec0\u4e48\uff1f'
        if any(t in text for t in ['\u8d28\u91cf', '\u9a8c\u6536', '\u5141\u8bb8\u504f\u5dee', '\u68c0\u6d4b']):
            return f'\u6839\u636e\u300a{short_file}\u300b\u4e2d\u7684\u8868\u683c\uff0c\u8d28\u91cf\u9a8c\u6536\u3001\u68c0\u6d4b\u6216\u5141\u8bb8\u504f\u5dee\u76f8\u5173\u8981\u6c42\u662f\u4ec0\u4e48\uff1f'
        return f'\u6839\u636e\u300a{short_file}\u300b\u4e2d\u7684\u8868\u683c\uff0c{topic}\u76f8\u5173\u5185\u5bb9\u6709\u54ea\u4e9b\u5173\u952e\u8981\u6c42\uff1f'
    if qtype == 'safety_management':
        return f'\u300a{short_file}\u300b\u4e2d\u5173\u4e8e\u5b89\u5168\u7ba1\u7406\u6216\u5b89\u5168\u9690\u60a3\u7684\u4e3b\u8981\u8981\u6c42\u662f\u4ec0\u4e48\uff1f'
    if qtype == 'quality_supervision':
        return f'\u300a{short_file}\u300b\u4e2d\u5173\u4e8e\u8d28\u91cf\u68c0\u67e5\u3001\u9a8c\u6536\u6216\u76d1\u7406\u7684\u8981\u6c42\u662f\u4ec0\u4e48\uff1f'
    return f'\u300a{short_file}\u300b\u4e2d\u5173\u4e8e\u201c{topic}\u201d\u7684\u4e3b\u8981\u5185\u5bb9\u662f\u4ec0\u4e48\uff1f'


def choose_candidates(items):
    candidates = []
    for item in items:
        text = clean_text(item.get('text') or '')
        score = candidate_score(item)
        if score < 4:
            continue
        qtype = classify_question_type(item, text)
        candidates.append({
            'candidate_score': score,
            'question_type': qtype,
            'clean_text_length': len(text),
            'topic': infer_topic(item, text),
            **item,
            'clean_text': text,
        })
    candidates.sort(key=lambda x: (x['candidate_score'], x.get('text_length') or 0), reverse=True)
    return candidates


def build_dataset(candidates, total=50):
    quotas = {
        'table_lookup': 15,
        'safety_management': 15,
        'quality_supervision': 10,
        'fact_lookup': 10,
    }
    max_per_file = 3
    selected = []
    used_keys = set()
    file_counts = Counter()
    type_counts = Counter()

    def can_use(c, strict_quota=True):
        key = (c.get('file_id'), c.get('chunk_index'))
        if key in used_keys:
            return False
        if file_counts[c.get('file_id')] >= max_per_file:
            return False
        if strict_quota and type_counts[c['question_type']] >= quotas.get(c['question_type'], 0):
            return False
        return True

    def add(c):
        selected.append(c)
        used_keys.add((c.get('file_id'), c.get('chunk_index')))
        file_counts[c.get('file_id')] += 1
        type_counts[c['question_type']] += 1

    by_file = defaultdict(list)
    for c in candidates:
        by_file[c.get('file_id')].append(c)

    for file_id, pool in sorted(by_file.items(), key=lambda kv: kv[0] or 0):
        pool = sorted(pool, key=lambda x: (type_counts[x['question_type']] - quotas.get(x['question_type'], 0), -x['candidate_score']))
        for c in pool:
            if can_use(c, strict_quota=True):
                add(c)
                break

    while len(selected) < total:
        progress = False
        for qtype in quotas:
            if type_counts[qtype] >= quotas[qtype]:
                continue
            pool = [c for c in candidates if c['question_type'] == qtype]
            pool.sort(key=lambda x: (file_counts[x.get('file_id')], -x['candidate_score'], x.get('chunk_index') or 0))
            for c in pool:
                if can_use(c, strict_quota=True):
                    add(c)
                    progress = True
                    break
            if len(selected) >= total:
                break
        if not progress:
            break

    if len(selected) < total:
        for c in sorted(candidates, key=lambda x: (file_counts[x.get('file_id')], -x['candidate_score'])):
            if can_use(c, strict_quota=False):
                add(c)
                if len(selected) >= total:
                    break

    buckets = defaultdict(list)
    for c in selected[:total]:
        buckets[c.get('file_id')].append(c)
    ordered = []
    while any(buckets.values()):
        for file_id in sorted(buckets.keys(), key=lambda x: x or 0):
            if buckets[file_id]:
                ordered.append(buckets[file_id].pop(0))

    rows = []
    for idx, c in enumerate(ordered[:total], start=1):
        rows.append({
            'id': f'q{idx:03d}',
            'question': build_question(c, c['question_type'], c['clean_text']),
            'question_type': c['question_type'],
            'difficulty': 'medium' if c['question_type'] == 'table_lookup' or c['clean_text_length'] > 450 else 'easy',
            'expected_answer': build_expected_answer(c.get('text') or ''),
            'relevant_chunks': [{
                'file_id': c.get('file_id'),
                'file_name': c.get('file_name'),
                'chunk_index': c.get('chunk_index'),
                'page': c.get('page'),
                'sheet_name': c.get('sheet_name'),
                'block_type': c.get('block_type'),
                'title_path': c.get('title_path'),
            }],
            'metadata': {
                'project_id': c.get('project_id'),
                'project_name': c.get('project_name'),
                'source_text_length': c['clean_text_length'],
                'candidate_score': c['candidate_score'],
                'topic': c['topic'],
                'generation_method': 'rule_based_first_draft',
                'needs_human_review': True,
            }
        })
    return rows


def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def build_report(items, candidates, dataset):
    files = Counter((i.get('file_id'), i.get('file_name')) for i in items)
    types = Counter(i.get('block_type') or 'unknown' for i in items)
    lengths = [len(clean_text(i.get('text') or '')) for i in items]
    s = sorted(lengths)
    pct = lambda p: s[int((len(s)-1)*p)] if s else 0
    short = sum(1 for x in lengths if x < 100)
    medium = sum(1 for x in lengths if 100 <= x <= 1200)
    long = sum(1 for x in lengths if x > 1200)
    noisy = sum(1 for i in items if looks_noisy(clean_text(i.get('text') or '')))
    ds_types = Counter(d['question_type'] for d in dataset)
    ds_files = Counter(d['relevant_chunks'][0]['file_name'] for d in dataset)
    ds_block_types = Counter(d['relevant_chunks'][0]['block_type'] for d in dataset)
    lines = []
    lines.append('# Chunk Quality Report')
    lines.append('')
    lines.append('## Overall')
    lines.append(f'- Total chunks: {len(items)}')
    lines.append(f'- File count: {len(files)}')
    lines.append(f'- Length min/max/avg: {min(lengths) if lengths else 0} / {max(lengths) if lengths else 0} / {round(sum(lengths)/len(lengths), 1) if lengths else 0}')
    lines.append(f'- Length p10/p25/p50/p75/p90/p95: {pct(.1)} / {pct(.25)} / {pct(.5)} / {pct(.75)} / {pct(.9)} / {pct(.95)}')
    lines.append(f'- Short chunks <100 chars: {short}')
    lines.append(f'- Medium chunks 100-1200 chars: {medium}')
    lines.append(f'- Long chunks >1200 chars: {long}')
    lines.append(f'- Noise-like chunks: {noisy}')
    lines.append('')
    lines.append('## Block Types')
    for k, v in types.most_common():
        lines.append(f'- {k}: {v}')
    lines.append('')
    lines.append('## Top Files By Chunk Count')
    for (fid, name), c in files.most_common(22):
        lines.append(f'- file_id={fid}, chunks={c}, file={name}')
    lines.append('')
    lines.append('## Candidate Selection')
    lines.append(f'- Candidate chunks selected: {len(candidates)}')
    lines.append('- Selection rule: prefer medium-length semantic paragraphs, useful tables, OCR text with enough Chinese content, and chunks containing safety/quality/table terms; avoid pure titles, page numbers, very short fragments, and noisy text.')
    lines.append('')
    lines.append('## Evaluation Dataset v1')
    lines.append(f'- Dataset size: {len(dataset)}')
    lines.append(f'- Covered files: {len(ds_files)}')
    lines.append('- Question types:')
    for k, v in ds_types.most_common():
        lines.append(f'  - {k}: {v}')
    lines.append('- Source block types:')
    for k, v in ds_block_types.most_common():
        lines.append(f'  - {k}: {v}')
    lines.append('')
    lines.append('## Notes')
    lines.append('- This is a rule-based first draft. relevant_chunks and expected_answer should be reviewed before being used as a formal benchmark.')
    lines.append('- The dataset intentionally includes table, OCR, safety, quality, and fact lookup questions to test different RAG failure modes.')
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    items = load_chunks()
    candidates = choose_candidates(items)
    dataset = build_dataset(candidates, total=50)
    write_jsonl(CANDIDATES, candidates[:300])
    write_jsonl(DATASET, dataset)
    build_report(items, candidates, dataset)
    print('chunks', len(items))
    print('candidates', len(candidates))
    print('dataset', len(dataset))
    print('question_types', Counter(d['question_type'] for d in dataset))
    print('covered_files', len(set(d['relevant_chunks'][0]['file_id'] for d in dataset)))
    print('block_types', Counter(d['relevant_chunks'][0]['block_type'] for d in dataset))
    bad = []
    for d in dataset:
        if '?' in d['question'] or '\\u' in d['question'] or '\\x' in d['question'] or '\ufffd' in d['question']:
            bad.append((d['id'], d['question']))
        if '\u8bf4\u660e\uff1a' in d['expected_answer'] or '\u5185\u5bb9\u7c7b\u578b\uff1a' in d['expected_answer']:
            bad.append((d['id'], 'meta in expected'))
    print('bad', len(bad))
    for d in dataset[:8]:
        src = d['relevant_chunks'][0]
        print(d['id'], d['question_type'], src['file_id'], src['chunk_index'], src['block_type'])
        print(d['question'])
        print((d['expected_answer'] or '')[:180].replace('\n', ' '))
        print('---')

if __name__ == '__main__':
    main()
