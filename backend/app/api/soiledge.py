"""Research-only bridge for the legacy Soiledge workbook and optional local AI."""
from __future__ import annotations

import io
import json
import math
import re
import statistics
import zipfile
from xml.etree import ElementTree as ET

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from ..models.gateway import ModelGateway, ModelUnavailable
from .auth import current_user_id

router = APIRouter(prefix="/api/soiledge", tags=["soiledge"])
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
HEADERS = {
    "土壤 pH": "ph", "土壤有机碳（OC）%": "organic_carbon", "全氮（TN）风干基%": "total_nitrogen",
    "有效磷（AP）（mg/kg）": "phosphorus", "速效钾（AK）（mg/kg）": "potassium",
    "碱解氮（AN）（mg/kg）": "nitrogen", "全磷（TP）(g/kg)": "total_phosphorus",
    "全钾（TK）(g/kg)": "total_potassium", "黏粒含量（Clay）%": "clay",
    "容重（BD）g/cm3": "bulk_density", "阳离子交换量cmol（+）/kg（CEC）": "cec",
}
ORDER = ["phosphorus", "clay", "total_phosphorus", "potassium", "total_nitrogen", "cec",
         "total_potassium", "bulk_density", "organic_carbon", "nitrogen", "ph"]
WEIGHTS = [.421316, .192481, .104318, .056098, .055143, .048418, .033938, .028733, .025493, .020388, .013673]
DIRECTIONS = ["pos", "mid", "pos", "pos", "pos", "pos", "pos", "neg", "pos", "pos", "mid"]
THRESHOLDS = {"设施蔬菜": 35.0, "水稻": 14.5, "玉米": 16.0, "大豆": 20.0, "中药": 35.0, "大田": 30.0}


def _column_index(address: str) -> int:
    letters = re.match(r"[A-Z]+", address)
    if not letters:
        raise ValueError("Excel 单元格位置无效")
    index = 0
    for char in letters.group():
        index = index * 26 + ord(char) - 64
    return index - 1


def _read_xlsx(content: bytes) -> list[list[str]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
        names = archive.namelist()
        if len(names) > 2000 or sum(archive.getinfo(name).file_size for name in names) > 80_000_000:
            raise ValueError("Excel 文件解压后过大")
        sheets = sorted(name for name in names if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name))
        if not sheets:
            raise ValueError("未找到 Excel 工作表")
        strings = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(node.itertext()) for node in root.findall("x:si", NS)]
        root = ET.fromstring(archive.read(sheets[0]))
        rows = []
        for row in root.findall(".//x:sheetData/x:row", NS):
            cells = {}
            for cell in row.findall("x:c", NS):
                index = _column_index(cell.attrib.get("r", ""))
                if index > 300:
                    raise ValueError("Excel 列数过多")
                value = cell.find("x:v", NS)
                inline = cell.find("x:is", NS)
                text = value.text if value is not None and value.text is not None else ""
                if cell.attrib.get("t") == "s" and text:
                    text = strings[int(text)]
                elif inline is not None:
                    text = "".join(inline.itertext())
                cells[index] = text.strip()
            if cells:
                rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
            if len(rows) > 10000:
                raise ValueError("单次最多处理 10000 行")
        return rows
    except (zipfile.BadZipFile, ET.ParseError, IndexError, KeyError) as exc:
        raise ValueError("Excel 文件格式不完整或已损坏") from exc


def _numeric(value: str) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def _guess_crop(sample: str, location: str) -> str:
    if "寿光" in location or "五常市-1" in location:
        return "设施蔬菜"
    if "五常市-2" in location:
        return "水稻"
    for text, crop in (("玉米", "玉米"), ("大豆", "大豆"), ("中药", "中药"), ("平贝", "中药"), ("水稻", "水稻")):
        if text in sample:
            return crop
    if any(text in sample for text in ("韭菜", "辣椒", "黄瓜", "番茄", "茄子", "芹菜")):
        return "设施蔬菜"
    return "大田"


