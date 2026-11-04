"""Deterministic demonstration scoring engine for the assessment P0 API.

The engine converts submitted laboratory values to canonical units, applies a
SMAF-style scoring curve set, and produces the structured analysis payload used
by the health-research UI. The rule set is a research-preview demonstration
parameterisation: it is deliberately conservative (no fertilizer doses, no
validated health grades) and must not be presented as an accepted model.
"""
from __future__ import annotations

from ..scientific.research_store import now, uid

DICTIONARY_VERSION = "0.2.0"

INDICATORS = [
    {"code": "soil_ph", "name": "酸碱度 pH", "units": [], "unit_required": False, "short": "pH"},
    {"code": "EC", "name": "电导率 EC", "units": ["dS/m", "μS/cm"], "unit_required": True, "short": "EC"},
    {"code": "TN", "name": "全氮 TN", "units": ["g/kg", "%"], "unit_required": True, "short": "TN"},
    {"code": "AN", "name": "碱解氮 AN", "units": ["mg/kg"], "unit_required": True, "short": "AN"},
    {"code": "AP", "name": "有效磷 AP", "units": ["mg/kg"], "unit_required": True, "short": "AP"},
    {"code": "AK", "name": "速效钾 AK", "units": ["mg/kg"], "unit_required": True, "short": "AK"},
    {"code": "cec", "name": "阳离子交换量 CEC", "units": ["cmol/kg"], "unit_required": True, "short": "CEC"},
    {"code": "BD", "name": "土壤容重 BD", "units": ["g/cm³", "kg/m³"], "unit_required": True, "short": "BD"},
    {"code": "SOC", "name": "有机碳 SOC", "units": ["g/kg", "%"], "unit_required": True, "short": "SOC"},
    {"code": "SOM", "name": "有机质 SOM", "units": ["g/kg", "%"], "unit_required": True, "short": "SOM"},
    {"code": "Sand", "name": "砂粒含量", "units": ["%"], "unit_required": True, "short": "Sand"},
    {"code": "Clay", "name": "黏粒含量", "units": ["%"], "unit_required": True, "short": "Clay"},
]
INDICATOR_MAP = {item["code"]: item for item in INDICATORS}

RECOMMENDED = ["soil_ph", "SOC", "TN", "AP", "AK", "cec", "BD"]
VALIDATED = {"soil_ph", "SOC", "TN", "cec", "BD", "Clay"}

PH_OPTIMUM = {
    "水稻": (5.5, 6.5),
    "玉米": (6.0, 7.2),
    "小麦": (6.0, 7.5),
    "大豆": (6.0, 7.0),
}
DEFAULT_PH = (5.8, 7.0)


def _curve(kind, *points):
    return {"kind": kind, "points": points}


CURVES = {
    "EC": _curve("down", 0.2, 2.0),
    "TN": _curve("up", 0.5, 2.5),
    "AN": _curve("up", 30, 150),
    "AP": _curve("up", 5, 45),
    "AK": _curve("up", 40, 180),
    "cec": _curve("up", 5, 25),
    "BD": _curve("down", 1.1, 1.6),
    "SOC": _curve("up", 8, 25),
    "Clay": _curve("opt", 10, 15, 35, 50),
    "Sand": _curve("opt", 15, 25, 60, 80),
}

# Function-level indicator weights. Only measured indicators are normalised in.
FUNCTIONS = [
    {"id": "production", "label": "生产支持", "weights": {"SOC": 0.30, "TN": 0.25, "soil_ph": 0.20, "BD": 0.15, "AN": 0.10}},
    {"id": "nutrition", "label": "养分供给", "weights": {"TN": 0.22, "SOC": 0.18, "cec": 0.16, "AP": 0.18, "AK": 0.14, "AN": 0.12}},
    {"id": "structure", "label": "土壤结构", "weights": {"BD": 0.40, "Clay": 0.30, "Sand": 0.15, "SOC": 0.15}},
    {"id": "water", "label": "水分调节", "weights": {"Clay": 0.30, "Sand": 0.20, "BD": 0.30, "SOC": 0.20}},
]
FUNCTION_WEIGHTS = {"production": 0.30, "nutrition": 0.30, "structure": 0.20, "water": 0.20}

