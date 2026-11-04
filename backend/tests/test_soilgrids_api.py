"""SoilGrids public map layer API contract tests (no external network calls)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from backend.app.main import app


class SoilgridsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_layers_catalog(self):
        response = self.client.get("/api/soilgrids/layers")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        codes = {item["code"] for item in payload["properties"]}
        self.assertTrue({"phh2o", "soc", "nitrogen", "cec", "bdod", "clay"} <= codes)
        self.assertEqual(payload["source"]["license"], "CC BY 4.0")
        self.assertEqual(payload["source"]["type"], "regional_prediction")

    def test_tile_rejects_unknown_layer_and_zoom(self):
        unknown = self.client.get("/api/soilgrids/tiles/unknown/5/1/1.png")
        self.assertEqual(unknown.status_code, 404)
        out_of_range = self.client.get("/api/soilgrids/tiles/phh2o/12/0/0.png")
        self.assertEqual(out_of_range.status_code, 404)
        bad_coords = self.client.get("/api/soilgrids/tiles/phh2o/5/0/99.png")
        self.assertEqual(bad_coords.status_code, 404)

    def test_point_validation(self):
        self.assertEqual(self.client.get("/api/soilgrids/point?lon=500&lat=20").status_code, 422)
        self.assertEqual(self.client.get("/api/soilgrids/point?lon=110&lat=-95").status_code, 422)


if __name__ == "__main__":
    unittest.main()
