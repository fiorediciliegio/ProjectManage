# ProjectManage

ProjectManage 是一个面向工程项目管理场景的全栈 Web 系统，覆盖项目基础信息、人员分工、计划节点、成本、质量、安全、文档资料和操作审计等模块，并在文档模块中集成了基于 RAG 的项目资料智能问答能力。

项目由 React 前端、Django 后端、MySQL 数据库、Qdrant 向量库和 Elasticsearch 检索服务组成，适合作为全栈开发、企业管理系统和 AI 应用开发方向的实习作品展示。

## 功能概览

### 用户与权限

- 支持用户登录、退出登录和当前用户状态保持。
- 基于 Django 用户体系关联项目人员信息。
- 按角色控制关键操作权限，包括管理员、项目经理、普通成员，以及项目内的财务、质量、安全、资料等岗位。
- 对项目、人员、成本、质量、安全、文件等关键操作记录审计日志。

### 项目管理

- 创建、查看、编辑和删除项目。
- 管理项目编号、名称、类型、负责人、预算金额、币种、起止时间、地址和描述。
- 支持项目列表、项目详情和项目级导航切换。

### 人员管理

- 创建、查看和删除人员信息。
- 管理人员编号、姓名、邮箱、岗位和描述。
- 支持将人员绑定到具体项目。
- 支持项目人员岗位统计图表。

### 计划节点管理

- 为项目维护里程碑节点。
- 支持节点名称、截止时间、描述和完成状态管理。
- 前端通过时间线展示项目计划进度。
- 支持项目节点状态统计。

### 成本管理

- 为项目创建和维护成本单。
- 管理费用类型、预算金额、实际成本、币种、日期、财务人员和备注。
- 支持成本总览、费用类型占比和月度成本趋势图表。

### 质量管理

- 支持创建质量检查模板和检查项。
- 支持新建、编辑、查看和删除质量检查报告。
- 支持按项目统计质量检查情况。

### 安全管理

- 支持创建安全检查模板和检查项。
- 支持新建安全检查报告，并上传现场图片附件。
- 支持安全问题列表、问题处理和已处理问题查询。
- 支持记录安全问题解决方案。

### 文档资料管理

- 支持项目文件上传、列表展示、预览、下载和删除。
- 支持 PDF、Word、文本、图片等文件的预览或内容提取。
- 上传、预览、下载、删除等操作会写入审计日志。

### 智能文档问答

- 支持将项目文件解析、切分并写入向量库。
- 支持文件重新入库和删除文件向量。
- 支持基于项目范围的文档问答。
- 支持对话历史问题改写、混合检索、rerank、上下文拼接、流式回答和来源引用。

### 审计日志

- 记录用户在系统中的关键操作。
- 支持按关键词、模块、操作类型和日期检索日志。
- 日志数据同步写入 Elasticsearch，便于搜索和分析。

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
- Qdrant
- Elasticsearch
- OpenAI Compatible API
- Qwen 系列模型接口
- 本地 Embedding 服务
- PaddleOCR
- PyMuPDF
- pdfplumber
- python-docx
- openpyxl

### 工程化与基础设施

- Docker Compose
- Redis Docker 服务
- Qdrant Docker 服务
- Elasticsearch Docker 服务
- Kibana Docker 服务
- 环境变量配置

## 系统架构

```text
React Frontend
    |
    | HTTP API / Session Cookie / CSRF
    v
Django Backend
    |
    | ORM
    v
MySQL

Django Backend
    |
    | Celery task dispatch
    v
Redis Broker
    |
    v
Celery Worker
    |
    | long-running jobs
    v
Document Processing / Future Async Jobs

Django Backend
    |
    | 文件解析 / OCR / 文本切分
    v
Document Processing
    |
    +--> Qdrant Vector Store
    |
    +--> Elasticsearch Keyword Index
    |
    +--> LLM Chat / Rerank API
```

## 目录结构

```text
ProjectManage
├── backend
│   ├── Projectmanagement        # Django 项目配置
│   ├── app01                    # 核心业务应用
│   │   ├── models.py            # 数据模型
│   │   ├── serializers.py       # 接口序列化
│   │   ├── views.py             # 业务接口
│   │   └── services             # RAG 与 Elasticsearch 服务
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend
│   ├── public
│   ├── src
│   │   ├── App.jsx
│   │   └── common
│   │       ├── api              # Axios 客户端
│   │       ├── components       # 通用组件
│   │       ├── hooks            # 登录态、路由保护、数据请求
│   │       ├── pages            # 页面模块
│   │       └── popups           # 创建和编辑弹窗
│   └── package.json
├── models                       # 本地模型文件
└── docker-compose.yml           # Redis / Qdrant / Elasticsearch / Kibana
```

