"""
Coach 飞轮 API — 审核队列 + 一键操作 + 效率统计
端点:
  GET  /api/v1/coach/review-queue           → 待审队列(含AI预填)
  POST /api/v1/coach/review/:id/approve     → 通过
  POST /api/v1/coach/review/:id/reject      → 驳回
  GET  /api/v1/coach/stats/today            → 今日效率统计
"""

from datetime import date, datetime
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

# from database import get_db
# from dependencies import require_coach_or_admin
# from models import User, CoachReviewQueue, BehaviorPrescription

router = APIRouter(prefix="/api/v1/coach", tags=["coach-flywheel"])


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════
class RxField(BaseModel):
    """处方六要素字段"""
    key: str
    label: str
    value: str
    placeholder: str = ""


class ReviewQueueItem(BaseModel):
    """待审队列项"""
    id: str
    student_name: str
    student_id: int
    stage: str                  # S0-S6
    level: str                  # L1-L5
    bpt_type: str               # 行为分型
    streak_days: int = 0
    risk_level: Literal["low", "medium", "high", "crisis"]
    type: Literal["prescription", "ai_reply", "push"]
    type_label: str
    priority: Literal["normal", "urgent"] = "normal"
    wait_time: str              # 人类可读等待时间
    created_at: str
    
    # AI预填内容
    ai_summary: str             # progress_analyzer生成的一段话摘要
    rx_fields: Optional[list[RxField]] = None       # 处方类: 六要素预填
    ai_draft: Optional[str] = None                  # AI回复类: 拟回复内容
    push_type: Optional[str] = None                 # 推送类: 推送类型
    push_content: Optional[str] = None              # 推送类: 推送内容


class ReviewQueueResponse(BaseModel):
    """队列响应"""
    items: list[ReviewQueueItem]
    total: int
    pending_prescription: int
    pending_ai_reply: int
    pending_push: int


class ReviewActionRequest(BaseModel):
    """审核操作请求"""
    note: Optional[str] = None              # 备注(驳回时建议填写)
    edited_content: Optional[str] = None    # 修改后的内容
    edited_rx_fields: Optional[list[RxField]] = None  # 修改后的处方字段


class ReviewActionResponse(BaseModel):
    """审核操作响应"""
    success: bool
    review_id: str
    action: str
    next_id: Optional[str] = None   # 下一个待审项ID (自动跳转)
    message: str = ""
    elapsed_seconds: int = 0        # 本条审核耗时


class CoachStatsResponse(BaseModel):
    """教练今日效率统计"""
    today_reviewed: int
    pending_count: int
    avg_seconds: int            # 平均审核耗时(秒)
    approved_count: int
    rejected_count: int
    approval_rate: float        # 通过率 0-1
    my_student_count: int
    fastest_review: int         # 最快一条(秒)
    slowest_review: int         # 最慢一条(秒)


