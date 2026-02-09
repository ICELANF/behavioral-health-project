# -*- coding: utf-8 -*-
"""
教练等级体系 API
Coach Level System API

六级四同道者体系：
L0 观察员 → L1 成长者 → L2 分享者 → L3 教练 → L4 促进师 → L5 大师

核心机制：
- 三维积分（成长/贡献/影响力）
- 四同道者晋级（L2起每级需引领4位同道者）
- 认证考核（L3起需专业认证）
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from core.database import get_db
from core.models import User, UserLearningStats, LearningTimeLog, LearningPointsLog
from api.dependencies import get_current_user
from core.learning_service import get_or_create_stats, _count_companions

router = APIRouter(prefix="/api/v1/coach-levels", tags=["教练等级体系"])


# 等级阈值（权威来源，与 learning_api.py COACH_LEVEL_REQUIREMENTS 一致）
_LEVEL_THRESHOLDS = {
    0: {"min_growth": 0, "min_contribution": 0, "min_influence": 0},
    1: {"min_growth": 100, "min_contribution": 0, "min_influence": 0},
    2: {"min_growth": 500, "min_contribution": 50, "min_influence": 0},
    3: {"min_growth": 800, "min_contribution": 200, "min_influence": 50},
    4: {"min_growth": 1500, "min_contribution": 600, "min_influence": 200},
    5: {"min_growth": 3000, "min_contribution": 1500, "min_influence": 600},
}

_LEVEL_META = {
    0: {"name": "观察员", "icon": "👀", "color": "#94a3b8"},
    1: {"name": "成长者", "icon": "🌱", "color": "#22c55e"},
    2: {"name": "分享者", "icon": "💬", "color": "#f59e0b"},
    3: {"name": "行为健康教练", "icon": "🎯", "color": "#8b5cf6"},
    4: {"name": "行为健康促进师", "icon": "⭐", "color": "#ec4899"},
    5: {"name": "行为健康促进大师", "icon": "👑", "color": "#dc2626"},
}

_COMPANION_REQS = {
    3: (4, "L1成长者", "grower"),
    4: (4, "L2分享者", "sharer"),
    5: (4, "L3教练", "coach"),
}


def _compute_user_level(stats: UserLearningStats) -> int:
    """根据三维积分计算用户当前等级"""
    level = 0
    for lvl in range(5, -1, -1):
        req = _LEVEL_THRESHOLDS[lvl]
        if (stats.growth_points >= req["min_growth"] and
            stats.contribution_points >= req["min_contribution"] and
            stats.influence_points >= req["min_influence"]):
            level = lvl
            break
    return level


# ============================================================================
# 6. 教练等级体系 API（六级四同道者）
# ============================================================================

@router.get("/levels")
async def get_coach_levels():
    """获取行为健康教练六级四同道者体系"""
    levels = [
        {
            "id": "l0",
            "name": "观察员",
            "level": 0,
            "icon": "👀",
            "color": "#94a3b8",
            "slogan": "好奇探索，初识行为健康",
            "description": "刚接触行为健康理念，正在学习和观察",
            "core_tasks": ["完成入门评估", "学习基础概念", "参与社群讨论"],
            "capabilities": ["浏览学习内容", "参与社群讨论", "完成自我评估"],
            "advancement": {
                "companions_required": 0,
                "points_required": {"growth": 100, "contribution": 0, "influence": 0},
                "conditions": ["完成「观察者入门」课程", "通过基础概念测试"]
            },
            "point_sources": {
                "growth": ["每日签到+1", "学习课程+5/节", "完成测评+10"],
                "contribution": [],
                "influence": []
            },
            "achieved": True,
            "current": False
        },
        {
            "id": "l1",
            "name": "成长者",
            "level": 1,
            "icon": "🌱",
            "color": "#22c55e",
            "slogan": "知行合一，亲身实践行为改变",
            "description": "正在亲身实践行为改变，体验行为改变的全过程",
            "core_tasks": ["完成系统课程", "每日行为打卡", "参与小组互动"],
            "capabilities": ["参与系统课程", "获得同伴支持", "查看个人数据报告"],
            "advancement": {
                "companions_required": 0,
                "points_required": {"growth": 500, "contribution": 50, "influence": 0},
                "conditions": ["完成系统课程", "实现至少3个行为目标"]
            },
            "point_sources": {
                "growth": ["课程学习+5/节", "行为打卡+3/次", "阶段考核+20"],
                "contribution": ["帮助同伴+5/次", "分享经验+3/次"],
                "influence": []
            },
            "achieved": True,
            "current": True
        },
        {
            "id": "l2",
            "name": "分享者",
            "level": 2,
            "icon": "💬",
            "color": "#f59e0b",
            "slogan": "乐于分享，帮助他人成长",
            "description": "完成课程后愿意分享经验，引领新成员入门",
            "core_tasks": ["引领4位观察员成为成长者", "分享成长故事", "参与社群答疑"],
            "capabilities": ["发布经验分享", "引领新成员", "获得分享者徽章"],
            "advancement": {
                "companions_required": 4,
                "companion_level": "L1成长者",
                "points_required": {"growth": 800, "contribution": 200, "influence": 50},
                "conditions": ["引领4位观察员成为成长者", "分享至少10篇成长故事"]
            },
            "point_sources": {
                "growth": ["持续学习+3/节", "深度复习+10/模块"],
                "contribution": ["成功引领+50/人", "经验分享+10/篇", "答疑解惑+5/次"],
                "influence": ["被点赞+1/次", "被收藏+2/次", "被引用+5/次"]
            },
            "achieved": False,
            "current": False
        },
        {
            "id": "l3",
            "name": "行为健康教练",
            "level": 3,
            "icon": "🎯",
            "color": "#8b5cf6",
            "slogan": "专业赋能，一对一陪伴成长",
            "description": "通过专业培训认证，可进行一对一行为健康辅导",
            "core_tasks": ["完成教练培训", "带领4位分享者成长", "接受督导指导"],
            "capabilities": ["一对一辅导", "带领学习小组", "获得认证证书", "收取服务费用"],
            "advancement": {
                "companions_required": 4,
                "companion_level": "L2分享者",
                "points_required": {"growth": 1500, "contribution": 600, "influence": 200},
                "conditions": ["带领4位成长者成为分享者", "完成100小时辅导实践", "通过教练认证考核"]
            },
            "point_sources": {
                "growth": ["专业培训+20/课", "案例研讨+15/次", "督导学习+30/次"],
                "contribution": ["辅导服务+20/小时", "培养分享者+100/人"],
                "influence": ["学员好评+10/次", "案例被采用+30/个"]
            },
            "certification": {
                "name": "行为健康教练认证",
                "requirements": ["完成120小时培训", "100小时实践", "通过考核"],
                "validity": "3年"
            },
            "achieved": False,
            "current": False
        },
        {
            "id": "l4",
            "name": "行为健康促进师",
            "level": 4,
            "icon": "⭐",
            "color": "#ec4899",
            "slogan": "团队引领，培育更多教练",
            "description": "培养教练团队，推动行为健康在更大范围传播",
            "core_tasks": ["督导教练成长", "带领4位教练", "开发课程内容"],
            "capabilities": ["督导教练", "开发课程", "组织培训", "区域推广"],
            "advancement": {
                "companions_required": 4,
                "companion_level": "L3教练",
                "points_required": {"growth": 3000, "contribution": 1500, "influence": 600},
                "conditions": ["培养4位分享者成为教练", "累计督导500小时", "开发至少1门课程"]
            },
            "point_sources": {
                "growth": ["高级研修+50/课", "学术研究+100/篇"],
                "contribution": ["督导教练+30/小时", "培养教练+200/人", "课程开发+500/门"],
                "influence": ["培训授课+50/次", "媒体报道+100/次"]
            },
            "certification": {
                "name": "行为健康促进师认证",
                "requirements": ["3年教练经验", "培养4名教练", "500小时督导"],
                "validity": "5年"
            },
            "achieved": False,
            "current": False
        },
        {
            "id": "l5",
            "name": "行为健康促进大师",
            "level": 5,
            "icon": "👑",
            "color": "#dc2626",
            "slogan": "行业引领，推动系统变革",
            "description": "行业领军人物，推动行为健康事业发展和社会影响",
            "core_tasks": ["引领行业发展", "培养促进师", "推动政策倡导"],
            "capabilities": ["行业引领", "政策倡导", "体系建设", "国际交流"],
            "advancement": {
                "companions_required": 4,
                "companion_level": "L4促进师",
                "points_required": {"growth": 5000, "contribution": 3000, "influence": 2000},
                "conditions": ["培养4位教练成为促进师", "累计影响10000+人", "推动至少1项行业标准"]
            },
            "point_sources": {
                "growth": ["顶级研修+100/课", "国际交流+200/次"],
                "contribution": ["培养促进师+500/人", "体系建设+1000/项"],
                "influence": ["行业演讲+100/次", "政策影响+500/项", "媒体影响+200/次"]
            },
            "certification": {
                "name": "行为健康促进大师",
                "requirements": ["5年促进师经验", "培养4名促进师", "显著行业贡献"],
                "validity": "终身"
            },
            "achieved": False,
            "current": False
        }
    ]
    return {"levels": levels}


@router.get("/modules")
async def get_coach_learning_modules(
    level: Optional[int] = None,
    category: Optional[str] = None,
    user_id: str = "test_user"
):
    """获取教练学习模块"""
    modules = [
        {
            "id": "cm1",
            "title": "行为健康教练概论",
            "description": "了解行为健康教练的角色、职责和伦理",
            "level": 0,
            "category": "foundation",
            "type": "course",
            "duration": 120,
            "points": 10,
            "completed": True,
            "progress": 100
        },
        {
            "id": "cm2",
            "title": "倾听与共情技术",
            "description": "学习有效倾听和建立共情连接的方法",
            "level": 0,
            "category": "skill",
            "type": "workshop",
            "duration": 180,
            "points": 15,
            "completed": False,
            "progress": 60
        },
        {
            "id": "cm3",
            "title": "动机访谈基础",
            "description": "掌握动机访谈的核心技术",
            "level": 1,
            "category": "skill",
            "type": "course",
            "duration": 240,
            "points": 20,
            "completed": False,
            "progress": 0
        },
        {
            "id": "cm4",
            "title": "案例督导实务",
            "description": "学习如何进行案例督导",
            "level": 2,
            "category": "supervision",
            "type": "workshop",
            "duration": 300,
            "points": 30,
            "completed": False,
            "progress": 0
        }
    ]

    if level is not None:
        modules = [m for m in modules if m["level"] == level]
    if category:
        modules = [m for m in modules if m["category"] == category]

    return {"modules": modules, "total": len(modules)}


@router.get("/progress")
def get_coach_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教练成长进度（六级四同道者体系）— 真实 DB"""
    stats = get_or_create_stats(db, current_user.id)
    current_level = _compute_user_level(stats)
    next_level = min(current_level + 1, 5)
    is_max = current_level >= 5

    next_req = _LEVEL_THRESHOLDS[next_level] if not is_max else None

    # 同道者
    comp_req = _COMPANION_REQS.get(next_level)
    comp_count = 0
    comp_required = 0
    comp_target_name = None
    if comp_req and not is_max:
        comp_required, comp_target_name, comp_target_role = comp_req
        comp_count = _count_companions(db, current_user.id, comp_target_role)

    # 徽章（基于实际里程碑）
    badges = []
    if stats.total_minutes >= 1:
        badges.append({"id": "starter", "name": "开始之旅", "icon": "🚀", "earned": True, "date": None})
    else:
        badges.append({"id": "starter", "name": "开始之旅", "icon": "🚀", "earned": False, "date": None})
    if stats.current_streak >= 7:
        badges.append({"id": "week1", "name": "坚持一周", "icon": "📆", "earned": True, "date": None})
    else:
        badges.append({"id": "week1", "name": "坚持一周", "icon": "📆", "earned": False, "date": None})
    if stats.contribution_points >= 1:
        badges.append({"id": "first_share", "name": "首次分享", "icon": "💬", "earned": True, "date": None})
    else:
        badges.append({"id": "first_share", "name": "首次分享", "icon": "💬", "earned": False, "date": None})

    cur_meta = _LEVEL_META[current_level]
    nxt_meta = _LEVEL_META[next_level] if not is_max else None

    return {
        "current_level": {
            "id": f"l{current_level}",
            "name": cur_meta["name"],
            "level": current_level,
            "icon": cur_meta["icon"],
            "color": cur_meta["color"],
        },
        "next_level": {
            "id": f"l{next_level}",
            "name": nxt_meta["name"],
            "level": next_level,
            "icon": nxt_meta["icon"],
            "color": nxt_meta["color"],
        } if nxt_meta else None,
        "points": {
            "growth": {
                "current": stats.growth_points,
                "required": next_req["min_growth"] if next_req else 0,
                "name": "成长积分", "icon": "📈",
                "description": "通过学习和实践获得",
            },
            "contribution": {
                "current": stats.contribution_points,
                "required": next_req["min_contribution"] if next_req else 0,
                "name": "贡献积分", "icon": "🤝",
                "description": "通过帮助他人获得",
            },
            "influence": {
                "current": stats.influence_points,
                "required": next_req["min_influence"] if next_req else 0,
                "name": "影响力积分", "icon": "✨",
                "description": "通过分享传播获得",
            },
        },
        "companions": {
            "required": comp_required,
            "current": comp_count,
            "target_level": comp_target_name,
            "members": [],
        },
        "badges": badges,
        "next_actions": [
            {"type": "course", "title": "完成今日课程", "points": 5, "category": "growth"},
            {"type": "checkin", "title": "行为打卡", "points": 3, "category": "growth"},
            {"type": "help", "title": "回答社群提问", "points": 5, "category": "contribution"},
        ],
        "mentorship": None,
    }


