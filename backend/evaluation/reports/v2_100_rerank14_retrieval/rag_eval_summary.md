# RAG Evaluation Summary

- Dataset: evaluation\rag_eval_dataset_v2_100_stratified.jsonl
- Samples: 100
- With generation: False
- K values: [1, 3, 5, 8]

## Overall Metrics

- recall@1: 0.0518
- precision@1: 0.1000
- hit_rate@1: 0.1000
- ndcg@1: 0.1000
- recall@3: 0.1115
- precision@3: 0.0767
- hit_rate@3: 0.2000
- ndcg@3: 0.1113
- recall@5: 0.1347
- precision@5: 0.0600
- hit_rate@5: 0.2200
- ndcg@5: 0.1172
- recall@8: 0.1703
- precision@8: 0.0475
- hit_rate@8: 0.2800
- ndcg@8: 0.1327

## By Question Type

- safety_management (n=28): recall@1=0.0714, precision@1=0.0714, hit_rate@1=0.0714, ndcg@1=0.0714, recall@3=0.1250, precision@3=0.0595, hit_rate@3=0.1786, ndcg@3=0.1100, recall@5=0.1429, precision@5=0.0429, hit_rate@5=0.2143, ndcg@5=0.1194, recall@8=0.1964, precision@8=0.0357, hit_rate@8=0.2857, ndcg@8=0.1400
- table_lookup (n=27): recall@1=0.0241, precision@1=0.1111, hit_rate@1=0.1111, ndcg@1=0.1111, recall@3=0.0512, precision@3=0.0741, hit_rate@3=0.1852, ndcg@3=0.0828, recall@5=0.0802, precision@5=0.0667, hit_rate@5=0.2222, ndcg@5=0.0825, recall@8=0.1074, precision@8=0.0556, hit_rate@8=0.2593, ndcg@8=0.0968
- quality_supervision (n=20): recall@1=0.1000, precision@1=0.1500, hit_rate@1=0.1500, ndcg@1=0.1500, recall@3=0.1750, precision@3=0.0833, hit_rate@3=0.2500, ndcg@3=0.1557, recall@5=0.1750, precision@5=0.0500, hit_rate@5=0.2500, ndcg@5=0.1557, recall@8=0.1750, precision@8=0.0312, hit_rate@8=0.2500, ndcg@8=0.1557
- fact_lookup (n=10): recall@1=0.0533, precision@1=0.2000, hit_rate@1=0.2000, ndcg@1=0.2000, recall@3=0.1267, precision@3=0.1667, hit_rate@3=0.3000, ndcg@3=0.1765, recall@5=0.1800, precision@5=0.1400, hit_rate@5=0.3000, ndcg@5=0.1836, recall@8=0.3133, precision@8=0.1250, hit_rate@8=0.6000, ndcg@8=0.2426
- cost_contract (n=8): recall@1=0.0000, precision@1=0.0000, hit_rate@1=0.0000, ndcg@1=0.0000, recall@3=0.0625, precision@3=0.0417, hit_rate@3=0.1250, ndcg@3=0.0383, recall@5=0.1250, precision@5=0.0500, hit_rate@5=0.1250, ndcg@5=0.0713, recall@8=0.1250, precision@8=0.0312, hit_rate@8=0.1250, ndcg@8=0.0713
- schedule_plan (n=7): recall@1=0.0000, precision@1=0.0000, hit_rate@1=0.0000, ndcg@1=0.0000, recall@3=0.1429, precision@3=0.0476, hit_rate@3=0.1429, ndcg@3=0.0901, recall@5=0.1429, precision@5=0.0286, hit_rate@5=0.1429, ndcg@5=0.0901, recall@8=0.1429, precision@8=0.0179, hit_rate@8=0.1429, ndcg@8=0.0901

## Output Files

- Detail JSONL: evaluation\reports\v2_100_rerank14_retrieval\rag_eval_details.jsonl
- Detail CSV: evaluation\reports\v2_100_rerank14_retrieval\rag_eval_details.csv
- Summary JSON: evaluation\reports\v2_100_rerank14_retrieval\rag_eval_summary.json
