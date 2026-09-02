# ProjectManage 项目结构说明与收尾整理清单

本文档用于项目收尾、复习和面试讲解。它不改变任何代码，只说明当前目录职责、核心模块位置、存在的结构问题，以及哪些文件适合清理或忽略。

## 1. 总体判断

当前项目不是乱到无法维护，但已经进入“功能复杂度高于目录组织清晰度”的阶段。

优点是顶层前后端分离明确，后端也已经形成 `models / serializers / services / tasks / views` 的基本 Django 分层。问题主要集中在两个大文件：

- `backend/app01/views.py`：接口函数过于集中，包含项目、人员、成本、质量、安全、文件、RAG 等大量接口。
- `backend/app01/services/langchain_rag_service.py`：RAG 相关能力很完整，但文件解析、切分、向量入库、检索、重排、压缩、生成都放在一个文件里。

这不会阻止项目写进简历，但会影响复习效率。如果面试官要求打开代码讲实现，最好提前准备这份模块地图。

## 2. 当前顶层目录

```text
D:\ProjectManage
  backend/                 Django 后端，包含业务接口、RAG、Celery、评测、压测
  frontend/                React 前端
  models/                  本地模型文件目录，通常不应提交到 Git
  docker-compose.yml       Docker 编排入口
  README.md                项目级说明文档
  PROJECT_STRUCTURE.md     当前结构说明与整理清单
```

## 3. 后端目录说明

```text
backend/
  Projectmanagement/       Django 项目配置目录
    settings.py            数据库、Redis、Celery、RAG 参数、缓存、日志等配置
    urls.py                全局路由入口
    celery.py              Celery 应用入口
    asgi.py / wsgi.py      部署入口

  app01/                   主要业务应用
    models.py              数据模型：项目、人员、文件、RAG 会话、审计日志等
    serializers.py         DRF 序列化器
    views.py               业务接口，目前最需要拆分的大文件
    tasks.py               Celery 异步任务，主要包含 RAG 文件入库/删除/取消等
    middleware.py          性能日志中间件
    admin.py               Django Admin 配置
    response.py            统一响应封装
    services/              服务层
      langchain_rag_service.py     RAG 编排入口，仍包含文件解析、入库、检索、生成等主流程
      rag/                         RAG 子模块，已拆出文本工具、Multi-Query 和上下文压缩
        text_utils.py              关键词提取、上下文截断、表格/图注文本识别
        multi_query.py             Multi-Query 生成、查询清洗去重、RRF 融合
        compression.py             保守规则压缩 + LLM 语义压缩
        memory.py                  长对话历史清洗、摘要记忆、查询改写
      elasticsearch_service.py     Elasticsearch / BM25 关键词检索与审计日志索引
      rag_resilience_service.py    RAG 限流、并发槽、熔断、降级
      cache_service.py             Redis API 缓存
      pagination.py                分页工具
    management/commands/   自定义 Django 命令
      rag_queue_snapshot.py        Celery 队列状态查看
      seed_loadtest_user.py        压测用户初始化
    migrations/            数据库迁移文件，应保留并提交

  evaluation/              RAG 评测集、评测脚本和评测报告
  load_tests/              Locust 压测脚本和压测说明
  media/                   用户上传文件，本地运行产物，不应提交
  .venv/                   Python 虚拟环境，不应提交
  .env                     本地真实环境变量，不应提交
  .env.example             环境变量模板，应提交
```

## 4. 前端目录说明

```text
frontend/
  src/
    App.jsx                前端路由与主入口
    common/
      api/client.js        Axios 客户端封装
      pages/               页面级组件
      components/          通用组件和业务组件
      popups/              创建/编辑弹窗
      hooks/               登录、路由、表单、项目参数等 Hooks
      constants/           表单字段、单位、项目/人员/成本常量
      utils/               前端工具函数
  public/                  静态资源
  package.json             前端依赖和脚本
  node_modules/            前端依赖，不应提交
  build/                   前端构建产物，不应提交
```