CAUSES = {
    "soil_ph": ["长期施用生理酸性肥料", "有机质不足导致缓冲能力下降", "灌溉水质或母质影响"],
    "TN": ["有机质矿化不足", "氮肥投入与作物需求不匹配", "反硝化或淋溶损失"],
    "SOC": ["有机物料投入不足", "秸秆移除或焚烧", "耕作扰动加速矿化"],
    "cec": ["黏粒与有机质含量偏低", "长期酸化导致交换位点减少", "质地偏砂"],
    "BD": ["机械压实", "有机质下降导致结构变差", "耕作层变浅"],
    "AP": ["磷肥投入不足或固定强", "土壤 pH 不适宜导致有效性下降", "径流与侵蚀损失"],
    "AK": ["钾肥投入不足", "黏粒与 CEC 偏低导致保钾能力差", "作物带走量高"],
    "EC": ["灌溉水盐分偏高", "蒸发浓缩", "排水不畅"],
    "AN": ["有机氮矿化速率低", "微生物活性受限", "采样与保存影响"],
    "Clay": ["成土母质差异", "侵蚀导致细颗粒流失", "长期耕作改变质地"],
    "Sand": ["成土母质差异", "细颗粒流失", "人为掺砂"],
}
ACTIONS = {
    "soil_ph": ("核对并调整酸化趋势", "结合土壤缓冲能力与轮作制度评估石灰类物料需求，需农技人员现场确认。", ["先复测 pH 与缓冲能力", "结合灌溉水质与轮作制度"], "复测 pH 与交换性酸"),
    "TN": ("核对氮素投入与损失", "结合前茬、目标产量与氮素平衡核算调整投入结构。", ["需有氮肥投入记录", "结合速效氮/矿化数据"], "复测全氮与碱解氮"),
    "SOC": ("提升有机物料投入", "通过秸秆还田、有机肥或轮作等方式提升有机碳，需结合机械与轮作条件。", ["先核对有机碳检测方法", "结合秸秆去向与轮作制度"], "复测有机碳与容重"),
    "cec": ("提升保肥能力", "通过有机物料与黏粒改良提升保肥能力，需结合质地与成本评估。", ["先核对 CEC 检测方法", "结合质地与有机质"], "复测 CEC 与有机质"),
    "BD": ("改善土壤结构", "评估深松、轮作与机械作业对压实的影响，需结合耕作层厚度。", ["先确认采样深度与含水状态", "结合机械作业记录"], "复测容重与入渗"),
    "AP": ("核对磷素供应", "结合土壤磷固定特征与轮作需求调整磷素管理，不提供具体用量。", ["先确认 Olsen 或 Bray 方法", "结合 pH 与钙镁含量"], "复测有效磷"),
    "AK": ("核对钾素供应", "结合 CEC 与作物带走量评估钾素管理，不提供具体用量。", ["先确认检测方法", "结合 CEC 与产量记录"], "复测速效钾"),
    "EC": ("核查盐分与排水", "结合灌溉水、排水条件与盐分离子判断盐分风险。", ["需补测盐分离子", "结合灌溉水质"], "复测 EC 与盐分离子"),
    "AN": ("补充氮素有效性证据", "碱解氮只反映短期供应潜力，需结合矿化培养判断。", ["采样与保存条件需记录"], "补测碱解氮或矿化培养"),
    "Clay": ("核对质地与结构", "结合质地三角图与结构观测判断限制。", ["需核对检测方法"], "复测质地与容重"),
    "Sand": ("核对质地与结构", "结合质地三角图与结构观测判断限制。", ["需核对检测方法"], "复测质地与容重"),
}


def _round(value, digits=1):
    return round(float(value) + 0.0, digits)


def _clamp(value):
    return max(0.0, min(100.0, float(value)))


def canonical_value(code, value, unit):
    """Convert a submitted value to the canonical unit used by the curves."""
    unit = (unit or "").strip()
    if code in ("TN", "SOC", "SOM"):
        if unit == "%":
            return float(value) * 10.0
        return float(value)
    if code == "EC" and unit == "μS/cm":
        return float(value) / 1000.0
    if code == "BD" and unit == "kg/m³":
        return float(value) / 1000.0
    return float(value)


def score_curve(code, value, crop_name=None):
    if code == "soil_ph":
        low, high = PH_OPTIMUM.get((crop_name or "").strip(), DEFAULT_PH)
        curve = {"kind": "opt", "points": (4.0, low, high, 8.5)}
    else:
        curve = CURVES.get(code)
        if not curve:
            return None
    kind, points = curve["kind"], curve["points"]
    if kind == "up":
        low, high = points
        return _clamp((value - low) / (high - low) * 100.0)
    if kind == "down":
        low, high = points
        return _clamp((high - value) / (high - low) * 100.0)
    low, opt_low, opt_high, high = points
    if value < opt_low:
        return _clamp((value - low) / (opt_low - low) * 100.0)
    if value > opt_high:
        return _clamp((high - value) / (high - opt_high) * 100.0)
    return 100.0


