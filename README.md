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

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
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

当前项目已经接入 Celery + Redis 基座：

- Celery 应用入口：`backend/Projectmanagement/celery.py`
- 任务自动发现：`app.autodiscover_tasks()`
- 示例健康检查任务：`backend/app01/tasks.py`
- Redis broker：`CELERY_BROKER_URL`
- Redis result backend：`CELERY_RESULT_BACKEND`

第一阶段只完成任务队列基础设施接入，尚未把业务接口迁移到后台任务。下一阶段建议优先把文件向量入库、重新入库、删除向量迁移为 Celery 任务。

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
- 将文件向量入库、OCR、Embedding 等耗时操作迁移到 Celery 异步任务，增加任务状态追踪和失败重试。

## 简历描述参考

```text
企业项目管理与智能文档问答系统
技术栈：React、Django REST Framework、MySQL、Redis、Celery、Qdrant、Elasticsearch、LangChain、PaddleOCR、Docker

- 设计并实现项目、人员、计划节点、成本、质量、安全、文档资料等核心业务模块，支持角色权限控制与操作审计。
- 基于 Qdrant + Elasticsearch 实现项目文档混合检索，支持 PDF、Word、Excel、图片 OCR 等多格式文档解析与入库。
- 接入大模型实现项目文档 RAG 问答，包含问题改写、rerank、上下文拼接、来源引用和流式返回。
- 引入 Celery + Redis 异步任务基础设施，为文件解析、OCR、Embedding 和向量入库等耗时任务队列化处理预留工程能力。
```
