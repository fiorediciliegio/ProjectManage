# ProjectManage

ProjectManage 是一个面向工程项目管理场景的前后端分离 Web 系统，覆盖项目基础信息、人员分工、计划节点、成本单、质量检查、安全检查、文件资料、操作审计等核心业务，并在文档资料模块中集成 RAG 智能问答能力，用于支持项目资料检索、归纳总结和多轮追问。

项目定位不是单一的 RAG Demo，而是一个带有完整业务模块、权限控制、日志审计、异步任务、缓存优化和工程化 RAG 链路的综合型项目管理系统。

## 核心功能

### 账号、权限与审计

- 支持基于 Django Session 的登录、退出登录和当前用户识别。
- 通过人员档案关联系统账号，区分系统管理员、项目管理员和普通成员。
- 按项目成员关系和角色控制项目、人员、文件、成本、质量、安全等模块的访问和操作权限。
- 对登录、项目维护、人员维护、文件上传/下载/删除、业务数据变更等关键操作记录审计日志。
- 审计日志同步写入 Elasticsearch，支持关键词、模块、操作类型、日期范围检索。

### 项目管理

- 支持项目创建、查询、编辑和删除。
- 管理项目编号、项目名称、项目类型、负责人、预算金额、币种、起止时间、地址和描述。
- 支持项目级导航切换，围绕单个项目组织人员、计划、成本、质量、安全和文档资料。

### 人员管理

- 支持人员信息维护，包括编号、姓名、邮箱、岗位和描述。
- 支持将人员加入项目，形成项目成员关系。
- 支持按人员角色进行项目成员统计和展示。

### 计划节点管理

- 支持为项目维护里程碑节点。
- 管理节点名称、截止时间、描述和完成状态。
- 前端通过时间线展示项目计划推进情况。

### 成本管理

- 支持项目成本单创建、编辑、查看和删除。
- 管理费用类型、预算金额、实际成本、币种、日期、财务人员和备注。
- 支持项目成本总览、费用类型分布、月度成本趋势等统计展示。

### 质量管理

- 支持质量检查模板和检查项配置。
- 支持创建、编辑、查看和删除质量检查报告。
- 支持按项目统计质量检查结果，辅助定位质量管理问题。

### 安全管理

- 支持安全检查模板和检查项配置。
- 支持安全检查报告创建和现场图片上传。
- 支持安全问题列表、问题处理、已处理问题查询和解决方案记录。

### 文件资料管理

- 支持项目文件上传、列表查询、预览、下载和删除。
- 支持 PDF、Word、Excel、文本、图片等多类型文件的内容解析。
- 文件上传、删除、下载等操作会记录审计日志。
- 文件列表支持分页，避免项目文档数量增加后一次性加载过多数据。

### RAG 智能文档问答

- 支持将项目文件解析、切分、向量化并写入 Qdrant。
- 支持文件重新入库、删除文件向量、入库状态查询和任务取消。
- 支持项目范围内的文档问答，回答包含来源片段引用。
- 支持多轮问答，会话可归档在左侧历史栏中，支持新建、切换和删除历史会话。
- 支持长对话摘要记忆：对较早轮次进行摘要沉淀，对近期对话保留原文，用于提升追问和上下文指代理解能力。
- 支持 Multi-Query 多路查询，利用大模型生成多个检索改写问题，提高复杂问法下的召回率。
- 支持向量检索与 Elasticsearch 关键词检索结合，通过 RRF 融合和 rerank 提升检索排序质量。
- 支持上下文压缩检索：先进行保守规则压缩，再通过 LLM 语义压缩提炼片段，降低无关上下文对回答质量的干扰。
- 支持流式回答、模型调用超时控制、输出 token 上限、限流、并发槽、熔断和降级回答。

## 技术栈

### 前端

- React 18
- React Router
- Axios
- Material UI
- MUI X Charts
- Ant Design
- Create React App

### 后端

- Python
- Django 5
- Django REST Framework
- MySQL
- Django Session Auth
- django-cors-headers
- Celery
- Redis

### AI 与检索

