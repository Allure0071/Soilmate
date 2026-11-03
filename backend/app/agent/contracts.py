"""Versioned, strict wire contracts for Router, Manager and Workers."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("timestamps must include UTC timezone")
    return value


class TaskStatus(str, Enum):
    queued = "queued"
    planning = "planning"
    waiting_for_user = "waiting_for_user"
    running = "running"
    reviewing = "reviewing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class StepStatus(str, Enum):
    pending = "pending"
    blocked = "blocked"
    ready = "ready"
    running = "running"
    succeeded = "succeeded"
    waiting_for_user = "waiting_for_user"
    retry = "retry"
    failed = "failed"
    cancelled = "cancelled"
    superseded = "superseded"


class WorkerRole(str, Enum):
    soil_expert = "soil_expert"
    data = "data_worker"
    mds = "mds_worker"
    validation = "validation_worker"
    decision = "decision_worker"
    report = "report_worker"


class Producer(StrictModel):
    type: Literal["router", "manager", "worker", "tool", "system", "user"]
    id: str = Field(min_length=1)


class AgentEvent(StrictModel):
    event_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    event_version: int = Field(ge=1)
    occurred_at: datetime
    producer: Producer
    task_id: Optional[str] = None
    conversation_id: Optional[str] = None
    plan_version: Optional[int] = Field(default=None, ge=1)
    step_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: str = Field(min_length=1)
    causation_id: Optional[str] = None
    idempotency_key: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)

    _utc = field_validator("occurred_at")(require_utc)


class TaskCard(StrictModel):
    task_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    conversation_id: Optional[str] = None
    task_type: str = Field(min_length=1)
    status: TaskStatus = TaskStatus.queued
    dataset_id: Optional[str] = None
    dataset_version: Optional[str] = None
    active_plan_version: Optional[int] = Field(default=None, ge=1)
    manager_session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    _utc = field_validator("created_at", "updated_at")(require_utc)


class TaskPlan(StrictModel):
    plan_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    goal: str = Field(min_length=1)
    constraints: dict[str, Any] = Field(default_factory=dict)
    step_ids: list[str] = Field(default_factory=list)
    approval_state: Literal["not_required", "pending", "approved", "rejected"] = "pending"
    created_at: datetime

    _utc = field_validator("created_at")(require_utc)


class TaskStep(StrictModel):
    step_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    plan_version: int = Field(ge=1)
    worker_type: WorkerRole
    step_name: str = Field(min_length=1)
    dependency_ids: list[str] = Field(default_factory=list)
    status: StepStatus = StepStatus.pending
    input_artifact_ids: list[str] = Field(default_factory=list)
    output_artifact_ids: list[str] = Field(default_factory=list)
    attempt: int = Field(default=0, ge=0)
    timeout_seconds: int = Field(gt=0)

    @model_validator(mode="after")
    def no_self_dependency(self):
        if self.step_id in self.dependency_ids or len(self.dependency_ids) != len(set(self.dependency_ids)):
            raise ValueError("invalid step dependencies")
        return self


class WorkerInput(StrictModel):
    task_id: str = Field(min_length=1)
    plan_version: int = Field(ge=1)
    step_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    allowed_tool_ids: list[str] = Field(default_factory=list)
    input_artifact_ids: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    context_refs: list[str] = Field(default_factory=list)


class WorkerResult(StrictModel):
    step_id: str = Field(min_length=1)
    status: Literal["succeeded", "waiting_for_user", "retry", "failed"]
    output_artifact_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    tool_run_ids: list[str] = Field(default_factory=list)
    error_code: Optional[str] = None
    summary: str


class ArtifactReference(StrictModel):
    artifact_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    storage_uri: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    dataset_version: Optional[str] = None
    plan_version: int = Field(ge=1)
    created_by: str = Field(min_length=1)
    created_at: datetime
    validation_status: Literal["pending", "validated", "rejected"] = "pending"

    _utc = field_validator("created_at")(require_utc)


class ApprovalRequest(StrictModel):
    approval_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    plan_version: int = Field(ge=1)
    action: str = Field(min_length=1)
    status: Literal["pending", "approved", "rejected"] = "pending"
    requested_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None

    _utc = field_validator("requested_at", "decided_at")(lambda v: require_utc(v) if v is not None else v)

    @model_validator(mode="after")
    def decision_is_complete(self):
        if self.status != "pending" and (self.decided_at is None or not self.decided_by):
            raise ValueError("decided approval requires actor and time")
        return self


class ModelRequest(StrictModel):
    task_id: Optional[str] = None
    role: WorkerRole
    model_profile: str = Field(min_length=1)
    messages_or_context_refs: list[Union[dict[str, Any], str]] = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    output_schema: Optional[dict[str, Any]] = None
    timeout_seconds: int = Field(gt=0)
    data_classification: Literal["public", "project_internal", "restricted"]
