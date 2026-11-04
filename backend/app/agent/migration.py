"""Additive, transactional Agent schema migration; never runs on import."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

VERSION = 2
REQUIRED_LEGACY = {"schema_migrations", "users", "projects", "datasets", "analysis_runs", "reports"}
SQL_PATH = Path(__file__).with_name("schema_v2.sql")


def migrate_agent_schema(connection: sqlite3.Connection) -> bool:
    """Return True only when v2 was newly applied to an existing research DB."""
    connection.execute("PRAGMA foreign_keys=ON")
    existing = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = REQUIRED_LEGACY - existing
    if missing:
        raise RuntimeError(f"legacy research schema missing: {', '.join(sorted(missing))}")
    if connection.execute("SELECT 1 FROM schema_migrations WHERE version=?", (VERSION,)).fetchone():
        return False
    statements = [statement.strip() for statement in SQL_PATH.read_text(encoding="utf-8").split(";") if statement.strip()]
    # Callers may already hold an implicit transaction (sqlite3 default mode).
    # Use a savepoint in that case so the migration stays atomic without raising
    # "cannot start a transaction within a transaction".
    nested = connection.in_transaction
    if nested:
        connection.execute("SAVEPOINT agent_schema_v2")
    else:
        connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            connection.execute(statement)
        connection.execute("INSERT INTO schema_migrations(version,applied_at) VALUES(?,?)",
                           (VERSION, datetime.now(timezone.utc).isoformat()))
        if nested:
            connection.execute("RELEASE agent_schema_v2")
        else:
            connection.commit()
    except Exception:
        if nested:
            connection.execute("ROLLBACK TO agent_schema_v2")
            connection.execute("RELEASE agent_schema_v2")
        else:
            connection.rollback()
        raise
    return True
