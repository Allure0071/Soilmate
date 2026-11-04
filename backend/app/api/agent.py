"""Authenticated Global Router and read-only task/event endpoints."""

import json
import sqlite3
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from ..agent.router import GlobalRouter
from ..scientific.research_store import connect, one, many, ROOT
from ..agent.manager import TaskManager
from ..agent.registry import REGISTRY
from ..agent.artifact_store import ArtifactStore
from ..agent.soil_expert import SoilExpert
from .auth import current_user_id
from ..models.gateway import ModelGateway, ModelUnavailable
from ..models.grounded import answer_question
from ..agent import local_assistant
from ..assessment import evidence as assessment_evidence, store as assessment_store

router = APIRouter(prefix="/api/agent", tags=["Super-agent Phase 2"])
global_router = GlobalRouter()


class MessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    task_id: Optional[str] = None
    message_id: Optional[str] = None


class ExpertQueryIn(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


def owned_task(con, task_id, user_id):
    row = one(con, """SELECT t.* FROM agent_tasks t JOIN projects p ON p.id=t.project_id
                     WHERE t.id=? AND p.owner_user_id=?""", (task_id, user_id))
    if row is None:
        raise HTTPException(404, "任务不存在")
    return row


@router.post("/messages")
def route_message(payload: MessageIn):
    try:
        with connect() as con:
            return global_router.route(con, current_user_id(), payload.text, payload.project_id,
                                       payload.conversation_id, payload.task_id, payload.message_id)
    except PermissionError:
        raise HTTPException(404, "项目或任务不存在")
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@router.get("/tasks")
def list_tasks(project_id: str):
    user_id = current_user_id()
    with connect() as con:
        if one(con, "SELECT 1 AS ok FROM projects WHERE id=? AND owner_user_id=?", (project_id, user_id)) is None:
            raise HTTPException(404, "项目不存在")
        return many(con, "SELECT * FROM agent_tasks WHERE project_id=? ORDER BY created_at DESC,id DESC", (project_id,))


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    with connect() as con:
        return owned_task(con, task_id, current_user_id())


@router.get("/tasks/{task_id}/events")
def get_task_events(task_id: str, after_seq: int = 0):
    if after_seq < 0:
        raise HTTPException(422, "after_seq 必须非负")
    with connect() as con:
        owned_task(con, task_id, current_user_id())
        return global_router.events.replay(con, task_id, after_seq)


@router.get("/artifacts/{artifact_id}")
def get_artifact(artifact_id: str):
    with connect() as con:
        row = one(con, """SELECT a.* FROM artifacts a JOIN projects p ON p.id=a.project_id
            WHERE a.id=? AND p.owner_user_id=?""", (artifact_id, current_user_id()))
        if row is None:
            raise HTTPException(404, "结果不存在")
        return row


class StepSpec(BaseModel):
    name: str = Field(min_length=1,max_length=80)
    role: str
    dependencies: list[str] = Field(default_factory=list)
    config: dict = Field(default_factory=dict)
    timeout_seconds: int = Field(default=30,ge=1,le=300)
    max_attempts: int = Field(default=2,ge=1,le=3)


class PlanIn(BaseModel):
    goal: str = Field(min_length=1,max_length=500)
    steps: list[StepSpec] = Field(min_length=1,max_length=50)
    constraints: dict = Field(default_factory=dict)


class ApproveIn(BaseModel):
    plan_version: int = Field(ge=1)


@router.post('/tasks/{task_id}/plans')
def propose_plan(task_id: str,payload: PlanIn):
    try:
        with connect() as con:
            con.execute('BEGIN IMMEDIATE')
            owned_task(con,task_id,current_user_id())
            return TaskManager().propose(con,task_id,payload.goal,
                [s.model_dump() for s in payload.steps],payload.constraints)
    except ValueError as exc:
        raise HTTPException(422,str(exc))


@router.post('/tasks/{task_id}/approve')
def approve_plan(task_id: str,payload: ApproveIn):
    try:
        with connect() as con:
            con.execute('BEGIN IMMEDIATE')
            owned_task(con,task_id,current_user_id())
            TaskManager().approve(con,task_id,payload.plan_version,current_user_id())
        return {'status':'approved','plan_version':payload.plan_version}
    except ValueError as exc:
        raise HTTPException(409,str(exc))


@router.post('/tasks/{task_id}/cancel')
def cancel_task(task_id: str):
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        owned_task(con,task_id,current_user_id())
        TaskManager().cancel(con,task_id,current_user_id())
    return {'status':'cancelled'}


@router.get('/tasks/{task_id}/runs')
def list_worker_runs(task_id: str):
    with connect() as con:
        owned_task(con,task_id,current_user_id())
        return many(con,'SELECT * FROM worker_runs WHERE task_id=? ORDER BY started_at,id',(task_id,))


@router.get('/tasks/{task_id}/failures')
def list_delivery_failures(task_id: str):
    with connect() as con:
        owned_task(con,task_id,current_user_id())
        return {'inbox':many(con,"""SELECT i.* FROM consumer_inbox i JOIN agent_events e ON e.id=i.event_id
            WHERE e.task_id=? AND i.status='failed'""",(task_id,)),
            'outbox':many(con,"""SELECT d.* FROM event_outbox_deadletters d JOIN agent_events e ON e.id=d.event_id
            WHERE e.task_id=?""",(task_id,))}


@router.get('/workers')
def list_worker_definitions():
    current_user_id()
    return [{'role':key,'capabilities':list(value.capabilities),'allowed_tools':list(value.allowed_tools),
             'execution_mode':'test_only','model_profile':value.model_profile} for key,value in REGISTRY.items()]


@router.get('/artifacts/{artifact_id}/content')
def read_artifact_content(artifact_id: str):
    row=get_artifact(artifact_id)
    try:
        with connect() as con:
            return ArtifactStore(ROOT/'data'/'agent_artifacts').read(con,artifact_id,
                row['task_id'],row['project_id'],current_user_id())
    except (ValueError,OSError):
        raise HTTPException(409,'Artifact missing or hash verification failed')


@router.post('/tasks/{task_id}/expert')
def ask_soil_expert(task_id: str, payload: ExpertQueryIn):
    """Answer with task-scoped Artifact evidence; never infer missing results."""
    with connect() as con:
        task=owned_task(con,task_id,current_user_id())
        rows=many(con,"SELECT id,kind,project_id FROM artifacts WHERE task_id=? ORDER BY created_at,id",(task_id,))
        store=ArtifactStore(ROOT/'data'/'agent_artifacts')
        facts=[]
        for row in rows:
            try:
                content=store.read(con,row['id'],task_id,task['project_id'],current_user_id())
            except (ValueError,OSError,PermissionError):
                continue
            facts.append({'artifact_id':row['id'],'kind':row['kind'],'content':content})
    return SoilExpert(ROOT.parent/'土壤健康知识库').answer(payload.query,facts)


class ModelQueryIn(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=4000)
    task_id: Optional[str] = Field(default=None, max_length=256)


@router.get('/model/status')
def model_status():
    current_user_id()
    status = ModelGateway().status()
    if not status.get('available'):
        status['local_fallback'] = True
        status['message'] = '研究助手已就绪（本地知识）'
    return status


def _assessment_context(con, task_id, user_id):
    if not task_id:
        return None
    try:
        assessment_store.init_assessment(con)
        row = assessment_store.get_task_row(con, task_id, user_id)
    except sqlite3.Error:
        return None
    if not row or not row.get('result_json'):
        return None
    try:
        result = json.loads(row['result_json'])
    except (TypeError, ValueError):
        return None
    analysis = result.get('analysis') if isinstance(result, dict) and result.get('kind') == 'analysis' else None
    if not analysis:
        return None
    payload = json.loads(row['payload_json'])
    measurement = None
    measurement_ids = payload.get('measurement_ids') or []
    if measurement_ids:
        measurement = assessment_store.get_measurement(con, measurement_ids[0], user_id)
    session = assessment_store.get_session(con, row['session_id'], user_id)
    chain = assessment_evidence.build_evidence_chain(analysis, measurement, session, task_id)
    return {
        'analysis': analysis,
        'task_id': task_id,
        'session_id': row['session_id'],
        'sample': measurement.get('sample_alias') if measurement else None,
        'measurement_id': measurement.get('id') if measurement else None,
        'chain': chain,
        'evidence_refs': assessment_evidence.evidence_refs(chain, task_id),
    }


@router.post('/expert')
def ask_model_expert(payload: ModelQueryIn):
    user_id=current_user_id()
    facts=[]
    assessment_context=None
    with connect() as con:
        assessment_context = _assessment_context(con, payload.task_id, user_id)
        if payload.task_id and not assessment_context:
            task=owned_task(con,payload.task_id,user_id)
            rows=many(con,'SELECT id,kind FROM artifacts WHERE task_id=? ORDER BY created_at,id',(payload.task_id,))
            store=ArtifactStore(ROOT/'data'/'agent_artifacts')
            for row in rows:
                try: content=store.read(con,row['id'],payload.task_id,task['project_id'],user_id)
                except (ValueError,OSError,PermissionError): continue
                facts.append({'artifact_id':row['id'],'kind':row['kind'],'content':content})
    gateway=ModelGateway()
    model_ready=bool(gateway.status().get('available'))
    if assessment_context:
        if model_ready:
            try:
                return answer_question(payload.query,[{'artifact_id':payload.task_id,'kind':'assessment','content':assessment_context['analysis']}],[])
            except ModelUnavailable:
                pass
        return local_assistant.answer(payload.query, assessment_context)
    if payload.task_id and not facts:
        return {'answer':'当前任务没有可核验的结果记录，请先完成分析后再解释本次结果。','answer_type':'clarification','evidence_refs':[],'knowledge_refs':[],'uncertainty':'missing_task_artifact','model':None}
    expert=SoilExpert(ROOT.parent/'土壤健康知识库')
    baseline=expert.answer(payload.query,facts)
    if baseline.get('uncertainty')=='missing_task_artifact':
        return {**baseline,'model':None}
    if model_ready:
        try:
            return answer_question(payload.query,facts,baseline.get('knowledge_refs'))
        except ModelUnavailable:
            pass
    return local_assistant.answer(payload.query, None)
