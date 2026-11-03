import unittest
import test_agent_phase2 as fixtures
from backend.app.agent.migration_v4 import migrate_runtime_schema
from backend.app.agent.manager import TaskManager
from backend.app.agent.registry import REGISTRY


class ManagerTests(unittest.TestCase):
    db=fixtures.Phase2Tests.db
    task=fixtures.Phase2Tests.task
    tearDown=fixtures.Phase2Tests.tearDown
    def setUp(self):
        fixtures.Phase2Tests.setUp(self)
        with self.db() as con: migrate_runtime_schema(con)
        self.manager=TaskManager()

    def test_manager_session_and_plan_versions(self):
        task=self.task()
        self.dispatcher.dispatch_once()
        self.dispatcher.consume_once('manager',self.manager.handle)
        specs=[{'name':'audit','role':'data_worker'}, {'name':'mds','role':'mds_worker','dependencies':['audit']}]
        with self.db() as con:
            self.assertIsNotNone(con.execute('SELECT manager_session_id FROM agent_tasks WHERE id=?',(task.task_id,)).fetchone()[0])
            first=self.manager.propose(con,task.task_id,'test',specs,{'budget':100})
            second=self.manager.propose(con,task.task_id,'test',specs,{'budget':70})
            self.assertEqual((first['plan_version'],second['plan_version']),(1,2))
            with self.assertRaises(ValueError): self.manager.approve(con,task.task_id,1,'u1')
            self.manager.approve(con,task.task_id,2,'u1')
            self.assertEqual(con.execute('SELECT count(*) FROM task_plans').fetchone()[0],2)

    def test_cycle_rejected_and_six_roles_registered(self):
        task=self.task()
        with self.db() as con:
            with self.assertRaises(ValueError):
                self.manager.propose(con,task.task_id,'cycle',[{'name':'a','role':'data_worker','dependencies':['b']},{'name':'b','role':'mds_worker','dependencies':['a']}])
            self.assertEqual(con.execute('SELECT count(*) FROM task_plans').fetchone()[0],0)
        self.assertEqual(len(REGISTRY),6)

    def test_delayed_manager_event_preserves_approved_plan(self):
        task=self.task()
        with self.db() as con:
            plan=self.manager.propose(con,task.task_id,'test',[{'name':'a','role':'data_worker'}])
            self.manager.approve(con,task.task_id,plan['plan_version'],'u1')
        self.dispatcher.dispatch_once()
        self.dispatcher.consume_once('manager',self.manager.handle)
        with self.db() as con:
            self.assertEqual(con.execute('SELECT status FROM agent_tasks WHERE id=?',(task.task_id,)).fetchone()[0],'running')
