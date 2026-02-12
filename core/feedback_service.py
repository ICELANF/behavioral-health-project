"""
Phase 4: 反馈学习闭环服务

提供:
- 反馈持久化 (替代 agent_api.py 内存存储)
- 日维度指标聚合 (定时任务调用)
- Agent 成长报告
- Prompt 版本管理
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_

from core.models import (
    AgentFeedback, AgentMetricsDaily, AgentPromptVersion,
    AgentTemplate, User,
)

logger = logging.getLogger(__name__)


# ── 反馈持久化 ──

def save_feedback(
    db: Session,
    agent_id: str,
    user_id: int,
    feedback_type: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    modifications: Optional[dict] = None,
    session_id: Optional[str] = None,
    user_message: Optional[str] = None,
    agent_response: Optional[str] = None,
    agents_used: Optional[list] = None,
    confidence: Optional[float] = None,
    processing_time_ms: Optional[int] = None,
    tenant_id: Optional[str] = None,
) -> AgentFeedback:
    """持久化一条 Agent 反馈记录"""
    fb = AgentFeedback(
        agent_id=agent_id,
        user_id=user_id,
        session_id=session_id,
        feedback_type=feedback_type,
        rating=rating,
        comment=comment,
        modifications=modifications,
        user_message=user_message,
        agent_response=agent_response,
        agents_used=agents_used,
        confidence=confidence,
        processing_time_ms=processing_time_ms,
        tenant_id=tenant_id,
    )
    db.add(fb)
    db.flush()
    return fb


# ── 日维度指标聚合 ──

def aggregate_daily_metrics(db: Session, target_date: Optional[date] = None):
    """
    聚合指定日期的 Agent 质量指标

    定时任务每日 01:00 调用, 聚合前一天数据
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = datetime.combine(target_date + timedelta(days=1), datetime.min.time())

    # 查询该日所有反馈, 按 agent_id 聚合
    rows = db.query(
        AgentFeedback.agent_id,
        func.count(AgentFeedback.id).label("feedback_count"),
        func.sum(case(
            (AgentFeedback.feedback_type == "accept", 1), else_=0
        )).label("accept_count"),
        func.sum(case(
            (AgentFeedback.feedback_type == "reject", 1), else_=0
        )).label("reject_count"),
        func.sum(case(
            (AgentFeedback.feedback_type == "modify", 1), else_=0
        )).label("modify_count"),
        func.sum(case(
            (AgentFeedback.feedback_type == "rate", 1), else_=0
        )).label("rate_count"),
        func.sum(case(
            (AgentFeedback.rating.isnot(None), AgentFeedback.rating), else_=0
        )).label("total_rating"),
        func.avg(AgentFeedback.processing_time_ms).label("avg_processing_ms"),
        func.avg(AgentFeedback.confidence).label("avg_confidence"),
    ).filter(
        AgentFeedback.created_at >= day_start,
        AgentFeedback.created_at < day_end,
    ).group_by(AgentFeedback.agent_id).all()

    count = 0
    for row in rows:
        fb_count = row.feedback_count or 0
        accept_ct = row.accept_count or 0
        rate_ct = row.rate_count or 0
        total_rat = row.total_rating or 0

        acceptance_rate = (accept_ct / fb_count) if fb_count > 0 else 0.0
        avg_rating = (total_rat / rate_ct) if rate_ct > 0 else 0.0

        # UPSERT
        existing = db.query(AgentMetricsDaily).filter(
            AgentMetricsDaily.agent_id == row.agent_id,
            AgentMetricsDaily.metric_date == target_date,
        ).first()

        if existing:
            existing.feedback_count = fb_count
            existing.accept_count = accept_ct
            existing.reject_count = row.reject_count or 0
            existing.modify_count = row.modify_count or 0
            existing.rate_count = rate_ct
            existing.total_rating = total_rat
            existing.avg_processing_ms = float(row.avg_processing_ms or 0)
            existing.avg_confidence = float(row.avg_confidence or 0)
            existing.acceptance_rate = round(acceptance_rate, 4)
            existing.avg_rating = round(avg_rating, 2)
        else:
            metric = AgentMetricsDaily(
                agent_id=row.agent_id,
                metric_date=target_date,
                feedback_count=fb_count,
                accept_count=accept_ct,
                reject_count=row.reject_count or 0,
                modify_count=row.modify_count or 0,
                rate_count=rate_ct,
                total_rating=total_rat,
                avg_processing_ms=float(row.avg_processing_ms or 0),
                avg_confidence=float(row.avg_confidence or 0),
                acceptance_rate=round(acceptance_rate, 4),
                avg_rating=round(avg_rating, 2),
            )
            db.add(metric)
        count += 1

    db.flush()
    logger.info("指标聚合完成: date=%s, agents=%d", target_date, count)
    return count


