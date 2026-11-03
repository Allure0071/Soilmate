"""Phase 4.1 role dispatch for deterministic Data/MDS workers."""
from typing import Any, Dict, List, Callable
from .phase4_1_adapters import DataWorker, MDSWorker


def execute_professional(role: str, config: Dict[str, Any], inputs: List[Any], cancelled: Callable[[], bool]):
    if cancelled():
        raise InterruptedError("execution cancelled before professional worker")
    if role == "data":
        result = DataWorker().execute(config)
    elif role == "mds":
        result = MDSWorker().execute(config)
    else:
        raise ValueError("professional worker is not implemented for role: " + role)
    if cancelled():
        raise InterruptedError("execution cancelled after professional worker")
    return result
