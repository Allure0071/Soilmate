import json
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import test_agent_phase2 as fixtures
from backend.app.agent.migration_v4 import migrate_runtime_schema
from backend.app.agent.manager import TaskManager
from backend.app.agent.runtime import WorkerRuntime
from backend.app.agent.registry import TestWorker
from backend.app.agent.artifact_store import ArtifactStore


class RuntimeTests(unittest.TestCase):
    db=fixtures.Phase2Tests.db
    task=fixtures.Phase2Tests.task
    tearDown=fixtures.Phase2Tests.tearDown
    def setUp(self):
        fixtures.Phase2Tests.setUp(self)
        with self.db() as con: migrate_runtime_schema(con)
        self.manager=TaskManager()
        self.artifacts=ArtifactStore(Path(self.tmp.name)/'artifacts')
        self.runtime=WorkerRuntime(self.db,self.artifacts)

    def plan(self,specs):
        task=self.task()
        self.dispatcher.dispatch_once()
        self.dispatcher.consume_once('manager',self.manager.handle)
        with self.db() as con:
            plan=self.manager.propose(con,task.task_id,'test runtime',specs)
            self.manager.approve(con,task.task_id,plan['plan_version'],'u1')
        return task,plan

    def test_parallel_roots_dependency_wait_and_artifact_exchange(self):
        task,plan=self.plan([{'name':'a','role':'data_worker'},{'name':'b','role':'soil_expert'},
                            {'name':'c','role':'mds_worker','dependencies':['a','b']}])
        barrier=threading.Barrier(2)
        original=TestWorker.execute
        def simultaneous(worker,*args):
            barrier.wait(timeout=3)
            return original(worker,*args)
        with patch.object(TestWorker,'execute',simultaneous):
            self.assertEqual(self.runtime.tick(),2)
        with self.db() as con:
            self.assertEqual(con.execute('SELECT status FROM task_steps WHERE id=?',(plan['step_ids']['c'],)).fetchone()[0],'blocked')
            self.assertEqual(con.execute("SELECT count(DISTINCT session_id) FROM worker_runs").fetchone()[0],2)
        self.assertEqual(self.runtime.tick(),1)
        with self.db() as con:
            self.assertEqual(con.execute('SELECT status FROM agent_tasks WHERE id=?',(task.task_id,)).fetchone()[0],'completed')
            aid=con.execute('SELECT output_artifact_ids_json FROM task_steps WHERE id=?',(plan['step_ids']['c'],)).fetchone()[0]
            content=self.artifacts.read(con,json.loads(aid)[0],task.task_id,'p1','u1')
            self.assertEqual(len(content['inputs']),2)

    def test_retry_creates_new_run_preserves_history(self):
        task,_=self.plan([{'name':'a','role':'data_worker','config':{'fail_first':True}}])
        self.runtime.tick()
        self.runtime.tick()
        with self.db() as con:
            self.assertEqual([r[0] for r in con.execute('SELECT status FROM worker_runs ORDER BY attempt')],['failed','succeeded'])
            self.assertEqual(con.execute('SELECT count(*) FROM artifacts').fetchone()[0],1)

    def test_expired_claim_recovers_without_duplicate_artifact(self):
        task,_=self.plan([{'name':'a','role':'data_worker'}])
        run=self.runtime.claim()
        with self.db() as con:
            con.execute("UPDATE worker_runs SET lease_until='2000-01-01' WHERE id=?",(run,))
        self.runtime.tick()
        self.runtime.tick()
        with self.db() as con:
            self.assertEqual(con.execute('SELECT count(*) FROM worker_runs').fetchone()[0],2)
            self.assertEqual(con.execute('SELECT count(*) FROM artifacts').fetchone()[0],1)

    def test_cancel_running_worker(self):
        task,_=self.plan([{'name':'a','role':'data_worker','config':{'delay_seconds':1}}])
        thread=threading.Thread(target=self.runtime.tick)
        thread.start()
        time.sleep(.15)
        with self.db() as con: self.manager.cancel(con,task.task_id,'u1')
        thread.join(timeout=3)
        self.assertFalse(thread.is_alive())
        with self.db() as con:
            self.assertEqual(con.execute('SELECT status FROM worker_runs').fetchone()[0],'cancelled')
            self.assertEqual(con.execute('SELECT count(*) FROM artifacts').fetchone()[0],0)

    def test_artifact_scope_and_hash_enforced(self):
        task,_=self.plan([{'name':'a','role':'data_worker'}])
        self.runtime.tick()
        with self.db() as con:
            artifact=con.execute('SELECT * FROM artifacts').fetchone()
            with self.assertRaises(PermissionError): self.artifacts.read(con,artifact['id'],'other','p1')
            with self.assertRaises(PermissionError): self.artifacts.read(con,artifact['id'],task.task_id,'p1','u2')
            (self.artifacts.root/artifact['storage_uri']).write_bytes(b'corrupt')
            with self.assertRaises(ValueError): self.artifacts.read(con,artifact['id'],task.task_id,'p1')

    def test_superseded_run_cannot_publish(self):
        task,_=self.plan([{'name':'a','role':'data_worker'}])
        old=self.runtime.claim()
        with self.db() as con:
            revised=self.manager.propose(con,task.task_id,'budget reduced',[{'name':'a','role':'data_worker'}],{'budget':70})
        self.runtime.execute(old)
        with self.db() as con:
            self.assertEqual(revised['plan_version'],2)
            self.assertEqual(con.execute('SELECT count(*) FROM artifacts').fetchone()[0],0)

    def test_completed_run_redelivery_does_not_repeat_artifact(self):
        self.plan([{'name':'a','role':'data_worker'}])
        run=self.runtime.claim()
        self.runtime.execute(run)
        self.runtime.execute(run)
        with self.db() as con:
            self.assertEqual(con.execute('SELECT count(*) FROM artifacts').fetchone()[0],1)
            self.assertEqual(con.execute('SELECT count(*) FROM worker_runs').fetchone()[0],1)

    def test_timeout_is_bounded(self):
        self.plan([{'name':'a','role':'data_worker','timeout_seconds':1,'max_attempts':1,
                    'config':{'delay_seconds':2}}])
        self.runtime.tick()
        with self.db() as con:
            self.assertEqual(con.execute('SELECT status FROM worker_runs').fetchone()[0],'timed_out')

    def test_multiple_tasks_preserve_context(self):
        first,_=self.plan([{'name':'a','role':'data_worker','config':{'value':'one'}}])
        second,_=self.plan([{'name':'b','role':'data_worker','config':{'value':'two'}}])
        self.runtime.tick()
        with self.db() as con:
            for task,value in ((first,'one'),(second,'two')):
                artifact=con.execute('SELECT id FROM artifacts WHERE task_id=?',(task.task_id,)).fetchone()[0]
                content=self.artifacts.read(con,artifact,task.task_id,'p1')
                self.assertEqual((content['task_id'],content['value']),(task.task_id,value))