- LangChain
- OpenAI-compatible Chat API
- Qwen / DashScope 兼容接口
- 本地 Embedding 服务
- Qdrant 向量数据库
- Elasticsearch / BM25 关键词检索
- RRF 检索结果融合
- 模型 rerank
- Multi-Query
- 长对话摘要记忆
- 上下文压缩检索
- Ragas 评测脚本

### 文档解析

- PyMuPDF
- pdfplumber
- python-docx
- openpyxl
- PaddleOCR

### 工程化

- Docker Compose
- Redis Cache
- Celery 多队列
- API 分页
- 性能日志中间件
- Pytest / Django TestCase
- Locust 压测脚本
- `.env.example` 环境变量模板

## 系统架构

```text
React Frontend
    |
    | Axios / Cookie Session / CSRF
    v
Django REST Backend
    |
    | ORM
    v
MySQL

Django Backend
    |
    | Cache Aside
    v
Redis Cache

Django Backend
    |
    | Celery Dispatch
    v
Redis Broker
    |
    +--> default queue
    +--> rag_index queue
    +--> rag_maintenance queue
            |
            v
       Celery Workers

RAG Pipeline
    |
    +--> File Parser / OCR / Splitter
    +--> Local Embedding Service
    +--> Qdrant Vector Store
    +--> Elasticsearch Keyword Index
    +--> Multi-Query / RRF / Rerank
    +--> Context Compression
    +--> LLM Answer Generation
```

## 目录结构

```text
ProjectManage/
  backend/
    Projectmanagement/        # Django 项目配置
      settings.py             # 数据库、Redis、Celery、RAG、缓存、日志配置
      urls.py                 # 全局路由
      celery.py               # Celery 应用入口
      asgi.py / wsgi.py       # 部署入口
    app01/
      models.py               # 项目、人员、文件、RAG 会话、审计日志等模型
      serializers.py          # DRF 序列化器
      views.py                # 接口兼容导出层
      views_modules/          # 按业务域拆分的接口实现
        common.py
        project_views.py
        person_views.py
        file_views.py
        cost_views.py
        quality_views.py
        safety_views.py
        rag_views.py
      services/
        cache_service.py
        elasticsearch_service.py
        pagination.py
        rag_resilience_service.py
        langchain_rag_service.py
        rag/                  # RAG 子模块
          loaders.py
          file_parsers.py
          pdf_parser.py
          image_parser.py
          splitters.py
          vector_store.py
          retrieval.py
          rerank.py
          multi_query.py
          compression.py
          memory.py
          generation.py
          llm_client.py
      management/commands/
        rag_queue_snapshot.py
        seed_loadtest_user.py
      migrations/
      tasks.py                # Celery 异步任务
      tests.py                # 后端基础测试
    evaluation/
      evaluate_rag_with_ragas.py
    load_tests/               # Locust 压测脚本与基线说明
    requirements.txt
    .env.example
  frontend/
    public/
    src/
      App.jsx
      index.js
      common/
        api/
        components/
        constants/
        hooks/
        pages/
        popups/
        utils/
    package.json
  docker-compose.yml          # Redis / Qdrant / Elasticsearch / Kibana
  PROJECT_STRUCTURE.md
  README.md
```

## 环境变量

后端环境变量模板位于：

```bash
backend/.env.example
```

本地开发时复制为 `.env`：

```bash
cd backend
copy .env.example .env
```

核心配置示例：

```env
DJANGO_SECRET_KEY=replace-with-your-local-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_ENGINE=django.db.backends.mysql
DB_NAME=project_management
DB_USER=root
DB_PASSWORD=replace-with-your-mysql-password
DB_HOST=localhost
DB_PORT=3306

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
CACHE_URL=redis://127.0.0.1:6379/2

EMBEDDING_BASE_URL=http://127.0.0.1:8080/v1
EMBEDDING_MODEL=Qwen3-Embedding-4B-GGUF

DASHSCOPE_API_KEY=replace-with-your-api-key
RAG_CHAT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
RAG_CHAT_MODEL=qwen3.8-max
RAG_RERANK_MODEL=qwen3-rerank
```

