# -*- coding: utf-8 -*-
"""
DailyTasks API — 成长者今日任务系统
/api/v1/daily-tasks/*

为 GrowerTodayHome.vue + useTaskGroups.ts + CatalogSheet.vue 提供数据。

端点:
  GET  /today              — 今日任务列表（TodayAction 格式）
  GET  /catalog            — 自选任务目录（CatalogItem 格式，按关注领域排序）
  POST /{id}/checkin       — 打卡完成任务（差异化积分，原则一铁律）
  POST /add-from-catalog   — 从目录添加自选任务（原则一 L3 + 原则四）
  DELETE /{id}             — 删除自选任务

遵循平台四原则（见 core/micro_action_service.py）:
  原则一  三来源体系（coach > rx > self）
  原则三  四维隐性数据驱动（关注领域 + 行为轨迹 + 设备 + 评估）
  原则四  AI必须先于人工（catalog 由 AI 预生成）
"""
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from core.database import get_db
from core.micro_action_service import MicroActionTaskService, DOMAIN_NAMES
from core.behavior_facts_service import BehaviorFactsService
from core.models import MicroActionTask, BehavioralProfile
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/daily-tasks", tags=["今日任务"])

task_service = MicroActionTaskService()
facts_service = BehaviorFactsService()

# ─────────────────────────────────────────────────────────────────
# 领域元数据
# ─────────────────────────────────────────────────────────────────

# domain → (tag中文, tag颜色)
DOMAIN_TAG_COLOR: Dict[str, tuple] = {
    "nutrition": ("营养", "#10b981"),
    "exercise":  ("运动", "#f59e0b"),
    "sleep":     ("睡眠", "#6366f1"),
    "emotion":   ("情绪", "#ec4899"),
    "stress":    ("压力", "#8b5cf6"),
    "cognitive": ("认知", "#3b82f6"),
    "social":    ("社交", "#0ea5e9"),
    "tcm":       ("中医", "#84cc16"),
}

# difficulty → 预估时间
DIFFICULTY_TIME: Dict[str, str] = {
    "easy": "约5分钟",
    "moderate": "约15分钟",
    "challenging": "约30分钟",
}

# domain → 输入方式（影响前端路由）
DOMAIN_INPUT_MODE: Dict[str, str] = {
    "nutrition": "photo",
    "exercise":  "device",
    "sleep":     "device",
    "emotion":   "text",
    "stress":    "text",
    "cognitive": "text",
    "social":    "text",
    "tcm":       "text",
}

# MicroActionTask.source → TodayAction.source
SOURCE_MAP: Dict[str, str] = {
    "intervention_plan": "rx",
    "ai_recommended":    "rx",
    "coach_assigned":    "coach",
    "coach":             "coach",
    "user_selected":     "self",
    "system":            "system",
}

# ─────────────────────────────────────────────────────────────────
# 静态自选任务目录（原则四：AI预生成，用户从中选取）
# ─────────────────────────────────────────────────────────────────

