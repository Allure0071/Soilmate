"""生成 SOM 与坡度的 5 km 研究预览栅格，不写入正式指标库。"""

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from rasterio.warp import Resampling, reproject

from backend.app.db import GRID_DIMS, grid_meta


def target_grid():
    meta = grid_meta(5)
    return (
        GRID_DIMS[5],
        Affine(*(float(meta[k]) for k in "abcdef")),
        rasterio.crs.CRS.from_wkt(meta["grid_crs"]),
    )


def save_preview(path, values, transform, crs, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = values.shape
    with rasterio.open(
        path, "w", driver="GTiff", height=height, width=width, count=1,
        dtype="float32", crs=crs, transform=transform, nodata=-9999.0,
        compress="deflate", predictor=3, tiled=True,
        blockxsize=256, blockysize=256,
    ) as dst:
        dst.write(values, 1)
    valid = values[values != -9999.0]
    report.update({
        "output": str(path), "valid_cells": int(valid.size),
        "total_cells": width * height,
        "min": float(np.min(valid)) if valid.size else None,
        "max": float(np.max(valid)) if valid.size else None,
    })
    path.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


def prepare_som(source_root, output_root, shape, transform, crs):
    source = source_root / "N/N02/CSDLv1/SOM/SOM.nc"
    subdataset = f"netcdf:{source}:SOM"
    destination = np.full(shape, -9999.0, dtype="float32")
    with rasterio.open(subdataset) as src:
        if src.count < 1 or src.nodata is None:
            raise ValueError("SOM 缺少有效波段或 NoData")
        # NetCDF 提供经纬度坐标，但未声明大地基准；WGS84 仅用于研究预览。
        # GDAL 的 NetCDF band 句柄在无 CRS 时无法可靠传递显式 src_crs，先读数组。
        reproject(
            source=src.read(1), destination=destination,
            src_transform=src.transform, src_crs="EPSG:4326", src_nodata=src.nodata,
            dst_transform=transform, dst_crs=crs, dst_nodata=-9999.0,
            resampling=Resampling.average,
        )
    save_preview(output_root / "n02_som_top_5km_preview.tif", destination, transform, crs, {
        "source": str(source), "indicator": "SOM", "depth_cm": [0, 4.5],
        "unit": "% of weight", "source_version": "CSDLv1",
        "crs_status": "lon/lat coordinates present; datum unverified, EPSG:4326 assumed for preview",
        "processing": "first NetCDF band, area-average reprojection to project 5 km grid",
    })


def prepare_slope(source_root, output_root, shape, transform, crs):
    paths = sorted((source_root / "X/X07/slope").glob("*_slope.tif"))
    if len(paths) != 9:
        raise ValueError(f"坡度瓦片应为 9 个，实际 {len(paths)} 个")
    destination = np.full(shape, -9999.0, dtype="float32")
    for path in paths:
        with rasterio.open(path) as src:
            piece = np.full(shape, -9999.0, dtype="float32")
            reproject(
                source=rasterio.band(src, 1), destination=piece,
                src_transform=src.transform, src_crs=src.crs, src_nodata=src.nodata,
                dst_transform=transform, dst_crs=crs, dst_nodata=-9999.0,
                resampling=Resampling.average,
            )
            mask = piece != -9999.0
            destination[mask] = piece[mask]
    save_preview(output_root / "x07_slope_5km_preview.tif", destination, transform, crs, {
        "source": [str(p) for p in paths], "indicator": "slope",
        "unit": "degree", "source_version": "SRTM V4.1 / Horn-derived",
        "processing": "nine slope tiles, area-average reprojection to project 5 km grid",
        "scope": "100–115°E, 30–45°N; not clipped to validated project regions",
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("data/processed/nx"))
    args = parser.parse_args()
    (width, height), transform, crs = target_grid()
    shape = (height, width)
    prepare_som(args.source_root, args.output_root, shape, transform, crs)
    prepare_slope(args.source_root, args.output_root, shape, transform, crs)


if __name__ == "__main__":
    main()