def _canonical_measurements(values):
    measured = {}
    notes = []
    for item in values:
        code = item.get("indicator_code")
        if code not in INDICATOR_MAP:
            continue
        value = item.get("value")
        if value is None:
            continue
        try:
            canonical = canonical_value(code, value, item.get("unit"))
        except (TypeError, ValueError):
            continue
        measured[code] = {
            "code": code,
            "name": INDICATOR_MAP[code]["name"],
            "raw": value,
            "unit": item.get("unit") or "",
            "method": item.get("method") or "",
            "canonical": canonical,
        }
        if code == "SOM" and "SOC" not in measured:
            measured["SOC"] = {
                "code": "SOC",
                "name": "有机碳 SOC（由有机质换算）",
                "raw": value,
                "unit": item.get("unit") or "",
                "method": item.get("method") or "",
                "canonical": canonical / 1.724,
                "derived": True,
            }
            notes.append("SOC 由 SOM ÷ 1.724 换算，建议直接测定有机碳。")
    return measured, notes


def _evidence(measurement_id, item):
    method = f"；方法：{item['method']}" if item.get("method") else ""
    return {
        "label": f"{item['name']} {item['raw']} {item['unit'] or '无量纲'}{method}",
        "source_id": measurement_id,
        "source_type": "measurement",
    }


def _status_for(code, score):
    if code not in VALIDATED:
        return "descriptive_only"
    if score >= 78:
        return "within_reference"
    if score >= 62:
        return "uncertain"
    return "needs_attention"


def _indicator_explanation(item, score, status):
    value_text = f"{item['raw']} {item['unit'] or '无量纲'}"
    if status == "within_reference":
        return f"{item['name']} 为 {value_text}，按演示规则换算得分约 {score:.0f}，处于参考区间内。"
    if status == "uncertain":
        return f"{item['name']} 为 {value_text}，得分约 {score:.0f}，接近参考区间下限，需结合地块背景与方法核实。"
    if status == "needs_attention":
        return f"{item['name']} 为 {value_text}，得分约 {score:.0f}，低于参考区间，建议列为优先核查项。"
    return f"{item['name']} 为 {value_text}，按演示曲线折算为 {score:.0f} 分；该指标尚无经过验证的独立判读阈值，仅作描述。"


