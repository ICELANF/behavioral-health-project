# -*- coding: utf-8 -*-
"""
内容管理 API

支持：
- 多来源内容管理（平台、专家、教练、用户分享）
- 视频配套测试
- 双轨学习激励（教练积分/成长者时长）
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger

router = APIRouter(prefix="/api/v1/content", tags=["内容管理"])


# ============================================================================
# Pydantic 模型
# ============================================================================

class ContentSource:
    PLATFORM = "platform"
    EXPERT = "expert"
    COACH = "coach"
    SHARER = "sharer"
    AI_GENERATED = "ai_generated"
    EXTERNAL = "external"


class ContentListQuery(BaseModel):
    """内容列表查询"""
    page: int = 1
    page_size: int = 20
    type: Optional[str] = None  # course/video/article/audio/card/case_share
    source: Optional[str] = None
    domain: Optional[str] = None
    status: Optional[str] = None
    keyword: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class ContentCard(BaseModel):
    """内容卡片（列表展示）"""
    id: str
    type: str
    source: str
    title: str
    subtitle: Optional[str] = None
    cover_url: Optional[str] = None
    icon: Optional[str] = None
    domain: str
    author: Dict[str, Any]
    view_count: int = 0
    like_count: int = 0
    duration: Optional[int] = None
    word_count: Optional[int] = None
    is_free: bool = True
    is_new: bool = False
    user_progress: Optional[int] = None


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== 视频测试相关 ====================

class QuizOption(BaseModel):
    """测试选项"""
    key: str
    content: str


class QuizQuestion(BaseModel):
    """测试题目"""
    question_id: str
    order: int
    type: str  # single/multiple/judge
    content: str
    options: List[QuizOption]
    correct_answer: Any  # str 或 List[str]
    explanation: Optional[str] = None
    points: int = 10


class VideoQuiz(BaseModel):
    """视频配套测试"""
    quiz_id: str
    video_id: str
    title: str
    description: Optional[str] = None
    questions: List[QuizQuestion]
    pass_score: int = 60
    max_attempts: int = 3
    time_limit_seconds: Optional[int] = None
    coach_points_bonus: int = 5
    grower_minutes_bonus: int = 5


class QuizSubmission(BaseModel):
    """测试提交"""
    quiz_id: str
    answers: Dict[str, Any]  # question_id -> answer


class QuizResult(BaseModel):
    """测试结果"""
    result_id: str
    quiz_id: str
    user_id: str
    score: int
    correct_count: int
    total_count: int
    passed: bool
    points_earned: int = 0
    minutes_earned: int = 0
    attempt_number: int
    submitted_at: datetime


# ==================== 案例分享 ====================

class CaseShareCreate(BaseModel):
    """创建案例分享"""
    title: str = Field(..., min_length=5, max_length=50)
    domain: str
    challenge: str = Field(..., min_length=20, max_length=500)
    approach: str = Field(..., min_length=20, max_length=500)
    outcome: str = Field(..., min_length=20, max_length=500)
    reflection: Optional[str] = Field(None, max_length=300)
    is_anonymous: bool = False
    allow_comments: bool = True


# ==================== 学习进度 ====================

class LearningProgressUpdate(BaseModel):
    """学习进度更新"""
    content_id: str
    content_type: str
    progress_percent: int = Field(..., ge=0, le=100)
    position: Optional[int] = None  # 视频/音频播放位置（秒）
    time_spent_seconds: int = 0


class CoachLearningPoints(BaseModel):
    """教练学习积分"""
    user_id: str
    total_points: int
    current_level: str
    level_progress: int
    next_level_points: int
    category_points: Dict[str, int]


class GrowerLearningTime(BaseModel):
    """成长者学习时长"""
    user_id: str
    total_minutes: int
    total_hours: float
    today_minutes: int
    week_minutes: int
    month_minutes: int
    current_streak: int
    longest_streak: int
    rewards_earned: int


# ============================================================================
# 内容列表 API
# ============================================================================

@router.get("", response_model=PaginatedResponse)
async def get_content_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    source: Optional[str] = None,
    domain: Optional[str] = None,
    keyword: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """获取内容列表"""
    # TODO: 从数据库查询，这里返回模拟数据
    mock_items = [
        {
            "id": "c1",
            "type": "course",
            "source": "platform",
            "title": "行为健康入门",
            "domain": "growth",
            "author": {"name": "平台官方", "verified": True},
            "view_count": 15680,
            "like_count": 1256,
            "duration": 5400,
            "is_free": True,
        },
        {
            "id": "c2",
            "type": "course",
            "source": "expert",
            "title": "正念冥想：从入门到精通",
            "domain": "mindfulness",
            "author": {"name": "李明远", "title": "正念导师", "verified": True},
            "view_count": 12340,
            "like_count": 978,
            "duration": 14400,
            "is_free": False,
        },
    ]

    # 筛选
    filtered = mock_items
    if type:
        filtered = [i for i in filtered if i.get("type") == type]
    if source:
        filtered = [i for i in filtered if i.get("source") == source]
    if domain:
        filtered = [i for i in filtered if i.get("domain") == domain]

    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size

    return PaginatedResponse(
        items=filtered[start:end],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/recommended")
async def get_recommended_content(limit: int = Query(10, ge=1, le=50)):
    """获取推荐内容"""
    # TODO: 基于用户画像推荐
    return [
        {
            "id": "rec1",
            "type": "card",
            "title": "3分钟呼吸放松",
            "icon": "🧘",
            "domain": "stress",
            "reason": "根据您最近的压力状态推荐"
        }
    ]


# ============================================================================
# 课程 API
# ============================================================================

@router.get("/course/{course_id}")
async def get_course_detail(course_id: str):
    """获取课程详情"""
    # TODO: 从数据库查询
    return {
        "id": course_id,
        "title": "行为健康入门",
        "description": "系统学习行为健康基础知识",
        "author": {"id": "platform", "name": "平台官方", "verified": True},
        "domain": "growth",
        "level": "beginner",
        "duration_minutes": 90,
        "chapter_count": 6,
        "lesson_count": 18,
        "chapters": [],
        "is_free": True,
        "enroll_count": 856,
        "rating": 4.8,
        "coach_points": 50,
        "grower_minutes": 90
    }


@router.post("/course/{course_id}/enroll")
async def enroll_course(course_id: str):
    """报名课程"""
    # TODO: 创建用户课程记录
    return {"success": True, "message": "报名成功"}


@router.post("/course/{course_id}/progress")
async def update_course_progress(course_id: str, data: LearningProgressUpdate):
    """更新课程学习进度"""
    # TODO: 更新数据库，计算积分/时长
    return {"success": True, "progress": data.progress_percent}


# ============================================================================
# 视频测试 API
# ============================================================================

@router.get("/video/{video_id}")
async def get_video_detail(video_id: str):
    """获取视频详情"""
    return {
        "video_id": video_id,
        "title": "正念呼吸入门",
        "url": "/videos/mindfulness-breathing.mp4",
        "duration_seconds": 600,
        "has_quiz": True,
        "min_watch_percent": 80,
        "coach_points": 10,
        "grower_minutes": 10
    }


@router.get("/video/{video_id}/quiz")
async def get_video_quiz(video_id: str):
    """获取视频配套测试"""
    # TODO: 从数据库查询
    return {
        "quiz_id": f"quiz_{video_id}",
        "video_id": video_id,
        "title": "正念呼吸知识测试",
        "pass_score": 60,
        "max_attempts": 3,
        "coach_points_bonus": 5,
        "grower_minutes_bonus": 5,
        "questions": [
            {
                "question_id": "q1",
                "order": 1,
                "type": "single",
                "content": "正念呼吸的核心是什么？",
                "options": [
                    {"key": "A", "content": "控制呼吸节奏"},
                    {"key": "B", "content": "觉察当下的呼吸"},
                    {"key": "C", "content": "深呼吸"},
                    {"key": "D", "content": "屏住呼吸"}
                ],
                "correct_answer": "B",
                "explanation": "正念呼吸的核心是觉察当下，而非控制呼吸。",
                "points": 10
            },
            {
                "question_id": "q2",
                "order": 2,
                "type": "judge",
                "content": "正念练习时走神是正常的。",
                "options": [
                    {"key": "true", "content": "正确"},
                    {"key": "false", "content": "错误"}
                ],
                "correct_answer": "true",
                "explanation": "走神是正常的，重要的是觉察到走神并温和地回到呼吸上。",
                "points": 10
            }
        ]
    }


@router.post("/video/{video_id}/quiz/submit")
async def submit_quiz(video_id: str, submission: QuizSubmission, user_id: str = "test_user"):
    """提交视频测试"""
    # TODO: 实际查询测试题目并评分
    # 模拟评分逻辑
    correct_answers = {"q1": "B", "q2": "true"}
    correct_count = 0
    total_count = len(correct_answers)

    for qid, correct in correct_answers.items():
        user_answer = submission.answers.get(qid)
        if user_answer == correct:
            correct_count += 1

    score = int((correct_count / total_count) * 100)
    passed = score >= 60

    # 计算奖励
    points_earned = 10 if passed else 0
    minutes_earned = 10 if passed else 0
    if score == 100:
        points_earned += 5
        minutes_earned += 5

    result = {
        "result_id": f"result_{datetime.now().timestamp()}",
        "quiz_id": submission.quiz_id,
        "user_id": user_id,
        "score": score,
        "correct_count": correct_count,
        "total_count": total_count,
        "passed": passed,
        "points_earned": points_earned,
        "minutes_earned": minutes_earned,
        "attempt_number": 1,
        "submitted_at": datetime.now().isoformat()
    }

    # TODO: 保存结果到数据库，更新用户学习记录

    return result


@router.post("/quiz", response_model=dict)
async def create_quiz(quiz: VideoQuiz):
    """创建视频测试（管理端）"""
    # TODO: 保存到数据库
    return {"success": True, "quiz_id": quiz.quiz_id}


@router.put("/quiz/{quiz_id}")
async def update_quiz(quiz_id: str, quiz: VideoQuiz):
    """更新视频测试（管理端）"""
    # TODO: 更新数据库
    return {"success": True, "quiz_id": quiz_id}


# ============================================================================
# 案例分享 API
# ============================================================================

@router.get("/cases")
async def get_case_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: Optional[str] = None,
    keyword: Optional[str] = None
):
    """获取案例列表"""
    # TODO: 从数据库查询
    mock_cases = [
        {
            "id": "case1",
            "title": "从焦虑到平静：我的21天正念之旅",
            "domain": "emotion",
            "challenge": "工作压力大，经常焦虑失眠...",
            "author": {"display_name": "成长ing", "is_anonymous": False},
            "like_count": 156,
            "helpful_count": 89,
            "comment_count": 23,
            "published_at": "2026-01-15"
        }
    ]

    filtered = mock_cases
    if domain:
        filtered = [c for c in filtered if c.get("domain") == domain]

    return {
        "items": filtered,
        "total": len(filtered),
        "page": page,
        "page_size": page_size
    }


@router.get("/case/{case_id}")
async def get_case_detail(case_id: str):
    """获取案例详情"""
    return {
        "id": case_id,
        "title": "从焦虑到平静：我的21天正念之旅",
        "domain": "emotion",
        "challenge": "工作压力大，经常焦虑失眠，情绪波动明显。",
        "approach": "参加了平台的21天正念打卡活动，每天坚持10分钟冥想。",
        "outcome": "焦虑感明显减轻，睡眠质量提升。",
        "reflection": "正念不是要消除负面情绪，而是学会与它们和平共处。",
        "author": {"display_name": "成长ing", "is_anonymous": False},
        "like_count": 156,
        "helpful_count": 89,
        "comment_count": 23,
        "published_at": "2026-01-15"
    }


@router.post("/case")
async def create_case_share(case: CaseShareCreate, user_id: str = "test_user"):
    """创建案例分享"""
    # TODO: 保存到数据库，设置待审核状态
    case_id = f"case_{datetime.now().timestamp()}"
    return {
        "success": True,
        "id": case_id,
        "message": "提交成功，等待审核"
    }


@router.post("/case/{case_id}/like")
async def like_case(case_id: str, user_id: str = "test_user"):
    """点赞案例"""
    # TODO: 更新数据库
    return {"liked": True, "like_count": 157}


@router.post("/case/{case_id}/helpful")
async def mark_case_helpful(case_id: str, user_id: str = "test_user"):
    """标记案例有帮助"""
    # TODO: 更新数据库
    return {"marked": True, "helpful_count": 90}


# ============================================================================
# 学习进度 API
# ============================================================================

@router.get("/user/learning-progress")
async def get_user_learning_progress(user_id: str = "test_user", user_type: str = "grower"):
    """获取用户学习进度"""
    if user_type == "coach":
        return {
            "type": "coach",
            "data": {
                "user_id": user_id,
                "total_points": 245,
                "current_level": "L1",
                "level_progress": 65,
                "next_level_points": 300,
                "category_points": {
                    "knowledge": 80,
                    "method": 60,
                    "skill": 45,
                    "value": 30,
                    "practice": 20,
                    "case_study": 10
                },
                "certification_progress": {
                    "points_met": False,
                    "exam_passed": False,
                    "practice_hours": 12,
                    "mentor_approved": False
                }
            }
        }
    else:
        return {
            "type": "grower",
            "data": {
                "user_id": user_id,
                "total_minutes": 1850,
                "total_hours": 30.8,
                "today_minutes": 25,
                "week_minutes": 180,
                "month_minutes": 720,
                "current_streak": 7,
                "longest_streak": 14,
                "rewards_earned": 4,
                "domain_minutes": {
                    "emotion": 450,
                    "sleep": 380,
                    "mindfulness": 520,
                    "stress": 300,
                    "growth": 200
                },
                "ongoing_courses": [
                    {
                        "id": "c1",
                        "title": "正念冥想入门",
                        "progress": 65,
                        "last_lesson": "第5章",
                        "last_accessed": "2026-02-04"
                    }
                ],
                "recent_badges": [
                    {"id": "b1", "name": "连续7天", "icon": "🔥", "earned_at": "2026-02-04"}
                ]
            }
        }


@router.post("/user/learning-progress")
async def record_learning_progress(
    data: LearningProgressUpdate,
    user_id: str = "test_user",
    user_type: str = "grower"
):
    """记录学习进度"""
    # TODO: 保存到数据库
    # 计算积分/时长
    if user_type == "coach":
        points_earned = data.time_spent_seconds // 60  # 简化：每分钟1积分
        return {
            "success": True,
            "points_earned": points_earned,
            "total_points": 250  # 模拟更新后总积分
        }
    else:
        minutes_earned = data.time_spent_seconds // 60
        return {
            "success": True,
            "minutes_earned": minutes_earned,
            "total_minutes": 1855  # 模拟更新后总时长
        }


@router.get("/user/learning-history")
async def get_learning_history(
    user_id: str = "test_user",
    page: int = 1,
    page_size: int = 20,
    type: Optional[str] = None
):
    """获取学习历史"""
    # TODO: 从数据库查询
    return {
        "items": [
            {
                "id": "h1",
                "content_id": "c1",
                "content_title": "正念冥想入门",
                "content_type": "course",
                "progress": 65,
                "time_spent_minutes": 45,
                "last_accessed": "2026-02-04T15:30:00"
            }
        ],
        "total": 1,
        "page": page,
        "page_size": page_size
    }


# ============================================================================
# 内容审核 API（管理端）
# ============================================================================

@router.get("/review/queue")
async def get_review_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    source: Optional[str] = None,
    priority: Optional[str] = None
):
    """获取审核队列"""
    # TODO: 从数据库查询待审核内容
    return {
        "items": [
            {
                "content_id": "case_123",
                "content_type": "case_share",
                "content_title": "我的戒烟经历",
                "source": "sharer",
                "author_name": "匿名用户",
                "submitted_at": "2026-02-04T10:00:00",
                "priority": "high"
            }
        ],
        "total": 1,
        "page": page,
        "page_size": page_size
    }


class ReviewDecision(BaseModel):
    """审核决定"""
    content_id: str
    content_type: str
    decision: str  # approved/rejected/revision
    comments: str
    revision_notes: Optional[str] = None
    checklist: Dict[str, bool] = {}


@router.post("/review/submit")
async def submit_review(decision: ReviewDecision, reviewer_id: str = "admin"):
    """提交审核决定"""
    # TODO: 更新内容状态，发送通知
    return {
        "success": True,
        "content_id": decision.content_id,
        "status": decision.decision
    }


# ============================================================================
# 内容详情页 API（新增）
# ============================================================================

@router.get("/detail/{content_type}/{content_id}")
async def get_content_detail(content_type: str, content_id: str, user_id: str = "test_user"):
    """
    获取内容详情（统一接口）

    支持类型：video, card, article
    返回：内容信息 + 用户进度 + 互动状态
    """
    # 模拟数据 - 实际应从数据库查询
    MOCK_DETAILS = {
        "breathing": {
            "id": "breathing",
            "type": "video",
            "title": "2分钟觉察呼吸练习",
            "description": "通过简单的呼吸觉察，帮助你快速平静心神，释放压力。适合任何时间、任何地点进行的正念入门练习。",
            "content": None,
            "video_url": "/videos/breathing-practice.mp4",
            "cover_url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800",
            "duration_seconds": 120,
            "domain": "mindfulness",
            "tags": ["正念", "呼吸", "减压", "入门"],
            "source": "platform",
            "author": {
                "id": "coach001",
                "name": "张老师",
                "avatar": None,
                "role": "认证正念教练",
                "verified": True
            },
            "stats": {
                "view_count": 12847,
                "like_count": 328,
                "comment_count": 56,
                "collect_count": 892
            },
            "has_quiz": True,
            "min_watch_percent": 80,
            "coach_points": 10,
            "grower_minutes": 2,
            "created_at": "2026-01-15T10:00:00Z",
            "updated_at": "2026-02-01T08:30:00Z"
        },
        "breakfast": {
            "id": "breakfast",
            "type": "card",
            "title": "今日一个小练习：观察你的早餐",
            "description": "用觉察的方式吃一顿早餐，感受食物的颜色、气味、口感，培养正念饮食习惯。",
            "content": "### 练习步骤\n\n1. **准备阶段**：找一个安静的用餐环境\n2. **观察阶段**：观察食物的颜色、形状\n3. **感受阶段**：闻一闻食物的香气\n4. **品尝阶段**：慢慢咀嚼，感受口感\n5. **感恩阶段**：感谢这份食物带来的滋养",
            "cover_url": "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=800",
            "domain": "mindfulness",
            "tags": ["正念饮食", "觉察", "习惯养成"],
            "source": "expert",
            "author": {
                "id": "coach002",
                "name": "李教练",
                "role": "营养师 & 正念教练",
                "verified": True
            },
            "stats": {
                "view_count": 5621,
                "like_count": 156,
                "comment_count": 23,
                "collect_count": 412
            },
            "coach_points": 5,
            "grower_minutes": 5,
            "created_at": "2026-02-01T06:00:00Z",
            "updated_at": "2026-02-01T06:00:00Z"
        }
    }

    content = MOCK_DETAILS.get(content_id)
    if not content:
        # 返回通用模拟数据
        content = {
            "id": content_id,
            "type": content_type,
            "title": f"内容 {content_id}",
            "description": "这是一段内容描述",
            "domain": "growth",
            "tags": ["学习", "成长"],
            "source": "platform",
            "author": {"name": "平台", "role": "官方", "verified": True},
            "stats": {"view_count": 100, "like_count": 10, "comment_count": 5, "collect_count": 20},
            "created_at": datetime.now().isoformat()
        }

    # 获取用户与该内容的互动状态
    user_interaction = {
        "liked": False,
        "collected": False,
        "completed": False,
        "progress_percent": 0,
        "last_position": 0,
        "completed_times": 0
    }

    return {
        "content": content,
        "user_interaction": user_interaction
    }


@router.get("/{content_id}/comments")
async def get_content_comments(
    content_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "hot"  # hot, newest, oldest
):
    """获取内容评论"""
    # 模拟数据
    mock_comments = [
        {
            "id": "c1",
            "user": {"id": "u1", "name": "小明", "avatar": None},
            "content": "每天早上做这个练习，精神好多了！已经坚持一周了。",
            "rating": 5,
            "like_count": 24,
            "reply_count": 3,
            "created_at": "2026-02-03T10:30:00Z",
            "is_top": True
        },
        {
            "id": "c2",
            "user": {"id": "u2", "name": "静心", "avatar": None},
            "content": "适合入门，2分钟刚好，不会太长让人坚持不下去。",
            "rating": 5,
            "like_count": 18,
            "reply_count": 1,
            "created_at": "2026-02-02T15:20:00Z"
        },
        {
            "id": "c3",
            "user": {"id": "u3", "name": "成长中", "avatar": None},
            "content": "配合睡前做效果更好，推荐给大家！",
            "rating": 4,
            "like_count": 12,
            "reply_count": 0,
            "created_at": "2026-02-01T22:10:00Z"
        }
    ]

    return {
        "items": mock_comments,
        "total": 56,
        "page": page,
        "page_size": page_size,
        "avg_rating": 4.8,
        "rating_distribution": {5: 42, 4: 10, 3: 3, 2: 1, 1: 0}
    }


@router.post("/{content_id}/comment")
async def add_content_comment(
    content_id: str,
    content: str = Body(..., embed=True),
    rating: Optional[int] = Body(None, embed=True, ge=1, le=5),
    user_id: str = "test_user"
):
    """添加评论"""
    comment_id = f"comment_{datetime.now().timestamp()}"
    return {
        "success": True,
        "comment_id": comment_id,
        "message": "评论发布成功"
    }


@router.get("/feed/related")
async def get_related_feed(
    domain: Optional[str] = None,
    content_id: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20)
):
    """
    获取相关动态（新闻、通知、社区热点）

    用于内容详情页的"相关动态"区块
    """
    # 模拟数据 - 实际应从多个数据源聚合
    mock_feed = [
        {
            "id": "f1",
            "type": "notification",
            "icon": "🔔",
            "title": "本月正念挑战赛开始报名",
            "summary": "21天正念打卡，赢取专属徽章",
            "link": "/activity/mindfulness-challenge",
            "time": "2小时前",
            "is_new": True
        },
        {
            "id": "f2",
            "type": "news",
            "icon": "📰",
            "title": "研究发现：每天5分钟呼吸练习可降低焦虑30%",
            "summary": "发表于《心理健康期刊》的最新研究显示...",
            "link": "/content/article/breathing-research",
            "source": "健康时报",
            "time": "今天",
            "is_new": False
        },
        {
            "id": "f3",
            "type": "community",
            "icon": "🏆",
            "title": "用户分享：坚持正念100天的改变",
            "summary": "从焦虑到平静，我的改变之路",
            "link": "/cases/mindfulness-100days",
            "author": "小王",
            "like_count": 256,
            "time": "昨天"
        },
        {
            "id": "f4",
            "type": "event",
            "icon": "📅",
            "title": "周六线上正念冥想共修",
            "summary": "本周六 9:00，一起静坐30分钟",
            "link": "/activity/weekend-meditation",
            "participants": 128,
            "time": "3天后"
        },
        {
            "id": "f5",
            "type": "tip",
            "icon": "💡",
            "title": "小贴士：呼吸练习的最佳时机",
            "summary": "早晨醒来后、午休前、睡前是最佳练习时段",
            "time": "推荐"
        }
    ]

    # 按领域过滤
    if domain:
        # 简化处理，实际应有更复杂的关联逻辑
        pass

    return {
        "items": mock_feed[:limit],
        "total": len(mock_feed),
        "last_updated": datetime.now().isoformat()
    }


@router.get("/recommendations")
async def get_content_recommendations(
    content_id: Optional[str] = None,
    domain: Optional[str] = None,
    user_id: str = "test_user",
    limit: int = Query(4, ge=1, le=20)
):
    """
    获取推荐内容

    基于：
    - 当前内容的领域/标签
    - 用户学习历史
    - 热门内容
    """
    mock_recommendations = [
        {
            "id": "v2",
            "type": "video",
            "title": "3分钟深度呼吸",
            "cover_url": None,
            "duration_seconds": 180,
            "domain": "mindfulness",
            "view_count": 8562,
            "rating": 4.9
        },
        {
            "id": "v3",
            "type": "video",
            "title": "身体扫描冥想",
            "cover_url": None,
            "duration_seconds": 600,
            "domain": "mindfulness",
            "view_count": 6234,
            "rating": 4.7
        },
        {
            "id": "v4",
            "type": "video",
            "title": "睡前放松指南",
            "cover_url": None,
            "duration_seconds": 480,
            "domain": "sleep",
            "view_count": 12890,
            "rating": 4.8
        },
        {
            "id": "c2",
            "type": "card",
            "title": "办公室1分钟减压",
            "cover_url": None,
            "domain": "stress",
            "view_count": 4521,
            "rating": 4.6
        }
    ]

    # 过滤掉当前内容
    if content_id:
        mock_recommendations = [r for r in mock_recommendations if r["id"] != content_id]

    # 按领域排序（优先相同领域）
    if domain:
        mock_recommendations.sort(key=lambda x: (x["domain"] != domain, -x["view_count"]))

    return {
        "items": mock_recommendations[:limit],
        "reason": "基于您的学习偏好推荐"
    }


@router.post("/{content_id}/like")
async def like_content(content_id: str, user_id: str = "test_user"):
    """点赞内容"""
    # TODO: 更新数据库
    return {"liked": True, "like_count": 329}


@router.post("/{content_id}/collect")
async def collect_content(content_id: str, user_id: str = "test_user"):
    """收藏内容"""
    # TODO: 更新数据库
    return {"collected": True, "collect_count": 893}


@router.get("/user/{user_id}/progress/{content_id}")
async def get_user_content_progress(user_id: str, content_id: str):
    """获取用户对特定内容的学习进度"""
    # 模拟数据
    return {
        "user_id": user_id,
        "content_id": content_id,
        "completed_times": 3,
        "last_completed_at": "2026-02-04T08:30:00Z",
        "total_time_spent_minutes": 6,
        "progress_percent": 100,
        "weekly_goal": {
            "target": 7,
            "completed": 2,
            "description": "每天1次正念练习"
        },
        "streak_days": 2
    }


# ============================================================================
# SSE 实时推送 API
# ============================================================================

async def generate_feed_events(domain: str = None) -> AsyncGenerator[str, None]:
    """生成实时动态事件流"""
    # 发送初始连接确认
    yield f"data: {json.dumps({'type': 'connected', 'message': '动态推送已连接'})}\n\n"

    # 模拟动态数据模板
    feed_templates = [
        {
            "type": "notification",
            "icon": "🔔",
            "title": "新活动：7天正念挑战赛",
            "summary": "参与挑战，赢取专属徽章",
            "link": "/activity/7day-challenge"
        },
        {
            "type": "news",
            "icon": "📰",
            "title": "研究：呼吸练习可有效减压",
            "summary": "哈佛最新研究表明...",
            "link": "/content/article/breathing-research"
        },
        {
            "type": "community",
            "icon": "🏆",
            "title": "恭喜用户「静心」完成百日打卡",
            "summary": "分享你的正念之旅",
            "link": "/cases/100days"
        },
        {
            "type": "event",
            "icon": "📅",
            "title": "周末线上冥想共修",
            "summary": "本周六 9:00 开始",
            "link": "/activity/weekend-meditation"
        },
        {
            "type": "tip",
            "icon": "💡",
            "title": "小贴士：最佳练习时间",
            "summary": "早晨醒来后效果更佳",
            "link": None
        }
    ]

    while True:
        await asyncio.sleep(15)  # 每15秒检查一次

        # 30%概率产生新动态
        if random.random() < 0.3:
            feed = random.choice(feed_templates).copy()
            feed["id"] = f"f_{datetime.now().timestamp()}"
            feed["time"] = "刚刚"
            feed["is_new"] = True

            event_data = {
                "type": "new_feed",
                "data": feed,
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"


async def generate_content_events(content_id: str) -> AsyncGenerator[str, None]:
    """生成内容更新事件流"""
    # 发送初始连接确认
    yield f"data: {json.dumps({'type': 'connected', 'content_id': content_id})}\n\n"

    # 模拟评论数据
    comment_templates = [
        "这个练习真的很有帮助！",
        "坚持了一周，感觉好多了",
        "推荐给朋友们",
        "每天都在做，效果不错",
        "简单易学，很适合入门"
    ]
    user_names = ["小明", "静心", "成长中", "阳光", "微风"]

    base_stats = {"like_count": 328, "view_count": 12847, "collect_count": 892}

    while True:
        await asyncio.sleep(10)  # 每10秒检查一次

        # 40%概率产生更新
        if random.random() < 0.4:
            update_type = random.choice(["new_comment", "stats_update"])

            if update_type == "new_comment":
                comment = {
                    "id": f"c_{datetime.now().timestamp()}",
                    "user": {
                        "name": random.choice(user_names),
                        "avatar": None
                    },
                    "content": random.choice(comment_templates),
                    "rating": random.randint(4, 5),
                    "like_count": 0,
                    "created_at": datetime.now().isoformat()
                }
                event_data = {
                    "type": "new_comment",
                    "data": comment,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 随机增加统计数
                base_stats["like_count"] += random.randint(0, 2)
                base_stats["view_count"] += random.randint(1, 5)
                event_data = {
                    "type": "stats_update",
                    "data": base_stats.copy(),
                    "timestamp": datetime.now().isoformat()
                }

            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"


@router.get("/feed/stream")
async def stream_feed(domain: str = Query(default=None)):
    """
    实时动态流（SSE）

    用于内容详情页的"相关动态"区块实时更新

    使用方式：
    ```javascript
    const eventSource = new EventSource('/api/v1/content/feed/stream?domain=mindfulness');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // 处理新动态
    };
    ```
    """
    logger.info(f"[SSE] Feed stream connected, domain={domain}")
    return StreamingResponse(
        generate_feed_events(domain),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
        }
    )


@router.get("/stream/{content_id}")
async def stream_content_updates(content_id: str):
    """
    内容更新流（SSE）

    用于内容详情页的评论、点赞等实时更新

    使用方式：
    ```javascript
    const eventSource = new EventSource('/api/v1/content/stream/breathing');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_comment') {
            // 添加新评论
        } else if (data.type === 'stats_update') {
            // 更新统计数
        }
    };
    ```
    """
    logger.info(f"[SSE] Content stream connected, content_id={content_id}")
    return StreamingResponse(
        generate_content_events(content_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
