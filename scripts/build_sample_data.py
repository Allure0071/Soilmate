"""Build small, synthetic map fixtures from the local schema (no source points copied)."""
import argparse
import sqlite3
from pathlib import Path

from pyproj import CRS, Transformer


ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    "soil_ph": (6.2, 0.04),
    "soil_soc": (18.0, 0.35),
    "soil_bd": (1.28, 0.006),
    "soil_tn": (1.6, 0.025),
    "annual_rain": (650.0, 3.0),
    "ndvi": (0.55, 0.004),
}
CENTERS = [(116.40, 39.90), (104.07, 30.67), (114.30, 30.60)]


def build(resolution):
    source = ROOT / "data" / ("soil.sqlite" if resolution == 5 else "soil_1km.sqlite")
    output_dir = ROOT / "sample-data"
    output_dir.mkdir(exist_ok=True)
    target = output_dir / source.name
    if target.exists():
        raise SystemExit(f"Refusing to replace existing fixture: {target}")
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as original, sqlite3.connect(target) as sample:
        for name in ("points", "indicators", "meta"):
            ddl = original.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()[0]
            sample.execute(ddl)
        meta = dict(original.execute("SELECT key,value FROM meta"))
        sample.executemany("INSERT INTO meta VALUES (?,?)", meta.items())
        columns = [row[1] for row in original.execute("PRAGMA table_info(indicators)")]
        indicators = original.execute("SELECT * FROM indicators ORDER BY id").fetchall()
        field_names = {row[2] for row in indicators}
        for row in indicators:
            record = dict(zip(columns, row))
            record.update(source_file="SYNTHETIC_TEST_DATA", band=1, min=None, max=None,
                          mean=None, valid_count=0, legend_min=None, legend_max=None)
            sample.execute("INSERT INTO indicators VALUES (" + ",".join("?" for _ in columns) + ")",
                           [record[name] for name in columns])
        point_columns = [row[1] for row in original.execute("PRAGMA table_info(points)")]
        to_grid = Transformer.from_crs("EPSG:4326", CRS.from_wkt(meta["grid_crs"]), always_xy=True)
        from_grid = Transformer.from_crs(CRS.from_wkt(meta["grid_crs"]), "EPSG:4326", always_xy=True)
        a, c, e, f = (float(meta[key]) for key in ("a", "c", "e", "f"))
        rows = []
        for site, (lon, lat) in enumerate(CENTERS):
            x, y = to_grid.transform(lon, lat)
            center_col, center_row = int((x - c) // a), int((y - f) // e)
            for dr in range(-8, 9):
                for dc in range(-8, 9):
                    r, col = center_row + dr, center_col + dc
                    point_lon, point_lat = from_grid.transform(c + (col + 0.5) * a,
                                                               f + (r + 0.5) * e)
                    values = {"row": r, "col": col, "lon": point_lon, "lat": point_lat}
                    for field, (base, step) in FIELDS.items():
                        if field in field_names:
                            values["v_" + field] = round(base + site * step * 5 + dr * step + dc * step / 2, 4)
                    rows.append([values.get(name) for name in point_columns])
        sample.executemany("INSERT INTO points VALUES (" + ",".join("?" for _ in point_columns) + ")", rows)
        sample.execute("CREATE INDEX IF NOT EXISTS sample_points_row_col ON points(row,col)")
        sample.commit()
    print(f"{target}: {len(rows)} synthetic points")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    for resolution in (5, 1):
        build(resolution)
