CREATE TABLE agent_conversations (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
 project_id TEXT REFERENCES projects(id), created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE agent_messages (
 id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES agent_conversations(id),
 role TEXT NOT NULL CHECK(role IN ('user','assistant','system','tool')),
 content TEXT NOT NULL, task_id TEXT, created_at TEXT NOT NULL
);
CREATE TABLE agent_tasks (
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
 conversation_id TEXT REFERENCES agent_conversations(id), task_type TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('queued','planning','waiting_for_user','running','reviewing','completed','failed','cancelled')),
 dataset_id TEXT REFERENCES datasets(id), dataset_version TEXT,
 active_plan_version INTEGER CHECK(active_plan_version IS NULL OR active_plan_version>0),
 manager_session_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE task_plans (
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES agent_tasks(id),
 version INTEGER NOT NULL CHECK(version>0), goal TEXT NOT NULL,
 constraints_json TEXT NOT NULL, approval_state TEXT NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(task_id,version)
);
CREATE TABLE task_steps (
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL, plan_version INTEGER NOT NULL,
 worker_type TEXT NOT NULL CHECK(worker_type IN ('soil_expert','data_worker','mds_worker','validation_worker','decision_worker','report_worker')),
 step_name TEXT NOT NULL, status TEXT NOT NULL, input_artifact_ids_json TEXT NOT NULL,
 output_artifact_ids_json TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0 CHECK(attempt>=0),
 timeout_seconds INTEGER NOT NULL CHECK(timeout_seconds>0),
 FOREIGN KEY(task_id,plan_version) REFERENCES task_plans(task_id,version)
);
CREATE TABLE step_dependencies (
 step_id TEXT NOT NULL REFERENCES task_steps(id), depends_on_step_id TEXT NOT NULL REFERENCES task_steps(id),
 PRIMARY KEY(step_id,depends_on_step_id), CHECK(step_id<>depends_on_step_id)
);
CREATE TABLE agent_sessions (
 id TEXT PRIMARY KEY, task_id TEXT REFERENCES agent_tasks(id), role TEXT NOT NULL,
 context_summary TEXT NOT NULL DEFAULT '', last_event_id TEXT, status TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(task_id,role,id)
);
CREATE TABLE agent_events (
 id TEXT PRIMARY KEY, task_id TEXT REFERENCES agent_tasks(id), conversation_id TEXT REFERENCES agent_conversations(id),
 event_type TEXT NOT NULL, event_version INTEGER NOT NULL CHECK(event_version>0),
 occurred_at TEXT NOT NULL, producer_type TEXT NOT NULL, producer_id TEXT NOT NULL,
 plan_version INTEGER, step_id TEXT REFERENCES task_steps(id), session_id TEXT REFERENCES agent_sessions(id),
 correlation_id TEXT NOT NULL, causation_id TEXT REFERENCES agent_events(id),
 idempotency_key TEXT NOT NULL UNIQUE, payload_json TEXT NOT NULL
);
CREATE TABLE event_outbox (
 event_id TEXT PRIMARY KEY REFERENCES agent_events(id), status TEXT NOT NULL CHECK(status IN ('pending','delivered')),
 attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts>=0), created_at TEXT NOT NULL, delivered_at TEXT
);
CREATE TABLE consumer_checkpoints (
 consumer_id TEXT PRIMARY KEY, last_event_id TEXT REFERENCES agent_events(id), updated_at TEXT NOT NULL
);
CREATE TABLE artifacts (
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES agent_tasks(id),
 project_id TEXT NOT NULL REFERENCES projects(id), kind TEXT NOT NULL, storage_uri TEXT NOT NULL,
 sha256 TEXT NOT NULL CHECK(length(sha256)=64), dataset_version TEXT,
 plan_version INTEGER NOT NULL CHECK(plan_version>0), created_by TEXT NOT NULL,
 validation_status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE tool_runs (
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES agent_tasks(id),
 step_id TEXT NOT NULL REFERENCES task_steps(id), tool_name TEXT NOT NULL,
 status TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE,
 input_json TEXT NOT NULL, result_json TEXT, started_at TEXT NOT NULL, ended_at TEXT
);
CREATE TABLE model_runs (
 id TEXT PRIMARY KEY, task_id TEXT REFERENCES agent_tasks(id),
 step_id TEXT REFERENCES task_steps(id), model_name TEXT NOT NULL,
 prompt_version TEXT NOT NULL, status TEXT NOT NULL, input_classification TEXT NOT NULL,
 usage_json TEXT, started_at TEXT NOT NULL, ended_at TEXT
);
CREATE TABLE approval_requests (
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL, plan_version INTEGER NOT NULL,
 action TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected')),
 requested_at TEXT NOT NULL, decided_at TEXT, decided_by TEXT REFERENCES users(id),
 FOREIGN KEY(task_id,plan_version) REFERENCES task_plans(task_id,version)
);
CREATE TABLE worker_heartbeats (
 session_id TEXT PRIMARY KEY REFERENCES agent_sessions(id), last_seen_at TEXT NOT NULL,
 state TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0 CHECK(attempt>=0)
);
CREATE INDEX idx_agent_conversations_user ON agent_conversations(user_id,updated_at);
CREATE INDEX idx_agent_tasks_project ON agent_tasks(project_id,updated_at);
CREATE INDEX idx_task_steps_status ON task_steps(status,task_id);
CREATE INDEX idx_agent_events_task ON agent_events(task_id,occurred_at,id);
CREATE INDEX idx_event_outbox_status ON event_outbox(status,created_at);
CREATE INDEX idx_artifacts_task ON artifacts(task_id,plan_version);
