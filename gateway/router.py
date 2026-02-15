"""
跨层API网关 — 路由分发 + 权限校验

用户层请求 → /v1/assistant/*  → assistant_agents
教练层请求 → /v1/agent/*      → professional_agents
跨层请求   → /v1/gateway/*    → 授权+脱敏后转发
"""
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/v1/gateway", tags=["cross_layer_gateway"])


@router.get("/patient-summary/{user_id}")
async def get_patient_summary_for_coach(
    user_id: str,
    # current_user = Depends(require_coach_role),
):
    """
    教练查看用户摘要 — 脱敏后返回
    
    数据流: 教练层 → 网关(授权+脱敏) → 用户层DB → 脱敏 → 返回教练
    """
    from .sanitizer import sanitize_for_coach
    # TODO: 查询用户层数据
    # raw_data = await user_db.get_patient_summary(user_id)
    # return sanitize_for_coach(raw_data)
    return {"user_id": user_id, "status": "stub"}


@router.post("/rx-delivery/{user_id}")
async def deliver_rx_to_user(
    user_id: str,
    rx_data: dict,
    # current_user = Depends(require_coach_role),
):
    """
    教练审核后的处方下发给用户
    
    数据流: 教练层(审核通过) → 网关(记录+转换) → 用户层存储 → 用户可见
    """
    # TODO: 验证教练审核状态
    # TODO: 写入用户层DB
    # TODO: 审计日志
    return {"delivered": True, "user_id": user_id}
