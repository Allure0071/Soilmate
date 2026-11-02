"""将全球候选预览限制在项目现有中国土壤覆盖网格内。"""

import json
from pathlib import Path

import numpy as np
import rasterio

from backend.app.db import GRID_DIMS, get_conn


def main():
    width, height = GRID_DIMS[5]
    coverage = np.zeros((height, width), dtype=bool)
    conn = get_conn(5)
    for row, col in conn.execute("SELECT row, col FROM points WHERE v_soil_ph IS NOT NULL"):
        coverage[row, col] = True
    conn.close()

    root = Path("data/processed/nx")
    for pattern in ("x02_pet_*_5km_preview.tif", "x06_sm_*_5km_preview.tif"):
        for path in sorted(root.glob(pattern)):
            with rasterio.open(path, "r+") as dst:
                values = dst.read(1)
                values[~coverage] = dst.nodata
                dst.write(values, 1)
                valid = values[values != dst.nodata]
            report_path = path.with_suffix(".json")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report.update({
                "coverage_mask": "project 5 km cells with non-null v_soil_ph; proxy for existing soil coverage",
                "valid_cells": int(valid.size),
                "min": float(valid.min()) if valid.size else None,
                "max": float(valid.max()) if valid.size else None,
            })
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(path.name, report["valid_cells"])


if __name__ == "__main__":
    main()
