# -*- coding: utf-8 -*-
"""
微行动 REST API
MicroAction API - 微行动任务管理

端点:
- GET  /api/v1/micro-actions/today     — 获取今日任务列表(自动生成)
- POST /api/v1/micro-actions/{id}/complete — 完成任务
- POST /api/v1/micro-actions/{id}/skip    — 跳过任务
- GET  /api/v1/micro-actions/history    — 历史记录(分页)
- GET  /api/v1/micro-actions/stats      — 统计数据
- GET  /api/v1/micro-actions/facts      — 行为事实
- POST /api/v1/micro-actions/coach-assign — 教练为学员指派微行动(审批队列)
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from loguru import logger

from core.database import get_db
from core.micro_action_service import MicroActionTaskService
from core.behavior_facts_service import BehaviorFactsService
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(prefix="/api/v1/micro-actions", tags=["微行动"])

# 服务实例
task_service = MicroActionTaskService()
facts_service = BehaviorFactsService()


# ============ Pydantic 模型 ============

class CompleteRequest(BaseModel):
    note: Optional[str] = Field(None, max_length=500, description="完成备注")
    mood_score: Optional[int] = Field(None, ge=1, le=5, description="心情评分 1-5")


class SkipRequest(BaseModel):
    note: Optional[str] = Field(None, max_length=500, description="跳过原因")


class CoachAssignMicroActionRequest(BaseModel):
    student_id: int = Field(..., description="学员ID")
    title: str = Field(..., min_length=1, max_length=200, description="微行动标题")
    description: str = Field("", max_length=1000, description="任务描述")
    domain: str = Field("exercise", description="领域: nutrition/exercise/sleep/emotion/stress/cognitive/social")
    frequency: str = Field("每天", description="频次: 每天/每周")
    auto_approve: bool = Field(False, description="促进师已审核，直接推送")
    duration_days: int = Field(7, ge=1, le=90, description="持续天数")


# ============ 端点 ============

@router.get("/today")
async def get_today_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取今日微行动任务列表

    如果今日还没有任务，会自动基于用户的干预计划生成
    """
    tasks = task_service.get_today_tasks(db, current_user.id)
    return {
        "tasks": [task_service._task_to_dict(t) for t in tasks],
        "total": len(tasks),
        "completed": sum(1 for t in tasks if t.status == "completed"),
    }


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: int,
    body: CompleteRequest = CompleteRequest(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """完成一个微行动任务"""
    try:
        task = task_service.complete_task(
            db, task_id, current_user.id,
            note=body.note,
            mood_score=body.mood_score,
        )
        # micro_action_complete 积分
        try:
            from core.models import PointTransaction
            db.add(PointTransaction(
                user_id=current_user.id,
                action="micro_action_complete",
                point_type="growth",
                amount=3,
            ))
            db.commit()
        except Exception as e:
            logger.warning(f"积分记录失败: {e}")

        return {
            "success": True,
            "task": task_service._task_to_dict(task),
            "message": "任务已完成",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/skip")
async def skip_task(
    task_id: int,
    body: SkipRequest = SkipRequest(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """跳过一个微行动任务"""
    try:
        task = task_service.skip_task(
            db, task_id, current_user.id,
            note=body.note,
        )
        return {
            "success": True,
            "task": task_service._task_to_dict(task),
            "message": "任务已跳过",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_task_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取微行动历史记录（分页，按日期筛选）"""
    return task_service.get_history(
        db, current_user.id,
        page=page, page_size=page_size,
        date_from=date_from, date_to=date_to,
    )


@router.get("/stats")
async def get_task_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取统计数据：连续天数/完成率/领域分布"""
    return facts_service.get_stats(db, current_user.id)


@router.get("/facts")
async def get_behavior_facts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取行为事实（供 StageRuntime 使用）"""
    facts = facts_service.get_facts(db, current_user.id)
    return facts.to_dict()


# ============ 教练端端点 ============

@router.post("/coach-assign", tags=["教练微行动"])
async def coach_assign_micro_action(
    body: CoachAssignMicroActionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """教练为学员指派微行动 — AI→审核→推送"""
    from core.models import User
    student = db.query(User).filter(User.id == body.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    valid_domains = {"nutrition", "exercise", "sleep", "emotion", "stress", "cognitive", "social"}
    if body.domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"无效领域，可选: {', '.join(valid_domains)}")

    from core.coach_push_queue_service import create_queue_item, create_and_deliver
    kwargs = dict(
        db=db,
        coach_id=current_user.id,
        student_id=body.student_id,
        source_type="micro_action_assign",
        title=f"微行动: {body.title}",
        content=body.description or body.title,
        content_extra={
            "task_title": body.title,
            "task_description": body.description,
            "domain": body.domain,
            "frequency": body.frequency,
            "duration_days": body.duration_days,
        },
        priority="normal",
    )

    if body.auto_approve:
        queue_item = create_and_deliver(**kwargs)
        db.commit()
        return {
            "success": True,
            "queue_item_id": queue_item.id,
            "status": "sent",
            "message": "微行动已推送给学员",
        }
    else:
        queue_item = create_queue_item(**kwargs)
        db.commit()
        return {
            "success": True,
            "queue_item_id": queue_item.id,
            "status": "pending_review",
            "message": "微行动已提交审批队列",
        }
