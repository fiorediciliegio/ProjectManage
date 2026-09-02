# ProjectManage RAG Evaluation Dataset official_v1_50

## 基本信息

- 数据集版本：official_v1_50
- 样本数量：50
- 覆盖文件数：22
- 适用任务：RAG 检索评估与生成评估
- 数据状态：正式评估集，可用于后续自动评估脚本

## 文件说明

- rag_eval_dataset_official_v1_50.jsonl：推荐给评估脚本读取，一行一条样本
- rag_eval_dataset_official_v1_50.json：带数据集元信息的完整 JSON 文件
- rag_eval_dataset_v1_50.jsonl：第一版草稿，保留作为来源版本

## 题型分布

- safety_management: 15
- table_lookup: 15
- quality_supervision: 10
- fact_lookup: 10

## 难度分布

- medium: 42
- easy: 8

## 来源 Chunk 类型

- pdf_ocr_text_semantic: 16
- pdf_table: 15
- pdf_paragraph_semantic: 15
- paragraph_semantic: 4

## 覆盖文件

- 南京市关于2022年施工现场消防安全及高大模板支撑体系专项检查的情况通报.pdf: 3
- 苏州市建设工程施工阶段监理工作检查表.pdf: 3
- 惠安县林口至聚龙道路景观环境综合提升工程勘察设计施工总承包(epc)项目工地会议纪要.pdf: 3
- 镇海区2022年公交候车亭提升改造采购及相关服务.pdf: 3
- 巴中市檬子河流域水环境综合治理项目（一期）巴中市檬子河流域水环境综合治理项目（一期）施工标段的招标文件预公示.PDF: 3
- 嘉兴兴港热网有限公司新海盐汽源段.pdf: 3
- 新桂广场•新桂国际工程BIM技术应用施工技术交底记录.pdf: 3
- 南雅医院二期一批工程-拉杆式悬挑脚手架专项施工方案.pdf: 3
- 广州市增城区住房和城乡建设局文件.pdf: 2
- 南通市地方标准-水运工程施工安全管理台账编制导则.pdf: 2
- 黄山路西延（小浹江路-富春江路）工程（道路.pdf: 2
- 双浦第一小学项目.pdf: 2
- 太河路北延（海关-骆霞线）工程.pdf: 2
- 镇海清泉路(兆龙路~兴庄路)工程 .pdf: 2
- 四川省房屋建筑和市政工程标准施工招标文件.pdf: 2
- 阿克苏诺贝尔过氧化物(宁波)有限公司退役场地地下水修复工程.pdf: 2
- 鄞州区JD08-B3、B4地块(江南公路地段)项目Ⅱ标段.pdf: 2
- 台金高速公路东延台州市区连接线工程项目.docx: 2
- 长安镇卫生院异地新建项目.pdf: 2
- 长安镇卫生院异地新建项目工程文明施工方案.docx: 2
- 新丰镇老旧小区品质提升工程(2021年度)设计采购施工总承包(EPC)建设工程质量竣工验收会议纪要.pdf: 1
- 望江单元SC0401-A33-17、18地块小学建设项目.pdf: 1

## 推荐评估指标

- 检索环节：Recall@K、Precision@K、HitRate@K、NDCG@K
- 生成环节：Faithfulness、Answer Relevance、Context Relevance、Citation Accuracy

## 字段说明

- id：评估样本编号
- question：用户问题
- question_type：问题类型
- expected_answer：参考答案
- relevant_chunks：正式标注的相关 chunk，可用于召回率、命中率和 NDCG 评估
- metadata.evaluation_focus：该样本重点观察的评估指标

## 使用建议

- 先用 relevant_chunks 评估检索结果是否命中正确片段。
- 再用 expected_answer 与模型答案评估答案相关性和忠实度。
- 对于要求引用来源的回答，可以检查模型引用的 chunk 是否落在 relevant_chunks 内。
