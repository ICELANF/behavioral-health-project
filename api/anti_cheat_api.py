"""
防刷策略 API 端点 + 审查队列
契约来源: Sheet⑦ 防刷策略矩阵 + Sheet⑩

端点清单:
  POST /v1/anti-cheat/evaluate       — 积分发放前策略校验 (内部调用)
  POST /v1/anti-cheat/confirm         — 交叉验证确认 (AS-04)
  GET  /v1/anti-cheat/daily-status    — 查询今日各事件剩余次数
  GET  /v1/anti-cheat/review-queue    — 异常审查队列 (管理员)
  POST /v1/anti-cheat/review-resolve  — 审查结果处理 (管理员)
  GET  /v1/anti-cheat/strategy-map    — 查询事件→策略映射
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import date, datetime, timezone

router = APIRouter(prefix="/v1/anti-cheat", tags=["anti-cheat"])


# ── 请求/响应模型 ──

class EvaluateRequest(BaseModel):
    user_id: int
    event_type: str
    base_points: int
    points_category: str
    quality_score: float = 1.0
    counterpart_user_id: int = 0
    behavior_id: str = ""
    metadata: Dict[str, Any] = {}


class EvaluateResponse(BaseModel):
    final_points: int
    original_points: int
    awarded: bool
    verdict_summary: str
    user_message: str
    flagged_for_review: bool
    pending_confirmation: bool
    strategy_details: List[Dict]


class ConfirmRequest(BaseModel):
    confirmer_user_id: int
    original_user_id: int
    event_type: str
    behavior_id: str


class DailyStatusResponse(BaseModel):
    event_caps: List[Dict]  # [{event_type, daily_cap, used, remaining}]
    date: str


class ReviewItem(BaseModel):
    user_id: int
    event_type: str
    anomalies: List[Dict]
    timestamp: str
    status: str = "pending"  # pending | approved | rejected | rollback


class ReviewResolveRequest(BaseModel):
    review_id: str
    action: str  # "approve" | "reject" | "rollback"
    notes: str = ""


class StrategyMapResponse(BaseModel):
    event_type: str
    strategies: List[str]
    strategy_names: List[str]


# ── 端点实现 ──

@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_points(req: EvaluateRequest):
    """
    积分发放前策略校验 (内部调用)。
    
    IncentiveEngine.award_points() 调用此端点决定最终积分值。
    """
    from anti_cheat_engine import AntiCheatPipeline, PointsAwardRequest
    
    pipeline = AntiCheatPipeline.create_default()
    
    award_req = PointsAwardRequest(
        user_id=req.user_id,
        event_type=req.event_type,
        base_points=req.base_points,
        points_category=req.points_category,
        quality_score=req.quality_score,
        counterpart_user_id=req.counterpart_user_id,
        behavior_id=req.behavior_id,
        metadata=req.metadata,
    )
    
    result = await pipeline.process(award_req)
    
    return EvaluateResponse(
        final_points=result.final_points,
        original_points=result.original_points,
        awarded=result.awarded,
        verdict_summary=result.verdict_summary,
        user_message=result.user_message,
        flagged_for_review=result.flagged_for_review,
        pending_confirmation=result.pending_confirmation,
        strategy_details=[
            {
                "strategy": sr.strategy.value,
                "verdict": sr.verdict.value,
                "adjusted_points": sr.adjusted_points,
                "reason": sr.reason,
            }
            for sr in result.strategy_results
        ],
    )


@router.post("/confirm")
async def confirm_cross_verify(req: ConfirmRequest):
    """
    交叉验证确认 (AS-04)。
    
    对方点击「确认」后调用, 释放积分。
    """
    from anti_cheat_engine import AntiCheatPipeline
    
    pipeline = AntiCheatPipeline.create_default()
    success = await pipeline.process_cross_verify_confirmation(
        confirmer_user_id=req.confirmer_user_id,
        original_user_id=req.original_user_id,
        event_type=req.event_type,
        behavior_id=req.behavior_id,
    )
    
    if not success:
        raise HTTPException(404, detail="未找到待确认记录")
    
    return {"confirmed": True, "message": "确认成功, 积分已发放"}


@router.get("/daily-status", response_model=DailyStatusResponse)
async def get_daily_status(user_id: int):
    """
    查询今日各事件剩余次数。
    前端展示: 用户可看到自己今日各行为的积分获取进度。
    """
    from anti_cheat_engine import DailyCapStrategy
    
    strategy = DailyCapStrategy()
    today = date.today().isoformat()
    
    caps_info = []
    for event_type, cap in strategy._caps.items():
        if cap > 0:
            day_key = strategy._day_key(user_id, event_type)
            used = await strategy._get_count(day_key)
            caps_info.append({
                "event_type": event_type,
                "daily_cap": cap,
                "used": used,
                "remaining": max(0, cap - used),
            })
    
    return DailyStatusResponse(event_caps=caps_info, date=today)


@router.get("/review-queue")
async def get_review_queue(
    status: str = "pending",
    limit: int = 20,
    offset: int = 0,
):
    """
    异常审查队列 (管理员)。
    AS-06 标记的异常行为进入此队列。
    """
    # TODO: 实际从 DB/Redis 读取
    return {
        "items": [],
        "total": 0,
        "status_filter": status,
        "limit": limit,
        "offset": offset,
    }


@router.post("/review-resolve")
async def resolve_review(req: ReviewResolveRequest):
    """
    审查结果处理 (管理员)。
    
    操作:
      approve  — 确认无异常, 积分保留
      reject   — 确认异常, 积分不追溯 (已发放不回收)
      rollback — 确认刷量, 回收积分 + 记录违规
    """
    valid_actions = {"approve", "reject", "rollback"}
    if req.action not in valid_actions:
        raise HTTPException(400, detail=f"Invalid action: {req.action}")
    
    # TODO: 实际写入审查结果
    return {
        "review_id": req.review_id,
        "action": req.action,
        "resolved": True,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/strategy-map/{event_type}", response_model=StrategyMapResponse)
async def get_strategy_map(event_type: str):
    """查询指定事件适用的防刷策略"""
    from anti_cheat_engine import get_strategies_for_event
    
    strategies = get_strategies_for_event(event_type)
    
    strategy_names = {
        "AS-01": "每日上限",
        "AS-02": "质量加权",
        "AS-03": "时间衰减",
        "AS-04": "交叉验证",
        "AS-05": "成长轨校验",
        "AS-06": "异常检测",
    }
    
    return StrategyMapResponse(
        event_type=event_type,
        strategies=strategies,
        strategy_names=[strategy_names.get(s, s) for s in strategies],
    )
