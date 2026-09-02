# RAG Evaluation Summary

- Dataset: D:\ProjectManage\backend\evaluation\rag_eval_dataset_official_v1_50.jsonl
- Samples: 50
- With generation: False
- K values: [1, 3, 5, 8]

## Overall Metrics

- recall@1: 0.3000
- precision@1: 0.3000
- hit_rate@1: 0.3000
- ndcg@1: 0.3000
- recall@3: 0.4000
- precision@3: 0.1333
- hit_rate@3: 0.4000
- ndcg@3: 0.3579
- recall@5: 0.5000
- precision@5: 0.1000
- hit_rate@5: 0.5000
- ndcg@5: 0.3992
- recall@8: 0.5600
- precision@8: 0.0700
- hit_rate@8: 0.5600
- ndcg@8: 0.4197

## By Question Type

- safety_management (n=15): recall@1=0.2667, precision@1=0.2667, hit_rate@1=0.2667, ndcg@1=0.2667, recall@3=0.3333, precision@3=0.1111, hit_rate@3=0.3333, ndcg@3=0.3000, recall@5=0.4000, precision@5=0.0800, hit_rate@5=0.4000, ndcg@5=0.3287, recall@8=0.6000, precision@8=0.0750, hit_rate@8=0.6000, ndcg@8=0.3972
- table_lookup (n=15): recall@1=0.2667, precision@1=0.2667, hit_rate@1=0.2667, ndcg@1=0.2667, recall@3=0.3333, precision@3=0.1111, hit_rate@3=0.3333, ndcg@3=0.3087, recall@5=0.4000, precision@5=0.0800, hit_rate@5=0.4000, ndcg@5=0.3374, recall@8=0.4000, precision@8=0.0500, hit_rate@8=0.4000, ndcg@8=0.3374
- quality_supervision (n=10): recall@1=0.3000, precision@1=0.3000, hit_rate@1=0.3000, ndcg@1=0.3000, recall@3=0.4000, precision@3=0.1333, hit_rate@3=0.4000, ndcg@3=0.3631, recall@5=0.4000, precision@5=0.0800, hit_rate@5=0.4000, ndcg@5=0.3631, recall@8=0.4000, precision@8=0.0500, hit_rate@8=0.4000, ndcg@8=0.3631
- fact_lookup (n=10): recall@1=0.4000, precision@1=0.4000, hit_rate@1=0.4000, ndcg@1=0.4000, recall@3=0.6000, precision@3=0.2000, hit_rate@3=0.6000, ndcg@3=0.5131, recall@5=0.9000, precision@5=0.1800, hit_rate@5=0.9000, ndcg@5=0.6335, recall@8=0.9000, precision@8=0.1125, hit_rate@8=0.9000, ndcg@8=0.6335

## Output Files

- Detail JSONL: D:\ProjectManage\backend\evaluation\reports\rag_eval_details.jsonl
- Detail CSV: D:\ProjectManage\backend\evaluation\reports\rag_eval_details.csv
- Summary JSON: D:\ProjectManage\backend\evaluation\reports\rag_eval_summary.json