def build_analysis(session, measurement):
    values = measurement.get("values") or []
    measured, conversion_notes = _canonical_measurements(values)
    measurement_id = measurement["id"]
    crop = session.get("crop_name") or ""

    indicator_assessments = []
    scored = {}
    for item in measured.values():
        score = score_curve(item["code"], item["canonical"], crop)
        if score is None:
            continue
        scored[item["code"]] = score
        status = _status_for(item["code"], score)
        indicator_assessments.append({
            "indicator_code": item["code"],
            "status": status,
            "score": _round(score),
            "explanation": _indicator_explanation(item, score, status),
            "evidence": [_evidence(measurement_id, item)],
        })

    function_scores = {}
    for function in FUNCTIONS:
        total = 0.0
        weight = 0.0
        for code, part in function["weights"].items():
            if code in scored:
                total += scored[code] * part
                weight += part
        if weight:
            function_scores[function["id"]] = {
                "label": function["label"],
                "score": _round(total / weight),
            }

    composite = None
    if len(scored) >= 3 and len(function_scores) >= 2:
        total = 0.0
        weight = 0.0
        for function_id, part in FUNCTION_WEIGHTS.items():
            if function_id in function_scores:
                total += function_scores[function_id]["score"] * part
                weight += part
        composite = _round(total / weight)

    measured_codes = list(measured.keys())
    missing_codes = [code for code in RECOMMENDED if code not in measured_codes]
    extra_codes = [code for code in measured_codes if code not in RECOMMENDED]
    recommended_hit = all(code in measured_codes for code in RECOMMENDED)
    if len(measured_codes) == 1:
        scope = "single_indicator"
    elif recommended_hit:
        scope = "recommended_set"
    else:
        scope = "partial_indicators"

    low = [item for item in indicator_assessments if item["status"] == "needs_attention"]
    uncertain = [item for item in indicator_assessments if item["status"] == "uncertain"]
    if composite is None:
        summary = f"本次共 {len(measured_codes)} 项有效检测记录，暂不形成综合分数，仅作指标级描述与证据缺口说明。"
        score_explanation = "综合分数需要至少 3 项有效指标并覆盖 2 个以上土壤功能；当前证据不足，不做外推，也不把缺失项当作零值。"
    else:
        grade = "较好" if composite >= 80 else ("中等" if composite >= 65 else "偏低")
        if low:
            summary = (f"已对 {len(measured_codes)} 项检测记录完成评价：综合处于“{grade}”区间"
                       f"（综合分值 {composite:.0f}），{len(low)} 项指标需优先核查，{len(uncertain)} 项待核实。")
        else:
            summary = (f"已对 {len(measured_codes)} 项检测记录完成评价：综合处于“{grade}”区间"
                       f"（综合分值 {composite:.0f}），本次未触发优先核查项，{len(uncertain)} 项指标待核实。")
        score_explanation = ("综合分由生产支持、养分供给、土壤结构、水分调节四项功能加权得到；"
                             "缺测指标不按零值处理，也不参与外推。")

    problems = []
    problem_codes = []
    for item in low + uncertain:
        code = item["indicator_code"]
        raw_item = measured[code]
        problem_codes.append(code)
        problems.append({
            "id": uid("apr"),
            "title": f"{raw_item['name']}{'低于参考区间' if item['status'] == 'needs_attention' else '接近参考区间下限'}",
            "observation": item["explanation"],
            "possible_causes": CAUSES.get(code, []),
            "verification_needed": [
                "核对采样深度、采样时间与检测方法",
                "结合地块背景（作物、轮作、投入记录）判断",
            ],
            "evidence": item["evidence"],
            "priority": "high" if item["status"] == "needs_attention" else "medium",
        })

    decisions = []
    for code, problem in zip(problem_codes, problems):
        action, reason, conditions, goal = ACTIONS.get(code, ("核对原始记录并补测", "需要更多证据判断该指标的管理含义。", ["核对检测方法与采样信息"], "复测相关指标"))
        decisions.append({
            "id": uid("adc"),
            "action": action,
            "reason": reason,
            "conditions": conditions,
            "evidence": problem["evidence"],
            "verification_goal": goal,
        })
    if not decisions:
        decisions.append({
            "id": uid("adc"),
            "action": "维持当前管理并定期复测",
            "reason": "本次已测指标未触发优先核查项；单一检测记录不足以判断变化趋势。",
            "conditions": ["保持采样深度与方法一致", "记录当季投入与管理"],
            "evidence": [{"label": "本次检测记录", "source_id": measurement_id, "source_type": "measurement"}],
            "verification_goal": "下一季复测相同指标并核对可比性",
        })

    gaps = []
    for code in missing_codes:
        gaps.append(f"未测：{INDICATOR_MAP[code]['name']}（{code}），本次不参与评分。")
    if not measurement.get("sampling_date"):
        gaps.append("未填写采样日期：无法判断与季节、施肥窗口的关系。")
    no_method = [item["name"] for item in measured.values() if not item.get("method")]
    if no_method:
        gaps.append("未登记检测方法：" + "、".join(no_method[:5]) + "，与其他报告比较前需核对方法口径。")
    gaps.extend(conversion_notes)

    optional_tests = []
    for code in missing_codes:
        optional_tests.append({
            "code": code,
            "name": INDICATOR_MAP[code]["name"],
            "reason": "补齐推荐指标后可形成更完整的评价范围。",
        })

    return {
        "id": uid("ana"),
        "mode": session.get("mode") or "quick",
        "measurement_ids": [measurement_id],
        "input_snapshot": [
            {"source_type": "measurement", "source_id": measurement_id, "label": f"{item['name']} {item['raw']} {item['unit'] or '无量纲'}",
             "indicator_code": item["code"]}
            for item in measured.values()
        ],
        "coverage": {
            "recommended_codes": RECOMMENDED,
            "measured_codes": measured_codes,
            "missing_codes": missing_codes,
            "extra_codes": extra_codes,
        },
        "assessment": {
            "summary": summary,
            "scope": scope,
            "composite_score": composite,
            "score_explanation": score_explanation,
            "indicator_assessments": indicator_assessments,
            "function_scores": [
                {"id": function_id, "label": info.get("label"), "score": info.get("score")}
                for function_id, info in function_scores.items()
            ],
        },
        "problems": problems,
        "decisions": decisions,
        "gaps": gaps,
        "optional_tests": optional_tests,
        "next_plan_id": None,
        "model_info": {
            "model_name": "Soilmate 研究评价引擎",
            "model_version": "0.2.0",
            "is_fine_tuned": False,
            "rule_version": "SMAF-style-v0.2",
        },
        "limitations": [
            "评价规则版本 SMAF-style-v0.2；不同规则参数会带来分数差异。",
            "检测方法、采样深度与时间差异会影响跨报告比较，比较前需核对检测口径。",
            "单次检测不用于判断变化趋势，建议按同一深度与方法复测。",
            "结果供土壤健康研究与田间管理参考；本报告不含施肥剂量，田间措施需结合现场条件与农技人员复核。",
        ],
        "created_at": now(),
    }
