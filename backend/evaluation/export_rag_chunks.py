import argparse
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Projectmanagement.settings')

import django
django.setup()

from django.conf import settings
from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from app01.services.langchain_rag_service import get_langchain_qdrant_client


def build_project_filter(project_id):
    if project_id is None:
        return None

    return Filter(
        must=[
            FieldCondition(
                key='metadata.project_id',
                match=MatchValue(value=project_id),
            )
        ]
    )


def export_chunks(output_path, project_id=None, limit=100):
    client = get_langchain_qdrant_client()
    collection_name = settings.LANGCHAIN_QDRANT_COLLECTION

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scroll_filter = build_project_filter(project_id)

    rows = []
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = point.payload or {}
            metadata = payload.get('metadata') or {}

            text = (
                payload.get('page_content')
                or payload.get('text')
                or payload.get('content')
                or ''
            )

            row = {
                'point_id': str(point.id),
                'file_id': metadata.get('file_id'),
                'file_name': metadata.get('file_name'),
                'project_id': metadata.get('project_id'),
                'project_name': metadata.get('project_name'),
                'chunk_index': metadata.get('chunk_index'),
                'merged_chunk_indexes': metadata.get('merged_chunk_indexes'),
                'page': metadata.get('page'),
                'sheet_name': metadata.get('sheet_name'),
                'title_path': metadata.get('title_path'),
                'block_type': metadata.get('block_type'),
                'text': text,
                'text_length': len(text),
            }

            rows.append(row)

        if offset is None:
            break

    rows.sort(
        key=lambda item: (
            item.get('project_id') or 0,
            item.get('file_id') or 0,
            item.get('chunk_index') or 0,
        )
    )

    with output_path.open('w', encoding='utf-8') as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + '\n')

    return {
        'output_path': str(output_path),
        'chunks_count': len(rows),
        'files_count': len({row.get('file_id') for row in rows if row.get('file_id') is not None}),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output',
        default='evaluation/chunks_export.jsonl',
        help='导出的 jsonl 文件路径',
    )
    parser.add_argument(
        '--project-id',
        type=int,
        default=None,
        help='只导出指定项目的 chunks，不填则导出全部',
    )

    args = parser.parse_args()

    result = export_chunks(
        output_path=args.output,
        project_id=args.project_id,
    )

    print('导出完成')
    print(f"文件路径: {result['output_path']}")
    print(f"chunk 数量: {result['chunks_count']}")
    print(f"文件数量: {result['files_count']}")


if __name__ == '__main__':
    main()