# ═══════════════════════════════════════════════════
# GET /review-queue
# ═══════════════════════════════════════════════════
@router.get("/review-queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    type_filter: Optional[str] = Query(None, description="prescription|ai_reply|push"),
    risk_filter: Optional[str] = Query(None, description="low|medium|high|crisis"),
    # current_user: User = Depends(require_coach_or_admin),
    # db: AsyncSession = Depends(get_db),
):
    """
    获取待审队列
    
    数据来源:
    1. prescription: InterventionPlanner→rx_composer Agent生成处方→入队待教练确认
    2. ai_reply: 用户对话→Agent回复→quality_auditor标记需人审→入队
    3. push: notification_agent生成推送→CoachPushQueue(pending)→待审
    
    AI预填逻辑:
    - ai_summary: progress_analyzer Agent分析学员近7天数据，生成一段话摘要
    - rx_fields: rx_composer Agent预填处方六要素，教练可直接A通过或修改
    - ai_draft: Agent拟回复，教练可直接A发送或编辑后发送
    
    排序: urgent优先 → risk_level降序 → created_at升序(先到先审)
    """
    # --- Mock ---
    items = [
        ReviewQueueItem(
            id="rv_001", student_name="王阿姨", student_id=1001,
            stage="S1", level="L2", bpt_type="情绪型", streak_days=0,
            risk_level="high", type="ai_reply", type_label="AI回复审核",
            priority="urgent", wait_time="15分钟前", created_at="2026-02-17T14:15:00",
            ai_summary="王阿姨在对话中表达了对控糖失败的沮丧感，SPI=22分(L2层)，有dropout风险。AI建议以共情为主，避免设定新目标。",
            ai_draft="阿姨，控糖确实不容易，您能坚持测量血糖已经很了不起了。我们不急着改变太多，先从您最舒服的节奏开始，好吗？",
        ),
        ReviewQueueItem(
            id="rv_002", student_name="李大爷", student_id=1002,
            stage="S2", level="L3", bpt_type="关系型", streak_days=5,
            risk_level="medium", type="prescription", type_label="行为处方",
            priority="normal", wait_time="2小时前", created_at="2026-02-17T12:30:00",
            ai_summary="李大爷连续5天完成八段锦打卡，但血糖控制不理想(空腹7.8)，AI建议将运动从早上调整到餐后30分钟，并增加步行处方。",
            rx_fields=[
                RxField(key="target", label="目标行为", value="餐后30分钟步行15分钟", placeholder="具体做什么"),
                RxField(key="frequency", label="频次剂量", value="每日午餐后 + 晚餐后", placeholder="多久一次"),
                RxField(key="time_place", label="时间地点", value="饭后30分钟，小区内步道", placeholder="何时何地"),
                RxField(key="trigger", label="启动线索", value="吃完饭放下碗筷→换鞋→出门", placeholder="提醒机制"),
                RxField(key="obstacle", label="障碍预案", value="下雨天改为室内原地踏步10分钟", placeholder="遇到困难怎么办"),
                RxField(key="support", label="支持资源", value="邀请老伴一起走", placeholder="谁来帮助(选填)"),
            ],
        ),
        ReviewQueueItem(
            id="rv_003", student_name="张叔", student_id=1003,
            stage="S3", level="L3", bpt_type="行动型", streak_days=12,
            risk_level="low", type="push", type_label="推送审核",
            priority="normal", wait_time="3小时前", created_at="2026-02-17T11:00:00",
            ai_summary="张叔连续12天全打卡，S3阶段表现稳定，运动量逐步增加。建议推送鼓励消息+挑战性任务。",
            push_type="微行动挑战",
            push_content="张叔，您连续12天的坚持太厉害了！今天试试把散步距离延长到2公里？",
        ),
    ]
    
    # 筛选
    if type_filter:
        items = [i for i in items if i.type == type_filter]
    if risk_filter:
        items = [i for i in items if i.risk_level == risk_filter]
    
    # 排序: urgent→risk→time
    risk_order = {"crisis": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda x: (0 if x.priority == "urgent" else 1, risk_order.get(x.risk_level, 9), x.created_at))
    
    return ReviewQueueResponse(
        items=items,
        total=len(items),
        pending_prescription=sum(1 for i in items if i.type == "prescription"),
        pending_ai_reply=sum(1 for i in items if i.type == "ai_reply"),
        pending_push=sum(1 for i in items if i.type == "push"),
    )


# ═══════════════════════════════════════════════════
# POST /review/{review_id}/approve
# ═══════════════════════════════════════════════════
@router.post("/review/{review_id}/approve", response_model=ReviewActionResponse)
async def approve_review(
    review_id: str = Path(...),
    req: ReviewActionRequest = ReviewActionRequest(),
    # current_user: User = Depends(require_coach_or_admin),
    # db: AsyncSession = Depends(get_db),
):
    """
    通过审核 (快捷键A)
    
    逻辑:
    1. 查找审核项
    2. 按类型执行:
       - prescription: 激活处方→生成daily_tasks→通知学员
       - ai_reply: 发送AI回复给学员(如有edited_content则用修改版)
       - push: 投递推送到学员(App+微信)
    3. 记录审核日志(coach_id, action, elapsed_seconds)
    4. 返回下一个待审项ID
    """
    # --- 实际实现 ---
    # review = await db.get(CoachReviewQueue, review_id)
    # if not review:
    #     raise HTTPException(404, "审核项不存在")
    # if review.coach_id != current_user.id:
    #     raise HTTPException(403, "非本人队列")
    #
    # elapsed = (datetime.utcnow() - review.picked_at).total_seconds()
    # review.status = "approved"
    # review.reviewed_at = datetime.utcnow()
    # review.review_note = req.note
    #
    # # 按类型执行后续
    # if review.type == "prescription":
    #     await _activate_prescription(review, req.edited_rx_fields, db)
    # elif review.type == "ai_reply":
    #     content = req.edited_content or review.ai_draft
    #     await _send_ai_reply(review.student_id, content, db)
    # elif review.type == "push":
    #     await _deliver_push(review, db)
    #
    # await db.commit()
    # next_item = await _get_next_review(current_user.id, db)
    
    return ReviewActionResponse(
        success=True,
        review_id=review_id,
        action="approve",
        next_id="rv_002",  # Mock: 下一个
        message="已通过并发送",
        elapsed_seconds=18,
    )