真实 `.env`、本地模型、构建产物、上传文件、评测数据和评测报告均已通过 `.gitignore` 忽略，不应提交到 GitHub。

## 本地启动

### 1. 启动基础设施

项目根目录执行：

```bash
docker compose up -d
```

该命令会启动：

- Redis: `127.0.0.1:6379`
- Qdrant: `127.0.0.1:6333`
- Elasticsearch: `127.0.0.1:9200`
- Kibana: `127.0.0.1:5601`

当前 `docker-compose.yml` 主要用于启动中间件服务。MySQL、后端、前端和本地 Embedding 服务按下面步骤分别启动。

### 2. 准备 MySQL

创建数据库：

```sql
CREATE DATABASE project_management DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

然后确认 `backend/.env` 中的 `DB_NAME`、`DB_USER`、`DB_PASSWORD`、`DB_HOST`、`DB_PORT` 与本机 MySQL 配置一致。

### 3. 启动本地 Embedding 服务

RAG 入库需要 OpenAI-compatible Embedding 接口。默认配置为：

```env
EMBEDDING_BASE_URL=http://127.0.0.1:8080/v1
EMBEDDING_MODEL=Qwen3-Embedding-4B-GGUF
```

可以使用 llama.cpp server、兼容 OpenAI Embedding 协议的本地模型服务，或将配置改为其他兼容服务。模型文件建议放在 `models/` 目录，该目录不会提交到 GitHub。

### 4. 启动后端

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

后端接口地址：

```text
http://localhost:8000
```

### 5. 启动 Celery Worker

Windows 本地开发建议使用 `solo` pool。

默认队列：

```bash
cd backend
.\.venv\Scripts\activate
celery -A Projectmanagement worker -l info -Q default -P solo
```

RAG 入库队列：

```bash
cd backend
.\.venv\Scripts\activate
celery -A Projectmanagement worker -l info -Q rag_index -P solo
```

RAG 维护队列：

```bash
cd backend
.\.venv\Scripts\activate
celery -A Projectmanagement worker -l info -Q rag_maintenance -P solo
```

也可以启动一个监听全部队列的 Worker：

```bash
celery -A Projectmanagement worker -l info -Q default,rag_index,rag_maintenance -P solo
```

### 6. 启动前端

```bash
cd frontend
npm install
npm start
```

前端默认访问：

```text
http://localhost:3000
```

前端 Axios 默认请求后端：

```text
http://localhost:8000
```

## RAG 主流程

1. 在项目中上传 PDF、Word、Excel、文本或图片文件。
2. 点击文件入库，后端创建异步任务并将文件状态更新为排队中。
3. Celery Worker 解析文件内容，必要时调用 OCR。
4. 文本被切分为 chunk，并写入 Qdrant 向量库。
5. 同步写入 Elasticsearch，用于关键词检索和混合召回。
6. 用户在项目文档问答区提问。
7. 系统根据历史会话进行问题改写，并通过 Multi-Query 生成多个检索问题。
8. 系统执行向量检索和关键词检索，通过 RRF 融合候选结果。
9. 对候选片段进行 rerank 和上下文压缩。
10. 调用聊天模型生成流式回答，并返回来源引用。
11. 对话消息写入数据库，用户可在左侧历史栏继续查看、切换或删除历史会话。

## RAG 稳定性设计

- **异步入库**：文件解析、OCR、Embedding、向量写入通过 Celery 后台任务执行，避免长任务阻塞 HTTP 请求。
- **任务状态管理**：文件记录包含入库状态、阶段、错误详情、重试次数、任务 ID、取消时间等字段，前端可展示排队中、入库中、失败、完成等状态。
- **任务取消**：支持取消排队中或运行中的 RAG 入库任务，并在任务侧检查取消状态。
- **Celery 多队列**：将默认任务、RAG 入库任务、RAG 维护任务拆到不同队列，为后续资源隔离和独立扩容预留空间。
- **缓存优化**：项目列表、项目详情、节点、成员、成本、文件等读接口支持 Redis Cache Aside 缓存，降低重复查询压力。
- **分页控制**：核心列表接口支持分页和最大页大小限制，避免一次性返回过多数据。
- **限流和并发槽**：RAG 问答链路限制用户级、项目级、全局请求频率，并限制同时进行中的模型调用数量。
- **熔断与降级**：模型调用连续失败时短时间熔断，避免不稳定外部模型拖垮主流程；必要时返回降级结果。
- **超时与 token budget**：对最终回答、Multi-Query、上下文压缩、摘要记忆等不同模型调用设置超时和输出上限，控制延迟与费用。

## 权限说明

项目通过 `Person.sys_role` 和项目成员关系共同判断权限：

- `admin`：系统管理员，可管理项目、人员和系统级数据。
- `project_manager`：项目管理员，可管理负责项目下的关键业务数据。
- `member`：普通成员，只能访问与自身相关或所在项目允许访问的数据。

部分业务模块还会结合岗位字段判断，例如财务、质量、安全、资料等岗位可以负责对应模块操作。

## 测试

后端使用 Django TestCase / SimpleTestCase 编写基础测试。

运行全部后端测试：

```bash
cd backend
.\.venv\Scripts\activate
python manage.py test app01.tests
```

常用快速检查：

```bash
python manage.py check
```

RAG 相关测试覆盖了会话创建、历史消息复用、会话消息查询、会话删除、长对话摘要记忆、上下文压缩、token budget 配置、SQL/检索工具安全边界等关键逻辑。

## 压测

项目包含 Locust 压测脚本和基线说明，位于：

```text
backend/load_tests/
```

可用于观察登录、项目列表、文件列表、RAG 状态查询等接口在并发访问下的响应时间、失败率和瓶颈。

## RAG 评测脚本

项目保留最新 Ragas 评测脚本：

```text
backend/evaluation/evaluate_rag_with_ragas.py
```

评测数据集、评测输出和中间产物不提交到 GitHub。使用时可在本地准备评测集，并配置可用的 OpenAI-compatible LLM 后运行脚本。

## 常见问题

### 1. 后端无法连接 MySQL

检查 MySQL 是否启动，并确认 `backend/.env` 中数据库名、账号、密码、端口正确。Windows 下启动 MySQL 服务可能需要管理员权限。

### 2. 文件入库一直失败

检查 Redis、Celery Worker、Qdrant、Elasticsearch 和本地 Embedding 服务是否都已启动。RAG 入库最常见的依赖是 Embedding 服务和 Qdrant。

### 3. RAG 问答报模型调用错误

检查 `DASHSCOPE_API_KEY`、`RAG_CHAT_BASE_URL`、`RAG_CHAT_MODEL`、账号额度和模型权限。若使用免费额度，可能受到限额、并发或模型可用性的影响。

### 4. Elasticsearch 未启动会影响什么

Elasticsearch 主要用于审计日志搜索和 RAG 关键词检索。若未启动，基础业务仍可使用，但混合检索和日志搜索能力会受影响。

### 5. 前端请求跨域失败

确认 Django 后端运行在 `http://localhost:8000`，并检查 CORS 和 CSRF 配置。前端 Axios 默认携带 Cookie。

## 可扩展方向

- 将 RAG 解析、OCR、Embedding、向量写入进一步拆成 Celery Chain / Chord，增强大批量文件入库能力。
- 增加软删除和会话收藏，完善 RAG 历史会话管理体验。
- 引入更完整的 Metadata Filter，根据文件类型、上传人、时间范围、业务模块过滤检索范围。
- 建立稳定的 RAG 离线评测集，并定期对检索召回、答案相关性、忠实度进行评估。
- 将本地部署升级为完整 Docker Compose 或 Kubernetes 部署，包括 MySQL、后端、前端和 Worker。
- 增加 Prometheus / Grafana 或 OpenTelemetry，完善接口、任务和模型调用可观测性。
- 增加 RBAC 配置后台，让角色权限可以动态配置。

## License

本项目用于学习、作品集展示和实习求职项目演示。