## 本地启动

### 1. 启动基础服务

在项目根目录执行：

```bash
docker compose up -d
```

启动后默认服务地址：

- Redis: `redis://127.0.0.1:6379/0`
- Qdrant: `http://127.0.0.1:6333`
- Elasticsearch: `http://127.0.0.1:9200`
- Kibana: `http://127.0.0.1:5601`

### 2. 配置后端环境变量

复制后端环境变量模板：

```bash
cd backend
copy .env.example .env
```

根据本地环境修改 `.env` 中的数据库配置：

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
DB_CONN_MAX_AGE=60
DB_CONN_HEALTH_CHECKS=True
DB_CONNECT_TIMEOUT=5
DB_READ_TIMEOUT=30
DB_WRITE_TIMEOUT=30

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
CACHE_URL=redis://127.0.0.1:6379/2
CACHE_KEY_PREFIX=projectmanage
CACHE_DEFAULT_TIMEOUT=300
API_CACHE_ENABLED=True
API_CACHE_TTL_PROJECT_LIST=60
API_CACHE_TTL_PROJECT_DETAIL=60
API_CACHE_TTL_PROJECT_NODES=30
API_CACHE_TTL_PROJECT_PERSONS=60
API_CACHE_TTL_PROJECT_COSTS=30
API_CACHE_TTL_PROJECT_FILES=10
API_DEFAULT_PAGE_SIZE=50
API_MAX_PAGE_SIZE=100
```

如果需要使用智能文档问答，还需要配置模型和检索相关环境变量：

```env
ELASTICSEARCH_URL=http://127.0.0.1:9200
QDRANT_URL=http://127.0.0.1:6333

EMBEDDING_PROVIDER=llama_cpp
EMBEDDING_BASE_URL=http://127.0.0.1:8080/v1
EMBEDDING_MODEL=Qwen3-Embedding-4B-GGUF

DASHSCOPE_API_KEY=your-api-key
RAG_CHAT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
RAG_CHAT_MODEL=qwen3.6-plus
RAG_RERANK_MODEL=qwen3-rerank
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

后端默认运行在：

```text
http://localhost:8000
```

### 4. 启动 Celery Worker

Celery 用于承载后续文件解析、OCR、Embedding、向量入库等耗时任务，避免这些任务阻塞 Django 请求线程。开发环境可单独打开一个终端执行：

```bash
cd backend
celery -A Projectmanagement worker -l info
```

Windows 本地如果默认进程池启动异常，可以使用 solo pool：

```bash
cd backend
celery -A Projectmanagement worker -l info -P solo
```

当前项目已经配置了按任务类型拆分的 Celery 队列：

- `default`：普通轻量任务，例如健康检查和后续普通后台任务
- `rag_index`：RAG 文件入库任务，包含文件解析、OCR、Embedding、Qdrant 向量写入和 Elasticsearch 关键词索引
- `rag_maintenance`：RAG 维护任务，例如删除文件向量、取消入库后的清理任务

生产或类生产环境建议按队列启动 worker，让长耗时入库任务不要阻塞维护任务：

```bash
cd backend
celery -A Projectmanagement worker -Q default -n default@%h -l info --concurrency=2
celery -A Projectmanagement worker -Q rag_index -n rag_index@%h -l info --concurrency=2 --prefetch-multiplier=1
celery -A Projectmanagement worker -Q rag_maintenance -n rag_maintenance@%h -l info --concurrency=1 --prefetch-multiplier=1
```

