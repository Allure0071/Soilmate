"""Phase 3 execution records; explicit, additive migration."""
from datetime import datetime, timezone


def migrate_runtime_schema(con):
    versions = {r[0] for r in con.execute("SELECT version FROM schema_migrations")}
    if 3 not in versions:
        raise RuntimeError("schema v3 required")
    if 4 in versions:
        return False
    con.execute("BEGIN IMMEDIATE")
    try:
        con.execute("ALTER TABLE task_steps ADD COLUMN config_json TEXT NOT NULL DEFAULT '{}'")
        con.execute("ALTER TABLE task_steps ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 2")
        con.execute("ALTER TABLE agent_tasks ADD COLUMN cancel_requested INTEGER NOT NULL DEFAULT 0")
        con.execute("""CREATE TABLE worker_runs(
          id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES agent_tasks(id),
          step_id TEXT NOT NULL REFERENCES task_steps(id), plan_version INTEGER NOT NULL,
          session_id TEXT NOT NULL REFERENCES agent_sessions(id), attempt INTEGER NOT NULL,
          execution_key TEXT NOT NULL, status TEXT NOT NULL, started_at TEXT NOT NULL,
          ended_at TEXT, lease_until TEXT NOT NULL, result_json TEXT, error TEXT,
          UNIQUE(step_id,attempt))""")
        con.execute("""CREATE TABLE execution_claims(
          execution_key TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES agent_tasks(id),
          step_id TEXT NOT NULL REFERENCES task_steps(id), status TEXT NOT NULL,
          artifact_id TEXT REFERENCES artifacts(id), updated_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE artifact_links(
          run_id TEXT NOT NULL REFERENCES worker_runs(id), artifact_id TEXT NOT NULL REFERENCES artifacts(id),
          direction TEXT NOT NULL CHECK(direction IN ('input','output')), PRIMARY KEY(run_id,artifact_id,direction))""")
        con.execute("CREATE INDEX idx_worker_runs_active ON worker_runs(status,lease_until)")
        con.execute("""CREATE TRIGGER task_plans_immutable BEFORE UPDATE ON task_plans
          BEGIN SELECT RAISE(ABORT,'plan versions are immutable'); END""")
        con.execute("""CREATE TRIGGER task_plans_no_delete BEFORE DELETE ON task_plans
          BEGIN SELECT RAISE(ABORT,'plan versions are immutable'); END""")
        con.execute("""CREATE TRIGGER worker_runs_terminal BEFORE UPDATE ON worker_runs
          WHEN OLD.status!='running' BEGIN SELECT RAISE(ABORT,'terminal run is immutable'); END""")
        con.execute("""CREATE TRIGGER worker_runs_no_delete BEFORE DELETE ON worker_runs
          BEGIN SELECT RAISE(ABORT,'run history is immutable'); END""")
        for operation in ('UPDATE','DELETE'):
            con.execute(f"""CREATE TRIGGER artifacts_no_{operation.lower()} BEFORE {operation} ON artifacts
              BEGIN SELECT RAISE(ABORT,'artifacts are immutable'); END""")
        con.execute("INSERT INTO schema_migrations VALUES(4,?)", (datetime.now(timezone.utc).isoformat(),))
        con.commit()
    except Exception:
        con.rollback()
        raise
    return True
