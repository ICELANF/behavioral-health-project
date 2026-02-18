"""
Grower 飞轮 API — 今日行动 + 打卡 + 连续天数
端点:
  GET  /api/v1/daily-tasks/today          → 今日行动列表
  POST /api/v1/daily-tasks/:id/checkin    → 任务打卡
  GET  /api/v1/user/streak                → 连续天数
  GET  /api/v1/coach-tip/today            → AI教练一句话
  GET  /api/v1/weekly-summary             → 本周一览
"""

from datetime import date, datetime, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

# from database import get_db
# from dependencies import get_current_user
# from models import User, DailyTask, TaskCheckin, UserStreak
# from sqlalchemy import select, func, and_
# from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["grower-flywheel"])


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════
class TodayAction(BaseModel):
    """今日行动项"""
    id: str
    order: int
    title: str
    tag: str                     # 营养 | 监测 | 运动 | 睡眠 | 情绪 | 学习
    tag_color: str               # hex color
    time_hint: str               # 时间提示 e.g. "7:00-9:00"
    input_mode: Optional[str] = None  # photo | voice | text | device
    quick_label: str = "打卡"
    done: bool = False
    done_time: Optional[str] = None   # HH:MM
    source: str = "rx"           # rx(处方生成) | manual(手动) | system(系统)
    agent_id: Optional[str] = None    # 关联的Agent ID


class TodayTasksResponse(BaseModel):
    """今日行动列表响应"""
    date: str
    tasks: list[TodayAction]
    done_count: int
    total_count: int
    completion_pct: int
    streak_days: int


class CheckinRequest(BaseModel):
    """打卡请求"""
    note: Optional[str] = None        # 文字备注
    photo_url: Optional[str] = None   # 图片URL (食物拍照)
    value: Optional[float] = None     # 数值 (血糖/步数)
    voice_url: Optional[str] = None   # 语音URL


class CheckinResponse(BaseModel):
    """打卡响应"""
    success: bool
    task_id: str
    done_time: str
    streak_days: int
    message: str                      # 即时反馈文案
    emoji: str                        # 反馈emoji
    points_earned: int = 0            # 获得积分
    badge_unlocked: Optional[str] = None  # 解锁徽章


class StreakResponse(BaseModel):
    """连续天数"""
    current_streak: int
    longest_streak: int
    today_completed: bool
    last_checkin_date: Optional[str] = None


class CoachTipResponse(BaseModel):
    """AI教练一句话"""
    tip: str
    tip_type: str       # encouragement | insight | suggestion | celebration
    agent_id: str       # 生成此tip的Agent


class WeekDay(BaseModel):
    """本周单日"""
    label: str          # 一/二/三...
    date: str           # YYYY-MM-DD
    status: str         # full | partial | today | future | missed


class WeeklySummaryResponse(BaseModel):
    """本周一览"""
    days: list[WeekDay]
    week_completion_pct: int
    best_day: Optional[str] = None


# ═══════════════════════════════════════════════════
# 标签颜色映射
# ═══════════════════════════════════════════════════
TAG_COLORS = {
    "营养": "#f59e0b",
    "监测": "#3b82f6",
    "运动": "#10b981",
    "睡眠": "#8b5cf6",
    "情绪": "#ec4899",
    "学习": "#6366f1",
}

# 即时反馈库
CHECKIN_FEEDBACK = [
    {"emoji": "🎉", "message": "太棒了！"},
    {"emoji": "💪", "message": "做到了！"},
    {"emoji": "✨", "message": "继续保持！"},
    {"emoji": "🔥", "message": "又进一步！"},
    {"emoji": "👏", "message": "好样的！"},
    {"emoji": "🏆", "message": "全部完成！"},
    {"emoji": "⭐", "message": "坚持就是胜利！"},
]


