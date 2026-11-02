"""Prepare a clearly labelled reference view of the supplied Z01 zones.

The source boundary is not asserted to match the project's N+X model zones.
The 1 km lookup raster is approximate near boundaries; it is for display only.
"""

import json
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.features import rasterize, shapes
from rasterio.transform import from_origin
from rasterio.warp import transform_geom
import shapefile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"E:\soil_data\new-chat\Z\Z01\Agr_qu.shp")
OUT = ROOT / "data" / "processed"
LOOKUP = OUT / "z01_reference_1km.tif"
BOUNDARIES = OUT / "z01_reference_boundaries.geojson"


def main():
    reader = shapefile.Reader(str(SOURCE), encoding="gbk")
    source_crs = CRS.from_wkt(SOURCE.with_suffix(".prj").read_text(encoding="utf-8"))
    zones = {}
    polygons = []
    for item in reader.iterShapeRecords():
        code = item.record[5]
        zone_id = ord(code) - ord("A") + 1
        zones[str(zone_id)] = {
            "code": code,
            "source_name": item.record[4].strip(),
            "english_name": item.record[6].strip(),
        }
        polygons.append((item.shape.__geo_interface__, zone_id))

    xmin, ymin, xmax, ymax = reader.bbox
    left = math.floor(xmin / 1000) * 1000
    top = math.ceil(ymax / 1000) * 1000
    OUT.mkdir(parents=True, exist_ok=True)
    for cell_size, path in [(1000, LOOKUP), (5000, None)]:
        transform = from_origin(left, top, cell_size, cell_size)
        width = math.ceil((xmax - left) / cell_size)
        height = math.ceil((top - ymin) / cell_size)
        raster = rasterize(polygons, out_shape=(height, width), transform=transform, fill=0, dtype="uint8")
        if path:
            with rasterio.open(path, "w", driver="GTiff", width=width, height=height,
                               count=1, dtype="uint8", crs=source_crs, transform=transform,
                               compress="deflate", nodata=0) as dataset:
                dataset.write(raster, 1)
        else:
            features = []
            for geometry, value in shapes(raster, mask=raster != 0, transform=transform):
                info = zones[str(int(value))]
                features.append({
                    "type": "Feature",
                    "properties": {**info, "status": "reference_only"},
                    "geometry": transform_geom(source_crs, "EPSG:4326", geometry, precision=5),
                })
            BOUNDARIES.write_text(json.dumps({
                "type": "FeatureCollection", "features": features,
            }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    (OUT / "z01_reference_metadata.json").write_text(json.dumps({
        "source": str(SOURCE), "source_crs": source_crs.to_wkt(),
        "status": "reference_only", "lookup_resolution_m": 1000,
        "warning": "Source zones are not yet mapped to the project's N+X agricultural zones; lookup is approximate near boundaries and must not drive scoring.",
        "zones": zones,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prepared {len(zones)} source zones, {len(features)} display polygons")


if __name__ == "__main__":
    main()
