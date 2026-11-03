"""Concurrency and migration gates required before Runtime development."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import unittest
import test_agent_phase2 as fixtures
from backend.app.agent.events import EventStore
from backend.app.agent.contracts import AgentEvent, Producer
from backend.app.agent.migration_v4 import migrate_runtime_schema


class Phase3PreflightTests(unittest.TestCase):
    setUp = fixtures.Phase2Tests.setUp
    tearDown = fixtures.Phase2Tests.tearDown
    db = fixtures.Phase2Tests.db
    task = fixtures.Phase2Tests.task
    def test_concurrent_task_sequences(self):
        task = self.task()
        def emit(index):
            with self.db() as con:
                con.execute('BEGIN IMMEDIATE')
                EventStore().append(con, AgentEvent(event_id=f'parallel-{index}', event_type='test.event',
                    event_version=1, occurred_at=datetime.now(timezone.utc), producer=Producer(type='system',id='test'),
                    task_id=task.task_id, correlation_id=str(index), idempotency_key=f'parallel-{index}', payload={}))
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(emit, range(32)))
        with self.db() as con:
            rows = EventStore().replay(con, task.task_id)
            self.assertEqual([r['task_event_seq'] for r in rows], list(range(1,34)))
            before = con.total_changes
            EventStore().replay(con, task.task_id)
            self.assertEqual(con.total_changes, before)

    def test_v4_migration_idempotent(self):
        with self.db() as con:
            self.assertTrue(migrate_runtime_schema(con))
            self.assertFalse(migrate_runtime_schema(con))
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(), [])
