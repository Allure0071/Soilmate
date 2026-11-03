"""Add Phase 2 event-delivery columns and inbox without modifying old records."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

VERSION = 3
SQL_PATH = Path(__file__).with_name("schema_v3.sql")


def migrate_event_schema(connection: sqlite3.Connection) -> bool:
    connection.execute("PRAGMA foreign_keys=ON")
    versions = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
    if 2 not in versions:
        raise RuntimeError("Agent schema v2 is required")
    if VERSION in versions:
        return False
    statements = [s.strip() for s in SQL_PATH.read_text(encoding="utf-8").split(";") if s.strip()]
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            connection.execute(statement)
        for (task_id,) in connection.execute("SELECT DISTINCT task_id FROM agent_events WHERE task_id IS NOT NULL").fetchall():
            ids = connection.execute("SELECT id FROM agent_events WHERE task_id=? ORDER BY rowid", (task_id,)).fetchall()
            for sequence, (event_id,) in enumerate(ids, 1):
                connection.execute("UPDATE agent_events SET task_event_seq=? WHERE id=?", (sequence, event_id))
            connection.execute("INSERT INTO task_event_counters VALUES(?,?)", (task_id, len(ids)))
        for operation in ("UPDATE", "DELETE"):
            connection.execute(f"""CREATE TRIGGER agent_events_no_{operation.lower()}
                BEFORE {operation} ON agent_events BEGIN
                SELECT RAISE(ABORT, 'event log is append-only'); END""")
        connection.execute("INSERT INTO schema_migrations(version,applied_at) VALUES(?,?)",
                           (VERSION, datetime.now(timezone.utc).isoformat()))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return True
