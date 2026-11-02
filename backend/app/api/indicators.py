"""指标清单接口。"""
from fastapi import APIRouter

from ..db import Resolution, get_conn

router = APIRouter()


@router.get("/api/indicators")
def list_indicators(res: Resolution = Resolution.km5):
    conn = get_conn(res)
    rows = conn.execute(
        "SELECT id, name, col_name, source_file, band, unit, cname, "
        "min, max, mean, valid_count, legend_min, legend_max "
        "FROM indicators ORDER BY id"
    ).fetchall()
    conn.close()
    return {"count": len(rows), "res": res, "indicators": [dict(r) for r in rows]}
