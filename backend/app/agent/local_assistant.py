"""Local knowledge assistant used when the fine-tuned model service is offline.

The platform's research assistant must keep working without the GPU inference
service, so this module answers from (a) the current assessment task result and
(b) a curated local knowledge base. It is deterministic, inspectable and never
invents task evidence. When the model service is configured and healthy the
API prefers the grounded model path instead.
"""
from __future__ import annotations

import re

KNOWLEDGE = [
    (
        ("土壤", "健康", "维度", "功能"),
        "平台把土壤健康拆成四项功能分别评价：生产支持（有机碳、全氮、pH、容重）、养分供给（全氮、有效磷、速效钾、CEC）、土壤结构（容重、黏粒、砂粒、有机碳）、水分调节（黏粒、砂粒、容重、有机碳）。分功能评价可以避免用一个总分掩盖关键短板。",
    ),
    (
        ("最小数据集", "mds"),
        "最小数据集（MDS）是在检测预算约束下，用尽量少的指标表征目标任务所需信息的一组指标。它需要同时考虑功能覆盖、区域差异、检测成本和稳定性；本平台用共享指标 N + 区域增补 X 的 N+X 方式给出选测清单。",
    ),
    (
        ("n+x", "选测", "筛选", "指标"),
        "N+X 选测由两部分组成：N 是跨区域共享的核心指标，保证不同地区之间可以横向比较；X 是按区域或地块补充的指标，用来补充本地关键限制信息。选择时同时考虑功能贡献、被替代的本地信息与检测成本，并在结果中记录取舍。",
    ),
    (
        ("稳健", "区间", "规则", "翻转", "敏感"),
        "稳健评分的做法是先确定各功能的评分规则集合，再在合理规则范围内传播结果：输出分数区间、等级稳定性和在全部规则下都成立的稳定短板。如果不同规则下等级发生翻转，报告会标记为敏感项，而不是给出看似精确的单一等级。",
    ),
    (
        ("证据", "引用", "来源", "可信", "依据"),
        "结果中的每条结论都带证据引用：来自哪条检测记录、使用什么方法、哪套规则版本。证据缺口和适用范围会单独列出；缺失指标不作为零值参与评分，也不会被推断补齐。报告页可以下载完整的评价报告与限制说明。",
    ),
    (
        ("地图", "soilgrids", "公开数据", "图层"),
        "地图的公开数据图层来自 ISRIC SoilGrids 2.0（250 m 区域预测值，CC BY 4.0）。可在工具栏「公开数据」切换 pH、有机碳、全氮、CEC、容重、黏粒、砂粒、粉粒；点击地图可以读取该点位的真实公开属性值。区域预测值用于背景参考，与地块实测分开使用。",
    ),
    (
        ("报告", "导出", "下载", "打印"),
        "在「报告与记录」页可以下载本次评价报告（HTML），包含结论摘要、检测记录、指标判读、建议、适用范围与限制；在浏览器中可直接打印或另存为 PDF。报告引用的是当前任务的结果，重新分析会生成新任务与新报告。",
    ),
    (
        ("录入", "检测", "单位", "采样"),
        "检测录入需要每项指标提供数值、报告单位与检测方法；平台会统一单位口径后再评价。至少一项有效实测即可开始，缺失的推荐指标会进入证据缺口与补测建议，不影响已有证据的评价范围。",
    ),
    (
        ("深度", "地块", "周期"),
        "深度分析在快速试用的基础上关联地块与种植周期，便于按同一地块、同一土层比较多次采样。提交后可以查看评价结果、依据版本与报告。",
    ),
]

TASK_INTENTS = [
    (("缺少", "缺口", "证据", "补测"), "gaps"),
    (("建议", "管理", "措施", "怎么办", "如何"), "decisions"),
    (("为什么", "原因", "限制", "短板", "问题"), "problems"),
    (("分数", "结果", "评价", "怎么样", "结论", "怎么样"), "summary"),
    (("指标", "判读", "单项"), "indicators"),
]


def _tokens(text):
    text = (text or "").lower()
    raw = re.findall(r"[a-z0-9+#]+|[\u4e00-\u9fff]+", text)
    terms = []
    for token in raw:
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            terms.extend(token[i:i + 2] for i in range(len(token) - 1))
        else:
            terms.append(token)
    return terms


def _knowledge_match(query):
    terms = set(_tokens(query))
    best = None
    best_score = 0
    for keywords, answer in KNOWLEDGE:
        score = sum(1 for keyword in keywords if keyword in terms or keyword in (query or "").lower())
        if score > best_score:
            best, best_score = answer, score
    return best