def _evaluate(rows: list[list[str]], crop_override: str | None) -> dict:
    header_row = next((index for index, row in enumerate(rows[:5]) if "采样点编号" in row), None)
    if header_row is None:
        raise ValueError("未找到‘采样点编号’列；请使用 Soiledge 原 Excel 模板")
    headers = rows[header_row]
    index = {name: i for i, name in enumerate(headers)}
    available = [key for key in ORDER if key in index or any(HEADERS.get(name) == key for name in headers)]
    if len(available) < 6:
        raise ValueError("可识别的指标列不足 6 项")
    mapped = {key: index.get(key, next((i for i, name in enumerate(headers) if HEADERS.get(name) == key), -1)) for key in available}
    records = []
    for cells in rows[header_row + 1:]:
        site = cells[index["采样点编号"]] if index["采样点编号"] < len(cells) else ""
        if not site:
            continue
        get = lambda name: cells[index[name]] if name in index and index[name] < len(cells) else ""
        records.append({"site": site, "location": get("企业编号/采样时间"), "sample": get("样品编号"),
                        "values": {key: _numeric(cells[mapped[key]]) if mapped[key] < len(cells) else None for key in available}})
    if not records:
        raise ValueError("没有可处理的样点记录")
    if crop_override and crop_override not in THRESHOLDS:
        raise ValueError("作物类型无效")
    # Legacy process_upload.py: batch-specific median imputation, min/max, no weight renormalization.
    columns = {}
    for key in available:
        actual = [record["values"][key] for record in records if record["values"][key] is not None]
        if not actual:
            raise ValueError(f"指标 {key} 全部为空，无法按原小程序算法处理")
        median = statistics.median(actual)
        filled = [record["values"][key] if record["values"][key] is not None else median for record in records]
        columns[key] = (filled, min(filled), max(filled), statistics.median(filled))
    result = []
    for row_index, record in enumerate(records):
        score = 0.0
        for key, weight, direction in zip(ORDER, WEIGHTS, DIRECTIONS):
            if key not in columns:
                continue
            values, low, high, middle = columns[key]
            value = values[row_index]
            if high == low:
                normalized = .5
            elif direction == "neg":
                normalized = (high - value) / (high - low)
            elif direction == "mid":
                deviation = max(abs(high - middle), abs(low - middle))
                normalized = 1 - abs(value - middle) / deviation if deviation else 1.0
            else:
                normalized = (value - low) / (high - low)
            score += (normalized + .0001) * weight * 100
        score = round(score, 2)
        crop = crop_override or _guess_crop(record["sample"], record["location"])
        result.append({"site": record["site"], "location": record["location"], "sample": record["sample"],
                       "crop": crop, "score": score, "threshold": THRESHOLDS[crop],
                       "level": "达到参照阈值" if score >= THRESHOLDS[crop] else "低于参照阈值"})
    result.sort(key=lambda item: (item["level"] != "达到参照阈值", -item["score"]))
    return {"total": len(result), "above": sum(item["level"] == "达到参照阈值" for item in result),
            "below": sum(item["level"] == "低于参照阈值" for item in result),
            "imputed_cells": sum(record["values"][key] is None for record in records for key in available),
            "available_indicators": available, "rows": result,
            "method": "Soiledge process_upload.py: batch-specific median imputation and min-max normalization; research estimate only"}


@router.post("/upload")
async def upload(request: Request, crop: str = ""):
    content = await request.body()
    if not content or len(content) > 12_000_000:
        raise HTTPException(413, "请选择不超过 12 MB 的 .xlsx 文件")
    try:
        return _evaluate(_read_xlsx(content), crop or None)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


class AiInput(BaseModel):
    crop: str = Field(max_length=30)
    score: float
    threshold: float
    diagnostics: list[dict] = Field(max_length=11)


@router.post("/ai")
def ai_evaluate(payload: AiInput):
    current_user_id()
    if payload.crop not in THRESHOLDS or not math.isfinite(payload.score):
        raise HTTPException(400, "评估输入无效")
    details = []
    for entry in payload.diagnostics:
        label = str(entry.get("label", ""))[:40]
        raw = str(entry.get("raw", ""))[:30]
        value = str(entry.get("score", ""))[:30]
        details.append(f"{label}: 原始值 {raw}, 标准化值 {value}")
    prompt = (f"作物：{payload.crop}\n整份样本的 Soiledge SHI 研究估算：{payload.score:.2f} / 100；"
              f"仅用于整份 SHI 比较的作物参照阈值：{payload.threshold:.2f}。\n各指标如下，标准化值也是 0–100：\n"
              + "\n".join(details)
              + "\n请只根据列出的指标指出标准化值较低的项目及可进一步核验的管理方向。"
                "作物参照阈值只适用于整份 SHI，绝对不能把它当成任一指标的阈值。"
                "未列出的指标一律不推断；不判断未给出的有机质、土层、年份和土壤结构。"
                "不用 Markdown，不给未经验证的施用剂量，不宣称正式诊断。")
    try:
        response=ModelGateway().answer([
            {'role':'system','content':'你是土壤研究助理。仅解释给出的研究估算，不修改分数、不补造缺失数据、不给未经验证的剂量。只输出最终回答。'},
            {'role':'user','content':prompt}])
        return {'available':True,'evaluation':response['text'],'model':response['model'],'truncated':response['truncated']}
    except ModelUnavailable as error:
        raise HTTPException(503,{'code':error.code,'message':str(error)})
