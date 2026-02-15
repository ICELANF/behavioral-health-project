# -*- coding: utf-8 -*-
"""
cost_attribution.py — LLM 成本归因分析服务

按租户 / 用户 / Agent 三维度归因 LLM 调用成本:
  - cost_per_user:   每用户累计 Token 消耗与金额
  - cost_per_agent:  每 Agent 累计 Token 消耗与金额
  - cost_per_tenant: 每租户累计 Token 消耗与金额
  - cost_report:     周期性成本报告生成
  - cost_breakdown:  按维度拆分的成本明细
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 模型定价表 (每 1K token, USD)
# ══════════════════════════════════════════════════════════════

MODEL_PRICING = {
    "gpt-4o":        {"input": 0.0025, "output": 0.010},
    "qwen-max":      {"input": 0.0020, "output": 0.006},
    "qwen-plus":     {"input": 0.0008, "output": 0.002},
    "deepseek-chat": {"input": 0.0001, "output": 0.0002},
    "qwen-turbo":    {"input": 0.0003, "output": 0.0006},
    "ollama-local":  {"input": 0.0, "output": 0.0},
}


@dataclass
class CostRecord:
    """单次 LLM 调用成本记录"""
    timestamp: str
    model: str
    agent_id: str
    user_id: str
    tenant_id: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


@dataclass
class CostAttribution:
    """成本归因分析引擎"""
    records: List[CostRecord] = field(default_factory=list)

    def add_record(self, record: CostRecord):
        """记录一次 LLM 调用的成本"""
        self.records.append(record)
        logger.info("Cost recorded: model=%s, agent=%s, user=%s, tokens=%d, cost=$%.4f",
                     record.model, record.agent_id, record.user_id,
                     record.total_tokens, record.cost_usd)

    def cost_per_user(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """按用户汇总成本"""
        cutoff = datetime.now() - timedelta(days=days)
        user_records = [r for r in self.records
                        if r.user_id == user_id and r.timestamp >= cutoff.isoformat()]
        total_cost = sum(r.cost_usd for r in user_records)
        total_tokens = sum(r.total_tokens for r in user_records)
        return {
            "user_id": user_id,
            "period_days": days,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "call_count": len(user_records),
        }

    def cost_per_agent(self, agent_id: str, days: int = 30) -> Dict[str, Any]:
        """按 Agent 汇总成本"""
        cutoff = datetime.now() - timedelta(days=days)
        agent_records = [r for r in self.records
                         if r.agent_id == agent_id and r.timestamp >= cutoff.isoformat()]
        total_cost = sum(r.cost_usd for r in agent_records)
        total_tokens = sum(r.total_tokens for r in agent_records)
        return {
            "agent_id": agent_id,
            "period_days": days,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "call_count": len(agent_records),
        }

    def cost_per_tenant(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """按租户汇总成本"""
        cutoff = datetime.now() - timedelta(days=days)
        tenant_records = [r for r in self.records
                          if r.tenant_id == tenant_id and r.timestamp >= cutoff.isoformat()]
        total_cost = sum(r.cost_usd for r in tenant_records)
        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": sum(r.total_tokens for r in tenant_records),
            "call_count": len(tenant_records),
        }

    def cost_report(self, days: int = 30) -> Dict[str, Any]:
        """生成综合成本报告"""
        cutoff = datetime.now() - timedelta(days=days)
        period_records = [r for r in self.records if r.timestamp >= cutoff.isoformat()]
        total = sum(r.cost_usd for r in period_records)

        by_model = {}
        for r in period_records:
            by_model.setdefault(r.model, 0.0)
            by_model[r.model] += r.cost_usd

        return {
            "period_days": days,
            "total_cost_usd": round(total, 4),
            "total_calls": len(period_records),
            "total_tokens": sum(r.total_tokens for r in period_records),
            "by_model": {k: round(v, 4) for k, v in by_model.items()},
            "generated_at": datetime.now().isoformat(),
        }

    def cost_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """多维度成本拆分"""
        cutoff = datetime.now() - timedelta(days=days)
        period_records = [r for r in self.records if r.timestamp >= cutoff.isoformat()]

        by_user = {}
        by_agent = {}
        by_tenant = {}
        for r in period_records:
            by_user.setdefault(r.user_id, 0.0)
            by_user[r.user_id] += r.cost_usd
            by_agent.setdefault(r.agent_id, 0.0)
            by_agent[r.agent_id] += r.cost_usd
            if r.tenant_id:
                by_tenant.setdefault(r.tenant_id, 0.0)
                by_tenant[r.tenant_id] += r.cost_usd

        return {
            "period_days": days,
            "cost_per_user_top10": dict(sorted(by_user.items(), key=lambda x: -x[1])[:10]),
            "cost_per_agent": {k: round(v, 4) for k, v in by_agent.items()},
            "cost_per_tenant": {k: round(v, 4) for k, v in by_tenant.items()},
        }


def calculate_call_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """计算单次调用成本"""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["qwen-turbo"])
    cost = (prompt_tokens / 1000 * pricing["input"]
            + completion_tokens / 1000 * pricing["output"])
    return round(cost, 6)
