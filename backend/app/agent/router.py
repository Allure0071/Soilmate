"""Deterministic Global Router; routes messages but never runs analysis tools."""

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .contracts import AgentEvent, Producer
from .events import EventStore


def now():
    return datetime.now(timezone.utc)


def uid(prefix):
    return prefix + "_" + uuid.uuid4().hex


class RouteResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal["general_knowledge_query", "domain_expert_query", "new_analysis_task",
                    "task_followup", "task_modification", "task_status_query",
                    "artifact_retrieval", "clarification"]
    target: Literal["soil_expert", "manager", "task_registry", "clarification"]
    conversation_id: Optional[str]
    task_id: Optional[str]
    message_id: Optional[str]
    event_ids: list[str] = Field(default_factory=list)
    candidate_task_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    clarification: Optional[str] = None


class GlobalRouter:
    def __init__(self, event_store: Optional[EventStore] = None):
        self.events = event_store or EventStore()

    @staticmethod
    def classify(text: str) -> str:
        value = text.strip().lower()
        if not value:
            return "clarification"
        if any(x in value for x in ("预算", "约束", "改成", "调整", "降低", "增加")) and any(
                x in value for x in ("降低", "增加", "修改", "调整", "改成", "%", "％")):
            return "task_modification"
        if any(x in value for x in ("之前的分析", "历史任务", "任务状态", "进度", "完成了吗")):
            return "task_status_query"
        if any(x in value for x in ("查看报告", "找出报告", "结果文件", "artifact", "来源记录")):
            return "artifact_retrieval"
        if any(x in value for x in ("帮我分析", "分析这份", "开始分析", "做一次mds", "做一次 mds", "筛选指标")):
            return "new_analysis_task"
        if any(x in value for x in ("这次", "当前", "刚才", "本次")) and any(
                x in value for x in ("为什么", "没有选择", "未选择", "结果", "指标")):
            return "task_followup"
        if "为什么" in value and any(x in value for x in ("没有选择", "未选择")):
            return "task_followup"
        if any(x in value for x in ("土壤", "mds", "soc", "cec", "指标", "肥力")):
            if any(x in value for x in ("mds", "soc", "cec", "指标", "空间验证", "随机交叉验证")):
                return "domain_expert_query"
            return "general_knowledge_query"
        return "clarification"

    @staticmethod
    def _owned_project(con: sqlite3.Connection, user_id: str, project_id: str):
        if con.execute("SELECT 1 FROM projects WHERE id=? AND owner_user_id=?", (project_id, user_id)).fetchone() is None:
            raise PermissionError("project not found or not owned by user")

    def _resolve_task(self, con, user_id, project_id, conversation_id, explicit_task_id, text):
        if explicit_task_id:
            row = con.execute("""SELECT t.id,t.project_id FROM agent_tasks t JOIN projects p ON p.id=t.project_id
                WHERE t.id=? AND p.owner_user_id=?""", (explicit_task_id, user_id)).fetchone()
            if row is None or (project_id and row["project_id"] != project_id):
                raise PermissionError("task not found or not owned by user")
            return row["id"]
        if not conversation_id:
            return None
        rows = con.execute("""SELECT t.id,t.task_type FROM agent_tasks t JOIN projects p ON p.id=t.project_id
            WHERE t.conversation_id=? AND p.owner_user_id=? AND
            t.status NOT IN ('completed','failed','cancelled') ORDER BY t.created_at DESC""",
            (conversation_id, user_id)).fetchall()
        if project_id:
            rows = [r for r in rows if con.execute("SELECT 1 FROM agent_tasks WHERE id=? AND project_id=?",
                                                  (r["id"], project_id)).fetchone()]
        if len(rows) == 1:
            return rows[0]["id"]
        # A single archived task in this conversation is unambiguous; multiple remain ambiguous.
        if not rows:
            history = con.execute("""SELECT t.id FROM agent_tasks t JOIN projects p ON p.id=t.project_id
                WHERE t.conversation_id=? AND p.owner_user_id=? AND (? IS NULL OR t.project_id=?)
                ORDER BY t.created_at DESC""", (conversation_id, user_id, project_id, project_id)).fetchall()
            if len(history) == 1:
                return history[0]["id"]
        return None

    def route(self, con: sqlite3.Connection, user_id: str, text: str,
              project_id: Optional[str] = None, conversation_id: Optional[str] = None,
              task_id: Optional[str] = None, message_id: Optional[str] = None) -> RouteResult:
        """Caller supplies one DB transaction. User message, task and events commit together."""
        if not text.strip() or len(text) > 4000:
            return RouteResult(intent="clarification", target="clarification", conversation_id=conversation_id,
                               task_id=None, message_id=None, clarification="请提供不超过 4000 字的具体问题或目标。")
        if project_id:
            self._owned_project(con, user_id, project_id)
        if message_id:
            earlier = con.execute("""SELECT m.conversation_id,m.task_id,m.content,c.user_id,c.project_id
                FROM agent_messages m JOIN agent_conversations c ON c.id=m.conversation_id WHERE m.id=?""",
                (message_id,)).fetchone()
            if earlier:
                if earlier["task_id"]:
                    self._resolve_task(con, user_id, project_id, conversation_id, earlier["task_id"], text)
                if (earlier["user_id"] != user_id or earlier["content"] != text or
                        (task_id and earlier["task_id"] != task_id) or
                        (conversation_id and earlier["conversation_id"] != conversation_id) or
                        (project_id and earlier["project_id"] not in (None, project_id))):
                    raise ValueError("message id reused for another request")
                saved = con.execute("SELECT id,payload_json FROM agent_events WHERE idempotency_key=?",
                                    ("route:" + message_id,)).fetchone()
                if saved is None:
                    raise RuntimeError("message exists without route event")
                import json
                payload = json.loads(saved["payload_json"])
                return RouteResult(intent=payload["intent"], target=payload["target_consumer"],
                                   conversation_id=earlier["conversation_id"], task_id=earlier["task_id"],
                                   message_id=message_id, event_ids=[saved["id"]])
        if project_id:
            self._owned_project(con, user_id, project_id)
        if conversation_id:
            conv = con.execute("SELECT user_id,project_id FROM agent_conversations WHERE id=?", (conversation_id,)).fetchone()
            if conv is None or conv["user_id"] != user_id or (project_id and conv["project_id"] not in (None, project_id)):
                raise PermissionError("conversation not found or not owned by user")
        intent = self.classify(text)
        linked_task = self._resolve_task(con, user_id, project_id, conversation_id, task_id, text)
        if intent in ("task_followup", "task_modification", "artifact_retrieval") and linked_task is None:
            return RouteResult(intent="clarification", target="clarification", conversation_id=conversation_id,
                               task_id=None, message_id=None, clarification="请指定本次分析的 task_id；当前无法确定你指的是哪次结果。")
        if intent == "new_analysis_task" and not project_id:
            return RouteResult(intent="clarification", target="clarification", conversation_id=conversation_id,
                               task_id=None, message_id=None, clarification="请先选择你有权限访问的项目。")
        if intent == "clarification":
            return RouteResult(intent="clarification", target="clarification", conversation_id=conversation_id,
                               task_id=None, message_id=None, clarification="请说明是专业问题、新分析、任务追问还是查看历史结果。")
        stamp = now().isoformat()
        if not conversation_id:
            conversation_id = uid("conv")
            con.execute("INSERT INTO agent_conversations VALUES(?,?,?,?,?)",
                        (conversation_id, user_id, project_id, stamp, stamp))
        message_id = message_id or uid("msg")
        if intent == "new_analysis_task":
            linked_task = uid("task")
            con.execute("""INSERT INTO agent_tasks(id,project_id,conversation_id,task_type,status,created_at,updated_at)
                VALUES(?,?,?,'mds_analysis','queued',?,?)""", (linked_task, project_id, conversation_id, stamp, stamp))
        target = "soil_expert" if intent in ("general_knowledge_query", "domain_expert_query", "task_followup") else "manager"
        if intent == "task_status_query":
            target = "task_registry"
        con.execute("INSERT INTO agent_messages(id,conversation_id,role,content,task_id,created_at) VALUES(?,?,'user',?,?,?)",
                    (message_id, conversation_id, text, linked_task, stamp))
        event_id = uid("evt")
        kind = "task.created" if intent == "new_analysis_task" else "router.intent_classified"
        event = AgentEvent(event_id=event_id, event_type=kind, event_version=1, occurred_at=now(),
                           producer=Producer(type="router", id="global_router"), task_id=linked_task,
                           conversation_id=conversation_id, correlation_id=message_id,
                           idempotency_key="route:" + message_id,
                           payload={"intent": intent, "target_consumer": target, "message_id": message_id})
        self.events.append(con, event)
        candidates = []
        artifacts = []
        if intent == "task_status_query":
            candidates = [row["id"] for row in con.execute("""SELECT t.id FROM agent_tasks t
                JOIN projects p ON p.id=t.project_id WHERE p.owner_user_id=?
                AND (? IS NULL OR t.project_id=?) ORDER BY t.created_at DESC,t.id DESC LIMIT 50""",
                (user_id, project_id, project_id)).fetchall()]
        if intent == "artifact_retrieval":
            artifacts = [row["id"] for row in con.execute("""SELECT a.id FROM artifacts a
                JOIN projects p ON p.id=a.project_id WHERE a.task_id=? AND p.owner_user_id=?
                ORDER BY a.created_at DESC,a.id DESC LIMIT 50""", (linked_task, user_id)).fetchall()]
        return RouteResult(intent=intent, target=target, conversation_id=conversation_id,
                           task_id=linked_task, message_id=message_id, event_ids=[event_id],
                           candidate_task_ids=candidates, artifact_ids=artifacts)