# ═══════════════════════════════════════════════════
# GET /daily-tasks/today
# ═══════════════════════════════════════════════════
@router.get("/daily-tasks/today", response_model=TodayTasksResponse)
async def get_today_tasks(
    # current_user: User = Depends(get_current_user),
    # db: AsyncSession = Depends(get_db),
):
    """
    获取今日行动列表
    
    生成逻辑 (由 scheduler_agent 每日凌晨生成):
    1. 查询用户当前活跃的行为处方 (behavior_prescriptions WHERE status='active')
    2. 按处方的 frequency_dose 生成今日任务
    3. 加入系统级任务 (血糖监测等, 来自 monitoring_plans)
    4. 按时间排序
    5. 关联已完成的打卡记录
    
    数据流: InterventionPlanner → behavior_prescriptions → scheduler_agent → daily_tasks
    """
    # --- 实际实现时: 查询daily_tasks表 ---
    # today = date.today()
    # stmt = select(DailyTask).where(
    #     DailyTask.user_id == current_user.id,
    #     DailyTask.task_date == today,
    # ).order_by(DailyTask.order)
    # result = await db.execute(stmt)
    # tasks = result.scalars().all()
    
    # --- Mock 数据 ---
    tasks = [
        TodayAction(
            id="dt_001", order=1, title="记录早餐",
            tag="营养", tag_color=TAG_COLORS["营养"], time_hint="7:00-9:00",
            input_mode="photo", quick_label="拍照",
            done=True, done_time="07:42", source="rx", agent_id="nutrition_guide",
        ),
        TodayAction(
            id="dt_002", order=2, title="晨起血糖测量",
            tag="监测", tag_color=TAG_COLORS["监测"], time_hint="空腹",
            input_mode="device", quick_label="记录",
            done=True, done_time="06:58", source="system", agent_id="health_assistant",
        ),
        TodayAction(
            id="dt_003", order=3, title="八段锦第三式 · 调理脾胃须单举",
            tag="运动", tag_color=TAG_COLORS["运动"], time_hint="10分钟",
            input_mode="voice", quick_label="开始",
            done=False, source="rx", agent_id="tcm_exercise_guide",
        ),
        TodayAction(
            id="dt_004", order=4, title="记录午餐",
            tag="营养", tag_color=TAG_COLORS["营养"], time_hint="12:00-13:00",
            input_mode="photo", quick_label="拍照",
            done=False, source="rx", agent_id="nutrition_guide",
        ),
        TodayAction(
            id="dt_005", order=5, title="下午散步15分钟",
            tag="运动", tag_color=TAG_COLORS["运动"], time_hint="14:00-16:00",
            input_mode="device", quick_label="打卡",
            done=False, source="rx", agent_id="exercise_guide",
        ),
    ]
    
    done_count = sum(1 for t in tasks if t.done)
    total_count = len(tasks)
    
    return TodayTasksResponse(
        date=date.today().isoformat(),
        tasks=tasks,
        done_count=done_count,
        total_count=total_count,
        completion_pct=int(done_count / total_count * 100) if total_count > 0 else 0,
        streak_days=7,  # Mock
    )


# ═══════════════════════════════════════════════════
# POST /daily-tasks/{task_id}/checkin
# ═══════════════════════════════════════════════════
@router.post("/daily-tasks/{task_id}/checkin", response_model=CheckinResponse)
async def checkin_task(
    task_id: str = Path(..., description="任务ID"),
    req: CheckinRequest = CheckinRequest(),
    # current_user: User = Depends(get_current_user),
    # db: AsyncSession = Depends(get_db),
):
    """
    任务打卡
    
    逻辑:
    1. 查找任务, 验证归属和未完成状态
    2. 创建 TaskCheckin 记录 (含多模态数据引用)
    3. 标记任务完成, 记录完成时间
    4. 更新连续天数 (UserStreak)
    5. 计算积分奖励
    6. 检查徽章解锁条件
    7. 如果是最后一个任务 → 额外庆祝反馈
    8. 触发 habit_tracker Agent 记录行为数据
    """
    # --- 实际实现 ---
    # task = await db.get(DailyTask, task_id)
    # if not task or task.user_id != current_user.id:
    #     raise HTTPException(404, "任务不存在")
    # if task.done:
    #     raise HTTPException(400, "任务已完成")
    #
    # # 创建打卡记录
    # checkin = TaskCheckin(
    #     task_id=task_id,
    #     user_id=current_user.id,
    #     note=req.note,
    #     photo_url=req.photo_url,
    #     value=req.value,
    #     voice_url=req.voice_url,
    #     checked_at=datetime.utcnow(),
    # )
    # db.add(checkin)
    #
    # # 标记完成
    # task.done = True
    # task.done_time = datetime.utcnow().strftime("%H:%M")
    #
    # # 更新连续天数
    # streak = await _update_streak(db, current_user.id)
    #
    # # 积分
    # points = _calculate_checkin_points(task)
    # current_user.growth_points += points
    #
    # await db.commit()
    
    # --- Mock ---
    now = datetime.now().strftime("%H:%M")
    streak = 8  # 模拟连续8天
    points = 10

    # 全部完成检测
    # all_done = await _check_all_done(db, current_user.id, date.today())
    all_done = False  # Mock

    # 个性化反馈 (替代原 random.choice)
    feedback = _build_personalized_feedback(
        streak_days=streak, task_tag="运动", all_done=all_done,
    )
    if all_done:
        points = 50  # 全完成额外奖励
    
    return CheckinResponse(
        success=True,
        task_id=task_id,
        done_time=now,
        streak_days=streak,
        message=feedback["message"],
        emoji=feedback["emoji"],
        points_earned=points,
        badge_unlocked=None,  # TODO: 徽章解锁检测
    )


