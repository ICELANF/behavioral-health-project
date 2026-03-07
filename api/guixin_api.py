# -*- coding: utf-8 -*-
"""
归心 API — Phase 1 最小知己端点

端点：
- GET  /api/v1/guixin/today-anchor     晨醒聚合
- GET  /api/v1/guixin/profile-card      P+M+BPT6 画像卡
- POST /api/v1/guixin/rx/prescription   矩阵处方匹配
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from api.dependencies import get_db, get_current_user
from core.models import BehavioralProfile, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/guixin", tags=["guixin"])


# ── Schemas ──────────────────────────────────

class PrescriptionRequest(BaseModel):
    motivation_keywords: list[str] = []
    sisuo: Optional[dict] = None  # {"desire": "A", "fear": "B", "aversion": "C", "confusion": "D"}


class PrescriptionResponse(BaseModel):
    personality_archetype: Optional[str] = None
    motivation_type: Optional[str] = None
    bpt6_type: Optional[str] = None
    strategy: Optional[dict] = None
    xzb_tone: Optional[str] = None


# ── BPT-6 友好名 ────────────────────────────

BPT6_LABELS = {
    "action":      {"name": "行动型", "desc": "先做再想，用行动解决问题"},
    "knowledge":   {"name": "知识型", "desc": "理解原理后才放心行动"},
    "emotion":     {"name": "情绪型", "desc": "状态好时执行力强"},
    "relation":    {"name": "关系型", "desc": "在陪伴和支持中找到动力"},
    "ambivalent":  {"name": "矛盾型", "desc": "一旦开始就能坚持，启动是关键"},
    "environment": {"name": "环境型", "desc": "稳定的外部结构让行动变容易"},
    "mixed":       {"name": "混合型", "desc": "多种特质并存，灵活适应"},
}

# ── SPI → 可读提示 ──────────────────────────

def spi_to_hint(spi_score: float) -> str:
    if spi_score >= 70:
        return "今天状态很好，适合挑战新目标"
    elif spi_score >= 50:
        return "稳步推进，保持节奏"
    elif spi_score >= 30:
        return "今天轻量行动，积累能量"
    else:
        return "今天先休息，我在这里陪你"


# ── GET /today-anchor ────────────────────────

@router.get("/today-anchor")
async def today_anchor(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """晨醒聚合接口：今日行动 + 画像摘要 + 状态提示"""
    profile = db.query(BehavioralProfile).filter(
        BehavioralProfile.user_id == user.id
    ).first()

    if not profile:
        return {
            "has_profile": False,
            "readiness_hint": "完成首次评估，开启你的行为健康之旅",
            "today_action": None,
            "archetype": None,
            "motivation": None,
            "bpt6_type": None,
            "bpt6_label": None,
            "stage": None,
            "stage_name": None,
        }

    bpt6_info = BPT6_LABELS.get(profile.bpt6_type or "mixed", BPT6_LABELS["mixed"])

    return {
        "has_profile": True,
        "readiness_hint": spi_to_hint(profile.spi_score or 50),
        "today_action": None,  # Phase 2: 从 micro_action_tasks 取当日任务
        "archetype": profile.personality_archetype,
        "motivation": profile.motivation_type,
        "bpt6_type": profile.bpt6_type,
        "bpt6_label": bpt6_info,
        "stage": profile.current_stage.value if profile.current_stage else None,
        "stage_name": profile.friendly_stage_name,
    }


# ── GET /profile-card ────────────────────────

@router.get("/profile-card")
async def profile_card(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """P+M+BPT6 三维画像卡"""
    profile = db.query(BehavioralProfile).filter(
        BehavioralProfile.user_id == user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="尚未完成评估，暂无画像数据")

    bpt6_info = BPT6_LABELS.get(profile.bpt6_type or "mixed", BPT6_LABELS["mixed"])

    # 尝试获取 P×M 策略
    strategy = None
    xzb_tone = None
    if profile.personality_archetype and profile.motivation_type:
        try:
            from core.personality_matrix import get_prescription_strategy
            strategy = get_prescription_strategy(
                profile.personality_archetype,
                profile.motivation_type
            )
            xzb_tone = strategy.get("xzb_tone") if strategy else None
        except Exception as e:
            logger.warning(f"P×M strategy lookup failed: {e}")

    return {
        "personality_archetype": profile.personality_archetype,
        "motivation_type": profile.motivation_type,
        "bpt6_type": profile.bpt6_type,
        "bpt6_label": bpt6_info,
        "big5_scores": profile.big5_scores,
        "spi_score": profile.spi_score,
        "spi_level": profile.spi_level,
        "stage": profile.current_stage.value if profile.current_stage else None,
        "stage_name": profile.friendly_stage_name,
        "capacity_total": profile.capacity_total,
        "capacity_weak": profile.capacity_weak,
        "capacity_strong": profile.capacity_strong,
        "strategy": strategy,
        "xzb_tone": xzb_tone,
    }


# ── POST /rx/prescription ───────────────────

@router.post("/rx/prescription", response_model=PrescriptionResponse)
async def rx_prescription(
    req: PrescriptionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """矩阵处方匹配：根据用户画像 + 动机关键词生成处方策略"""
    from core.personality_matrix import (
        classify_personality,
        classify_motivation,
        get_prescription_strategy,
    )

    profile = db.query(BehavioralProfile).filter(
        BehavioralProfile.user_id == user.id
    ).first()

    # P 型：优先用缓存，否则从 big5 计算
    p_type = None
    if profile and profile.personality_archetype:
        p_type = profile.personality_archetype
    elif profile and profile.big5_scores:
        raw = {
            dim: (data.get("score", 0) if isinstance(data, dict) else 0)
            for dim, data in profile.big5_scores.items()
        }
        p_type = classify_personality(raw)

    # M 型：从关键词计算
    m_type = None
    if req.motivation_keywords:
        m_type = classify_motivation(req.motivation_keywords)
    elif profile and profile.motivation_type:
        m_type = profile.motivation_type

    # 缓存到 profile
    if profile:
        if p_type and not profile.personality_archetype:
            profile.personality_archetype = p_type
        if m_type and not profile.motivation_type:
            profile.motivation_type = m_type
        db.commit()

    # 查矩阵
    strategy = None
    xzb_tone = None
    if p_type and m_type:
        strategy = get_prescription_strategy(p_type, m_type)
        xzb_tone = strategy.get("xzb_tone") if strategy else None

    bpt6_type = profile.bpt6_type if profile else None

    return PrescriptionResponse(
        personality_archetype=p_type,
        motivation_type=m_type,
        bpt6_type=bpt6_type,
        strategy=strategy,
        xzb_tone=xzb_tone,
    )
