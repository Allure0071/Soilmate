"""Build a compact evidence chain for an assessment result.

The chain is intentionally structured rather than prose: every step points to
the measurement record, indicator judgement, function score, rule version or
boundary that supports a result. It is reused by the assessment API and by the
research assistant so the sidebar can show the same evidence as the report.
"""
from __future__ import annotations

from . import engine

STATUS_LABELS = {
    "within_reference": "参考范围内",
    "uncertain": "待核实",
    "needs_attention": "需关注",
    "descriptive_only": "仅作描述",
}


def _format_value(value, unit):
    if value is None:
        return "—"
    text = f"{value:g}" if isinstance(value, float) else str(value)
    return f"{text} {unit}" if unit else text


def build_evidence_chain(analysis, measurement, session=None, task_id=""):
    """Return an ordered chain of evidence nodes for a completed analysis."""
    if not analysis or not measurement:
        return []
    assessment = analysis.get("assessment") or {}
    values = {item.get("indicator_code"): item for item in (measurement.get("values") or [])}
    sample = measurement.get("sample_alias") or "未命名样本"
    sampled_at = measurement.get("sampling_date") or "未填写采样日期"
    measurement_id = measurement.get("id") or ""
    chain = []

    chain.append({
        "step": 1,
        "kind": "sample",
        "title": "样本与检测记录",
        "summary": f"{sample} · {sampled_at} · 检测记录 {measurement_id}",
        "items": [{
            "label": f"{sample}（{sampled_at}）",
            "detail": f"共 {len(values)} 项检测值，检测方法随记录保存",
            "source_id": measurement_id,
        }],
    })

    indicator_items = []
    for item in assessment.get("indicator_assessments") or []:
        code = item.get("indicator_code") or ""
        raw = values.get(code) or {}
        meta = engine.INDICATOR_MAP.get(code, {})
        name = meta.get("name") or raw.get("name") or code
        status = STATUS_LABELS.get(item.get("status"), item.get("status") or "未标注")
        method = raw.get("method") or "检测方法未登记"
        score = item.get("score")
        indicator_items.append({
            "label": f"{name} {_format_value(raw.get('value'), raw.get('unit'))}",
            "detail": f"{method} · 指标得分 {score if score is not None else '—'} · {status}",
            "status": item.get("status"),
            "source_id": measurement_id,
        })
    chain.append({
        "step": 2,
        "kind": "indicator",
        "title": "指标判读",
        "summary": f"{len(indicator_items)} 项指标完成判读；缺测指标不按零分处理",
        "items": indicator_items,
    })

    function_scores = assessment.get("function_scores") or []
    if not function_scores:
        scored = {item.get("indicator_code"): item.get("score") for item in (assessment.get("indicator_assessments") or [])}
        for function in engine.FUNCTIONS:
            total = 0.0
            weight = 0.0
            for code, part in function.get("weights", {}).items():
                score = scored.get(code)
                if score is None:
                    continue
                total += score * part
                weight += part
            if weight:
                function_scores.append({"id": function["id"], "label": function["label"], "score": round(total / weight, 1)})
    function_items = [
        {"label": item.get("label") or item.get("id"), "detail": f"功能得分 {item.get('score')}"}
        for item in function_scores
    ]
    composite = assessment.get("composite_score")
    if composite is None:
        score_summary = assessment.get("summary") or "已完成指标判读。"
    else:
        grade = "较好" if composite >= 80 else ("中等" if composite >= 65 else "偏低")
        score_summary = f"综合分 {composite} · {grade}区间"
    chain.append({
        "step": 3,
        "kind": "score",
        "title": "功能评分与综合结论",
        "summary": score_summary,
        "detail": assessment.get("score_explanation") or "",
        "items": function_items,
    })

    model = analysis.get("model_info") or {}
    rule_version = model.get("rule_version") or ""
    chain.append({
        "step": 4,
        "kind": "rule",
        "title": "评价规则与版本",
        "summary": " · ".join(part for part in [model.get("model_name"), model.get("model_version"), f"规则 {rule_version}" if rule_version else ""] if part) or "规则版本未登记",
        "items": [{"label": f"评价规则版本：{rule_version or '未登记'}", "detail": "重新分析会生成新任务，原结果保留"}],
    })

    boundary_items = [{"label": gap} for gap in (analysis.get("gaps") or [])[:4]]
    boundary_items += [{"label": limitation} for limitation in (analysis.get("limitations") or [])[:2]]
    chain.append({
        "step": 5,
        "kind": "boundary",
        "title": "边界与证据缺口",
        "summary": "缺测不等同于零值；报告保留适用范围、规则版本与证据缺口。",
        "items": boundary_items,
    })
    return chain


def evidence_refs(chain, task_id=""):
    """Compact reference list used by the assistant answer footer."""
    refs = []
    seen = set()
    for node in chain:
        if node.get("kind") != "indicator":
            continue
        for item in node.get("items") or []:
            key = item.get("label")
            if key in seen:
                continue
            seen.add(key)
            refs.append({
                "type": "measurement",
                "artifact_id": item.get("source_id") or "",
                "label": key,
            })
    if not refs:
        refs.append({"type": "assessment_task", "artifact_id": task_id, "kind": "analysis"})
    return refs
