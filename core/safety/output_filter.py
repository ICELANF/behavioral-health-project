# -*- coding: utf-8 -*-
"""
L4 — 输出过滤

- 医疗声明检测 (药名+剂量模式)
- 合规标注 (自动追加免责声明)
- 内容分级: safe / review_needed / blocked
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 免责声明
DISCLAIMER_ZH = "\n\n---\n*以上内容仅供健康参考, 不构成医疗建议。具体诊疗方案请咨询您的主治医生。*"

# 药品+剂量模式
_DRUG_DOSAGE = re.compile(
    r"(每[日天]|一[日天])\s*\d+\s*(次|mg|ml|g|片|粒|支|iu|单位)"
    r"|"
    r"(服用|注射|口服)\s*[\u4e00-\u9fff]+\s*\d+\s*(mg|ml|g|片|粒)"
    r"|"
    r"\d+\s*(mg|ml|g)\s*(每[日天]|/天|/日|bid|tid|qd|qid)",
    re.IGNORECASE,
)

# 绝对化声明
_ABSOLUTE_CLAIMS = re.compile(
    r"(保证|确保|肯定|一定|100%)\s*(治愈|治好|恢复|有效|成功)"
    r"|"
    r"(可以替代|无需|不用)\s*(医生|就医|看病|治疗|用药)",
)

# 诊断性声明
_DIAGNOSTIC = re.compile(
    r"(你[得患]了|诊断[为是]|确诊)\s*[\u4e00-\u9fff]{2,}"
    r"|"
    r"(根据.*症状.*判断|可以确定.*是)"
)


@dataclass
class OutputFilterResult:
    text: str                  # 处理后的文本
    grade: str = "safe"        # safe / review_needed / blocked
    annotations: list[str] = field(default_factory=list)
    disclaimer_added: bool = False
    original_text: str = ""


class OutputFilter:
    """L4 输出安全过滤器"""

    def filter(self, text: str, input_category: str = "normal") -> OutputFilterResult:
        """
        扫描 LLM 输出并进行安全处理.

        Args:
            text: LLM 生成的原始输出
            input_category: L1 输入过滤结果的 category

        Returns:
            OutputFilterResult: 处理后的结果
        """
        if not text or not text.strip():
            return OutputFilterResult(text=text, grade="safe")

        original = text
        annotations = []
        grade = "safe"

        # 1) 诊断性声明 → blocked (必须人工审核)
        if _DIAGNOSTIC.search(text):
            annotations.append("diagnostic_statement_detected")
            grade = "blocked"
            text = re.sub(
                _DIAGNOSTIC,
                "[此部分需要专业医生确认]",
                text,
            )

        # 2) 绝对化声明 → review_needed
        if _ABSOLUTE_CLAIMS.search(text):
            annotations.append("absolute_claim_detected")
            if grade == "safe":
                grade = "review_needed"
            text = re.sub(
                _ABSOLUTE_CLAIMS,
                lambda m: f"[需谨慎评估] {m.group(0)}",
                text,
            )

        # 3) 药品剂量 → review_needed
        if _DRUG_DOSAGE.search(text):
            annotations.append("drug_dosage_detected")
            if grade == "safe":
                grade = "review_needed"

        # 4) 医疗类输入 — 始终追加免责声明
        disclaimer_added = False
        if input_category in ("medical_advice", "crisis") or annotations:
            if DISCLAIMER_ZH.strip() not in text:
                text = text.rstrip() + DISCLAIMER_ZH
                disclaimer_added = True

        return OutputFilterResult(
            text=text,
            grade=grade,
            annotations=annotations,
            disclaimer_added=disclaimer_added,
            original_text=original,
        )
