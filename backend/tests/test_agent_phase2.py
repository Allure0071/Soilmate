"""Phase 2 event durability, routing, isolation, retry and replay tests."""

import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.agent.contracts import AgentEvent, Producer
from backend.app.agent.events import EventDispatcher, EventStore
from backend.app.agent.migration import migrate_agent_schema
from backend.app.agent.migration_v3 import migrate_event_schema
from backend.app.agent.router import GlobalRouter
from backend.app.scientific.research_store import SCHEMA


class Phase2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "research.sqlite"
        with self.db() as con:
            con.executescript(SCHEMA)
            con.execute("CREATE TABLE users(id TEXT PRIMARY KEY)")
            con.execute("ALTER TABLE projects ADD COLUMN owner_user_id TEXT")
            con.execute("INSERT INTO schema_migrations VALUES(1,'fixture')")
            con.executemany("INSERT INTO users(id) VALUES(?)", [("u1",), ("u2",)])
            con.executemany("INSERT INTO projects(id,name,owner_user_id,created_at) VALUES(?,?,?,?)",
                            [("p1", "东北", "u1", "now"), ("p2", "黄淮海", "u2", "now")])
        with self.db() as con:
            self.assertTrue(migrate_agent_schema(con))
            self.assertTrue(migrate_event_schema(con))
            self.assertFalse(migrate_event_schema(con))
        self.router = GlobalRouter()
        self.dispatcher = EventDispatcher(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    @contextmanager
    def db(self):
        con = sqlite3.connect(self.path, timeout=5)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def task(self, text="帮我分析这份东北土壤数据", user="u1", project="p1", conversation=None):
        with self.db() as con:
            return self.router.route(con, user, text, project, conversation)

    def test_t1_two_tasks_get_distinct_ids(self):
        a = self.task()
        b = self.task("帮我分析这份黄淮海数据")
        self.assertNotEqual(a.task_id, b.task_id)
        self.assertNotEqual(a.conversation_id, b.conversation_id)

    def test_t2_duplicate_event_and_inbox_do_not_repeat_business_write(self):
        task = self.task()
        with self.db() as con:
            con.execute("CREATE TABLE business_counter(id TEXT PRIMARY KEY,n INTEGER NOT NULL)")
        self.assertEqual(self.dispatcher.dispatch_once(), task.event_ids[0])
        with self.db() as con:
            self.assertEqual(con.execute("SELECT count(*) FROM consumer_inbox").fetchone()[0], 1)
            event = AgentEvent(event_id="other", event_type="task.created", event_version=1,
                               occurred_at=datetime.now(timezone.utc), producer=Producer(type="router", id="global_router"),
                               task_id=task.task_id, conversation_id=task.conversation_id,
                               correlation_id=task.message_id, idempotency_key="route:" + task.message_id,
                               payload={"intent": "new_analysis_task", "target_consumer": "manager", "message_id": task.message_id})
            _, _, created = EventStore().append(con, event)
            self.assertFalse(created)
        def handler(con, event):
            con.execute("INSERT INTO business_counter VALUES(?,1)", (event.event_id,))
        self.assertEqual(self.dispatcher.consume_once("manager", handler), task.event_ids[0])
        self.assertIsNone(self.dispatcher.consume_once("manager", handler))
        with self.db() as con:
            self.assertEqual(con.execute("SELECT sum(n) FROM business_counter").fetchone()[0], 1)

    def test_t3_outbox_survives_dispatcher_restart(self):
        script = ("import sqlite3,os; from backend.app.agent.router import GlobalRouter; "
                  f"c=sqlite3.connect({str(self.path)!r}); c.row_factory=sqlite3.Row; "
                  "c.execute('PRAGMA foreign_keys=ON'); "
                  "GlobalRouter().route(c,'u1','帮我分析这份数据','p1'); c.commit(); os._exit(0)")
        subprocess.run([sys.executable, "-c", script], check=True, timeout=15)
        with self.db() as con:
            record = con.execute("SELECT event_id,status FROM event_outbox").fetchone()
            event_id = record["event_id"]
            self.assertEqual(record["status"], "pending")
        restarted = EventDispatcher(self.db)
        self.assertEqual(restarted.dispatch_once(), event_id)
        with self.db() as con:
            self.assertEqual(con.execute("SELECT status FROM event_outbox WHERE event_id=?", (event_id,)).fetchone()[0], "delivered")

    def test_t5_t6_consumer_failure_is_bounded_and_recorded(self):
        task = self.task()
        self.dispatcher.dispatch_once()
        instant = datetime.now(timezone.utc)
        def fail(con, event):
            raise RuntimeError("simulated failure")
        for offset in (0, 10, 20):
            self.assertIsNone(self.dispatcher.consume_once("manager", fail, instant + timedelta(seconds=offset)))
        with self.db() as con:
            row = con.execute("SELECT status,attempts,last_error FROM consumer_inbox WHERE event_id=?", task.event_ids).fetchone()
            self.assertEqual((row["status"], row["attempts"]), ("failed", 3))
            self.assertIn("simulated failure", row["last_error"])
        self.assertIsNone(self.dispatcher.consume_once("manager", fail, instant + timedelta(hours=1)))

    def test_t7_t8_task_sequence_isolated_and_replay_ordered(self):
        a = self.task()
        b = self.task("帮我分析这份黄淮海数据")
        with self.db() as con:
            for route in (a, b, a):
                eid = "e_" + str(con.execute("SELECT count(*) FROM agent_events").fetchone()[0])
                EventStore().append(con, AgentEvent(event_id=eid, event_type="task.progress_updated", event_version=1,
                    occurred_at=datetime.now(timezone.utc), producer=Producer(type="system", id="test"),
                    task_id=route.task_id, correlation_id=eid, idempotency_key=eid,
                    payload={"target_consumer": "manager"}))
            a_seq = [x["task_event_seq"] for x in EventStore().replay(con, a.task_id)]
            b_seq = [x["task_event_seq"] for x in EventStore().replay(con, b.task_id)]
        self.assertEqual(a_seq, [1, 2, 3])
        self.assertEqual(b_seq, [1, 2])

    def test_t9_independent_knowledge_does_not_create_task(self):
        with self.db() as con:
            result = self.router.route(con, "u1", "土壤健康是什么？")
            self.assertEqual((result.intent, result.target, result.task_id),
                             ("general_knowledge_query", "soil_expert", None))
            self.assertEqual(con.execute("SELECT count(*) FROM agent_tasks").fetchone()[0], 0)

    def test_t10_t12_followup_and_modification_target_correct_task(self):
        a = self.task()
        b = self.task("帮我分析这份黄淮海数据")
        with self.db() as con:
            followup = self.router.route(con, "u1", "为什么这次没有选择 CEC？", "p1", a.conversation_id, a.task_id)
            change = self.router.route(con, "u1", "把检测预算降低 30%", "p1", a.conversation_id, a.task_id)
            self.assertEqual((followup.intent, followup.target, followup.task_id),
                             ("task_followup", "soil_expert", a.task_id))
            self.assertEqual((change.intent, change.target, change.task_id),
                             ("task_modification", "manager", a.task_id))
            self.assertEqual(con.execute("SELECT count(*) FROM agent_events WHERE task_id=?", (b.task_id,)).fetchone()[0], 1)

    def test_t11_new_task_and_duplicate_message_id(self):
        with self.db() as con:
            first = self.router.route(con, "u1", "帮我分析这份数据", "p1", message_id="fixed")
        with self.db() as con:
            again = self.router.route(con, "u1", "帮我分析这份数据", "p1", message_id="fixed")
            self.assertEqual(first.task_id, again.task_id)
            self.assertEqual(con.execute("SELECT count(*) FROM agent_tasks").fetchone()[0], 1)

    def test_t4_historical_task_followup_uses_explicit_id(self):
        task = self.task()
        with self.db() as con:
            con.execute("UPDATE agent_tasks SET status='completed' WHERE id=?", (task.task_id,))
            result = self.router.route(con, "u1", "为什么这次没有选择 CEC？",
                                       "p1", task_id=task.task_id)
            self.assertEqual((result.intent, result.task_id, result.target),
                             ("task_followup", task.task_id, "soil_expert"))

    def test_t13_cross_user_task_denied(self):
        task = self.task()
        with self.db() as con:
            with self.assertRaises(PermissionError):
                self.router.route(con, "u2", "为什么这次没有选择 CEC？", "p2", task_id=task.task_id)

    def test_t14_unknown_intent_clarifies(self):
        with self.db() as con:
            result = self.router.route(con, "u1", "你好呀")
            self.assertEqual(result.intent, "clarification")
            self.assertEqual(con.execute("SELECT count(*) FROM agent_tasks").fetchone()[0], 0)

    def test_business_event_and_outbox_rollback_together(self):
        with self.assertRaises(RuntimeError):
            with self.db() as con:
                self.router.route(con, "u1", "帮我分析这份数据", "p1")
                raise RuntimeError("crash before commit")
        with self.db() as con:
            for table in ("agent_tasks", "agent_events", "event_outbox", "agent_messages"):
                self.assertEqual(con.execute("SELECT count(*) FROM " + table).fetchone()[0], 0)

    def test_failed_consumer_write_rolls_back_and_checkpoint_waits(self):
        task = self.task()
        self.dispatcher.dispatch_once()
        with self.db() as con:
            con.execute("CREATE TABLE side_effect(id TEXT PRIMARY KEY)")
        def fail(con, event):
            con.execute("INSERT INTO side_effect VALUES(?)", (event.event_id,))
            raise RuntimeError("crash before acknowledgement")
        self.dispatcher.consume_once("manager", fail)
        with self.db() as con:
            self.assertEqual(con.execute("SELECT count(*) FROM side_effect").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT count(*) FROM consumer_checkpoints").fetchone()[0], 0)

    def test_ambiguous_task_and_missing_results_request_clarification(self):
        first = self.task()
        self.task("帮我分析这份黄淮海数据", conversation=first.conversation_id)
        with self.db() as con:
            ambiguous = self.router.route(con, "u1", "把预算降低30%", "p1", first.conversation_id)
            missing = self.router.route(con, "u1", "为什么这次没有选择CEC？", "p1")
            self.assertEqual((ambiguous.intent, missing.intent), ("clarification", "clarification"))

    def test_event_log_rejects_update_and_delete(self):
        task = self.task()
        with self.db() as con:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("UPDATE agent_events SET event_type='fake' WHERE id=?", task.event_ids)
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("DELETE FROM agent_events WHERE id=?", task.event_ids)

    def test_invalid_dispatch_target_has_bounded_deadletter(self):
        task = self.task()
        with self.db() as con:
            EventStore().append(con, AgentEvent(event_id="bad", event_type="test.invalid", event_version=1,
                occurred_at=datetime.now(timezone.utc), producer=Producer(type="system", id="test"),
                task_id=task.task_id, correlation_id="bad", idempotency_key="bad",
                payload={"target_consumer": []}))
        self.dispatcher.dispatch_once()
        stamp = datetime.now(timezone.utc)
        for offset in (0, 10, 20):
            self.dispatcher.dispatch_once(stamp + timedelta(seconds=offset))
        with self.db() as con:
            self.assertEqual(con.execute("SELECT attempts FROM event_outbox_deadletters WHERE event_id='bad'").fetchone()[0], 3)

    def test_history_registry_and_artifact_recall(self):
        task = self.task()
        with self.db() as con:
            con.execute("""INSERT INTO artifacts(id,task_id,project_id,kind,storage_uri,sha256,
                plan_version,created_by,validation_status,created_at)
                VALUES('a1',?,'p1','report','reference-only',?,1,'test','pending','now')""", (task.task_id, 'a'*64))
            registry = self.router.route(con, "u1", "查看之前的分析", "p1")
            recall = self.router.route(con, "u1", "查看报告", "p1", task_id=task.task_id)
            self.assertEqual(registry.candidate_task_ids, [task.task_id])
            self.assertEqual(recall.artifact_ids, ['a1'])


if __name__ == "__main__":
    unittest.main()
