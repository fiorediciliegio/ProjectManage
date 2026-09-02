from langchain_core.documents import Document


# ———————————————————— 文件预处理 ————————————————————
def build_base_metadata(file_obj):
    file_name = f'{file_obj.NAME_File}{file_obj.FORM_File or ""}'
    return {
        'file_id': file_obj.pk,
        'file_name': file_name,
        'project_id': file_obj.ID_Project_id,
        'project_name': file_obj.ID_Project.NAME_Project,
        'file_extension': (file_obj.FORM_File or '').lower(),
    }

# 结构化数据
def make_block(text, block_type, base_metadata, order, title_path=None, page=None, sheet_name=None, caption=None):
    return {
        **base_metadata,
        'text': (text or '').strip(),
        'block_type': block_type,
        'title_path': title_path or [],
        'page': page,
        'sheet_name': sheet_name,
        'caption': caption,
        'order': order,
    }

# 定义不同文件类型和 block 类型的切分策略
def get_semantic_merge_profile(block):
    file_extension = block.get('file_extension')
    block_type = block.get('block_type')

    if block_type in ['pdf_table', 'table', 'sheet_table']:
        return {
            'mergeable': False,
            'target_chars': 1600,
            'max_chars': 2200,
        }

    if block_type in ['title', 'pdf_title']:
        return {
            'mergeable': False,
            'target_chars': 0,
            'max_chars': 0,
        }

    if file_extension == '.pdf':
        return {
            'mergeable': block_type in ['pdf_paragraph', 'pdf_ocr_text', 'pdf_merged_paragraph'],
            'target_chars': 900,
            'max_chars': 1300,
        }

    if file_extension == '.docx':
        return {
            'mergeable': block_type in ['paragraph'],
            'target_chars': 900,
            'max_chars': 1300,
        }

    if file_extension in ['.txt', '.md', '.py', '.json', '.js', '.css', '.html']:
        return {
            'mergeable': True,
            'target_chars': 1000,
            'max_chars': 1400,
        }

    if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
        return {
            'mergeable': block_type in ['image_ocr_text'],
            'target_chars': 800,
            'max_chars': 1200,
        }

    return {
        'mergeable': True,
        'target_chars': 900,
        'max_chars': 1300,
    }

# 根据语义将 block 转 Document
def make_document_from_block(block):
    text = block.get('text', '').strip()
    title_path = block.get('title_path') or []
    caption = block.get('caption')

    prefix_lines = []

    if title_path:
        prefix_lines.append(f"标题路径：{' > '.join(title_path[-4:])}")

    if caption:
        prefix_lines.append(f"说明：{caption}")

    if block.get('block_type'):
        prefix_lines.append(f"内容类型：{block.get('block_type')}")

    page_content = '\n'.join(prefix_lines + [text]) if prefix_lines else text

    metadata = {
        key: value
        for key, value in block.items()
        if key != 'text'
    }

    return Document(
        page_content=page_content,
        metadata=metadata,
    )

# 根据语义合并 block
def blocks_to_semantic_documents(blocks):
    documents = []
    buffer_texts = []
    buffer_block = None
    buffer_chars = 0
    order = 0

    def flush_buffer():
        nonlocal buffer_texts, buffer_block, buffer_chars, order

        if not buffer_texts or not buffer_block:
            return

        merged_block = {
            **buffer_block,
            'text': '\n'.join(buffer_texts).strip(),
            'block_type': f"{buffer_block.get('block_type')}_semantic",
            'order': order,
        }

        documents.append(make_document_from_block(merged_block))

        buffer_texts = []
        buffer_block = None
        buffer_chars = 0
        order += 1

    for block in blocks:
        text = str(block.get('text') or '').strip()
        if not text:
            continue

        profile = get_semantic_merge_profile(block)
        block_type = block.get('block_type')
        title_path = block.get('title_path') or []
        page = block.get('page')
        sheet_name = block.get('sheet_name')

        if not profile['mergeable']:
            flush_buffer()
            single_block = {
                **block,
                'order': order,
            }
            documents.append(make_document_from_block(single_block))
            order += 1
            continue

        if buffer_block:
            buffer_profile = get_semantic_merge_profile(buffer_block)
            buffer_title_path = buffer_block.get('title_path') or []
            buffer_type = buffer_block.get('block_type')
            buffer_page = buffer_block.get('page')
            buffer_sheet_name = buffer_block.get('sheet_name')

            should_flush = (
                title_path != buffer_title_path
                or block_type != buffer_type
                or sheet_name != buffer_sheet_name
                or buffer_chars + len(text) > buffer_profile['max_chars']
            )

            if block.get('file_extension') == '.pdf':
                if page is not None and buffer_page is not None:
                    should_flush = should_flush or page - buffer_page > 1

            if should_flush:
                flush_buffer()

        if not buffer_block:
            buffer_block = block

        buffer_texts.append(text)
        buffer_chars += len(text)

        if buffer_chars >= profile['target_chars']:
            flush_buffer()

    flush_buffer()
    return merge_short_documents(documents)

# 短 document 二次合并
def merge_short_documents(documents, min_chars=220, max_chars=1200):
    merged = []
    buffer_doc = None

    def doc_key(doc):
        metadata = doc.metadata or {}
        return (
            metadata.get('file_id'),
            tuple(metadata.get('title_path') or []),
            metadata.get('block_type'),
            metadata.get('sheet_name'),
        )

    for doc in documents:
        content = doc.page_content or ''

        if buffer_doc is None:
            buffer_doc = doc
            continue

        buffer_content = buffer_doc.page_content or ''
        same_group = doc_key(buffer_doc) == doc_key(doc)

        if (
            same_group
            and len(buffer_content) < min_chars
            and len(buffer_content) + len(content) <= max_chars
        ):
            buffer_doc.page_content = buffer_content.rstrip() + '\n' + content.lstrip()
        else:
            merged.append(buffer_doc)
            buffer_doc = doc

    if buffer_doc is not None:
        merged.append(buffer_doc)

    return merged
