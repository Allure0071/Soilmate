"""Seed one completed assessment run for a local demo account.

Usage:
    .venv/bin/python scripts/seed_assessment_demo.py --email demo@soilmate.local
    .venv/bin/python scripts/seed_assessment_demo.py --email demo@soilmate.local --password 'SoilmateDemo2026!'

The script writes one quick-analysis session/measurement/task into
data/research_v2.sqlite and marks the task completed with the deterministic
engine result. It prints a direct demo URL for /research.
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.api import auth
from backend.app.assessment import engine
from backend.app.assessment import store as astore
from backend.app.scientific.research_store import connect, initialize, now, one

VALUES = [
    {"indicator_code": "soil_ph", "value": 6.5, "unit": None, "method": "水土比 2.5:1 · 电位法", "source_type": "user_measurement"},
    {"indicator_code": "SOC", "value": 22, "unit": "g/kg", "method": "重铬酸钾氧化法", "source_type": "user_measurement"},
    {"indicator_code": "TN", "value": 1.8, "unit": "g/kg", "method": "凯氏定氮法", "source_type": "user_measurement"},
    {"indicator_code": "AP", "value": 30, "unit": "mg/kg", "method": "Olsen 法", "source_type": "user_measurement"},
    {"indicator_code": "AK", "value": 150, "unit": "mg/kg", "method": "乙酸铵浸提法", "source_type": "user_measurement"},
    {"indicator_code": "cec", "value": 22, "unit": "cmol/kg", "method": "乙酸铵交换法", "source_type": "user_measurement"},
    {"indicator_code": "BD", "value": 1.20, "unit": "g/cm³", "method": "环刀法", "source_type": "user_measurement"},
]


def ensure_user(con, email, password):
    existing = one(con, "SELECT id FROM users WHERE email=?", (email,))
    if existing:
        return existing["id"]
    user_id = "user_" + uuid.uuid4().hex[:16]
    con.execute("INSERT INTO users VALUES(?,?,?,?)", (user_id, email, auth.password_hash(password), now()))
    return user_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default="demo@soilmate.local")
    parser.add_argument("--password", default="SoilmateDemo2026!")
    parser.add_argument("--sample", default="示范地块 A-07 表层样本")
    parser.add_argument("--crop", default="水稻")
    parser.add_argument("--background", default="粤北稻区示范地块 · 秋季采样")
    args = parser.parse_args()

    initialize()
    with connect() as con:
        astore.init_assessment(con)
        auth.init_auth(con)
        user_id = ensure_user(con, args.email, args.password)
        session = astore.create_session(con, user_id, "quick", args.crop, args.background, None, None)
        measurement = astore.create_measurement(con, user_id, session["id"], {
            "sample_alias": args.sample,
            "sampling_date": "2026-10-18",
            "values": VALUES,
        })
        task_id = astore.create_task(con, user_id, session["id"], "quick_analysis", {
            "type": "quick_analysis",
            "session_id": session["id"],
            "measurement_ids": [measurement["id"]],
        })
        analysis = engine.build_analysis(session, measurement)
        astore.update_task(con, task_id, "completed", result={"kind": "analysis", "analysis": analysis})
        email = one(con, "SELECT email FROM users WHERE id=?", (user_id,))["email"]

    print("账号：", email)
    print("会话：", session["id"])
    print("任务：", task_id)
    print("综合分：", analysis["assessment"]["composite_score"])
    print("演示地址：")
    print(f"http://localhost:5173/research?stage=analysis&assessmentSession={session['id']}&assessmentTask={task_id}")


if __name__ == "__main__":
    main()
