"""Assessment P0 API used by the health-research workspace.

Endpoints follow the contract in docs/assessment-api/. Successful responses use
the {data, request_id, data_origin} envelope; errors use the structured error
envelope. The scoring engine is a deterministic research-preview implementation
(see engine.py) and is not a validated health-assessment model.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from ..api.auth import current_user_id
from ..scientific.research_store import many, now, uid
from ..assessment import demo as assessment_demo, engine, evidence, store as astore

router = APIRouter(prefix="/api/assessment", tags=["Assessment P0"])

TASK_RUNNING_AFTER = 1.2
TASK_DONE_AFTER = 3.0


def _request_id():
    return uid("req")


def ok(data, status=200):
    return JSONResponse({"data": data, "request_id": _request_id(), "data_origin": "real"}, status_code=status)


def error(status, code, message, fields=None, retryable=False):
    return JSONResponse({
        "error": {"code": code, "message": message, "fields": fields or [], "retryable": bool(retryable)},
        "request_id": _request_id(),
        "data_origin": "real",
    }, status_code=status)


def _elapsed_seconds(created_at):
    try:
        created = datetime.fromisoformat(created_at)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - created).total_seconds())
    except (TypeError, ValueError):
        return 0.0


class SessionIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    mode: Literal["quick", "deep"]
    crop_name: Optional[str] = Field(default=None, max_length=64)
    background: Optional[str] = Field(default="", max_length=2000)
    field_id: Optional[str] = Field(default=None, max_length=128)
    cycle_id: Optional[str] = Field(default=None, max_length=128)


class MeasurementValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    indicator_code: str = Field(min_length=1, max_length=32)
    value: float
    unit: Optional[str] = Field(default=None, max_length=16)
    method: Optional[str] = Field(default=None, max_length=200)
    source_type: str = Field(default="user_measurement", max_length=32)


class MeasurementIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    session_id: str = Field(min_length=1, max_length=64)
    sample_alias: str = Field(min_length=1, max_length=120)
    sampling_date: Optional[str] = Field(default=None, max_length=32)
    values: List[MeasurementValue] = Field(min_length=1, max_length=40)


class TaskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["quick_analysis", "deep_analysis"]
    session_id: str = Field(min_length=1, max_length=64)
    measurement_ids: List[str] = Field(min_length=1, max_length=10)
    field_id: Optional[str] = Field(default=None, max_length=128)
    cycle_id: Optional[str] = Field(default=None, max_length=128)


def _idempotent_replay(con, user_id, key, method, path, body):
    if not key:
        return None
    previous = astore.replay_idempotent(con, user_id, key, method, path, body)
    if previous == "conflict":
        return error(409, "IDEMPOTENCY_CONFLICT", "同一提交标识对应的内容发生变化，请返回核对后重新提交。", retryable=False)
    if previous:
        status, payload = previous
        return JSONResponse(payload, status_code=status)
    return None


@router.get("/indicators")
def indicators():
    current_user_id()
    items = []
    for item in engine.INDICATORS:
        items.append({
            "code": item["code"],
            "name": item["name"],
            "short": item["short"],
            "units": item["units"],
            "unit_required": item["unit_required"],
        })
    return ok({"items": items, "dictionary_version": engine.DICTIONARY_VERSION})


@router.post("/sessions")
def create_session(payload: SessionIn, idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    user_id = current_user_id()
    body = payload.model_dump()
    with astore.db() as con:
        replay = _idempotent_replay(con, user_id, idempotency_key, "POST", "/sessions", body)
        if replay is not None:
            return replay
        session = astore.create_session(con, user_id, payload.mode, payload.crop_name, payload.background,
                                        payload.field_id, payload.cycle_id)
        response = {"data": session, "request_id": _request_id(), "data_origin": "real"}
        astore.remember_idempotent(con, user_id, idempotency_key, "POST", "/sessions", body, 200, response)
        return JSONResponse(response, status_code=200)


@router.get("/sessions/{session_id}")
def read_session(session_id: str):
    user_id = current_user_id()
    with astore.db() as con:
        session = astore.get_session(con, session_id, user_id)
        if not session:
            return error(404, "SESSION_NOT_FOUND", "未找到该研究会话，或该会话不属于当前账号。", retryable=False)
        return ok(session)


@router.post("/measurements")
def create_measurement(payload: MeasurementIn, idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    user_id = current_user_id()
    body = payload.model_dump()
    codes = [value.indicator_code for value in payload.values]
    if len(codes) != len(set(codes)):
        return error(422, "DUPLICATE_INDICATOR", "本次录入中存在重复指标，请合并后再提交。", retryable=False)
    fields = []
    for value in payload.values:
        definition = engine.INDICATOR_MAP.get(value.indicator_code)
        if not definition:
            fields.append({"path": f"values.{value.indicator_code}", "message": "指标代码不在服务端字典中。"})
            continue
        if not math.isfinite(value.value) or abs(value.value) > 1e9:
            fields.append({"path": f"values.{value.indicator_code}.value", "message": "检测值必须是有限数值。"})
        if value.unit and value.unit not in definition["units"]:
            fields.append({"path": f"values.{value.indicator_code}.unit", "message": "报告单位与服务端字典不一致。"})
        if definition["unit_required"] and not value.unit:
            fields.append({"path": f"values.{value.indicator_code}.unit", "message": "该指标需要提供报告单位。"})
        if value.source_type != "user_measurement":
            fields.append({"path": f"values.{value.indicator_code}.source_type", "message": "健康研究只接受实测输入。"})
    if fields:
        return error(422, "INVALID_MEASUREMENT", "检测记录未通过服务端校验，请返回录入页修正。", fields=fields, retryable=False)
    with astore.db() as con:
        replay = _idempotent_replay(con, user_id, idempotency_key, "POST", "/measurements", body)
        if replay is not None:
            return replay
        session = astore.get_session(con, payload.session_id, user_id)
        if not session:
            return error(404, "SESSION_NOT_FOUND", "未找到该研究会话，或该会话不属于当前账号。", retryable=False)
        if session["mode"] == "deep" and payload.values and not session.get("field_id"):
            return error(422, "FIELD_REQUIRED", "深度分析需要先关联地块与种植周期。", retryable=False)
        measurement = astore.create_measurement(con, user_id, payload.session_id, {**body, "values": [value.model_dump() for value in payload.values]})
        response = {"data": measurement, "request_id": _request_id(), "data_origin": "real"}
        astore.remember_idempotent(con, user_id, idempotency_key, "POST", "/measurements", body, 200, response)
        return JSONResponse(response, status_code=200)


@router.get("/measurements/{measurement_id}")
def read_measurement(measurement_id: str):
    user_id = current_user_id()
    with astore.db() as con:
        measurement = astore.get_measurement(con, measurement_id, user_id)
        if not measurement:
            return error(404, "MEASUREMENT_NOT_FOUND", "未找到该检测记录，或该记录不属于当前账号。", retryable=False)
        return ok(measurement)


@router.post("/tasks")
def create_task(payload: TaskIn, idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    user_id = current_user_id()
    body = payload.model_dump()
    with astore.db() as con:
        replay = _idempotent_replay(con, user_id, idempotency_key, "POST", "/tasks", body)
        if replay is not None:
            return replay
        session = astore.get_session(con, payload.session_id, user_id)
        if not session:
            return error(404, "SESSION_NOT_FOUND", "未找到该研究会话，或该会话不属于当前账号。", retryable=False)
        if session["mode"] == "deep" and not (session.get("field_id") and session.get("cycle_id")):
            return error(422, "FIELD_REQUIRED", "深度分析需要先关联地块与种植周期。", retryable=False)
        measurements = []
        for measurement_id in payload.measurement_ids:
            measurement = astore.get_measurement(con, measurement_id, user_id)
            if not measurement or measurement["session_id"] != payload.session_id:
                return error(404, "MEASUREMENT_NOT_FOUND", "检测记录与当前会话不匹配。", retryable=False)
            measurements.append(measurement)
        task_id = astore.create_task(con, user_id, payload.session_id, payload.type, body)
        response = {
            "data": {"task_id": task_id, "type": payload.type, "session_id": payload.session_id, "status": "queued", "created_at": now()},
            "request_id": _request_id(),
            "data_origin": "real",
        }
        astore.remember_idempotent(con, user_id, idempotency_key, "POST", "/tasks", body, 202, response)
        return JSONResponse(response, status_code=202)


def _task_payload(row, con):
    status = row["status"]
    created_at = row["created_at"]
    elapsed = _elapsed_seconds(created_at)
    result = json.loads(row["result_json"]) if row.get("result_json") else None
    error_payload = json.loads(row["error_json"]) if row.get("error_json") else None
    if status in ("queued", "running"):
        if elapsed >= TASK_DONE_AFTER:
            session = astore.get_session(con, row["session_id"], row["user_id"])
            payload = json.loads(row["payload_json"])
            measurement = astore.get_measurement(con, payload["measurement_ids"][0], row["user_id"])
            analysis = engine.build_analysis(session, measurement)
            result = {"kind": "analysis", "analysis": analysis}
            status = "completed"
            astore.update_task(con, row["id"], "completed", result=result)
        elif elapsed >= TASK_RUNNING_AFTER:
            status = "running"
            astore.update_task(con, row["id"], "running")
    stages = {
        "queued": "任务已排队",
        "running": "正在评价检测记录",
        "completed": "本次分析完成",
    }
    agent_tasks = []
    if status == "running":
        agent_tasks = [
            {"id": "check", "summary": "核对指标、单位与样本身份", "status": "completed"},
            {"id": "score", "summary": "计算功能分与综合区间", "status": "running"},
            {"id": "gaps", "summary": "整理证据缺口与待核实项", "status": "queued"},
        ]
    elif status in ("completed", "partial"):
        agent_tasks = [
            {"id": "check", "summary": "核对指标、单位与样本身份", "status": "completed"},
            {"id": "score", "summary": "计算功能分与综合区间", "status": "completed"},
            {"id": "gaps", "summary": "整理证据缺口与待核实项", "status": "completed"},
        ]
    sample_alias = None
    try:
        payload = json.loads(row["payload_json"])
        measurement_ids = payload.get("measurement_ids") or []
        if measurement_ids:
            measurement = astore.get_measurement(con, measurement_ids[0], row["user_id"])
            sample_alias = measurement.get("sample_alias") if measurement else None
    except (KeyError, TypeError, ValueError):
        sample_alias = None
    return {
        "task_id": row["id"],
        "type": row["type"],
        "session_id": row["session_id"],
        "sample_alias": sample_alias,
        "status": status,
        "current_stage": stages.get(status, ""),
        "agent_tasks": agent_tasks,
        "result": result if status in ("completed", "partial") else None,
        "error": error_payload,
        "created_at": created_at,
        "updated_at": row["updated_at"],
    }


@router.get("/tasks")
def list_tasks(limit: int = 5):
    user_id = current_user_id()
    limit = max(1, min(20, int(limit)))
    with astore.db() as con:
        try:
            assessment_demo.ensure_demo_assessment(con, user_id)
        except Exception:
            pass
        rows = many(con, "SELECT * FROM assessment_tasks WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
        items = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            sample_alias, sampling_date = None, None
            measurement_ids = payload.get("measurement_ids") or []
            if measurement_ids:
                measurement = astore.get_measurement(con, measurement_ids[0], user_id)
                if measurement:
                    sample_alias = measurement.get("sample_alias")
                    sampling_date = measurement.get("sampling_date")
            items.append({
                "task_id": row["id"],
                "type": row["type"],
                "status": row["status"],
                "session_id": row["session_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "sample_alias": sample_alias,
                "sampling_date": sampling_date,
            })
        return ok({"items": items})


@router.get("/tasks/{task_id}/evidence")
def task_evidence(task_id):
    user_id = current_user_id()
    with astore.db() as con:
        row = astore.get_task_row(con, task_id, user_id)
        if not row:
            return error(404, "TASK_NOT_FOUND", "任务不存在或无权访问。")
        if not row.get("result_json"):
            return error(409, "TASK_NOT_READY", "任务尚未形成结果，请稍后再试。")
        try:
            result = json.loads(row["result_json"])
            analysis = result.get("analysis") if isinstance(result, dict) else None
        except (TypeError, ValueError):
            analysis = None
        if not analysis:
            return error(409, "TASK_NOT_READY", "任务结果尚不可读取。")
        payload = json.loads(row["payload_json"])
        measurement = None
        measurement_ids = payload.get("measurement_ids") or []
        if measurement_ids:
            measurement = astore.get_measurement(con, measurement_ids[0], user_id)
        session = astore.get_session(con, row["session_id"], user_id)
        chain = evidence.build_evidence_chain(analysis, measurement, session, task_id)
        return ok({
            "task_id": task_id,
            "session_id": row["session_id"],
            "measurement_id": measurement.get("id") if measurement else None,
            "sample_alias": measurement.get("sample_alias") if measurement else None,
            "rule_version": (analysis.get("model_info") or {}).get("rule_version"),
            "chain": chain,
        })


@router.get("/tasks/{task_id}")
def read_task(task_id: str):
    user_id = current_user_id()
    with astore.db() as con:
        row = astore.get_task_row(con, task_id, user_id)
        if not row:
            return error(404, "TASK_NOT_FOUND", "未找到该分析任务，或该任务不属于当前账号。", retryable=False)
        payload = _task_payload(row, con)
        updated = astore.get_task_row(con, task_id, user_id)
        payload["status"] = updated["status"] if updated else payload["status"]
        return ok(payload)
