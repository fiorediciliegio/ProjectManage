
from django.conf import settings
from app01.models import File
from app01.services.langchain_rag_service import (
    load_file_as_blocks,
    load_file_as_documents,
    split_documents,
    get_langchain_qdrant_client,
    search_file_chunks_langchain,
)
from qdrant_client.models import Filter, FieldCondition, MatchValue
import fitz

file_obj = File.objects.get(id=34)
print('FILE:', file_obj.pk, file_obj.NAME_File, file_obj.FORM_File, 'project=', file_obj.ID_Project_id)

pdf = fitz.open(file_obj.FILE.path)
print('PDF page_count:', pdf.page_count)
pdf.close()

blocks = load_file_as_blocks(file_obj)
block_pages = [b.get('page') for b in blocks if b.get('page')]
print('blocks:', len(blocks), 'min_page:', min(block_pages) if block_pages else None, 'max_page:', max(block_pages) if block_pages else None)
print('last block samples:')
for b in blocks[-8:]:
    print('page=', b.get('page'), 'type=', b.get('block_type'), 'text=', (b.get('text') or '')[:140].replace('\n', ' '))

keywords = ['80%', '???', '????', '??????', '????']
for kw in keywords:
    hits = [b for b in blocks if kw in (b.get('text') or '')]
    print('block keyword', kw, 'hits=', len(hits), 'pages=', sorted(set([h.get('page') for h in hits if h.get('page')]))[:30])
    for h in hits[:3]:
        print('  sample page=', h.get('page'), (h.get('text') or '')[:180].replace('\n', ' '))

docs = load_file_as_documents(file_obj)
chunks = split_documents(docs)
chunk_pages = [c.metadata.get('page') for c in chunks if c.metadata.get('page')]
print('docs:', len(docs), 'chunks:', len(chunks), 'chunk min_page:', min(chunk_pages) if chunk_pages else None, 'chunk max_page:', max(chunk_pages) if chunk_pages else None)
for kw in keywords:
    hits = [c for c in chunks if kw in (c.page_content or '')]
    print('chunk keyword', kw, 'hits=', len(hits), 'pages=', sorted(set([h.metadata.get('page') for h in hits if h.metadata.get('page')]))[:30])
    for h in hits[:3]:
        print('  sample page=', h.metadata.get('page'), 'chunk=', h.metadata.get('chunk_index'), h.page_content[:180].replace('\n', ' '))

client = get_langchain_qdrant_client()
flt = Filter(must=[FieldCondition(key='metadata.file_id', match=MatchValue(value=file_obj.pk))])
all_points = []
offset = None
while True:
    points, offset = client.scroll(
        collection_name=settings.LANGCHAIN_QDRANT_COLLECTION,
        scroll_filter=flt,
        limit=1000,
        offset=offset,
        with_payload=True,
        with_vectors=False,
    )
    all_points.extend(points)
    if offset is None:
        break
q_pages=[]
q_chunks=[]
for p in all_points:
    payload = p.payload or {}
    meta = payload.get('metadata') or {}
    if meta.get('page'):
        q_pages.append(meta.get('page'))
    if meta.get('chunk_index') is not None:
        q_chunks.append(meta.get('chunk_index'))
print('qdrant collection:', settings.LANGCHAIN_QDRANT_COLLECTION)
print('qdrant_points:', len(all_points), 'q_min_page:', min(q_pages) if q_pages else None, 'q_max_page:', max(q_pages) if q_pages else None, 'q_max_chunk:', max(q_chunks) if q_chunks else None)
print('qdrant last payload samples:')
for p in sorted(all_points, key=lambda x: (x.payload or {}).get('metadata', {}).get('chunk_index', -1))[-5:]:
    payload=p.payload or {}; meta=payload.get('metadata') or {}; text=payload.get('page_content') or payload.get('text') or ''
    print(' page=', meta.get('page'), 'chunk=', meta.get('chunk_index'), 'text=', text[:140].replace('\n',' '))

questions = [
    '???Fe-SMA????????????????',
    '??????????????????????????????80%??????????',
    '80% ???? ??? ?????? ???????',
]
for q in questions:
    print('\nSEARCH:', q)
    try:
        results = search_file_chunks_langchain(q, project_id=file_obj.ID_Project_id, limit=10)
    except Exception as e:
        print('SEARCH_ERROR:', repr(e))
        continue
    for r in results:
        print('score=', round(float(r.get('score') or 0), 4), 'file=', r.get('file_id'), 'page=', r.get('page'), 'chunk=', r.get('chunk_index'), 'name=', r.get('file_name'))
        print((r.get('text') or '')[:260].replace('\n',' '))
        print('---')