# ── Agent 成长报告 ──

def get_agent_growth_report(
    db: Session,
    agent_id: str,
    days: int = 30,
) -> dict:
    """
    获取单个 Agent 的成长报告

    返回最近 N 天的日维度指标 + 汇总
    """
    since = date.today() - timedelta(days=days)

    metrics = db.query(AgentMetricsDaily).filter(
        AgentMetricsDaily.agent_id == agent_id,
        AgentMetricsDaily.metric_date >= since,
    ).order_by(AgentMetricsDaily.metric_date).all()

    # 汇总
    total_feedback = sum(m.feedback_count for m in metrics)
    total_accept = sum(m.accept_count for m in metrics)
    total_reject = sum(m.reject_count for m in metrics)
    total_rate_count = sum(m.rate_count for m in metrics)
    total_rating_sum = sum(m.total_rating for m in metrics)

    overall_acceptance = (total_accept / total_feedback) if total_feedback > 0 else 0.0
    overall_avg_rating = (total_rating_sum / total_rate_count) if total_rate_count > 0 else 0.0

    # 趋势 (最近7天 vs 前7天)
    recent_7 = [m for m in metrics if m.metric_date >= date.today() - timedelta(days=7)]
    prev_7 = [m for m in metrics if date.today() - timedelta(days=14) <= m.metric_date < date.today() - timedelta(days=7)]

    def avg_acceptance(ms):
        total = sum(m.feedback_count for m in ms)
        accept = sum(m.accept_count for m in ms)
        return (accept / total) if total > 0 else 0.0

    trend_acceptance = avg_acceptance(recent_7) - avg_acceptance(prev_7)

    # Prompt 版本历史
    prompt_versions = db.query(AgentPromptVersion).filter(
        AgentPromptVersion.agent_id == agent_id,
    ).order_by(AgentPromptVersion.version.desc()).limit(5).all()

    return {
        "agent_id": agent_id,
        "period_days": days,
        "summary": {
            "total_feedback": total_feedback,
            "total_accept": total_accept,
            "total_reject": total_reject,
            "acceptance_rate": round(overall_acceptance, 4),
            "avg_rating": round(overall_avg_rating, 2),
            "trend_acceptance_7d": round(trend_acceptance, 4),
        },
        "daily_metrics": [
            {
                "date": str(m.metric_date),
                "feedback_count": m.feedback_count,
                "accept_count": m.accept_count,
                "reject_count": m.reject_count,
                "acceptance_rate": m.acceptance_rate,
                "avg_rating": m.avg_rating,
                "avg_processing_ms": m.avg_processing_ms,
            }
            for m in metrics
        ],
        "prompt_versions": [
            {
                "version": pv.version,
                "is_active": pv.is_active,
                "traffic_pct": pv.traffic_pct,
                "change_reason": pv.change_reason,
                "prev_avg_rating": pv.prev_avg_rating,
                "prev_acceptance_rate": pv.prev_acceptance_rate,
                "created_at": pv.created_at.isoformat() if pv.created_at else None,
            }
            for pv in prompt_versions
        ],
    }


def get_all_agents_summary(db: Session, days: int = 30) -> list:
    """获取所有 Agent 的成长摘要"""
    since = date.today() - timedelta(days=days)

    # 聚合所有 Agent 的指标
    rows = db.query(
        AgentMetricsDaily.agent_id,
        func.sum(AgentMetricsDaily.feedback_count).label("total_feedback"),
        func.sum(AgentMetricsDaily.accept_count).label("total_accept"),
        func.sum(AgentMetricsDaily.reject_count).label("total_reject"),
        func.sum(AgentMetricsDaily.rate_count).label("total_rate_count"),
        func.sum(AgentMetricsDaily.total_rating).label("total_rating_sum"),
        func.avg(AgentMetricsDaily.avg_processing_ms).label("avg_processing_ms"),
    ).filter(
        AgentMetricsDaily.metric_date >= since,
    ).group_by(AgentMetricsDaily.agent_id).all()

    results = []
    for row in rows:
        fb = row.total_feedback or 0
        acc = row.total_accept or 0
        rate_ct = row.total_rate_count or 0
        rat_sum = row.total_rating_sum or 0

        # 获取模板显示名
        tpl = db.query(AgentTemplate).filter(
            AgentTemplate.agent_id == row.agent_id
        ).first()

        results.append({
            "agent_id": row.agent_id,
            "display_name": tpl.display_name if tpl else row.agent_id,
            "total_feedback": fb,
            "acceptance_rate": round((acc / fb) if fb > 0 else 0, 4),
            "avg_rating": round((rat_sum / rate_ct) if rate_ct > 0 else 0, 2),
            "avg_processing_ms": round(float(row.avg_processing_ms or 0), 1),
        })

    return sorted(results, key=lambda x: x["acceptance_rate"], reverse=True)


