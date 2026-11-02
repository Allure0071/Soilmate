"""Persistent research registry. The map raster SQLite files remain read-only."""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "data" / "research_sources"
DB = ROOT / "data" / "research_v2.sqlite"


def now():
    return datetime.now(timezone.utc).isoformat()


def uid(prefix):
    return prefix + "_" + uuid.uuid4().hex[:16]


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def unpack(value):
    return json.loads(value) if value else {}


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@contextmanager
def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB), timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS datasets(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), kind TEXT NOT NULL,
 name TEXT NOT NULL, source_uri TEXT NOT NULL, source_sha256 TEXT NOT NULL, data_version TEXT NOT NULL,
 status TEXT NOT NULL, metadata_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS samples(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
 dataset_id TEXT NOT NULL REFERENCES datasets(id), kind TEXT NOT NULL, external_id TEXT NOT NULL,
 metadata_json TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(dataset_id,kind,external_id));
CREATE TABLE IF NOT EXISTS sample_pairings(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
 soil_sample_id TEXT NOT NULL REFERENCES samples(id), microbe_sample_id TEXT NOT NULL REFERENCES samples(id),
 status TEXT NOT NULL, evidence_json TEXT NOT NULL, review_note TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS analysis_runs(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
 sample_id TEXT NOT NULL REFERENCES samples(id), dataset_id TEXT NOT NULL REFERENCES datasets(id), kind TEXT NOT NULL,
 status TEXT NOT NULL, algorithm_version TEXT NOT NULL, config_json TEXT NOT NULL, source_sha256 TEXT NOT NULL,
 result_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assessment_results(id TEXT PRIMARY KEY, run_id TEXT NOT NULL UNIQUE REFERENCES analysis_runs(id),
 sample_id TEXT NOT NULL REFERENCES samples(id), state TEXT NOT NULL, result_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS microbial_evidence(id TEXT PRIMARY KEY, run_id TEXT NOT NULL UNIQUE REFERENCES analysis_runs(id),
 sample_id TEXT NOT NULL REFERENCES samples(id), state TEXT NOT NULL, result_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS research_actions(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
 run_id TEXT NOT NULL REFERENCES analysis_runs(id), action_code TEXT NOT NULL, action_class TEXT NOT NULL,
 status TEXT NOT NULL, reason TEXT NOT NULL, parameters_json TEXT NOT NULL, estimated_cost TEXT NOT NULL,
 preconditions_json TEXT NOT NULL, before_json TEXT NOT NULL, after_json TEXT NOT NULL, log_json TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
 version INTEGER NOT NULL, content TEXT NOT NULL, run_ids_json TEXT NOT NULL, source_json TEXT NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(project_id,version));
CREATE INDEX IF NOT EXISTS idx_samples_project ON samples(project_id,kind);
CREATE INDEX IF NOT EXISTS idx_runs_project ON analysis_runs(project_id,created_at);
CREATE INDEX IF NOT EXISTS idx_reports_project ON reports(project_id,version);
"""


def initialize():
    with connect() as con:
        con.executescript(SCHEMA)
        con.execute("INSERT OR IGNORE INTO schema_migrations VALUES(1,?)", (now(),))
        seed(con)


def _csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _seed_dataset(con, project_id, dataset_id, kind, filename, name, version, sample_kind, id_field):
    if con.execute("SELECT 1 FROM datasets WHERE id=?", (dataset_id,)).fetchone():
        return
    path = SOURCE / filename
    if not path.exists():
        raise FileNotFoundError(f"Research source missing: {path}")
    rows = _csv(path)
    sha = digest(path)
    con.execute("INSERT INTO datasets VALUES(?,?,?,?,?,?,?,?,?,?)",
                (dataset_id, project_id, kind, name, str(path), sha, version, "source_registered",
                 dump({"rows": len(rows), "data_type": "real_source", "units_unverified": kind == "soil"}), now()))
    for row in rows:
        external = row[id_field].strip()
        if not external:
            raise ValueError("Blank sample identity in source")
        con.execute("INSERT INTO samples VALUES(?,?,?,?,?,?,?)",
                    (f"{dataset_id}:{external}", project_id, dataset_id, sample_kind, external, dump(row), now()))


def seed(con):
    # A fresh checkout can use synthetic map fixtures without private research CSVs.
    if not all((SOURCE / name).is_file() for name in (
        "local_74_soil_partial_scores.csv", "public_sample_manifest.csv"
    )):
        return
    for pid, name, desc in (
        ("local-soil-74", "本地土壤样点研究 · 74 条", "真实本地土壤表；缺生物转化维度及验证阈值"),
        ("public-ko-70", "公开氮循环 KO 方法案例 · 70 条", "独立公开研究；不与本地土壤样本配对"),
    ):
        con.execute("INSERT OR IGNORE INTO projects(id,name,description,created_at) VALUES(?,?,?,?)", (pid, name, desc, now()))
    _seed_dataset(con, "local-soil-74", "local-soil-74-v06", "soil", "local_74_soil_partial_scores.csv",
                  "74 个本地土壤样点原始指标与两维探索结果", "v0.6", "soil", "soil_sample_id")
    _seed_dataset(con, "public-ko-70", "public-ko-70-figshare", "microbiome",
                  "public_sample_manifest.csv", "70 个公开宏基因组样本与 ENA 身份表", "figshare-28492940-v1",
                  "microbiome", "sample_alias")


def one(con, query, args=()):
    row = con.execute(query, args).fetchone()
    return dict(row) if row else None


def many(con, query, args=()):
    return [dict(x) for x in con.execute(query, args).fetchall()]


def sample(con, sample_id):
    row = one(con, "SELECT * FROM samples WHERE id=?", (sample_id,))
    if row:
        row["metadata"] = unpack(row.pop("metadata_json"))
    return row


def dataset(con, dataset_id):
    row = one(con, "SELECT * FROM datasets WHERE id=?", (dataset_id,))
    if row:
        row["metadata"] = unpack(row.pop("metadata_json"))
    return row
