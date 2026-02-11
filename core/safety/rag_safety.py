# -*- coding: utf-8 -*-
"""
L2 — RAG 安全增强

- Evidence tier 权重: T1(1.0) > T2(0.8) > T3(0.5) > T4(0.2)
- 过滤过期文档 (expires_at < now)
- 安全 scope 注入
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Evidence tier 权重
TIER_WEIGHTS = {
    "T1": 1.0,   # 系统性综述 / Meta分析
    "T2": 0.8,   # RCT / 队列研究
    "T3": 0.5,   # 观察研究 / 专家共识
    "T4": 0.2,   # 专家意见 / 个案报告
}


@dataclass
class RAGSafetyResult:
    references: list[dict] = field(default_factory=list)
    tier_distribution: dict[str, int] = field(default_factory=dict)
    filtered_count: int = 0       # 被安全过滤掉的引用数
    total_count: int = 0          # 原始引用数


class RAGSafety:
    """L2 RAG 安全增强"""

    def enhance(self, query: str, rag_results: list[dict],
                now: datetime | None = None) -> RAGSafetyResult:
        """
        对 RAG 检索结果进行安全增强:
        1. 过滤过期文档
        2. 按 evidence tier 重排序
        3. 统计 tier 分布
        """
        if now is None:
            now = datetime.utcnow()

        total = len(rag_results)
        safe_results = []
        filtered = 0

        for ref in rag_results:
            # 过期过滤
            expires_at = ref.get("expires_at")
            if expires_at:
                try:
                    if isinstance(expires_at, str):
                        exp = datetime.fromisoformat(expires_at)
                    else:
                        exp = expires_at
                    if exp < now:
                        filtered += 1
                        continue
                except (ValueError, TypeError):
                    pass

            # 获取 tier
            tier = ref.get("evidence_tier", "T4")
            if tier not in TIER_WEIGHTS:
                tier = "T4"
            ref["_safety_weight"] = TIER_WEIGHTS[tier]
            ref["_evidence_tier"] = tier
            safe_results.append(ref)

        # 按 evidence tier 权重降序排列
        safe_results.sort(key=lambda r: r.get("_safety_weight", 0), reverse=True)

        # 统计分布
        tier_dist: dict[str, int] = {}
        for ref in safe_results:
            t = ref.get("_evidence_tier", "T4")
            tier_dist[t] = tier_dist.get(t, 0) + 1

        return RAGSafetyResult(
            references=safe_results,
            tier_distribution=tier_dist,
            filtered_count=filtered,
            total_count=total,
        )