# ── Prompt 版本管理 ──

def create_prompt_version(
    db: Session,
    agent_id: str,
    system_prompt: str,
    change_reason: str = "",
    created_by: Optional[int] = None,
    activate: bool = True,
) -> AgentPromptVersion:
    """创建新的 prompt 版本"""
    # 获取当前最大版本号
    max_ver = db.query(func.max(AgentPromptVersion.version)).filter(
        AgentPromptVersion.agent_id == agent_id,
    ).scalar() or 0

    # 获取前一版本的指标 (最近30天)
    prev_metrics = get_agent_growth_report(db, agent_id, days=30)
    prev_rating = prev_metrics["summary"]["avg_rating"]
    prev_acceptance = prev_metrics["summary"]["acceptance_rate"]

    new_version = AgentPromptVersion(
        agent_id=agent_id,
        version=max_ver + 1,
        system_prompt=system_prompt,
        change_reason=change_reason,
        is_active=activate,
        traffic_pct=100 if activate else 0,
        prev_avg_rating=prev_rating or None,
        prev_acceptance_rate=prev_acceptance or None,
        created_by=created_by,
    )

    # 如果激活, 停用其他版本
    if activate:
        db.query(AgentPromptVersion).filter(
            AgentPromptVersion.agent_id == agent_id,
            AgentPromptVersion.is_active == True,
        ).update({"is_active": False, "traffic_pct": 0})

    db.add(new_version)

    # 同步更新 AgentTemplate
    if activate:
        tpl = db.query(AgentTemplate).filter(
            AgentTemplate.agent_id == agent_id,
        ).first()
        if tpl:
            tpl.system_prompt = system_prompt
            tpl.updated_at = datetime.utcnow()

    db.flush()
    logger.info("Prompt 版本创建: agent=%s, v%d, activate=%s", agent_id, new_version.version, activate)
    return new_version


def list_prompt_versions(
    db: Session,
    agent_id: str,
    limit: int = 10,
) -> list:
    """列出 Agent 的 prompt 版本历史"""
    versions = db.query(AgentPromptVersion).filter(
        AgentPromptVersion.agent_id == agent_id,
    ).order_by(AgentPromptVersion.version.desc()).limit(limit).all()

    return [
        {
            "id": v.id,
            "version": v.version,
            "system_prompt": v.system_prompt[:200] + "..." if len(v.system_prompt or "") > 200 else v.system_prompt,
            "change_reason": v.change_reason,
            "is_active": v.is_active,
            "traffic_pct": v.traffic_pct,
            "prev_avg_rating": v.prev_avg_rating,
            "prev_acceptance_rate": v.prev_acceptance_rate,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


# ── 反馈查询 ──

def list_feedbacks(
    db: Session,
    agent_id: Optional[str] = None,
    feedback_type: Optional[str] = None,
    tenant_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """查询反馈记录"""
    q = db.query(AgentFeedback)
    if agent_id:
        q = q.filter(AgentFeedback.agent_id == agent_id)
    if feedback_type:
        q = q.filter(AgentFeedback.feedback_type == feedback_type)
    if tenant_id:
        q = q.filter(AgentFeedback.tenant_id == tenant_id)

    total = q.count()
    items = q.order_by(AgentFeedback.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": [
            {
                "id": fb.id,
                "agent_id": fb.agent_id,
                "user_id": fb.user_id,
                "feedback_type": fb.feedback_type,
                "rating": fb.rating,
                "comment": fb.comment,
                "user_message": (fb.user_message or "")[:100],
                "agent_response": (fb.agent_response or "")[:100],
                "confidence": fb.confidence,
                "created_at": fb.created_at.isoformat() if fb.created_at else None,
            }
            for fb in items
        ],
        "total": total,
    }
