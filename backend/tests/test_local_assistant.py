"""Local knowledge assistant fallback tests (no model service required)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.agent import local_assistant

ANALYSIS = {
    "assessment": {
        "summary": "已对 7 项检测记录完成评价：综合处于“中等”区间（综合分值 79）。",
        "composite_score": 78.8,
        "indicator_assessments": [
            {"indicator_code": "TN", "status": "uncertain"},
            {"indicator_code": "SOC", "status": "within_reference"},
        ],
    },
    "problems": [{"title": "全氮 TN接近参考区间下限", "observation": "全氮 1.8 g/kg，得分约 65。", "possible_causes": ["氮肥投入不足"]}],
    "decisions": [{"action": "核对氮素投入与损失", "reason": "结合氮素平衡核算调整投入结构。"}],
    "gaps": ["建议按同一深度复测。"],
    "limitations": ["单次检测不用于判断变化趋势。"],
}


class LocalAssistantTests(unittest.TestCase):
    def test_domain_faq(self):
        payload = local_assistant.answer("什么是最小数据集 MDS？")
        self.assertEqual(payload["answer_type"], "domain_fact")
        self.assertIn("最小数据集", payload["answer"])
        self.assertIsNone(payload["model"])

    def test_task_summary_uses_current_result(self):
        payload = local_assistant.answer("这次结果怎么样？", {"analysis": ANALYSIS, "sample": "示范地块 A-07 表层样本", "task_id": "atk_test"})
        self.assertEqual(payload["answer_type"], "task_fact")
        self.assertIn("示范地块 A-07", payload["answer"])
        self.assertIn("78.8", payload["answer"])
        self.assertEqual(payload["evidence_refs"][0]["artifact_id"], "atk_test")

    def test_task_gaps_intent(self):
        payload = local_assistant.answer("还缺少哪些证据？", {"analysis": ANALYSIS, "sample": "样本", "task_id": "atk_test"})
        self.assertIn("证据缺口", payload["answer"])
        self.assertIn("复测", payload["answer"])

    def test_unknown_question_is_clarification(self):
        payload = local_assistant.answer("今天天气怎么样")
        self.assertEqual(payload["answer_type"], "clarification")


if __name__ == "__main__":
    unittest.main()
