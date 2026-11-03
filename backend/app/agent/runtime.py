"""Background Test Worker scheduler with durable claims, retries and cancellation."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from .contracts import WorkerInput, WorkerResult
from .registry import REGISTRY,TestWorker
from .professional_workers import execute_professional
from .validation_decision import validate, decide
from .report_worker import build_report
from .router import uid,now
from .manager import emit


class WorkerRuntime:
    def __init__(self,connection_factory,artifacts,max_workers=2):
        self.db=connection_factory
        self.artifacts=artifacts
        self.max_workers=max_workers

    def handle(self,con,event):
        # Inbox handler performs only short scheduling metadata changes.
        if event.event_type=='approval.granted': self.refresh(con,event.task_id)

    def refresh(self,con,task_id=None):
        con.execute('''UPDATE task_steps SET status='ready' WHERE status='blocked'
            AND (? IS NULL OR task_id=?) AND EXISTS(SELECT 1 FROM agent_tasks t
              WHERE t.id=task_steps.task_id AND t.status='running' AND t.cancel_requested=0
              AND t.active_plan_version=task_steps.plan_version)
            AND NOT EXISTS(SELECT 1 FROM step_dependencies d JOIN task_steps p ON p.id=d.depends_on_step_id
              WHERE d.step_id=task_steps.id AND p.status!='succeeded')''',(task_id,task_id))

    def claim(self):
        with self.db() as con:
            con.execute('BEGIN IMMEDIATE')
            self.refresh(con)
            step=con.execute('''SELECT s.* FROM task_steps s JOIN agent_tasks t ON t.id=s.task_id
              WHERE s.status IN ('ready','retry') AND t.status='running' AND t.cancel_requested=0
              AND t.active_plan_version=s.plan_version AND s.attempt<s.max_attempts
              AND EXISTS(SELECT 1 FROM approval_requests a WHERE a.task_id=s.task_id
                AND a.plan_version=s.plan_version AND a.status='approved') ORDER BY s.rowid LIMIT 1''').fetchone()
            if step is None: return None
            attempt=step['attempt']+1
            run_id,session=uid('run'),uid('session')
            key=f"{step['task_id']}:{step['plan_version']}:{step['id']}"
            stamp=now().isoformat()
            con.execute('''INSERT INTO agent_sessions(id,task_id,role,status,created_at,updated_at)
                VALUES(?,?,?,'active',?,?)''',(session,step['task_id'],step['worker_type'],stamp,stamp))
            con.execute('''INSERT INTO worker_runs(id,task_id,step_id,plan_version,session_id,attempt,
                execution_key,status,started_at,lease_until) VALUES(?,?,?,?,?,?,?,'running',?,?)''',
                (run_id,step['task_id'],step['id'],step['plan_version'],session,attempt,key,stamp,
                 (now()+timedelta(seconds=step['timeout_seconds']+5)).isoformat()))
            con.execute("INSERT OR IGNORE INTO execution_claims VALUES(?,?,?,'running',NULL,?)",(key,step['task_id'],step['id'],stamp))
            con.execute("UPDATE task_steps SET status='running',attempt=? WHERE id=?",(attempt,step['id']))
            emit(con,step['task_id'],'worker.started',{'run_id':run_id,'step_id':step['id']},'started:'+run_id)
            return run_id

    def execute(self,run_id):
        try:
            self._execute(run_id)
        except Exception as exc:
            # Missing/corrupt input or unexpected setup errors require review, not blind rerun.
            with self.db() as con:
                con.execute('BEGIN IMMEDIATE')
                run=con.execute('SELECT * FROM worker_runs WHERE id=?',(run_id,)).fetchone()
                if run and run['status']=='running':
                    con.execute("UPDATE worker_runs SET status='recovery_required',error=?,ended_at=? WHERE id=?",(str(exc)[:500],now().isoformat(),run_id))
                    con.execute("UPDATE task_steps SET status='waiting_for_user' WHERE id=?",(run['step_id'],))
                    con.execute("UPDATE agent_tasks SET status='waiting_for_user' WHERE id=? AND status='running'",(run['task_id'],))
                    emit(con,run['task_id'],'task.waiting_user',{'run_id':run_id,'reason':str(exc)[:500]},'review:'+run_id)

    def _execute(self,run_id):
        with self.db() as con:
            run=dict(con.execute('SELECT * FROM worker_runs WHERE id=?',(run_id,)).fetchone())
            if run['status']!='running': return
            step=dict(con.execute('SELECT * FROM task_steps WHERE id=?',(run['step_id'],)).fetchone())
            task=dict(con.execute('SELECT * FROM agent_tasks WHERE id=?',(run['task_id'],)).fetchone())
            input_ids=[r[0] for r in con.execute('''SELECT l.artifact_id FROM step_dependencies d
                JOIN worker_runs r ON r.step_id=d.depends_on_step_id AND r.status='succeeded'
                JOIN artifact_links l ON l.run_id=r.id AND l.direction='output' WHERE d.step_id=?''',(step['id'],))]
            inputs=[self.artifacts.read(con,a,task['id'],task['project_id']) for a in input_ids]
            for artifact_id in input_ids:
                con.execute("INSERT INTO artifact_links VALUES(?,?,'input')",(run_id,artifact_id))
        request=WorkerInput(task_id=task['id'],plan_version=run['plan_version'],step_id=step['id'],
            session_id=run['session_id'],allowed_tool_ids=list(REGISTRY[step['worker_type']].allowed_tools),input_artifact_ids=input_ids)
        started=time.monotonic()
        def cancelled():
            if time.monotonic()-started>=step['timeout_seconds']: return True
            with self.db() as con:
                current=con.execute('SELECT cancel_requested,active_plan_version FROM agent_tasks WHERE id=?',(task['id'],)).fetchone()
                return bool(current[0] or current[1]!=run['plan_version'])
        try:
            worker_config={**json.loads(step['config_json']),'_attempt':run['attempt']}
            if step['worker_type'] in ('data_worker','mds_worker') and worker_config.get('execution_mode') == 'professional':
                content=execute_professional(step['worker_type'].replace('_worker',''),worker_config,inputs,cancelled)
            elif step['worker_type'] == 'validation_worker' and worker_config.get('execution_mode') == 'professional':
                content=validate(inputs,worker_config)
            elif step['worker_type'] == 'decision_worker' and worker_config.get('execution_mode') == 'professional':
                content=decide(inputs,worker_config)
            elif step['worker_type'] == 'report_worker' and worker_config.get('execution_mode') == 'professional':
                content=build_report(inputs,worker_config)
            else:
                content=TestWorker().execute(request,worker_config,inputs,cancelled)
            with self.db() as con:
                con.execute('BEGIN IMMEDIATE')
                current=con.execute('SELECT * FROM agent_tasks WHERE id=?',(task['id'],)).fetchone()
                state=con.execute('SELECT status FROM worker_runs WHERE id=?',(run_id,)).fetchone()[0]
                if state!='running': return
                if current['cancel_requested'] or current['active_plan_version']!=run['plan_version']:
                    raise InterruptedError('task cancelled or plan superseded')
                artifact_kind={'data_worker':'dataset_profile','mds_worker':'mds_result','validation_worker':'validation_report','decision_worker':'decision_recommendation','report_worker':'soil_health_report'}.get(step['worker_type'],'test_worker_result')
                artifact_id=self.artifacts.publish(con,run,task['project_id'],content,artifact_kind)
                summary='Professional worker completed' if step['worker_type'] in ('data_worker','mds_worker') and worker_config.get('execution_mode') == 'professional' else 'Test Worker completed'
                result=WorkerResult(step_id=step['id'],status='succeeded',output_artifact_ids=[artifact_id],summary=summary)
                con.execute("UPDATE worker_runs SET status='succeeded',ended_at=?,result_json=? WHERE id=?",(now().isoformat(),result.model_dump_json(),run_id))
                con.execute("UPDATE execution_claims SET status='succeeded',artifact_id=?,updated_at=? WHERE execution_key=?",(artifact_id,now().isoformat(),run['execution_key']))
                con.execute("UPDATE task_steps SET status='succeeded',output_artifact_ids_json=? WHERE id=?",(json.dumps([artifact_id]),step['id']))
                con.execute("UPDATE agent_sessions SET status='completed',updated_at=? WHERE id=?",(now().isoformat(),run['session_id']))
                emit(con,task['id'],'worker.completed',{'run_id':run_id,'artifact_ids':[artifact_id]},'completed:'+run_id)
        except Exception as exc:
            with self.db() as con:
                con.execute('BEGIN IMMEDIATE')
                row=con.execute('SELECT status FROM worker_runs WHERE id=?',(run_id,)).fetchone()
                if row[0]!='running': return
                status='timed_out' if time.monotonic()-started>=step['timeout_seconds'] else ('cancelled' if isinstance(exc,InterruptedError) else 'failed')
                con.execute('UPDATE worker_runs SET status=?,error=?,ended_at=? WHERE id=?',(status,str(exc)[:500],now().isoformat(),run_id))
                current=con.execute('SELECT cancel_requested,active_plan_version FROM agent_tasks WHERE id=?',(task['id'],)).fetchone()
                next_state='superseded' if current[1]!=run['plan_version'] else ('cancelled' if current[0] else ('retry' if run['attempt']<step['max_attempts'] else 'failed'))
                con.execute('UPDATE task_steps SET status=? WHERE id=?',(next_state,step['id']))
                con.execute("UPDATE agent_sessions SET status='failed' WHERE id=?",(run['session_id'],))
                emit(con,task['id'],'worker.failed',{'run_id':run_id,'status':status},'failed:'+run_id)

    def recover(self):
        with self.db() as con:
            con.execute('BEGIN IMMEDIATE')
            rows=con.execute("SELECT * FROM worker_runs WHERE status='running' AND lease_until<?",(now().isoformat(),)).fetchall()
            for run in rows:
                con.execute("UPDATE worker_runs SET status='failed',error='expired Test Worker lease',ended_at=? WHERE id=?",(now().isoformat(),run['id']))
                step=con.execute('SELECT attempt,max_attempts FROM task_steps WHERE id=?',(run['step_id'],)).fetchone()
                task=con.execute('SELECT cancel_requested,active_plan_version FROM agent_tasks WHERE id=?',(run['task_id'],)).fetchone()
                status='cancelled' if task[0] else ('superseded' if task[1]!=run['plan_version'] else ('retry' if step[0]<step[1] else 'failed'))
                con.execute("UPDATE task_steps SET status=? WHERE id=? AND status='running'",(status,run['step_id']))
                emit(con,run['task_id'],'worker.failed',{'run_id':run['id'],'reason':'lease_expired'},'expired:'+run['id'])

    def tick(self):
        self.recover()
        ids=[]
        for _ in range(self.max_workers):
            claimed=self.claim()
            if claimed: ids.append(claimed)
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            list(pool.map(self.execute,ids))
        with self.db() as con:
            con.execute('BEGIN IMMEDIATE')
            previous={r['id']:r['status'] for r in con.execute("SELECT id,status FROM agent_tasks WHERE status='running'")}
            con.execute("""UPDATE agent_tasks SET status='failed' WHERE status='running' AND EXISTS(
                SELECT 1 FROM task_steps s WHERE s.task_id=agent_tasks.id AND s.plan_version=agent_tasks.active_plan_version AND s.status='failed')""")
            con.execute("""UPDATE agent_tasks SET status='completed' WHERE status='running' AND EXISTS(
                SELECT 1 FROM task_steps s WHERE s.task_id=agent_tasks.id AND s.plan_version=agent_tasks.active_plan_version)
                AND NOT EXISTS(SELECT 1 FROM task_steps s WHERE s.task_id=agent_tasks.id
                  AND s.plan_version=agent_tasks.active_plan_version AND s.status!='succeeded')""")
            for task_id in previous:
                status=con.execute('SELECT status FROM agent_tasks WHERE id=?',(task_id,)).fetchone()[0]
                if status in ('completed','failed'):
                    emit(con,task_id,'task.'+status,{},f'task-terminal:{task_id}:'+status+':'+str(con.execute('SELECT active_plan_version FROM agent_tasks WHERE id=?',(task_id,)).fetchone()[0]))
        return len(ids)
