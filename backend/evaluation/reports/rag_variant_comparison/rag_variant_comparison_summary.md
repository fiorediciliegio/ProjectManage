# RAG Variant Comparison

- Dataset: D:\ProjectManage\backend\evaluation\rag_eval_dataset_official_v1_50.jsonl
- Sample limit: 5
- K values: [1, 3, 5, 8]
- Generation enabled: False
- LLM compression mode: disabled

## Variants

- `single_query_no_compression`: 单查询，无上下文压缩
- `multi_query_no_compression`: Multi-Query，无上下文压缩
- `multi_query_two_stage_compression`: Multi-Query，规则+LLM 两级上下文压缩

## Overall

### single_query_no_compression

- samples: 5
- errors: 0
- candidate_hit_rate@8: 0.2000
- context_hit_rate@8: 0.2000
- context_recall@8: 0.2000
- avg_context_chars: 5240.0
- avg_estimated_context_tokens: 2577.4
- compression_text_ratio: 1.0000
- avg_total_ms: 9916.5

### multi_query_no_compression

- samples: 5
- errors: 0
- candidate_hit_rate@8: 0.2000
- context_hit_rate@8: 0.2000
- context_recall@8: 0.2000
- avg_context_chars: 5240.0
- avg_estimated_context_tokens: 2577.4
- compression_text_ratio: 1.0000
- avg_total_ms: 11255.1

### multi_query_two_stage_compression

- samples: 5
- errors: 0
- candidate_hit_rate@8: 0.2000
- context_hit_rate@8: 0.2000
- context_recall@8: 0.2000
- avg_context_chars: 4042.8
- avg_estimated_context_tokens: 1942.6
- compression_text_ratio: 0.6651
- avg_total_ms: 17302.2

## Output Files

- Detail JSONL: D:\ProjectManage\backend\evaluation\reports\rag_variant_comparison\rag_variant_comparison_details.jsonl
- Detail CSV: D:\ProjectManage\backend\evaluation\reports\rag_variant_comparison\rag_variant_comparison_details.csv
- Summary JSON: D:\ProjectManage\backend\evaluation\reports\rag_variant_comparison\rag_variant_comparison_summary.json
