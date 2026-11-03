"""HTTP contract checks for Agent Session, CSRF and project ownership."""

import asyncio
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from backend.app import main
from backend.app.api import auth
from backend.app.agent.migration import migrate_agent_schema
from backend.app.agent.migration_v3 import migrate_event_schema
from backend.app.scientific import research_store as store


class AgentApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "research.sqlite"
        self.patch_db = patch.object(store, "DB", self.db)
        self.patch_source = patch.object(store, "SOURCE", Path(self.tmp.name) / "missing_sources")
        self.patch_db.start()
        self.patch_source.start()
        store.initialize()
        with store.connect() as con:
            auth.init_auth(con)
            con.executemany("INSERT INTO users(id,email,password_hash,created_at) VALUES(?,?,?,?)",
                            [("u1", "u1@example.org", "unused", "now"), ("u2", "u2@example.org", "unused", "now")])
            con.executemany("INSERT INTO projects(id,name,owner_user_id,created_at) VALUES(?,?,?,?)",
                            [("p1", "One", "u1", "now"), ("p2", "Two", "u2", "now")])
        with store.connect() as con:
            migrate_agent_schema(con)
            migrate_event_schema(con)
        with store.connect() as con:
            con.executemany("INSERT INTO auth_sessions VALUES(?,?,?,?,?)",
                            [(auth.token_hash("session-one-token-123456789012345"), "u1", "csrf-1", int(time.time()) + 3600, "now"),
                             (auth.token_hash("session-two-token-123456789012345"), "u2", "csrf-2", int(time.time()) + 3600, "now")])

    def tearDown(self):
        self.patch_source.stop()
        self.patch_db.stop()
        self.tmp.cleanup()

    def test_http_auth_csrf_and_owner_checks(self):
        # Windows Proactor's socketpair can hang in restricted test environments.
        if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        async def scenario():
            transport = httpx.ASGITransport(app=main.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                body = {"text": "帮我分析这份数据", "project_id": "p1"}
                unauth = await client.post("/api/agent/messages", json=body)
                self.assertEqual(unauth.status_code, 401)
                client.cookies.set(auth.COOKIE, "session-one-token-123456789012345")
                no_csrf = await client.post("/api/agent/messages", json=body)
                self.assertEqual(no_csrf.status_code, 403)
                created = await client.post("/api/agent/messages", json=body, headers={"X-CSRF-Token": "csrf-1"})
                self.assertEqual(created.status_code, 200, created.text)
                task_id = created.json()["task_id"]
                with store.connect() as con:
                    con.execute("""INSERT INTO artifacts(id,task_id,project_id,kind,storage_uri,sha256,
                        plan_version,created_by,validation_status,created_at)
                        VALUES(?,?,'p1','test','not-a-local-file',?,1,'test','pending','now')""",
                        ("artifact-test", task_id, "a" * 64))
                own = await client.get(f"/api/agent/tasks/{task_id}/events")
                self.assertEqual(own.status_code, 200)
                self.assertEqual(own.json()[0]["task_event_seq"], 1)
                existing_research = await client.get("/api/research/bootstrap")
                self.assertEqual(existing_research.status_code, 200)
                client.cookies.set(auth.COOKIE, "session-two-token-123456789012345")
                forbidden = await client.get(f"/api/agent/tasks/{task_id}/events")
                self.assertEqual(forbidden.status_code, 404)
                artifact = await client.get("/api/agent/artifacts/artifact-test")
                self.assertEqual(artifact.status_code, 404)
                cross_project = await client.post("/api/agent/messages", json=body, headers={"X-CSRF-Token": "csrf-2"})
                self.assertEqual(cross_project.status_code, 404)
        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