Windows 本地可用 `-P solo` 分别启动队列，主要用于验证路由是否正确：

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\celery -A Projectmanagement worker -Q rag_index -n rag_index@%h -P solo --loglevel=INFO
.\.venv\Scripts\celery -A Projectmanagement worker -Q rag_maintenance -n rag_maintenance@%h -P solo --loglevel=INFO
```

### 5. 启动前端

```bash
cd frontend
npm install
npm start
```

前端默认运行在：

```text
http://localhost:3000
```

## 接口模块

后端主要接口包括：

- `/login/`：登录
- `/logout/`：退出登录
- `/current-user/`：获取当前用户
- `/projects/`：项目管理
- `/persons/`：人员管理
- `/project-nodes/`：计划节点管理
- `/projects/<project_id>/costs/`：项目成本管理
- `/projects/<project_id>/quality/templates/`：质量检查模板
- `/projects/<project_id>/quality/reports/`：质量报告
- `/projects/<project_id>/safety/templates/`：安全检查模板
- `/projects/<project_id>/safety/reports/`：安全报告
- `/projects/<project_id>/files/`：项目文件管理
- `/files/<file_id>/rag/index/`：文件入库
- `/files/<file_id>/rag/reindex/`：文件重新入库
- `/files/<file_id>/rag/vectors/`：删除文件向量
- `/projects/<project_id>/rag/chat/`：项目文档问答
- `/audit-logs/search/`：审计日志搜索

## 异步任务基础

当前项目已经接入 Celery + Redis，并已将文件 RAG 入库链路迁移为后台任务：

- Celery 应用入口：`backend/Projectmanagement/celery.py`
- 任务自动发现：`app.autodiscover_tasks()`
- 示例健康检查任务：`backend/app01/tasks.py`
- Redis broker：`CELERY_BROKER_URL`
- Redis result backend：`CELERY_RESULT_BACKEND`
- 异步入库任务：`app01.tasks.rag_index_file_task`
- 异步删除索引任务：`app01.tasks.rag_delete_file_vectors_task`
- 入库任务队列：`CELERY_RAG_INDEX_QUEUE=rag_index`
- 维护任务队列：`CELERY_RAG_MAINTENANCE_QUEUE=rag_maintenance`
- 被快照命令监控的队列：`CELERY_MONITORED_QUEUES=default,rag_index,rag_maintenance`

文件入库状态会持久化到 `File` 表，接口和前端可展示 `未入库 / 排队中 / 入库中 / 正在重试 / 取消中 / 已取消 / 已入库 / 入库失败 / 删除中` 等总状态。后台任务还会记录阶段级进度，例如 `解析文件`、`切分文本`、`连接向量库`、`生成向量`、`写入向量库`、`写入关键词索引` 等。任务失败时会记录失败阶段、异常类型和 traceback 摘要，便于定位 Qdrant、Embedding 服务、Elasticsearch 或文件解析环节的问题。

队列隔离的意义：

- 入库任务属于重任务，可能持续几十秒到几分钟，单独放在 `rag_index`，便于单独扩容或限流
- 删除索引和取消清理属于维护任务，单独放在 `rag_maintenance`，避免被大量入库任务长期堵住
- `CELERY_WORKER_PREFETCH_MULTIPLIER=1` 可减少某个 worker 一次性预取太多任务，避免任务分配不均
- `CELERY_TASK_ACKS_LATE=True` 让 worker 在任务完成后再确认，worker 异常退出时任务更容易被重新投递
- 如本地 Embedding 服务吞吐有限，可设置 `CELERY_RAG_INDEX_RATE_LIMIT=6/m` 之类的速率限制，保护模型服务和向量库

异步入库任务设置了自动重试策略：

- 最大重试次数：`RAG_INDEX_MAX_RETRIES=3`
- 指数退避基准：`RAG_INDEX_RETRY_BASE_DELAY=30`，默认重试间隔为 30 秒、60 秒、120 秒
- 最大退避时间：`RAG_INDEX_RETRY_MAX_DELAY=300`
- 可重试错误：Qdrant、Embedding/OpenAI-compatible、Elasticsearch、HTTP 请求中的连接错误、超时、限流和 5xx 类临时故障
- 不盲目重试：文件不存在、业务逻辑错误、不可恢复的解析错误会直接进入失败状态
- 前端展示：重试次数、最大重试次数、下次重试时间、是否可自动重试

异步入库任务支持取消：

- 取消接口：`POST /files/<file_id>/rag/cancel/`
- 取消方式：先写入数据库取消标记，再调用 Celery `revoke` 阻止未开始任务继续执行
- 运行中任务：采用协作式取消，在文件解析、切分、清理旧索引、生成向量、写入向量库和写入 Elasticsearch 等阶段边界检查取消标记
- 取消清理：任务确认取消后会清理该文件已写入的 Qdrant 向量和 Elasticsearch 关键词索引，避免残留脏数据
- 前端展示：支持选择正在排队、入库或重试的文件并提交取消请求

## 压测基线

项目提供 Locust 压测脚本：`backend/load_tests/locustfile.py`。默认场景只压测登录、项目列表、项目详情、节点列表、人员列表、成本列表、文件列表和 RAG 入库状态查询，不会主动调用 RAG 问答模型，也不会主动提交入库任务，避免消耗模型额度或压垮本地 Embedding 服务。

安装压测依赖：

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
```