@router.get("/practice-records")
def get_practice_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取实践记录 — 真实 DB（基于学习时长日志）"""
    query = db.query(LearningTimeLog).filter(
        LearningTimeLog.user_id == current_user.id
    )
    total = query.count()
    items = query.order_by(LearningTimeLog.earned_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    total_minutes = db.query(func.coalesce(func.sum(LearningTimeLog.minutes), 0)).filter(
        LearningTimeLog.user_id == current_user.id
    ).scalar()

    records = []
    for item in items:
        records.append({
            "id": str(item.id),
            "client_name": item.domain or "学习",
            "session_date": item.earned_at.strftime("%Y-%m-%d") if item.earned_at else None,
            "duration": item.minutes,
            "type": "learning",
            "notes": f"{item.domain or '综合'}学习 {item.minutes} 分钟",
            "supervisor_feedback": None,
            "approved": True,
        })

    return {
        "records": records,
        "total_hours": round(total_minutes / 60, 1),
        "approved_hours": round(total_minutes / 60, 1),
        "total": total,
        "page": page,
    }


@router.get("/companions")
def get_companions_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取四同道者培养进度 — 真实 DB"""
    stats = get_or_create_stats(db, current_user.id)
    current_level = _compute_user_level(stats)
    next_level = min(current_level + 1, 5)
    is_max = current_level >= 5

    cur_meta = _LEVEL_META[current_level]
    nxt_meta = _LEVEL_META.get(next_level)

    # 当前等级同道者需求
    cur_comp = _COMPANION_REQS.get(current_level)
    cur_comp_required = cur_comp[0] if cur_comp else 0
    cur_comp_target = cur_comp[1] if cur_comp else None

    # 下一等级同道者需求
    nxt_comp = _COMPANION_REQS.get(next_level) if not is_max else None
    nxt_comp_required = nxt_comp[0] if nxt_comp else 0
    nxt_comp_target = nxt_comp[1] if nxt_comp else None
    nxt_comp_role = nxt_comp[2] if nxt_comp else None

    companion_descs = {
        3: "引领4位观察员完成系统课程成为成长者",
        4: "引领4位成长者成为分享者",
        5: "引领4位分享者成为教练",
    }

    # 查询实际同道者候选人
    comp_current = 0
    companion_candidates = []
    if nxt_comp_role:
        comp_current = _count_companions(db, current_user.id, nxt_comp_role)
        if hasattr(User, 'referred_by'):
            referred = db.query(User).filter(
                User.referred_by == current_user.id
            ).limit(20).all()
            for u in referred:
                r = u.role.value if hasattr(u.role, 'value') else str(u.role)
                role_levels = {
                    "observer": 0, "grower": 1, "sharer": 2, "coach": 3,
                    "promoter": 4, "supervisor": 4, "master": 5,
                }
                u_level = role_levels.get(r, 0)
                companion_candidates.append({
                    "id": str(u.id),
                    "name": u.username,
                    "avatar": "👤",
                    "current_level": u_level,
                    "level_name": _LEVEL_META.get(u_level, _LEVEL_META[0])["name"],
                    "progress": min(100, u_level * 25),
                    "joined_date": u.created_at.strftime("%Y-%m-%d") if hasattr(u, 'created_at') and u.created_at else None,
                    "status": "active" if u.is_active else "inactive",
                })

    return {
        "system_info": {
            "name": "四同道者机制",
            "description": "每位成员晋级需要引领4位同道者完成上一级别的成长",
            "principle": "通过「带人」实现自身深度成长，形成可持续的成长网络",
        },
        "my_level": {
            "level": current_level,
            "name": cur_meta["name"],
            "companions_required": cur_comp_required,
            "target_level_name": cur_comp_target,
        },
        "next_level_requirement": {
            "level": next_level,
            "name": nxt_meta["name"],
            "companions_required": nxt_comp_required,
            "target_level_name": nxt_comp_target,
            "description": companion_descs.get(next_level, ""),
        } if not is_max and nxt_comp_required > 0 else None,
        "my_companions": [],
        "companion_candidates": companion_candidates,
        "network_stats": {
            "total_influenced": len(companion_candidates),
            "direct_companions": comp_current,
            "indirect_companions": 0,
        },
    }


