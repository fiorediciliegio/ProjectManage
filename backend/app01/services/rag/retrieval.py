from django.conf import settings


def hybrid_search_file_chunks(question, project_id=None, final_limit=8):
    from app01.services.langchain_rag_service import (
        MODEL_RERANK_CANDIDATE_LIMIT,
        RERANK_CANDIDATE_LIMIT,
        attach_query_metadata,
        generate_multi_search_queries,
        keyword_search_file_chunks,
        reciprocal_rank_fusion,
        rerank_search_results_with_model,
        rule_rerank_search_results,
        search_file_chunks_langchain,
    )

    queries = generate_multi_search_queries(question)
    recall_limit = max(1, int(getattr(settings, 'RAG_MULTI_QUERY_RECALL_LIMIT', 20)))
    result_groups = []

    for query_index, query in enumerate(queries, start=1):
        vector_results = search_file_chunks_langchain(
            question=query,
            project_id=project_id,
            limit=recall_limit,
        )
        keyword_results = keyword_search_file_chunks(
            query=query,
            project_id=project_id,
            limit=recall_limit,
        )
        result_groups.extend([
            ('vector', attach_query_metadata(vector_results, query, query_index)),
            ('keyword', attach_query_metadata(keyword_results, query, query_index)),
        ])

    fused_results = reciprocal_rank_fusion(
        result_groups=result_groups,
        rrf_k=60,
        top_k=RERANK_CANDIDATE_LIMIT,
    )
    rule_reranked_results = rule_rerank_search_results(
        search_results=fused_results,
        question=question,
        top_k=MODEL_RERANK_CANDIDATE_LIMIT,
    )
    return rerank_search_results_with_model(
        question=question,
        search_results=rule_reranked_results,
        top_k=final_limit,
    )
