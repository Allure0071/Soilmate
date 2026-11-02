"""按需展示已对齐的 N+X 研究预览栅格。"""

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import json

import numpy as np
import rasterio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from PIL import Image
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

from .point import _lonlat_to_rowcol

router = APIRouter()
PREVIEW_DIR = Path(__file__).absolute().parents[3] / "data" / "processed" / "nx"
LAYERS = {
    "n01_an": {
        "filename": "n01_an_0_5cm_5km_preview.tif", "name": "碱解氮 · 0–5 cm",
        "unit": "原始值（单位待核）", "range": [300, 4500], "category": "soil",
        "note": "CSDLv2 研究预览；源文件未明确数值缩放系数，不参与评分。",
    },
    "n02_som": {
        "filename": "n02_som_top_5km_preview.tif", "name": "有机质 · 0–4.5 cm",
        "unit": "% of weight", "range": [0, 12], "category": "soil",
        "note": "CSDLv1 研究预览；NetCDF 未声明大地基准，暂按经纬度 WGS84 对齐，不参与评分。",
    },
    "x07_slope": {
        "filename": "x07_slope_5km_preview.tif", "name": "坡度 · 黄土高原候选区",
        "unit": "度", "range": [0, 30], "category": "env",
        "note": "SRTM 派生坡度研究预览；尚未按最终九大区边界裁剪，不参与评分。",
    },
}


def _discover_layers():
    discovered = {}
    for report_path in sorted(PREVIEW_DIR.glob("*_5km_preview.json")):
        path = report_path.with_suffix(".tif")
        if not path.is_file():
            continue
        layer_id = report_path.stem.removesuffix("_5km_preview")
        if path.name in {layer["filename"] for layer in LAYERS.values()}:
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        depth = report.get("depth_cm")
        year = report.get("year")
        if layer_id.startswith("n01_an_"):
            name, unit, category = f"碱解氮 · {depth[0]:g}–{depth[1]:g} cm", "原始值（单位待核）", "soil"
            note = "CSDLv2 分层预览；数值缩放系数待核实，不参与评分。"
        elif layer_id.startswith("n02_som_"):
            name, unit, category = f"有机质 · {depth[0]:g}–{depth[1]:g} cm", "% of weight", "soil"
            note = "CSDLv1 分层预览；大地基准待核实，不参与评分。"
        elif layer_id.startswith("x05_al_"):
            name, unit, category = f"交换性铝 · {depth[0]:g}–{depth[1]:g} cm", "me/100 g", "soil"
            note = "CSDLv1 交换性 Al³⁺ 分层预览；大地基准待核实，不参与评分。"
        elif layer_id.startswith("x02_pet_"):
            name, unit, category = f"潜在蒸散发 · {year}", "mm/年", "env"
            note = "12 个月潜在蒸散发求和；按资料原始年份展示，不参与评分。"
        elif layer_id.startswith("x04_sw_erosion_"):
            name, unit, category = f"西南侵蚀模数 · {year}", "t/(ha·年)", "env"
            note = "西南区域 RUSLE 产品；与全国水蚀产品来源不同，不参与评分。"
        elif layer_id.startswith("x04_erosion_"):
            name, unit, category = f"侵蚀模数 · {year}", "t/(ha·年)", "env"
            note = "源文件的 9999 特殊值已排除；含义仍待原作者核对，不参与评分。"
        elif layer_id.startswith("x06_sm_"):
            name, unit, category = f"土壤湿度 · {year}", "原始值（单位待核）", "env"
            note = "GLASS 2020 年预览；单位与时间聚合定义待核实，不参与评分。"
        else:
            continue
        with rasterio.open(path) as src:
            values = src.read(1, masked=True).compressed()
        if not values.size:
            continue
        low, high = np.percentile(values, [2, 98])
        if high <= low:
            high = low + 1
        discovered[layer_id] = {
            "filename": path.name, "name": name, "unit": unit,
            "range": [float(f"{low:.3g}"), float(f"{high:.3g}")],
            "category": category, "note": note,
        }
    return discovered


LAYERS.update(_discover_layers())


def _layer(layer_id):
    layer = LAYERS.get(layer_id)
    if layer is None:
        raise HTTPException(status_code=404, detail="未知预览图层")
    path = PREVIEW_DIR / layer["filename"]
    if not path.is_file():
        raise HTTPException(status_code=404, detail="预览图层尚未生成")
    return layer, path


@router.get("/api/preview/layers")
def list_preview_layers():
    return {"layers": [
        {"id": layer_id, **{k: v for k, v in layer.items() if k != "filename"}}
        for layer_id, layer in LAYERS.items()
        if (PREVIEW_DIR / layer["filename"]).is_file()
    ]}


@router.get("/api/preview/point")
def preview_point(lon: float = Query(..., ge=-180, le=180),
                  lat: float = Query(..., ge=-90, le=90)):
    try:
        row, col = _lonlat_to_rowcol(lon, lat, 5)
    except HTTPException as exc:
        if exc.status_code != 404:
            raise
        return {"lon": lon, "lat": lat, "values": {}}
    values = {}
    for layer_id, layer in LAYERS.items():
        path = PREVIEW_DIR / layer["filename"]
        if not path.is_file():
            continue
        with rasterio.open(path) as src:
            value = float(src.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])
            if value == src.nodata or not np.isfinite(value):
                value = None
        values[layer_id] = value
    return {"lon": lon, "lat": lat, "values": values}


@lru_cache(maxsize=256)
def _render_tile(layer_id, z, x, y):
    layer, path = _layer(layer_id)
    world = 20037508.342789244
    span = 2 * world / (1 << z)
    left, right = -world + x * span, -world + (x + 1) * span
    top, bottom = world - y * span, world - (y + 1) * span
    target = np.full((256, 256), -9999.0, dtype="float32")
    with rasterio.open(path) as src:
        reproject(
            source=rasterio.band(src, 1), destination=target,
            src_transform=src.transform, src_crs=src.crs, src_nodata=src.nodata,
            dst_transform=from_bounds(left, bottom, right, top, 256, 256),
            dst_crs="EPSG:3857", dst_nodata=-9999.0,
            resampling=Resampling.bilinear,
        )
    valid = (target != -9999.0) & np.isfinite(target)
    low, high = layer["range"]
    scaled = np.clip((target - low) / (high - low), 0, 1)
    stops = [0.0, 0.35, 0.7, 1.0]
    colors = np.array([[239, 229, 194], [172, 204, 151], [57, 143, 128], [20, 73, 94]])
    rgba = np.empty((256, 256, 4), dtype="uint8")
    for channel in range(3):
        rgba[:, :, channel] = np.interp(scaled, stops, colors[:, channel]).astype("uint8")
    rgba[:, :, 3] = np.where(valid, 210, 0).astype("uint8")
    stream = BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(stream, format="PNG", optimize=True)
    return stream.getvalue()


@router.get("/api/preview/tiles/{layer_id}/{z}/{x}/{y}.png")
def preview_tile(layer_id: str, z: int, x: int, y: int):
    if not (0 <= z <= 12 and 0 <= x < 1 << z and 0 <= y < 1 << z):
        raise HTTPException(status_code=404, detail="瓦片坐标超出范围")
    return Response(_render_tile(layer_id, z, x, y), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})
