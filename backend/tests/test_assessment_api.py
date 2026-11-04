"""Assessment P0 API contract tests against a temporary research database."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from backend.app.api import assessment as assessment_api
from backend.app.main import app
from backend.app.scientific import research_store

VALUES = [
    {"indicator_code": "soil_ph", "value": 6.5, "unit": None, "method": "电位法", "source_type": "user_measurement"},
    {"indicator_code": "SOC", "value": 22, "unit": "g/kg", "method": "重铬酸钾氧化法", "source_type": "user_measurement"},
    {"indicator_code": "TN", "value": 1.8, "unit": "g/kg", "method": "凯氏定氮法", "source_type": "user_measurement"},
    {"indicator_code": "AP", "value": 30, "unit": "mg/kg", "method": "Olsen 法", "source_type": "user_measurement"},
    {"indicator_code": "AK", "value": 150, "unit": "mg/kg", "method": "乙酸铵浸提法", "source_type": "user_measurement"},
    {"indicator_code": "cec", "value": 22, "unit": "cmol/kg", "method": "乙酸铵交换法", "source_type": "user_measurement"},
    {"indicator_code": "BD", "value": 1.2, "unit": "g/cm³", "method": "环刀法", "source_type": "user_measurement"},
]


class AssessmentApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_db = research_store.DB
        research_store.DB = Path(self.tmp.name) / "assessment_test.sqlite"
        self.original_running = assessment_api.TASK_RUNNING_AFTER
        self.original_done = assessment_api.TASK_DONE_AFTER
        assessment_api.TASK_RUNNING_AFTER = 0.0
        assessment_api.TASK_DONE_AFTER = 0.0
        self.client = TestClient(app)
        response = self.client.post("/api/auth/register", json={"email": "assessment@example.com", "password": "SoilmateDemo2026!"})
        self.assertEqual(response.status_code, 200, response.text)
        self.csrf = self.client.get("/api/auth/me").json()["csrf_token"]
        self.headers = {"X-CSRF-Token": self.csrf}

    def tearDown(self):
        research_store.DB = self.original_db
        assessment_api.TASK_RUNNING_AFTER = self.original_running
        assessment_api.TASK_DONE_AFTER = self.original_done
        self.tmp.cleanup()

    def _post(self, path, payload, key):
        return self.client.post(path, json=payload, headers={**self.headers, "Idempotency-Key": key})

    def test_requires_login(self):
        anonymous = TestClient(app)
        response = anonymous.get("/api/assessment/indicators")
        self.assertEqual(response.status_code, 401)

    def test_quick_analysis_round_trip(self):
        dictionary = self.client.get("/api/assessment/indicators")
        self.assertEqual(dictionary.status_code, 200)
        codes = {item["code"] for item in dictionary.json()["data"]["items"]}
        self.assertTrue({"soil_ph", "SOC", "TN", "AP", "AK", "cec", "BD", "Clay"} <= codes)

        session_response = self._post("/api/assessment/sessions", {"mode": "quick", "crop_name": "水稻", "background": "示范地块"}, "session-key")
        self.assertEqual(session_response.status_code, 200)
        session_id = session_response.json()["data"]["id"]

        replay = self._post("/api/assessment/sessions", {"mode": "quick", "crop_name": "水稻", "background": "示范地块"}, "session-key")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["data"]["id"], session_id)
        conflict = self._post("/api/assessment/sessions", {"mode": "quick", "crop_name": "玉米", "background": "其他地块"}, "session-key")
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()["error"]["code"], "IDEMPOTENCY_CONFLICT")

        measurement_response = self._post("/api/assessment/measurements", {
            "session_id": session_id,
            "sample_alias": "示范地块 A-07 表层样本",
            "sampling_date": "2026-10-18",
            "values": VALUES,
        }, "measurement-key")
        self.assertEqual(measurement_response.status_code, 200, measurement_response.text)
        measurement_id = measurement_response.json()["data"]["id"]

        invalid = self._post("/api/assessment/measurements", {
            "session_id": session_id,
            "sample_alias": "错误单位样本",
            "values": [{**VALUES[1], "unit": "mg/kg"}],
        }, "invalid-measurement")
        self.assertEqual(invalid.status_code, 422)

        task_response = self._post("/api/assessment/tasks", {
            "type": "quick_analysis",
            "session_id": session_id,
            "measurement_ids": [measurement_id],
        }, "task-key")
        self.assertEqual(task_response.status_code, 202)
        task_id = task_response.json()["data"]["task_id"]

        listed = self.client.get("/api/assessment/tasks?limit=5")
        self.assertEqual(listed.status_code, 200)
        self.assertIn(task_id, [item["task_id"] for item in listed.json()["data"]["items"]])

        task = self.client.get(f"/api/assessment/tasks/{task_id}").json()["data"]
        self.assertEqual(task["status"], "completed")
        analysis = task["result"]["analysis"]
        self.assertEqual(analysis["coverage"]["measured_codes"], [value["indicator_code"] for value in VALUES])
        self.assertEqual(analysis["assessment"]["scope"], "recommended_set")
        self.assertIsInstance(analysis["assessment"]["composite_score"], float)
        self.assertTrue(analysis["assessment"]["summary"])
        for item in analysis["assessment"]["indicator_assessments"]:
            for evidence in item["evidence"]:
                self.assertTrue(evidence["label"] and evidence["source_id"] and evidence["source_type"])
        for problem in analysis["problems"]:
            self.assertTrue(problem["id"] and problem["title"] and problem["observation"])
        for decision in analysis["decisions"]:
            self.assertTrue(decision["id"] and decision["action"] and decision["reason"])
        self.assertIsInstance(analysis["gaps"], list)
        self.assertEqual(analysis["coverage"]["missing_codes"], [])
        self.assertTrue(analysis["limitations"])
        self.assertTrue(analysis["model_info"]["model_name"])
        self.assertEqual(len(analysis["assessment"]["function_scores"]), 4)
        evidence_response = self.client.get(f"/api/assessment/tasks/{task_id}/evidence")
        self.assertEqual(evidence_response.status_code, 200)
        evidence_payload = evidence_response.json()["data"]
        self.assertEqual(evidence_payload["measurement_id"], measurement_id)
        self.assertTrue(evidence_payload["rule_version"])
        self.assertEqual([node["kind"] for node in evidence_payload["chain"]],
                         ["sample", "indicator", "score", "rule", "boundary"])
        self.assertEqual(len(evidence_payload["chain"][1]["items"]), len(VALUES))

        restored_session = self.client.get(f"/api/assessment/sessions/{session_id}").json()["data"]
        self.assertEqual(restored_session["latest_task_id"], task_id)
        self.assertEqual(restored_session["measurement_ids"], [measurement_id])
        restored_measurement = self.client.get(f"/api/assessment/measurements/{measurement_id}")
        self.assertEqual(restored_measurement.status_code, 200)
        self.assertEqual(len(restored_measurement.json()["data"]["values"]), len(VALUES))

    def test_deep_analysis_requires_field(self):
        session = self._post("/api/assessment/sessions", {"mode": "deep", "crop_name": "水稻"}, "deep-session").json()["data"]
        response = self._post("/api/assessment/measurements", {
            "session_id": session["id"],
            "sample_alias": "深度样本",
            "values": VALUES,
        }, "deep-measurement")
        self.assertEqual(response.status_code, 422)

    def test_other_users_cannot_read_task(self):
        session_id = self._post("/api/assessment/sessions", {"mode": "quick"}, "owner-session").json()["data"]["id"]
        measurement_id = self._post("/api/assessment/measurements", {
            "session_id": session_id, "sample_alias": "样本", "values": VALUES,
        }, "owner-measurement").json()["data"]["id"]
        task_id = self._post("/api/assessment/tasks", {
            "type": "quick_analysis", "session_id": session_id, "measurement_ids": [measurement_id],
        }, "owner-task").json()["data"]["task_id"]

        other = TestClient(app)
        other.post("/api/auth/register", json={"email": "other@example.com", "password": "SoilmateDemo2026!"})
        response = other.get(f"/api/assessment/tasks/{task_id}")
        self.assertEqual(response.status_code, 404)

    def test_every_account_gets_its_own_demo_assessment(self):
        listed = self.client.get("/api/assessment/tasks?limit=5")
        self.assertEqual(listed.status_code, 200)
        demo_items = [item for item in listed.json()["data"]["items"] if item["sample_alias"] == "示范地块 A-07 表层样本"]
        self.assertEqual(len(demo_items), 1)
        task_id = demo_items[0]["task_id"]
        task = self.client.get(f"/api/assessment/tasks/{task_id}").json()["data"]
        self.assertEqual(task["result"]["analysis"]["assessment"]["composite_score"], 78.8)

        other = TestClient(app)
        other.post("/api/auth/register", json={"email": "demo-other@example.com", "password": "SoilmateDemo2026!"})
        other_items = other.get("/api/assessment/tasks?limit=5").json()["data"]["items"]
        other_demo = [item for item in other_items if item["sample_alias"] == "示范地块 A-07 表层样本"]
        self.assertEqual(len(other_demo), 1)
        self.assertNotEqual(other_demo[0]["task_id"], task_id)
        self.assertEqual(other.get(f"/api/assessment/tasks/{other_demo[0]['task_id']}").status_code, 200)


    def test_local_password_reset(self):
        response = self.client.post("/api/auth/reset", json={"email": "assessment@example.com", "password": "NewSoilmatePass2026!"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        login = self.client.post("/api/auth/login", json={"email": "assessment@example.com", "password": "NewSoilmatePass2026!"})
        self.assertEqual(login.status_code, 200)

    def test_local_password_reset_is_generic_for_unknown_email(self):
        response = self.client.post("/api/auth/reset", json={"email": "nobody@example.com", "password": "NewSoilmatePass2026!"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])


if __name__ == "__main__":
    unittest.main()