创建或刷新本地专用压测账号：

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\python manage.py seed_loadtest_user
```

启动被测服务：

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\python manage.py runserver 8000
```

另开终端运行 100 并发、5 分钟基线压测：

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\python -m locust -f load_tests\locustfile.py --host http://localhost:8000 --headless -u 100 -r 10 -t 5m --csv load_tests\reports\baseline_100u
```

Windows 本地可以用 Waitress 模拟更接近生产的 WSGI 服务，避免只用 Django `runserver` 评估并发能力：

```powershell
cd D:\ProjectManage\backend
$env:DJANGO_DEBUG="False"
$env:PERF_LOG_ENABLED="False"
$env:DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
.\.venv\Scripts\python -m waitress --listen=127.0.0.1:8001 --threads=32 --connection-limit=300 Projectmanagement.wsgi:application
```

另开终端压测 Waitress：

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\python -m locust -f load_tests\locustfile.py --host http://127.0.0.1:8001 --headless -u 100 -r 20 -t 1m --only-summary --csv load_tests\reports\waitress32_100u_1m
```

可选环境变量：

- `PM_LOADTEST_USERNAME`：压测登录用户名，默认 `loadtest_user`
- `PM_LOADTEST_PASSWORD`：压测登录密码，默认 `loadtest123456`
- `PM_LOADTEST_PROJECT_ID`：固定压测某个项目，不设置则自动取项目列表
- `PM_LOADTEST_ENABLE_RAG_CHAT=1`：额外压测 RAG 问答，会消耗远程模型额度
- `PM_LOADTEST_ONLY_RAG_CHAT=1`：只调度 RAG 问答请求，用于观察限流、熔断和降级
- `PM_LOADTEST_RAG_CHAT_TIMEOUT=45`：单次流式问答探测允许的最长时间
- `PM_LOADTEST_ENABLE_RAG_INDEX=1`：额外提交文件入库任务，会占用 Celery、Embedding、Qdrant 和 Elasticsearch 资源
- `PM_LOADTEST_ONLY_RAG_INDEX=1`：只调度 RAG 入库提交和入库状态轮询，用于观察 Celery 队列消费能力
- `PM_LOADTEST_MAX_INDEX_SUBMITS_PER_USER=1`：每个虚拟用户最多提交多少次入库任务
- `PM_LOADTEST_FILE_DISCOVERY_PAGE_SIZE=100`：发现压测文件时单页拉取的文件数量

RAG 入库队列压测示例：

```powershell
cd D:\ProjectManage\backend

# 终端 1：启动 worker。Windows 本地建议先用 solo 跑通链路。
.\.venv\Scripts\celery -A Projectmanagement worker -Q rag_index -n rag_index@%h -P solo --loglevel=INFO

# 终端 1.5：另开一个维护队列 worker，处理删除索引、取消清理等任务。
.\.venv\Scripts\celery -A Projectmanagement worker -Q rag_maintenance -n rag_maintenance@%h -P solo --loglevel=INFO

# 终端 2：启动后端服务。
.\.venv\Scripts\waitress-serve --listen=127.0.0.1:8006 --threads=16 Projectmanagement.wsgi:application

# 终端 3：只压测 RAG 入库提交与状态轮询。
$env:PM_LOADTEST_ENABLE_RAG_INDEX="1"
$env:PM_LOADTEST_ONLY_RAG_INDEX="1"
$env:PM_LOADTEST_PROJECT_ID="3"
$env:PM_LOADTEST_MAX_INDEX_SUBMITS_PER_USER="2"
$env:PM_LOADTEST_FILE_DISCOVERY_PAGE_SIZE="100"
.\.venv\Scripts\locust -f load_tests\locustfile.py --host=http://127.0.0.1:8006 --headless -u 5 -r 1 -t 45s --csv load_tests\reports\rag-index-only
```

