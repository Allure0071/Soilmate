"""Contract and additive migration tests against an ephemeral copy of the real schema."""

import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backend.app.agent.contracts import AgentEvent, ApprovalRequest, TaskStep
from backend.app.agent.migration import migrate_agent_schema
from pydantic import ValidationError

SOURCE = Path(r"E:\soil-frontend\data\backups\research_v2_pre_agent_v2_20261102.sqlite")
EXPECTED_NEW_TABLES = {
    "agent_conversations", "agent_messages", "agent_tasks", "task_plans", "task_steps",
    "step_dependencies", "agent_sessions", "agent_events", "event_outbox",
    "consumer_checkpoints", "artifacts", "tool_runs", "model_runs",
    "approval_requests", "worker_heartbeats",
}


class MigrationTests(unittest.TestCase):
    def test_additive_and_idempotent_on_real_schema_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            dst = sqlite3.connect(str(Path(folder) / "copy.sqlite"))
            if SOURCE.is_file():
                src = sqlite3.connect(SOURCE.as_uri() + "?immutable=1", uri=True)
                src.backup(dst)
                src.close()
            else:
                from backend.app.scientific.research_store import SCHEMA
                dst.executescript(SCHEMA)
                dst.execute("CREATE TABLE users(id TEXT PRIMARY KEY)")
                dst.execute("INSERT INTO schema_migrations VALUES(1,'fixture')")
            original = {name: dst.execute("SELECT COUNT(*) FROM " + name).fetchone()[0]
                        for name in ("projects", "datasets", "analysis_runs", "reports")}
            self.assertTrue(migrate_agent_schema(dst))
            self.assertFalse(migrate_agent_schema(dst))
            tables = {r[0] for r in dst.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue(EXPECTED_NEW_TABLES <= tables)
            self.assertEqual(dst.execute("SELECT COUNT(*) FROM schema_migrations WHERE version=2").fetchone()[0], 1)
            for name, count in original.items():
                self.assertEqual(dst.execute("SELECT COUNT(*) FROM " + name).fetchone()[0], count)
            self.assertEqual(dst.execute("PRAGMA foreign_key_check").fetchall(), [])
            dst.close()

    def test_rejects_missing_legacy_schema(self):
        with sqlite3.connect(":memory:") as connection:
            with self.assertRaises(RuntimeError):
                migrate_agent_schema(connection)


class ContractTests(unittest.TestCase):
    def test_event_requires_utc_and_rejects_unknown_fields(self):
        event = dict(event_id="e1", event_type="task.created", event_version=1,
                     occurred_at=datetime.now(timezone.utc), producer={"type": "router", "id": "router"},
                     correlation_id="c1", idempotency_key="k1")
        self.assertEqual(AgentEvent.model_validate(event).event_id, "e1")
        with self.assertRaises(ValidationError):
            AgentEvent.model_validate({**event, "occurred_at": datetime.now().replace(tzinfo=None)})
        with self.assertRaises(ValidationError):
            AgentEvent.model_validate({**event, "arbitrary": True})

    def test_step_and_approval_invariants(self):
        step = dict(step_id="s1", task_id="t1", plan_version=1, worker_type="mds_worker",
                    step_name="selection", dependency_ids=["s1"], timeout_seconds=60)
        with self.assertRaises(ValidationError):
            TaskStep.model_validate(step)
        approval = dict(approval_id="a1", task_id="t1", plan_version=1,
                        action="approve_plan", status="approved", requested_at=datetime.now(timezone.utc))
        with self.assertRaises(ValidationError):
            ApprovalRequest.model_validate(approval)


if __name__ == "__main__":
    unittest.main()
