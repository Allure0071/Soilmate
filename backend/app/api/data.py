"""只读分页浏览 SQLite 数据表。"""
from fastapi import APIRouter, Query
from typing import Literal, Optional

from ..db import Resolution, get_conn

router = APIRouter()
TABLE_ORDER = {"points": "row, col", "indicators": "id", "meta": "key"}


@router.get("/api/data")
def browse_data(res: Resolution = Resolution.km5,
                table: Literal["points", "indicators", "meta"] = "points",
                page: int = Query(1, ge=1),
                page_size: int = Query(20, ge=1, le=100),
                lon_min: Optional[float] = None,
                lon_max: Optional[float] = None,
                lat_min: Optional[float] = None,
                lat_max: Optional[float] = None):
    """分页返回白名单中的表；经纬度过滤仅适用于 points。"""
    conn = get_conn(res)
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    where, params = "", []
    if table == "points" and None not in (lon_min, lon_max, lat_min, lat_max):
        where = "WHERE lon BETWEEN ? AND ? AND lat BETWEEN ? AND ?"
        params = [lon_min, lon_max, lat_min, lat_max]
    total = conn.execute(f"SELECT count(*) FROM {table} {where}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = conn.execute(
        f"SELECT * FROM {table} {where} ORDER BY {TABLE_ORDER[table]} LIMIT ? OFFSET ?",
        params + [page_size, offset]).fetchall()
    names = {r[0]: r[1] for r in conn.execute("SELECT col_name, cname FROM indicators")} if table == "points" else {}
    conn.close()
    return {
        "res": res,
        "total": total,
        "page": page,
        "page_size": page_size,
        "columns": [{"col": c, "cname": names.get(c[2:], c) if c.startswith("v_") else c} for c in cols],
        "rows": [[None if v is None else v for v in r] for r in rows],
    }
