"""Public SoilGrids 2.0 data for the map (ISRIC, CC BY 4.0).

Exposes:
- GET /api/soilgrids/layers            property catalog
- GET /api/soilgrids/tiles/{code}/{z}/{x}/{y}.png   WMS raster tile proxy
- GET /api/soilgrids/legend/{code}.png              WMS legend graphic proxy
- GET /api/soilgrids/point?lon=&lat=                real point values (regional prediction)

These are model predictions at 250 m, not field measurements. They are kept
separate from the platform's registered research layers.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Query, Response

from ..scientific.research_store import connect, initialize
from ..assessment import engine

router = APIRouter(prefix="/api/soilgrids", tags=["SoilGrids"])

WMS = "https://maps.isric.org/mapserv"
REST = "https://rest.isric.org/soilgrids/v2.0/properties/query"
ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = ROOT / "data" / "soilgrids_cache"
SOURCE = {
    "name": "ISRIC SoilGrids 2.0",
    "provider": "ISRIC — World Soil Information",
    "license": "CC BY 4.0",
    "doi": "10.5194/soil-7-217-2021",
    "url": "https://soilgrids.org",
    "type": "regional_prediction",
    "note": "250 m 区域预测值，不是田间实测。",
}

PROPERTIES = {
    "phh2o": {"name": "土壤酸碱度 pH", "unit": "无量纲", "d_factor": 10, "range": [4.0, 8.0]},
    "soc": {"name": "有机碳 SOC", "unit": "g/kg", "d_factor": 10, "range": [0, 60]},
    "nitrogen": {"name": "全氮 TN", "unit": "g/kg", "d_factor": 100, "range": [0, 5]},
    "cec": {"name": "阳离子交换量 CEC", "unit": "cmol(c)/kg", "d_factor": 10, "range": [0, 40]},
    "bdod": {"name": "容重 BD", "unit": "g/cm³", "d_factor": 100, "range": [0.9, 1.6]},
    "clay": {"name": "黏粒含量 Clay", "unit": "%", "d_factor": 10, "range": [0, 60]},
    "sand": {"name": "砂粒含量 Sand", "unit": "%", "d_factor": 10, "range": [0, 90]},
    "silt": {"name": "粉粒含量 Silt", "unit": "%", "d_factor": 10, "range": [0, 80]},
}
POINT_PROPERTIES = ["phh2o", "soc", "nitrogen", "cec", "bdod", "clay", "sand", "silt"]
DEPTH_LABEL = "0–5 cm"


def _tile_bbox(z, x, y):
    origin = 20037508.342789244
    size = 2 * origin / (2 ** z)
    minx = -origin + x * size
    maxy = origin - y * size
    return minx, maxy - size, minx + size, maxy


def _transparent_png():
    import base64
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    )


def _fetch_wms(params, timeout=30):
    with httpx.Client(timeout=httpx.Timeout(timeout, connect=8), follow_redirects=False, trust_env=False) as client:
        response = client.get(WMS, params=params)
    if response.status_code != 200 or "image" not in response.headers.get("content-type", ""):
        raise HTTPException(502, "SoilGrids 瓦片服务暂不可用")
    return response.content


def _init_cache(con):
    con.execute(
        "CREATE TABLE IF NOT EXISTS soilgrids_points("
        "lon REAL NOT NULL, lat REAL NOT NULL, payload_json TEXT NOT NULL, fetched_at TEXT NOT NULL,"
        "PRIMARY KEY(lon, lat))"
    )


@router.get("/layers")
def layers():
    items = []
    for code, meta in PROPERTIES.items():
        items.append({
            "code": code,
            "name": meta["name"],
            "unit": meta["unit"],
            "depth": DEPTH_LABEL,
            "range": meta["range"],
        })
    return {"properties": items, "source": SOURCE, "tile_url": "/api/soilgrids/tiles/{code}/{z}/{x}/{y}.png"}


@router.get("/tiles/{code}/{z}/{x}/{y}.png")
def tile(code: str, z: int, x: int, y: int):
    if code not in PROPERTIES:
        raise HTTPException(404, "未登记的公开数据图层")
    if not 3 <= z <= 9:
        raise HTTPException(404, "瓦片层级超出范围")
    count = 2 ** z
    if not (0 <= x < count and 0 <= y < count):
        raise HTTPException(404, "瓦片坐标超出范围")
    cache_path = CACHE_DIR / code / str(z) / str(x) / f"{y}.png"
    if cache_path.is_file():
        return Response(cache_path.read_bytes(), media_type="image/png", headers={"Cache-Control": "public, max-age=604800"})
    minx, miny, maxx, maxy = _tile_bbox(z, x, y)
    params = {
        "map": f"/map/{code}.map",
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": f"{code}_0-5cm_mean",
        "STYLES": "",
        "CRS": "EPSG:3857",
        "BBOX": f"{minx:.2f},{miny:.2f},{maxx:.2f},{maxy:.2f}",
        "WIDTH": "256",
        "HEIGHT": "256",
        "FORMAT": "image/png",
        "TRANSPARENT": "true",
    }
    try:
        content = _fetch_wms(params)
    except HTTPException:
        return Response(_transparent_png(), media_type="image/png", status_code=200)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(content)
    return Response(content, media_type="image/png", headers={"Cache-Control": "public, max-age=604800"})


def _query_property(client, code, lon, lat):
    """Read the rendered SoilGrids value at a point via WMS GetFeatureInfo."""
    import math
    import re

    x = lon * 20037508.34 / 180.0
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) / (math.pi / 180.0) * 20037508.34 / 180.0
    delta = 1000.0
    params = {
        "map": f"/map/{code}.map",
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": f"{code}_0-5cm_mean",
        "QUERY_LAYERS": f"{code}_0-5cm_mean",
        "STYLES": "",
        "CRS": "EPSG:3857",
        "BBOX": f"{x - delta:.2f},{y - delta:.2f},{x + delta:.2f},{y + delta:.2f}",
        "WIDTH": "101",
        "HEIGHT": "101",
        "I": "50",
        "J": "50",
        "INFO_FORMAT": "text/html",
    }
    response = client.get(WMS, params=params)
    response.raise_for_status()
    match = re.search(r'id="value"[^>]*>([^<]+)<', response.text)
    if not match:
        return code, None
    try:
        raw = float(match.group(1))
    except ValueError:
        return code, None
    meta = PROPERTIES[code]
    value = raw / meta["d_factor"]
    digits = 2 if code in ("phh2o", "nitrogen", "bdod") else 1
    return code, {"value": round(value, digits), "unit": meta["unit"], "raw": raw}


def _fetch_point(lon, lat):
    values = {}
    with httpx.Client(timeout=httpx.Timeout(8, connect=4), follow_redirects=False, trust_env=False) as client:
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(_query_property, client, code, lon, lat): code for code in POINT_PROPERTIES}
            for future in as_completed(futures):
                code = futures[future]
                try:
                    code, value = future.result()
                except Exception:
                    continue
                if value is not None:
                    values[code] = value
    return {
        "lon": lon,
        "lat": lat,
        "depth": DEPTH_LABEL,
        "values": values,
        "assessment": _assessment_for(values),
        "source": SOURCE,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _assessment_for(values):
    """Run the platform evaluation rules over the public point values."""
    mapping = [
        ("phh2o", "soil_ph", None, "SoilGrids 0–5 cm 预测值"),
        ("soc", "SOC", "g/kg", "SoilGrids 0–5 cm 预测值"),
        ("nitrogen", "TN", "g/kg", "SoilGrids 0–5 cm 预测值"),
        ("cec", "cec", "cmol(c)/kg", "SoilGrids 0–5 cm 预测值"),
        ("bdod", "BD", "g/cm³", "SoilGrids 0–5 cm 预测值"),
        ("clay", "Clay", "%", "SoilGrids 0–5 cm 预测值"),
    ]
    measurements = []
    for code, indicator_code, unit, method in mapping:
        item = values.get(code)
        if not item:
            continue
        measurements.append({
            "indicator_code": indicator_code,
            "value": item["value"],
            "unit": unit,
            "method": method,
            "source_type": "regional_prediction",
        })
    if not measurements:
        return None
    session = {"mode": "quick", "crop_name": None}
    measurement = {"id": "soilgrids-public-point", "values": measurements, "sampling_date": None}
    analysis = engine.build_analysis(session, measurement)
    return {
        "summary": analysis["assessment"]["summary"],
        "composite_score": analysis["assessment"]["composite_score"],
        "scope": analysis["assessment"]["scope"],
        "score_explanation": analysis["assessment"]["score_explanation"],
        "problems": [{"title": item["title"], "observation": item["observation"]} for item in analysis["problems"][:3]],
        "decisions": [{"action": item["action"], "reason": item["reason"]} for item in analysis["decisions"][:3]],
        "gaps": analysis["gaps"][:3],
        "limitations": analysis["limitations"][:2],
        "data_type": "regional_prediction",
    }


@router.get("/point")
def point(lon: float = Query(ge=-180, le=180), lat: float = Query(ge=-90, le=90)):
    initialize()
    key_lon, key_lat = round(lon, 3), round(lat, 3)
    with connect() as con:
        _init_cache(con)
        row = con.execute("SELECT payload_json FROM soilgrids_points WHERE lon=? AND lat=?", (key_lon, key_lat)).fetchone()
        if row:
            payload = json.loads(row[0])
            if not payload.get("assessment"):
                payload["assessment"] = _assessment_for(payload.get("values") or {})
                con.execute("UPDATE soilgrids_points SET payload_json=? WHERE lon=? AND lat=?",
                            (json.dumps(payload, ensure_ascii=False), key_lon, key_lat))
            return payload
    payload = _fetch_point(key_lon, key_lat)
    if not payload["values"]:
        raise HTTPException(502, "公开土壤数据暂不可用，请稍后重试")
    with connect() as con:
        _init_cache(con)
        con.execute(
            "INSERT OR REPLACE INTO soilgrids_points VALUES(?,?,?,?)",
            (key_lon, key_lat, json.dumps(payload, ensure_ascii=False), payload["fetched_at"]),
        )
    return payload
