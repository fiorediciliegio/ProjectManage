# ProjectManage Load Test Baseline

This document records the local baseline collected on 2026-08-31.

## Scope

- Target: local Django development server, `http://localhost:8000`
- Tool: Locust
- Scenario: login, project list, project detail, node list, person list, cost list, file list, and RAG index status query
- Excluded by default: RAG chat and RAG indexing submission
- Test account: `loadtest_user`

The current baseline is intended to find hot endpoints and regressions during local development. It is not a production-capacity benchmark because Django `runserver` is not a production WSGI/ASGI server.

## Key Finding

The first smoke test exposed `GET /projects/:id/files/` as the dominant bottleneck. It took 3.3s to 5.4s for a single authenticated user because the file list endpoint synchronously queried Qdrant through `get_indexed_file_ids(project_id)` on every request.

The hot path was changed to read the persisted MySQL index status instead. After the change, the same endpoint returned in about 18ms in the authenticated smoke test.

## Commands

Install development dependencies:

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
```

Create or refresh the local load test account:

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\python manage.py seed_loadtest_user
```

Run a smoke test:

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\python -m locust -f load_tests\locustfile.py --host http://localhost:8000 --headless -u 1 -r 1 -t 20s --csv load_tests\reports\smoke_1u
```

Run the 100-user baseline:

```powershell
cd D:\ProjectManage\backend
.\.venv\Scripts\python -m locust -f load_tests\locustfile.py --host http://localhost:8000 --headless -u 100 -r 20 -t 1m --only-summary --csv load_tests\reports\baseline_100u_1m
```

## Result Summary

### 20 Users, 1 Minute

- Requests: 835
- Failures: 0
- Throughput: 14.54 req/s
- Aggregate median: 15ms
- Aggregate P95: 36ms
- Slow setup endpoints:
  - `GET /csrf/`: avg 2072ms
  - `POST /login/`: avg 1080ms
- Main business endpoint P95 values:
  - `GET /projects/`: 20ms
  - `GET /projects/:id/`: 18ms
  - `GET /projects/:id/files/`: 25ms
  - `GET /projects/:id/costs/`: 26ms
  - `GET /projects/:id/persons/`: 23ms
  - `GET /files/:id/rag/status/`: 29ms

### 100 Users, 1 Minute

- Requests: 3993
- Failures: 0
- Throughput: 69.67 req/s
- Aggregate median: 21ms
- Aggregate P95: 1200ms
- Aggregate P95 is dominated by one-time session setup endpoints:
  - `GET /csrf/`: avg 2355ms, P95 3000ms
  - `POST /login/`: avg 1743ms, P95 2700ms
- Main business endpoint P95 values:
  - `GET /projects/`: 70ms
  - `GET /projects/:id/`: 56ms
  - `GET /projects/:id/files/`: 61ms
  - `GET /projects/:id/costs/`: 83ms
  - `GET /projects/:id/nodes/`: 72ms
  - `GET /projects/:id/persons/`: 57ms
  - `GET /files/:id/rag/status/`: 210ms

### Waitress 32 Threads, 100 Users, 1 Minute

This run used a warmed local Waitress WSGI server:

```powershell
cd D:\ProjectManage\backend
$env:DJANGO_DEBUG="False"
$env:PERF_LOG_ENABLED="False"
$env:DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
.\.venv\Scripts\python -m waitress --listen=127.0.0.1:8001 --threads=32 --connection-limit=300 Projectmanagement.wsgi:application
```

Results:

- Requests: 4091
- Failures: 0
- Throughput: 68.79 req/s
- Aggregate median: 21ms
- Aggregate P95: 340ms
- Slow setup endpoint:
  - `POST /login/`: avg 1670ms, P95 2200ms
- Main business endpoint P95 values:
  - `GET /projects/`: 56ms
  - `GET /projects/:id/`: 160ms
  - `GET /projects/:id/files/`: 140ms
  - `GET /projects/:id/costs/`: 120ms
  - `GET /projects/:id/nodes/`: 89ms
  - `GET /projects/:id/persons/`: 140ms
  - `GET /files/:id/rag/status/`: 110ms

Compared with Django `runserver`, the warmed Waitress run kept the same zero failure rate and similar throughput, while aggregate P95 dropped from 1200ms to 340ms. The remaining tail latency is mainly caused by concurrent login and short bursts during user startup.

Waitress also emitted `Task queue depth` warnings during the 100-user burst, confirming that requests queued behind the server worker thread pool during startup. This makes thread-pool sizing, database connection management, and login burst control the next backend-concurrency concerns.

### After Django MySQL Connection Reuse

The Django MySQL connection settings were changed to reuse healthy database connections:

- `DB_CONN_MAX_AGE=60`
- `DB_CONN_HEALTH_CHECKS=True`
- `DB_CONNECT_TIMEOUT=5`
- `DB_READ_TIMEOUT=30`
- `DB_WRITE_TIMEOUT=30`

Waitress 32 threads, 100 users, 1 minute:

- Requests: 4164
- Failures: 0
- Throughput: 72.56 req/s
- Aggregate median: 15ms
- Aggregate P95: 300ms
- Slow setup endpoint:
  - `POST /login/`: avg 1673ms, P95 2200ms
- Main business endpoint P95 values:
  - `GET /projects/`: 65ms
  - `GET /projects/:id/`: 53ms
  - `GET /projects/:id/files/`: 110ms
  - `GET /projects/:id/costs/`: 120ms
  - `GET /projects/:id/nodes/`: 79ms
  - `GET /projects/:id/persons/`: 89ms
  - `GET /files/:id/rag/status/`: 110ms

Compared with the previous warmed Waitress baseline, throughput improved from 68.79 req/s to 72.56 req/s and aggregate P95 improved from 340ms to 300ms. The improvement is modest because MySQL is local and the main remaining pressure is login CPU cost plus request queuing during burst startup.

MySQL status after the run:

- `max_connections`: 151
- `Threads_connected`: 34

This matches the Waitress thread count and confirms that persistent Django connections are being reused without exhausting local MySQL capacity.

### After Redis API Cache

The project now caches high-frequency read endpoints with Django `RedisCache`:

- Project list and detail
- Project nodes
- Project persons
- Project costs
- Project files

RAG index status is not cached because it changes frequently and is polled by the frontend.

Waitress 32 threads, 100 users, 1 minute:

- Requests: 4264
- Failures: 0
- Throughput: 71.79 req/s
- Aggregate median: 15ms
- Aggregate P95: 240ms
- Slow setup endpoint:
  - `POST /login/`: avg 1578ms, P95 2200ms
- Main business endpoint P95 values:
  - `GET /projects/`: 36ms
  - `GET /projects/:id/`: 58ms
  - `GET /projects/:id/files/`: 83ms
  - `GET /projects/:id/costs/`: 61ms
  - `GET /projects/:id/nodes/`: 78ms
  - `GET /projects/:id/persons/`: 43ms
  - `GET /files/:id/rag/status/`: 86ms

Compared with the database-connection baseline, aggregate P95 improved from 300ms to 240ms. Throughput stayed close to the previous run because the load scenario is still dominated by login bursts and local server queueing, but cached business read endpoints showed lower P95 latency.

Cache invalidation was verified on `GET /projects/:id/files/`: after bumping the project cache version, the first request returned `X-API-Cache: MISS`, and the second returned `X-API-Cache: HIT`.

## Current Bottlenecks

1. Login is expensive under concurrent startup because password verification is CPU-bound and every virtual user logs in at the beginning of the test.
2. `GET /csrf/` was slow under `runserver`, but much faster after using a warmed Waitress server. The earlier result should be treated as development-server noise rather than a confirmed application bottleneck.
3. Business GET endpoints are healthy at 100 local users. Redis caching improved P95 latency for read-heavy endpoints, but login bursts and server queueing still dominate aggregate tail latency.
4. RAG chat and RAG indexing were intentionally disabled. They need separate stress tests because they depend on remote LLM quota, local embedding throughput, Qdrant, Elasticsearch, Redis, and Celery worker capacity.

### After Pagination and Response-Size Limits

The project now applies default pagination to growing list endpoints:

- `GET /projects/`
- `GET /projects/:id/nodes/`
- `GET /projects/:id/persons/`
- `GET /projects/:id/costs/`
- `GET /projects/:id/files/`

Each response keeps the original array key and adds a `pagination` object. The default page size is 50 and the maximum accepted page size is 100. Pagination parameters are included in the Redis cache key, so different pages are cached separately.

Waitress 32 threads, 100 users, 1 minute:

- Requests: 3996
- Failures: 0
- Throughput: 69.63 req/s
- Aggregate median: 19ms
- Aggregate P95: 390ms
- Slow setup endpoint:
  - `POST /login/`: avg 1813ms, P95 2200ms
- Main business endpoint P95 values:
  - `GET /projects/`: 230ms
  - `GET /projects/:id/`: 310ms
  - `GET /projects/:id/files/`: 250ms
  - `GET /projects/:id/costs/`: 170ms
  - `GET /projects/:id/nodes/`: 260ms
  - `GET /projects/:id/persons/`: 300ms
  - `GET /files/:id/rag/status/`: 210ms

Compared with the Redis-cache baseline, this local run had lower throughput and higher aggregate P95 because startup/login burst queuing was heavier in this sample. The important capacity improvement is that list endpoints now have a hard response-size ceiling and will not load, serialize, and return unbounded rows as project data grows.

Functional smoke verification:

- `GET /projects/?page=1&page_size=2` returned 2 projects plus pagination metadata.
- A second identical request returned `X-API-Cache: HIT`.
- `GET /projects/?page=1&page_size=9999` was clamped to `page_size=100`.
- Project files, costs, nodes, and persons endpoints returned the expected original array keys plus `pagination`.

### RAG/Celery Queue Workload Probe

The Locust script now supports a dedicated RAG indexing queue workload:

- `PM_LOADTEST_ENABLE_RAG_INDEX=1` enables index task submission.
- `PM_LOADTEST_ONLY_RAG_INDEX=1` switches the task set to RAG index submission and status polling only.
- `PM_LOADTEST_PROJECT_ID=<id>` fixes the test to a project with enough files.
- `PM_LOADTEST_MAX_INDEX_SUBMITS_PER_USER=<n>` controls how many index submissions each virtual user may attempt.
- `PM_LOADTEST_FILE_DISCOVERY_PAGE_SIZE=100` discovers more candidate files under backend pagination.

The project also includes `python manage.py rag_queue_snapshot`, which prints database-side file index status counts and optional Celery inspect data.

Local probe environment:

- Backend: Waitress, 16 threads, `127.0.0.1:8006`
- Worker: Celery on Windows with `-P solo`
- RAG dependencies: DashScope embedding API, Qdrant `127.0.0.1:6333`, Elasticsearch `127.0.0.1:9200`
- Load: 5 users, spawn rate 1/s, 45 seconds, fixed project 3

Result:

- Requests: 118
- Failures: 0
- `POST /files/:id/rag/index/`: 10 requests, 0 failures, median 56ms, avg 170ms, P95 490ms
- `GET /files/:id/rag/status/`: 88 requests, 0 failures, median 12ms, avg 13ms, P95 23ms
- RAG metrics printed by Locust:
  - `submit.accepted=9`
  - `submit.conflict=1`
  - `status.queued=54`
  - `status.running=20`
  - `status.completed=7`
  - `stage.queued=54`
  - `stage.parse=12`
  - `stage.embedding=6`

Finding:

- The HTTP submission/status endpoints are stable under this small queue workload.
- Duplicate submission protection worked: one conflicting submit was treated as a successful guarded response instead of a server failure.
- The real bottleneck is worker-side throughput. With Windows `-P solo`, the worker processes indexing tasks mostly sequentially. Observed successful indexing tasks took roughly 47-64 seconds for medium PDFs and around 118 seconds for a larger PDF with 389 chunks.
- OCR initialization adds a noticeable delay when a file requires OCR components.
- For a production-like concurrency story, the next optimization should split RAG indexing into resource-aware queues or run multiple Linux worker processes with controlled concurrency.

### RAG Chat Resilience Probe

The Locust script now supports a dedicated RAG chat workload:

- `PM_LOADTEST_ENABLE_RAG_CHAT=1` enables RAG chat requests.
- `PM_LOADTEST_ONLY_RAG_CHAT=1` switches the task set to RAG chat only.
- `PM_LOADTEST_RAG_CHAT_TIMEOUT=<seconds>` controls the stream probe timeout.
- The script parses NDJSON stream events and records `chat.completed`, `chat.degraded`, `chat.rate_limited`, `chat.stream_error`, and event-type counters.

Local degraded-mode probe:

- Backend: Waitress, 16 threads, `127.0.0.1:8006`
- Users: 5
- Spawn rate: 1/s
- Duration: 60 seconds
- Project: 3
- Question: `这个项目文件主要讲了什么？`
- Important limitation: this run was executed in the Codex sandbox where outbound access to DashScope/Qwen was blocked by a local proxy. It should be interpreted as a model-unavailable resilience test, not a real external-model throughput test.

Result:

- Total requests: 122
- Total failures: 0
- `POST /projects/:id/rag/chat/`: 107 requests, 0 failures, median 28ms, avg 534ms, P95 81ms, max 27012ms
- Bootstrap `GET /csrf/`: 5 requests, median about 15000ms. This was cold-start/session setup noise and not representative of the RAG endpoint itself.
- RAG metrics printed by Locust:
  - `chat.completed=2`
  - `chat.degraded=2`
  - `chat.event.delta=2`
  - `chat.event.done=2`
  - `chat.event.notice=2`
  - `chat.rate_limited=105`

Findings:

- Admission control protected the RAG endpoint under burst load. Because all virtual users used the same `loadtest_user`, most requests were correctly rejected with HTTP 429 instead of entering the expensive retrieval/model path.
- The model circuit breaker and fallback path worked: when rerank/chat model calls failed, the endpoint returned a degraded retrieval-summary stream with a `done` event instead of surfacing a hard 5xx error.
- The 27s max RAG request corresponds to the first attempts waiting on external model failures before the circuit opened. After the circuit opened, protected or degraded responses returned in tens of milliseconds.
- A real model-throughput run should be performed from the user's normal local environment after explicitly approving that project-derived retrieved text may be sent to the configured external model provider.

## Query Observation

The project now includes `app01.middleware.PerformanceLogMiddleware`. During load tests, it logs request duration, SQL query count, SQL total time, and up to three slow SQL summaries for selected hot paths.

Current local query-count smoke results after warm-up:

- `GET /projects/`: 3 SQL queries
- `GET /projects/:id/`: 3 SQL queries
- `GET /projects/:id/nodes/`: 3 SQL queries
- `GET /projects/:id/persons/`: 4 SQL queries
- `GET /projects/:id/costs/`: 9 SQL queries
- `GET /projects/:id/files/`: 3 SQL queries
- `GET /files/:id/rag/status/`: 4 SQL queries

No obvious N+1 query pattern appeared in this small local dataset. `GET /projects/:id/costs/` is currently the query-heaviest endpoint in the baseline scenario and should be reviewed first if it grows with real data volume.

## Next Measurement Steps

1. Run a real RAG chat throughput probe from a normal local environment where the configured model provider is reachable and approved for project-derived retrieval content.
2. Retest the RAG-only queue probe with separate `rag_index` and `rag_maintenance` workers, and compare Redis broker queue depths before and after the run.
3. Add endpoint-level assertions for more write paths so load tests catch functional regressions, not only latency.
