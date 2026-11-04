"""Per-account demonstration assessment.

The live demo ships one completed assessment (示范地块 A-07) so every account can
open the health-research flow and see the full result, evidence chain, and report.
Accounts receive their own copy: records are owned by that user, the result is
computed with the same deterministic engine, and repeated calls stay idempotent.
"""
from __future__ import annotations

from ..scientific.research_store import now, one
from . import engine
from . import store as astore

DEMO_SAMPLE = "示范地块 A-07 表层样本"
DEMO_CROP = "水稻"
DEMO_BACKGROUND = "演示环境 · 粤北稻区示范地块 · 秋季采样"
DEMO_DATE = "2026-10-18"
DEMO_VALUES = [
    {"indicator_code": "soil_ph", "value": 6.5, "unit": None, "method": "水土比 2.5:1 · 电位法", "source_type": "user_measurement"},
    {"indicator_code": "SOC", "value": 22, "unit": "g/kg", "method": "重铬酸钾氧化法", "source_type": "user_measurement"},
    {"indicator_code": "TN", "value": 1.8, "unit": "g/kg", "method": "凯氏定氮法", "source_type": "user_measurement"},
    {"indicator_code": "AP", "value": 30, "unit": "mg/kg", "method": "Olsen 法", "source_type": "user_measurement"},
    {"indicator_code": "AK", "value": 150, "unit": "mg/kg", "method": "乙酸铵浸提法", "source_type": "user_measurement"},
    {"indicator_code": "cec", "value": 22, "unit": "cmol/kg", "method": "乙酸铵交换法", "source_type": "user_measurement"},
    {"indicator_code": "BD", "value": 1.20, "unit": "g/cm³", "method": "环刀法", "source_type": "user_measurement"},
]


def _marker(con, user_id):
    return one(con, "SELECT * FROM assessment_demo_seeds WHERE user_id=?", (user_id,))


def _marker_is_valid(con, user_id, row):
    if not row or not row.get("session_id") or not row.get("task_id"):
        return False
    return bool(astore.get_session(con, row["session_id"], user_id) and astore.get_task_row(con, row["task_id"], user_id))


def _remember(con, user_id, session_id, task_id):
    con.execute(
        "INSERT INTO assessment_demo_seeds(user_id, session_id, task_id, created_at) VALUES(?,?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET session_id=excluded.session_id, task_id=excluded.task_id, created_at=excluded.created_at",
        (user_id, session_id, task_id, now()),
    )


def _existing_demo(con, user_id):
    return one(con, """
        SELECT s.id AS session_id, t.id AS task_id
        FROM assessment_sessions s
        JOIN assessment_measurements m ON m.session_id = s.id
        JOIN assessment_tasks t ON t.session_id = s.id
        WHERE s.user_id = ? AND m.sample_alias = ? AND t.status = 'completed'
        ORDER BY s.created_at DESC LIMIT 1
    """, (user_id, DEMO_SAMPLE))


def ensure_demo_assessment(con, user_id):
    """Create/return this account's demo session and task. Safe to call often."""
    astore.init_assessment(con)
    row = _marker(con, user_id)
    if _marker_is_valid(con, user_id, row):
        return {"session_id": row["session_id"], "task_id": row["task_id"], "created": False}

    existing = _existing_demo(con, user_id)
    if existing:
        _remember(con, user_id, existing["session_id"], existing["task_id"])
        return {"session_id": existing["session_id"], "task_id": existing["task_id"], "created": False}

    # Reserve the marker first so two parallel first requests cannot seed twice.
    reserved = con.execute(
        "INSERT OR IGNORE INTO assessment_demo_seeds(user_id, session_id, task_id, created_at) VALUES(?, '', '', ?)",
        (user_id, now()),
    )
    if reserved.rowcount == 0:
        row = _marker(con, user_id)
        if _marker_is_valid(con, user_id, row):
            return {"session_id": row["session_id"], "task_id": row["task_id"], "created": False}
        return None

    try:
        session = astore.create_session(con, user_id, "quick", DEMO_CROP, DEMO_BACKGROUND, None, None)
        measurement = astore.create_measurement(con, user_id, session["id"], {
            "sample_alias": DEMO_SAMPLE,
            "sampling_date": DEMO_DATE,
            "values": DEMO_VALUES,
        })
        task_id = astore.create_task(con, user_id, session["id"], "quick_analysis", {
            "type": "quick_analysis",
            "session_id": session["id"],
            "measurement_ids": [measurement["id"]],
        })
        analysis = engine.build_analysis(session, measurement)
        astore.update_task(con, task_id, "completed", result={"kind": "analysis", "analysis": analysis})
        _remember(con, user_id, session["id"], task_id)
        return {"session_id": session["id"], "task_id": task_id, "created": True}
    except Exception:
        con.execute("DELETE FROM assessment_demo_seeds WHERE user_id=? AND session_id=''", (user_id,))
        raise
