"""Assessment P0 persistence: sessions, measurements, tasks and idempotency.

Prototype use: the assessment engine is a deterministic demonstration ruleset.
It is not a validated soil-health model and must not be presented as one.
"""
from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager

from ..scientific.research_store import connect, initialize, now, one, many, uid, dump, unpack

SCHEMA = """
CREATE TABLE IF NOT EXISTS assessment_sessions(
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  crop_name TEXT,
  background TEXT NOT NULL DEFAULT '',
  field_id TEXT,
  cycle_id TEXT,
  created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assessment_measurements(
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES assessment_sessions(id),
  user_id TEXT NOT NULL,
  sample_alias TEXT NOT NULL,
  sampling_date TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assessment_tasks(
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES assessment_sessions(id),
  user_id TEXT NOT NULL,
  type TEXT NOT NULL,
  status TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  result_json TEXT,
  error_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assessment_idempotency(
  user_id TEXT NOT NULL,
  key TEXT NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  status INTEGER NOT NULL,
  response_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(user_id, key));
CREATE TABLE IF NOT EXISTS assessment_demo_seeds(
  user_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL DEFAULT '',
  task_id TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_assessment_sessions_user ON assessment_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_assessment_measurements_session ON assessment_measurements(session_id);
CREATE INDEX IF NOT EXISTS idx_assessment_tasks_session ON assessment_tasks(session_id);
"""


def init_assessment(con):
    con.executescript(SCHEMA)


@contextmanager
def db():
    initialize()
    with connect() as con:
        init_assessment(con)
        yield con


def request_hash(method, path, body):
    return hashlib.sha256(dump({"method": method, "path": path, "body": body or {}}).encode("utf-8")).hexdigest()


def replay_idempotent(con, user_id, key, method, path, body):
    """Return (status, response) for a previous identical write, or None."""
    if not key:
        return None
    row = one(con, "SELECT * FROM assessment_idempotency WHERE user_id=? AND key=?", (user_id, key))
    if not row:
        return None
    if row["request_hash"] != request_hash(method, path, body):
        return "conflict"
    return int(row["status"]), unpack(row["response_json"])


def remember_idempotent(con, user_id, key, method, path, body, status, response):
    if not key:
        return
    con.execute(
        "INSERT OR REPLACE INTO assessment_idempotency VALUES(?,?,?,?,?,?,?,?)",
        (user_id, key, method, path, request_hash(method, path, body), int(status), dump(response), now()),
    )


def create_session(con, user_id, mode, crop_name, background, field_id, cycle_id):
    session_id = uid("ases")
    con.execute(
        "INSERT INTO assessment_sessions VALUES(?,?,?,?,?,?,?,?)",
        (session_id, user_id, mode, crop_name, background or "", field_id, cycle_id, now()),
    )
    return get_session(con, session_id, user_id)


def get_session(con, session_id, user_id):
    row = one(con, "SELECT * FROM assessment_sessions WHERE id=? AND user_id=?", (session_id, user_id))
    if not row:
        return None
    measurements = many(con, "SELECT id FROM assessment_measurements WHERE session_id=? ORDER BY created_at", (session_id,))
    tasks = many(con, "SELECT id FROM assessment_tasks WHERE session_id=? ORDER BY created_at DESC LIMIT 1", (session_id,))
    return {
        "id": row["id"],
        "mode": row["mode"],
        "crop_name": row["crop_name"],
        "background": row["background"],
        "field_id": row["field_id"],
        "cycle_id": row["cycle_id"],
        "measurement_ids": [item["id"] for item in measurements],
        "latest_task_id": tasks[0]["id"] if tasks else None,
        "created_at": row["created_at"],
    }


def create_measurement(con, user_id, session_id, payload):
    measurement_id = uid("ame")
    con.execute(
        "INSERT INTO assessment_measurements VALUES(?,?,?,?,?,?,?)",
        (measurement_id, session_id, user_id, payload["sample_alias"], payload.get("sampling_date"),
         dump(payload), now()),
    )
    return get_measurement(con, measurement_id, user_id)


def get_measurement(con, measurement_id, user_id):
    row = one(con, "SELECT * FROM assessment_measurements WHERE id=? AND user_id=?", (measurement_id, user_id))
    if not row:
        return None
    payload = unpack(row["payload_json"])
    payload.update({"id": row["id"], "session_id": row["session_id"], "created_at": row["created_at"]})
    return payload


def create_task(con, user_id, session_id, task_type, payload):
    task_id = uid("atk")
    con.execute(
        "INSERT INTO assessment_tasks VALUES(?,?,?,?,?,?,?,?,?,?)",
        (task_id, session_id, user_id, task_type, "queued", dump(payload), None, None, now(), now()),
    )
    return task_id


def get_task_row(con, task_id, user_id):
    return one(con, "SELECT * FROM assessment_tasks WHERE id=? AND user_id=?", (task_id, user_id))


def update_task(con, task_id, status, result=None, error=None):
    con.execute(
        "UPDATE assessment_tasks SET status=?, result_json=?, error_json=?, updated_at=? WHERE id=?",
        (status, dump(result) if result is not None else None, dump(error) if error is not None else None, now(), task_id),
    )