# ═══════════════════════════════════════════════════
# GET /user/streak
# ═══════════════════════════════════════════════════
@router.get("/user/streak", response_model=StreakResponse)
async def get_user_streak(
    # current_user: User = Depends(get_current_user),
    # db: AsyncSession = Depends(get_db),
):
    """
    获取用户连续天数
    
    计算逻辑:
    1. 从今天往回查, 连续每天至少完成1个任务 = 连续天数
    2. 历史最长连续天数存在 user_streaks 表
    """
    # --- 实际实现 ---
    # streak_record = await db.execute(
    #     select(UserStreak).where(UserStreak.user_id == current_user.id)
    # )
    # streak = streak_record.scalar_one_or_none()
    
    return StreakResponse(
        current_streak=7,
        longest_streak=14,
        today_completed=False,  # 今天还有未完成任务
        last_checkin_date=date.today().isoformat(),
    )


# ═══════════════════════════════════════════════════
# GET /coach-tip/today
# ═══════════════════════════════════════════════════
@router.get("/coach-tip/today", response_model=CoachTipResponse)
async def get_coach_tip_today(
    # current_user: User = Depends(get_current_user),
    # db: AsyncSession = Depends(get_db),
):
    """
    AI教练今日一句话
    
    生成逻辑 (由 health_assistant Agent 生成):
    1. 获取用户最近7天行为数据 (打卡/设备/对话)
    2. 通过 progress_analyzer Agent 分析趋势
    3. 根据当前阶段(S0-S6)和心理层级(L1-L5)选择话术风格:
       - S0-S1 / L1-L2: 共情型 → "你已经在努力了"
       - S2-S3 / L3: 洞察型 → "你的步数比上周多了800步"
       - S4-S6 / L4-L5: 建议型 → "试试今天换一条新路线？"
    4. 缓存到Redis, key=f"coach_tip:{user_id}:{date}", TTL=24h
    """
    # --- 实际实现: 调用Agent或读缓存 ---
    # cache_key = f"coach_tip:{current_user.id}:{date.today().isoformat()}"
    # cached = await redis.get(cache_key)
    # if cached:
    #     return CoachTipResponse(**json.loads(cached))
    #
    # # 调用 health_assistant Agent
    # from core.agents.user_agents.health_assistant import generate_daily_tip
    # tip_data = await generate_daily_tip(current_user.id, db)
    # await redis.setex(cache_key, 86400, json.dumps(tip_data))
    
    return CoachTipResponse(
        tip="昨天的步数比前天多了800步，今天试试走一个新路线？",
        tip_type="insight",
        agent_id="health_assistant",
    )


