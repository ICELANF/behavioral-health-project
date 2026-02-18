"""
Observer 飞轮 API — 试用墙额度管理
端点:
  GET  /api/v1/observer/quota/today     → 今日剩余额度
  POST /api/v1/observer/quota/consume   → 消耗一次额度
  GET  /api/v1/assessment/progress      → 评估进度 (扩展已有)
"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# from database import get_db
# from dependencies import get_current_user
# from models import User, ObserverQuotaLog, AssessmentSession

router = APIRouter(prefix="/api/v1", tags=["observer-flywheel"])

# ═══════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════
OBSERVER_DAILY_LIMITS = {
    "chat": 3,       # 对话次数
    "food_scan": 3,  # 食物识别次数
    "voice": 3,      # 语音输入次数
}


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════
class QuotaTodayResponse(BaseModel):
    """今日额度响应"""
    chat_used: int = 0
    chat_limit: int = 3
    chat_remaining: int = 3
    food_scan_used: int = 0
    food_scan_limit: int = 3
    food_scan_remaining: int = 3
    voice_used: int = 0
    voice_limit: int = 3
    voice_remaining: int = 3
    total_used: int = 0
    total_limit: int = 9
    total_remaining: int = 9
    date: str  # YYYY-MM-DD


class ConsumeRequest(BaseModel):
    """消耗额度请求"""
    quota_type: str  # chat | food_scan | voice


class ConsumeResponse(BaseModel):
    """消耗额度响应"""
    success: bool
    quota_type: str
    remaining: int
    message: str = ""
    upgrade_prompt: bool = False  # 是否弹升级提示


class AssessmentProgressResponse(BaseModel):
    """评估进度响应"""
    started: bool = False
    completed: bool = False
    progress_pct: int = 0  # 0-100
    current_module: Optional[str] = None  # ttm7 | big5 | bpt6 | capacity | spi
    modules_done: list[str] = []
    modules_total: int = 5
    estimated_minutes_left: int = 0
    can_upgrade: bool = False  # 是否满足升级条件


# ═══════════════════════════════════════════════════
# GET /observer/quota/today
# ═══════════════════════════════════════════════════
@router.get("/observer/quota/today", response_model=QuotaTodayResponse)
async def get_observer_quota_today(
    # current_user: User = Depends(get_current_user),
    # db: AsyncSession = Depends(get_db),
):
    """
    获取Observer今日剩余额度
    
    逻辑:
    1. 查询 observer_quota_log 表，统计今日各类型使用次数
    2. 计算剩余 = 限额 - 已用
    3. 仅 Observer 角色有效 (role_level <= 1)
    """
    # --- 实际实现时取消注释 ---
    # if current_user.role_level > 1:
    #     # Grower+ 无限额度
    #     return QuotaTodayResponse(
    #         chat_used=0, chat_limit=999999, chat_remaining=999999,
    #         food_scan_used=0, food_scan_limit=999999, food_scan_remaining=999999,
    #         voice_used=0, voice_limit=999999, voice_remaining=999999,
    #         total_used=0, total_limit=999999, total_remaining=999999,
    #         date=date.today().isoformat(),
    #     )
    #
    # today = date.today()
    # stmt = select(
    #     ObserverQuotaLog.quota_type,
    #     func.count(ObserverQuotaLog.id)
    # ).where(
    #     ObserverQuotaLog.user_id == current_user.id,
    #     func.date(ObserverQuotaLog.created_at) == today,
    # ).group_by(ObserverQuotaLog.quota_type)
    #
    # result = await db.execute(stmt)
    # usage = {row[0]: row[1] for row in result.all()}
    
    # --- Mock 数据 (开发阶段) ---
    usage = {"chat": 1, "food_scan": 0, "voice": 0}
    today_str = date.today().isoformat()
    
    chat_used = usage.get("chat", 0)
    food_used = usage.get("food_scan", 0)
    voice_used = usage.get("voice", 0)
    
    return QuotaTodayResponse(
        chat_used=chat_used,
        chat_limit=OBSERVER_DAILY_LIMITS["chat"],
        chat_remaining=max(0, OBSERVER_DAILY_LIMITS["chat"] - chat_used),
        food_scan_used=food_used,
        food_scan_limit=OBSERVER_DAILY_LIMITS["food_scan"],
        food_scan_remaining=max(0, OBSERVER_DAILY_LIMITS["food_scan"] - food_used),
        voice_used=voice_used,
        voice_limit=OBSERVER_DAILY_LIMITS["voice"],
        voice_remaining=max(0, OBSERVER_DAILY_LIMITS["voice"] - voice_used),
        total_used=chat_used + food_used + voice_used,
        total_limit=sum(OBSERVER_DAILY_LIMITS.values()),
        total_remaining=max(0, sum(OBSERVER_DAILY_LIMITS.values()) - chat_used - food_used - voice_used),
        date=today_str,
    )


# ═══════════════════════════════════════════════════
# POST /observer/quota/consume
# ═══════════════════════════════════════════════════
@router.post("/observer/quota/consume", response_model=ConsumeResponse)
async def consume_observer_quota(
    req: ConsumeRequest,
    # current_user: User = Depends(get_current_user),
    # db: AsyncSession = Depends(get_db),
):
    """
    消耗一次Observer额度
    
    逻辑:
    1. 检查quota_type是否合法
    2. 查询今日已用次数
    3. 如已达上限 → 返回失败 + upgrade_prompt=True
    4. 未达上限 → 写入日志 + 返回剩余次数
    """
    if req.quota_type not in OBSERVER_DAILY_LIMITS:
        raise HTTPException(status_code=400, detail=f"无效的额度类型: {req.quota_type}")
    
    limit = OBSERVER_DAILY_LIMITS[req.quota_type]
    
    # --- 实际实现时取消注释 ---
    # if current_user.role_level > 1:
    #     return ConsumeResponse(success=True, quota_type=req.quota_type, remaining=999999)
    #
    # today = date.today()
    # stmt = select(func.count(ObserverQuotaLog.id)).where(
    #     ObserverQuotaLog.user_id == current_user.id,
    #     ObserverQuotaLog.quota_type == req.quota_type,
    #     func.date(ObserverQuotaLog.created_at) == today,
    # )
    # result = await db.execute(stmt)
    # used = result.scalar() or 0
    
    # --- Mock ---
    used = 1  # 假设已用1次
    
    if used >= limit:
        return ConsumeResponse(
            success=False,
            quota_type=req.quota_type,
            remaining=0,
            message="今日次数已用完，完成健康评估可解锁无限使用",
            upgrade_prompt=True,
        )
    
    # --- 实际实现: 写入日志 ---
    # log = ObserverQuotaLog(
    #     user_id=current_user.id,
    #     quota_type=req.quota_type,
    #     created_at=datetime.utcnow(),
    # )
    # db.add(log)
    # await db.commit()
    
    remaining = limit - used - 1
    return ConsumeResponse(
        success=True,
        quota_type=req.quota_type,
        remaining=remaining,
        message=f"剩余{remaining}次" if remaining > 0 else "这是今天最后一次，完成评估可解锁无限使用",
        upgrade_prompt=(remaining == 0),
    )


# ═══════════════════════════════════════════════════
# GET /assessment/progress
# ═══════════════════════════════════════════════════
@router.get("/assessment/progress", response_model=AssessmentProgressResponse)
async def get_assessment_progress(
    # current_user: User = Depends(get_current_user),
    # db: AsyncSession = Depends(get_db),
):
    """
    获取BAPS评估进度 (扩展已有接口，增加飞轮所需字段)
    
    逻辑:
    1. 查询 assessment_sessions 表，找当前用户最新的评估会话
    2. 统计已完成的模块数
    3. 计算进度百分比和预估剩余时间
    4. 判断是否满足升级条件 (全部完成)
    """
    # --- 实际实现时取消注释 ---
    # stmt = select(AssessmentSession).where(
    #     AssessmentSession.user_id == current_user.id,
    # ).order_by(AssessmentSession.created_at.desc()).limit(1)
    # result = await db.execute(stmt)
    # session = result.scalar_one_or_none()
    #
    # if not session:
    #     return AssessmentProgressResponse(started=False)

    # --- Mock ---
    modules_all = ["ttm7", "big5", "bpt6", "capacity", "spi"]
    modules_done = ["ttm7"]  # 模拟已完成1个
    
    progress_pct = int(len(modules_done) / len(modules_all) * 100)
    current_idx = len(modules_done)
    current_module = modules_all[current_idx] if current_idx < len(modules_all) else None
    
    # 每模块约2分钟
    minutes_left = (len(modules_all) - len(modules_done)) * 2
    
    return AssessmentProgressResponse(
        started=len(modules_done) > 0,
        completed=len(modules_done) == len(modules_all),
        progress_pct=progress_pct,
        current_module=current_module,
        modules_done=modules_done,
        modules_total=len(modules_all),
        estimated_minutes_left=minutes_left,
        can_upgrade=len(modules_done) == len(modules_all),
    )


# ═══════════════════════════════════════════════════
# 数据库模型参考 (新增表)
# ═══════════════════════════════════════════════════
"""
-- 新增到 models.py:

class ObserverQuotaLog(Base):
    __tablename__ = "observer_quota_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    quota_type = Column(String(20), nullable=False)  # chat | food_scan | voice
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_observer_quota_user_date", "user_id", "created_at"),
    )

-- 迁移SQL:
CREATE TABLE observer_quota_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    quota_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_observer_quota_user_date ON observer_quota_logs(user_id, created_at);
"""
