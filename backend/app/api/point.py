"""点查询接口：经纬度 -> 该点全部指标值。"""
from fastapi import APIRouter, HTTPException, Query

from ..db import Resolution, get_conn, grid_meta, GRID_DIMS

router = APIRouter()


def _lonlat_to_rowcol(lon: float, lat: float, res: int = 5) -> tuple[int, int]:
    """经纬度 -> 参考网格（Albers）行列号。"""
    from pyproj import CRS, Transformer
    from rasterio.transform import rowcol

    meta = grid_meta(res)
    transform = _affine_from_meta(meta)
    transformer = Transformer.from_crs("EPSG:4326", CRS.from_wkt(meta["grid_crs"]), always_xy=True)
    x, y = transformer.transform(lon, lat)
    r, c = rowcol(transform, x, y)
    r, c = int(r), int(c)
    gw, gh = GRID_DIMS[res]
    if not (0 <= r < gh and 0 <= c < gw):
        raise HTTPException(status_code=404, detail="坐标超出数据范围")
    return r, c


def _affine_from_meta(meta: dict):
    from affine import Affine
    return Affine(
        float(meta["a"]), float(meta["b"]), float(meta["c"]),
        float(meta["d"]), float(meta["e"]), float(meta["f"]),
    )


@router.get("/api/point")
def query_point(lon: float = Query(..., ge=-180, le=180),
                lat: float = Query(..., ge=-90, le=90),
                res: Resolution = Resolution.km5):
    r, c = _lonlat_to_rowcol(lon, lat, res)
    conn = get_conn(res)
    ind_rows = conn.execute(
        "SELECT name, col_name, cname, unit, min, max FROM indicators ORDER BY id"
    ).fetchall()
    row = conn.execute(
        f"SELECT * FROM points WHERE row=? AND col=?", (r, c)
    ).fetchone()
    conn.close()

    values = {}
    if row is not None:
        d = dict(row)
        for ind in ind_rows:
            v = d.get("v_" + ind["col_name"])
            values[ind["col_name"]] = {
                "name": ind["name"],
                "cname": ind["cname"],
                "unit": ind["unit"],
                "min": ind["min"],
                "max": ind["max"],
                "value": v,  # None 表示该指标此点无效
            }
    return {
        "lon": lon, "lat": lat, "row": r, "col": c, "res": res,
        "found": row is not None,
        "values": values,
    }
