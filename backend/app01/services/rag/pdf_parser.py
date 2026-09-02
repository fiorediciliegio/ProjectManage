from django.conf import settings
from paddleocr import PaddleOCR

from app01.services.rag.blocks import make_block

import fitz
import os
import pdfplumber
import re
import statistics
import tempfile


# .pdf 解析
# 添加页眉页脚识别函数
PDF_HEADER_RATIO = 0.045
PDF_FOOTER_RATIO = 0.055
PDF_REPEAT_RATIO = 0.6

def normalize_pdf_margin_text(text):
    return re.sub(r'\s+', '', text or '').strip()

def is_page_number_text(text):
    normalized = normalize_pdf_margin_text(text)

    return bool(
        re.match(r'^\d+$', normalized)
        or re.match(r'^第?\d+页$', normalized)
        or re.match(r'^[-—]\d+[-—]$', normalized)
        or re.match(r'^\d+/\d+$', normalized)
    )

def extract_text_from_pdf_block(block):
    lines = []
    max_font_size = 0
    font_sizes = []

    for line in block.get('lines', []):
        line_text_parts = []

        for span in line.get('spans', []):
            text = span.get('text', '').strip()
            if not text:
                continue

            line_text_parts.append(text)

            size = span.get('size', 0)
            if size:
                font_sizes.append(size)
                max_font_size = max(max_font_size, size)

        if line_text_parts:
            lines.append(''.join(line_text_parts))

    return '\n'.join(lines).strip(), max_font_size, font_sizes

# 统计重复页眉页脚文本
def collect_repeated_pdf_margin_texts(pdf):
    margin_text_counts = {}
    page_count = pdf.page_count

    if page_count < 3:
        return set()

    for page_index in range(page_count):
        page = pdf.load_page(page_index)
        page_height = page.rect.height
        page_dict = page.get_text('dict')

        for block in page_dict.get('blocks', []):
            if block.get('type') != 0:
                continue

            bbox = block.get('bbox')
            if not bbox:
                continue

            x0, y0, x1, y1 = bbox
            in_header = y1 <= page_height * PDF_HEADER_RATIO
            in_footer = y0 >= page_height * (1 - PDF_FOOTER_RATIO)

            if not in_header and not in_footer:
                continue

            text, _, _ = extract_text_from_pdf_block(block)
            normalized = normalize_pdf_margin_text(text)

            if not normalized:
                continue

            if len(normalized) > 80:
                continue

            margin_text_counts.setdefault(normalized, set()).add(page_index)

    min_repeat_pages = max(3, int(page_count * PDF_REPEAT_RATIO))

    return {
        text
        for text, page_indexes in margin_text_counts.items()
        if len(page_indexes) >= min_repeat_pages
    }

# 判断某个block是否应过滤
def should_skip_pdf_margin_block(block, page, repeated_margin_texts):
    bbox = block.get('bbox')
    if not bbox:
        return False

    x0, y0, x1, y1 = bbox
    page_height = page.rect.height

    in_header = y1 <= page_height * PDF_HEADER_RATIO
    in_footer = y0 >= page_height * (1 - PDF_FOOTER_RATIO)

    if not in_header and not in_footer:
        return False

    text, _, _ = extract_text_from_pdf_block(block)
    normalized = normalize_pdf_margin_text(text)

    if not normalized:
        return True
    if is_page_number_text(normalized):
        return True
    if normalized in repeated_margin_texts:
        return True
    return False

# 标题判断函数
def get_pdf_page_average_font_size(page_dict):
    font_sizes = []

    for block in page_dict.get('blocks', []):
        if block.get('type') != 0:
            continue

        for line in block.get('lines', []):
            for span in line.get('spans', []):
                size = span.get('size', 0)
                text = span.get('text', '').strip()

                if size and text:
                    font_sizes.append(size)

    if not font_sizes:
        return 12
    return statistics.median(font_sizes)