TASK_CATALOG: List[Dict[str, Any]] = [
    # ── 营养 ──
    {"id": "nutrition-track-meals",  "category": "营养", "default_title": "记录今日三餐",    "estimated_minutes": 5,  "difficulty": "easy",       "icon": "🥗", "description": "拍照或文字记录，培养饮食意识",          "domain": "nutrition", "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "nutrition-less-sugar",   "category": "营养", "default_title": "减少精制糖摄入",  "estimated_minutes": 0,  "difficulty": "moderate",   "icon": "🚫", "description": "今日饮料选无糖款，或减少一份甜食",    "domain": "nutrition", "points_reward": {"growth": 4, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "nutrition-more-veg",     "category": "营养", "default_title": "增加蔬菜摄入",    "estimated_minutes": 0,  "difficulty": "easy",       "icon": "🥦", "description": "每餐保证至少一种蔬菜",                "domain": "nutrition", "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "nutrition-water",        "category": "营养", "default_title": "喝够8杯水",        "estimated_minutes": 0,  "difficulty": "easy",       "icon": "💧", "description": "全天均匀补水，避免一次大量饮水",      "domain": "nutrition", "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    # ── 运动 ──
    {"id": "exercise-walk",          "category": "运动", "default_title": "饭后散步15分钟",  "estimated_minutes": 15, "difficulty": "easy",       "icon": "🚶", "description": "饭后30分钟内开始，温和启动代谢",      "domain": "exercise",  "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "exercise-stretch",       "category": "运动", "default_title": "拉伸放松5分钟",   "estimated_minutes": 5,  "difficulty": "easy",       "icon": "🧘", "description": "颈肩腰背全身拉伸，缓解久坐僵硬",      "domain": "exercise",  "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "exercise-cardio",        "category": "运动", "default_title": "有氧运动20分钟",  "estimated_minutes": 20, "difficulty": "moderate",   "icon": "🏃", "description": "快走/慢跑/骑车，心率达到中等强度",    "domain": "exercise",  "points_reward": {"growth": 5, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "exercise-strength",      "category": "运动", "default_title": "力量训练15分钟",  "estimated_minutes": 15, "difficulty": "challenging","icon": "💪", "description": "深蹲/俯卧撑/平板支撑基础力量组合",    "domain": "exercise",  "points_reward": {"growth": 7, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    # ── 睡眠 ──
    {"id": "sleep-no-phone",         "category": "睡眠", "default_title": "22:30前放下手机", "estimated_minutes": 0,  "difficulty": "moderate",   "icon": "📵", "description": "睡前1小时远离蓝光，帮助褪黑素分泌",    "domain": "sleep",     "points_reward": {"growth": 4, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "sleep-record",           "category": "睡眠", "default_title": "记录今晚入睡时间","estimated_minutes": 2,  "difficulty": "easy",       "icon": "😴", "description": "记录实际入睡时刻和睡眠质量感受",      "domain": "sleep",     "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "sleep-breathing",        "category": "睡眠", "default_title": "睡前腹式呼吸5分钟","estimated_minutes": 5, "difficulty": "easy",       "icon": "🌙", "description": "放松神经系统，提高睡眠深度",          "domain": "sleep",     "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    # ── 情绪 ──
    {"id": "emotion-breathing",      "category": "情绪", "default_title": "3分钟腹式呼吸",   "estimated_minutes": 3,  "difficulty": "easy",       "icon": "💨", "description": "4秒吸气-7秒屏息-8秒呼气，激活副交感神经","domain": "emotion",   "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "emotion-gratitude",      "category": "情绪", "default_title": "写下今日一件感恩的事","estimated_minutes": 5,"difficulty": "easy",       "icon": "🙏", "description": "感恩日记，哪怕一句话，建立积极归因习惯","domain": "emotion",   "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "emotion-awareness",      "category": "情绪", "default_title": "情绪觉察记录",    "estimated_minutes": 5,  "difficulty": "moderate",   "icon": "💭", "description": "标注当下情绪名称和触发事件，提升情绪粒度","domain": "emotion",  "points_reward": {"growth": 4, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    # ── 压力 ──
    {"id": "stress-meditation",      "category": "压力", "default_title": "5分钟正念冥想",   "estimated_minutes": 5,  "difficulty": "easy",       "icon": "🧘", "description": "专注呼吸，觉察但不评判当下感受",      "domain": "stress",    "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "stress-priority",        "category": "压力", "default_title": "写下今日三项优先任务","estimated_minutes": 3,"difficulty": "easy",      "icon": "📝", "description": "清单减轻认知负荷，降低压力焦虑",      "domain": "stress",    "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "stress-talk",            "category": "压力", "default_title": "与信任的人倾诉5分钟","estimated_minutes": 5,"difficulty": "moderate",  "icon": "🗣️", "description": "社会支持是最有效的压力缓冲",           "domain": "stress",    "points_reward": {"growth": 4, "contribution": 0, "influence": 0}, "frequency_suggestion": "as_needed"},
    # ── 认知 ──
    {"id": "cognitive-read",         "category": "认知", "default_title": "阅读行为健康内容10分钟","estimated_minutes": 10,"difficulty": "easy",    "icon": "📖", "description": "在学习中心选择感兴趣内容，积累知识积分","domain": "cognitive", "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "cognitive-journal",      "category": "认知", "default_title": "写下今日一个新认知","estimated_minutes": 5, "difficulty": "easy",       "icon": "✍️", "description": "记录学到的新观点或对旧问题的新理解",  "domain": "cognitive", "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    # ── 社交 ──
    {"id": "social-share",           "category": "社交", "default_title": "与家人分享健康行动","estimated_minutes": 5, "difficulty": "easy",       "icon": "👨‍👩‍👧", "description": "传递健康行为影响力，强化社会认同",  "domain": "social",    "points_reward": {"growth": 3, "contribution": 1, "influence": 1}, "frequency_suggestion": "daily"},
    {"id": "social-encourage",       "category": "社交", "default_title": "给同道者发一条鼓励","estimated_minutes": 2, "difficulty": "easy",       "icon": "💌", "description": "利他行为同时强化自身动机",            "domain": "social",    "points_reward": {"growth": 3, "contribution": 1, "influence": 1}, "frequency_suggestion": "daily"},
    # ── 中医 ──
    {"id": "tcm-acupoint",           "category": "中医", "default_title": "穴位按摩5分钟",   "estimated_minutes": 5,  "difficulty": "easy",       "icon": "🖐️", "description": "按揉合谷、内关等穴位，调和气血",      "domain": "tcm",       "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
    {"id": "tcm-record",             "category": "中医", "default_title": "记录今日体质感受","estimated_minutes": 3,  "difficulty": "easy",       "icon": "🌿", "description": "记录精力、消化、睡眠等中医体质指标",  "domain": "tcm",       "points_reward": {"growth": 3, "contribution": 0, "influence": 0}, "frequency_suggestion": "daily"},
]

# 目录 ID → 条目 快速查找
CATALOG_BY_ID: Dict[str, Dict] = {item["id"]: item for item in TASK_CATALOG}

# ─────────────────────────────────────────────────────────────────
# 内部转换工具
# ─────────────────────────────────────────────────────────────────

def _task_to_today_action(task: MicroActionTask, order: int) -> Dict[str, Any]:
    """MicroActionTask → TodayAction（前端格式）"""
    tag, tag_color = DOMAIN_TAG_COLOR.get(task.domain, (task.domain, "#6b7280"))
    return {
        "id": str(task.id),
        "order": order,
        "title": task.title,
        "tag": tag,
        "tag_color": tag_color,
        "time_hint": DIFFICULTY_TIME.get(task.difficulty or "easy", "约5分钟"),
        "input_mode": DOMAIN_INPUT_MODE.get(task.domain, "text"),
        "quick_label": "打卡完成",
        "done": task.status == "completed",
        "done_time": task.completed_at.strftime("%H:%M") if task.completed_at else None,
        "source": SOURCE_MAP.get(task.source or "system", "system"),
        "agent_id": None,
        "domain": task.domain,
        "difficulty": task.difficulty,
    }


# ─────────────────────────────────────────────────────────────────
# Pydantic 模型
# ─────────────────────────────────────────────────────────────────

class AddFromCatalogRequest(BaseModel):
    catalog_id: str = Field("", description="目录任务ID（空字符串表示自定义）")
    custom_title: Optional[str] = Field(None, max_length=50, description="自定义任务名（catalog_id为空时使用）")


# ─────────────────────────────────────────────────────────────────
# 端点
# ─────────────────────────────────────────────────────────────────

@router.get("/today")
async def get_today_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取今日任务列表（TodayAction 格式）

    按来源优先级排序：教练指定(coach) > AI推荐/计划(rx) > 自选(self) > 系统(system)
    包含 streak_days 连续打卡天数
    """
    try:
        tasks = task_service.get_today_tasks(db, current_user.id)
    except Exception as e:
        logger.warning(f"获取今日任务失败 user={current_user.id}: {e}")
        tasks = []

    # 按来源优先级排序
    source_priority = {"coach": 0, "rx": 1, "self": 2, "system": 3}
    def task_sort_key(t: MicroActionTask):
        src = SOURCE_MAP.get(t.source or "system", "system")
        done = 1 if t.status == "completed" else 0
        return (done, source_priority.get(src, 9))

    tasks_sorted = sorted(tasks, key=task_sort_key)

    today_actions = [
        _task_to_today_action(t, i + 1)
        for i, t in enumerate(tasks_sorted)
    ]

    # 连续打卡天数
    streak_days = 0
    try:
        facts = facts_service.get_facts(db, current_user.id)
        streak_days = facts.streak_days
    except Exception:
        pass

    return {
        "tasks": today_actions,
        "total": len(today_actions),
        "done": sum(1 for t in today_actions if t["done"]),
        "streak_days": streak_days,
    }


@router.get("/catalog")
async def get_task_catalog(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取自选任务目录（原则四：AI预生成，用户从中选取）

    按用户关注领域排序：关注领域的任务优先展示
    """
    # 获取用户关注领域（原则二）
    focus_domains: List[str] = []
    try:
        profile = db.query(BehavioralProfile).filter(
            BehavioralProfile.user_id == current_user.id
        ).first()
        if profile and profile.primary_domains:
            focus_domains = list(profile.primary_domains)
    except Exception:
        pass

    # 按关注领域排序：关注领域的任务排前面
    def catalog_sort_key(item: Dict) -> tuple:
        domain = item.get("domain", "")
        is_focus = 0 if domain in focus_domains else 1
        # 关注领域内按照关注顺序排
        focus_order = focus_domains.index(domain) if domain in focus_domains else 99
        diff_order = {"easy": 0, "moderate": 1, "challenging": 2}.get(item.get("difficulty", "easy"), 1)
        return (is_focus, focus_order, diff_order)

    sorted_catalog = sorted(TASK_CATALOG, key=catalog_sort_key)

    return {
        "items": sorted_catalog,
        "total": len(sorted_catalog),
        "focus_domains": focus_domains,
    }


@router.post("/{task_id}/checkin")
async def checkin_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    打卡完成任务（差异化积分，原则一铁律）

    积分权重：coach(5~7) > rx(4~6) > self(3~5) > system(2~4)
    同时更新连续打卡天数和 BehavioralProfile（数据闭环）
    """
    try:
        tid = int(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务ID")

    try:
        task = task_service.complete_task(db, tid, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 差异化积分（原则一）
    points = task_service.get_completion_points(task)
    points_breakdown: Dict[str, int] = {"base": points}

    try:
        from core.models import PointTransaction
        db.add(PointTransaction(
            user_id=current_user.id,
            action="micro_action_complete",
            point_type="growth",
            amount=points,
        ))
        db.commit()
    except Exception as e:
        logger.warning(f"积分记录失败: {e}")

    # 连续打卡天数
    streak_days = 0
    try:
        facts = facts_service.get_facts(db, current_user.id)
        streak_days = facts.streak_days
    except Exception:
        pass

    # 打卡反馈消息
    source_mapped = SOURCE_MAP.get(task.source or "system", "system")
    if source_mapped == "coach":
        emoji, message = "🏥", "教练指定任务完成！"
    elif source_mapped == "rx":
        emoji, message = "🤖", "AI推荐任务完成！"
    elif source_mapped == "self":
        emoji, message = "💪", "自选任务完成！"
    else:
        emoji, message = "✅", "任务完成！"

    if streak_days >= 7:
        emoji = "🔥"
        message = f"连续 {streak_days} 天！"

    return {
        "success": True,
        "points_earned": points,
        "points_breakdown": points_breakdown,
        "streak_days": streak_days,
        "emoji": emoji,
        "message": message,
        "badge_unlocked": None,
        "badge_name": "",
        "milestone_reached": "",
    }


@router.post("/add-from-catalog")
async def add_task_from_catalog(
    body: AddFromCatalogRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    从目录添加自选任务（原则一 L3 + 原则四）

    catalog_id 不为空时：从预生成目录中取 domain/title/difficulty
    catalog_id 为空时：使用 custom_title（默认 cognitive 领域，easy 难度）
    """
    if body.catalog_id and body.catalog_id in CATALOG_BY_ID:
        item = CATALOG_BY_ID[body.catalog_id]
        domain = item["domain"]
        title = item["default_title"]
        description = item.get("description", "")
        difficulty = item.get("difficulty", "easy")
        rx_id = body.catalog_id
    elif body.custom_title and body.custom_title.strip():
        # 自定义任务：归入 cognitive 领域
        domain = "cognitive"
        title = body.custom_title.strip()
        description = "用户自定义任务"
        difficulty = "easy"
        rx_id = None
    else:
        raise HTTPException(status_code=400, detail="请提供 catalog_id 或 custom_title")

    try:
        task = task_service.user_self_add_task(
            db=db,
            user_id=current_user.id,
            domain=domain,
            title=title,
            description=description,
            difficulty=difficulty,
            rx_id=rx_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "task": _task_to_today_action(task, 0),
        "message": f"已添加「{title}」",
    }


@router.delete("/{task_id}")
async def remove_self_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    删除自选任务（仅限 source=user_selected）

    coach 和 rx 来源的任务不允许用户删除
    """
    try:
        tid = int(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的任务ID")

    task = db.query(MicroActionTask).filter(
        MicroActionTask.id == tid,
        MicroActionTask.user_id == current_user.id,
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.source not in ("user_selected", "system"):
        raise HTTPException(status_code=403, detail="教练指定和AI推荐任务不可删除")

    task.status = "expired"
    db.commit()

    return {"success": True, "message": "任务已移除"}
