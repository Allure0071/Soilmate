"""将已核对的 N/X 栅格逐层对齐到 5 km 项目网格。

只写研究预览，不改原始文件或正式 SQLite 数据库。
"""

import argparse
import subprocess
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

from prepare_nx_previews import save_preview, target_grid


N01_DEPTHS = ["5-15", "15-30", "30-60", "100-200"]
SOM_BOTTOMS = [4.5, 9.1, 16.6, 28.9, 49.3, 82.9, 138.3, 229.6]


def warp_band(source, band, shape, transform, crs, source_crs=None, array_source=False):
    target = np.full(shape, -9999.0, dtype="float32")
    with rasterio.open(source) as src:
        data = src.read(band) if array_source else rasterio.band(src, band)
        reproject(
            source=data, destination=target,
            src_transform=src.transform, src_crs=source_crs or src.crs,
            src_nodata=src.nodata, dst_transform=transform, dst_crs=crs,
            dst_nodata=-9999.0, resampling=Resampling.average,
        )
    return target


def n01_depths(root, out, shape, transform, crs):
    for depth in N01_DEPTHS:
        archive = root / "N/N01" / f"AN_{depth}cm_1km_mean.zip"
        source = f"/vsizip/{archive.as_posix()}/AN_{depth}cm_1km.tif"
        values = warp_band(source, 1, shape, transform, crs)
        save_preview(out / f"n01_an_{depth.replace('-', '_')}cm_5km_preview.tif", values, transform, crs, {
            "source": str(archive), "indicator": "AN", "depth_cm": [float(v) for v in depth.split("-")],
            "unit_status": "unverified; raw source values", "processing": "area-average reprojection",
        })


def som_depths(root, out, shape, transform, crs):
    source = root / "N/N02/CSDLv1/SOM/SOM.nc"
    subdataset = f"netcdf:{source}:SOM"
    with rasterio.open(subdataset) as src:
        if src.count != len(SOM_BOTTOMS):
            raise ValueError("SOM 土层数量与预期不符")
        for band in range(2, src.count + 1):
            values = np.full(shape, -9999.0, dtype="float32")
            reproject(
                source=src.read(band), destination=values,
                src_transform=src.transform, src_crs="EPSG:4326", src_nodata=src.nodata,
                dst_transform=transform, dst_crs=crs, dst_nodata=-9999.0,
                resampling=Resampling.average,
            )
            top, bottom = SOM_BOTTOMS[band - 2], SOM_BOTTOMS[band - 1]
            save_preview(out / f"n02_som_band{band}_5km_preview.tif", values, transform, crs, {
                "source": str(source), "indicator": "SOM", "depth_cm": [top, bottom],
                "unit": "% of weight", "crs_status": "lon/lat coordinates; datum unverified",
                "processing": "area-average reprojection, EPSG:4326 assumed for preview",
            })


def al_depths(root, out, shape, transform, crs):
    source = root / "N/N02/CSDLv1/AL/AL.nc"
    subdataset = f"netcdf:{source}:AL"
    with rasterio.open(subdataset) as src:
        if src.count != len(SOM_BOTTOMS):
            raise ValueError("AL 土层数量与预期不符")
        for band in range(1, src.count + 1):
            values = np.full(shape, -9999.0, dtype="float32")
            reproject(
                source=src.read(band), destination=values,
                src_transform=src.transform, src_crs="EPSG:4326", src_nodata=src.nodata,
                dst_transform=transform, dst_crs=crs, dst_nodata=-9999.0,
                resampling=Resampling.average,
            )
            top = 0 if band == 1 else SOM_BOTTOMS[band - 2]
            bottom = SOM_BOTTOMS[band - 1]
            if not np.any(values != -9999.0):
                print(f"SKIP AL band {band}: no valid cells on target grid", flush=True)
                continue
            save_preview(out / f"x05_al_band{band}_5km_preview.tif", values, transform, crs, {
                "source": str(source), "indicator": "exchangeable_Al3+", "depth_cm": [top, bottom],
                "unit": "me/100 g", "crs_status": "lon/lat coordinates; datum unverified",
                "processing": "area-average reprojection, EPSG:4326 assumed for preview",
            })


def x06_sm(root, out, shape, transform, crs):
    source = root / "X/X06/GLASS_SM_2020_ave.tif"
    values = warp_band(source, 1, shape, transform, crs)
    save_preview(out / "x06_sm_2020_5km_preview.tif", values, transform, crs, {
        "source": str(source), "indicator": "GLASS_SM", "year": 2020,
        "unit_status": "unverified; raw source values", "processing": "area-average reprojection from sinusoidal CRS",
    })


