import re


DEFAULT_CONTEXT_MAX_ITEM_CHARS = 1800


def extract_query_terms(question):
    text = str(question or '').strip()
    if not text:
        return []

    terms = re.findall(r'[A-Za-z][A-Za-z0-9\-_/.]*|[\u4e00-\u9fff]{2,}|\d+(?:\.\d+)?', text)
    stop_words = {'什么', '哪些', '怎么', '如何', '为什么', '这个', '那个', '一下', '进行', '可以', '是否', '影响', '情况'}

    filtered_terms = []
    for term in terms:
        if term in stop_words:
            continue
        if len(term) <= 1:
            continue
        filtered_terms.append(term)
    return filtered_terms


def truncate_context_text(text, max_chars=DEFAULT_CONTEXT_MAX_ITEM_CHARS):
    text = str(text or '').strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rstrip() + '...'


def looks_like_table_or_figure_text(text):
    text = str(text or '').strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        return False

    if text.count('|') >= 4:
        return True

    numeric_lines = sum(1 for line in lines if re.search(r'\d', line))
    short_lines = sum(1 for line in lines if len(line) <= 35)

    if len(lines) >= 5:
        numeric_ratio = numeric_lines / len(lines)
        short_ratio = short_lines / len(lines)

        if numeric_ratio >= 0.45 and short_ratio >= 0.55:
            return True

    figure_keywords = ['图', 'Fig.', 'Fig ', '表', 'Table']
    if any(text.startswith(keyword) for keyword in figure_keywords):
        return True

    return False
