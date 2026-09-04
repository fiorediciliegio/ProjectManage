# ProjectManage

ProjectManage 是一个面向工程项目管理场景的前后端分离 Web 系统，覆盖项目基础信息、人员分工、计划节点、成本单、质量检查、安全检查、文件资料、操作审计等核心业务，并在文档资料模块中集成 RAG 智能问答能力，用于支持项目资料检索、归纳总结和多轮追问。

项目不仅包含基础 CRUD 页面，还围绕企业管理系统的典型业务需求实现了权限区分、操作日志、异步任务、Redis 缓存、接口分页、性能日志、RAG 混合检索、上下文压缩、多轮对话记忆、限流熔断和压测脚本等工程化能力。

## 功能概览

### 账号、权限与审计

- 支持基于 Django Session 的登录、退出登录和当前用户识别。
- 通过人员档案关联系统账号，区分系统管理员、项目管理员和普通成员。
- 基于系统角色、项目成员关系和岗位字段控制项目、人员、成本、质量、安全、文件等模块的访问权限。
- 对登录、项目维护、人员维护、文件上传/下载/删除、业务数据变更等关键操作记录审计日志。
- 审计日志同步写入 Elasticsearch，支持关键词、模块、操作类型和日期范围检索。

### 工程项目管理

- 项目管理：支持项目创建、查询、编辑和删除，维护项目编号、名称、类型、负责人、预算、币种、周期、地址和描述。
- 人员管理：支持人员档案维护、项目成员绑定和项目人员岗位统计。
- 计划节点：支持项目里程碑节点维护，并通过时间线展示计划推进情况。
- 成本管理：支持成本单创建、编辑、删除和统计，包含费用类型分布和月度成本趋势。
- 质量管理：支持质量检查模板、检查项和质量检查报告管理。
- 安全管理：支持安全检查模板、安全检查报告、安全问题处理和解决方案记录。
- 文件资料：支持项目文件上传、列表分页、预览、下载、删除和多类型文件内容解析。

### RAG 智能文档问答

- 支持将项目文件解析、结构化切分、语义合并、向量化并写入 Qdrant。
- 支持文件重新入库、删除文件向量、入库状态查询、失败重试和任务取消。
- 支持项目范围内的文档问答，回答包含来源片段引用。
- 支持左侧历史会话栏，提供新建会话、切换历史会话和删除会话能力。
- 支持长对话摘要记忆，将早期对话压缩为摘要记忆，并结合近期原文上下文处理多轮追问。
- 支持 Multi-Query 多路查询，利用大模型生成多个检索改写问题，提高复杂问题召回率。
- 支持向量检索与 Elasticsearch 关键词检索结合，通过 RRF 融合和 rerank 提升候选片段排序质量。
- 支持上下文压缩检索，先进行保守规则压缩，再通过 LLM 语义压缩提炼候选片段。
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
- DashScope Embedding API
- Qdrant 向量数据库
- Elasticsearch / BM25 关键词检索
- RRF 检索结果融合
- 模型 rerank
- Multi-Query
- 长对话摘要记忆
- 上下文压缩检索
- Ragas 评测脚本

### 文档解析与工程化

- PyMuPDF、pdfplumber、python-docx、openpyxl、PaddleOCR
- Docker Compose
- Redis Cache
- Celery 多队列
- API 分页
- 性能日志中间件
- Django TestCase / SimpleTestCase
- Locust 压测脚本

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
    +--> DashScope Embedding API
    +--> Qdrant Vector Store
    +--> Elasticsearch Keyword Index
    +--> Multi-Query / RRF / Rerank
    +--> Context Compression
    +--> LLM Answer Generation