def is_pdf_title_block(text, max_font_size, average_font_size):
    stripped = (text or '').strip()

    if not stripped:
        return False

    normalized = stripped.replace('\n', '')

    heading_patterns = [
        r'^摘要$',
        r'^关键词',
        r'^Abstract$',
        r'^Keywords',
        r'^引言$',
        r'^结论$',
        r'^参考文献$',
        r'^第[一二三四五六七八九十\d]+章',
        r'^\d+(\.\d+)*\s+.+',
    ]

    if any(re.match(pattern, normalized, re.IGNORECASE) for pattern in heading_patterns):
        return True
    if max_font_size >= average_font_size + 2 and len(normalized) <= 80:
        return True
    return False

# 多栏判断函数
def is_two_column_page(text_blocks, page_width):
    if len(text_blocks) < 8:
        return False

    left_count = 0
    right_count = 0
    middle_count = 0

    for block in text_blocks:
        x0, y0, x1, y1 = block.get('bbox')
        center_x = (x0 + x1) / 2

        if center_x < page_width * 0.42:
            left_count += 1
        elif center_x > page_width * 0.58:
            right_count += 1
        else:
            middle_count += 1

    total = len(text_blocks)

    return left_count >= total * 0.3 and right_count >= total * 0.3 and middle_count <= total * 0.25

# 排序函数
def sort_pdf_text_blocks_by_layout(text_blocks, page_width):
    if not is_two_column_page(text_blocks, page_width):
        return sorted(
            text_blocks,
            key=lambda item: (
                round(item.get('bbox')[1], 1),
                round(item.get('bbox')[0], 1),
            )
        )
    left_blocks = []
    right_blocks = []
    full_width_blocks = []

    for block in text_blocks:
        x0, y0, x1, y1 = block.get('bbox')
        block_width = x1 - x0
        center_x = (x0 + x1) / 2

        if block_width >= page_width * 0.65:
            full_width_blocks.append(block)
        elif center_x < page_width / 2:
            left_blocks.append(block)
        else:
            right_blocks.append(block)

    full_width_blocks.sort(key=lambda item: (item.get('bbox')[1], item.get('bbox')[0]))
    left_blocks.sort(key=lambda item: (item.get('bbox')[1], item.get('bbox')[0]))
    right_blocks.sort(key=lambda item: (item.get('bbox')[1], item.get('bbox')[0]))

    return full_width_blocks + left_blocks + right_blocks

# .pdf 表格转Markdown
def convert_pdf_table_to_markdown(table):
    if not table:
        return ''

    rows = []

    for row in table:
        cleaned_row = [
            normalize_pdf_table_cell(cell)
            for cell in row
        ]

        if any(cleaned_row):
            rows.append(cleaned_row)

    if not rows:
        return ''

    max_cols = max(len(row) for row in rows)

    normalized_rows = [
        row + [''] * (max_cols - len(row))
        for row in rows
    ]

    header = normalized_rows[0]
    body = normalized_rows[1:]

    lines = []
    lines.append('| ' + ' | '.join(header) + ' |')
    lines.append('| ' + ' | '.join(['---'] * max_cols) + ' |')

    for row in body:
        lines.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(lines)

def normalize_pdf_table_cell(cell):
    if cell is None:
        return ''

    text = str(cell).strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('|', '/')

    return text

