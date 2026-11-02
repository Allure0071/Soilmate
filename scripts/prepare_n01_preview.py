"""将 CSDLv2 0–5 cm 碱解氮候选栅格对齐到项目 5 km 网格。

此脚本只生成原始值预览，不修改 SQLite，也不生成健康评分。
"""

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from rasterio.warp import Resampling, reproject

from backend.app.db import GRID_DIMS, grid_meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="AN_0-5cm_1km.tif 路径")
    parser.add_argument("--output", type=Path, default=Path("data/processed/nx/n01_an_0_5cm_5km_preview.tif"))
    args = parser.parse_args()

    meta = grid_meta(5)
    transform = Affine(*(float(meta[k]) for k in "abcdef"))
    width, height = GRID_DIMS[5]
    target_crs = rasterio.crs.CRS.from_wkt(meta["grid_crs"])
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(args.source) as src:
        if src.crs is None or src.nodata is None or src.count != 1:
            raise ValueError("源栅格必须明确声明 CRS、NoData 且只有一个波段")
        output_profile = {
            "driver": "GTiff", "width": width, "height": height, "count": 1,
            "dtype": "float32", "crs": target_crs, "transform": transform,
            "nodata": -9999.0, "compress": "deflate", "predictor": 3,
            "tiled": True, "blockxsize": 256, "blockysize": 256,
        }
        with rasterio.open(args.output, "w", **output_profile) as dst:
            reproject(
                source=rasterio.band(src, 1), destination=rasterio.band(dst, 1),
                src_transform=src.transform, src_crs=src.crs, src_nodata=src.nodata,
                dst_transform=transform, dst_crs=target_crs, dst_nodata=-9999.0,
                resampling=Resampling.average,
            )

    with rasterio.open(args.output) as dst:
        data = dst.read(1, masked=True)
        valid = data.compressed()
        report = {
            "source": str(args.source), "output": str(args.output),
            "indicator": "AN", "depth_cm": [0, 5], "source_version": "CSDLv2",
            "processing": "area-average reprojection to project 5 km Albers grid",
            "unit_status": "unverified; retain source numeric values",
            "valid_cells": int(valid.size), "total_cells": width * height,
            "min_raw": float(np.min(valid)) if valid.size else None,
            "max_raw": float(np.max(valid)) if valid.size else None,
        }
    args.output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