```

## 目录结构

```text
ProjectManage/
├─ backend/                                      # Django 后端：业务接口、数据库模型、RAG、异步任务、测试
│  ├─ Projectmanagement/                         # Django 项目配置目录
│  │  ├─ settings.py                             # 全局配置：数据库、Redis、Celery、缓存、RAG 参数、日志
│  │  ├─ urls.py                                 # 后端 API 路由入口
│  │  ├─ celery.py                               # Celery 应用入口，用于异步任务调度
│  │  ├─ asgi.py                                 # ASGI 部署入口
│  │  └─ wsgi.py                                 # WSGI 部署入口
│  │
│  ├─ app01/                                     # 核心业务应用
│  │  ├─ models.py                               # 数据模型：项目、人员、文件、成本、质量、安全、RAG 会话、审计日志
│  │  ├─ serializers.py                          # DRF 序列化器，负责模型与接口 JSON 数据转换
│  │  ├─ views.py                                # 兼容导出层，统一暴露拆分后的接口函数
│  │  ├─ response.py                             # 统一接口响应封装
│  │  ├─ middleware.py                           # 性能日志中间件，记录请求耗时、SQL 数量、慢查询
│  │  ├─ tasks.py                                # Celery 异步任务：RAG 入库、删除向量、取消任务等
│  │  ├─ tests.py                                # 后端测试：权限、RAG 会话、限流、压缩、token 参数等
│  │  │
│  │  ├─ views_modules/                          # 接口层按业务域拆分
│  │  │  ├─ common.py                            # 登录、权限校验、审计日志、公共工具函数
│  │  │  ├─ project_views.py                     # 项目与计划节点接口
│  │  │  ├─ person_views.py                      # 人员与项目成员接口
│  │  │  ├─ file_views.py                        # 文件上传、预览、下载、删除接口
│  │  │  ├─ cost_views.py                        # 成本单接口与成本统计
│  │  │  ├─ quality_views.py                     # 质量模板、质量报告、质量统计接口
│  │  │  ├─ safety_views.py                      # 安全模板、安全报告、问题处理接口
│  │  │  └─ rag_views.py                         # RAG 入库、状态查询、多轮问答、历史会话接口
│  │  │
│  │  ├─ services/                               # 服务层：复用业务逻辑与外部系统访问
│  │  │  ├─ cache_service.py                     # Redis 缓存封装，支持 Cache Aside 和缓存失效
│  │  │  ├─ elasticsearch_service.py             # Elasticsearch 索引、关键词检索、审计日志搜索
│  │  │  ├─ pagination.py                        # 通用分页工具
│  │  │  ├─ rag_resilience_service.py            # RAG 限流、并发槽、熔断、降级保护
│  │  │  ├─ langchain_rag_service.py             # RAG 兼容导出层，保留旧调用入口
│  │  │  │
│  │  │  └─ rag/                                 # RAG 核心能力模块
│  │  │     ├─ loaders.py                        # 文件加载与解析入口
│  │  │     ├─ file_parsers.py                   # Word、Excel、文本等文件解析
│  │  │     ├─ pdf_parser.py                     # PDF 正文、表格、扫描页 OCR 解析
│  │  │     ├─ image_parser.py                   # 图片 OCR 解析
│  │  │     ├─ splitters.py                      # 超长文本递归切分兜底
│  │  │     ├─ semantic_chunking.py              # Embedding 语义合并、标题强制切分、表格独立处理
│  │  │     ├─ embeddings.py                     # DashScope Embedding 客户端适配
│  │  │     ├─ vector_store.py                   # Embedding、Qdrant 向量写入与删除
│  │  │     ├─ retrieval.py                      # 混合检索主流程：向量检索、关键词检索、RRF 融合
│  │  │     ├─ rerank.py                         # 规则 rerank 与模型 rerank
│  │  │     ├─ multi_query.py                    # Multi-Query 多路查询生成与去重
│  │  │     ├─ compression.py                    # 保守规则压缩 + LLM 上下文压缩
│  │  │     ├─ memory.py                         # 长对话摘要记忆与历史问题改写
│  │  │     ├─ generation.py                     # 最终回答生成、流式输出、来源引用整理
│  │  │     ├─ llm_client.py                     # OpenAI-compatible LLM 客户端封装
│  │  │     └─ http_clients.py                   # 外部 HTTP 调用封装，统一处理代理与超时
│  │  │
│  │  ├─ management/commands/                    # 自定义 Django 命令
│  │  │  ├─ rag_queue_snapshot.py                # 查看 Celery / RAG 队列状态
│  │  │  └─ seed_loadtest_user.py                # 初始化压测用户
│  │  │
│  │  └─ migrations/                             # 数据库迁移文件
│  │
│  ├─ evaluation/                                # RAG 离线评测脚本目录
│  │  └─ evaluate_rag_with_ragas.py              # Ragas 评测脚本
│  │
│  ├─ load_tests/                                # Locust 压测脚本与压测基线说明
│  ├─ Dockerfile                                 # 后端容器镜像定义
│  ├─ docker-entrypoint.sh                       # 后端容器启动脚本：等待 MySQL 并执行迁移
│  ├─ requirements.txt                           # Python 依赖
│  ├─ manage.py                                  # Django 命令入口
│  └─ .env.example                               # 后端环境变量模板
│
├─ frontend/                                     # React 前端
│  ├─ public/                                    # 静态资源
│  ├─ src/
│  │  ├─ App.jsx                                 # 前端路由与页面入口
│  │  ├─ index.js                                # React 应用挂载入口
│  │  ├─ index.css                               # 全局样式
│  │  └─ common/
│  │     ├─ api/                                 # Axios 客户端与 CSRF 处理
│  │     ├─ components/                          # 通用组件：表格、图表、导航栏、文件管理、RAG 问答
│  │     ├─ constants/                           # 项目、人员、成本等模块字段配置
│  │     ├─ hooks/                               # 登录态、路由保护、数据请求、自定义 Hook
│  │     ├─ pages/                               # 页面模块：项目、人员、成本、质量、安全、文档、日志
│  │     ├─ popups/                              # 创建和编辑弹窗组件
│  │     └─ utils/                               # 前端工具函数
│  ├─ Dockerfile                                 # 前端生产构建镜像定义
│  ├─ nginx.conf                                 # 前端 Nginx 静态资源服务配置
│  └─ package.json                               # 前端依赖与启动脚本
│
├─ docker-compose.yml                            # MySQL、Redis、Qdrant、Elasticsearch、后端、Worker、前端编排
├─ README.md                                     # 项目说明文档
└─ .gitignore                                    # Git 忽略规则
```

## RAG 核心链路地图

RAG 主链路由 `backend/app01/services/langchain_rag_service.py` 保持兼容入口，核心能力拆分到 `backend/app01/services/rag/` 下的多个子模块。

```text
文件上传
-> 文件解析
-> 文档结构化 block
-> 标题/章节 metadata 补强
-> 规则语义合并
-> Embedding 相似度语义合并
-> 超长文本递归切分兜底
-> DashScope Embedding
-> Qdrant 向量入库
-> Elasticsearch BM25 关键词索引
-> Multi-Query 多路查询
-> Qdrant + BM25 混合检索
-> RRF 融合
-> 规则 rerank
-> 模型 rerank
-> 相邻 chunk 扩展
-> 保守规则上下文压缩
-> LLM 语义上下文压缩
-> 长对话摘要记忆
-> 最终回答生成
-> 流式返回答案与来源引用
```

核心模块职责：

- `loaders.py`：统一文件加载入口，调度不同类型文件解析器。
- `file_parsers.py`：处理 Word、Excel、文本等结构化或半结构化文件。
- `pdf_parser.py`：处理 PDF 正文、表格、页眉页脚和扫描页 OCR。
- `image_parser.py`：处理图片 OCR。
- `splitters.py`：根据文档类型和文本结构对超长文本执行递归切分兜底。
- `semantic_chunking.py`：基于标题强制切分、表格独立处理和 Embedding 相似度进行短段落语义合并。
- `embeddings.py`：封装 DashScope Embedding 客户端，供语义切分和向量入库复用。
- `vector_store.py`：封装 Embedding、Qdrant collection 创建、向量写入、向量删除和向量查询。
- `retrieval.py`：编排向量检索、关键词检索、多路召回和 RRF 融合。
- `rerank.py`：执行规则 rerank、模型 rerank 和分数融合。
- `multi_query.py`：生成多路查询问题，并对查询结果做去重与融合。
- `compression.py`：执行保守规则压缩和 LLM 语义压缩。
- `memory.py`：维护长对话摘要记忆，并根据历史上下文改写追问。
- `generation.py`：生成最终回答，组织来源引用，并在异常时返回降级结果。
- `llm_client.py`：创建 OpenAI-compatible 聊天模型客户端。
- `http_clients.py`：统一封装外部 HTTP 调用的代理、超时与客户端配置。

## RAG 稳定性设计

- **异步入库**：文件解析、OCR、Embedding、向量写入通过 Celery 后台任务执行，避免长任务阻塞 HTTP 请求。
- **任务状态管理**：文件记录包含入库状态、阶段、错误详情、重试次数、任务 ID、取消时间等字段，前端可展示排队中、入库中、失败、完成等状态。
- **任务取消**：支持取消排队中或运行中的 RAG 入库任务，并在任务侧检查取消状态。
- **Celery 多队列**：将默认任务、RAG 入库任务、RAG 维护任务拆到不同队列，为资源隔离和独立扩容预留空间。
- **缓存优化**：项目列表、项目详情、节点、成员、成本、文件等读接口支持 Redis Cache Aside 缓存，降低重复查询压力。
- **分页控制**：核心列表接口支持分页和最大页大小限制，避免一次性返回过多数据。
- **限流和并发槽**：RAG 问答链路限制用户级、项目级、全局请求频率，并限制同时进行中的模型调用数量。
- **熔断与降级**：模型调用连续失败时短时间熔断，避免不稳定外部模型持续影响主流程；必要时返回降级结果。
- **超时与 token budget**：对最终回答、Multi-Query、上下文压缩、摘要记忆等不同模型调用设置超时和输出上限，控制延迟与调用成本。

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

ELASTICSEARCH_REQUEST_TIMEOUT=20
ELASTICSEARCH_MAX_RETRIES=2
ELASTICSEARCH_BULK_CHUNK_SIZE=100
ELASTICSEARCH_BULK_REQUEST_TIMEOUT=60
RAG_KEYWORD_INDEX_REQUIRED=False

EMBEDDING_PROVIDER=dashscope
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=qwen3.7-text-embedding
EMBEDDING_DIMENSIONS=1024
RAG_SEMANTIC_CHUNKING_ENABLED=True
RAG_SEMANTIC_CHUNKING_SIMILARITY_THRESHOLD=0.62
RAG_SEMANTIC_CHUNKING_SHORT_MERGE_MIN_SIMILARITY=0.5

DASHSCOPE_API_KEY=replace-with-your-api-key
RAG_CHAT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
RAG_CHAT_MODEL=qwen3.8-max
RAG_RERANK_MODEL=qwen3-rerank
```

