from django.conf import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 切分策略函数
def get_split_profile(document):
    metadata = document.metadata or {}
    file_extension = metadata.get('file_extension')
    block_type = metadata.get('block_type')

    if block_type in ['pdf_table', 'table', 'sheet_table']:
        return {
            'chunk_size': 1800,
            'chunk_overlap': 80,
            'protect_limit': 2200,
        }

    if file_extension == '.pdf':
        return {
            'chunk_size': 1100,
            'chunk_overlap': 160,
            'protect_limit': None,
        }

    if file_extension == '.docx':
        return {
            'chunk_size': 1000,
            'chunk_overlap': 140,
            'protect_limit': None,
        }

    if file_extension in ['.xlsx', '.xlsm']:
        return {
            'chunk_size': 1600,
            'chunk_overlap': 80,
            'protect_limit': 2200,
        }

    if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
        return {
            'chunk_size': 800,
            'chunk_overlap': 100,
            'protect_limit': None,
        }

    return {
        'chunk_size': 1000,
        'chunk_overlap': 140,
        'protect_limit': None,
    }

# document 太长时兜底切分
def split_documents(documents):
    chunks = []
    for document in documents:
        content = document.page_content or ''
        profile = get_split_profile(document)
        protect_limit = profile.get('protect_limit')
        if protect_limit and len(content) <= protect_limit:
            chunks.append(document)
            continue

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=profile['chunk_size'],
            chunk_overlap=profile['chunk_overlap'],
            separators=['\n\n', '\n', '。', '；', '，', ' ', ''],
        )
        chunks.extend(splitter.split_documents([document]))
    for index, chunk in enumerate(chunks):
        chunk.metadata['chunk_index'] = index
    return chunks
