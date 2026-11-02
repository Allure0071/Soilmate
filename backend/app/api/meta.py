"""meta 与 regions 接口。"""
from pathlib import Path

from fastapi import APIRouter

from ..db import Resolution, get_conn, grid_meta, GRID_DIMS

router = APIRouter()

SCORES_DIR = Path(__file__).absolute().parents[3] / "data" / "scores"
TILES_DIR = Path(__file__).absolute().parents[2] / "static" / "tiles"


@router.get("/api/meta")
def meta(res: Resolution = Resolution.km5):
    m = grid_meta(res)
    gw, gh = GRID_DIMS[res]
    return {
        "grid_crs_wkt": m.get("grid_crs"),
        "res": res,
        "grid_width": gw,
        "grid_height": gh,
        "resolution_m": float(m.get("a", 0)),
        "version": "phase2",
        "tiles_available": (TILES_DIR / "1km").is_dir() if res == Resolution.km1 else (
            TILES_DIR.is_dir() and any(p.is_dir() and p.name != "1km" for p in TILES_DIR.iterdir())
        ),
    }


@router.get("/api/regions")
def regions():
    """9 大农业区 SHI 均值（第二期接入完整评分逻辑，本期返回区域统计）。"""
    import csv
    result = []
    if SCORES_DIR.exists():
        for f in sorted(SCORES_DIR.glob("*_score.csv")):
            name = f.stem.replace("_score", "")
            vals = []
            with open(f, newline="") as fh:
                reader = csv.DictReader(fh)
                col = None
                for r in reader:
                    if col is None:
                        col = next((k for k in r if "shi" in k.lower() or "score" in k.lower()), None)
                        if col is None:
                            break
                    try:
                        vals.append(float(r[col]))
                    except (TypeError, ValueError):
                        pass
            if vals:
                result.append({"region": name, "n": len(vals),
                               "mean": sum(vals) / len(vals)})
    return {"phase": 1, "regions": result}
