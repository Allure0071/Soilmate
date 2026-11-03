"""Per-task Manager, immutable plan versions and DAG/approval control."""
import json
import re
from .events import EventStore
from .contracts import AgentEvent, Producer
from .router import now, uid
from .registry import REGISTRY


def emit(con, task_id, kind, payload, key):
    EventStore().append(con, AgentEvent(event_id=uid('evt'), event_type=kind, event_version=1,
        occurred_at=now(), producer=Producer(type='manager', id='task_manager'), task_id=task_id,
        correlation_id=task_id, idempotency_key=key,
        payload={'target_consumer': 'audit', **payload}))


def owned(con, task_id, user_id):
    row = con.execute('''SELECT t.* FROM agent_tasks t JOIN projects p ON p.id=t.project_id
                         WHERE t.id=? AND p.owner_user_id=?''', (task_id,user_id)).fetchone()
    if row is None:
        raise PermissionError('task not found')
    return row


class TaskManager:
    def handle(self, con, event):
        task = con.execute('SELECT * FROM agent_tasks WHERE id=?', (event.task_id,)).fetchone()
        if task is None:
            raise ValueError('task missing')
        if not task['manager_session_id']:
            session = uid('manager')
            stamp = now().isoformat()
            con.execute('''INSERT INTO agent_sessions(id,task_id,role,status,created_at,updated_at)
                           VALUES(?,?,'manager','active',?,?)''', (session, task['id'],stamp,stamp))
            con.execute("UPDATE agent_tasks SET manager_session_id=?,status=CASE WHEN status='queued' THEN 'planning' ELSE status END WHERE id=?",
                        (session,task['id']))
            emit(con,task['id'],'manager.assigned',{'session_id':session},'manager:'+task['id'])
        if event.payload.get('intent') == 'task_modification':
            plan = con.execute('SELECT * FROM task_plans WHERE task_id=? AND version=?',
                               (task['id'],task['active_plan_version'])).fetchone()
            if plan:
                rows = con.execute('SELECT * FROM task_steps WHERE task_id=? AND plan_version=?',
                                   (task['id'],plan['version'])).fetchall()
                specs = []
                names = {r['id']:r['step_name'] for r in rows}
                for row in rows:
                    deps = [names[r[0]] for r in con.execute('SELECT depends_on_step_id FROM step_dependencies WHERE step_id=?',(row['id'],))]
                    specs.append({'name':row['step_name'],'role':row['worker_type'],'dependencies':deps,
                                  'config':json.loads(row['config_json']), 'timeout_seconds':row['timeout_seconds'],
                                  'max_attempts':row['max_attempts']})
                msg = con.execute('SELECT content FROM agent_messages WHERE id=?', (event.payload['message_id'],)).fetchone()
                constraints = json.loads(plan['constraints_json'])
                constraints['requested_change'] = msg[0]
                reduction=re.search(r'降低\s*(\d+(?:\.\d+)?)\s*[%％]',msg[0])
                if reduction and isinstance(constraints.get('budget'),(int,float)):
                    percent=float(reduction.group(1))
                    if not 0<=percent<=100: raise ValueError('budget reduction out of range')
                    constraints['budget']=constraints['budget']*(1-percent/100)
                # A revision records the request; its approval is mandatory before execution.
                self.propose(con,task['id'],plan['goal'],specs,constraints)

    def propose(self, con, task_id, goal, specs, constraints=None):
        if not specs or len(specs)>50:
            raise ValueError('plan requires 1..50 steps')
        names = [s['name'] for s in specs]
        if len(names)!=len(set(names)):
            raise ValueError('duplicate step names')
        dependencies = {s['name']:set(s.get('dependencies',[])) for s in specs}
        for spec in specs:
            if spec['role'] not in REGISTRY or not dependencies[spec['name']] <= set(names):
                raise ValueError('unknown worker or dependency')
            config = spec.get('config',{})
            allowed_config={'value','delay_seconds','fail_first'}
            if spec['role'] in ('data_worker','mds_worker'):
                allowed_config |= {'execution_mode','dataset_path','allowed_data_root','config_path','rech_script','output_root','timeout_seconds'}
                if config.get('execution_mode') == 'professional':
                    required={'dataset_path','allowed_data_root'}
                    if spec['role']=='mds_worker': required |= {'config_path','rech_script','output_root'}
                    if not required <= set(config):
                        raise ValueError('professional worker config missing required paths')
            if set(config)-allowed_config:
                raise ValueError('unsupported worker config')
            if not 0 < spec.get('timeout_seconds',30) <= 300 or not 1 <= spec.get('max_attempts',2) <= 3:
                raise ValueError('invalid timeout or retry limit')
        remaining = {n:set(ds) for n,ds in dependencies.items()}
        while remaining:
            ready = {n for n,ds in remaining.items() if not ds}
            if not ready:
                raise ValueError('cyclic dependencies')
            remaining = {n:ds-ready for n,ds in remaining.items() if n not in ready}
        task = con.execute('SELECT * FROM agent_tasks WHERE id=?',(task_id,)).fetchone()
        if task is None or task['status']=='cancelled':
            raise ValueError('task missing or cancelled')
        version = con.execute('SELECT coalesce(max(version),0)+1 FROM task_plans WHERE task_id=?',(task_id,)).fetchone()[0]
        stamp = now().isoformat()
        con.execute('INSERT INTO task_plans VALUES(?,?,?,?,?,?,?)',
                    (uid('plan'),task_id,version,goal,json.dumps(constraints or {},ensure_ascii=False),'pending',stamp))
        ids = {n:uid('step') for n in names}
        for spec in specs:
            con.execute('''INSERT INTO task_steps(id,task_id,plan_version,worker_type,step_name,status,
                input_artifact_ids_json,output_artifact_ids_json,timeout_seconds,config_json,max_attempts)
                VALUES(?,?,?,?,?,'pending','[]','[]',?,?,?)''',
                (ids[spec['name']],task_id,version,spec['role'],spec['name'],spec.get('timeout_seconds',30),
                 json.dumps(spec.get('config',{}),ensure_ascii=False),spec.get('max_attempts',2)))
            for dep in dependencies[spec['name']]:
                con.execute('INSERT INTO step_dependencies VALUES(?,?)',(ids[spec['name']],ids[dep]))
        con.execute("UPDATE task_steps SET status='superseded' WHERE task_id=? AND plan_version<>? AND status NOT IN ('succeeded','failed','cancelled')",(task_id,version))
        con.execute("UPDATE agent_tasks SET active_plan_version=?,status='waiting_for_user' WHERE id=?",(version,task_id))
        approval = uid('approval')
        con.execute("INSERT INTO approval_requests(id,task_id,plan_version,action,status,requested_at) VALUES(?,?,?,'execute_plan','pending',?)",(approval,task_id,version,stamp))
        emit(con,task_id,'plan.proposed',{'plan_version':version,'approval_id':approval},f'plan:{task_id}:{version}')
        return {'task_id':task_id,'plan_version':version,'approval_id':approval,'step_ids':ids}

    def approve(self, con, task_id, version, user_id):
        task = owned(con,task_id,user_id)
        if task['active_plan_version']!=version or task['cancel_requested']:
            raise ValueError('stale plan or cancelled task')
        prior=con.execute("SELECT status FROM approval_requests WHERE task_id=? AND plan_version=?",(task_id,version)).fetchone()
        if prior and prior[0]=='approved': return
        con.execute("UPDATE approval_requests SET status='approved',decided_by=?,decided_at=? WHERE task_id=? AND plan_version=? AND status='pending'",(user_id,now().isoformat(),task_id,version))
        con.execute("UPDATE task_steps SET status='blocked' WHERE task_id=? AND plan_version=? AND status='pending'",(task_id,version))
        con.execute("UPDATE agent_tasks SET status='running' WHERE id=?",(task_id,))
        emit(con,task_id,'approval.granted',{'plan_version':version,'target_consumer':'runtime'},f'approved:{task_id}:{version}')

    def cancel(self, con, task_id, user_id):
        owned(con,task_id,user_id)
        con.execute("UPDATE agent_tasks SET cancel_requested=1,status='cancelled' WHERE id=?",(task_id,))
        con.execute("UPDATE task_steps SET status='cancelled' WHERE task_id=? AND status IN ('pending','blocked','ready','retry')",(task_id,))
        emit(con,task_id,'task.cancelled',{},'cancel:'+task_id)
