"""Evidence-grounded Soil Expert core for Phase 4.2.

This first version is provider-neutral and deterministic. It never invents a
task conclusion: task-specific claims must be backed by readable Artifacts.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class SoilExpert:
    def __init__(self, knowledge_root: Path):
        self.knowledge_root = Path(knowledge_root).resolve()

    def _knowledge(self, query: str) -> List[Dict[str, str]]:
        raw = [t.lower() for t in re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+", query)]
        terms=[]
        for token in raw:
            if re.fullmatch(r"[\u4e00-\u9fff]+", token):
                terms.extend(token[i:i+2] for i in range(len(token)-1))
            elif len(token) >= 2:
                terms.append(token)
        hits=[]
        if not self.knowledge_root.exists(): return hits
        for path in self.knowledge_root.rglob("*.md"):
            try: text=path.read_text(encoding="utf-8")
            except (OSError, UnicodeError): continue
            score=sum(text.lower().count(t) for t in terms)
            if score: hits.append({"path":str(path),"score":str(score),"excerpt":text[:600]})
        return sorted(hits,key=lambda x:int(x["score"]),reverse=True)[:3]

    def answer(self, query: str, task_facts: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        facts = task_facts or []
        refs=[]
        for fact in facts:
            if isinstance(fact, dict) and fact.get("artifact_id"):
                refs.append({"type":"task_artifact","artifact_id":fact["artifact_id"],"kind":fact.get("kind")})
        knowledge=self._knowledge(query)
        lower=query.lower()
        asks_task=any(k in lower for k in ("本次","这次","当前","为什么没","为什么不","没有选择","最终指标"))
        if asks_task and not facts:
            return {"answer":"当前任务没有可读取的分析 Artifact，暂时不能对本次筛选原因下结论。请先完成 Data/MDS 分析或提供对应结果。","answer_type":"clarification","evidence_refs":[],"uncertainty":"missing_task_artifact","knowledge_refs":knowledge}
        if facts:
            summary=[]
            for f in facts:
                content=f.get("content",{}) if isinstance(f,dict) else {}
                if isinstance(content,dict):
                    if content.get("metadata"): summary.append(str(content["metadata"]))
                    if content.get("row_count") is not None: summary.append("数据行数="+str(content["row_count"]))
            answer="已读取当前任务 Artifact。可确认的任务事实："+"；".join(summary) if summary else "已读取当前任务 Artifact，但其中没有足够字段解释该问题。"
            return {"answer":answer,"answer_type":"task_fact","evidence_refs":refs,"uncertainty":"仅陈述 Artifact 中可见事实，未推断未记录的筛选原因。","knowledge_refs":knowledge}
        if knowledge:
            return {"answer":"这是一般土壤健康知识问题，回答应以知识库条目为依据；当前检索到相关条目。","answer_type":"domain_fact","evidence_refs":[],"uncertainty":"未关联具体分析任务。","knowledge_refs":knowledge}
        return {"answer":"目前没有足够的领域条目或当前任务证据回答这个问题。","answer_type":"clarification","evidence_refs":[],"uncertainty":"insufficient_evidence","knowledge_refs":[]}
