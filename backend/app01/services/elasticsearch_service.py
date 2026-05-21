from django.conf import settings
from elasticsearch import Elasticsearch, helpers


def get_elasticsearch_client():
    return Elasticsearch(settings.ELASTICSEARCH_URL)


def ensure_file_chunk_index():
    client = get_elasticsearch_client()
    index_name = settings.ELASTICSEARCH_INDEX

    if client.indices.exists(index=index_name):
        return client

    mapping = {
        'mappings': {
            'properties': {
                'file_id': {'type': 'integer'},
                'project_id': {'type': 'integer'},
                'file_name': {
                    'type': 'text',
                    'fields': {
                        'keyword': {'type': 'keyword', 'ignore_above': 256},
                    },
                },
                'file_extension': {'type': 'keyword'},
                'project_name': {
                    'type': 'text',
                    'fields': {
                        'keyword': {'type': 'keyword', 'ignore_above': 256},
                    },
                },
                'chunk_index': {'type': 'integer'},
                'text': {'type': 'text'},
                'title_path': {'type': 'text'},
                'page': {'type': 'integer'},
                'sheet_name': {
                    'type': 'text',
                    'fields': {
                        'keyword': {'type': 'keyword', 'ignore_above': 256},
                    },
                },
                'block_type': {'type': 'keyword'},
            }
        }
    }

    client.indices.create(index=index_name, body=mapping)
    return client


def normalize_title_path(title_path):
    if not title_path:
        return ''

    if isinstance(title_path, list):
        return ' > '.join(str(item) for item in title_path if item)

    return str(title_path)


def document_to_elasticsearch_body(file_obj, document):
    metadata = document.metadata or {}

    return {
        'file_id': metadata.get('file_id') or file_obj.pk,
        'project_id': metadata.get('project_id') or file_obj.ID_Project_id,
        'project_name': metadata.get('project_name') or file_obj.ID_Project.NAME_Project,
        'file_name': metadata.get('file_name') or f'{file_obj.NAME_File}{file_obj.FORM_File or ""}',
        'file_extension': metadata.get('file_extension') or (file_obj.FORM_File or '').lower(),
        'chunk_index': metadata.get('chunk_index'),
        'text': document.page_content or '',
        'title_path': normalize_title_path(metadata.get('title_path')),
        'page': metadata.get('page'),
        'sheet_name': metadata.get('sheet_name'),
        'block_type': metadata.get('block_type'),
    }


def index_chunks_to_elasticsearch(file_obj, chunks):
    client = ensure_file_chunk_index()
    index_name = settings.ELASTICSEARCH_INDEX
    actions = []

    for chunk in chunks:
        metadata = chunk.metadata or {}
        chunk_index = metadata.get('chunk_index')

        if chunk_index is None:
            continue

        actions.append({
            '_op_type': 'index',
            '_index': index_name,
            '_id': f'file-{file_obj.pk}-chunk-{chunk_index}',
            '_source': document_to_elasticsearch_body(file_obj, chunk),
        })

    if not actions:
        return {
            'indexed_count': 0,
            'message': '没有可写入 Elasticsearch 的文档片段',
        }

    helpers.bulk(client, actions)

    return {
        'indexed_count': len(actions),
        'message': '文件片段写入 Elasticsearch 成功',
    }


def delete_file_chunks_from_elasticsearch(file_id):
    client = ensure_file_chunk_index()
    index_name = settings.ELASTICSEARCH_INDEX

    response = client.delete_by_query(
        index=index_name,
        body={
            'query': {
                'term': {
                    'file_id': file_id,
                }
            }
        },
        refresh=True,
        conflicts='proceed',
    )

    return {
        'deleted_count': response.get('deleted', 0),
        'message': '文件片段已从 Elasticsearch 删除',
    }


def keyword_search_file_chunks(query, project_id=None, limit=20):
    client = ensure_file_chunk_index()
    index_name = settings.ELASTICSEARCH_INDEX

    must_conditions = [
        {
            'multi_match': {
                'query': query,
                'fields': [
                    'text^3',
                    'title_path^2',
                    'file_name^1.5',
                    'project_name',
                    'sheet_name',
                ],
                'type': 'best_fields',
            }
        }
    ]

    filter_conditions = []

    if project_id is not None:
        filter_conditions.append({
            'term': {
                'project_id': project_id,
            }
        })

    response = client.search(
        index=index_name,
        body={
            'size': limit,
            'query': {
                'bool': {
                    'must': must_conditions,
                    'filter': filter_conditions,
                }
            }
        },
    )

    results = []

    for hit in response.get('hits', {}).get('hits', []):
        source = hit.get('_source', {})

        results.append({
            'score': hit.get('_score'),
            'file_id': source.get('file_id'),
            'project_id': source.get('project_id'),
            'project_name': source.get('project_name'),
            'file_name': source.get('file_name'),
            'file_extension': source.get('file_extension'),
            'chunk_index': source.get('chunk_index'),
            'block_type': source.get('block_type'),
            'page': source.get('page'),
            'sheet_name': source.get('sheet_name'),
            'title_path': source.get('title_path'),
            'text': source.get('text'),
            'retrieval_type': 'keyword',
        })

    return results