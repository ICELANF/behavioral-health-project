"""
Phase 4: Agent 反馈学习闭环 API

端点:
  POST   /v1/agent-feedback/submit              — 提交反馈
  GET    /v1/agent-feedback/list                 — 反馈列表
  GET    /v1/agent-feedback/growth/{agent_id}    — Agent 成长报告
  GET    /v1/agent-feedback/summary              — 所有 Agent 汇总
  GET    /v1/agent-feedback/metrics/{agent_id}   — Agent 日维度指标
  POST   /v1/agent-feedback/prompt-version       — 创建 Prompt 版本
  GET    /v1/agent-feedback/prompt-versions/{agent_id} — Prompt 版本列表
  POST   /v1/agent-feedback/aggregate            — 手动触发聚合 (admin)
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import User
from api.dependencies import get_current_user, require_coach_or_admin, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-feedback", tags=["agent-feedback"])


# ── Pydantic Schemas ──

class FeedbackSubmit(BaseModel):
    agent_id: str = Field(..., description="Agent 标识")
    feedback_type: str = Field(..., description="accept/reject/modify/rate")
    rating: Optional[int] = Field(None, ge=1, le=5, description="1-5 评分")
    comment: Optional[str] = None
    modifications: Optional[dict] = None
    session_id: Optional[str] = None
    user_message: Optional[str] = None
    agent_response: Optional[str] = None
    agents_used: Optional[List[str]] = None
    confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    tenant_id: Optional[str] = None


class PromptVersionCreate(BaseModel):
    agent_id: str
    system_prompt: str
    change_reason: str = ""
    activate: bool = True


# ── 端点 ──

@router.post("/submit")
def submit_feedback(
    data: FeedbackSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交 Agent 反馈"""
    from core.feedback_service import save_feedback

    if data.feedback_type not in ("accept", "reject", "modify", "rate"):
        raise HTTPException(status_code=400, detail="feedback_type 必须为 accept/reject/modify/rate")

    fb = save_feedback(
        db=db,
        agent_id=data.agent_id,
        user_id=current_user.id,
        feedback_type=data.feedback_type,
        rating=data.rating,
        comment=data.comment,
        modifications=data.modifications,
        session_id=data.session_id,
        user_message=data.user_message,
        agent_response=data.agent_response,
        agents_used=data.agents_used,
        confidence=data.confidence,
        processing_time_ms=data.processing_time_ms,
        tenant_id=data.tenant_id,
    )
    db.commit()
    return {"success": True, "data": {"id": fb.id, "agent_id": fb.agent_id}}


@router.get("/list")
def list_feedback(
    agent_id: Optional[str] = Query(None),
    feedback_type: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """查询反馈记录"""
    from core.feedback_service import list_feedbacks

    result = list_feedbacks(db, agent_id=agent_id, feedback_type=feedback_type,
                            tenant_id=tenant_id, skip=skip, limit=limit)
    return {"success": True, "data": result}


@router.get("/growth/{agent_id}")
def agent_growth_report(
    agent_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agent 成长报告"""
    from core.feedback_service import get_agent_growth_report

    report = get_agent_growth_report(db, agent_id, days=days)
    return {"success": True, "data": report}


@router.get("/summary")
def agents_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """所有 Agent 成长摘要"""
    from core.feedback_service import get_all_agents_summary

    summaries = get_all_agents_summary(db, days=days)
    return {"success": True, "data": summaries}


@router.get("/metrics/{agent_id}")
def agent_metrics(
    agent_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agent 日维度指标"""
    from core.models import AgentMetricsDaily
    from datetime import date, timedelta

    since = date.today() - timedelta(days=days)
    metrics = db.query(AgentMetricsDaily).filter(
        AgentMetricsDaily.agent_id == agent_id,
        AgentMetricsDaily.metric_date >= since,
    ).order_by(AgentMetricsDaily.metric_date).all()

    return {
        "success": True,
        "data": [
            {
                "date": str(m.metric_date),
                "total_calls": m.total_calls,
                "feedback_count": m.feedback_count,
                "accept_count": m.accept_count,
                "reject_count": m.reject_count,
                "acceptance_rate": m.acceptance_rate,
                "avg_rating": m.avg_rating,
                "avg_processing_ms": m.avg_processing_ms,
            }
            for m in metrics
        ],
    }


@router.post("/prompt-version")
def create_prompt_version_endpoint(
    data: PromptVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """创建新的 Prompt 版本"""
    from core.feedback_service import create_prompt_version

    try:
        pv = create_prompt_version(
            db=db,
            agent_id=data.agent_id,
            system_prompt=data.system_prompt,
            change_reason=data.change_reason,
            created_by=current_user.id,
            activate=data.activate,
        )
        db.commit()
        return {
            "success": True,
            "data": {
                "id": pv.id,
                "agent_id": pv.agent_id,
                "version": pv.version,
                "is_active": pv.is_active,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/prompt-versions/{agent_id}")
def list_prompt_versions_endpoint(
    agent_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agent Prompt 版本历史"""
    from core.feedback_service import list_prompt_versions

    versions = list_prompt_versions(db, agent_id, limit=limit)
    return {"success": True, "data": versions}


@router.post("/aggregate")
def trigger_aggregation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """手动触发日指标聚合"""
    from core.feedback_service import aggregate_daily_metrics
    from datetime import date, timedelta

    yesterday = date.today() - timedelta(days=1)
    count = aggregate_daily_metrics(db, target_date=yesterday)
    db.commit()
    return {"success": True, "data": {"date": str(yesterday), "agents_aggregated": count}}
