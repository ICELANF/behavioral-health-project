# -*- coding: utf-8 -*-
"""
L1 — 输入过滤

- 敏感词匹配 (从 configs/safety_keywords.json 加载)
- 正则规则 (手机号/身份证/药品剂量)
- 意图分类 (crisis / medical_advice / normal)
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── 预编译正则 ──

_PII_PATTERNS = {
    "phone": re.compile(r"1[3-9]\d{9}"),
    "id_card": re.compile(r"\d{17}[\dXx]"),
    "email_addr": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
}

_DOSAGE_PATTERN = re.compile(
    r"(服用|注射|口服|静脉|皮下|肌注)\s*\d+\s*(mg|ml|g|片|粒|支|iu|单位)",
    re.IGNORECASE,
)


@dataclass
class InputFilterResult:
    safe: bool
    category: str = "normal"          # normal / crisis / medical_advice / pii / blocked
    blocked_terms: list[str] = field(default_factory=list)
    pii_detected: list[str] = field(default_factory=list)  # 类型列表, 不含实际值
    severity: str = "low"             # low / medium / high / critical
    detail: str = ""


class InputFilter:
    """L1 输入安全过滤器"""

    def __init__(self, keywords_path: Optional[str] = None):
        if keywords_path is None:
            keywords_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "configs", "safety_keywords.json",
            )
        self._load_keywords(keywords_path)

    def _load_keywords(self, path: str):
        self.crisis_keywords: list[str] = []
        self.warning_keywords: list[str] = []
        self.blocked_keywords: list[str] = []
        self.medical_keywords: list[str] = []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.crisis_keywords = data.get("crisis", [])
            self.warning_keywords = data.get("warning", [])
            self.blocked_keywords = data.get("blocked", [])
            self.medical_keywords = data.get("medical_advice", [])
            logger.info("Safety keywords loaded: crisis=%d warning=%d blocked=%d medical=%d",
                        len(self.crisis_keywords), len(self.warning_keywords),
                        len(self.blocked_keywords), len(self.medical_keywords))
        except FileNotFoundError:
            logger.warning("Safety keywords file not found: %s, using defaults", path)
            # 最小默认集 (与 CrisisAgent 一致)
            self.crisis_keywords = ["自杀", "自残", "不想活", "结束生命", "去死", "跳楼", "割腕", "遗书"]
            self.warning_keywords = ["活着没意思", "太痛苦了", "撑不下去", "崩溃", "绝望"]
        except Exception as e:
            logger.error("Failed to load safety keywords: %s", e)

    def check(self, text: str) -> InputFilterResult:
        """检查输入文本安全性"""
        if not text or not text.strip():
            return InputFilterResult(safe=True)

        # 1) 危机关键词 (最高优先级)
        for kw in self.crisis_keywords:
            if kw in text:
                return InputFilterResult(
                    safe=False,
                    category="crisis",
                    blocked_terms=[kw],
                    severity="critical",
                    detail=f"检测到危机关键词: {kw}",
                )

        # 2) 屏蔽词
        found_blocked = [kw for kw in self.blocked_keywords if kw in text]
        if found_blocked:
            return InputFilterResult(
                safe=False,
                category="blocked",
                blocked_terms=found_blocked,
                severity="high",
                detail="检测到屏蔽内容",
            )

        # 3) 警告关键词
        found_warning = [kw for kw in self.warning_keywords if kw in text]

        # 4) PII 检测 (不阻断, 仅标记)
        pii_types = []
        for pii_type, pattern in _PII_PATTERNS.items():
            if pattern.search(text):
                pii_types.append(pii_type)

        # 5) 医疗建议意图
        found_medical = [kw for kw in self.medical_keywords if kw in text]
        has_dosage = bool(_DOSAGE_PATTERN.search(text))

        # 综合判断
        if found_warning:
            return InputFilterResult(
                safe=True,  # 不阻断, 但提升关注度
                category="crisis",
                blocked_terms=found_warning,
                pii_detected=pii_types,
                severity="high",
                detail="检测到心理预警关键词",
            )

        if has_dosage or found_medical:
            return InputFilterResult(
                safe=True,
                category="medical_advice",
                blocked_terms=found_medical,
                pii_detected=pii_types,
                severity="medium",
                detail="检测到医疗相关意图",
            )

        if pii_types:
            return InputFilterResult(
                safe=True,
                category="pii",
                pii_detected=pii_types,
                severity="low",
                detail=f"检测到个人信息类型: {', '.join(pii_types)}",
            )

        return InputFilterResult(safe=True, category="normal")
