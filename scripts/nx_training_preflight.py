"""Check whether an N+X CSV is structurally ready for supervised fitting.

This utility validates data readiness only. It never imputes values, creates
labels, assigns health scores, or fits a model.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REQUIRED = [
    "sample_id", "site_id", "source_record_id", "source_dataset_id",
    "region_code", "longitude", "latitude", "crs", "sampling_date",
    "location_precision_m", "land_use", "soil_type", "depth_top_cm", "depth_bottom_cm",
    "n_ece_value", "n_alkali_hydrolyzable_n_value", "n_bulk_density_value",
    "n_sand_pct_value", "n_cec_value", "n_ph_value",
    "n_organic_matter_value", "n_provenance_json", "x_indicator_codes", "x_values_json",
    "x_units_json", "x_methods_json",
    "label_health_grade", "label_health_score", "label_function_name",
    "label_function_value", "label_definition", "label_source", "label_method",
    "label_assessor", "label_date", "label_time_window", "label_independence_verified",
]
N_FEATURES = [
    "n_ece_value", "n_alkali_hydrolyzable_n_value", "n_bulk_density_value",
    "n_sand_pct_value", "n_cec_value", "n_ph_value",
    "n_organic_matter_value",
]
N_METADATA = [
    "n_ece_unit", "n_ece_method", "n_alkali_hydrolyzable_n_unit",
    "n_alkali_hydrolyzable_n_method", "n_bulk_density_unit",
    "n_bulk_density_method", "n_sand_pct_unit", "n_sand_pct_method",
    "n_cec_unit", "n_cec_method", "n_ph_unit", "n_ph_method",
    "n_organic_matter_unit", "n_organic_matter_method",
]
LABELS = [
    "label_health_grade", "label_health_score", "label_function_value",
]
ROW_REQUIRED = [
    "sample_id", "site_id", "source_record_id", "source_dataset_id", "region_code",
    "longitude", "latitude", "crs", "sampling_date", "location_precision_m",
    "land_use", "soil_type", "depth_top_cm", "depth_bottom_cm", "n_provenance_json",
    "x_indicator_codes", "x_values_json", "x_units_json", "x_methods_json",
    "label_definition", "label_source", "label_method", "label_assessor",
    "label_date", "label_time_window", "label_independence_verified",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input UTF-8 CSV")
    parser.add_argument("--output", required=True, help="Output JSON report")
    args = parser.parse_args()

    source = Path(args.input)
    destination = Path(args.output)
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, str]] = []
    headers: list[str] = []

    if not source.exists():
        errors.append(f"输入文件不存在：{source}")
    else:
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            rows = list(reader)

    missing_columns = [column for column in REQUIRED if column not in headers]
    if missing_columns:
        errors.append("缺少必需字段：" + ", ".join(missing_columns))

    missing_rows = {column: 0 for column in N_FEATURES + LABELS}
    duplicate_sample_ids: list[str] = []
    duplicate_site_ids = Counter()
    regions = Counter()
    label_counts = Counter()
    seen_samples = set()
    labeled_rows = 0
    invalid_feature_values = 0
    invalid_x_payload_rows: list[int] = []
    row_missing_counts = Counter()
    label_target_types = set()

    for row_number, row in enumerate(rows, start=2):
        sample_id = row.get("sample_id", "").strip()
        site_id = row.get("site_id", "").strip()
        region = row.get("region_code", "").strip()
        if sample_id:
            if sample_id in seen_samples:
                duplicate_sample_ids.append(sample_id)
            seen_samples.add(sample_id)
        if site_id:
            duplicate_site_ids[site_id] += 1
        if region:
            regions[region] += 1
        for column in ROW_REQUIRED:
            if not row.get(column, "").strip():
                row_missing_counts[column] += 1
        if row.get("label_function_value", "").strip() and not row.get("label_function_name", "").strip():
            row_missing_counts["label_function_name (label_function_value 非空时必填)"] += 1
        for column in N_FEATURES + ["longitude", "latitude", "location_precision_m", "depth_top_cm", "depth_bottom_cm"]:
            value = row.get(column, "").strip()
            if value:
                try:
                    parsed = float(value)
                    if parsed != parsed or parsed in (float("inf"), float("-inf")):
                        invalid_feature_values += 1
                except ValueError:
                    invalid_feature_values += 1
        present_labels = [column for column in LABELS if row.get(column, "").strip()]
        if len(present_labels) == 1:
            labeled_rows += 1
            label_target_types.add(present_labels[0])
            label_counts[present_labels[0]] += 1
        elif len(present_labels) > 1:
            errors.append(f"第 {row_number} 行混有多个标签目标；每个训练文件只允许一个 Y")
        else:
            errors.append(f"第 {row_number} 行缺少标签 Y")
        for column in missing_rows:
            if not row.get(column, "").strip():
                missing_rows[column] += 1
        if row.get("x_values_json", "").strip():
            try:
                x_values = json.loads(row["x_values_json"])
                x_units = json.loads(row.get("x_units_json", ""))
                x_methods = json.loads(row.get("x_methods_json", ""))
                codes = [code.strip() for code in row.get("x_indicator_codes", "").split(";") if code.strip()]
                valid_x = (
                    isinstance(x_values, dict) and bool(x_values)
                    and isinstance(x_units, dict) and isinstance(x_methods, dict)
                    and set(x_values) == set(x_units) == set(x_methods) == set(codes)
                    and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                            and v == v and v not in (float("inf"), float("-inf"))
                            for v in x_values.values())
                    and all(isinstance(v, str) and v.strip() for v in list(x_units.values()) + list(x_methods.values()))
                )
                if not valid_x:
                    invalid_x_payload_rows.append(row_number)
            except (json.JSONDecodeError, TypeError):
                invalid_x_payload_rows.append(row_number)
        else:
            invalid_x_payload_rows.append(row_number)
        for column in ("x_indicator_codes", "x_units_json", "x_methods_json"):
            if not row.get(column, "").strip():
                invalid_x_payload_rows.append(row_number)
        if row.get("n_provenance_json", "").strip():
            try:
                provenance = json.loads(row["n_provenance_json"])
                expected_features = {column.removesuffix("_value") for column in N_FEATURES}
                if not isinstance(provenance, dict) or set(provenance) != expected_features:
                    errors.append(f"第 {row_number} 行 N 指标逐项来源字段不完整")
                elif any(not isinstance(item, dict) or not item.get("source_dataset_id") or not item.get("source_record_id")
                         for item in provenance.values()):
                    errors.append(f"第 {row_number} 行 N 指标来源缺少数据集或原记录 ID")
            except json.JSONDecodeError:
                errors.append(f"第 {row_number} 行 n_provenance_json 格式错误")
        if row.get("depth_top_cm", "").strip() and row.get("depth_bottom_cm", "").strip():
            try:
                if float(row["depth_top_cm"]) >= float(row["depth_bottom_cm"]):
                    errors.append(f"第 {row_number} 行土层深度上下界无效")
            except ValueError:
                errors.append(f"第 {row_number} 行土层深度不是数值")
        try:
            from datetime import date
            date.fromisoformat(row.get("sampling_date", "").strip())
            date.fromisoformat(row.get("label_date", "").strip())
        except ValueError:
            if row.get("sampling_date", "").strip() or row.get("label_date", "").strip():
                errors.append(f"第 {row_number} 行采样日期或标签日期不是 YYYY-MM-DD")
        if row.get("label_independence_verified", "").strip().lower() != "yes":
            errors.append(f"第 {row_number} 行标签独立性未由负责人核实")
        if row.get("crs", "").strip().upper() not in {"EPSG:4326", "WGS84"}:
            errors.append(f"第 {row_number} 行坐标 CRS 必须是 EPSG:4326/WGS84")
        for target in ("label_health_score", "label_function_value"):
            value = row.get(target, "").strip()
            if value:
                try:
                    parsed = float(value)
                    if parsed != parsed or parsed in (float("inf"), float("-inf")):
                        errors.append(f"第 {row_number} 行 {target} 不是有限数值")
                except ValueError:
                    errors.append(f"第 {row_number} 行 {target} 不是数值")
        try:
            longitude = float(row.get("longitude", ""))
            latitude = float(row.get("latitude", ""))
            if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                errors.append(f"第 {row_number} 行经纬度超出合法范围")
        except ValueError:
            pass

    if not rows:
        errors.append("没有训练样本行；当前文件只是空模板")
    if rows and not labeled_rows:
        errors.append("没有独立标签 Y；禁止监督拟合")
    elif rows and labeled_rows < len(rows):
        warnings.append(f"仅 {labeled_rows}/{len(rows)} 行存在标签；拟合前需解释缺失机制并完成样本筛选")
    if duplicate_sample_ids:
        errors.append(f"sample_id 重复：{len(duplicate_sample_ids)} 条重复记录")
    if invalid_feature_values:
        errors.append(f"坐标或 N 指标字段包含非数值内容：{invalid_feature_values} 处")
    if invalid_x_payload_rows:
        errors.append(f"X 指标代码、数值、单位、方法 JSON 缺失或键不一致：{len(invalid_x_payload_rows)} 行")
    if rows:
        missing_n_metadata = [column for column in N_METADATA if any(not row.get(column, "").strip() for row in rows)]
        if missing_n_metadata:
            errors.append("N 指标缺少单位或测定方法：" + ", ".join(missing_n_metadata))
        if len(label_target_types) > 1:
            errors.append("标签目标混杂；健康等级、健康分和功能观测必须拆成独立训练文件")
    if rows and any(missing_rows.get(column, len(rows)) for column in N_FEATURES):
        errors.append("N 七项有缺失；当前门槛要求完整 N+X 样本，不能默认以 0 填补")
    if len(regions) < 9:
        warnings.append(f"当前仅覆盖 {len(regions)} 个 region_code；若目标是全国九区，需逐区报告覆盖和验证能力")
    repeated_sites = sum(count > 1 for count in duplicate_site_ids.values())
    if repeated_sites:
        warnings.append(f"有 {repeated_sites} 个 site_id 含重复记录；交叉验证必须按 site_id 分组")

    if row_missing_counts:
        errors.append("必需逐行字段缺失计数：" + ", ".join(f"{key}={value}" for key, value in sorted(row_missing_counts.items())))
    ready = bool(rows) and not errors
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(source),
        "n_rows": len(rows),
        "n_columns": len(headers),
        "required_columns_missing": missing_columns,
        "rows_with_any_label_value": labeled_rows,
        "label_column_counts": dict(label_counts),
        "n_indicator_missing_counts": missing_rows,
        "region_row_counts": dict(regions),
        "duplicate_sample_id_count": len(duplicate_sample_ids),
        "repeated_site_count": repeated_sites,
        "preflight_passed": ready,
        "errors": errors,
        "warnings": warnings,
        "scope": "仅代表结构门槛检查通过；标签语义独立性、样本量充分性及模型有效性仍须人工/科学审查",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # Escaped JSON keeps console output portable across Windows code pages.
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
