"""SOILMATE V2 research API: persisted, source-bound, and fail-closed."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from ..scientific import unified_pipeline as mfti
from ..scientific.research_store import (SOURCE, connect, dataset, dump, initialize, many,
                                         now, one, sample, uid, unpack, digest)
from .auth import current_user_id

router = APIRouter(prefix="/api/research", tags=["Research V2"])


def db():
    initialize()
    return connect()


def require(value, name):
    if value is None:
        raise HTTPException(404, f"{name} 不存在")
    return value


class ProjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=1000)


class ImportIn(BaseModel):
    project_id: str
    kind: str
    name: str
    source_name: str
    csv_text: str
    source_type: str = "user_upload"
    data_version: str = "v1"


class AnalysisIn(BaseModel):
    sample_id: str
    module_id: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class PairIn(BaseModel):
    soil_sample_id: str
    microbe_sample_id: str
    identity_evidence: str = ""
    sampling_date: str = ""
    depth_top_cm: Optional[float] = None
    depth_bottom_cm: Optional[float] = None
    source_uri: str = ""


class RunsIn(BaseModel):
    project_id: str
    run_ids: List[str] = Field(default_factory=list)


class ReportIn(RunsIn):
    reference_run_ids: List[str] = Field(default_factory=list)


def _project(con, pid):
    return require(one(con, "SELECT * FROM projects WHERE id=? AND owner_user_id=?",
                       (pid, current_user_id())), "项目")


def _sample(con, sid):
    row = require(sample(con, sid), "样本")
    _project(con, row["project_id"])
    return row


def _run(con, rid):
    row = require(one(con, "SELECT * FROM analysis_runs WHERE id=?", (rid,)), "分析任务")
    _project(con, row["project_id"])
    row["result"] = unpack(row.pop("result_json"))
    row["config"] = unpack(row.pop("config_json"))
    return row


def _save_run(con, s, kind, status, version, config, source_sha, result):
    rid = uid("run")
    con.execute("INSERT INTO analysis_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (rid, s["project_id"], s["id"], s["dataset_id"], kind, status, version,
                 dump(config), source_sha, dump(result), now()))
    table = "assessment_results" if kind == "nshi" else "microbial_evidence"
    con.execute(f"INSERT INTO {table} VALUES(?,?,?,?,?)", (uid("result"), rid, s["id"], status, dump(result)))
    return _run(con, rid)


@router.get("/bootstrap")
def bootstrap():
    with db() as con:
        user_id = current_user_id()
        return {"projects": many(con, "SELECT * FROM projects WHERE owner_user_id=? ORDER BY created_at,id", (user_id,)),
                "datasets": many(con, """SELECT d.id,d.project_id,d.kind,d.name,d.data_version,d.source_sha256,d.status
                                      FROM datasets d JOIN projects p ON p.id=d.project_id
                                      WHERE p.owner_user_id=? ORDER BY d.created_at,d.id""", (user_id,)),
                "schema_version": one(con, "SELECT max(version) AS version FROM schema_migrations")["version"]}


@router.post("/projects")
def create_project(payload: ProjectIn):
    with db() as con:
        pid = uid("project")
        con.execute("INSERT INTO projects(id,name,description,created_at,owner_user_id) VALUES(?,?,?,?,?)",
                    (pid, payload.name, payload.description, now(), current_user_id()))
        return _project(con, pid)


@router.get("/projects")
def projects():
    with db() as con:
        return many(con, "SELECT * FROM projects WHERE owner_user_id=? ORDER BY created_at,id", (current_user_id(),))


@router.get("/projects/{project_id}")
def project(project_id: str):
    with db() as con:
        p = _project(con, project_id)
        p["datasets"] = many(con, "SELECT id,kind,name,data_version,source_sha256,status FROM datasets WHERE project_id=?", (project_id,))
        p["sample_counts"] = many(con, "SELECT kind,count(*) AS n FROM samples WHERE project_id=? GROUP BY kind", (project_id,))
        return p


@router.get("/datasets")
def datasets(project_id: str):
    with db() as con:
        _project(con, project_id)
        return [dataset(con, row["id"]) for row in many(con, "SELECT id FROM datasets WHERE project_id=? ORDER BY created_at", (project_id,))]


@router.post("/datasets/import")
def import_dataset(payload: ImportIn):
    if payload.kind not in ("soil", "microbiome"):
        raise HTTPException(400, "kind 仅支持 soil 或 microbiome")
    if len(payload.csv_text.encode("utf-8")) > 2_000_000:
        raise HTTPException(413, "CSV 超过 2 MB 上限")
    if payload.source_type != "user_upload":
        raise HTTPException(400, "用户导入数据必须标记 user_upload")
    rows = list(csv.DictReader(io.StringIO(payload.csv_text)))
    key = "soil_sample_id" if payload.kind == "soil" else "sample_alias"
    if not rows or key not in rows[0] or any(not row.get(key, "").strip() for row in rows):
        raise HTTPException(400, f"CSV 必须包含非空 {key}")
    ids = [r[key].strip() for r in rows]
    if len(ids) != len(set(ids)):
        raise HTTPException(400, "样本身份重复")
    with db() as con:
        _project(con, payload.project_id)
        did = uid("dataset")
        sha = hashlib.sha256(payload.csv_text.encode("utf-8")).hexdigest()
        stored_source = SOURCE.parent / "research_uploads" / f"{did}.csv"
        stored_source.parent.mkdir(parents=True, exist_ok=True)
        stored_source.write_text(payload.csv_text, encoding="utf-8")
        con.execute("INSERT INTO datasets VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (did, payload.project_id, payload.kind, payload.name, str(stored_source), sha,
                     payload.data_version, "imported_unverified", dump({"rows": len(rows), "source_type": "user_upload"}), now()))
        for row in rows:
            con.execute("INSERT INTO samples VALUES(?,?,?,?,?,?,?)",
                        (uid("sample"), payload.project_id, did, payload.kind, row[key].strip(), dump(row), now()))
        return {"dataset_id": did, "rows": len(rows), "sha256": sha, "status": "imported_unverified"}


@router.get("/samples")
def samples(project_id: str, kind: Optional[str] = None, limit: int = 100):
    if limit < 1 or limit > 500:
        raise HTTPException(400, "limit 范围 1–500")
    with db() as con:
        _project(con, project_id)
        query = "SELECT id FROM samples WHERE project_id=?"
        args = [project_id]
        if kind:
            query += " AND kind=?"
            args.append(kind)
        query += " ORDER BY external_id LIMIT ?"
        args.append(limit)
        return [sample(con, r["id"]) for r in many(con, query, args)]


@router.post("/pairings/audit")
def audit_pairing(payload: PairIn):
    with db() as con:
        soil = _sample(con, payload.soil_sample_id)
        microbe = _sample(con, payload.microbe_sample_id)
        if soil["kind"] != "soil" or microbe["kind"] != "microbiome":
            raise HTTPException(400, "样本类型不符")
        gaps = []
        if soil["project_id"] != microbe["project_id"]:
            gaps.append("不同研究项目，禁止跨项目样本级关联")
        if not payload.identity_evidence or not payload.source_uri:
            gaps.append("缺独立身份及来源证据")
        soil_date = soil["metadata"].get("sampling_date")
        microbe_date = microbe["metadata"].get("sampling_date")
        if not soil_date or not microbe_date or soil_date != microbe_date or payload.sampling_date != soil_date:
            gaps.append("采样日期未由双方源记录独立核对")
        for key in ("depth_top_cm", "depth_bottom_cm"):
            a, b, claimed = soil["metadata"].get(key), microbe["metadata"].get(key), getattr(payload, key)
            if a in (None, "") or b in (None, "") or str(a) != str(b) or claimed is None or float(a) != claimed:
                gaps.append(f"{key} 土层未由双方源记录独立核对")
        # A self-declared form cannot authorize scientific pairing without an independent review workflow.
        status = "rejected" if soil["project_id"] != microbe["project_id"] else "pending_independent_review"
        pid = uid("pair")
        con.execute("INSERT INTO sample_pairings VALUES(?,?,?,?,?,?,?,?)",
                    (pid, soil["project_id"], soil["id"], microbe["id"], status,
                     dump(payload.model_dump()), "; ".join(gaps) or "字段一致；仍需独立研究人员复核原始记录", now()))
        return {"id": pid, "status": status, "joint_analysis_allowed": False,
                "gaps": gaps or ["等待独立研究人员复核原始记录"]}


@router.get("/pairings")
def pairings(project_id: str):
    with db() as con:
        _project(con, project_id)
        return many(con, "SELECT * FROM sample_pairings WHERE project_id=? ORDER BY created_at DESC", (project_id,))


@router.post("/joint/run")
def joint_run(payload: PairIn):
    with db() as con:
        _sample(con, payload.soil_sample_id)
        _sample(con, payload.microbe_sample_id)
        pair = one(con, "SELECT * FROM sample_pairings WHERE soil_sample_id=? AND microbe_sample_id=? AND status='verified'",
                   (payload.soil_sample_id, payload.microbe_sample_id))
        if not pair:
            raise HTTPException(409, "没有独立核验的样本配对；禁止地块级联合分析")
        raise HTTPException(501, "配对通过后的联合模型仍需独立验证")


def _outliers(rows, key):
    values = sorted(float(r[key]) for r in rows if r.get(key) not in (None, ""))
    if len(values) < 4:
        return 0
    q1, q3 = values[len(values)//4], values[(3*len(values))//4]
    return sum(x < q1-1.5*(q3-q1) or x > q3+1.5*(q3-q1) for x in values)


def _local_nshi(con, s):
    records = [unpack(r["metadata_json"]) for r in many(con, "SELECT metadata_json FROM samples WHERE dataset_id=?", (s["dataset_id"],))]
    audit = mfti.indicator_audit(records)
    raw = s["metadata"]
    keys = ["TN_raw_percent", "AN_raw_mgkg", "CEC_raw_cmolkg", "BD_raw_gcm3"]
    quality = {k: {"missing_fraction": round(sum(not r.get(k) for r in records)/len(records), 4),
                   "iqr_outlier_count": _outliers(records, k), "unit": k.rsplit("_", 1)[-1]}
               for k in keys}
    return {"assessment_state": "insufficient_data", "nshi_score": None, "health_class": None,
            "raw_data": {k: raw.get(k) for k in keys}, "data_quality": quality,
            "tds": keys, "mds": audit,
            "selection_reason": "74 样本 Spearman 冗余阈值 |ρ|≥0.85 与固定种子 100 次 Bootstrap；仅探索性基线",
            "dimensions": {"nitrogen_supply_relative": raw.get("nitrogen_supply_relative"),
                           "nitrogen_retention_relative": raw.get("nitrogen_retention_relative"),
                           "biological_transformation": None},
            "gaps": ["缺生物转化维度实测值", "缺独立参照阈值与区域效度验证", "样本身份/时间/土层未满足跨组学配对"],
            "risk": "不能给出健康等级或氮损失风险", "algorithm_source": "soilmate_unified_20261019/run_pipeline.py::indicator_audit"}


def _generic_nshi(con, s, config):
    import pandas as pd
    from ..scientific import nshi_prototype_v12 as nshi
    rows = [unpack(r["metadata_json"]) for r in many(con, "SELECT metadata_json FROM samples WHERE dataset_id=?", (s["dataset_id"],))]
    frame = pd.DataFrame(rows)
    dimensions = config.get("dimensions", nshi.DEFAULT_DIMENSIONS)
    audit = nshi.soil_audit(frame, dimensions, min_sample=200)
    raw = s["metadata"]
    out = {"assessment_state": "raw_data", "raw_data": raw, "audit": audit,
           "tds": list(dict.fromkeys(sum(dimensions.values(), []))), "mds": None,
           "dimensions": {}, "nshi_score": None, "health_class": None,
           "gaps": [], "algorithm_source": "N-SHI-prototype-1.2::soil_audit/select_mds/score_soil"}
    if not audit["required_metadata_complete"] or audit["duplicate_sample_keys"] or not audit["dimensions_complete"]:
        out["assessment_state"] = "insufficient_data"
        out["gaps"] = ["身份元数据、样本唯一性或三维指标不完整；拒绝综合评分"]
        return out
    selected = nshi.select_mds(frame, audit, dimensions, n_boot=20)
    out["mds"] = selected
    rules = config.get("score_rules", {})
    if not rules:
        out["assessment_state"] = "insufficient_data"
        out["gaps"] = ["评分方向和参照阈值未核验；拒绝综合评分"]
        return out
    scores, status = nshi.score_soil(frame, selected, {"score_rules": rules}, audit)
    if scores is None:
        out["assessment_state"] = "insufficient_data"
        out["gaps"] = [status]
        return out
    match = scores.loc[frame["soil_sample_id"].astype(str) == s["external_id"]]
    out["assessment_state"] = "exploratory_assessment"
    out["nshi_score"] = float(match.iloc[0]["n_shi_score"]) if len(match) and pd.notna(match.iloc[0]["n_shi_score"]) else None
    out["dimensions"] = {k: float(match.iloc[0][k]) if len(match) and pd.notna(match.iloc[0][k]) else None
                         for k in ("nitrogen_supply", "biological_transformation", "nitrogen_retention")}
    out["score_status"] = status
    out["gaps"] = ["相对探索性评分未经过独立阈值或功能验证，不是健康真值"]
    return out


@router.post("/analyses/nshi")
def run_nshi(payload: AnalysisIn):
    with db() as con:
        s = _sample(con, payload.sample_id)
        if s["kind"] != "soil":
            raise HTTPException(400, "N-SHI 需要土壤样本")
        ds = dataset(con, s["dataset_id"])
        result = _local_nshi(con, s) if ds["id"] == "local-soil-74-v06" else _generic_nshi(con, s, payload.config)
        result["source"] = {"dataset_id": ds["id"], "sha256": ds["source_sha256"], "version": ds["data_version"],
                            "source_uri": ds["source_uri"]}
        result["sample_id"] = s["id"]
        return _save_run(con, s, "nshi", result["assessment_state"], "N-SHI-prototype-1.2 + audit-v2",
                         payload.config, ds["source_sha256"], result)


@lru_cache(maxsize=1)
def _public_evidence():
    return {(row["sample_alias"], row["module_id"]): row for row in mfti.public_branch()}


@router.post("/analyses/mfti")
def run_mfti(payload: AnalysisIn):
    if payload.module_id not in ("M00528", "M00529", "M00530"):
        raise HTTPException(400, "仅支持已登记的 3 个 KEGG 模块")
    with db() as con:
        s = _sample(con, payload.sample_id)
        if s["kind"] != "microbiome":
            raise HTTPException(400, "MFTI 需要微生物样本")
        ds = dataset(con, s["dataset_id"])
        if ds["id"] != "public-ko-70-figshare":
            result = {"mfti_evidence_status": "insufficient_data", "gaps": ["新导入样本没有接入 KO×Sample 原始矩阵及注释版本"],
                      "sample_id": s["id"], "module_id": payload.module_id, "pairing_status": "unverified"}
        else:
            row = require(_public_evidence().get((s["external_id"], payload.module_id)), "KO 分析结果")
            result = dict(row)
            result["sample_id"] = s["id"]
            result["pairing_status"] = "not_paired_with_local_soil"
            result["detection_condition"] = "检测条件尚未充分核验；未计算校准概率"
            result["gaps"] = ["同一 Run FASTQ 质量与有效 reads 未核验", "注释版本/质量与独立功能真值待复核", "无本地土壤样本配对"]
            result["algorithm_source"] = "soilmate_unified_20261019/run_pipeline.py::public_branch"
        result["source"] = {"dataset_id": ds["id"], "manifest_sha256": ds["source_sha256"],
                            "ko_sha256": digest(SOURCE / "ko_counts_by_sample.csv.gz") if ds["id"] == "public-ko-70-figshare" else None,
                            "version": ds["data_version"], "source_uri": ds["source_uri"]}
        return _save_run(con, s, "mfti", result["mfti_evidence_status"], "MFTI-structure-v2",
                         {"module_id": payload.module_id}, ds["source_sha256"], result)


@router.get("/runs")
def runs(project_id: str, limit: int = 50):
    with db() as con:
        _project(con, project_id)
        return many(con, "SELECT id,project_id,sample_id,dataset_id,kind,status,algorithm_version,source_sha256,created_at FROM analysis_runs WHERE project_id=? ORDER BY created_at DESC,id DESC LIMIT ?",
                    (project_id, min(max(limit, 1), 200)))


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    with db() as con:
        return _run(con, run_id)


def _plan(run):
    result = run["result"]
    gaps = result.get("gaps", [])
    if run["kind"] == "mfti":
        actions = [("CHECK_QC", "blocked_input", 5, 2, 1, "需要同一 Run 的质控和有效测序深度"),
                   ("CHECK_PATHWAY", "computable", 3, 1, 0, "复核已登记 KO 通路关键步骤"),
                   ("VERIFY_PAIRING", "human_review", 2, 3, 1, "核验土壤与微生物样本来源"),
                   ("LAB_VALIDATION", "laboratory", 2, 5, 2, "实验室验证过程活性")]
    else:
        actions = [("BIO_ASSAY", "laboratory", 5, 5, 1, "测定缺失的生物转化维度"),
                   ("VERIFY_UNITS", "human_review", 4, 1, 0, "核对指标单位与参照阈值"),
                   ("VERIFY_PAIRING", "human_review", 2, 3, 1, "核对样本身份、时间和土层")]
    ranked = [{"code": code, "class": cls, "benefit": benefit, "cost": cost, "risk": risk,
               "score": round(benefit/(cost+1)-0.25*risk, 3), "precondition": pre}
              for code, cls, benefit, cost, risk, pre in actions]
    # Missing same-run QC is a decision gate, even if a cheap structural check scores higher.
    chosen = ranked[0] if run["kind"] == "mfti" and run["status"] == "insufficient_data" else max(ranked, key=lambda x: x["score"])
    return {"chosen": chosen, "candidates": ranked, "gaps": gaps,
            "reason": f"基于持久化结果 {run['id']} 的缺口；{chosen['precondition']}。建议不等于已执行。"}


@router.post("/actions/plan")
def plan_action(payload: RunsIn):
    if not payload.run_ids:
        raise HTTPException(400, "至少指定一个分析任务")
    with db() as con:
        _project(con, payload.project_id)
        run = _run(con, payload.run_ids[-1])
        if run["project_id"] != payload.project_id:
            raise HTTPException(400, "任务不属于当前项目")
        plan = _plan(run)
        c = plan["chosen"]
        aid = uid("action")
        before = {"analysis_status": run["status"], "gaps": plan["gaps"]}
        con.execute("INSERT INTO research_actions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (aid, payload.project_id, run["id"], c["code"], c["class"], "proposed", plan["reason"],
                     dump({"candidates": plan["candidates"]}), "unknown", dump([c["precondition"]]),
                     dump(before), dump(before), dump(["规则选择；尚未执行"]), now(), now()))
        return {"id": aid, "run_id": run["id"], "status": "proposed", **plan}


@router.post("/actions/{action_id}/execute")
def execute_action(action_id: str):
    with db() as con:
        row = require(one(con, "SELECT * FROM research_actions WHERE id=?", (action_id,)), "行动")
        _project(con, row["project_id"])
        run = _run(con, row["run_id"])
        if row["status"] != "proposed":
            return {"id": action_id, "status": row["status"], "log": unpack(row["log_json"])}
        if row["action_class"] != "computable":
            state = {"blocked_input": "waiting_for_input", "human_review": "waiting_for_researcher",
                     "laboratory": "waiting_for_lab"}[row["action_class"]]
            message = "当前缺少前置条件；未声称工具或实验已完成"
        else:
            state = "completed"
            result = run["result"]
            message = f"已从已登记 KO 结果复核 {result.get('module_id')}：{result.get('steps_observed')}/{result.get('steps_total')} 个步骤；生物活性仍未验证"
        after = {"analysis_status": run["status"], "gaps": run["result"].get("gaps", []),
                 "note": "没有新测量进入系统，科学判断未改变"}
        con.execute("UPDATE research_actions SET status=?,after_json=?,log_json=?,updated_at=? WHERE id=?",
                    (state, dump(after), dump([message]), now(), action_id))
        return {"id": action_id, "status": state, "log": [message], "before": unpack(row["before_json"]), "after": after}


@router.get("/actions")
def actions(project_id: str):
    with db() as con:
        _project(con, project_id)
        return many(con, "SELECT * FROM research_actions WHERE project_id=? ORDER BY created_at DESC,id DESC", (project_id,))


@router.post("/reports")
def create_report(payload: ReportIn):
    with db() as con:
        p = _project(con, payload.project_id)
        ids = payload.run_ids or [r["id"] for r in many(con, "SELECT id FROM analysis_runs WHERE project_id=? ORDER BY created_at DESC LIMIT 2", (p["id"],))]
        if not ids:
            raise HTTPException(400, "当前项目还没有分析结果，不能生成研究报告")
        records = [_run(con, rid) for rid in ids]
        if any(r["project_id"] != p["id"] for r in records):
            raise HTTPException(400, "报告包含其他项目任务")
        reference = [_run(con, rid) for rid in payload.reference_run_ids]
        if any(r["project_id"] == p["id"] for r in reference):
            raise HTTPException(400, "同项目结果请列入主任务，而非独立参考案例")
        if any(r["kind"] != "mfti" for r in reference):
            raise HTTPException(400, "跨项目引用仅支持独立 MFTI 方法案例")
        number = one(con, "SELECT COALESCE(MAX(version),0)+1 AS n FROM reports WHERE project_id=?", (p["id"],))["n"]
        ds = [dataset(con, rid) for rid in dict.fromkeys(r["dataset_id"] for r in records + reference)]
        actions = many(con, "SELECT run_id,action_code,action_class,status,reason,estimated_cost,preconditions_json,log_json,after_json FROM research_actions WHERE project_id=? ORDER BY created_at", (p["id"],))
        pair = many(con, "SELECT status,review_note FROM sample_pairings WHERE project_id=?", (p["id"],))
        lines = [f"# 壤脉天玑 · Soilmate V1.1 研究报告 · v{number}", "", f"项目：{p['name']}（{p['id']}）", f"生成时间：{now()}",
                 "", "## 数据来源与版本"]
        for d in ds:
            lines.append(f"- {d['name']}；{d['data_version']}；SHA-256 {d['source_sha256']}；{d['source_uri']}")
        lines += ["", "## 样本与分析任务"]
        for r in records:
            s = sample(con, r["sample_id"])
            lines += [f"### {r['kind']} · {s['kind']}样本 {s['external_id']} · {r['id']}",
                      f"算法 {r['algorithm_version']}；状态 {r['status']}；输入 SHA-256 {r['source_sha256']}",
                      f"配置：{dump(r['config'])}", f"结果：{dump(r['result'])}", ""]
        if reference:
            lines += ["## 独立公开微生物方法案例（跨项目引用，未配对）"]
            for r in reference:
                s = sample(con, r["sample_id"])
                lines += [f"- {s['external_id']} / {r['id']}：{dump(r['result'])}",
                          "  仅用于 MFTI 方法展示，不能解释本地土壤样本。"]
            lines.append("")
        lines += ["## 配对审核", f"已核验配对：{sum(x['status']=='verified' for x in pair)}；当前没有可用于地块级联合分析的确认配对。", ""]
        lines += ["## Agent 行动与实际执行"]
        lines += [f"- 关联运行 {a['run_id']} · {a['action_code']}（{a['action_class']}）：{a['status']}；建议理由：{a['reason']}；预估成本：{a['estimated_cost']}；前置条件：{a['preconditions_json']}；执行日志：{a['log_json']}；执行后状态：{a['after_json']}" for a in actions] or ["- 尚无行动记录"]
        lines += ["", "## 证据缺口与边界", "- 缺完整生物转化维度、核验阈值和配对证据时，不生成正式 N-SHI 或地块级联合结论。",
                  "- 公开 KO 预测基因计数不是表达量、酶活或氮转化速率；同 Run QC 未核验时不输出检测概率。"]
        rid = uid("report")
        content = "\n".join(lines) + "\n"
        con.execute("INSERT INTO reports VALUES(?,?,?,?,?,?,?)", (rid, p["id"], number, content, dump(ids + payload.reference_run_ids),
                    dump([{"id": d["id"], "sha256": d["source_sha256"]} for d in ds]), now()))
        return {"id": rid, "project_id": p["id"], "version": number, "run_ids": ids,
                "reference_run_ids": payload.reference_run_ids, "content": content}


@router.get("/reports")
def reports(project_id: str):
    with db() as con:
        _project(con, project_id)
        return many(con, "SELECT id,project_id,version,run_ids_json,created_at FROM reports WHERE project_id=? ORDER BY version DESC", (project_id,))


@router.get("/reports/{report_id}")
def report(report_id: str):
    with db() as con:
        row = require(one(con, "SELECT * FROM reports WHERE id=?", (report_id,)), "报告")
        _project(con, row["project_id"])
        return row


@router.get("/reports/{report_id}/download", response_class=PlainTextResponse)
def download_report(report_id: str):
    return report(report_id)["content"]