def _indicator_lines(analysis):
    lines = []
    for item in analysis.get("assessment", {}).get("indicator_assessments", [])[:8]:
        status = {
            "needs_attention": "需关注",
            "within_reference": "在参考范围内",
            "uncertain": "待核实",
            "descriptive_only": "仅作描述",
        }.get(item.get("status"), item.get("status"))
        lines.append(f"{item.get('indicator_code')}（{status}）")
    return lines


def _task_answer(query, context):
    analysis = context.get("analysis") or {}
    assessment = analysis.get("assessment") or {}
    summary = assessment.get("summary") or "本次任务已完成评价。"
    score = assessment.get("composite_score")
    score_text = f"综合分为 {score}。" if score is not None else "本次未形成综合分数。"
    problems = analysis.get("problems") or []
    decisions = analysis.get("decisions") or []
    gaps = analysis.get("gaps") or []
    limitations = analysis.get("limitations") or []
    sample = context.get("sample")
    prefix = f"当前样本：{sample}。" if sample else "当前任务："

    intent = "summary"
    for keywords, name in TASK_INTENTS:
        if any(keyword in (query or "") for keyword in keywords):
            intent = name
            break

    if intent == "gaps":
        lines = [f"{g}" for g in gaps[:5]]
        if not lines:
            lines = ["当前记录已覆盖推荐指标并登记检测方法；如需更完整判断，可按同一深度复测并补记采样与管理背景。"]
        return prefix + "本次评价的证据缺口与补测建议：", "；".join(lines), "task_fact"
    if intent == "decisions":
        lines = [f"{d.get('action')}（{d.get('reason')}）" for d in decisions[:4]]
        if not lines:
            lines = ["当前未触发需要调整的管理项；保持现有管理并按同一方法复测即可。"]
        return prefix + "建议与核对目标：", "；".join(lines), "task_fact"
    if intent == "problems":
        lines = []
        for problem in problems[:4]:
            causes = "、".join((problem.get("possible_causes") or [])[:2])
            lines.append(f"{problem.get('title')}：{problem.get('observation')}" + (f"（可能成因：{causes}）" if causes else ""))
        if not lines:
            lines = ["本次未触发优先核查项；如需进一步判断，可结合地块管理背景与复测数据。"]
        return prefix + "本次评价中的问题与待核实事项：", "；".join(lines), "task_fact"
    if intent == "indicators":
        return prefix + "本次参与判读的指标：", "、".join(_indicator_lines(analysis)) + "。", "task_fact"

    extra = []
    if problems:
        extra.append("优先核查项：" + "；".join(p.get("title") for p in problems[:2]))
    if decisions:
        extra.append("建议：" + "；".join(d.get("action") for d in decisions[:2]))
    if limitations:
        extra.append("适用范围：" + limitations[0])
    detail = " ".join(extra) if extra else "可查看「结果与分析」「依据与版本」「报告与记录」了解完整结论与依据。"
    return prefix + summary + " " + score_text, detail, "task_fact"


def answer(query, task_context=None):
    """Return an assistant payload compatible with /api/agent/expert."""
    if task_context and task_context.get("analysis"):
        lead, detail, answer_type = _task_answer(query, task_context)
        return {
            "answer": lead + "\n\n" + detail,
            "answer_type": answer_type,
            "evidence_refs": task_context.get("evidence_refs") or [{"type": "assessment_task", "artifact_id": task_context.get("task_id", ""), "kind": "analysis"}],
            "evidence_chain": task_context.get("chain") or [],
            "knowledge_refs": [],
            "uncertainty": "回答基于当前任务结果与平台知识整理；具体判断请结合原始检测记录与人工复核。",
            "model": None,
        }

    matched = _knowledge_match(query)
    if matched:
        return {
            "answer": matched,
            "answer_type": "domain_fact",
            "evidence_refs": [],
            "knowledge_refs": [{"source": "平台知识库 · 方法与数据说明"}],
            "uncertainty": "回答来自平台知识库，未关联具体地块任务。",
            "model": None,
        }

    return {
        "answer": "我可以解释土壤健康评价方法、指标判读、报告依据与地图公开数据，也可以结合当前任务结果回答。你可以问：本次结果的短板是什么？还需要补测哪些指标？报告里的依据是什么？",
        "answer_type": "clarification",
        "evidence_refs": [],
        "knowledge_refs": [],
        "uncertainty": "问题暂未匹配到知识条目。",
        "model": None,
    }
