"""Phase 4.1 controlled Data/MDS adapters.

These adapters are deliberately independent of the Worker runtime: they validate
inputs, run in a bounded workspace, and return JSON-safe summaries. They do not
modify the RECH-MDS reference implementation.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class AdapterError(ValueError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_input(path: Path, allowed_root: Optional[Path] = None) -> Path:
    p = path.resolve()
    if not p.is_file() or p.suffix.lower() != ".csv":
        raise AdapterError("input must be an existing CSV file")
    if allowed_root is not None and p != allowed_root.resolve() and allowed_root.resolve() not in p.parents:
        raise AdapterError("input is outside the allowed dataset root")
    return p


def audit_csv(path: Path, allowed_root: Optional[Path] = None, sample_limit: int = 1000) -> Dict[str, Any]:
    """Audit a CSV without changing it or loading unbounded content into memory."""
    if sample_limit < 1 or sample_limit > 100000:
        raise AdapterError("invalid sample limit")
    p = _safe_input(Path(path), allowed_root)
    with p.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise AdapterError("CSV has no header")
        fields = [str(x).strip() for x in reader.fieldnames]
        if len(fields) != len(set(fields)) or any(not x for x in fields):
            raise AdapterError("CSV header contains empty or duplicate fields")
        nonempty = {f: 0 for f in fields}
        numeric = {f: 0 for f in fields}
        missing = {f: 0 for f in fields}
        rows = 0
        for row in reader:
            rows += 1
            if rows <= sample_limit:
                for f in fields:
                    value = (row.get(f) or "").strip()
                    if not value:
                        missing[f] += 1
                    else:
                        nonempty[f] += 1
                        try:
                            float(value)
                            numeric[f] += 1
                        except ValueError:
                            pass
    return {
        "schema_version": "data_profile.v1",
        "source_name": p.name,
        "source_sha256": _sha256(p),
        "row_count": rows,
        "field_count": len(fields),
        "fields": [{"name": f, "sample_nonempty": nonempty[f],
                     "sample_missing": missing[f], "sample_numeric": numeric[f]}
                    for f in fields],
        "sample_limit": sample_limit,
        "evidence_tier": "observed_input",
    }


def run_rech_mds(data_path: Path, config_path: Path, rech_script: Path,
                 output_root: Path, timeout_seconds: int = 300,
                 allowed_data_root: Optional[Path] = None) -> Dict[str, Any]:
    """Run the existing RECH-MDS CLI in a fresh bounded directory."""
    if not 1 <= timeout_seconds <= 3600:
        raise AdapterError("timeout must be between 1 and 3600 seconds")
    data = _safe_input(Path(data_path), allowed_data_root)
    config = Path(config_path).resolve()
    script = Path(rech_script).resolve()
    if not config.is_file() or config.suffix.lower() != ".json":
        raise AdapterError("config must be an existing JSON file")
    if not script.is_file() or script.name != "rech_mds.py":
        raise AdapterError("unexpected RECH-MDS script")
    out_root = Path(output_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="rech-mds-", dir=str(out_root)))
    command = [sys.executable, str(script), "--data", str(data), "--config", str(config), "--out", str(run_dir)]
    try:
        proc = subprocess.run(command, capture_output=True, text=True,
                              timeout=timeout_seconds, cwd=str(script.parent))
    except subprocess.TimeoutExpired as exc:
        raise AdapterError("RECH-MDS timed out") from exc
    if proc.returncode != 0:
        raise AdapterError("RECH-MDS failed: " + (proc.stderr or proc.stdout)[-1000:])
    required = ["selection_trace.csv", "mds_by_region.csv", "outer_test_metrics.csv", "run_metadata.json"]
    missing = [name for name in required if not (run_dir / name).is_file()]
    if missing:
        raise AdapterError("RECH-MDS missing outputs: " + ", ".join(missing))
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    return {
        "schema_version": "mds_result.v1",
        "output_dir": str(run_dir),
        "input_sha256": _sha256(data),
        "config_sha256": _sha256(config),
        "script_sha256": _sha256(script),
        "files": required,
        "metadata": metadata,
        "evidence_tier": "computed_from_observed_input",
    }


class DataWorker:
    """Runtime-facing Data Worker. The source path must be supplied by a trusted adapter."""
    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return audit_csv(Path(config["dataset_path"]), Path(config["allowed_data_root"]))


class MDSWorker:
    """Runtime-facing MDS Worker using only the pinned reference CLI."""
    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return run_rech_mds(Path(config["dataset_path"]), Path(config["config_path"]),
                            Path(config["rech_script"]), Path(config["output_root"]),
                            int(config.get("timeout_seconds", 300)),
                            Path(config["allowed_data_root"]))