压测前后可以查看入库状态和 Celery 队列快照：

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\python manage.py rag_queue_snapshot --skip-celery-inspect
```

说明：`-P solo` 适合 Windows 本地验证，但它基本按顺序处理任务，不适合作为最终吞吐方案。生产环境通常会在 Linux 上用多 worker 进程，并按 `default / rag_index / rag_maintenance` 等队列分别配置并发。后续如果继续深入优化，可以把当前 `rag_index` 里的解析、OCR、Embedding、向量写入继续拆成更细粒度的任务链路。

RAG 问答限流/降级压测示例：

```powershell
cd D:\ProjectManage\backend
$env:PM_LOADTEST_ENABLE_RAG_CHAT="1"
$env:PM_LOADTEST_ONLY_RAG_CHAT="1"
$env:PM_LOADTEST_PROJECT_ID="3"
$env:PM_LOADTEST_RAG_CHAT_TIMEOUT="60"
$env:PM_LOADTEST_RAG_QUESTION="这个项目文件主要讲了什么？"
.\.venv\Scripts\locust -f load_tests\locustfile.py --host=http://127.0.0.1:8006 --headless -u 5 -r 1 -t 60s --csv load_tests\reports\rag-chat
```

Locust 会额外输出 `RAG_LOAD_METRICS_START` 到 `RAG_LOAD_METRICS_END` 之间的指标，例如 `chat.completed`、`chat.degraded`、`chat.rate_limited`、`chat.event.done`，用于判断问答链路是正常回答、降级回答还是被限流保护。

建议先观察这些指标：

- 接口平均响应时间、P95、P99
- 失败率和失败接口
- `GET /projects/:id/files/` 是否明显慢于普通列表接口
- MySQL CPU、连接数和慢查询
- Redis 队列长度
- Celery Worker 是否堆积任务
- Qdrant / Elasticsearch 响应是否抖动

### 性能日志

后端提供轻量级性能日志 middleware，用于压测时定位慢接口和 SQL 查询问题。开发环境默认开启，会对 `/projects/`、`/files/`、`/login/`、`/csrf/` 等接口输出请求耗时、SQL 查询次数、SQL 总耗时和慢 SQL 数量。

可通过环境变量调整：

- `PERF_LOG_ENABLED=True`：是否开启性能日志
- `PERF_SLOW_REQUEST_MS=500`：请求耗时超过该阈值时用 warning 输出
- `PERF_SLOW_QUERY_MS=100`：单条 SQL 超过该阈值时输出 SQL 摘要
- `PERF_QUERY_WARN_COUNT=30`：单个请求 SQL 次数超过该阈值时用 warning 输出
- `PERF_LOG_SAMPLE_RATE=1.0`：采样比例，压测噪声过大时可调成 `0.1`
- `PERF_LOG_PATH_PREFIXES=/projects/,/files/,/login/,/csrf/`：需要观测的接口路径前缀

日志示例：

```text
request method=GET path=/projects/1/files/ status=200 duration_ms=18 db_queries=1 db_time_ms=4 slow_queries=0 user=loadtest_user
```

这类日志适合回答“你怎么定位高并发瓶颈”：先用 Locust 找到 P95/P99 变慢的接口，再用性能日志确认是请求层、SQL 次数、慢 SQL，还是外部服务调用导致的。

### 数据库连接参数

后端默认开启 MySQL 连接复用，减少并发请求下频繁建立数据库连接的成本：

- `DB_CONN_MAX_AGE=60`：每个工作线程中的数据库连接最多复用 60 秒，兼顾复用收益和连接数量控制
- `DB_CONN_HEALTH_CHECKS=True`：复用连接前做健康检查，降低 MySQL 断开空闲连接后出现偶发错误的概率
- `DB_CONNECT_TIMEOUT=5`：连接 MySQL 最多等待 5 秒，避免数据库不可用时请求长时间卡住
- `DB_READ_TIMEOUT=30` / `DB_WRITE_TIMEOUT=30`：读写超时 30 秒，用于限制异常慢查询或网络抖动造成的阻塞时间
- `charset=utf8mb4`：保证中文和特殊字符存储兼容性
- `STRICT_TRANS_TABLES`：让 MySQL 对非法数据更早报错，减少静默截断带来的数据质量问题

注意：Django 的 `CONN_MAX_AGE` 是连接复用，不是完整意义上的数据库连接池。生产环境如果需要更强的连接池能力，通常会结合 Gunicorn/Uvicorn Worker 数量、数据库最大连接数、ProxySQL 或云数据库连接池一起设计。

### 分页和响应大小控制

后端对容易增长的列表接口增加了统一分页，避免项目数据变多后单次请求全量查询、全量序列化、全量传输。

已支持分页的接口：

- `GET /projects/?page=1&page_size=50`
- `GET /projects/<project_id>/nodes/?page=1&page_size=50`
- `GET /projects/<project_id>/persons/?page=1&page_size=50`
- `GET /projects/<project_id>/costs/?page=1&page_size=50`
- `GET /projects/<project_id>/files/?page=1&page_size=50`

响应会保留原来的业务数组字段，例如 `projects`、`files`、`costs`、`persons`、`project_nodes`，同时增加：

```json
{
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 128,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

默认参数：

- `API_DEFAULT_PAGE_SIZE=50`：默认每页 50 条，兼顾前端列表展示和接口响应体大小
- `API_MAX_PAGE_SIZE=100`：最大每页 100 条，防止客户端传入过大的 `page_size` 压垮数据库和序列化层

分页参数会进入 Redis 缓存 key，因此不同页码、不同 page size 会缓存为不同结果。

前端项目列表、全局人员列表、项目人员列表、成本列表、文件列表和计划节点时间线已经接入分页控件，会把页码和每页数量传给后端，避免页面继续依赖一次性拉取全量数据。

### Redis 接口缓存

后端使用 Django 自带 `RedisCache` 缓存高频读接口，默认使用 `redis://127.0.0.1:6379/2`，和 Celery broker/result backend 分开 Redis DB 编号，避免任务队列数据和接口缓存混在一起。

当前缓存的接口：

- `GET /projects/`：项目列表，TTL 60 秒
- `GET /projects/<project_id>/`：项目详情，TTL 60 秒
- `GET /projects/<project_id>/nodes/`：项目节点列表，TTL 30 秒
- `GET /projects/<project_id>/persons/`：项目人员列表，TTL 60 秒
- `GET /projects/<project_id>/costs/`：项目成本列表，TTL 30 秒
- `GET /projects/<project_id>/files/`：项目文件列表，TTL 10 秒

没有缓存 RAG 入库状态接口，因为前端会频繁轮询该接口，状态变化很快；缓存它容易让用户看到滞后的“排队中 / 入库中 / 已完成”。

缓存使用版本号失效策略：项目相关写操作成功后递增缓存版本，新的读请求会生成新 key，旧 key 等待 TTL 自动过期。这样不需要扫描 Redis key，也避免在高并发下做大量删除操作。

会触发缓存失效的操作包括：

- 创建、修改、删除项目
- 创建、修改、删除项目节点
- 添加或移除项目人员
- 创建、修改、删除成本单
- 上传、删除文件
- 文件入库、重新入库、删除向量、取消入库
- Celery 后台入库任务更新文件入库状态

接口响应会带 `X-API-Cache` 响应头，值为 `HIT` 或 `MISS`，用于本地调试和压测观察。

可配置项：

- `CACHE_URL=redis://127.0.0.1:6379/2`
- `CACHE_KEY_PREFIX=projectmanage`
- `API_CACHE_ENABLED=True`
- `API_CACHE_TTL_PROJECT_LIST=60`
- `API_CACHE_TTL_PROJECT_DETAIL=60`
- `API_CACHE_TTL_PROJECT_NODES=30`
- `API_CACHE_TTL_PROJECT_PERSONS=60`
- `API_CACHE_TTL_PROJECT_COSTS=30`
- `API_CACHE_TTL_PROJECT_FILES=10`
- `API_DEFAULT_PAGE_SIZE=50`
- `API_MAX_PAGE_SIZE=100`

### RAG 问答限流、熔断与降级

RAG 问答接口 `POST /projects/<project_id>/rag/chat/` 是高成本接口，会同时消耗 MySQL、Qdrant、Elasticsearch、rerank 模型和回答模型资源。项目对这条链路增加了三层保护：

- 限流：进入问答前先检查 Redis 计数器，限制单用户、单项目和全局请求频率
- 并发槽：限制同时进行的流式问答数量，避免大量长连接占满后端线程和模型服务
- 熔断与降级：rerank 或回答模型连续失败后短时间熔断；rerank 熔断时退回规则排序，回答模型熔断时退回检索结果摘要

默认参数：

- `RAG_CHAT_RATE_LIMIT_ENABLED=True`
- `RAG_CHAT_RATE_WINDOW_SECONDS=60`
- `RAG_CHAT_USER_RATE_LIMIT_PER_MINUTE=12`
- `RAG_CHAT_PROJECT_RATE_LIMIT_PER_MINUTE=60`
- `RAG_CHAT_GLOBAL_RATE_LIMIT_PER_MINUTE=120`
- `RAG_CHAT_USER_MAX_IN_FLIGHT=2`
- `RAG_CHAT_GLOBAL_MAX_IN_FLIGHT=8`
- `RAG_CHAT_IN_FLIGHT_TTL=300`
- `RAG_CHAT_TIMEOUT=45`
- `RAG_CIRCUIT_BREAKER_ENABLED=True`
- `RAG_CHAT_MODEL_CIRCUIT_FAILURE_THRESHOLD=3`
- `RAG_CHAT_MODEL_CIRCUIT_OPEN_SECONDS=60`
- `RAG_RERANK_CIRCUIT_FAILURE_THRESHOLD=3`
- `RAG_RERANK_CIRCUIT_OPEN_SECONDS=60`

参数选择说明：

- 单用户每分钟 12 次：对真实使用已经比较宽松，同时能拦住脚本式高频刷新
- 单用户同时 2 个流式问答：防止一个用户开多个长连接占用线程
- 全局同时 8 个流式问答：适合本地模型和中小型部署的保守默认值，后续应根据压测和模型吞吐上调
- 模型超时 45 秒：给流式回答留出生成时间，但避免外部模型卡死时长期占用请求线程
- 连续失败 3 次熔断 60 秒：适合本地开发和演示，既能快速保护系统，又不会因为一次偶发错误立刻降级

降级行为：

- rerank 模型失败或熔断：保留向量检索 + Elasticsearch 关键词检索 + 规则 rerank 结果
- query rewrite 失败或熔断：使用用户原始问题继续检索
- 回答模型失败或熔断：返回检索结果摘要，并在流式事件中标记 `degraded=true`

## 项目亮点

- 业务完整度较高，不只是单表 CRUD，而是覆盖项目管理中多个核心业务域。
- 前后端分离，包含登录态、CSRF、权限校验、文件上传下载、图表展示和审计日志。
- 文档模块集成 RAG 能力，支持多格式文件解析、OCR、向量检索、关键词检索、rerank 和来源引用。
- 使用 Qdrant 与 Elasticsearch 组合实现混合检索，提高项目资料问答的召回能力。
- 使用 Docker Compose 管理 Redis、Qdrant 与 Elasticsearch 等基础设施，便于本地开发和演示。

## 当前可改进方向

- 补充单元测试和接口测试，提高核心业务的可验证性。
- 将前端接口地址改为环境变量配置，减少硬编码。
- 修复前端 ESLint 警告，保证 CI 环境下生产构建稳定通过。
- 收紧生产环境安全配置，例如关闭 `DEBUG`、限制 CORS 来源、完善密钥管理。
- 增加初始化数据脚本，降低本地演示成本。
- 继续完善异步任务重试、超时告警、任务取消和后台任务管理页面。

## 简历描述参考

```text
企业项目管理与智能文档问答系统
技术栈：React、Django REST Framework、MySQL、Redis、Celery、Qdrant、Elasticsearch、LangChain、PaddleOCR、Docker

- 设计并实现项目、人员、计划节点、成本、质量、安全、文档资料等核心业务模块，支持角色权限控制与操作审计。
- 基于 Qdrant + Elasticsearch 实现项目文档混合检索，支持 PDF、Word、Excel、图片 OCR 等多格式文档解析与入库。
- 接入大模型实现项目文档 RAG 问答，包含问题改写、rerank、上下文拼接、来源引用和流式返回。
- 引入 Celery + Redis 承载文件解析、OCR、Embedding 和向量入库等耗时任务，并实现入库状态持久化、阶段级进度追踪、失败诊断记录和指数退避重试。
```
