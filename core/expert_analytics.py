# -*- coding: utf-8 -*-
"""
expert_analytics.py — 专家效率分析与赋能服务

量化追踪健康管理师 (B端专家) 使用 AI 工具后的效率提升:
  - expert_efficiency:   专家工作效率指标
  - advisor_tool:        AI 辅助工具使用统计
  - expert_ROI:          专家使用 AI 的投资回报率
  - B端仪表盘:           专家工作效率仪表盘数据

核心指标:
  - 单位时间服务用户数 (clients_per_hour)
  - 干预方案生成时间 (plan_generation_time)
  - 用户满意度 (client_satisfaction)
  - AI 建议采纳率 (ai_adoption_rate)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExpertEfficiencyMetrics:
    """专家效率指标"""
    expert_id: str
    period_start: str
    period_end: str
    # 效率指标
    clients_served: int = 0
    total_hours: float = 0
    clients_per_hour: float = 0
    # AI 工具使用
    ai_queries: int = 0
    ai_suggestions_accepted: int = 0
    ai_adoption_rate: float = 0
    # 质量指标
    avg_satisfaction: float = 0
    plans_generated: int = 0
    avg_plan_time_minutes: float = 0
    # expert_efficiency 综合分
    expert_efficiency_score: float = 0
    # advisor_tool 使用深度
    advisor_tool_depth: float = 0


def compute_expert_efficiency(
    expert_id: str,
    clients_served: int,
    total_hours: float,
    ai_queries: int,
    ai_accepted: int,
    avg_satisfaction: float,
    plans_generated: int,
    avg_plan_time: float,
) -> ExpertEfficiencyMetrics:
    """计算专家效率综合指标

    expert_efficiency = weighted(
        clients_per_hour * 0.3 +
        ai_adoption_rate * 0.25 +
        satisfaction * 0.25 +
        plan_speed * 0.2
    )
    """
    cph = clients_served / max(total_hours, 1)
    adoption = ai_accepted / max(ai_queries, 1)

    # 归一化到 0-100
    cph_score = min(cph / 5 * 100, 100)      # 5 clients/hr = 100分
    adoption_score = adoption * 100
    sat_score = avg_satisfaction * 20          # 5分制 → 100
    speed_score = max(0, 100 - avg_plan_time * 2)  # 越快越高

    expert_efficiency_score = (
        cph_score * 0.3 +
        adoption_score * 0.25 +
        sat_score * 0.25 +
        speed_score * 0.2
    )

    # advisor_tool 使用深度 = 查询频率 × 采纳率
    advisor_tool_depth = (ai_queries / max(clients_served, 1)) * adoption

    metrics = ExpertEfficiencyMetrics(
        expert_id=expert_id,
        period_start=(datetime.now() - timedelta(days=30)).isoformat(),
        period_end=datetime.now().isoformat(),
        clients_served=clients_served,
        total_hours=total_hours,
        clients_per_hour=round(cph, 2),
        ai_queries=ai_queries,
        ai_suggestions_accepted=ai_accepted,
        ai_adoption_rate=round(adoption, 4),
        avg_satisfaction=avg_satisfaction,
        plans_generated=plans_generated,
        avg_plan_time_minutes=avg_plan_time,
        expert_efficiency_score=round(expert_efficiency_score, 1),
        advisor_tool_depth=round(advisor_tool_depth, 4),
    )

    logger.info("expert_efficiency computed: expert=%s, score=%.1f, adoption=%.2f",
                expert_id, expert_efficiency_score, adoption)
    return metrics


def compute_expert_ROI(
    expert_efficiency_before: float,
    expert_efficiency_after: float,
    ai_cost_per_month: float,
    revenue_per_client: float,
    additional_clients: int,
) -> Dict[str, Any]:
    """计算专家使用 AI 工具的投资回报率 (expert_ROI)

    expert_ROI = (增量收入 - AI工具成本) / AI工具成本 × 100%
    """
    incremental_revenue = additional_clients * revenue_per_client
    roi = (incremental_revenue - ai_cost_per_month) / max(ai_cost_per_month, 0.01) * 100
    efficiency_uplift = (expert_efficiency_after - expert_efficiency_before) / max(expert_efficiency_before, 1) * 100

    result = {
        "expert_efficiency_before": expert_efficiency_before,
        "expert_efficiency_after": expert_efficiency_after,
        "efficiency_uplift_pct": round(efficiency_uplift, 1),
        "ai_cost_monthly": ai_cost_per_month,
        "incremental_revenue": incremental_revenue,
        "expert_ROI_pct": round(roi, 1),
        "payback_months": round(ai_cost_per_month / max(incremental_revenue - ai_cost_per_month, 0.01), 1),
    }
    logger.info("expert_ROI calculated: uplift=%.1f%%, ROI=%.1f%%", efficiency_uplift, roi)
    return result


def get_advisor_tool_stats(expert_id: str) -> Dict[str, Any]:
    """获取 advisor_tool 使用统计"""
    return {
        "expert_id": expert_id,
        "advisor_tool_features_used": [
            "ai_chat_assistant",
            "auto_plan_generation",
            "risk_alert_review",
            "batch_push_approval",
            "content_recommendation",
        ],
        "advisor_tool_sessions_30d": 0,
        "advisor_tool_avg_duration_min": 0,
    }