def x04_erosion(root, out, staging, shape, transform, crs):
    archive = root / "X/X04/SoilErasionChina_2000-2015.zip"
    target_dir = staging / "x04"
    target_dir.mkdir(parents=True, exist_ok=True)
    for year in (2000, 2005, 2010, 2015):
        member = f"SoilErosionData/SE{year}.tif"
        path = target_dir / member
        if not path.is_file():
            subprocess.run(["tar", "-xf", str(archive), "-C", str(target_dir), member], check=True)
        # 9999 是源文件中的特殊高值（约 1% 像元），元数据未说明其含义；
        # 保守地从预览中排除，防止它污染 5 km 面积平均。
        with rasterio.open(path) as src:
            source_data = src.read(1)
            source_data[(source_data == src.nodata) | (source_data >= 9999)] = -9999.0
            values = np.full(shape, -9999.0, dtype="float32")
            reproject(
                source=source_data, destination=values,
                src_transform=src.transform, src_crs=src.crs, src_nodata=-9999.0,
                dst_transform=transform, dst_crs=crs, dst_nodata=-9999.0,
                resampling=Resampling.average,
            )
        save_preview(out / f"x04_erosion_{year}_5km_preview.tif", values, transform, crs, {
            "source": f"{archive}!{member}", "indicator": "soil_erosion_modulus", "year": year,
            "unit": "t/(ha·year)", "processing": "area-average reprojection from Beijing 1954 Albers",
            "quality_note": "source value 9999 treated as unverified sentinel and excluded",
        })
        path.unlink()


def x04_southwest(root, out, staging, shape, transform, crs):
    archive = root / "X/X04/SoilErosionSouthWestChina_2000-2015.zip"
    target_dir = staging / "x04sw"
    target_dir.mkdir(parents=True, exist_ok=True)
    for year in range(2000, 2016):
        member = f"SoilErosion_A_2000_2015/A{year}.tif"
        path = target_dir / member
        if not path.is_file():
            subprocess.run(["tar", "-xf", str(archive), "-C", str(target_dir), member], check=True)
        values = warp_band(path, 1, shape, transform, crs)
        save_preview(out / f"x04_sw_erosion_{year}_5km_preview.tif", values, transform, crs, {
            "source": f"{archive}!{member}", "indicator": "soil_erosion_modulus_sw",
            "year": year, "unit": "t/(ha·year)",
            "processing": "Southwest RUSLE product, area-average reprojection from WGS84 Albers",
        })
        path.unlink()


def pet_years(root, out, staging, shape, transform, crs):
    target_dir = staging / "x02"
    target_dir.mkdir(parents=True, exist_ok=True)
    for year in range(2017, 2025):
        archive = root / "X/X02" / f"pet_{year}.rar"
        output_path = out / f"x02_pet_{year}_5km_preview.tif"
        if output_path.is_file() and output_path.with_suffix(".json").is_file():
            continue
        member = f"pet_{year}.nc"
        path = target_dir / member
        if not path.is_file():
            try:
                subprocess.run(["tar", "-xf", str(archive), "-C", str(target_dir), member], check=True)
            except subprocess.CalledProcessError:
                path.unlink(missing_ok=True)
                print(f"SKIP {year}: archive extraction failed: {archive}", flush=True)
                continue
        monthly_sum = np.zeros(shape, dtype="float32")
        all_valid = np.ones(shape, dtype=bool)
        with rasterio.open(f"netcdf:{path}:etp") as src:
            if src.count != 12:
                raise ValueError(f"{year} PET 预期 12 个波段，实际 {src.count}")
            for band in range(1, 13):
                monthly = np.full(shape, -9999.0, dtype="float32")
                # NetCDF 经纬度网格未声明 CRS；经纬度坐标按 EPSG:4326 试算。
                reproject(
                    source=src.read(band), destination=monthly,
                    src_transform=src.transform, src_crs="EPSG:4326", src_nodata=src.nodata,
                    dst_transform=transform, dst_crs=crs, dst_nodata=-9999.0,
                    resampling=Resampling.average,
                )
                valid = monthly != -9999.0
                all_valid &= valid
                monthly_sum[valid] += monthly[valid] * 0.1  # NetCDF unit: 0.1 mm
        monthly_sum[~all_valid] = -9999.0
        save_preview(out / f"x02_pet_{year}_5km_preview.tif", monthly_sum, transform, crs, {
            "source": f"{archive}!{member}", "indicator": "PET", "year": year,
            "unit": "mm/year", "processing": "sum of 12 monthly PET bands × 0.1, then 5 km area-average",
            "crs_status": "lon/lat coordinates; datum assumed EPSG:4326 for preview",
        })
        path.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("data/processed/nx"))
    parser.add_argument("--staging", type=Path, default=Path("data/staging"))
    parser.add_argument("--group", choices=["n01", "som", "al", "x02", "x04", "x04sw", "x06", "all"], default="all")
    args = parser.parse_args()
    (width, height), transform, crs = target_grid()
    shape = (height, width)
    tasks = {"n01": n01_depths, "som": som_depths, "al": al_depths, "x06": x06_sm}
    for name, task in tasks.items():
        if args.group in ("all", name):
            task(args.source_root, args.output_root, shape, transform, crs)
    if args.group in ("all", "x04"):
        x04_erosion(args.source_root, args.output_root, args.staging, shape, transform, crs)
    if args.group in ("all", "x04sw"):
        x04_southwest(args.source_root, args.output_root, args.staging, shape, transform, crs)
    if args.group in ("all", "x02"):
        pet_years(args.source_root, args.output_root, args.staging, shape, transform, crs)


if __name__ == "__main__":
    main()