# ═══════════════════════════════════════════════════
# POST /review/{review_id}/reject
# ═══════════════════════════════════════════════════
@router.post("/review/{review_id}/reject", response_model=ReviewActionResponse)
async def reject_review(
    review_id: str = Path(...),
    req: ReviewActionRequest = ReviewActionRequest(),
    # current_user: User = Depends(require_coach_or_admin),
    # db: AsyncSession = Depends(get_db),
):
    """
    驳回审核 (快捷键R)
    
    逻辑:
    1. 标记为rejected
    2. 如果是prescription → 退回rx_composer Agent重新生成
    3. 如果是ai_reply → 退回Agent重新生成(附教练备注)
    4. 如果是push → 取消推送
    5. 记录审核日志
    """
    if not req.note:
        # 驳回建议填写原因(但不强制)
        pass
    
    return ReviewActionResponse(
        success=True,
        review_id=review_id,
        action="reject",
        next_id="rv_003",
        message="已驳回" + (f"，备注: {req.note}" if req.note else ""),
        elapsed_seconds=12,
    )


# ═══════════════════════════════════════════════════
# GET /stats/today
# ═══════════════════════════════════════════════════
@router.get("/stats/today", response_model=CoachStatsResponse)
async def get_coach_stats_today(
    # current_user: User = Depends(require_coach_or_admin),
    # db: AsyncSession = Depends(get_db),
):
    """
    教练今日效率统计
    
    数据源: coach_review_logs 表
    用途: CoachWorkbench.vue 顶部统计栏
    """
    # --- 实际实现 ---
    # today = date.today()
    # stmt = select(
    #     func.count(CoachReviewLog.id),
    #     func.avg(CoachReviewLog.elapsed_seconds),
    #     func.min(CoachReviewLog.elapsed_seconds),
    #     func.max(CoachReviewLog.elapsed_seconds),
    # ).where(
    #     CoachReviewLog.coach_id == current_user.id,
    #     func.date(CoachReviewLog.reviewed_at) == today,
    # )
    
    return CoachStatsResponse(
        today_reviewed=34,
        pending_count=12,
        avg_seconds=28,
        approved_count=30,
        rejected_count=4,
        approval_rate=0.88,
        my_student_count=45,
        fastest_review=8,
        slowest_review=120,
    )


# ═══════════════════════════════════════════════════
# 数据库模型参考
# ═══════════════════════════════════════════════════
"""
-- 新增 coach_review_queue 表:
CREATE TABLE coach_review_queue (
    id VARCHAR(50) PRIMARY KEY,
    coach_id INTEGER NOT NULL REFERENCES users(id),
    student_id INTEGER NOT NULL REFERENCES users(id),
    type VARCHAR(20) NOT NULL,           -- prescription | ai_reply | push
    priority VARCHAR(10) DEFAULT 'normal', -- normal | urgent
    status VARCHAR(20) DEFAULT 'pending',  -- pending | approved | rejected | skipped
    
    -- AI预填内容
    ai_summary TEXT,
    rx_fields_json JSONB,                 -- 处方六要素 JSON
    ai_draft TEXT,                         -- AI拟回复
    push_type VARCHAR(50),
    push_content TEXT,
    
    -- 审核结果
    review_note TEXT,
    edited_content TEXT,
    reviewed_at TIMESTAMP,
    elapsed_seconds INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    picked_at TIMESTAMP                    -- 教练开始审核的时间
);
CREATE INDEX idx_review_coach_status ON coach_review_queue(coach_id, status);
CREATE INDEX idx_review_priority ON coach_review_queue(priority, created_at);

-- 新增 coach_review_logs 表 (审核日志, 用于效率统计):
CREATE TABLE coach_review_logs (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL REFERENCES users(id),
    review_id VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,          -- approve | reject | skip
    elapsed_seconds INTEGER,
    reviewed_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_review_log_coach_date ON coach_review_logs(coach_id, reviewed_at);
"""
