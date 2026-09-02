# Chunk Quality Report

## Overall
- Total chunks: 3458
- File count: 22
- Length min/max/avg: 0 / 1799 / 296.9
- Length p10/p25/p50/p75/p90/p95: 10 / 23 / 127 / 508 / 936 / 955
- Short chunks <100 chars: 1598
- Medium chunks 100-1200 chars: 1849
- Long chunks >1200 chars: 11
- Noise-like chunks: 1292

## Block Types
- pdf_paragraph_semantic: 1875
- pdf_title: 1145
- pdf_table: 336
- pdf_ocr_text_semantic: 73
- paragraph_semantic: 25
- table: 4

## Top Files By Chunk Count
- file_id=65, chunks=651, file=长安镇卫生院异地新建项目.pdf
- file_id=51, chunks=393, file=太河路北延（海关-骆霞线）工程.pdf
- file_id=54, chunks=389, file=巴中市檬子河流域水环境综合治理项目（一期）巴中市檬子河流域水环境综合治理项目（一期）施工标段的招标文件预公示.PDF
- file_id=55, chunks=346, file=嘉兴兴港热网有限公司新海盐汽源段.pdf
- file_id=49, chunks=320, file=双浦第一小学项目.pdf
- file_id=48, chunks=286, file=黄山路西延（小浹江路-富春江路）工程（道路.pdf
- file_id=52, chunks=232, file=镇海清泉路(兆龙路~兴庄路)工程 .pdf
- file_id=62, chunks=196, file=南雅医院二期一批工程-拉杆式悬挑脚手架专项施工方案.pdf
- file_id=59, chunks=171, file=阿克苏诺贝尔过氧化物(宁波)有限公司退役场地地下水修复工程.pdf
- file_id=53, chunks=128, file=镇海区2022年公交候车亭提升改造采购及相关服务.pdf
- file_id=44, chunks=127, file=南通市地方标准-水运工程施工安全管理台账编制导则.pdf
- file_id=61, chunks=90, file=鄞州区JD08-B3、B4地块(江南公路地段)项目Ⅱ标段.pdf
- file_id=45, chunks=29, file=苏州市建设工程施工阶段监理工作检查表.pdf
- file_id=64, chunks=27, file=台金高速公路东延台州市区连接线工程项目.docx
- file_id=58, chunks=26, file=新桂广场•新桂国际工程BIM技术应用施工技术交底记录.pdf
- file_id=46, chunks=18, file=惠安县林口至聚龙道路景观环境综合提升工程勘察设计施工总承包(epc)项目工地会议纪要.pdf
- file_id=43, chunks=11, file=南京市关于2022年施工现场消防安全及高大模板支撑体系专项检查的情况通报.pdf
- file_id=42, chunks=10, file=广州市增城区住房和城乡建设局文件.pdf
- file_id=56, chunks=4, file=四川省房屋建筑和市政工程标准施工招标文件.pdf
- file_id=66, chunks=2, file=长安镇卫生院异地新建项目工程文明施工方案.docx
- file_id=47, chunks=1, file=新丰镇老旧小区品质提升工程(2021年度)设计采购施工总承包(EPC)建设工程质量竣工验收会议纪要.pdf
- file_id=57, chunks=1, file=望江单元SC0401-A33-17、18地块小学建设项目.pdf

## Candidate Selection
- Candidate chunks selected: 1864
- Selection rule: prefer medium-length semantic paragraphs, useful tables, OCR text with enough Chinese content, and chunks containing safety/quality/table terms; avoid pure titles, page numbers, very short fragments, and noisy text.

## Evaluation Dataset v1
- Dataset size: 50
- Covered files: 22
- Question types:
  - safety_management: 15
  - table_lookup: 15
  - quality_supervision: 10
  - fact_lookup: 10
- Source block types:
  - pdf_ocr_text_semantic: 16
  - pdf_table: 15
  - pdf_paragraph_semantic: 15
  - paragraph_semantic: 4

## Notes
- This is a rule-based first draft. relevant_chunks and expected_answer should be reviewed before being used as a formal benchmark.
- The dataset intentionally includes table, OCR, safety, quality, and fact lookup questions to test different RAG failure modes.