@router.get("/overview")
async def get_six_level_overview():
    """获取六级体系概览"""
    return {
        "system_name": "行为健康教练六级体系",
        "slogan": "人人成为行为健康的促进者",
        "core_mechanism": "四同道者",
        "description": "通过六级成长路径，从观察者到大师，每一级都通过培养4位同道者实现晋级，形成可持续发展的行为健康促进网络",
        "levels_summary": [
            {"level": 0, "name": "观察员", "icon": "👀", "focus": "学习观察", "color": "#94a3b8"},
            {"level": 1, "name": "成长者", "icon": "🌱", "focus": "亲身实践", "color": "#22c55e"},
            {"level": 2, "name": "分享者", "icon": "💬", "focus": "经验传承", "color": "#f59e0b"},
            {"level": 3, "name": "行为健康教练", "icon": "🎯", "focus": "专业辅导", "color": "#8b5cf6"},
            {"level": 4, "name": "行为健康促进师", "icon": "⭐", "focus": "团队引领", "color": "#ec4899"},
            {"level": 5, "name": "行为健康促进大师", "icon": "👑", "focus": "行业引领", "color": "#dc2626"}
        ],
        "point_types": [
            {"id": "growth", "name": "成长积分", "icon": "📈", "description": "通过学习和自我实践获得", "color": "#22c55e"},
            {"id": "contribution", "name": "贡献积分", "icon": "🤝", "description": "通过帮助他人成长获得", "color": "#3b82f6"},
            {"id": "influence", "name": "影响力积分", "icon": "✨", "description": "通过传播和社会影响获得", "color": "#f59e0b"}
        ],
        "growth_path": {
            "entry": "任何人都可以从观察员开始",
            "advancement": "完成当前级别任务 + 培养4位同道者",
            "ultimate_goal": "推动行为健康成为社会共识"
        }
    }


# 导出路由
__all__ = ["router"]