前端目前最需要关注的是：

- `frontend/src/common/components/FileManager.jsx`：文件管理、入库状态、RAG 问答都集中在这里，后续可拆分。

## 5. RAG 核心链路地图

RAG 主链路集中在：

```text
backend/app01/services/langchain_rag_service.py
```

当前能力包括：

```text
文件解析
-> 文档结构化 block
-> 语义切分
-> 本地 Embedding
-> Qdrant 向量入库
-> Elasticsearch BM25 关键词索引
-> Multi-Query 多路查询
-> Qdrant + BM25 混合检索
-> RRF 融合
-> 规则 rerank
-> 模型 rerank
-> 相邻 chunk 扩展
-> 规则上下文压缩
-> LLM 上下文压缩
-> 长对话记忆
-> 最终回答生成
```

相关配置在：

```text
backend/Projectmanagement/settings.py
backend/.env
backend/.env.example
```

RAG 前端入口主要在：

```text
frontend/src/common/components/FileManager.jsx
```

## 6. 异步与高并发相关模块

```text
backend/app01/tasks.py
```

主要负责：

- 文件异步入库；
- 文件重新入库；
- 删除向量索引；
- 任务取消；
- 失败重试；
- 入库阶段状态记录。

```text
backend/app01/services/rag_resilience_service.py
```

主要负责：

- RAG 问答限流；
- 用户级并发槽；
- 全局并发槽；
- 模型熔断；
- 降级保护。

```text
backend/app01/services/cache_service.py
```

主要负责：

- Redis API 缓存；
- 项目维度缓存版本号；
- 写操作后的缓存失效。

```text
backend/load_tests/
```

主要负责：

- Locust 压测脚本；
- 压测基线记录；
- 后续性能对比。

## 7. 评测相关目录

```text
backend/evaluation/
```

建议按这几类理解：

- `rag_eval_dataset_*.json/jsonl`：RAG 评测集；
- `chunks_export.jsonl`：从向量/文档切片中导出的评测基础数据，文件较大；
- `build_eval_dataset_*.py`：评测集构建脚本；
- `evaluate_rag_official_v1.py`：原始 RAG 评测脚本；
- `compare_rag_variants.py`：RAG 多配置对比评测脚本；
- `analyze_failed_retrieval.py`：失败召回分析脚本；
- `reports/`：评测输出报告。

这部分不算无用，反而是 RAG 项目的亮点。但建议 README 或简历讲解中明确说明它们是“离线评测资产”，否则文件数量会显得多。

## 8. 当前最影响理解的结构问题

### 8.1 `views.py` 过大

问题：

- 所有业务接口集中在一个文件；
- 很难快速定位某个业务模块；
- 面试时不利于体现接口层分模块组织。

建议后续拆成：

```text
app01/views/
  auth_views.py
  project_views.py
  person_views.py
  cost_views.py
  quality_views.py
  safety_views.py
  file_views.py
  rag_views.py
```

低风险做法：先拆 RAG 和文件接口，因为它们现在是项目亮点，复习价值最高。

### 8.2 `langchain_rag_service.py` 仍然偏大

问题：

- 已经拆出 `rag/text_utils.py`、`rag/multi_query.py`、`rag/compression.py`、`rag/memory.py`；
- 主服务文件仍包含文件解析、切分、向量入库、邻居扩展、rerank 和最终生成；
- 后续复习 rerank、入库、生成时仍需要在大文件里上下滚动。

建议后续继续拆成：

```text
app01/services/rag/
  loaders.py          文件解析
  splitters.py        文档切分
  vector_store.py     Qdrant、Embedding、入库、删除
  keyword_store.py    Elasticsearch/BM25，可继续复用 elasticsearch_service.py
  retrieval.py        混合检索主编排、Qdrant/ES 召回聚合
  rerank.py           规则 rerank、模型 rerank
  compression.py      规则压缩、LLM 压缩（已拆）
  memory.py           长对话摘要记忆（已拆）
  generation.py       最终回答生成
```