# ═══════════════════════════════════════════════════
# GET /weekly-summary
# ═══════════════════════════════════════════════════
@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def get_weekly_summary(
    # current_user: User = Depends(get_current_user),
    # db: AsyncSession = Depends(get_db),
):
    """
    本周一览 (7天完成情况)
    
    逻辑:
    1. 获取本周一到周日的每日任务
    2. 每天: 全部完成=full, 部分完成=partial, 未完成=missed, 今天=today, 未来=future
    3. 计算周完成率
    """
    today = date.today()
    monday = today - timedelta(days=today.weekday())  # 本周一
    labels = ["一", "二", "三", "四", "五", "六", "日"]
    
    # --- 实际实现: 查询每日完成情况 ---
    # for i in range(7):
    #     d = monday + timedelta(days=i)
    #     stmt = select(DailyTask).where(
    #         DailyTask.user_id == current_user.id,
    #         DailyTask.task_date == d,
    #     )
    #     ...
    
    # --- Mock ---
    mock_statuses = ["full", "full", "partial", "full", "today", "future", "future"]
    days = []
    for i in range(7):
        d = monday + timedelta(days=i)
        if d > today:
            status = "future"
        elif d == today:
            status = "today"
        else:
            status = mock_statuses[i]
        
        days.append(WeekDay(
            label=labels[i],
            date=d.isoformat(),
            status=status,
        ))
    
    completed_days = sum(1 for d in days if d.status == "full")
    past_days = sum(1 for d in days if d.status in ("full", "partial", "missed", "today"))
    
    return WeeklySummaryResponse(
        days=days,
        week_completion_pct=int(completed_days / max(past_days, 1) * 100),
        best_day="一" if completed_days > 0 else None,
    )


# ═══════════════════════════════════════════════════
# 内部辅助函数
# ═══════════════════════════════════════════════════
def _build_personalized_feedback(
    streak_days: int, task_tag: str, all_done: bool,
) -> dict:
    """
    个性化打卡反馈 — 替代原 random.choice(CHECKIN_FEEDBACK)

    优先级: 里程碑 > 全部完成 > tag匹配 > 降级random
    """
    # 里程碑天数
    milestones = {7: "🔥", 14: "⭐", 21: "💪", 30: "🏆", 60: "🎉", 90: "👑"}
    if streak_days in milestones:
        return {
            "emoji": milestones[streak_days],
            "message": f"连续{streak_days}天！您的坚持正在改变生活。",
        }

    # 全部完成
    if all_done:
        return {"emoji": "🏆", "message": "今天全部完成！太厉害了！"}

    # 基于tag的反馈
    tag_feedback = {
        "营养": {"emoji": "🥗", "message": "记录饮食是改变的第一步！"},
        "运动": {"emoji": "🏃", "message": "动起来了！身体会感谢您的。"},
        "监测": {"emoji": "📊", "message": "数据记录好了，心里有数！"},
        "睡眠": {"emoji": "😴", "message": "关注睡眠，身体会慢慢好起来。"},
        "情绪": {"emoji": "💚", "message": "关注自己的感受，这很重要。"},
    }
    if task_tag in tag_feedback:
        return tag_feedback[task_tag]

    # 降级: random
    import random
    return random.choice(CHECKIN_FEEDBACK)


def _calculate_checkin_points(task_tag: str) -> int:
    """根据任务类型计算积分"""
    base_points = {
        "营养": 10,
        "监测": 10,
        "运动": 15,
        "睡眠": 10,
        "情绪": 10,
        "学习": 5,
    }
    return base_points.get(task_tag, 10)


# ═══════════════════════════════════════════════════
# 数据库模型参考
# ═══════════════════════════════════════════════════
"""
-- daily_tasks 表已存在, 需扩展字段:
ALTER TABLE daily_tasks ADD COLUMN input_mode VARCHAR(20);   -- photo|voice|text|device
ALTER TABLE daily_tasks ADD COLUMN quick_label VARCHAR(20) DEFAULT '打卡';
ALTER TABLE daily_tasks ADD COLUMN agent_id VARCHAR(50);     -- 关联Agent
ALTER TABLE daily_tasks ADD COLUMN source VARCHAR(20) DEFAULT 'rx';  -- rx|manual|system

-- 新增 task_checkins 表:
CREATE TABLE task_checkins (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    note TEXT,
    photo_url VARCHAR(500),
    value FLOAT,
    voice_url VARCHAR(500),
    checked_at TIMESTAMP DEFAULT NOW(),
    points_earned INTEGER DEFAULT 0
);
CREATE INDEX idx_checkin_user_date ON task_checkins(user_id, checked_at);

-- 新增 user_streaks 表:
CREATE TABLE user_streaks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_checkin_date DATE,
    updated_at TIMESTAMP DEFAULT NOW()
);
"""
