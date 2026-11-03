ALTER TABLE agent_events ADD COLUMN task_event_seq INTEGER;
ALTER TABLE event_outbox ADD COLUMN next_attempt_at TEXT;
ALTER TABLE event_outbox ADD COLUMN last_error TEXT;
ALTER TABLE event_outbox ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 3;
CREATE TABLE task_event_counters (
 task_id TEXT PRIMARY KEY REFERENCES agent_tasks(id), last_seq INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE consumer_inbox (
 consumer_id TEXT NOT NULL, event_id TEXT NOT NULL REFERENCES agent_events(id),
 status TEXT NOT NULL CHECK(status IN ('pending','processing','succeeded','failed')),
 attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts>=0), max_attempts INTEGER NOT NULL DEFAULT 3,
 next_attempt_at TEXT, last_error TEXT, processed_at TEXT,
 PRIMARY KEY(consumer_id,event_id)
);
CREATE TABLE event_outbox_deadletters (
 event_id TEXT PRIMARY KEY REFERENCES agent_events(id), attempts INTEGER NOT NULL,
 last_error TEXT NOT NULL, failed_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_agent_events_task_seq ON agent_events(task_id,task_event_seq) WHERE task_id IS NOT NULL;
CREATE INDEX idx_consumer_inbox_status ON consumer_inbox(status,next_attempt_at);
