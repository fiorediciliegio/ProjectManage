# RAG Evaluation Summary

- Dataset: evaluation\rag_eval_dataset_v2_500.jsonl
- Samples: 500
- With generation: False
- K values: [1, 3, 5, 8]

## Overall Metrics

- recall@1: 0.0544
- precision@1: 0.1200
- hit_rate@1: 0.1200
- ndcg@1: 0.1200
- recall@3: 0.0991
- precision@3: 0.0773
- hit_rate@3: 0.1920
- ndcg@3: 0.1101
- recall@5: 0.1467
- precision@5: 0.0668
- hit_rate@5: 0.2580
- ndcg@5: 0.1244
- recall@8: 0.1831
- precision@8: 0.0510
- hit_rate@8: 0.2940
- ndcg@8: 0.1390

## By Question Type

- safety_management (n=139): recall@1=0.0528, precision@1=0.0719, hit_rate@1=0.0719, ndcg@1=0.0719, recall@3=0.0923, precision@3=0.0432, hit_rate@3=0.1295, ndcg@3=0.0803, recall@5=0.1513, precision@5=0.0460, hit_rate@5=0.2302, ndcg@5=0.1085, recall@8=0.1825, precision@8=0.0351, hit_rate@8=0.2662, ndcg@8=0.1205
- table_lookup (n=133): recall@1=0.0464, precision@1=0.1955, hit_rate@1=0.1955, ndcg@1=0.1955, recall@3=0.0907, precision@3=0.1278, hit_rate@3=0.3008, ndcg@3=0.1449, recall@5=0.1174, precision@5=0.0992, hit_rate@5=0.3383, ndcg@5=0.1318, recall@8=0.1338, precision@8=0.0714, hit_rate@8=0.3684, ndcg@8=0.1409
- quality_supervision (n=100): recall@1=0.0600, precision@1=0.0800, hit_rate@1=0.0800, ndcg@1=0.0800, recall@3=0.1150, precision@3=0.0533, hit_rate@3=0.1600, ndcg@3=0.1028, recall@5=0.1500, precision@5=0.0420, hit_rate@5=0.2000, ndcg@5=0.1191, recall@8=0.1850, precision@8=0.0312, hit_rate@8=0.2300, ndcg@8=0.1310
- fact_lookup (n=48): recall@1=0.1236, precision@1=0.2708, hit_rate@1=0.2708, ndcg@1=0.2708, recall@3=0.2007, precision@3=0.1667, hit_rate@3=0.3333, ndcg@3=0.2301, recall@5=0.3111, precision@5=0.1458, hit_rate@5=0.4792, ndcg@5=0.2686, recall@8=0.4090, precision@8=0.1198, hit_rate@8=0.5417, ndcg@8=0.3095
- cost_contract (n=40): recall@1=0.0125, precision@1=0.0250, hit_rate@1=0.0250, ndcg@1=0.0250, recall@3=0.0375, precision@3=0.0250, hit_rate@3=0.0750, ndcg@3=0.0307, recall@5=0.0750, precision@5=0.0250, hit_rate@5=0.1000, ndcg@5=0.0480, recall@8=0.1000, precision@8=0.0219, hit_rate@8=0.1250, ndcg@8=0.0586
- schedule_plan (n=40): recall@1=0.0312, precision@1=0.0500, hit_rate@1=0.0500, ndcg@1=0.0500, recall@3=0.0500, precision@3=0.0333, hit_rate@3=0.0750, ndcg@3=0.0518, recall@5=0.0938, precision@5=0.0400, hit_rate@5=0.1250, ndcg@5=0.0711, recall@8=0.1562, precision@8=0.0344, hit_rate@8=0.1750, ndcg@8=0.0927

## Output Files

- Detail JSONL: evaluation\reports\v2_500_retrieval\rag_eval_details.jsonl
- Detail CSV: evaluation\reports\v2_500_retrieval\rag_eval_details.csv
- Summary JSON: evaluation\reports\v2_500_retrieval\rag_eval_summary.json
