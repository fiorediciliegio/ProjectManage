from app01.services.rag.blocks import (
    blocks_to_semantic_documents,
    build_base_metadata,
    get_semantic_merge_profile,
    make_block,
    make_document_from_block,
    merge_short_documents,
)
from app01.services.rag.file_parsers import (
    convert_docx_table_to_markdown,
    convert_xlsx_sheet_to_markdown_with_formulas,
    format_excel_cell_value_with_formula,
    get_heading_level,
    load_docx_blocks,
    load_plain_file_blocks,
    load_xlsx_blocks,
)
from app01.services.rag.image_parser import load_image_blocks
from app01.services.rag.pdf_parser import (
    collect_repeated_pdf_margin_texts,
    convert_pdf_table_to_markdown,
    extract_pdf_table_blocks,
    extract_text_from_ocr_result,
    extract_text_from_pdf_block,
    get_ocr_engine,
    get_pdf_page_average_font_size,
    is_page_number_text,
    is_pdf_title_block,
    is_scanned_pdf_page,
    is_two_column_page,
    load_pdf_blocks,
    normalize_pdf_margin_text,
    normalize_pdf_table_cell,
    ocr_pdf_page,
    render_pdf_page_to_image,
    should_skip_pdf_margin_block,
    sort_pdf_text_blocks_by_layout,
)
from app01.services.rag.splitters import get_split_profile, split_documents


TEXT_FILE_EXTENSIONS = ['.txt', '.md', '.py', '.json', '.js', '.css', '.html']
EXCEL_FILE_EXTENSIONS = ['.xlsx', '.xlsm']
IMAGE_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']


def load_file_as_blocks(file_obj):
    file_path = file_obj.FILE.path
    file_extension = (file_obj.FORM_File or '').lower()
    base_metadata = build_base_metadata(file_obj)

    if file_extension in TEXT_FILE_EXTENSIONS:
        return load_plain_file_blocks(file_path, base_metadata)

    if file_extension == '.docx':
        return load_docx_blocks(file_path, base_metadata)

    if file_extension in EXCEL_FILE_EXTENSIONS:
        return load_xlsx_blocks(file_path, base_metadata)

    if file_extension == '.pdf':
        return load_pdf_blocks(file_path, base_metadata)

    if file_extension in IMAGE_FILE_EXTENSIONS:
        return load_image_blocks(file_path, base_metadata)

    raise ValueError(f'暂不支持该文件类型入库：{file_extension}')


def load_file_as_documents(file_obj):
    blocks = load_file_as_blocks(file_obj)
    return blocks_to_semantic_documents(blocks)


def preview_file_chunks(file_obj):
    documents = load_file_as_documents(file_obj)
    chunks = split_documents(documents)
    return [
        {
            'content': chunk.page_content,
            'metadata': chunk.metadata,
        }
        for chunk in chunks
    ]