`.env` 用于本地真实环境变量，评测数据和运行报告可按需在本地生成；这些运行期资产通过 `.gitignore` 与源码分离管理。

## Docker Compose 一键启动

完整 Docker Compose 部署包含 MySQL、Redis、Qdrant、Elasticsearch、Kibana、Django Backend、Celery Worker 和 React Frontend / Nginx。

### 1. 配置可选环境变量

Compose 文件已经提供了本地默认值，也可以在项目根目录创建 `.env` 覆盖关键配置：

```env
MYSQL_ROOT_PASSWORD=projectmanage123456
MYSQL_DATABASE=project_management
MYSQL_HOST_PORT=3307
DJANGO_SECRET_KEY=replace-with-your-secret-key
DJANGO_DEBUG=True

DASHSCOPE_API_KEY=replace-with-your-api-key
RAG_CHAT_MODEL=qwen3.8-max
RAG_RERANK_MODEL=qwen3-rerank

ELASTICSEARCH_REQUEST_TIMEOUT=20
ELASTICSEARCH_MAX_RETRIES=2
ELASTICSEARCH_BULK_CHUNK_SIZE=100
ELASTICSEARCH_BULK_REQUEST_TIMEOUT=60
RAG_KEYWORD_INDEX_REQUIRED=False

EMBEDDING_PROVIDER=dashscope
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=qwen3.7-text-embedding
EMBEDDING_DIMENSIONS=1024
RAG_SEMANTIC_CHUNKING_ENABLED=True
RAG_SEMANTIC_CHUNKING_SIMILARITY_THRESHOLD=0.62
RAG_SEMANTIC_CHUNKING_SHORT_MERGE_MIN_SIMILARITY=0.5
```

