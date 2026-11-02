"""数据库连接与网格常量。"""
import sqlite3
from enum import IntEnum
from pathlib import Path


class Resolution(IntEnum):
    km1 = 1
    km5 = 5

# 各分辨率数据库（5km 默认；1km 第二期）
DB_PATHS = {
    5: Path(__file__).absolute().parents[2] / "data" / "soil.sqlite",
    1: Path(__file__).absolute().parents[2] / "data" / "soil_1km.sqlite",
}

# 各分辨率参考网格尺寸（5km: soil_ph_5km.tif；1km: soil_ph_1km.tif，Albers 等积投影）
GRID_DIMS = {5: (967, 809), 1: (4833, 4045)}

# 兼容旧引用
DB_PATH = DB_PATHS[5]
GRID_WIDTH, GRID_HEIGHT = GRID_DIMS[5]

# 参考网格（Albers 等积投影，5km/1km 共用同一投影定义）
GRID_CRS = (
    'PROJCS["Albers_Conic_Equal_Area",GEOGCS["WGS 84",'
    'DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],'
    'PROJECTION["Albers_Conic_Equal_Area"],'
    'PARAMETER["latitude_of_center",0],PARAMETER["longitude_of_center",105],'
    'PARAMETER["standard_parallel_1",25],PARAMETER["standard_parallel_2",47],'
    'PARAMETER["false_easting",0],PARAMETER["false_northing",0],'
    'UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'
)
# transform 由初始化脚本写入各库 meta 表
_grid_meta: dict[int, dict] = {}


def get_conn(res: int = 5) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATHS[res]}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def grid_meta(res: int = 5) -> dict:
    """从对应分辨率 meta 表读 transform（缓存）。"""
    if res not in _grid_meta:
        conn = get_conn(res)
        rows = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        conn.close()
        _grid_meta[res] = rows
    return _grid_meta[res]
