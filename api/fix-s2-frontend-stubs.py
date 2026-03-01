"""
S2 修复: 前端契约兜底路由
=================================
为前端8个API模块引用的所有端点提供兜底stub响应
防止前端因后端未实现而报错/白屏

部署: 复制到 api/frontend_stubs.py, 在 main.py 中注册

特点:
- 只在真正的路由不存在时才生效 (优先级最低)
- 返回符合前端期望的数据结构 (items:[], total:0 等)
- 响应头添加 X-Stub: true 标记, 便于调试
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["frontend-stubs"])

STUB_HEADER = {"X-Stub": "true", "X-Stub-Reason": "endpoint-not-yet-implemented"}


def stub_list(items=None, total=0):
    """标准列表响应"""
    return JSONResponse(
        content={"items": items or [], "total": total},
        headers=STUB_HEADER,
    )


def stub_object(data=None):
    """标准对象响应"""
    return JSONResponse(
        content=data or {},
        headers=STUB_HEADER,
    )


def stub_success(msg="ok"):
    """标准成功响应"""
    return JSONResponse(
        content={"success": True, "message": msg},
        headers=STUB_HEADER,
    )


# ═══════════════════════════════════════════════════════
# coach.ts 兜底 (补 assessments 相关)
# ═══════════════════════════════════════════════════════

@router.get("/coach/assessments")
async def stub_coach_assessments(
    page: int = Query(1), page_size: int = Query(20)
):
    """教练评估列表 - stub"""
    return stub_list()


@router.post("/coach/assessments/{assessment_id}/review")
async def stub_coach_assessment_review(assessment_id: int):
    """审核评估 - stub"""
    return stub_success("assessment review stub")


# ═══════════════════════════════════════════════════════
# assessment.ts 兜底
# ═══════════════════════════════════════════════════════

@router.get("/assessment-assignments/my")
async def stub_assessment_my(
    status: Optional[str] = None,
    page: int = Query(1), page_size: int = Query(20)
):
    """我的评估任务 - stub"""
    return stub_list()


@router.get("/assessment-assignments/{assignment_id}")
async def stub_assessment_detail(assignment_id: int):
    """评估详情 - stub"""
    return stub_object({
        "id": assignment_id,
        "title": "Assessment (stub)",
        "status": "pending",
        "questions": [],
    })


@router.post("/assessment-assignments/{assignment_id}/submit")
async def stub_assessment_submit(assignment_id: int):
    """提交评估 - stub"""
    return stub_success("assessment submitted (stub)")


@router.get("/assessment-assignments/{assignment_id}/result")
async def stub_assessment_result(assignment_id: int):
    """评估结果 - stub"""
    return stub_object({
        "id": assignment_id,
        "score": 0,
        "status": "pending",
        "feedback": "Result not yet available (stub)",
    })


# ═══════════════════════════════════════════════════════
# companion.ts 兜底
# ═══════════════════════════════════════════════════════

@router.get("/companions")
async def stub_companions(page: int = Query(1), page_size: int = Query(20)):
    """同伴列表 - stub"""
    return stub_list()


@router.get("/companions/{companion_id}")
async def stub_companion_detail(companion_id: int):
    """同伴详情 - stub"""
    return stub_object({"id": companion_id, "name": "Companion (stub)", "status": "active"})


@router.post("/companions/invite")
async def stub_companion_invite():
    """邀请同伴 - stub"""
    return stub_success("invitation sent (stub)")


@router.get("/companions/invitations")
async def stub_companion_invitations(page: int = Query(1), page_size: int = Query(20)):
    """收到的邀请 - stub"""
    return stub_list()


@router.post("/companions/invitations/{invitation_id}/accept")
async def stub_invitation_accept(invitation_id: int):
    """接受邀请 - stub"""
    return stub_success("accepted (stub)")


@router.post("/companions/invitations/{invitation_id}/reject")
async def stub_invitation_reject(invitation_id: int):
    """拒绝邀请 - stub"""
    return stub_success("rejected (stub)")


# ═══════════════════════════════════════════════════════
# exam.ts 兜底
# ═══════════════════════════════════════════════════════

@router.get("/exams")
async def stub_exams(page: int = Query(1), page_size: int = Query(20)):
    """考试列表 - stub"""
    return stub_list()


@router.get("/exams/{exam_id}")
async def stub_exam_detail(exam_id: int):
    """考试详情 - stub"""
    return stub_object({
        "id": exam_id, "title": "Exam (stub)",
        "description": "", "duration_minutes": 60,
        "question_count": 0, "status": "draft",
    })


@router.post("/exams/{exam_id}/start")
async def stub_exam_start(exam_id: int):
    """开始考试 - stub"""
    return stub_object({"session_id": 0, "exam_id": exam_id, "status": "not_available"})


@router.post("/exam-sessions/{session_id}/answer")
async def stub_exam_answer(session_id: int):
    """提交答案 - stub"""
    return stub_success("answer recorded (stub)")


@router.post("/exam-sessions/{session_id}/finish")
async def stub_exam_finish(session_id: int):
    """结束考试 - stub"""
    return stub_success("exam finished (stub)")


@router.get("/exam-sessions/{session_id}/result")
async def stub_exam_result(session_id: int):
    """考试结果 - stub"""
    return stub_object({"session_id": session_id, "score": 0, "passed": False, "feedback": "Result (stub)"})


@router.get("/exam-sessions/my")
async def stub_exam_my(page: int = Query(1), page_size: int = Query(20)):
    """我的考试记录 - stub"""
    return stub_list()


# ═══════════════════════════════════════════════════════
# journey.ts 兜底
# ═══════════════════════════════════════════════════════

@router.get("/journey/overview")
async def stub_journey_overview():
    """成长路径概览 - stub"""
    return stub_object({
        "current_level": "observer",
        "next_level": "grower",
        "progress_pct": 0,
        "milestones": [],
    })


@router.get("/journey/progress")
async def stub_journey_progress():
    """成长进度 - stub"""
    return stub_object({"completed": 0, "total": 10, "items": []})


@router.post("/journey/promotion/apply")
async def stub_journey_apply():
    """申请晋级 - stub"""
    return stub_success("promotion application submitted (stub)")


@router.get("/journey/promotion/history")
async def stub_journey_history(page: int = Query(1), page_size: int = Query(20)):
    """晋级历史 - stub"""
    return stub_list()


# ═══════════════════════════════════════════════════════
# learning.ts 兜底
# ═══════════════════════════════════════════════════════

@router.get("/content/courses")
async def stub_courses(page: int = Query(1), page_size: int = Query(20)):
    """课程列表 - stub"""
    return stub_list()


@router.get("/content/courses/{course_id}")
async def stub_course_detail(course_id: int):
    """课程详情 - stub"""
    return stub_object({"id": course_id, "title": "Course (stub)", "chapters": [], "status": "draft"})


@router.get("/content/{content_id}")
async def stub_content_detail(content_id: int):
    """内容详情 - stub"""
    return stub_object({"id": content_id, "title": "Content (stub)", "type": "article", "body": ""})


@router.get("/content/recommended")
async def stub_content_recommended(page: int = Query(1), page_size: int = Query(20)):
    """推荐内容 - stub"""
    return stub_list()


@router.get("/learning/my")
async def stub_learning_my(page: int = Query(1), page_size: int = Query(20)):
    """我的学习 - stub"""
    return stub_list()


@router.get("/learning/credits")
async def stub_learning_credits():
    """学分 - stub"""
    return JSONResponse(
        content={"total_credits": 0, "items": []},
        headers=STUB_HEADER,
    )


@router.post("/content/{content_id}/quiz/submit")
async def stub_quiz_submit(content_id: int):
    """提交测验 - stub"""
    return stub_object({"score": 0, "passed": False, "feedback": "Quiz result (stub)"})


# ═══════════════════════════════════════════════════════
# profile.ts 兜底
# ═══════════════════════════════════════════════════════

@router.get("/profile")
async def stub_profile():
    """个人中心 - stub"""
    return stub_object({
        "id": 0, "name": "", "phone": "", "role": "observer",
        "avatar": "", "level": 1, "credits": 0,
    })


@router.put("/profile")
async def stub_profile_update():
    """更新资料 - stub"""
    return stub_success("profile updated (stub)")


@router.get("/profile/certifications")
async def stub_certifications():
    """我的认证 - stub"""
    return stub_list()


@router.get("/profile/leaderboard")
async def stub_leaderboard(page: int = Query(1), page_size: int = Query(20)):
    """排行榜 - stub"""
    return stub_list()


@router.post("/profile/change-password")
async def stub_change_password():
    """修改密码 - stub"""
    return stub_success("password changed (stub)")


@router.get("/profile/settings")
async def stub_settings():
    """账号设置 - stub"""
    return stub_object({
        "notifications_enabled": True,
        "language": "zh-CN",
        "theme": "light",
    })


@router.put("/profile/settings")
async def stub_settings_update():
    """更新设置 - stub"""
    return stub_success("settings updated (stub)")
