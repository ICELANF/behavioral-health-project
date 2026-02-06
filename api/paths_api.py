# -*- coding: utf-8 -*-
"""
六大路径 API
Six Growth Paths API

路径体系：
1. 项目型干预 (intervention) - 三见六段五层课程
2. 专家/医疗支持 (expert) - 专家资源库
3. 认知学习 (knowledge) - 知识内容体系
4. 低门槛实践 (practice) - 成长者活动
5. 社群陪伴 (community) - 三层支持网络
6. 教练成长 (coach) - 教练培养体系
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from loguru import logger

router = APIRouter(prefix="/api/v1/paths", tags=["六大路径"])


# ============================================================================
# 路径元数据
# ============================================================================

PATH_METADATA = {
    "intervention": {
        "id": "intervention",
        "name": "项目型干预路径",
        "subtitle": "有计划、有节奏、有反馈、有陪伴",
        "description": "通过结构化的「三见六段五层」课程体系，在专业人士陪伴下共同成长为自己应该成为的样子。",
        "icon": "🎯",
        "color": "#8b5cf6",
        "features": ["系统课程", "专家咨询", "行为任务", "进度追踪"],
        "suitable_for": ["想要系统改善的人", "需要专业指导的人", "愿意投入时间的人"],
        "estimated_duration": "12-24周",
        "difficulty": "hard"
    },
    "expert": {
        "id": "expert",
        "name": "专家/医疗支持路径",
        "subtitle": "有些问题需要专业力量",
        "description": "连接心理、营养、运动、睡眠等领域的专业专家，获得一对一的专业支持。",
        "icon": "🧠",
        "color": "#ec4899",
        "features": ["专家资源库", "在线预约", "1对1咨询", "跟进建议"],
        "suitable_for": ["需要专业评估的人", "情况较复杂的人", "希望快速获得帮助的人"],
        "difficulty": "medium"
    },
    "knowledge": {
        "id": "knowledge",
        "name": "认知学习路径",
        "subtitle": "先理解，再行动",
        "description": "通过系统的学习内容，理解行为健康的理念、知识、方法和真实案例。",
        "icon": "📚",
        "color": "#3b82f6",
        "features": ["理念篇", "知识篇", "方法篇", "案例篇"],
        "suitable_for": ["喜欢先了解原理的人", "自主学习能力强的人", "想打好基础的人"],
        "estimated_duration": "自主安排",
        "difficulty": "easy"
    },
    "practice": {
        "id": "practice",
        "name": "低门槛实践路径",
        "subtitle": "不用改变生活，先改变一个动作",
        "description": "从2分钟微行动开始，通过打卡活动和挑战赛，轻松养成健康习惯。",
        "icon": "🎮",
        "color": "#22c55e",
        "features": ["每日微行动", "主题打卡", "挑战赛", "成就徽章"],
        "suitable_for": ["时间有限的人", "想要轻松开始的人", "喜欢游戏化的人"],
        "estimated_duration": "每天2-10分钟",
        "difficulty": "easy"
    },
    "community": {
        "id": "community",
        "name": "社群陪伴路径",
        "subtitle": "不是一个人在改变",
        "description": "加入支持社群，与有相似经历的同伴互助，或向专业人士寻求帮助。",
        "icon": "🤝",
        "color": "#f59e0b",
        "features": ["同伴支持", "同业互助", "专家连接", "社群活动"],
        "suitable_for": ["希望获得支持的人", "喜欢分享交流的人", "想帮助他人的人"],
        "difficulty": "easy"
    },
    "coach": {
        "id": "coach",
        "name": "教练成长路径",
        "subtitle": "你的经验本身就是力量",
        "description": "进入教练培养体系，通过分级学习和实践，成为帮助他人的行为健康教练。",
        "icon": "🎓",
        "color": "#6366f1",
        "features": ["分级课程", "实践训练", "导师督导", "认证考核"],
        "suitable_for": ["有助人意愿的人", "想发展事业的人", "有相关经验的人"],
        "estimated_duration": "6-12个月",
        "difficulty": "hard"
    }
}

# ============================================================================
# 三见六段五层课程体系定义
# ============================================================================

# 三见（三大阶段）
THREE_INSIGHTS = {
    "health_visible": {
        "id": "health_visible",
        "name": "健康看得见",
        "english_name": "Health Visible",
        "order": 1,
        "months": "1-2月",
        "color": "#3b82f6",
        "icon": "👁️",
        "theme": "让身体和行为改善变成「看得见」的体验",
        "core_tasks": ["建立身体基线", "看见自己的模式", "获得可见的身体改善与行为小胜利"],
        "modules": ["A", "B", "C"]
    },
    "change_visible": {
        "id": "change_visible",
        "name": "改变看得见",
        "english_name": "Change Visible",
        "order": 2,
        "months": "3-4月",
        "color": "#8b5cf6",
        "icon": "🔄",
        "theme": "生命节奏建立 + 行为模式改变 + 身份开始松动",
        "core_tasks": ["从做到变成我就是这样的人", "生命节奏建立", "身份松动"],
        "modules": ["D", "E"]
    },
    "growth_visible": {
        "id": "growth_visible",
        "name": "成长看得见",
        "english_name": "Growth Visible",
        "order": 3,
        "months": "5-6月",
        "color": "#f59e0b",
        "icon": "🌱",
        "theme": "主动生命者 × 不反弹生活方式 × 生命脚本重写",
        "core_tasks": ["成为主动生命实践者", "建立不反弹系统", "生命脚本重写"],
        "modules": ["F", "G"]
    }
}

# 六段定义（从三见演化而来的六个阶段）
SIX_STAGES = [
    {"id": "see_status", "name": "看见现状", "english_name": "See Status", "order": 1, "phase": "health_visible", "description": "建立身体基线，看见当前状态"},
    {"id": "see_pattern", "name": "看见模式", "english_name": "See Pattern", "order": 2, "phase": "health_visible", "description": "识别行为触发链、奖励链、情绪链"},
    {"id": "see_possible", "name": "看见可能", "english_name": "See Possible", "order": 3, "phase": "health_visible", "description": "发现改变的可能性，建立稳态系统"},
    {"id": "see_value", "name": "看见价值", "english_name": "See Value", "order": 4, "phase": "change_visible", "description": "理解改变的意义，激活价值链"},
    {"id": "see_power", "name": "看见力量", "english_name": "See Power", "order": 5, "phase": "growth_visible", "description": "发现内在力量，建立身份认同"},
    {"id": "see_future", "name": "看见未来", "english_name": "See Future", "order": 6, "phase": "growth_visible", "description": "规划未来三年，建立LifeOS系统"}
]

# 五层定义
FIVE_LAYERS = [
    {"id": "body", "name": "身体层", "icon": "💪", "order": 1, "description": "CGM/HRV/体成分/睡眠等身体数据"},
    {"id": "behavior", "name": "行为层", "icon": "🎯", "order": 2, "description": "行为触发链、奖励链、习惯系统"},
    {"id": "cognition", "name": "认知层", "icon": "🧠", "order": 3, "description": "思维模式、解释风格、信念系统"},
    {"id": "identity", "name": "身份层", "icon": "👤", "order": 4, "description": "自我认同、角色觉察、身份转变"},
    {"id": "life", "name": "生命层", "icon": "🌟", "order": 5, "description": "生命脚本、价值系统、未来愿景"}
]

# 六大维度
SIX_DIMENSIONS = [
    {"id": "nutrition", "name": "营养", "icon": "🥗", "color": "#22c55e"},
    {"id": "exercise", "name": "运动", "icon": "🏃", "color": "#3b82f6"},
    {"id": "cognition", "name": "认知", "icon": "🧠", "color": "#8b5cf6"},
    {"id": "sleep", "name": "睡眠", "icon": "😴", "color": "#6366f1"},
    {"id": "support", "name": "社会支持", "icon": "🤝", "color": "#f59e0b"},
    {"id": "barrier", "name": "障碍因素", "icon": "🚧", "color": "#ef4444"}
]

# 七大模块详细定义
INTERVENTION_MODULES = {
    "A": {
        "id": "A",
        "name": "3天强化营",
        "phase": "health_visible",
        "timing": "第1月 · 第1周",
        "duration_days": 3,
        "theme": "看见身体和行为",
        "description": "进入第一段「看见现状」，启动第二段「看见模式」",
        "days": [
            {
                "day": 1,
                "title": "看见身体",
                "layer": "body",
                "content": [
                    "CGM实时曲线演示：吃什么、情绪、压力怎么影响血糖",
                    "HRV压力测试：5分钟看到压力对行为的影响",
                    "体成分基线建立",
                    "睡眠节律现状图",
                    "五大基线图建立：CGM 24h、体成分、情绪链、行为雷达、炎症/体温"
                ],
                "outcome": "身体立即反馈，建立可视化基线"
            },
            {
                "day": 2,
                "title": "看见模式",
                "layer": "behavior",
                "content": [
                    "生存路径依赖分析",
                    "情绪–需要链识别",
                    "行为触发链与奖励链",
                    "饮食链：触发→选择→摄入→血糖反馈→情绪",
                    "运动链：触发→动机→执行→肌肉能量感",
                    "睡眠链分析"
                ],
                "outcome": "行为背后的模式可视化"
            },
            {
                "day": 3,
                "title": "让改变变得可能",
                "layer": "behavior",
                "content": [
                    "立即有效的三个行为：稳糖早餐、餐后步行、呼吸节律",
                    "个人行动处方（A/B/C版本）",
                    "个人行为链AB测试",
                    "制定21天行为链觉察训练计划"
                ],
                "outcome": "找到可马上见效的行为"
            }
        ]
    },
    "B": {
        "id": "B",
        "name": "21天行为链觉察训练营",
        "phase": "health_visible",
        "timing": "第1月 · 第2-4周",
        "duration_days": 21,
        "theme": "看见模式 → 看见可能",
        "description": "通过每日行为链记录，建立觉察习惯",
        "tools": ["行为链记录卡", "CGM曲线叠加", "习惯雷达图"],
        "weeks": [
            {
                "week": 1,
                "title": "饮食链觉察",
                "dimension": "nutrition",
                "focus": "营养 × 情绪",
                "tasks": ["稳糖早餐", "餐后血糖可视化", "情绪性进食觉察", "饥饿–情绪–血糖三点共现图"]
            },
            {
                "week": 2,
                "title": "运动链觉察",
                "dimension": "exercise",
                "focus": "运动 × 行为",
                "tasks": ["3000步餐后实验", "15分钟力量基础", "肌肉量与血糖敏感性关系图", "动一点就见效可视化"]
            },
            {
                "week": 3,
                "title": "睡眠链觉察",
                "dimension": "sleep",
                "focus": "睡眠 × 压力 × 代谢",
                "tasks": ["90分钟节律练习", "HRV稳定计划", "晚间行为链拆解", "第二版行为画像形成"]
            }
        ]
    },
    "C": {
        "id": "C",
        "name": "健康稳态系统",
        "phase": "health_visible",
        "timing": "第2月",
        "duration_days": 30,
        "theme": "从改善到稳定",
        "description": "建立四大稳定模块，形成健康稳态",
        "modules": [
            {"name": "稳糖稳定", "dimension": "nutrition", "description": "营养摄入与血糖稳定"},
            {"name": "稳定运动节律", "dimension": "exercise", "description": "运动习惯与身体适应"},
            {"name": "睡眠节奏重建", "dimension": "sleep", "description": "睡眠质量与生物钟"},
            {"name": "情绪稳定 × 压力管理", "dimension": "cognition", "description": "认知调节与障碍因素处理"}
        ],
        "outcomes": ["第一版个人健康看得见报告", "三条稳定行为链", "身体证据改善"]
    },
    "D": {
        "id": "D",
        "name": "5天生命升级集训",
        "phase": "change_visible",
        "timing": "第3月 · 第1周",
        "duration_days": 5,
        "theme": "行为模式识别 × 生命故事分享",
        "description": "从做到变成我就是这样的人",
        "days": [
            {
                "day": 1,
                "title": "生命地图",
                "layer": "cognition",
                "content": ["行为来源于故事，故事来源于生存模式", "三类故事：匮乏—恐惧—应对", "CGM × 情绪 × 生存模式联动图"]
            },
            {
                "day": 2,
                "title": "角色觉察",
                "layer": "identity",
                "content": ["内在角色识别：批评者/回避者/超责任者/放弃者等", "情绪–需要链", "行为–角色依赖循环"]
            },
            {
                "day": 3,
                "title": "行为模式拆解",
                "layer": "behavior",
                "content": ["反复失败的四种行为链识别", "如何重写行为链", "身份链训练"]
            },
            {
                "day": 4,
                "title": "生命故事分享",
                "layer": "cognition",
                "content": ["我是什么模式", "我为什么总卡在这里", "我如何走出老故事"]
            },
            {
                "day": 5,
                "title": "生命节奏设计",
                "layer": "cognition",
                "content": ["生活方式五环节结构化", "改变为什么对我重要？", "价值链激活", "未来30天计划"]
            }
        ]
    },
    "E": {
        "id": "E",
        "name": "生命节奏觉察实践",
        "phase": "change_visible",
        "timing": "第3-4月",
        "duration_days": 60,
        "theme": "行为链系统化 + 五大生活方式模块",
        "description": "两个月的持续实践，让行为系统化",
        "components": [
            {
                "name": "行为链系统化",
                "items": ["A/B/C版本行为处方", "障碍因素处理", "五大障碍 × 五大重构路径"]
            },
            {
                "name": "五大生活方式模块",
                "items": [
                    "1）稳糖营养节奏",
                    "2）运动能力成长：从动不动到能动",
                    "3）睡眠90分钟节奏",
                    "4）认知自我觉察（思维链/解释风格）",
                    "5）社会支持系统（同伴—教练—复位机制）"
                ]
            }
        ],
        "outcomes": ["行为可预测", "身体第二次显著改善", "身份松动"]
    },
    "F": {
        "id": "F",
        "name": "5天集训：成长看得见",
        "phase": "growth_visible",
        "timing": "第5月 · 第1周",
        "duration_days": 5,
        "theme": "成为主动生命实践者 + 不反弹故事分享",
        "description": "从改变走向成长，从行为走向生命",
        "days": [
            {
                "day": 1,
                "title": "身份升级",
                "layer": "identity",
                "content": ["我是谁→我如何活出我是谁", "行为稳定性来源于身份", "身份链：证据—行为—身份"]
            },
            {
                "day": 2,
                "title": "不反弹系统",
                "layer": "body",
                "content": ["代谢稳定系统", "肌肉量 × 胰岛素敏感性 × 生活节奏", "反弹的五大根因与五大修复路径"]
            },
            {
                "day": 3,
                "title": "生命脚本识别",
                "layer": "life",
                "content": ["生存脚本", "家庭脚本", "成就脚本", "情绪脚本"]
            },
            {
                "day": 4,
                "title": "生命脚本重写",
                "layer": "life",
                "content": ["我过去为何如此", "我要怎样活", "结构化脚本重写练习"]
            },
            {
                "day": 5,
                "title": "未来三年LifeOS",
                "layer": "life",
                "content": ["行为系统", "健康系统", "关系系统", "成长系统", "抗路径依赖（换轨能力）"]
            }
        ]
    },
    "G": {
        "id": "G",
        "name": "成为主动生命实践者",
        "phase": "growth_visible",
        "timing": "第5-6月",
        "duration_days": 60,
        "theme": "主动生命者五大能力 + 五环生活方式系统",
        "description": "最终阶段，建立可持续的生活方式系统",
        "five_abilities": [
            {"name": "节律稳定", "icon": "⏰"},
            {"name": "能量稳定", "icon": "⚡"},
            {"name": "情绪稳定", "icon": "💚"},
            {"name": "关系稳定", "icon": "🤝"},
            {"name": "行动可持续", "icon": "🔄"}
        ],
        "lifestyle_system": [
            "营养智能化",
            "运动可持续化",
            "睡眠系统化",
            "情绪–需要一致化",
            "社会支持体系化"
        ],
        "outcomes": ["生命节奏形成", "自我领导力提升", "行为不再需要强意志", "身份稳定", "能向未来生长"]
    }
}

# 知识分类
KNOWLEDGE_CATEGORIES = [
    {"id": "philosophy", "name": "理念篇", "icon": "💡", "description": "为什么行为改变重要"},
    {"id": "science", "name": "知识篇", "icon": "🔬", "description": "科学原理与机制"},
    {"id": "pathway", "name": "路径篇", "icon": "🗺️", "description": "不同阶段的策略"},
    {"id": "technique", "name": "方法篇", "icon": "🛠️", "description": "具体技巧与工具"},
    {"id": "case", "name": "案例篇", "icon": "📝", "description": "真实成功故事"}
]

# 专家领域
EXPERT_DOMAINS = [
    {"id": "psychology", "name": "心理健康", "icon": "🧠"},
    {"id": "nutrition", "name": "营养饮食", "icon": "🥗"},
    {"id": "exercise", "name": "运动健身", "icon": "🏃"},
    {"id": "sleep", "name": "睡眠管理", "icon": "😴"},
    {"id": "stress", "name": "压力管理", "icon": "🧘"},
    {"id": "addiction", "name": "成瘾康复", "icon": "🚭"},
    {"id": "chronic", "name": "慢病管理", "icon": "💊"},
    {"id": "family", "name": "家庭关系", "icon": "👨‍👩‍👧"}
]


# ============================================================================
# 通用路径 API
# ============================================================================

@router.get("")
async def get_all_paths():
    """获取所有路径概览"""
    return {
        "paths": list(PATH_METADATA.values()),
        "total": len(PATH_METADATA)
    }


@router.get("/home/overview")
async def get_home_overview(user_id: str = "test_user"):
    """获取首页概览数据"""
    return {
        "platform": {
            "name": "行为健康数字平台",
            "slogan": "行为健康·赋能生命",
            "tagline": "主动健康 行为养成 逆转慢病",
            "description": "我们相信，真正决定健康结局的，不是知识的多少，而是每天的行为选择。通过科学的方法，我们帮助你看见、理解并改变行为模式。"
        },
        "stats": {
            "users": 28650,
            "success_stories": 1256,
            "daily_active": 8920,
            "experts": 86
        },
        "highlights": [
            {"icon": "👁️", "title": "看见", "desc": "数据可视化让改变看得见"},
            {"icon": "🧠", "title": "理解", "desc": "识别行为模式和触发链"},
            {"icon": "🎯", "title": "行动", "desc": "科学方法指导每日实践"},
            {"icon": "🤝", "title": "陪伴", "desc": "专家和同伴全程支持"}
        ]
    }


@router.get("/home/user-status")
async def get_home_user_status(user_id: str = "test_user"):
    """获取用户在首页的状态摘要"""
    return {
        "user": {
            "name": "用户",
            "level": "L1",
            "level_name": "成长者",
            "stage": "S2_INTERVENING",
            "stage_name": "干预期",
            "days_joined": 32,
            "streak": 12
        },
        "current_path": {
            "id": "intervention",
            "name": "180天系统课程",
            "day": 15,
            "total_days": 180,
            "progress": 8,
            "current_module": "21天行为链觉察训练营",
            "next_task": "餐后15分钟步行"
        },
        "today_summary": {
            "tasks_completed": 2,
            "tasks_total": 4,
            "points_earned": 25,
            "checkins": 1
        },
        "achievements_recent": [
            {"id": "streak_7", "name": "七日连续", "icon": "🔥", "date": "2026-01-30"},
            {"id": "first_cgm", "name": "首次CGM", "icon": "📊", "date": "2026-01-22"}
        ]
    }


@router.get("/home/paths-summary")
async def get_home_paths_summary(user_id: str = "test_user"):
    """获取六大路径在首页的摘要展示"""
    return {
        "paths": [
            {
                "id": "intervention",
                "name": "系统课程",
                "subtitle": "180天深度改变",
                "icon": "🎯",
                "color": "#8b5cf6",
                "status": "in_progress",
                "progress": 8,
                "highlight": "Day 15 · 运动链觉察",
                "cta": "继续学习"
            },
            {
                "id": "practice",
                "name": "轻松实践",
                "subtitle": "每天2分钟起步",
                "icon": "🎮",
                "color": "#22c55e",
                "status": "available",
                "progress": 0,
                "highlight": "6大分类 · 50+微行动",
                "cta": "开始体验"
            },
            {
                "id": "knowledge",
                "name": "理论学习",
                "subtitle": "七大主题深入了解",
                "icon": "📚",
                "color": "#3b82f6",
                "status": "available",
                "progress": 0,
                "highlight": "缘起·观念·知识·方法",
                "cta": "探索内容"
            },
            {
                "id": "community",
                "name": "社群陪伴",
                "subtitle": "不是一个人在改变",
                "icon": "🤝",
                "color": "#f59e0b",
                "status": "available",
                "progress": 0,
                "highlight": "三层支持网络",
                "cta": "加入社群"
            },
            {
                "id": "expert",
                "name": "专家支持",
                "subtitle": "专业问题专业解答",
                "icon": "🩺",
                "color": "#ec4899",
                "status": "available",
                "progress": 0,
                "highlight": "86位认证专家",
                "cta": "预约咨询"
            },
            {
                "id": "coach",
                "name": "教练成长",
                "subtitle": "成为促进者",
                "icon": "🎓",
                "color": "#6366f1",
                "status": "locked",
                "progress": 0,
                "highlight": "完成180天后解锁",
                "cta": "了解更多"
            }
        ]
    }


@router.get("/home/quick-actions")
async def get_home_quick_actions(user_id: str = "test_user"):
    """获取首页快速行动"""
    return {
        "today_focus": {
            "title": "今日重点",
            "message": "今天是第15天，继续运动链觉察训练",
            "icon": "🎯"
        },
        "actions": [
            {
                "id": "a1",
                "type": "task",
                "title": "餐后15分钟步行",
                "subtitle": "观察血糖曲线变化",
                "icon": "🚶",
                "time": "早餐后",
                "duration": 15,
                "points": 10,
                "status": "pending",
                "priority": "high"
            },
            {
                "id": "a2",
                "type": "task",
                "title": "记录运动链",
                "subtitle": "触发→行为→感受",
                "icon": "📝",
                "time": "上午",
                "duration": 5,
                "points": 5,
                "status": "pending",
                "priority": "medium"
            },
            {
                "id": "a3",
                "type": "checkin",
                "title": "21天早起挑战",
                "subtitle": "今日打卡",
                "icon": "🌅",
                "time": "随时",
                "points": 5,
                "status": "completed",
                "priority": "medium"
            },
            {
                "id": "a4",
                "type": "content",
                "title": "运动为什么能改变血糖？",
                "subtitle": "8分钟视频",
                "icon": "🎥",
                "time": "推荐",
                "duration": 8,
                "points": 3,
                "status": "pending",
                "priority": "low"
            }
        ]
    }


@router.get("/home/featured-content")
async def get_home_featured_content(user_id: str = "test_user"):
    """获取首页精选内容"""
    return {
        "sections": [
            {
                "id": "recommended",
                "title": "为你推荐",
                "items": [
                    {
                        "id": "c1",
                        "type": "video",
                        "title": "2分钟呼吸觉察练习",
                        "thumbnail": None,
                        "duration": 2,
                        "icon": "🧘",
                        "tag": "正念"
                    },
                    {
                        "id": "c2",
                        "type": "article",
                        "title": "为什么改变这么难？行为链的秘密",
                        "thumbnail": None,
                        "read_time": 5,
                        "icon": "📖",
                        "tag": "理解行为"
                    },
                    {
                        "id": "c3",
                        "type": "card",
                        "title": "今日练习：观察你的早餐选择",
                        "thumbnail": None,
                        "icon": "🥗",
                        "tag": "每日觉察"
                    }
                ]
            },
            {
                "id": "popular",
                "title": "热门内容",
                "items": [
                    {
                        "id": "c4",
                        "type": "video",
                        "title": "血糖曲线告诉你的事",
                        "views": 12580,
                        "duration": 10,
                        "icon": "📈"
                    },
                    {
                        "id": "c5",
                        "type": "article",
                        "title": "从「做到」到「我就是这样的人」",
                        "views": 8920,
                        "read_time": 8,
                        "icon": "💡"
                    }
                ]
            }
        ]
    }


@router.get("/home/community-preview")
async def get_home_community_preview(user_id: str = "test_user"):
    """获取首页社区预览"""
    return {
        "activities": {
            "ongoing_count": 3,
            "items": [
                {"id": "act1", "title": "7天早起觉察挑战", "icon": "🌅", "participants": 1234, "my_progress": 3},
                {"id": "act2", "title": "21天习惯养成打卡", "icon": "✅", "participants": 3456, "my_progress": 12}
            ]
        },
        "stories": {
            "total": 1256,
            "recent": [
                {
                    "id": "s1",
                    "user": "成长中的李明",
                    "avatar": "👨",
                    "title": "从120kg到85kg，我的180天",
                    "preview": "一开始我只是想减肥，没想到收获了更多...",
                    "likes": 328,
                    "time": "2小时前"
                },
                {
                    "id": "s2",
                    "user": "早起打卡王",
                    "avatar": "👩",
                    "title": "坚持早起100天后的变化",
                    "preview": "以前觉得早起是折磨，现在成了最享受的时光...",
                    "likes": 256,
                    "time": "5小时前"
                }
            ]
        },
        "support_stats": {
            "messages_today": 1256,
            "new_connections": 89
        }
    }


@router.get("/{path_id}")
async def get_path_detail(path_id: str, user_id: str = "test_user"):
    """获取路径详情"""
    if path_id not in PATH_METADATA:
        raise HTTPException(status_code=404, detail="路径不存在")

    path_info = PATH_METADATA[path_id]

    # 获取用户在该路径的进度
    user_progress = {
        "status": "not_started",
        "progress_percent": 0,
        "started_at": None,
        "current_stage": None,
        "milestones": []
    }

    return {
        "path": path_info,
        "user_progress": user_progress
    }


@router.post("/{path_id}/start")
async def start_path(path_id: str, user_id: str = "test_user"):
    """开始一个路径"""
    if path_id not in PATH_METADATA:
        raise HTTPException(status_code=404, detail="路径不存在")

    # TODO: 在数据库中创建用户路径记录
    return {
        "success": True,
        "message": f"已开始 {PATH_METADATA[path_id]['name']}",
        "path_id": path_id,
        "started_at": datetime.now().isoformat()
    }


# ============================================================================
# 1. 项目型干预路径 API
# ============================================================================

@router.get("/intervention/overview")
async def get_intervention_overview(user_id: str = "test_user"):
    """获取干预路径概览"""
    return {
        "title": "180天行为健康系统课程",
        "slogan": "健康看得见 → 改变看得见 → 成长看得见",
        "subtitle": "三见×六段×五层·科学系统的行为改变之旅",
        "description": "这不是一个减肥课程，也不是一个健身计划。这是一场关于「看见」的旅程——看见身体、看见行为模式、看见改变的可能、看见真正的自己。",
        "philosophy": {
            "core": "行为改变的核心不是意志力，而是看见",
            "principles": [
                {"icon": "👁️", "text": "看见才能改变，改变才能成长"},
                {"icon": "🔗", "text": "行为背后是模式，模式背后是故事"},
                {"icon": "🌱", "text": "不是成为更好的人，而是成为真正的自己"}
            ]
        },
        "stats": {
            "total_days": 180,
            "total_months": 6,
            "modules": 7,
            "intensive_camps": 3,
            "practice_days": 141,
            "participants": 2680,
            "completion_rate": 78,
            "satisfaction": 96
        },
        "highlights": [
            {"icon": "📊", "title": "数据可视化", "desc": "CGM、HRV、体成分等让身体变化看得见"},
            {"icon": "🧠", "title": "行为链觉察", "desc": "识别触发→行为→奖励链，打破旧模式"},
            {"icon": "👤", "title": "身份升级", "desc": "从「我在做」到「我就是这样的人」"},
            {"icon": "🤝", "title": "陪伴成长", "desc": "教练督导+同伴支持，你不是一个人"}
        ],
        "suitable_for": [
            "反复尝试减重/健康管理但总是反弹的人",
            "知道要改变但总是「做不到」的人",
            "想系统了解自己行为模式的人",
            "愿意投入6个月时间进行深度改变的人"
        ],
        "not_suitable_for": [
            "寻找快速减肥方法的人",
            "不愿意面对自己行为模式的人",
            "没有时间投入学习的人"
        ]
    }


@router.get("/intervention/journey")
async def get_intervention_journey(user_id: str = "test_user"):
    """获取180天学习旅程地图"""
    return {
        "journey": [
            {
                "phase": "health_visible",
                "name": "健康看得见",
                "subtitle": "看见身体·看见模式·看见可能",
                "months": "第1-2月",
                "days": "1-60天",
                "color": "#3b82f6",
                "icon": "👁️",
                "description": "让身体和行为改善变成「看得见」的体验",
                "milestones": [
                    {"day": 3, "title": "完成强化营", "icon": "🎯"},
                    {"day": 24, "title": "行为链觉察", "icon": "🔗"},
                    {"day": 60, "title": "健康稳态", "icon": "💚"}
                ],
                "outcomes": ["五大基线图建立", "三条稳定行为链", "身体证据改善"],
                "modules": ["A", "B", "C"]
            },
            {
                "phase": "change_visible",
                "name": "改变看得见",
                "subtitle": "看见价值·身份松动·节奏建立",
                "months": "第3-4月",
                "days": "61-120天",
                "color": "#8b5cf6",
                "icon": "🔄",
                "description": "生命节奏建立 + 行为模式改变 + 身份开始松动",
                "milestones": [
                    {"day": 65, "title": "生命地图", "icon": "🗺️"},
                    {"day": 90, "title": "身份觉察", "icon": "👤"},
                    {"day": 120, "title": "节奏稳定", "icon": "⏰"}
                ],
                "outcomes": ["行为可预测", "身份松动", "身体第二次显著改善"],
                "modules": ["D", "E"]
            },
            {
                "phase": "growth_visible",
                "name": "成长看得见",
                "subtitle": "看见力量·看见未来·生命重写",
                "months": "第5-6月",
                "days": "121-180天",
                "color": "#f59e0b",
                "icon": "🌱",
                "description": "主动生命者 × 不反弹生活方式 × 生命脚本重写",
                "milestones": [
                    {"day": 125, "title": "身份升级", "icon": "⬆️"},
                    {"day": 150, "title": "脚本重写", "icon": "📝"},
                    {"day": 180, "title": "LifeOS建立", "icon": "🌟"}
                ],
                "outcomes": ["生命节奏形成", "身份稳定", "能向未来生长"],
                "modules": ["F", "G"]
            }
        ],
        "total_days": 180,
        "current_day": 15  # 用户当前所在天数（模拟）
    }


@router.get("/intervention/structure")
async def get_intervention_structure():
    """获取三见六段五层课程结构"""
    return {
        "overview": {
            "name": "180天·三见×六段×五层课程体系",
            "slogan": "健康看得见 → 改变看得见 → 成长看得见",
            "total_days": 180,
            "total_months": 6
        },
        "three_insights": list(THREE_INSIGHTS.values()),
        "six_stages": SIX_STAGES,
        "five_layers": FIVE_LAYERS,
        "six_dimensions": SIX_DIMENSIONS,
        "modules": INTERVENTION_MODULES
    }


@router.get("/intervention/modules")
async def get_intervention_modules(
    phase: Optional[str] = None,
    module_id: Optional[str] = None,
    user_id: str = "test_user"
):
    """获取干预课程模块列表"""
    modules = list(INTERVENTION_MODULES.values())

    # 按阶段过滤
    if phase:
        modules = [m for m in modules if m.get("phase") == phase]

    # 按模块ID过滤
    if module_id and module_id in INTERVENTION_MODULES:
        return {"module": INTERVENTION_MODULES[module_id]}

    # 添加用户进度信息（模拟）
    user_progress = {
        "A": {"status": "completed", "progress": 100},
        "B": {"status": "in_progress", "progress": 65, "current_week": 2, "current_day": 10},
        "C": {"status": "locked", "progress": 0},
        "D": {"status": "locked", "progress": 0},
        "E": {"status": "locked", "progress": 0},
        "F": {"status": "locked", "progress": 0},
        "G": {"status": "locked", "progress": 0}
    }

    for m in modules:
        m["user_progress"] = user_progress.get(m["id"], {"status": "locked", "progress": 0})

    return {"modules": modules, "total": len(modules)}


@router.get("/intervention/module/{module_id}")
async def get_intervention_module_detail(module_id: str, user_id: str = "test_user"):
    """获取单个模块详情"""
    if module_id not in INTERVENTION_MODULES:
        raise HTTPException(status_code=404, detail="模块不存在")

    module = INTERVENTION_MODULES[module_id].copy()

    # 添加用户进度
    progress_map = {
        "A": {"status": "completed", "progress": 100, "completed_days": [1, 2, 3]},
        "B": {"status": "in_progress", "progress": 65, "current_week": 2, "current_day": 10, "completed_days": list(range(1, 11))}
    }
    module["user_progress"] = progress_map.get(module_id, {"status": "locked", "progress": 0})

    return module


@router.get("/intervention/tasks")
async def get_behavior_tasks(user_id: str = "guest"):
    """获取用户专属行为养成任务（根据用户阶段和偏好定制）"""
    # 基础任务库
    all_tasks = {
        "awareness": [
            {"id": "t1", "title": "每日2分钟呼吸觉察", "description": "早晨醒来后，花2分钟觉察呼吸", "icon": "🧘"},
            {"id": "t2", "title": "情绪日记", "description": "记录今天最强烈的一个情绪及触发事件", "icon": "📝"},
            {"id": "t3", "title": "行为链记录", "description": "记录一次饮食行为的触发-行为-结果链", "icon": "🔗"},
        ],
        "action": [
            {"id": "t4", "title": "稳糖早餐", "description": "吃一份低GI早餐，观察血糖变化", "icon": "🥗"},
            {"id": "t5", "title": "餐后步行", "description": "餐后步行15分钟", "icon": "🚶"},
            {"id": "t6", "title": "睡前放松", "description": "睡前30分钟不看手机", "icon": "😴"},
        ],
        "maintain": [
            {"id": "t7", "title": "运动打卡", "description": "完成今日运动目标", "icon": "🏃"},
            {"id": "t8", "title": "营养记录", "description": "记录今日三餐营养摄入", "icon": "📊"},
            {"id": "t9", "title": "睡眠复盘", "description": "记录昨晚睡眠质量", "icon": "🌙"},
        ]
    }

    # 根据用户ID生成个性化任务（模拟）
    # 实际应用中应从数据库查询用户当前阶段和任务
    import hashlib
    user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)

    # 根据用户确定阶段（模拟）
    stages = ["awareness", "action", "maintain"]
    user_stage = stages[user_hash % 3]

    # 获取该阶段的任务
    stage_tasks = all_tasks.get(user_stage, all_tasks["awareness"])

    # 为用户生成进度数据（模拟，实际应从数据库获取）
    tasks = []
    for i, task in enumerate(stage_tasks):
        completed = (user_hash + i) % 7
        tasks.append({
            **task,
            "frequency": "daily",
            "stage": user_stage,
            "completed_count": completed,
            "target_count": 7,
            "streak": max(0, completed - 1)
        })

    return {"tasks": tasks, "user_id": user_id, "stage": user_stage}


@router.get("/intervention/progress")
async def get_intervention_progress(user_id: str = "test_user"):
    """获取干预进度"""
    return {
        "current_phase": "health_visible",
        "current_phase_name": "健康看得见",
        "current_module": "B",
        "current_module_name": "21天行为链觉察训练营",
        "current_day": 15,
        "total_days": 180,
        "total_progress": 8,
        "phase_progress": 25,
        "module_progress": 52,
        "days_in_program": 15,
        "streak": 12,
        "next_milestone": {
            "name": "完成饮食链觉察",
            "day": 21,
            "days_left": 6
        },
        "completed_modules": 1,
        "total_modules": 7,
        "completed_tasks": 42,
        "total_tasks": 180,
        "achievements": [
            {"id": "first_cgm", "name": "首次CGM", "icon": "📊", "date": "2026-01-22"},
            {"id": "week1", "name": "第一周完成", "icon": "🎯", "date": "2026-01-28"},
            {"id": "stable_breakfast", "name": "稳糖早餐达人", "icon": "🥗", "date": "2026-02-01"}
        ],
        "weekly_summary": {
            "tasks_completed": 5,
            "tasks_total": 7,
            "avg_cgm_stability": 78,
            "behavior_chains_logged": 12,
            "support_messages": 8
        }
    }


@router.get("/intervention/today")
async def get_intervention_today(user_id: str = "test_user"):
    """获取今日学习内容"""
    return {
        "day": 15,
        "date": "2026-02-05",
        "module": "B",
        "module_name": "21天行为链觉察训练营",
        "week": 2,
        "week_title": "运动链觉察",
        "theme": "运动 × 行为",
        "focus": "感受运动带来的即时反馈",
        "morning_message": "今天是第15天，你已经坚持了两周！今天我们要觉察运动和血糖的关系。",
        "tasks": [
            {
                "id": "t1",
                "time": "早餐后",
                "title": "餐后15分钟步行",
                "description": "吃完早餐后，进行15分钟轻快步行，观察血糖曲线变化",
                "icon": "🚶",
                "duration": 15,
                "completed": False,
                "points": 10
            },
            {
                "id": "t2",
                "time": "上午",
                "title": "记录运动链",
                "description": "记录：触发（什么让你想动/不想动）→ 行为 → 感受",
                "icon": "📝",
                "duration": 5,
                "completed": False,
                "points": 5
            },
            {
                "id": "t3",
                "time": "午餐后",
                "title": "3000步实验",
                "description": "午餐后累计步行3000步，对比不走路时的血糖曲线",
                "icon": "👟",
                "duration": 30,
                "completed": False,
                "points": 15
            },
            {
                "id": "t4",
                "time": "晚上",
                "title": "当日复盘",
                "description": "回顾今天的运动感受，写下「动一点」的身体反馈",
                "icon": "🌙",
                "duration": 10,
                "completed": False,
                "points": 5
            }
        ],
        "learning_content": {
            "title": "运动为什么能改变血糖？",
            "type": "video",
            "duration": 8,
            "thumbnail": None,
            "key_points": [
                "肌肉是最大的「血糖消耗器」",
                "运动后24-48小时胰岛素敏感性提升",
                "不需要大量运动，餐后走路就很有效"
            ]
        },
        "reflection_prompt": "今天的运动给你的身体带来了什么感受？血糖曲线有什么变化？",
        "coach_tip": "不要追求完美，先从「动一点」开始。重要的是让身体记住「动起来很舒服」。"
    }


@router.get("/intervention/tools")
async def get_intervention_tools():
    """获取干预工具箱"""
    return {
        "categories": [
            {
                "id": "monitoring",
                "name": "监测工具",
                "icon": "📊",
                "color": "#3b82f6",
                "tools": [
                    {
                        "id": "cgm",
                        "name": "CGM血糖监测",
                        "description": "24小时实时血糖曲线，让血糖变化看得见",
                        "icon": "📈",
                        "status": "active",
                        "usage_tip": "重点关注餐后2小时血糖波动"
                    },
                    {
                        "id": "hrv",
                        "name": "HRV心率变异",
                        "description": "反映自主神经系统状态，压力和恢复的窗口",
                        "icon": "💓",
                        "status": "active",
                        "usage_tip": "晨起测量，追踪恢复状态"
                    },
                    {
                        "id": "body_comp",
                        "name": "体成分分析",
                        "description": "不只是体重，关注肌肉量和体脂率",
                        "icon": "⚖️",
                        "status": "weekly",
                        "usage_tip": "每周同一时间测量"
                    },
                    {
                        "id": "sleep",
                        "name": "睡眠追踪",
                        "description": "睡眠质量、深睡比例、睡眠节律",
                        "icon": "😴",
                        "status": "daily",
                        "usage_tip": "关注90分钟睡眠周期"
                    }
                ]
            },
            {
                "id": "recording",
                "name": "记录工具",
                "icon": "📝",
                "color": "#8b5cf6",
                "tools": [
                    {
                        "id": "behavior_chain",
                        "name": "行为链记录卡",
                        "description": "记录触发→行为→奖励，识别自动化模式",
                        "icon": "🔗",
                        "template": True
                    },
                    {
                        "id": "emotion_log",
                        "name": "情绪日记",
                        "description": "记录情绪触发和身体感受的关联",
                        "icon": "💭",
                        "template": True
                    },
                    {
                        "id": "food_log",
                        "name": "饮食记录",
                        "description": "不只记录吃什么，更记录为什么吃",
                        "icon": "🍽️",
                        "template": True
                    }
                ]
            },
            {
                "id": "practice",
                "name": "练习工具",
                "icon": "🧘",
                "color": "#22c55e",
                "tools": [
                    {
                        "id": "breath",
                        "name": "呼吸练习",
                        "description": "4-7-8呼吸、盒式呼吸等HRV调节练习",
                        "icon": "🌬️",
                        "duration": "2-5分钟"
                    },
                    {
                        "id": "body_scan",
                        "name": "身体扫描",
                        "description": "觉察身体各部位的感受和紧张",
                        "icon": "🧘",
                        "duration": "5-10分钟"
                    },
                    {
                        "id": "micro_move",
                        "name": "微运动",
                        "description": "办公室可做的简单运动",
                        "icon": "🏃",
                        "duration": "2-3分钟"
                    }
                ]
            }
        ]
    }


@router.get("/intervention/support")
async def get_intervention_support(user_id: str = "test_user"):
    """获取支持系统"""
    return {
        "coach": {
            "id": "coach1",
            "name": "李教练",
            "avatar": "👨‍🏫",
            "title": "行为健康教练 · L4",
            "bio": "3年教练经验，已帮助200+人完成180天课程",
            "specialties": ["饮食行为", "运动习惯", "情绪管理"],
            "next_session": "2026-02-07 19:00",
            "messages_unread": 2
        },
        "group": {
            "id": "group15",
            "name": "第15期学习小组",
            "member_count": 28,
            "active_count": 24,
            "my_rank": 8,
            "today_checkins": 18,
            "recent_messages": [
                {"user": "小明", "content": "今天餐后血糖终于平稳了！", "time": "10分钟前"},
                {"user": "Lisa", "content": "第一次看到运动后血糖下降这么快", "time": "30分钟前"}
            ]
        },
        "expert_sessions": [
            {
                "id": "es1",
                "expert": "张营养师",
                "topic": "稳糖饮食实战",
                "date": "2026-02-08",
                "time": "20:00",
                "type": "group",
                "registered": True
            }
        ],
        "resources": {
            "faq_count": 56,
            "articles": 23,
            "videos": 18,
            "templates": 12
        }
    }


@router.get("/intervention/five-layers-progress")
async def get_five_layers_progress(user_id: str = "test_user"):
    """获取五层成长进度"""
    return {
        "layers": [
            {
                "id": "body",
                "name": "身体层",
                "icon": "💪",
                "order": 1,
                "description": "CGM/HRV/体成分/睡眠等身体数据",
                "color": "#ef4444",
                "progress": 35,
                "current_focus": True,
                "achievements": ["CGM基线建立", "HRV压力测试"],
                "next_goal": "建立稳糖模式",
                "metrics": [
                    {"name": "血糖稳定度", "value": 78, "unit": "%", "trend": "up"},
                    {"name": "HRV均值", "value": 45, "unit": "ms", "trend": "stable"},
                    {"name": "深睡比例", "value": 22, "unit": "%", "trend": "up"}
                ]
            },
            {
                "id": "behavior",
                "name": "行为层",
                "icon": "🎯",
                "order": 2,
                "description": "行为触发链、奖励链、习惯系统",
                "color": "#f59e0b",
                "progress": 28,
                "current_focus": True,
                "achievements": ["识别3条行为链"],
                "next_goal": "建立2条正向行为链",
                "metrics": [
                    {"name": "行为链记录", "value": 42, "unit": "条", "trend": "up"},
                    {"name": "习惯达成率", "value": 68, "unit": "%", "trend": "up"}
                ]
            },
            {
                "id": "cognition",
                "name": "认知层",
                "icon": "🧠",
                "order": 3,
                "description": "思维模式、解释风格、信念系统",
                "color": "#8b5cf6",
                "progress": 12,
                "current_focus": False,
                "achievements": [],
                "next_goal": "第3月开始深入",
                "locked": True
            },
            {
                "id": "identity",
                "name": "身份层",
                "icon": "👤",
                "order": 4,
                "description": "自我认同、角色觉察、身份转变",
                "color": "#3b82f6",
                "progress": 5,
                "current_focus": False,
                "achievements": [],
                "next_goal": "第3月开始探索",
                "locked": True
            },
            {
                "id": "life",
                "name": "生命层",
                "icon": "🌟",
                "order": 5,
                "description": "生命脚本、价值系统、未来愿景",
                "color": "#22c55e",
                "progress": 0,
                "current_focus": False,
                "achievements": [],
                "next_goal": "第5月开始重写",
                "locked": True
            }
        ],
        "insight": "目前你正处于「健康看得见」阶段，重点在身体层和行为层的觉察。认知层和身份层会在第3月逐步打开。"
    }


# ============================================================================
# 2. 专家/医疗支持路径 API
# ============================================================================

@router.get("/expert/overview")
async def get_expert_overview(user_id: str = "test_user"):
    """获取专家支持路径概览"""
    return {
        "title": "专家支持",
        "slogan": "专业的问题，交给专业的人",
        "subtitle": "连接心理、营养、运动、睡眠等领域的专业专家",
        "description": "有些问题需要专业力量。我们精选各领域认证专家，提供一对一深度咨询，帮助你解决复杂问题，加速改变进程。",
        "value_props": [
            {"icon": "🎓", "title": "专业认证", "desc": "所有专家均经过严格资质审核"},
            {"icon": "🔒", "title": "隐私保护", "desc": "咨询内容严格保密"},
            {"icon": "💬", "title": "深度对话", "desc": "一对一深度咨询，个性化建议"},
            {"icon": "📋", "title": "跟进支持", "desc": "咨询后持续跟进，确保效果"}
        ],
        "stats": {
            "total_experts": 86,
            "domains": 8,
            "consultations_completed": 12680,
            "satisfaction_rate": 97,
            "avg_rating": 4.8
        },
        "how_it_works": [
            {"step": 1, "title": "选择专家", "desc": "按领域或问题类型找到合适的专家", "icon": "🔍"},
            {"step": 2, "title": "预约时间", "desc": "查看专家日程，选择方便的时段", "icon": "📅"},
            {"step": 3, "title": "在线咨询", "desc": "通过视频/语音进行深度对话", "icon": "💬"},
            {"step": 4, "title": "获得方案", "desc": "收到个性化建议和行动计划", "icon": "📝"}
        ],
        "service_types": [
            {
                "id": "initial",
                "name": "初次咨询",
                "duration": "60分钟",
                "price_range": "200-500元",
                "description": "首次深度评估，了解情况并给出初步建议",
                "icon": "🎯",
                "recommended": True
            },
            {
                "id": "followup",
                "name": "跟进咨询",
                "duration": "45分钟",
                "price_range": "150-400元",
                "description": "持续跟进进展，调整方案",
                "icon": "🔄",
                "recommended": False
            },
            {
                "id": "urgent",
                "name": "紧急支持",
                "duration": "30分钟",
                "price_range": "150-300元",
                "description": "紧急情况下的快速支持",
                "icon": "🚨",
                "recommended": False
            },
            {
                "id": "package",
                "name": "疗程套餐",
                "duration": "多次",
                "price_range": "按套餐",
                "description": "系统性解决问题，更优惠",
                "icon": "📦",
                "recommended": False
            }
        ]
    }


@router.get("/expert/my-consultations")
async def get_my_consultations(user_id: str = "test_user"):
    """获取我的咨询记录"""
    return {
        "upcoming": [
            {
                "id": "c1",
                "expert": {
                    "id": "exp1",
                    "name": "张明远",
                    "avatar": "👨‍⚕️",
                    "title": "临床心理学博士"
                },
                "type": "跟进咨询",
                "datetime": "2026-02-07 14:00",
                "duration": 45,
                "status": "confirmed",
                "meeting_link": "https://meeting.example.com/abc123"
            }
        ],
        "past": [
            {
                "id": "c0",
                "expert": {
                    "id": "exp1",
                    "name": "张明远",
                    "avatar": "👨‍⚕️",
                    "title": "临床心理学博士"
                },
                "type": "初次咨询",
                "datetime": "2026-01-25 10:00",
                "duration": 60,
                "status": "completed",
                "rating": 5,
                "notes": "讨论了焦虑管理策略，制定了21天练习计划",
                "action_items": ["每日5分钟呼吸练习", "记录焦虑触发事件", "下次复诊前完成问卷"]
            }
        ],
        "stats": {
            "total_consultations": 3,
            "total_hours": 2.5,
            "experts_consulted": 2
        }
    }


@router.get("/expert/domains")
async def get_expert_domains():
    """获取专家领域分类"""
    domains_enhanced = [
        {
            "id": "psychology",
            "name": "心理健康",
            "icon": "🧠",
            "color": "#8b5cf6",
            "description": "焦虑、抑郁、情绪管理、人际关系",
            "expert_count": 18,
            "common_issues": ["焦虑情绪", "抑郁倾向", "压力过大", "人际困扰"],
            "featured_expert": {"name": "张明远", "rating": 4.9}
        },
        {
            "id": "nutrition",
            "name": "营养饮食",
            "icon": "🥗",
            "color": "#22c55e",
            "description": "饮食管理、体重控制、慢病营养",
            "expert_count": 15,
            "common_issues": ["饮食紊乱", "体重管理", "糖尿病饮食", "营养不均"],
            "featured_expert": {"name": "李健康", "rating": 4.8}
        },
        {
            "id": "exercise",
            "name": "运动健身",
            "icon": "🏃",
            "color": "#3b82f6",
            "description": "运动处方、康复训练、体能提升",
            "expert_count": 12,
            "common_issues": ["久坐不动", "运动损伤", "体能下降", "运动习惯"],
            "featured_expert": {"name": "陈运动", "rating": 4.7}
        },
        {
            "id": "sleep",
            "name": "睡眠管理",
            "icon": "😴",
            "color": "#6366f1",
            "description": "失眠调理、作息调整、睡眠障碍",
            "expert_count": 10,
            "common_issues": ["入睡困难", "睡眠浅", "早醒", "作息紊乱"],
            "featured_expert": {"name": "王晓睡", "rating": 4.9}
        },
        {
            "id": "stress",
            "name": "压力管理",
            "icon": "🧘",
            "color": "#f59e0b",
            "description": "压力调节、职场倦怠、身心平衡",
            "expert_count": 11,
            "common_issues": ["职业倦怠", "慢性压力", "工作焦虑", "生活平衡"],
            "featured_expert": {"name": "林静心", "rating": 4.8}
        },
        {
            "id": "addiction",
            "name": "成瘾康复",
            "icon": "🚭",
            "color": "#ef4444",
            "description": "烟酒成瘾、行为成瘾、戒断支持",
            "expert_count": 8,
            "common_issues": ["戒烟戒酒", "游戏成瘾", "购物成瘾", "复发预防"],
            "featured_expert": {"name": "赵戒瘾", "rating": 4.7}
        },
        {
            "id": "chronic",
            "name": "慢病管理",
            "icon": "💊",
            "color": "#ec4899",
            "description": "糖尿病、高血压、代谢综合征",
            "expert_count": 14,
            "common_issues": ["血糖管理", "血压控制", "代谢调理", "用药指导"],
            "featured_expert": {"name": "周慢病", "rating": 4.9}
        },
        {
            "id": "family",
            "name": "家庭关系",
            "icon": "👨‍👩‍👧",
            "color": "#14b8a6",
            "description": "亲子关系、夫妻沟通、家庭和谐",
            "expert_count": 9,
            "common_issues": ["亲子冲突", "夫妻沟通", "原生家庭", "家庭压力"],
            "featured_expert": {"name": "钱家和", "rating": 4.8}
        }
    ]
    return {"domains": domains_enhanced, "total": len(domains_enhanced)}


@router.get("/expert/featured")
async def get_featured_experts():
    """获取推荐专家"""
    return {
        "featured": [
            {
                "id": "exp1",
                "name": "张明远",
                "avatar": "👨‍⚕️",
                "title": "临床心理学博士",
                "organization": "北京心理健康中心",
                "domains": ["psychology", "stress"],
                "domain_names": ["心理健康", "压力管理"],
                "credentials": ["国家二级心理咨询师", "注册心理治疗师"],
                "rating": 4.9,
                "review_count": 128,
                "consultation_count": 356,
                "bio": "从事心理咨询工作15年，擅长焦虑、抑郁情绪调节。温和而专业，善于倾听。",
                "specialties": ["焦虑调节", "情绪管理", "压力应对", "人际关系"],
                "verified": True,
                "badge": "金牌专家",
                "next_available": "明天 10:00",
                "base_rate": 300,
                "highlight": "用户好评率99%"
            },
            {
                "id": "exp2",
                "name": "李健康",
                "avatar": "👩‍⚕️",
                "title": "注册营养师",
                "organization": "健康生活研究院",
                "domains": ["nutrition", "chronic"],
                "domain_names": ["营养饮食", "慢病管理"],
                "credentials": ["国家注册营养师", "糖尿病管理师"],
                "rating": 4.8,
                "review_count": 89,
                "consultation_count": 234,
                "bio": "专注于慢性病营养管理，帮助数百人改善饮食习惯，建立可持续的健康饮食模式。",
                "specialties": ["糖尿病饮食", "体重管理", "营养评估", "饮食计划"],
                "verified": True,
                "badge": "营养专家",
                "next_available": "今天 14:00",
                "base_rate": 200,
                "highlight": "帮助500+用户改善饮食"
            },
            {
                "id": "exp3",
                "name": "王晓睡",
                "avatar": "👨‍🔬",
                "title": "睡眠医学专家",
                "organization": "省立医院睡眠中心",
                "domains": ["sleep"],
                "domain_names": ["睡眠管理"],
                "credentials": ["主任医师", "睡眠医学专委会委员"],
                "rating": 4.9,
                "review_count": 76,
                "consultation_count": 189,
                "bio": "20年睡眠障碍诊疗经验，主攻失眠症和睡眠呼吸暂停。",
                "specialties": ["失眠治疗", "睡眠呼吸暂停", "作息调节", "睡眠卫生"],
                "verified": True,
                "badge": "睡眠专家",
                "next_available": "后天 09:00",
                "base_rate": 400,
                "highlight": "三甲医院专家"
            }
        ],
        "categories": [
            {"id": "hot", "name": "热门推荐", "icon": "🔥"},
            {"id": "new", "name": "新晋专家", "icon": "✨"},
            {"id": "top_rated", "name": "好评榜首", "icon": "⭐"}
        ]
    }


@router.get("/expert/list")
async def get_expert_list(
    domain: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    """获取专家列表"""
    experts = [
        {
            "id": "exp1",
            "name": "张明远",
            "avatar": "👨‍⚕️",
            "title": "临床心理学博士",
            "organization": "北京心理健康中心",
            "domains": ["psychology", "stress"],
            "domain_names": ["心理健康", "压力管理"],
            "credentials": ["国家二级心理咨询师", "注册心理治疗师"],
            "rating": 4.9,
            "review_count": 128,
            "consultation_count": 356,
            "bio": "从事心理咨询工作15年，擅长焦虑、抑郁情绪调节",
            "specialties": ["焦虑调节", "情绪管理", "压力应对"],
            "verified": True,
            "source": "invited",
            "next_available": "2026-02-07T10:00:00",
            "next_available_text": "明天 10:00 可约",
            "base_rate": 300,
            "rate_unit": "session"
        },
        {
            "id": "exp2",
            "name": "李健康",
            "avatar": "👩‍⚕️",
            "title": "注册营养师",
            "organization": "健康生活研究院",
            "domains": ["nutrition", "chronic"],
            "domain_names": ["营养饮食", "慢病管理"],
            "credentials": ["国家注册营养师", "糖尿病管理师"],
            "rating": 4.8,
            "review_count": 89,
            "consultation_count": 234,
            "bio": "专注于慢性病营养管理，帮助数百人改善饮食习惯",
            "specialties": ["糖尿病饮食", "体重管理", "营养评估"],
            "verified": True,
            "source": "registered",
            "next_available": "2026-02-06T14:00:00",
            "next_available_text": "今天 14:00 可约",
            "base_rate": 200,
            "rate_unit": "session"
        },
        {
            "id": "exp3",
            "name": "王晓睡",
            "avatar": "👨‍🔬",
            "title": "睡眠医学专家",
            "organization": "省立医院睡眠中心",
            "domains": ["sleep"],
            "domain_names": ["睡眠管理"],
            "credentials": ["主任医师", "睡眠医学专委会委员"],
            "rating": 4.9,
            "review_count": 76,
            "consultation_count": 189,
            "bio": "20年睡眠障碍诊疗经验",
            "specialties": ["失眠治疗", "睡眠呼吸暂停", "作息调节"],
            "verified": True,
            "source": "partner",
            "next_available": "2026-02-08T09:00:00",
            "next_available_text": "后天 09:00 可约",
            "base_rate": 400,
            "rate_unit": "session"
        },
        {
            "id": "exp4",
            "name": "林静心",
            "avatar": "👩‍🏫",
            "title": "正念减压导师",
            "organization": "身心平衡工作室",
            "domains": ["stress", "psychology"],
            "domain_names": ["压力管理", "心理健康"],
            "credentials": ["MBSR认证导师", "心理咨询师"],
            "rating": 4.8,
            "review_count": 95,
            "consultation_count": 267,
            "bio": "专注正念减压10年，帮助职场人士找回内心平静",
            "specialties": ["正念冥想", "职场压力", "身心平衡"],
            "verified": True,
            "source": "registered",
            "next_available": "2026-02-06T16:00:00",
            "next_available_text": "今天 16:00 可约",
            "base_rate": 250,
            "rate_unit": "session"
        },
        {
            "id": "exp5",
            "name": "陈运动",
            "avatar": "🏃",
            "title": "运动康复师",
            "organization": "活力运动医学中心",
            "domains": ["exercise"],
            "domain_names": ["运动健身"],
            "credentials": ["运动康复师", "体能训练师"],
            "rating": 4.7,
            "review_count": 68,
            "consultation_count": 156,
            "bio": "运动医学背景，擅长为久坐人群制定科学运动方案",
            "specialties": ["运动处方", "康复训练", "久坐调理"],
            "verified": True,
            "source": "registered",
            "next_available": "2026-02-07T15:00:00",
            "next_available_text": "明天 15:00 可约",
            "base_rate": 180,
            "rate_unit": "session"
        }
    ]

    # 按领域过滤
    if domain:
        experts = [e for e in experts if domain in e["domains"]]

    # 按关键词过滤
    if keyword:
        keyword_lower = keyword.lower()
        experts = [e for e in experts if
                  keyword_lower in e["name"].lower() or
                  keyword_lower in e["bio"].lower() or
                  any(keyword_lower in s.lower() for s in e["specialties"])]

    return {
        "experts": experts,
        "total": len(experts),
        "page": page,
        "page_size": page_size
    }


@router.get("/expert/faq")
async def get_expert_faq():
    """获取专家咨询常见问题"""
    return {
        "faqs": [
            {
                "id": "f1",
                "question": "第一次咨询需要准备什么？",
                "answer": "建议提前整理好想要讨论的问题，回顾近期的状态变化。咨询前会收到专家发送的简短问卷，请如实填写以帮助专家更好地了解你的情况。",
                "category": "咨询准备"
            },
            {
                "id": "f2",
                "question": "咨询方式有哪些？",
                "answer": "目前支持视频咨询和语音咨询两种方式。视频咨询效果更好，但如果你不方便露面，语音咨询也是很好的选择。",
                "category": "咨询方式"
            },
            {
                "id": "f3",
                "question": "一次咨询能解决问题吗？",
                "answer": "这取决于问题的复杂程度。简单的问题可能一次咨询就能获得清晰的方向，复杂的问题可能需要多次咨询。专家会在首次咨询后给出建议。",
                "category": "咨询效果"
            },
            {
                "id": "f4",
                "question": "咨询内容会保密吗？",
                "answer": "绝对保密。所有咨询内容严格保密，专家遵守职业伦理规范。除非涉及自伤或伤害他人的紧急情况，否则不会向任何第三方透露。",
                "category": "隐私安全"
            },
            {
                "id": "f5",
                "question": "如何选择合适的专家？",
                "answer": "建议根据你的主要问题选择对应领域的专家，同时可以参考专家的专长、用户评价和简介。如果不确定，可以先预约初次咨询，专家会帮你判断是否匹配。",
                "category": "选择专家"
            },
            {
                "id": "f6",
                "question": "预约后可以取消吗？",
                "answer": "可以。咨询开始前24小时取消可全额退款，24小时内取消将收取50%费用。紧急情况请联系客服处理。",
                "category": "预约政策"
            }
        ]
    }


@router.get("/expert/{expert_id}")
async def get_expert_detail(expert_id: str):
    """获取专家详情"""
    # TODO: 从数据库查询
    return {
        "id": expert_id,
        "name": "张明远",
        "avatar": None,
        "title": "临床心理学博士",
        "organization": "北京心理健康中心",
        "domains": ["psychology", "stress"],
        "credentials": ["国家二级心理咨询师", "注册心理治疗师"],
        "rating": 4.9,
        "review_count": 128,
        "consultation_count": 356,
        "bio": "从事心理咨询工作15年，擅长焦虑、抑郁情绪调节。曾任多家企业心理顾问，帮助上千人改善心理健康状态。",
        "specialties": ["焦虑调节", "情绪管理", "压力应对", "人际关系"],
        "verified": True,
        "source": "invited",
        "availability": {
            "next_available": "2026-02-07T10:00:00",
            "slots": [
                {"id": "s1", "start_time": "2026-02-07T10:00:00", "end_time": "2026-02-07T11:00:00", "available": True},
                {"id": "s2", "start_time": "2026-02-07T14:00:00", "end_time": "2026-02-07T15:00:00", "available": True},
                {"id": "s3", "start_time": "2026-02-08T10:00:00", "end_time": "2026-02-08T11:00:00", "available": False}
            ],
            "consultation_types": [
                {"id": "ct1", "name": "初次咨询", "duration": 60, "price": 300, "description": "首次深度评估与建议"},
                {"id": "ct2", "name": "跟进咨询", "duration": 45, "price": 250, "description": "持续跟进与指导"},
                {"id": "ct3", "name": "紧急支持", "duration": 30, "price": 200, "description": "紧急情绪支持"}
            ]
        },
        "pricing": {
            "currency": "CNY",
            "base_rate": 300,
            "unit": "session",
            "packages": [
                {"id": "p1", "name": "3次套餐", "sessions": 3, "price": 800, "valid_days": 30},
                {"id": "p2", "name": "6次套餐", "sessions": 6, "price": 1500, "valid_days": 60}
            ]
        },
        "reviews": [
            {"user": "匿名用户", "rating": 5, "content": "张老师很专业，帮助我度过了最难的时期", "created_at": "2026-01-20"},
            {"user": "成长中", "rating": 5, "content": "非常有耐心，给了很多实用建议", "created_at": "2026-01-15"}
        ]
    }


@router.post("/expert/{expert_id}/book")
async def book_expert_consultation(
    expert_id: str,
    slot_id: str = Body(..., embed=True),
    consultation_type: str = Body(..., embed=True),
    user_id: str = "test_user"
):
    """预约专家咨询"""
    # TODO: 实际预约逻辑
    return {
        "success": True,
        "booking_id": f"booking_{datetime.now().timestamp()}",
        "expert_id": expert_id,
        "scheduled_at": "2026-02-07T10:00:00",
        "message": "预约成功，请准时参加"
    }


# ============================================================================
# 3. 认知学习路径 API - 行为健康理论学习版块
# ============================================================================

@router.get("/knowledge/overview")
async def get_knowledge_overview():
    """获取知识学习版块概览"""
    return {
        "title": "行为健康理论学习",
        "slogan": "先理解，再行动",
        "description": "系统学习行为健康的理论基础，从缘起到效果，从认知到实践，构建完整的知识体系",
        "content_stats": {
            "total_articles": 156,
            "total_videos": 48,
            "total_tools": 23,
            "total_assessments": 12
        }
    }


@router.get("/knowledge/categories")
async def get_knowledge_categories():
    """获取行为健康知识七大主题分类"""
    categories = [
        {
            "id": "origin",
            "name": "缘起",
            "icon": "🌅",
            "color": "#f97316",
            "description": "为什么行为健康如此重要？从个人到社会的深层意义",
            "subtitle": "理解行为健康的时代背景与意义",
            "content_count": 18,
            "key_topics": ["现代生活挑战", "慢性病危机", "心理健康时代", "预防医学转型"]
        },
        {
            "id": "concept",
            "name": "观念",
            "icon": "💡",
            "color": "#eab308",
            "description": "行为健康的核心理念与价值观",
            "subtitle": "建立正确的行为健康观念",
            "content_count": 24,
            "key_topics": ["整体健康观", "行为即生活方式", "自我负责", "渐进式改变"]
        },
        {
            "id": "knowledge",
            "name": "知识",
            "icon": "📚",
            "color": "#22c55e",
            "description": "行为科学、心理学、神经科学的基础知识",
            "subtitle": "了解行为改变的科学原理",
            "content_count": 35,
            "key_topics": ["习惯回路", "动机理论", "神经可塑性", "行为心理学"]
        },
        {
            "id": "method",
            "name": "方法",
            "icon": "🔧",
            "color": "#3b82f6",
            "description": "经过验证的行为改变方法与技巧",
            "subtitle": "掌握行为改变的实用方法",
            "content_count": 42,
            "key_topics": ["动机访谈", "正念练习", "习惯堆叠", "环境设计"]
        },
        {
            "id": "pathway",
            "name": "路径",
            "icon": "🗺️",
            "color": "#8b5cf6",
            "description": "行为改变的阶段路径与成长地图",
            "subtitle": "明确从当前到目标的路径",
            "content_count": 28,
            "key_topics": ["改变六阶段", "三见六段五层", "复发预防", "长期维持"]
        },
        {
            "id": "tool",
            "name": "工具",
            "icon": "🛠️",
            "color": "#ec4899",
            "description": "实用的自我管理工具与评估量表",
            "subtitle": "使用工具辅助行为管理",
            "content_count": 23,
            "key_topics": ["行为追踪", "目标设定", "情绪记录", "进度评估"]
        },
        {
            "id": "outcome",
            "name": "效果",
            "icon": "📊",
            "color": "#06b6d4",
            "description": "行为改变的预期效果与科学证据",
            "subtitle": "了解行为改变带来的成效",
            "content_count": 20,
            "key_topics": ["研究证据", "成功案例", "健康指标", "生活质量"]
        }
    ]
    return {"categories": categories}


@router.get("/knowledge/formats")
async def get_content_formats():
    """获取内容形式分类"""
    formats = [
        {
            "id": "article",
            "name": "文章",
            "icon": "📝",
            "color": "#3b82f6",
            "description": "深度阅读，系统学习",
            "content_count": 86
        },
        {
            "id": "literature",
            "name": "文献",
            "icon": "📖",
            "color": "#8b5cf6",
            "description": "学术研究，循证支持",
            "content_count": 32
        },
        {
            "id": "video",
            "name": "视频",
            "icon": "🎬",
            "color": "#ef4444",
            "description": "直观演示，轻松理解",
            "content_count": 48
        },
        {
            "id": "infographic",
            "name": "图文",
            "icon": "🖼️",
            "color": "#22c55e",
            "description": "可视化呈现，快速获取",
            "content_count": 28
        },
        {
            "id": "interactive",
            "name": "交互展板",
            "icon": "🎯",
            "color": "#f59e0b",
            "description": "互动体验，个性化探索",
            "content_count": 15
        },
        {
            "id": "assessment",
            "name": "调查评估",
            "icon": "📋",
            "color": "#06b6d4",
            "description": "自我认知，科学评估",
            "content_count": 12
        }
    ]
    return {"formats": formats}


@router.get("/knowledge/assessments")
async def get_self_assessments(user_id: str = "test_user"):
    """获取自我认知调查评估列表"""
    assessments = [
        {
            "id": "four_cognitions",
            "name": "四所认知评估",
            "icon": "🧠",
            "color": "#8b5cf6",
            "description": "评估您对「所是、所有、所能、所愿」四个维度的认知清晰度",
            "dimensions": ["所是（我是谁）", "所有（我拥有什么）", "所能（我能做什么）", "所愿（我想要什么）"],
            "questions_count": 24,
            "duration": "10-15分钟",
            "completed": False,
            "last_result": None,
            "recommended": True
        },
        {
            "id": "life_foundation",
            "name": "生命底色探索",
            "icon": "🎨",
            "color": "#ec4899",
            "description": "探索塑造您生命底色的核心经历与价值观",
            "dimensions": ["早期经历", "核心信念", "价值排序", "意义来源"],
            "questions_count": 32,
            "duration": "15-20分钟",
            "completed": True,
            "last_result": {
                "date": "2026-01-15",
                "summary": "您的生命底色以「成长」和「连接」为主要特征"
            },
            "recommended": False
        },
        {
            "id": "behavior_pattern",
            "name": "行为模式识别",
            "icon": "🔄",
            "color": "#22c55e",
            "description": "识别您的行为触发模式、习惯回路和应对方式",
            "dimensions": ["触发识别", "行为循环", "奖励机制", "应对策略"],
            "questions_count": 28,
            "duration": "12-18分钟",
            "completed": False,
            "last_result": None,
            "recommended": True
        },
        {
            "id": "readiness_assessment",
            "name": "改变准备度评估",
            "icon": "🚀",
            "color": "#f59e0b",
            "description": "评估您当前处于行为改变的哪个阶段",
            "dimensions": ["问题意识", "改变意愿", "自我效能", "行动准备"],
            "questions_count": 16,
            "duration": "5-8分钟",
            "completed": True,
            "last_result": {
                "date": "2026-02-01",
                "summary": "您处于「准备阶段」，已准备好开始行动"
            },
            "recommended": False
        },
        {
            "id": "wellbeing_check",
            "name": "身心健康自检",
            "icon": "💚",
            "color": "#06b6d4",
            "description": "全面评估当前的身体、心理、社会健康状态",
            "dimensions": ["身体健康", "心理状态", "社会支持", "生活满意度"],
            "questions_count": 20,
            "duration": "8-10分钟",
            "completed": False,
            "last_result": None,
            "recommended": True
        }
    ]
    return {"assessments": assessments}


@router.get("/knowledge/interactive-boards")
async def get_interactive_boards():
    """获取交互展板列表 - 自我预期与行为健康实现路径"""
    boards = [
        {
            "id": "expectation_explorer",
            "name": "自我预期探索",
            "icon": "🎯",
            "color": "#8b5cf6",
            "description": "探索您对未来生活的预期，明确想要成为的样子",
            "type": "exploration",
            "sections": ["理想生活画像", "健康目标设定", "能力期望", "关系愿景"],
            "interactive": True,
            "duration": "15-20分钟"
        },
        {
            "id": "bh_pathway_planner",
            "name": "行为健康实现路径",
            "icon": "🗺️",
            "color": "#22c55e",
            "description": "从行为健康的角度，规划实现预期的具体路径",
            "type": "planning",
            "sections": ["现状分析", "目标分解", "行为规划", "里程碑设定"],
            "interactive": True,
            "duration": "20-30分钟"
        },
        {
            "id": "habit_designer",
            "name": "习惯设计工作坊",
            "icon": "🔧",
            "color": "#f59e0b",
            "description": "交互式设计您的专属习惯方案",
            "type": "design",
            "sections": ["触发设计", "行为细化", "奖励设置", "环境优化"],
            "interactive": True,
            "duration": "25-30分钟"
        },
        {
            "id": "change_stages_map",
            "name": "改变阶段地图",
            "icon": "📍",
            "color": "#ec4899",
            "description": "可视化您在行为改变旅程中的位置",
            "type": "visualization",
            "sections": ["当前位置", "下一阶段", "潜在挑战", "资源支持"],
            "interactive": True,
            "duration": "10-15分钟"
        }
    ]
    return {"boards": boards}


@router.get("/knowledge/content")
async def get_knowledge_content(
    category: Optional[str] = None,
    format_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    user_id: str = "test_user"
):
    """获取知识内容列表"""
    contents = [
        # 缘起
        {
            "id": "k1",
            "title": "为什么行为健康成为时代命题",
            "category": "origin",
            "format": "article",
            "summary": "从慢性病流行到心理健康危机，理解行为健康兴起的时代背景",
            "read_time": 12,
            "author": {"id": "a1", "name": "平台编辑", "verified": True},
            "tags": ["时代背景", "慢性病", "预防医学"],
            "view_count": 4256,
            "like_count": 389,
            "completed": True,
            "progress": 100
        },
        {
            "id": "k2",
            "title": "健康的决定因素：行为占多大比重？",
            "category": "origin",
            "format": "infographic",
            "summary": "可视化展示生活方式对健康的影响权重",
            "read_time": 3,
            "author": {"id": "a1", "name": "平台编辑", "verified": True},
            "tags": ["健康决定因素", "数据可视化"],
            "view_count": 6120,
            "like_count": 528,
            "completed": False,
            "progress": 0
        },
        # 观念
        {
            "id": "k3",
            "title": "整体健康观：身心社灵的统一",
            "category": "concept",
            "format": "video",
            "summary": "理解WHO定义的健康不仅是没有疾病",
            "duration": 15,
            "author": {"id": "a2", "name": "张教授", "title": "健康心理学家", "verified": True},
            "tags": ["整体健康", "世卫组织", "观念"],
            "view_count": 3890,
            "like_count": 345,
            "completed": False,
            "progress": 40
        },
        {
            "id": "k4",
            "title": "行为即生活方式：每一个选择都在塑造你",
            "category": "concept",
            "format": "article",
            "summary": "理解日常行为如何累积成生活方式，进而影响健康",
            "read_time": 10,
            "author": {"id": "a3", "name": "李医生", "verified": True},
            "tags": ["生活方式", "选择", "累积效应"],
            "view_count": 2780,
            "like_count": 234,
            "completed": False,
            "progress": 0
        },
        # 知识
        {
            "id": "k5",
            "title": "习惯回路：触发→行为→奖励",
            "category": "knowledge",
            "format": "video",
            "summary": "了解习惯形成的神经科学原理",
            "duration": 12,
            "author": {"id": "a2", "name": "张教授", "title": "神经科学家", "verified": True},
            "tags": ["习惯", "神经科学", "行为模式"],
            "view_count": 5890,
            "like_count": 445,
            "completed": True,
            "progress": 100
        },
        {
            "id": "k6",
            "title": "动机心理学：内在动机vs外在动机",
            "category": "knowledge",
            "format": "article",
            "summary": "理解不同类型动机对行为改变的影响",
            "read_time": 15,
            "author": {"id": "a4", "name": "王教授", "title": "动机心理学专家", "verified": True},
            "tags": ["动机", "心理学", "自我决定理论"],
            "view_count": 3420,
            "like_count": 287,
            "completed": False,
            "progress": 0
        },
        {
            "id": "k7",
            "title": "神经可塑性：大脑可以改变",
            "category": "knowledge",
            "format": "literature",
            "summary": "学术综述：神经可塑性研究进展及其在行为改变中的应用",
            "read_time": 25,
            "author": {"id": "a5", "name": "科学期刊编辑部", "verified": True},
            "tags": ["神经可塑性", "文献", "研究证据"],
            "view_count": 1230,
            "like_count": 98,
            "completed": False,
            "progress": 0
        },
        # 方法
        {
            "id": "k8",
            "title": "动机访谈入门：与自己对话的艺术",
            "category": "method",
            "format": "video",
            "summary": "学习动机访谈的核心技术和自我应用",
            "duration": 20,
            "author": {"id": "a6", "name": "行为教练陈老师", "verified": True},
            "tags": ["动机访谈", "方法", "自我对话"],
            "view_count": 4560,
            "like_count": 398,
            "completed": False,
            "progress": 0
        },
        {
            "id": "k9",
            "title": "微习惯：从2分钟开始",
            "category": "method",
            "format": "article",
            "summary": "学习如何用极小的起步降低行为改变的门槛",
            "read_time": 10,
            "author": {"id": "a3", "name": "行为教练王老师", "verified": True},
            "tags": ["微习惯", "方法", "实用技巧"],
            "view_count": 7670,
            "like_count": 689,
            "completed": True,
            "progress": 100
        },
        # 路径
        {
            "id": "k10",
            "title": "行为改变的六个阶段",
            "category": "pathway",
            "format": "infographic",
            "summary": "了解从无意识到习惯养成的完整路径",
            "read_time": 5,
            "author": {"id": "a1", "name": "平台编辑", "verified": True},
            "tags": ["改变阶段", "路径", "跨理论模型"],
            "view_count": 8120,
            "like_count": 756,
            "completed": True,
            "progress": 100
        },
        {
            "id": "k11",
            "title": "三见六段五层：180天成长框架",
            "category": "pathway",
            "format": "interactive",
            "summary": "交互式了解行为健康核心课程体系",
            "duration": 15,
            "author": {"id": "a1", "name": "平台编辑", "verified": True},
            "tags": ["三见六段五层", "课程体系", "成长框架"],
            "view_count": 5430,
            "like_count": 467,
            "completed": False,
            "progress": 0
        },
        # 工具
        {
            "id": "k12",
            "title": "SMART目标设定工具",
            "category": "tool",
            "format": "interactive",
            "summary": "交互式设定具体、可衡量、可达成、相关、有时限的目标",
            "duration": 10,
            "author": {"id": "a1", "name": "平台编辑", "verified": True},
            "tags": ["SMART", "目标设定", "工具"],
            "view_count": 6780,
            "like_count": 589,
            "completed": False,
            "progress": 0
        },
        {
            "id": "k13",
            "title": "行为追踪模板下载",
            "category": "tool",
            "format": "article",
            "summary": "可下载的行为追踪表格和使用指南",
            "read_time": 5,
            "author": {"id": "a1", "name": "平台编辑", "verified": True},
            "tags": ["追踪", "模板", "下载"],
            "view_count": 4320,
            "like_count": 345,
            "completed": False,
            "progress": 0
        },
        # 效果
        {
            "id": "k14",
            "title": "真实案例：从久坐到每天运动的转变",
            "category": "outcome",
            "format": "article",
            "summary": "一位IT从业者如何在3个月内养成运动习惯",
            "read_time": 15,
            "author": {"id": "u1", "name": "成长者小李", "verified": False},
            "tags": ["案例", "运动", "上班族"],
            "view_count": 3340,
            "like_count": 278,
            "completed": False,
            "progress": 0
        },
        {
            "id": "k15",
            "title": "研究证据：行为干预的长期效果",
            "category": "outcome",
            "format": "literature",
            "summary": "Meta分析：行为干预对慢性病管理的有效性",
            "read_time": 20,
            "author": {"id": "a5", "name": "科学期刊编辑部", "verified": True},
            "tags": ["研究", "证据", "有效性"],
            "view_count": 1890,
            "like_count": 145,
            "completed": False,
            "progress": 0
        }
    ]

    # 过滤
    if category:
        contents = [c for c in contents if c["category"] == category]
    if format_type:
        contents = [c for c in contents if c["format"] == format_type]

    return {
        "contents": contents,
        "total": len(contents),
        "page": page,
        "page_size": page_size
    }


@router.get("/knowledge/progress")
async def get_knowledge_progress(user_id: str = "test_user"):
    """获取学习进度"""
    return {
        "total_content": 190,
        "completed_content": 28,
        "total_minutes": 320,
        "category_progress": {
            "origin": {"completed": 1, "total": 18, "percent": 6},
            "concept": {"completed": 3, "total": 24, "percent": 13},
            "knowledge": {"completed": 8, "total": 35, "percent": 23},
            "method": {"completed": 6, "total": 42, "percent": 14},
            "pathway": {"completed": 5, "total": 28, "percent": 18},
            "tool": {"completed": 3, "total": 23, "percent": 13},
            "outcome": {"completed": 2, "total": 20, "percent": 10}
        },
        "format_progress": {
            "article": {"completed": 12, "total": 86},
            "literature": {"completed": 2, "total": 32},
            "video": {"completed": 8, "total": 48},
            "infographic": {"completed": 4, "total": 28},
            "interactive": {"completed": 1, "total": 15},
            "assessment": {"completed": 2, "total": 12}
        },
        "assessments_completed": 2,
        "assessments_total": 5,
        "streak": 7,
        "last_studied_at": "2026-02-05T10:30:00"
    }


# ============================================================================
# 4. 低门槛实践路径 API - 不用改变生活，先改变一个动作
# ============================================================================

@router.get("/practice/overview")
async def get_practice_overview(user_id: str = "test_user"):
    """获取实践路径概览"""
    return {
        "title": "低门槛实践",
        "slogan": "不用改变生活，先改变一个动作",
        "description": "从2分钟微行动开始，通过打卡、挑战、游戏化机制，让健康习惯养成变得轻松有趣",
        "core_principle": "微小改变 × 持续重复 = 显著效果",
        "daily_goal": {
            "micro_actions": 3,
            "minutes": 10
        },
        "stats": {
            "total_users": 12580,
            "total_checkins": 458920,
            "avg_streak": 8.5
        }
    }


@router.get("/practice/today")
async def get_today_summary(user_id: str = "test_user"):
    """获取今日实践汇总"""
    return {
        "date": "2026-02-05",
        "greeting": "早上好！新的一天，从一个小动作开始 ☀️",
        "micro_actions": {
            "completed": 2,
            "target": 4,
            "streak": 12
        },
        "time_invested": {
            "today": 8,
            "weekly_avg": 12
        },
        "points": {
            "today": 25,
            "total": 1580,
            "to_next_level": 420
        },
        "motivation": {
            "quote": "「每天进步一点点，一年后你会感谢今天的自己」",
            "tip": "今天试试在午餐后散步5分钟？"
        },
        "active_activities": [
            {"id": "act1", "name": "21天早起挑战", "day": 6, "total": 21}
        ]
    }


@router.get("/practice/categories")
async def get_practice_categories():
    """获取实践分类"""
    categories = [
        {
            "id": "mindfulness",
            "name": "正念觉察",
            "icon": "🧘",
            "color": "#8b5cf6",
            "description": "专注当下，平静内心",
            "action_count": 8,
            "popular_actions": ["2分钟呼吸", "身体扫描", "正念进食"]
        },
        {
            "id": "movement",
            "name": "身体活动",
            "icon": "🏃",
            "color": "#22c55e",
            "description": "让身体动起来",
            "action_count": 12,
            "popular_actions": ["5分钟伸展", "爬楼梯", "办公室运动"]
        },
        {
            "id": "nutrition",
            "name": "健康饮食",
            "icon": "🥗",
            "color": "#f59e0b",
            "description": "吃得更健康",
            "action_count": 10,
            "popular_actions": ["多喝水", "吃一份蔬菜", "慢慢咀嚼"]
        },
        {
            "id": "sleep",
            "name": "睡眠管理",
            "icon": "😴",
            "color": "#3b82f6",
            "description": "睡个好觉",
            "action_count": 6,
            "popular_actions": ["睡前放下手机", "固定作息", "睡前放松"]
        },
        {
            "id": "emotion",
            "name": "情绪调节",
            "icon": "💚",
            "color": "#ec4899",
            "description": "管理情绪，提升幸福感",
            "action_count": 9,
            "popular_actions": ["感恩日记", "情绪记录", "积极暂停"]
        },
        {
            "id": "social",
            "name": "社交连接",
            "icon": "🤝",
            "color": "#06b6d4",
            "description": "维护人际关系",
            "action_count": 7,
            "popular_actions": ["问候朋友", "认真倾听", "表达感谢"]
        }
    ]
    return {"categories": categories}


@router.get("/practice/micro-actions")
async def get_micro_actions(category: Optional[str] = None, user_id: str = "test_user"):
    """获取每日微行动"""
    actions = [
        {
            "id": "ma1",
            "title": "2分钟呼吸",
            "description": "闭上眼睛，专注于呼吸。吸气4秒，屏息4秒，呼气6秒。",
            "duration": 2,
            "category": "mindfulness",
            "icon": "🧘",
            "difficulty": "easy",
            "points": 10,
            "completed_today": False,
            "streak": 5,
            "best_streak": 14,
            "total_completions": 42,
            "tip": "可以在工作间隙或睡前练习"
        },
        {
            "id": "ma2",
            "title": "喝一杯温水",
            "description": "起床后立即喝一杯温水，唤醒身体，促进代谢。",
            "duration": 1,
            "category": "nutrition",
            "icon": "💧",
            "difficulty": "easy",
            "points": 5,
            "completed_today": True,
            "streak": 12,
            "best_streak": 30,
            "total_completions": 89,
            "tip": "在床头放一杯水，醒来就能喝"
        },
        {
            "id": "ma3",
            "title": "感恩三件事",
            "description": "写下今天让你感恩的三件小事，培养积极心态。",
            "duration": 3,
            "category": "emotion",
            "icon": "🙏",
            "difficulty": "easy",
            "points": 15,
            "completed_today": False,
            "streak": 3,
            "best_streak": 21,
            "total_completions": 28,
            "tip": "可以是很小的事，比如今天的天气很好"
        },
        {
            "id": "ma4",
            "title": "5分钟伸展",
            "description": "站起来做简单的伸展动作，缓解久坐带来的僵硬。",
            "duration": 5,
            "category": "movement",
            "icon": "🤸",
            "difficulty": "easy",
            "points": 20,
            "completed_today": False,
            "streak": 0,
            "best_streak": 7,
            "total_completions": 15,
            "tip": "每隔1-2小时伸展一次效果更好"
        },
        {
            "id": "ma5",
            "title": "正念进食",
            "description": "下一餐时放下手机，专注于食物的颜色、味道、口感。",
            "duration": 10,
            "category": "mindfulness",
            "icon": "🍽️",
            "difficulty": "medium",
            "points": 25,
            "completed_today": False,
            "streak": 1,
            "best_streak": 5,
            "total_completions": 8,
            "tip": "从一顿饭开始，慢慢增加"
        },
        {
            "id": "ma6",
            "title": "睡前远离屏幕",
            "description": "睡前30分钟放下手机和电脑，让大脑准备入睡。",
            "duration": 30,
            "category": "sleep",
            "icon": "📵",
            "difficulty": "medium",
            "points": 30,
            "completed_today": False,
            "streak": 2,
            "best_streak": 10,
            "total_completions": 18,
            "tip": "可以用这段时间阅读或做放松练习"
        },
        {
            "id": "ma7",
            "title": "问候一位朋友",
            "description": "给一位朋友发消息问候，维护你们的友谊。",
            "duration": 2,
            "category": "social",
            "icon": "👋",
            "difficulty": "easy",
            "points": 15,
            "completed_today": True,
            "streak": 4,
            "best_streak": 14,
            "total_completions": 35,
            "tip": "不需要复杂的话题，简单的关心就好"
        },
        {
            "id": "ma8",
            "title": "吃一份水果或蔬菜",
            "description": "在今天的某一餐中加入一份新鲜的水果或蔬菜。",
            "duration": 5,
            "category": "nutrition",
            "icon": "🍎",
            "difficulty": "easy",
            "points": 15,
            "completed_today": False,
            "streak": 6,
            "best_streak": 21,
            "total_completions": 67,
            "tip": "把水果放在显眼的地方"
        }
    ]

    if category:
        actions = [a for a in actions if a["category"] == category]

    completed_today = sum(1 for a in actions if a["completed_today"])
    return {
        "actions": actions,
        "completed_today": completed_today,
        "total": len(actions),
        "today_points": sum(a["points"] for a in actions if a["completed_today"])
    }


@router.get("/practice/habits")
async def get_habit_tracking(user_id: str = "test_user"):
    """获取习惯追踪数据"""
    return {
        "active_habits": [
            {
                "id": "h1",
                "name": "每日饮水",
                "target": "8杯",
                "icon": "💧",
                "color": "#3b82f6",
                "current_streak": 12,
                "best_streak": 30,
                "weekly_completion": [True, True, True, True, True, False, False],  # Mon-Sun
                "monthly_rate": 85
            },
            {
                "id": "h2",
                "name": "早起（7点前）",
                "target": "每天",
                "icon": "🌅",
                "color": "#f59e0b",
                "current_streak": 5,
                "best_streak": 14,
                "weekly_completion": [True, True, True, False, True, False, False],
                "monthly_rate": 72
            },
            {
                "id": "h3",
                "name": "运动30分钟",
                "target": "每周3次",
                "icon": "🏃",
                "color": "#22c55e",
                "current_streak": 2,
                "best_streak": 8,
                "weekly_completion": [True, False, True, False, False, False, False],
                "monthly_rate": 60
            }
        ],
        "suggested_habits": [
            {"id": "sh1", "name": "阅读15分钟", "icon": "📖", "category": "growth", "adopters": 3250},
            {"id": "sh2", "name": "睡前冥想", "icon": "🧘", "category": "sleep", "adopters": 2890},
            {"id": "sh3", "name": "记录三餐", "icon": "📝", "category": "nutrition", "adopters": 1560}
        ]
    }


@router.get("/practice/activities")
async def get_practice_activities(
    type: Optional[str] = None,
    status: Optional[str] = None,
    user_id: str = "test_user"
):
    """获取打卡活动列表"""
    activities = [
        {
            "id": "act1",
            "title": "21天早起挑战",
            "description": "每天7点前起床，养成规律作息，开启活力满满的一天",
            "type": "challenge",
            "duration": "21天",
            "duration_days": 21,
            "category": "sleep",
            "icon": "🌅",
            "color": "#f59e0b",
            "participant_count": 1256,
            "start_date": "2026-02-01",
            "end_date": "2026-02-21",
            "progress": 28,
            "joined": True,
            "my_days_completed": 6,
            "daily_reward": 20,
            "completion_reward": 200
        },
        {
            "id": "act2",
            "title": "7天正念入门",
            "description": "每天5分钟正念练习，从忙碌中找到内心的宁静",
            "type": "checkin",
            "duration": "7天",
            "duration_days": 7,
            "category": "mindfulness",
            "icon": "🧘",
            "color": "#8b5cf6",
            "participant_count": 3890,
            "start_date": None,
            "end_date": None,
            "progress": 0,
            "joined": False,
            "my_days_completed": 0,
            "daily_reward": 15,
            "completion_reward": 100
        },
        {
            "id": "act3",
            "title": "30天健康饮食",
            "description": "逐步改善饮食习惯，每天记录三餐，减少加工食品",
            "type": "habit",
            "duration": "30天",
            "duration_days": 30,
            "category": "nutrition",
            "icon": "🥗",
            "color": "#22c55e",
            "participant_count": 892,
            "start_date": None,
            "end_date": None,
            "progress": 0,
            "joined": False,
            "my_days_completed": 0,
            "daily_reward": 15,
            "completion_reward": 300
        },
        {
            "id": "act4",
            "title": "14天步行计划",
            "description": "每天步行6000步以上，重新发现身边的风景",
            "type": "challenge",
            "duration": "14天",
            "duration_days": 14,
            "category": "movement",
            "icon": "🚶",
            "color": "#06b6d4",
            "participant_count": 2150,
            "start_date": None,
            "end_date": None,
            "progress": 0,
            "joined": False,
            "my_days_completed": 0,
            "daily_reward": 20,
            "completion_reward": 150
        },
        {
            "id": "act5",
            "title": "感恩日记21天",
            "description": "每天记录3件感恩的事，培养积极乐观的心态",
            "type": "checkin",
            "duration": "21天",
            "duration_days": 21,
            "category": "emotion",
            "icon": "📓",
            "color": "#ec4899",
            "participant_count": 1580,
            "start_date": None,
            "end_date": None,
            "progress": 0,
            "joined": False,
            "my_days_completed": 0,
            "daily_reward": 15,
            "completion_reward": 200
        }
    ]

    if type:
        activities = [a for a in activities if a["type"] == type]

    return {"activities": activities, "total": len(activities)}


@router.get("/practice/challenges")
async def get_challenges(user_id: str = "test_user"):
    """获取限时挑战赛"""
    challenges = [
        {
            "id": "ch1",
            "title": "春季焕新挑战赛",
            "description": "春天是改变的好时机！完成指定任务，赢取健康大礼包",
            "start_date": "2026-02-10",
            "end_date": "2026-02-24",
            "status": "active",
            "participant_count": 5678,
            "prize": "价值500元健康礼包",
            "prizes": [
                {"rank": "1-10名", "reward": "健康手环 + 500积分"},
                {"rank": "11-100名", "reward": "300积分"},
                {"rank": "完成挑战", "reward": "限定徽章 + 100积分"}
            ],
            "rules": [
                "每天完成至少3个微行动",
                "连续打卡7天获得双倍积分",
                "邀请好友参加额外获得50积分"
            ],
            "my_rank": 156,
            "my_score": 320,
            "my_progress": {
                "daily_actions": {"completed": 2, "target": 3},
                "streak_days": 5,
                "total_points": 320
            },
            "leaderboard": [
                {"rank": 1, "name": "健康达人", "score": 890, "avatar": "🏆"},
                {"rank": 2, "name": "早起王者", "score": 850, "avatar": "🥈"},
                {"rank": 3, "name": "运动先锋", "score": 820, "avatar": "🥉"}
            ]
        }
    ]
    return {"challenges": challenges}


@router.get("/practice/achievements")
async def get_achievements(user_id: str = "test_user"):
    """获取成就徽章"""
    achievements = [
        # 入门成就
        {"id": "ach1", "name": "第一步", "description": "完成第一个微行动", "icon": "🌱", "category": "beginner", "earned": True, "earned_at": "2026-01-15", "rarity": "common"},
        {"id": "ach2", "name": "初尝甜头", "description": "累计完成10个微行动", "icon": "🎯", "category": "beginner", "earned": True, "earned_at": "2026-01-18", "rarity": "common"},
        # 连续成就
        {"id": "ach3", "name": "连续7天", "description": "连续打卡7天", "icon": "🔥", "category": "streak", "earned": True, "earned_at": "2026-01-22", "rarity": "uncommon"},
        {"id": "ach4", "name": "连续21天", "description": "连续打卡21天", "icon": "⚡", "category": "streak", "earned": False, "progress": 57, "rarity": "rare"},
        {"id": "ach5", "name": "连续30天", "description": "连续打卡30天", "icon": "💎", "category": "streak", "earned": False, "progress": 40, "rarity": "epic"},
        # 分类成就
        {"id": "ach6", "name": "正念新手", "description": "完成20个正念练习", "icon": "🧘", "category": "mindfulness", "earned": True, "earned_at": "2026-01-28", "rarity": "uncommon"},
        {"id": "ach7", "name": "运动达人", "description": "完成50个运动微行动", "icon": "💪", "category": "movement", "earned": False, "progress": 30, "rarity": "rare"},
        {"id": "ach8", "name": "饮食管理", "description": "完成30个饮食微行动", "icon": "🥗", "category": "nutrition", "earned": False, "progress": 67, "rarity": "uncommon"},
        # 挑战成就
        {"id": "ach9", "name": "挑战完成者", "description": "完成一个打卡挑战", "icon": "🏆", "category": "challenge", "earned": False, "progress": 28, "rarity": "rare"},
        {"id": "ach10", "name": "早起王者", "description": "连续21天早起", "icon": "🌅", "category": "challenge", "earned": False, "progress": 28, "rarity": "epic"},
        # 社交成就
        {"id": "ach11", "name": "互助伙伴", "description": "帮助3位伙伴坚持打卡", "icon": "🤝", "category": "social", "earned": False, "progress": 33, "rarity": "uncommon"},
        {"id": "ach12", "name": "影响力", "description": "邀请5位朋友加入", "icon": "⭐", "category": "social", "earned": False, "progress": 20, "rarity": "rare"}
    ]
    return {
        "achievements": achievements,
        "earned_count": 4,
        "total_count": len(achievements),
        "by_rarity": {
            "common": {"earned": 2, "total": 2},
            "uncommon": {"earned": 1, "total": 3},
            "rare": {"earned": 0, "total": 4},
            "epic": {"earned": 0, "total": 2},
            "legendary": {"earned": 0, "total": 1}
        }
    }


@router.get("/practice/progress")
async def get_practice_progress(user_id: str = "test_user"):
    """获取实践总进度"""
    return {
        "level": {
            "current": 5,
            "name": "实践者",
            "icon": "🌿",
            "points": 1580,
            "points_to_next": 420,
            "next_level": {"level": 6, "name": "习惯达人", "icon": "🌳"}
        },
        "stats": {
            "total_actions": 186,
            "total_days": 42,
            "current_streak": 12,
            "best_streak": 21,
            "total_minutes": 560,
            "challenges_completed": 0,
            "achievements_earned": 4
        },
        "weekly_summary": {
            "actions": [3, 4, 2, 5, 3, 0, 0],  # Mon-Sun
            "total": 17,
            "avg": 3.4,
            "trend": "up"  # up, down, stable
        },
        "category_breakdown": {
            "mindfulness": {"count": 42, "percent": 23},
            "movement": {"count": 35, "percent": 19},
            "nutrition": {"count": 48, "percent": 26},
            "sleep": {"count": 25, "percent": 13},
            "emotion": {"count": 28, "percent": 15},
            "social": {"count": 8, "percent": 4}
        }
    }


@router.post("/practice/micro-action/{action_id}/complete")
async def complete_micro_action(action_id: str, user_id: str = "test_user"):
    """完成微行动"""
    return {
        "success": True,
        "action_id": action_id,
        "message": "太棒了！微行动已完成 🎉",
        "streak": 6,
        "points_earned": 15,
        "bonus": None,
        "achievement_unlocked": None
    }


@router.post("/practice/activity/{activity_id}/join")
async def join_activity(activity_id: str, user_id: str = "test_user"):
    """加入打卡活动"""
    return {
        "success": True,
        "activity_id": activity_id,
        "message": "已加入活动，加油！💪",
        "start_date": "2026-02-05"
    }


@router.post("/practice/activity/{activity_id}/checkin")
async def checkin_activity(activity_id: str, user_id: str = "test_user"):
    """活动打卡"""
    return {
        "success": True,
        "activity_id": activity_id,
        "day": 7,
        "points_earned": 20,
        "message": "打卡成功！继续保持 ⭐"
    }


# ============================================================================
# 5. 社群陪伴路径 API
# ============================================================================

@router.get("/community/overview")
async def get_community_overview(user_id: str = "test_user"):
    """获取社群陪伴路径概览"""
    return {
        "title": "社群陪伴",
        "slogan": "不是一个人在改变",
        "description": "行为改变的路上，有人理解、有人陪伴、有人支持，成功率提升3倍以上",
        "core_value": "连接 · 理解 · 陪伴 · 成长",
        "research_insight": "研究表明，有社会支持的人行为改变成功率是独自尝试的3.2倍",
        "stats": {
            "total_members": 8560,
            "active_groups": 156,
            "connections_made": 12890,
            "support_messages": 45670
        }
    }


@router.get("/community/my-network")
async def get_my_network(user_id: str = "test_user"):
    """获取我的社交网络状态"""
    return {
        "connections": {
            "companions": 3,
            "groups_joined": 2,
            "followers": 15,
            "following": 12
        },
        "support_circle": [
            {
                "id": "c1",
                "name": "小王",
                "avatar": "👨",
                "role": "互助伙伴",
                "relationship": "mutual",
                "last_interaction": "今天",
                "streak_days": 12,
                "status": "active"
            },
            {
                "id": "c2",
                "name": "健康达人Lisa",
                "avatar": "👩",
                "role": "学习对象",
                "relationship": "following",
                "last_interaction": "昨天",
                "streak_days": 0,
                "status": "active"
            },
            {
                "id": "c3",
                "name": "早起小分队",
                "avatar": "🌅",
                "role": "互助小组",
                "relationship": "group",
                "member_count": 8,
                "last_interaction": "2小时前",
                "status": "active"
            }
        ],
        "recent_support": {
            "given": 5,
            "received": 8,
            "this_week": True
        }
    }


@router.get("/community/layers")
async def get_support_layers():
    """获取三层支持网络"""
    return {
        "layers": [
            {
                "id": "peer",
                "name": "同伴支持",
                "icon": "👥",
                "color": "#22c55e",
                "description": "找到有相同经历的人，互相理解、鼓励和陪伴",
                "subtitle": "最懂你的，是走过同样路的人",
                "features": [
                    {"name": "匿名倾诉", "icon": "💭", "desc": "安全分享，无压力表达"},
                    {"name": "互助打卡", "icon": "✅", "desc": "相互监督，共同坚持"},
                    {"name": "经验分享", "icon": "📖", "desc": "真实故事，相互启发"}
                ],
                "user_count": 5680,
                "active_today": 890
            },
            {
                "id": "professional",
                "name": "同行支持",
                "icon": "🤝",
                "color": "#3b82f6",
                "description": "与同行业、同阶段的伙伴交流，共同应对相似挑战",
                "subtitle": "同频的人更容易产生共鸣",
                "features": [
                    {"name": "行业圈子", "icon": "💼", "desc": "找到同行，交流行业特有的健康挑战"},
                    {"name": "阶段群组", "icon": "📊", "desc": "和同阶段的人一起进步"},
                    {"name": "职场互助", "icon": "🏢", "desc": "工作生活平衡经验分享"}
                ],
                "user_count": 3450,
                "active_today": 456
            },
            {
                "id": "expert",
                "name": "专家支持",
                "icon": "👨‍🏫",
                "color": "#8b5cf6",
                "description": "获得专业人士的指导和帮助，解决复杂问题",
                "subtitle": "专业的问题交给专业的人",
                "features": [
                    {"name": "专家答疑", "icon": "❓", "desc": "专业问题，专家解答"},
                    {"name": "在线咨询", "icon": "💬", "desc": "一对一专业支持"},
                    {"name": "督导指导", "icon": "🎯", "desc": "个性化成长建议"}
                ],
                "user_count": 1230,
                "active_today": 180
            }
        ]
    }


@router.get("/community/groups")
async def get_community_groups(
    type: Optional[str] = None,
    topic: Optional[str] = None,
    user_id: str = "test_user"
):
    """获取社群列表"""
    groups = [
        {
            "id": "g1",
            "name": "焦虑自救互助组",
            "description": "一起面对焦虑，分享应对方法，你不是一个人",
            "type": "peer_support",
            "icon": "💚",
            "color": "#22c55e",
            "cover_url": None,
            "member_count": 256,
            "active_count": 45,
            "topics": ["焦虑", "情绪管理", "正念"],
            "rules": ["保持尊重", "保护隐私", "积极正向"],
            "joined": True,
            "my_role": "member",
            "unread_count": 3,
            "last_activity": "5分钟前",
            "highlights": ["今日打卡12人", "新成员+3"]
        },
        {
            "id": "g2",
            "name": "IT人健康圈",
            "description": "程序员的健康生活交流群，对抗久坐、熬夜、外卖",
            "type": "industry",
            "icon": "💻",
            "color": "#3b82f6",
            "cover_url": None,
            "member_count": 1890,
            "active_count": 234,
            "topics": ["久坐", "颈椎", "用眼健康", "熬夜"],
            "rules": ["友善交流", "拒绝广告"],
            "joined": False,
            "my_role": None,
            "unread_count": 0,
            "last_activity": "1小时前",
            "highlights": ["热门话题：站立办公体验"]
        },
        {
            "id": "g3",
            "name": "21天早起挑战群",
            "description": "一起早起，互相监督，养成早起习惯",
            "type": "challenge",
            "icon": "🌅",
            "color": "#f59e0b",
            "cover_url": None,
            "member_count": 567,
            "active_count": 189,
            "topics": ["早起", "作息", "晨间习惯"],
            "rules": ["每日打卡", "互相鼓励"],
            "joined": True,
            "my_role": "member",
            "unread_count": 8,
            "last_activity": "刚刚",
            "highlights": ["今日已有89人打卡", "你的排名：第23"]
        },
        {
            "id": "g4",
            "name": "健康饮食交流群",
            "description": "分享健康食谱，交流饮食心得，一起吃得更健康",
            "type": "topic",
            "icon": "🥗",
            "color": "#10b981",
            "cover_url": None,
            "member_count": 892,
            "active_count": 156,
            "topics": ["健康饮食", "减糖", "营养搭配"],
            "rules": ["分享真实经验", "不推销产品"],
            "joined": False,
            "my_role": None,
            "unread_count": 0,
            "last_activity": "30分钟前",
            "highlights": ["本周食谱推荐", "减糖第一周心得"]
        },
        {
            "id": "g5",
            "name": "正念冥想小组",
            "description": "每日正念练习，分享冥想体验，一起探索内心平静",
            "type": "topic",
            "icon": "🧘",
            "color": "#8b5cf6",
            "cover_url": None,
            "member_count": 445,
            "active_count": 78,
            "topics": ["正念", "冥想", "情绪管理"],
            "rules": ["保持安静心态", "尊重他人体验"],
            "joined": False,
            "my_role": None,
            "unread_count": 0,
            "last_activity": "2小时前",
            "highlights": ["每晚8点共修", "本周主题：呼吸觉察"]
        }
    ]

    if type:
        groups = [g for g in groups if g["type"] == type]

    return {"groups": groups, "total": len(groups)}


@router.get("/community/group-categories")
async def get_group_categories():
    """获取社群分类"""
    return {
        "categories": [
            {"id": "peer_support", "name": "互助小组", "icon": "💚", "color": "#22c55e", "count": 45},
            {"id": "industry", "name": "行业圈子", "icon": "💼", "color": "#3b82f6", "count": 28},
            {"id": "challenge", "name": "挑战群组", "icon": "🏆", "color": "#f59e0b", "count": 32},
            {"id": "topic", "name": "主题社群", "icon": "💬", "color": "#8b5cf6", "count": 51}
        ]
    }


@router.get("/community/peer-matches")
async def get_peer_matches(user_id: str = "test_user"):
    """获取同伴匹配推荐"""
    matches = [
        {
            "id": "pm1",
            "user": {
                "id": "u123",
                "name": "成长中的小李",
                "avatar": "👨",
                "bio": "正在养成早起习惯，希望找到一起坚持的伙伴",
                "stage": "行动期",
                "level": "L1成长者",
                "interests": ["运动", "早起", "正念"],
                "streak": 15,
                "join_days": 32
            },
            "match_score": 92,
            "match_reasons": [
                {"icon": "🌅", "reason": "都在养成早起习惯"},
                {"icon": "🧘", "reason": "对正念冥想感兴趣"},
                {"icon": "📊", "reason": "同处行动期，进度相近"}
            ],
            "common_groups": ["21天早起挑战群"],
            "status": "recommended"
        },
        {
            "id": "pm2",
            "user": {
                "id": "u456",
                "name": "健康先行者",
                "avatar": "👩",
                "bio": "已经坚持健康生活2年，愿意分享经验",
                "stage": "维持期",
                "level": "L2分享者",
                "interests": ["饮食管理", "压力应对", "睡眠"],
                "streak": 156,
                "join_days": 245
            },
            "match_score": 78,
            "match_reasons": [
                {"icon": "🥗", "reason": "都关注健康饮食"},
                {"icon": "📚", "reason": "可以学习成功经验"},
                {"icon": "🤝", "reason": "愿意帮助新人成长"}
            ],
            "common_groups": [],
            "status": "recommended"
        },
        {
            "id": "pm3",
            "user": {
                "id": "u789",
                "name": "IT老张",
                "avatar": "🧑‍💻",
                "bio": "程序员，正在对抗久坐和熬夜",
                "stage": "准备期",
                "level": "L1成长者",
                "interests": ["运动", "颈椎保护", "作息调整"],
                "streak": 8,
                "join_days": 15
            },
            "match_score": 85,
            "match_reasons": [
                {"icon": "💻", "reason": "同为IT行业"},
                {"icon": "🏃", "reason": "都想增加运动"},
                {"icon": "😴", "reason": "都在改善作息"}
            ],
            "common_groups": ["IT人健康圈"],
            "status": "recommended"
        }
    ]
    return {"matches": matches, "total": len(matches)}


@router.get("/community/activity-feed")
async def get_activity_feed(user_id: str = "test_user"):
    """获取社群动态"""
    activities = [
        {
            "id": "a1",
            "type": "checkin",
            "user": {"name": "小王", "avatar": "👨"},
            "content": "早起第12天打卡成功！今天6:30起床，感觉很清爽 🌅",
            "group": {"id": "g3", "name": "21天早起挑战群"},
            "time": "5分钟前",
            "likes": 8,
            "comments": 3,
            "liked": False
        },
        {
            "id": "a2",
            "type": "share",
            "user": {"name": "健康达人Lisa", "avatar": "👩"},
            "content": "分享一个对我很有效的减压方法：每天花5分钟做腹式呼吸，一个月下来焦虑感明显减轻了",
            "group": {"id": "g1", "name": "焦虑自救互助组"},
            "time": "30分钟前",
            "likes": 24,
            "comments": 12,
            "liked": True
        },
        {
            "id": "a3",
            "type": "milestone",
            "user": {"name": "成长中的小李", "avatar": "👨"},
            "content": "🎉 达成里程碑：连续打卡21天！感谢群里小伙伴的鼓励",
            "group": {"id": "g3", "name": "21天早起挑战群"},
            "time": "1小时前",
            "likes": 45,
            "comments": 18,
            "liked": True
        },
        {
            "id": "a4",
            "type": "question",
            "user": {"name": "新人小陈", "avatar": "🧑"},
            "content": "请问大家，刚开始正念冥想的时候总是走神怎么办？有什么技巧吗？",
            "group": {"id": "g5", "name": "正念冥想小组"},
            "time": "2小时前",
            "likes": 5,
            "comments": 8,
            "liked": False
        }
    ]
    return {"activities": activities}


@router.get("/community/events")
async def get_community_events(user_id: str = "test_user"):
    """获取社群活动"""
    events = [
        {
            "id": "e1",
            "title": "周六线上共修：正念呼吸",
            "description": "每周六晚8点，一起进行30分钟正念呼吸练习",
            "type": "online",
            "icon": "🧘",
            "color": "#8b5cf6",
            "host": {"name": "正念冥想小组", "avatar": "🧘"},
            "time": "2026-02-08 20:00",
            "duration": "30分钟",
            "participant_count": 45,
            "max_participants": 100,
            "joined": False,
            "recurring": "每周六"
        },
        {
            "id": "e2",
            "title": "早起打卡PK赛",
            "description": "21天早起挑战群专属活动，连续早起最久的人获得奖励",
            "type": "challenge",
            "icon": "🏆",
            "color": "#f59e0b",
            "host": {"name": "21天早起挑战群", "avatar": "🌅"},
            "time": "2026-02-10 - 2026-03-02",
            "duration": "21天",
            "participant_count": 156,
            "max_participants": None,
            "joined": True,
            "recurring": None
        },
        {
            "id": "e3",
            "title": "健康饮食分享会",
            "description": "分享你的健康食谱和饮食心得，优秀分享者获得积分奖励",
            "type": "sharing",
            "icon": "🥗",
            "color": "#10b981",
            "host": {"name": "健康饮食交流群", "avatar": "🥗"},
            "time": "2026-02-15 19:30",
            "duration": "1小时",
            "participant_count": 28,
            "max_participants": 50,
            "joined": False,
            "recurring": "每月一次"
        }
    ]
    return {"events": events}


@router.get("/community/support-stats")
async def get_support_stats(user_id: str = "test_user"):
    """获取支持统计"""
    return {
        "given": {
            "likes": 45,
            "comments": 23,
            "encouragements": 12,
            "this_week": 15
        },
        "received": {
            "likes": 89,
            "comments": 34,
            "encouragements": 28,
            "this_week": 22
        },
        "impact": {
            "helped_users": 8,
            "inspired_actions": 15,
            "support_score": 156
        },
        "badges": [
            {"id": "b1", "name": "热心伙伴", "icon": "💚", "earned": True},
            {"id": "b2", "name": "鼓励达人", "icon": "👏", "earned": True},
            {"id": "b3", "name": "分享之星", "icon": "⭐", "earned": False, "progress": 60}
        ]
    }


@router.post("/community/group/{group_id}/join")
async def join_community_group(group_id: str, user_id: str = "test_user"):
    """加入社群"""
    return {
        "success": True,
        "group_id": group_id,
        "message": "已加入社群，欢迎！"
    }


@router.post("/community/peer/{match_id}/connect")
async def connect_peer(match_id: str, user_id: str = "test_user"):
    """连接同伴"""
    return {
        "success": True,
        "match_id": match_id,
        "message": "连接请求已发送"
    }


@router.post("/community/activity/{activity_id}/like")
async def like_activity(activity_id: str, user_id: str = "test_user"):
    """点赞动态"""
    return {"success": True, "activity_id": activity_id}


@router.post("/community/event/{event_id}/join")
async def join_event(event_id: str, user_id: str = "test_user"):
    """参加活动"""
    return {"success": True, "event_id": event_id, "message": "报名成功！"}


# ============================================================================
# 6. 教练成长路径 API
# ============================================================================

@router.get("/coach/levels")
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
            "description": "正在亲身实践「三见六段五层」课程，体验行为改变的全过程",
            "core_tasks": ["完成180天课程", "每日行为打卡", "参与小组互动"],
            "capabilities": ["参与180天课程", "获得同伴支持", "查看个人数据报告"],
            "advancement": {
                "companions_required": 0,
                "points_required": {"growth": 500, "contribution": 50, "influence": 0},
                "conditions": ["完成180天「三见六段五层」课程", "实现至少3个行为目标"]
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


@router.get("/coach/modules")
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


@router.get("/coach/progress")
async def get_coach_progress(user_id: str = "test_user"):
    """获取教练成长进度（六级四同道者体系）"""
    return {
        "current_level": {
            "id": "l1",
            "name": "成长者",
            "level": 1,
            "icon": "🌱",
            "color": "#22c55e"
        },
        "next_level": {
            "id": "l2",
            "name": "分享者",
            "level": 2,
            "icon": "💬",
            "color": "#f59e0b"
        },
        # 三类积分
        "points": {
            "growth": {
                "current": 320,
                "required": 500,
                "name": "成长积分",
                "icon": "📈",
                "description": "通过学习和实践获得"
            },
            "contribution": {
                "current": 25,
                "required": 50,
                "name": "贡献积分",
                "icon": "🤝",
                "description": "通过帮助他人获得"
            },
            "influence": {
                "current": 0,
                "required": 0,
                "name": "影响力积分",
                "icon": "✨",
                "description": "通过分享传播获得"
            }
        },
        # 四同道者进度
        "companions": {
            "required": 0,  # L1不需要带人
            "current": 0,
            "target_level": None,
            "members": []
        },
        # 课程进度（三见六段五层）
        "course_progress": {
            "phase": "见自己",
            "stage": 2,
            "day": 45,
            "total_days": 180,
            "completion_rate": 25
        },
        # 成就徽章
        "badges": [
            {"id": "starter", "name": "开始之旅", "icon": "🚀", "earned": True, "date": "2026-01-01"},
            {"id": "week1", "name": "坚持一周", "icon": "📆", "earned": True, "date": "2026-01-07"},
            {"id": "first_share", "name": "首次分享", "icon": "💬", "earned": False, "date": None}
        ],
        # 下一步行动
        "next_actions": [
            {"type": "course", "title": "完成今日课程", "points": 5, "category": "growth"},
            {"type": "checkin", "title": "行为打卡", "points": 3, "category": "growth"},
            {"type": "help", "title": "回答社群提问", "points": 5, "category": "contribution"}
        ],
        # 督导信息（L3以上才有）
        "mentorship": None
    }


@router.get("/coach/practice-records")
async def get_practice_records(user_id: str = "test_user"):
    """获取实践记录"""
    records = [
        {
            "id": "pr1",
            "client_name": "案例A",
            "session_date": "2026-02-01",
            "duration": 45,
            "type": "initial_assessment",
            "notes": "初次评估，了解来访者情况",
            "supervisor_feedback": "评估全面，建议关注情绪变化",
            "approved": True
        },
        {
            "id": "pr2",
            "client_name": "案例A",
            "session_date": "2026-02-03",
            "duration": 40,
            "type": "follow_up",
            "notes": "跟进上次目标设定的执行情况",
            "supervisor_feedback": None,
            "approved": False
        }
    ]
    return {"records": records, "total_hours": 12, "approved_hours": 8}


@router.get("/coach/companions")
async def get_companions_progress(user_id: str = "test_user"):
    """获取四同道者培养进度"""
    return {
        "system_info": {
            "name": "四同道者机制",
            "description": "每位成员晋级需要引领4位同道者完成上一级别的成长",
            "principle": "通过「带人」实现自身深度成长，形成可持续的成长网络"
        },
        "my_level": {
            "level": 1,
            "name": "成长者",
            "companions_required": 0,  # L1不需要带人
            "target_level_name": None
        },
        "next_level_requirement": {
            "level": 2,
            "name": "分享者",
            "companions_required": 4,
            "target_level_name": "成长者",
            "description": "引领4位观察员完成180天课程成为成长者"
        },
        "my_companions": [],  # L1还没有开始带人
        "companion_candidates": [
            {
                "id": "c1",
                "name": "李小明",
                "avatar": "👤",
                "current_level": 0,
                "level_name": "观察员",
                "progress": 15,
                "joined_date": "2026-01-20",
                "status": "active"
            },
            {
                "id": "c2",
                "name": "王小华",
                "avatar": "👤",
                "current_level": 0,
                "level_name": "观察员",
                "progress": 8,
                "joined_date": "2026-01-25",
                "status": "active"
            }
        ],
        "network_stats": {
            "total_influenced": 2,
            "direct_companions": 0,
            "indirect_companions": 0
        }
    }


@router.get("/coach/six-level-overview")
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
