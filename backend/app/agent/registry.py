"""Six role declarations; only the controlled Test Worker is executable in Phase 3."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable
from .contracts import WorkerInput, WorkerResult, WorkerRole


@dataclass(frozen=True)
class WorkerDefinition:
    role: WorkerRole
    capabilities: tuple
    allowed_tools: tuple = ('test.echo',)
    model_profile: str = 'disabled'
    timeout_seconds: int = 30
    max_attempts: int = 2
    context_policy: str = 'task_plan_step_only'
    system_prompt: str = 'Phase 3 Test Worker only; no scientific conclusions or external actions.'
    input_schema: type = WorkerInput
    output_schema: type = WorkerResult


REGISTRY = {
    role.value: WorkerDefinition(role, capabilities)
    for role, capabilities in (
        (WorkerRole.soil_expert, ('domain_question',)),
        (WorkerRole.data, ('data_audit',)), (WorkerRole.mds, ('mds_selection',)),
        (WorkerRole.validation, ('validation',)), (WorkerRole.decision, ('comparison',)),
        (WorkerRole.report, ('report',)))
}


class WorkerBase(ABC):
    @abstractmethod
    def execute(self, request: WorkerInput, config: dict, inputs: list, cancelled: Callable):
        """Return JSON-compatible content using injected, restricted capabilities."""


class TestWorker(WorkerBase):
    def execute(self, request, config, inputs, cancelled):
        import time
        delay = float(config.get('delay_seconds', 0))
        if not 0 <= delay <= 5:
            raise ValueError('test delay must be between 0 and 5 seconds')
        until = time.monotonic() + delay
        while time.monotonic() < until:
            if cancelled():
                raise InterruptedError('execution cancelled')
            time.sleep(0.01)
        if config.get('fail_first') and config.get('_attempt') == 1:
            raise RuntimeError('test first attempt failure')
        return {'test_only': True, 'task_id': request.task_id, 'step_id': request.step_id,
                'plan_version': request.plan_version, 'inputs': inputs, 'value': config.get('value')}
