import os
import json
import random
import time
from collections import Counter
from threading import Lock

from locust import HttpUser, between, events, task


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


USERNAME = os.getenv("PM_LOADTEST_USERNAME", "loadtest_user")
PASSWORD = os.getenv("PM_LOADTEST_PASSWORD", "loadtest123456")
PROJECT_ID = os.getenv("PM_LOADTEST_PROJECT_ID")
ENABLE_RAG_CHAT = env_bool("PM_LOADTEST_ENABLE_RAG_CHAT", False)
ENABLE_RAG_INDEX = env_bool("PM_LOADTEST_ENABLE_RAG_INDEX", False)
ONLY_RAG_CHAT = env_bool("PM_LOADTEST_ONLY_RAG_CHAT", False)
ONLY_RAG_INDEX = env_bool("PM_LOADTEST_ONLY_RAG_INDEX", False)
RAG_INDEX_REBUILD = env_bool("PM_LOADTEST_RAG_INDEX_REBUILD", False)
MAX_INDEX_SUBMITS_PER_USER = int(os.getenv("PM_LOADTEST_MAX_INDEX_SUBMITS_PER_USER", "1"))
FILE_DISCOVERY_PAGE_SIZE = int(os.getenv("PM_LOADTEST_FILE_DISCOVERY_PAGE_SIZE", "100"))
RAG_QUESTION = os.getenv("PM_LOADTEST_RAG_QUESTION", "这个项目文件主要讲了什么？")
RAG_CHAT_PROBE_TIMEOUT = int(os.getenv("PM_LOADTEST_RAG_CHAT_TIMEOUT", "45"))
ACTIVE_RAG_STATUSES = {"queued", "running", "retrying", "cancelling", "deleting"}

RAG_METRICS = Counter()
RAG_METRICS_LOCK = Lock()


def record_rag_metric(name, value=1):
    with RAG_METRICS_LOCK:
        RAG_METRICS[name] += value


@events.quitting.add_listener
def report_rag_metrics(environment, **kwargs):
    if not (ENABLE_RAG_CHAT or ENABLE_RAG_INDEX or ONLY_RAG_CHAT or ONLY_RAG_INDEX):
        return

    print("RAG_LOAD_METRICS_START")
    with RAG_METRICS_LOCK:
        for name, value in sorted(RAG_METRICS.items()):
            print(f"{name}={value}")
    print("RAG_LOAD_METRICS_END")


class ProjectManageUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.project_ids = []
        self.file_ids_by_project = {}
        self.file_status_by_id = {}
        self.pending_index_file_ids = set()
        self.index_submits = 0
        self.login()
        self.discover_projects()

    def login(self):
        self.client.get("/csrf/", name="GET /csrf/")
        with self.client.post(
            "/login/",
            json={
                "username": USERNAME,
                "password": PASSWORD,
            },
            headers=self.csrf_headers(),
            name="POST /login/",
            catch_response=True,
        ) as response:
            if response.status_code >= 400:
                response.failure(f"login failed: {response.text[:300]}")
                return
            self.assert_json_data(response)

    def csrf_headers(self):
        token = self.client.cookies.get("csrftoken")
        if not token:
            return {}
        return {"X-CSRFToken": token}

    def discover_projects(self):
        data = self.get_json(
            "/projects/",
            name="GET /projects/ [bootstrap]",
            expected_key="projects",
            params={"page": 1, "page_size": FILE_DISCOVERY_PAGE_SIZE},
        )
        if data is None:
            return

        projects = data.get("projects", [])
        self.project_ids = [
            project.get("pjid")
            for project in projects
            if project.get("pjid") is not None
        ]

        if PROJECT_ID:
            self.project_ids = [int(PROJECT_ID)]

    def choose_project_id(self):
        if not self.project_ids:
            self.discover_projects()
        if not self.project_ids:
            return None
        return random.choice(self.project_ids)

    def assert_json_data(self, response, expected_key=None):
        try:
            payload = response.json()
        except ValueError:
            response.failure(f"response is not json: {response.text[:300]}")
            return None

        data = payload.get("data")
        if expected_key and (not isinstance(data, dict) or expected_key not in data):
            response.failure(f"missing data.{expected_key}: {str(payload)[:300]}")
            return None
        return data

    def get_json(self, url, name, expected_key=None, **kwargs):
        data = None
        with self.client.get(
            url,
            name=name,
            catch_response=True,
            **kwargs,
        ) as response:
            if response.status_code >= 400:
                response.failure(f"request failed: {response.text[:300]}")
                return None
            data = self.assert_json_data(response, expected_key=expected_key)
        return data

    def get_project_file_ids(self, project_id):
        if project_id in self.file_ids_by_project:
            return self.file_ids_by_project[project_id]

        data = self.get_json(
            f"/projects/{project_id}/files/",
            name="GET /projects/:id/files/ [bootstrap]",
            expected_key="files",
            params={"page": 1, "page_size": FILE_DISCOVERY_PAGE_SIZE},
        )
        if data is None:
            return []

        files = data.get("files", [])
        file_ids = [
            file_item.get("file_id")
            for file_item in files
            if file_item.get("file_id") is not None
        ]
        for file_item in files:
            file_id = file_item.get("file_id")
            if file_id is not None:
                self.file_status_by_id[file_id] = file_item.get("index_status")
        self.file_ids_by_project[project_id] = file_ids
        return file_ids

    def choose_index_file_id(self, project_id):
        file_ids = self.get_project_file_ids(project_id)
        candidates = [
            file_id
            for file_id in file_ids
            if self.file_status_by_id.get(file_id) not in ACTIVE_RAG_STATUSES
        ]
        if not candidates:
            return None
        return random.choice(candidates)

    @task(8)
    def list_projects(self):
        if ONLY_RAG_INDEX or ONLY_RAG_CHAT:
            return
        self.get_json(
            "/projects/",
            name="GET /projects/",
            expected_key="projects",
            params={"page": 1, "page_size": 10},
        )

    @task(6)
    def list_project_files(self):
        if ONLY_RAG_INDEX or ONLY_RAG_CHAT:
            return
        project_id = self.choose_project_id()
        if project_id is None:
            return

        data = self.get_json(
            f"/projects/{project_id}/files/",
            name="GET /projects/:id/files/",
            expected_key="files",
            params={"page": 1, "page_size": 10},
        )
        if data is None:
            return
        files = data.get("files", [])
        self.file_ids_by_project[project_id] = [
            file_item.get("file_id")
            for file_item in files
            if file_item.get("file_id") is not None
        ]
        for file_item in files:
            file_id = file_item.get("file_id")
            if file_id is not None:
                self.file_status_by_id[file_id] = file_item.get("index_status")

    @task(4)
    def get_project_detail(self):
        if ONLY_RAG_INDEX or ONLY_RAG_CHAT:
            return
        project_id = self.choose_project_id()
        if project_id is not None:
            self.get_json(f"/projects/{project_id}/", name="GET /projects/:id/", expected_key="project")

    @task(4)
    def list_project_nodes(self):
        if ONLY_RAG_INDEX or ONLY_RAG_CHAT:
            return
        project_id = self.choose_project_id()
        if project_id is not None:
            self.get_json(
                f"/projects/{project_id}/nodes/",
                name="GET /projects/:id/nodes/",
                expected_key="project_nodes",
                params={"page": 1, "page_size": 10},
            )

    @task(3)
    def list_project_persons(self):
        if ONLY_RAG_INDEX or ONLY_RAG_CHAT:
            return
        project_id = self.choose_project_id()
        if project_id is not None:
            self.get_json(
                f"/projects/{project_id}/persons/",
                name="GET /projects/:id/persons/",
                expected_key="persons",
                params={"page": 1, "page_size": 10},
            )

    @task(3)
    def list_project_costs(self):
        if ONLY_RAG_INDEX or ONLY_RAG_CHAT:
            return
        project_id = self.choose_project_id()
        if project_id is not None:
            self.get_json(
                f"/projects/{project_id}/costs/",
                name="GET /projects/:id/costs/",
                expected_key="costs",
                params={"page": 1, "page_size": 10},
            )

    @task(6)
    def get_rag_task_status(self):
        if ONLY_RAG_CHAT:
            return
        project_id = self.choose_project_id()
        if project_id is None:
            return

        file_ids = self.get_project_file_ids(project_id)
        if not file_ids:
            return

        if self.pending_index_file_ids and random.random() < 0.8:
            file_id = random.choice(list(self.pending_index_file_ids))
        else:
            file_id = random.choice(file_ids)

        data = self.get_json(
            f"/files/{file_id}/rag/status/",
            name="GET /files/:id/rag/status/",
        )
        if data is None:
            return

        index_status = data.get("index_status") or "unknown"
        index_stage = data.get("index_stage") or "unknown"
        self.file_status_by_id[file_id] = index_status
        record_rag_metric(f"status.{index_status}")
        record_rag_metric(f"stage.{index_stage}")
        if index_status in {"completed", "failed", "cancelled", "not_indexed"}:
            self.pending_index_file_ids.discard(file_id)

    @task(1)
    def rag_chat_readiness_probe(self):
        if ONLY_RAG_INDEX:
            return
        if not (ENABLE_RAG_CHAT or ONLY_RAG_CHAT):
            return

        project_id = self.choose_project_id()
        if project_id is None:
            return

        start_time = time.time()
        with self.client.post(
            f"/projects/{project_id}/rag/chat/",
            json={"question": RAG_QUESTION, "history": []},
            headers=self.csrf_headers(),
            name="POST /projects/:id/rag/chat/",
            stream=True,
            catch_response=True,
        ) as response:
            if response.status_code == 429:
                record_rag_metric("chat.rate_limited")
                response.success()
                return

            if not response.ok:
                record_rag_metric("chat.http_error")
                response.failure(f"RAG chat failed status={response.status_code} body={response.text[:300]}")
                return

            saw_done = False
            for raw_line in response.iter_lines():
                if time.time() - start_time > RAG_CHAT_PROBE_TIMEOUT:
                    record_rag_metric("chat.timeout")
                    response.failure(f"RAG chat stream exceeded {RAG_CHAT_PROBE_TIMEOUT}s probe window")
                    return
                if not raw_line:
                    continue

                try:
                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                    event = json.loads(line)
                except json.JSONDecodeError:
                    record_rag_metric("chat.bad_event")
                    continue

                event_type = event.get("type")
                if event_type:
                    record_rag_metric(f"chat.event.{event_type}")
                if event.get("degraded"):
                    record_rag_metric("chat.degraded")
                if event_type == "error":
                    record_rag_metric("chat.stream_error")
                    response.failure(event.get("message") or "RAG chat stream returned error event")
                    return
                if event_type == "done":
                    saw_done = True

            if saw_done:
                record_rag_metric("chat.completed")
            else:
                record_rag_metric("chat.no_done")
                response.failure("RAG chat stream ended without done event")

    @task(1)
    def submit_rag_index_task(self):
        if not ENABLE_RAG_INDEX:
            return
        if self.index_submits >= MAX_INDEX_SUBMITS_PER_USER:
            return

        project_id = self.choose_project_id()
        if project_id is None:
            return

        file_id = self.choose_index_file_id(project_id)
        if file_id is None:
            record_rag_metric("submit.no_candidate")
            return

        endpoint = "reindex" if RAG_INDEX_REBUILD else "index"
        with self.client.post(
            f"/files/{file_id}/rag/{endpoint}/",
            headers=self.csrf_headers(),
            name=f"POST /files/:id/rag/{endpoint}/",
            catch_response=True,
        ) as response:
            if response.status_code == 202:
                record_rag_metric("submit.accepted")
                self.index_submits += 1
                self.pending_index_file_ids.add(file_id)
                self.file_status_by_id[file_id] = "queued"
                self.assert_json_data(response)
                return

            if response.status_code == 409:
                record_rag_metric("submit.conflict")
                self.index_submits += 1
                response.success()
                return

            record_rag_metric("submit.failed")
            response.failure(f"index submit failed: {response.text[:300]}")


if ONLY_RAG_INDEX:
    rag_only_tasks = {
        ProjectManageUser.get_rag_task_status: 6,
    }
    if ENABLE_RAG_INDEX:
        rag_only_tasks[ProjectManageUser.submit_rag_index_task] = 3
    ProjectManageUser.tasks = rag_only_tasks

if ONLY_RAG_CHAT:
    ProjectManageUser.tasks = {
        ProjectManageUser.rag_chat_readiness_probe: 1,
    }