# .pdf 表格提取函数
def extract_pdf_table_blocks(file_path, base_metadata, start_order=0):
    blocks = []
    order = start_order

    with pdfplumber.open(file_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            for table_index, table in enumerate(tables, start=1):
                table_text = convert_pdf_table_to_markdown(table)

                if not table_text.strip():
                    continue

                blocks.append(
                    make_block(
                        text=table_text,
                        block_type='pdf_table',
                        base_metadata=base_metadata,
                        order=order,
                        page=page_index,
                        caption=f'PDF 第 {page_index} 页表格 {table_index}',
                    )
                )
                order += 1
    return blocks

# 扫描页判断
def is_scanned_pdf_page(page, min_text_length=40):
    text = page.get_text('text').strip()
    images = page.get_images(full=True)

    return len(text) < min_text_length and len(images) > 0

_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine

    if PaddleOCR is None:
        return None

    if _ocr_engine is None:
        _ocr_engine = PaddleOCR(
            lang='ch',
            text_detection_model_name='PP-OCRv5_mobile_det',
            text_recognition_model_name='PP-OCRv5_mobile_rec',
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            enable_mkldnn=False,
        )
    return _ocr_engine

# 把 pdf 页面渲染成 png
def render_pdf_page_to_image(page, zoom=2):
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    return pixmap.tobytes('png')

# OCR 结果解析函数
def extract_text_from_ocr_result(result, min_confidence=0.6):
    lines = []

    for page_result in result or []:
        if isinstance(page_result, dict):
            texts = page_result.get('rec_texts') or []
            scores = page_result.get('rec_scores') or []

            for index, text in enumerate(texts):
                score = scores[index] if index < len(scores) else 1
                if score >= min_confidence and str(text).strip():
                    lines.append(str(text).strip())
            continue

        if hasattr(page_result, 'json'):
            data = page_result.json
            texts = data.get('rec_texts') or []
            scores = data.get('rec_scores') or []

            for index, text in enumerate(texts):
                score = scores[index] if index < len(scores) else 1
                if score >= min_confidence and str(text).strip():
                    lines.append(str(text).strip())

            continue
        # 兼容旧版 PaddleOCR 返回格式
        for item in page_result or []:
            try:
                text = item[1][0]
                score = item[1][1]
            except (IndexError, TypeError):
                continue

            if score >= min_confidence and str(text).strip():
                lines.append(str(text).strip())
    return '\n'.join(lines)

# 单页 OCR 函数
def ocr_pdf_page(page):
    image_bytes = render_pdf_page_to_image(page)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
        temp_file.write(image_bytes)
        temp_image_path = temp_file.name

    try:
        ocr_engine = get_ocr_engine()
        result = ocr_engine.ocr(temp_image_path)
        return extract_text_from_ocr_result(result)
    finally:
        if os. path.exists(temp_image_path):
            os.remove(temp_image_path)


def load_pdf_blocks(file_path, base_metadata):
    pdf = fitz.open(file_path)
    blocks = []
    order = 0
    try:
        repeated_margin_texts = collect_repeated_pdf_margin_texts(pdf)

        for page_index in range(pdf.page_count):
            page = pdf.load_page(page_index)
            if is_scanned_pdf_page(page):
                ocr_text = ocr_pdf_page(page)
                if ocr_text.strip():
                    blocks.append(
                        make_block(
                            text=ocr_text,
                            block_type='pdf_ocr_text',
                            base_metadata=base_metadata,
                            order=order,
                            page=page_index + 1,
                            caption=f'PDF 第 {page_index + 1} 页 OCR 识别文本',
                        )
                    )
                    order += 1
                continue
            page_dict = page.get_text('dict')
            average_font_size = get_pdf_page_average_font_size(page_dict)
            raw_text_blocks = []

            for block in page_dict.get('blocks', []):
                if block.get('type') != 0:
                    continue
                if should_skip_pdf_margin_block(block, page, repeated_margin_texts):
                    continue
                bbox = block.get('bbox')
                if not bbox:
                    continue
                text, max_font_size, _ = extract_text_from_pdf_block(block)
                if not text:
                    continue
                raw_text_blocks.append({
                    'raw_block': block,
                    'bbox': bbox,
                    'text': text,
                    'max_font_size': max_font_size,
                })
            sorted_text_blocks = sort_pdf_text_blocks_by_layout(
                raw_text_blocks,
                page.rect.width,
            )
            for item in sorted_text_blocks:
                text = item['text']
                max_font_size = item['max_font_size']

                block_type = 'pdf_paragraph'
                if is_pdf_title_block(text, max_font_size, average_font_size):
                    block_type = 'pdf_title'

                blocks.append(
                    make_block(
                        text=text,
                        block_type=block_type,
                        base_metadata=base_metadata,
                        order=order,
                        page=page_index + 1,
                    )
                )
                order += 1
    finally:
        pdf.close()

    table_blocks = extract_pdf_table_blocks(
        file_path=file_path,
        base_metadata=base_metadata,
        start_order=order,
    )
    blocks.extend(table_blocks)
    blocks.sort(key=lambda item: (
        item.get('page') or 0,
        item.get('order') or 0,
    ))
    return blocks
