"""Read-only reference view of the supplied Z01 agriculture zones."""

import json
from functools import lru_cache
from pathlib import Path

import rasterio
from fastapi import APIRouter, HTTPException, Query
from pyproj import Transformer


router = APIRouter()
PROCESSED = Path(__file__).resolve().parents[3] / "data" / "processed"
BOUNDARIES = PROCESSED / "z01_reference_boundaries.geojson"
LOOKUP = PROCESSED / "z01_reference_1km.tif"
METADATA = PROCESSED / "z01_reference_metadata.json"


@lru_cache(maxsize=1)
def _metadata():
    return json.loads(METADATA.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _boundaries():
    return json.loads(BOUNDARIES.read_text(encoding="utf-8"))


@router.get("/api/zones/z01")
def z01_boundaries():
    if not BOUNDARIES.exists():
        raise HTTPException(status_code=503, detail="Z01 reference boundaries are unavailable")
    return _boundaries()


@router.get("/api/zones/z01/point")
def z01_point(lon: float = Query(..., ge=-180, le=180), lat: float = Query(..., ge=-90, le=90)):
    if not LOOKUP.exists() or not METADATA.exists():
        raise HTTPException(status_code=503, detail="Z01 reference lookup is unavailable")
    with rasterio.open(LOOKUP) as dataset:
        x, y = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True).transform(lon, lat)
        sampled = next(dataset.sample([(x, y)], masked=True))[0]
        value = 0 if getattr(sampled, "mask", False) else int(sampled)
    info = _metadata()["zones"].get(str(value))
    return {
        "lon": lon, "lat": lat, "zone": info,
        "status": "reference_only", "lookup_resolution_m": 1000,
        "model_mapping_verified": False,
    }
