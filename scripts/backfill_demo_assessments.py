"""Give every local account its own copy of the demonstration assessment.

Usage:
    .venv/bin/python scripts/backfill_demo_assessments.py

Accounts that already have the 示范地块 A-07 completed task are left unchanged;
new accounts get one completed quick-analysis session/measurement/task computed
with the same deterministic engine. The backend also does this automatically on
login, /api/auth/me, and the assessment task list, so this script is for existing
databases or a manual sync before a demo.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.assessment import demo, store


def main():
    with store.db() as con:
        users = con.execute("SELECT id, email FROM users ORDER BY created_at").fetchall()
        print(f"账号数：{len(users)}")
        for user in users:
            before = con.execute("SELECT COUNT(*) AS n FROM assessment_tasks WHERE user_id=?", (user["id"],)).fetchone()["n"]
            result = demo.ensure_demo_assessment(con, user["id"])
            after = con.execute("SELECT COUNT(*) AS n FROM assessment_tasks WHERE user_id=?", (user["id"],)).fetchone()["n"]
            state = "新建" if result and result.get("created") else "已存在"
            print(f"{user['email']}: {before} → {after} 项任务（{state}示范任务）")


if __name__ == "__main__":
    main()