低风险做法：继续按“拆一块、跑一组测试、提交一次”的节奏推进，优先拆 rerank 和 memory。

### 8.3 `tests.py` 开始变大

建议后续拆成：

```text
app01/tests/
  test_rag_resilience.py
  test_rag_chat_session.py
  test_rag_multi_query.py
  test_rag_compression.py
  test_file_index_tasks.py
```

如果现在不想大动，也可以先保留，因为测试能跑通比目录漂亮更重要。

### 8.4 `FileManager.jsx` 过大

建议后续拆成：

```text
frontend/src/common/components/file-manager/
  FileManager.jsx
  FileUploadPanel.jsx
  FileIndexStatus.jsx
  RagChatPanel.jsx
  RagSessionHeader.jsx
  RagSourceList.jsx
```

这会明显提升你复习前端 RAG 交互的效率。

## 9. 可清理或不应提交的文件/目录

以下一般不应该提交到 Git，已经在 `.gitignore` 中覆盖，或建议确认后清理：

```text
backend/.venv/
backend/.env
backend/.idea/
backend/**/__pycache__/
backend/**/*.pyc
backend/media/
frontend/node_modules/
frontend/build/
frontend/.env.local
models/
*.gguf
*.safetensors
*.bin
*.onnx
*.pt
*.pth
*.ckpt
```

以下是历史临时/无业务文件，当前 Git 状态里已经显示为删除，建议后续确认后提交删除：

```text
backend/tmp_rag_diag.py
backend/tmp_rag_diag_utf8.py
backend/htaccess
```

以下不是无用文件，不建议随便删：

```text
backend/app01/migrations/0026_*.py 到 0032_*.py
backend/app01/services/cache_service.py
backend/app01/services/pagination.py
backend/app01/services/rag_resilience_service.py
backend/app01/middleware.py
backend/app01/management/
backend/evaluation/
backend/load_tests/
backend/requirements-dev.txt
```

这些文件对应你后面加的异步入库、缓存、压测、RAG 评测、限流熔断、长对话记忆等功能，是项目亮点的一部分，应提交。

## 10. 建议的收尾顺序

如果目标是尽快用于简历，不建议现在做大规模重构。建议按这个顺序收尾：

1. 保留当前代码结构，先把 README、PROJECT_STRUCTURE、评测报告整理清楚。
2. 清理并提交临时文件删除项和 `.gitignore`。
3. 确认新增迁移、服务文件、评测脚本、压测脚本都已纳入 Git。
4. 跑一次后端检查、关键测试、前端 build。
5. 已小步拆出 `langchain_rag_service.py` 中的文本工具、Multi-Query、上下文压缩、长对话记忆子模块。
6. 最后再考虑拆 `views.py`，因为它牵涉 URL、导入和接口较多，风险更高。

## 11. 面试讲解建议

可以按下面这条主线讲：

```text
这是一个工程项目管理系统，基础业务包括项目、人员、进度、成本、质量、安全、文件管理。
在文件管理基础上，我扩展了 RAG 文档问答能力。
RAG 部分支持异步入库、混合检索、Multi-Query、rerank、两级上下文压缩、长对话记忆、限流熔断和离线评测。
为了支撑并发和稳定性，我引入 Celery 处理耗时入库任务，引入 Redis 做缓存、限流和熔断状态存储，并用 Locust 做压测基线。
```

如果被问目录结构，可以坦诚说：

```text
项目早期是单 Django app 快速迭代，所以 views.py 和 RAG service 文件偏大。
后期我已经按 services、tasks、evaluation、load_tests 做了功能分层。
如果继续工程化，会优先把 RAG service 拆成 retrieval、rerank、compression、memory、generation 等子模块。
```

这个回答比硬说“结构已经非常完美”更可信。
