"""
MultiAgentCoordinator — 多Agent协调 + 冲突消解
来源: §10 多Agent协调与冲突消解

协调9步 (§10.4):
  1.分配权重 → 2.检测冲突 → 3.消解冲突 → 4.融合Findings →
  5.融合Recommendations → 6.确定综合风险等级 → 7.计算综合置信度 →
  8.提取共识/分歧 → 9.生成摘要
"""
from __future__ import annotations
from .base import (
    AgentResult, RiskLevel, ConflictType,
    AGENT_BASE_WEIGHTS, CONFLICT_PRIORITY,
)


class MultiAgentCoordinator:
    """协调多个Agent的结果, 消解冲突, 输出统一结论"""

    def __init__(self):
        # 尝试从模板缓存加载冲突优先级, 失败降级到硬编码
        self._conflict_priority = CONFLICT_PRIORITY
        try:
            from core.agent_template_service import build_conflict_priority_from_templates
            tpl_conflicts = build_conflict_priority_from_templates()
            if tpl_conflicts:
                self._conflict_priority = tpl_conflicts
        except Exception:
            pass

    def coordinate(self, results: list[AgentResult]) -> dict:
        if not results:
            return {"findings": [], "recommendations": [], "risk_level": "low",
                    "confidence": 0.0, "summary": "无Agent输出"}

        # Step 1: 分配权重
        weighted = self._assign_weights(results)

        # Step 2-3: 检测并消解冲突
        conflicts = self._detect_conflicts(results)
        resolved = self._resolve_conflicts(results, conflicts)

        # Step 4: 融合Findings
        all_findings = []
        for r in resolved:
            all_findings.extend(r.findings)

        # Step 5: 融合Recommendations (按权重排序)
        rec_scored: list[tuple[float, str]] = []
        for r in resolved:
            w = weighted.get(r.agent_domain, 0.5)
            for rec in r.recommendations:
                rec_scored.append((w * r.confidence, rec))
        rec_scored.sort(key=lambda x: -x[0])
        all_recs = [rec for _, rec in rec_scored]

        # Step 6: 综合风险等级 (取最高)
        risk_order = [RiskLevel.CRITICAL, RiskLevel.HIGH,
                      RiskLevel.MODERATE, RiskLevel.LOW]
        overall_risk = RiskLevel.LOW
        for level in risk_order:
            if any(r.risk_level == level for r in resolved):
                overall_risk = level
                break

        # Step 7: 综合置信度 (加权平均)
        total_w = sum(weighted.get(r.agent_domain, 0.5) for r in resolved)
        if total_w > 0:
            overall_conf = sum(
                weighted.get(r.agent_domain, 0.5) * r.confidence
                for r in resolved
            ) / total_w
        else:
            overall_conf = 0.5

        # Step 8: 共识与分歧
        consensus = self._extract_consensus(resolved)
        divergence = [c for c in conflicts if c["resolved"] is False]

        # Step 9: 摘要
        agents_str = ", ".join(r.agent_domain for r in resolved)
        summary = (f"综合{len(resolved)}个Agent ({agents_str}) 结论: "
                   f"风险={overall_risk.value}, 置信度={overall_conf:.2f}")

        return {
            "findings": all_findings,
            "recommendations": all_recs,
            "tasks": [t for r in resolved for t in r.tasks],
            "risk_level": overall_risk.value,
            "confidence": round(overall_conf, 3),
            "conflicts": conflicts,
            "consensus": consensus,
            "divergence": divergence,
            "summary": summary,
        }

    # ── 内部方法 ──

    def _assign_weights(self, results: list[AgentResult]) -> dict[str, float]:
        return {
            r.agent_domain: AGENT_BASE_WEIGHTS.get(r.agent_domain, 0.5) * r.confidence
            for r in results
        }

    def _detect_conflicts(self, results: list[AgentResult]) -> list[dict]:
        conflicts = []
        domains = [r.agent_domain for r in results]
        for i, a in enumerate(results):
            for b in results[i + 1:]:
                # 检查recommendation文本层面的矛盾关键词
                pair = (a.agent_domain, b.agent_domain)
                sorted_pair = tuple(sorted(pair))
                if sorted_pair in self._conflict_priority or \
                   (sorted_pair[1], sorted_pair[0]) in self._conflict_priority:
                    conflicts.append({
                        "type": ConflictType.PRIORITY.value,
                        "agents": list(pair),
                        "resolved": True,
                        "winner": self._conflict_priority.get(
                            sorted_pair,
                            self._conflict_priority.get((sorted_pair[1], sorted_pair[0]),
                                                        sorted_pair[0])
                        ),
                    })
        return conflicts

    def _resolve_conflicts(self, results: list[AgentResult],
                           conflicts: list[dict]) -> list[AgentResult]:
        """冲突消解: 保留优先方的recommendation, 去除冲突方的矛盾建议"""
        # 简化实现: 降低低优先方的confidence
        losers = set()
        for c in conflicts:
            if c.get("resolved"):
                winner = c["winner"]
                for a in c["agents"]:
                    if a != winner:
                        losers.add(a)

        resolved = []
        for r in results:
            if r.agent_domain in losers:
                r.confidence *= 0.6  # 降权但不删除
            resolved.append(r)
        return resolved

    def _extract_consensus(self, results: list[AgentResult]) -> list[str]:
        """提取多Agent共识 (出现≥2次的recommendation关键主题)"""
        from collections import Counter
        topics = Counter()
        for r in results:
            for rec in r.recommendations:
                # 简化: 取前4字作为topic
                topic = rec[:8] if len(rec) > 8 else rec
                topics[topic] += 1
        return [t for t, c in topics.items() if c >= 2]
