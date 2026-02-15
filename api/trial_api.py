"""
观察员体验版 API 端点
契约来源: Sheet③ A节 · Sheet⑨ 治理触点
提供体验版评估和AI对话的额度查询/消耗接口
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.deps import (
    get_current_user,
    get_current_user_optional,
    get_trial_tracker,
    get_audit_logger,
)

router = APIRouter(prefix="/v1/trial", tags=["observer-trial"])


# ── 响应模型 ──

class TrialStatusResponse(BaseModel):
    used: int
    limit: int
    remaining: int
    allowed: bool
    upgrade_hint: Optional[str] = None


class TrialConsumeResponse(BaseModel):
    success: bool
    remaining: int
    upgrade_hint: Optional[str] = None


# ── 体验版评估 ──

@router.get("/assessment/status", response_model=TrialStatusResponse)
async def get_trial_assessment_status(
    user=Depends(get_current_user),
    tracker=Depends(get_trial_tracker),
):
    """查询体验版评估剩余额度"""
    result = await tracker.check_trial_assessment(user.id)
    return TrialStatusResponse(**result)


@router.post("/assessment/consume", response_model=TrialConsumeResponse)
async def consume_trial_assessment(
    user=Depends(get_current_user),
    tracker=Depends(get_trial_tracker),
    audit=Depends(get_audit_logger),
):
    """
    消耗一次体验版评估额度。
    
    调用时机: 用户点击「开始体验评估」时。
    契约规则: 每位注册观察员限1次 HF-20 快筛。
    审计触点: Sheet⑨ 观察员→体验版评估
    """
    success = await tracker.consume_trial_assessment(user.id)
    
    if not success:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "trial_limit_exceeded",
                "message": "体验版评估已使用完毕",
                "upgrade_hint": "成为成长者获取完整评估服务",
                "upgrade_action": "become_grower",
            }
        )
    
    # 审计记录 (Sheet⑨: 评估结果引导注册)
    await audit.log(
        user_id=user.id,
        action="trial_assessment_consumed",
        resource_type="assessment",
        details={"assessment_type": "HF-20", "trial": True},
    )
    
    status = await tracker.check_trial_assessment(user.id)
    return TrialConsumeResponse(
        success=True,
        remaining=status["remaining"],
        upgrade_hint="注册获取完整报告" if status["remaining"] == 0 else None,
    )


# ── AI 体验对话 ──

@router.get("/chat/status", response_model=TrialStatusResponse)
async def get_trial_chat_status(
    user=Depends(get_current_user),
    tracker=Depends(get_trial_tracker),
):
    """查询AI体验对话剩余轮数"""
    result = await tracker.check_trial_chat(user.id)
    return TrialStatusResponse(**result)


@router.post("/chat/consume", response_model=TrialConsumeResponse)
async def consume_trial_chat_round(
    user=Depends(get_current_user),
    tracker=Depends(get_trial_tracker),
    audit=Depends(get_audit_logger),
):
    """
    消耗一轮AI体验对话额度。
    
    调用时机: 每轮AI对话发送前。
    契约规则: 每位注册观察员限3轮对话。
    审计触点: Sheet⑨ 观察员→AI体验对话
    """
    success = await tracker.consume_trial_chat_round(user.id)
    
    if not success:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "trial_limit_exceeded",
                "message": "AI体验对话已达上限",
                "upgrade_hint": "注册解锁完整AI服务",
                "upgrade_action": "become_grower",
            }
        )
    
    # 审计记录 (Sheet⑨: 对话引导注册)
    await audit.log(
        user_id=user.id,
        action="trial_chat_round_consumed",
        resource_type="chat",
        details={"trial": True},
    )
    
    status = await tracker.check_trial_chat(user.id)
    return TrialConsumeResponse(
        success=True,
        remaining=status["remaining"],
        upgrade_hint="注册解锁完整AI服务" if status["remaining"] == 0 else None,
    )


# ── 体验版综合状态 (前端首屏一次性加载) ──

class TrialOverviewResponse(BaseModel):
    assessment: TrialStatusResponse
    chat: TrialStatusResponse
    role: str
    can_upgrade: bool


@router.get("/overview", response_model=TrialOverviewResponse)
async def get_trial_overview(
    user=Depends(get_current_user),
    tracker=Depends(get_trial_tracker),
):
    """
    获取体验版综合状态 (单次请求,减少前端多次调用)。
    前端路由守卫 loadTrialStatus() 调用此接口。
    """
    assessment = await tracker.check_trial_assessment(user.id)
    chat = await tracker.check_trial_chat(user.id)
    
    role = getattr(user, "role", "observer")
    can_upgrade = role.lower() == "observer"
    
    return TrialOverviewResponse(
        assessment=TrialStatusResponse(**assessment),
        chat=TrialStatusResponse(**chat),
        role=role,
        can_upgrade=can_upgrade,
    )