Embedding 与回答模型共用 `DASHSCOPE_API_KEY`，也可以通过 `EMBEDDING_API_KEY` 单独覆盖 Embedding 调用凭据。

### 2. 启动全部服务

```bash
docker compose up -d --build
```

首次启动时，后端容器会等待 MySQL 就绪，然后自动执行数据库迁移：

```bash
python manage.py migrate --noinput
```

### 3. 访问服务

- 前端页面：`http://localhost:3000`
- 后端接口：`http://localhost:8000`
- MySQL：`127.0.0.1:3307`
- Redis：`127.0.0.1:6379`
- Qdrant：`http://127.0.0.1:6333`
- Elasticsearch：`http://127.0.0.1:9200`
- Kibana：`http://127.0.0.1:5601`

### 4. 查看日志与停止服务

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f celery_worker
docker compose down
```

如需同时删除容器数据卷：

```bash
docker compose down -v
```

## 本地开发启动

本地开发模式适合直接在 Windows 上启动后端和前端，同时使用 Docker 启动 MySQL、Redis、Qdrant、Elasticsearch 等基础服务。

### 1. 启动基础服务

```bash
docker compose up -d mysql redis qdrant elasticsearch kibana
```

如果使用 Compose 中的 MySQL，本机连接端口默认为 `3307`，对应后端 `.env` 中的配置为：

```env
DB_HOST=localhost
DB_PORT=3307
```

### 2. 启动后端

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

### 3. 启动 Celery Worker

Windows 本地开发建议使用 `solo` pool。

```bash
cd backend
.\.venv\Scripts\activate
celery -A Projectmanagement worker -l info -Q default,rag_index,rag_maintenance -P solo
```

也可以按队列拆分启动多个 Worker：

```bash
celery -A Projectmanagement worker -l info -Q default -P solo
celery -A Projectmanagement worker -l info -Q rag_index -P solo
celery -A Projectmanagement worker -l info -Q rag_maintenance -P solo
```

### 4. 启动前端

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

## RAG 使用流程

1. 在项目中上传 PDF、Word、Excel、文本或图片文件。
2. 点击文件入库，后端创建异步任务并将文件状态更新为排队中。
3. Celery Worker 解析文件内容，必要时调用 OCR。
4. 文本被切分为 chunk，并写入 Qdrant 向量库。
5. 同步写入 Elasticsearch，用于关键词检索和混合召回；本地部署中如果 Elasticsearch 短暂不可用，系统会优先保证 Qdrant 向量入库完成，并记录关键词索引跳过信息。
6. 用户在项目文档问答区提问。
7. 系统根据历史会话进行问题改写，并通过 Multi-Query 生成多个检索问题。
8. 系统执行向量检索和关键词检索，通过 RRF 融合候选结果。
9. 对候选片段进行 rerank 和上下文压缩。
10. 调用聊天模型生成流式回答，并返回来源引用。
11. 对话消息写入数据库，用户可在左侧历史栏继续查看、切换或删除历史会话。

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

RAG 相关测试覆盖了会话创建、历史消息复用、会话消息查询、会话删除、长对话摘要记忆、上下文压缩、token budget 配置、限流熔断等关键逻辑。

## 压测

项目包含 Locust 压测脚本和基线说明，位于：

```text
backend/load_tests/
```

可用于观察登录、项目列表、文件列表、RAG 状态查询等接口在并发访问下的响应时间、失败率和瓶颈。

## RAG 评测

项目保留 Ragas 评测脚本：

```text
backend/evaluation/evaluate_rag_with_ragas.py
```

评测脚本用于在准备评测集和可用 OpenAI-compatible LLM 后，对 RAG 检索与回答质量进行离线评估。

## 可扩展方向

- 将 RAG 解析、OCR、Embedding、向量写入进一步拆成 Celery Chain / Chord，增强大批量文件入库能力。
- 增加软删除、会话收藏和会话搜索，完善 RAG 历史会话管理体验。
- 引入更完整的 Metadata Filter，根据文件类型、上传人、时间范围、业务模块过滤检索范围。
- 建立稳定的 RAG 离线评测集，并定期对检索召回、答案相关性、忠实度进行评估。
- 增加 Kubernetes 部署配置和生产环境观测能力。
- 增加 Prometheus / Grafana 或 OpenTelemetry，完善接口、任务和模型调用可观测性。
- 增加 RBAC 配置后台，让角色权限可以动态配置。
