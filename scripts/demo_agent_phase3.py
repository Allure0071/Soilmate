"""Create an isolated, synthetic Phase 3 execution package; never touches live data."""
import argparse
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from backend.app.scientific.research_store import SCHEMA
from backend.app.agent.migration import migrate_agent_schema
from backend.app.agent.migration_v3 import migrate_event_schema
from backend.app.agent.migration_v4 import migrate_runtime_schema
from backend.app.agent.router import GlobalRouter
from backend.app.agent.events import EventDispatcher,EventStore
from backend.app.agent.manager import TaskManager
from backend.app.agent.runtime import WorkerRuntime
from backend.app.agent.artifact_store import ArtifactStore


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    path=args.out/'demo.sqlite'
    @contextmanager
    def db():
        con=sqlite3.connect(path,timeout=10)
        con.row_factory=sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally: con.close()
    with db() as con:
        con.executescript(SCHEMA)
        con.execute('CREATE TABLE users(id TEXT PRIMARY KEY)')
        con.execute('ALTER TABLE projects ADD COLUMN owner_user_id TEXT')
        con.execute("INSERT INTO users VALUES('demo-user')")
        con.execute("INSERT INTO projects(id,name,created_at,owner_user_id) VALUES('demo','synthetic Runtime acceptance','now','demo-user')")
        con.execute("INSERT INTO schema_migrations VALUES(1,'demo')")
    with db() as con:
        migrate_agent_schema(con)
        migrate_event_schema(con)
        migrate_runtime_schema(con)
    with db() as con:
        routed=GlobalRouter().route(con,'demo-user','帮我分析这份数据','demo')
    dispatcher=EventDispatcher(db)
    manager=TaskManager()
    dispatcher.dispatch_once()
    dispatcher.consume_once('manager',manager.handle)
    with db() as con:
        proposed=manager.propose(con,routed.task_id,'synthetic Runtime acceptance',[
            {'name':'audit','role':'data_worker','config':{'value':'synthetic audit','delay_seconds':.2}},
            {'name':'methods','role':'soil_expert','config':{'value':'synthetic method check','delay_seconds':.2}},
            {'name':'report','role':'report_worker','dependencies':['audit','methods'],'config':{'value':'synthetic report'}}])
        manager.approve(con,routed.task_id,proposed['plan_version'],'demo-user')
    artifacts=ArtifactStore(args.out/'artifacts')
    runtime=WorkerRuntime(db,artifacts)
    for _ in range(10):
        while dispatcher.dispatch_once(): pass
        while dispatcher.consume_once('runtime',runtime.handle): pass
        runtime.tick()
        with db() as con:
            if con.execute('SELECT status FROM agent_tasks WHERE id=?',(routed.task_id,)).fetchone()[0]=='completed': break
    with db() as con:
        summary={'evidence_tier':'synthetic_demo','task_id':routed.task_id,
            'status':con.execute('SELECT status FROM agent_tasks WHERE id=?',(routed.task_id,)).fetchone()[0],
            'runs':[dict(r) for r in con.execute('SELECT * FROM worker_runs')],
            'artifacts':[dict(r) for r in con.execute('SELECT * FROM artifacts')],
            'events':EventStore().replay(con,routed.task_id)}
    (args.out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print({'status':summary['status'],'runs':len(summary['runs']),'artifacts':len(summary['artifacts'])})
    if summary['status']!='completed': raise SystemExit('demo did not complete')


if __name__=='__main__': main()
