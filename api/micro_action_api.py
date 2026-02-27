# -*- coding: utf-8 -*-
"""
微行动 REST API
MicroAction API - 微行动任务管理

遵循平台四原则（详见 core/micro_action_service.py 铁律文档）:
  原则一：三来源任务体系（L1教练指定 > L2 AI推荐 > L3用户自选）
  原则二：关注问题直接导出任务
  原则三：四维隐性数据驱动
  原则四：AI必须先于人工

端点:
  GET  /api/v1/micro-actions/today        — 获取今日任务列表（自动生成）
  GET  /api/v1/micro-actions/task-pool    — 获取三来源候选任务池（新增）
  POST /api/v1/micro-actions/self-add     — 用户自选添加任务（新增，原则一L3）
  PATCH /api/v1/micro-actions/focus-areas — 更新关注领域（新增，原则二）
  POST /api/v1/micro-actions/{id}/complete— 完成任务（含差异化积分）
  POST /api/v1/micro-actions/{id}/skip   — 跳过任务（含画像反哺）
  GET  /api/v1/micro-actions/history      — 历史记录（分页）
  GET  /api/v1/micro-actions/stats        — 统计数据
  GET  /api/v1/micro-actions/facts        — 行为事实
  POST /api/v1/micro-actions/coach-assign — 教练为学员指派微行动（审批队列）
"""
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from loguru import logger

from core.database import get_db
from core.micro_action_service import MicroActionTaskService, VALID_DOMAINS, DOMAIN_NAMES
from core.behavior_facts_service import BehaviorFactsService
from core.models import BehavioralProfile
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(prefix="/api/v1/micro-actions", tags=["微行动"])

task_service = MicroActionTaskService()
facts_service = BehaviorFactsService()


# ============ Pydantic 模型 ============

class CompleteRequest(BaseModel):
    note: Optional[str] = Field(None, max_length=500, description="完成备注")
    mood_score: Optional[int] = Field(None, ge=1, le=5, description="心情评分 1-5")


class SkipRequest(BaseModel):
    note: Optional[str] = Field(None, max_length=500, description="跳过原因")


class SelfAddRequest(BaseModel):
    """用户自选任务请求（原则四：候选池由AI预生成，用户从中确认）"""
    domain: str = Field(..., description=f"领域: {', '.join(VALID_DOMAINS)}")
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: str = Field("", max_length=500, description="任务描述")
    difficulty: str = Field("easy", description="难度: easy/moderate/challenging")
    rx_id: Optional[str] = Field(None, description="来源处方ID（来自 task-pool 的 rx_id）")

    @validator("domain")
    def validate_domain(cls, v):
        if v not in VALID_DOMAINS:
            raise ValueError(f"无效领域，可选: {', '.join(sorted(VALID_DOMAINS))}")
        return v

    @validator("difficulty")
    def validate_difficulty(cls, v):
        if v not in {"easy", "moderate", "challenging"}:
            raise ValueError("难度只能是 easy / moderate / challenging")
        return v


class FocusAreasRequest(BaseModel):
    """更新关注领域请求（原则二：关注问题直接导出任务）"""
    domains: List[str] = Field(..., description="关注领域列表，最多8个")

    @validator("domains")
    def validate_domains(cls, v):
        cleaned = [d for d in v if d in VALID_DOMAINS]
        if not cleaned:
            raise ValueError(f"至少选择一个有效领域: {', '.join(sorted(VALID_DOMAINS))}")
        return cleaned[:8]


class CoachAssignMicroActionRequest(BaseModel):
    student_id: int = Field(..., description="学员ID")
    title: str = Field(..., min_length=1, max_length=200, description="微行动标题")
    description: str = Field("", max_length=1000, description="任务描述")
    domain: str = Field("exercise", description="领域")
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

    如果今日还没有任务，会自动基于四维隐性数据生成（原则三）
    任务按来源排序：教练指定 > AI推荐/计划 > 自选 > 系统
    """
    tasks = task_service.get_today_tasks(db, current_user.id)

    # 按来源优先级排序显示
    source_order = {
        "coach_assigned": 0, "coach": 0,
        "ai_recommended": 1,
        "intervention_plan": 2,
        "user_selected": 3,
        "system": 4,
    }
    tasks_sorted = sorted(tasks, key=lambda t: source_order.get(t.source or "system", 5))

    return {
        "tasks": [task_service._task_to_dict(t) for t in tasks_sorted],
        "total": len(tasks),
        "completed": sum(1 for t in tasks if t.status == "completed"),
    }


@router.get("/task-pool")
async def get_task_pool(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取三来源候选任务池（原则一：L1教练指定 / L2 AI推荐 / L3自选）

    不写DB，供"添加任务"面板展示。
    数据由四维隐性数据驱动（原则三）：
      1. 用户关注领域 (primary_domains)
      2. 行为轨迹 (BehaviorFacts)
      3. 穿戴设备数据
      4. 认知调查结果 (BehavioralProfile)

    返回:
      focus_domains   — 当前关注领域列表
      covered_today   — 今日已有任务的领域（前端去重提示用）
      coach_pending   — L1：教练指定待执行任务（只读展示）
      ai_recommended  — L2：AI推荐（基于关注领域，优先展示）
      user_selectable — L3：按领域分组的自选候选池
    """
    pool = task_service.get_task_pool_by_focus(db, current_user.id)
    return pool


@router.post("/self-add")
async def self_add_task(
    body: SelfAddRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    用户自选添加任务（原则一 L3 + 原则四）

    铁律：
    - 任务内容必须来自 /task-pool 的 AI 预生成候选池（rx_id 字段追溯来源）
    - 今日总任务上限 5 个
    - 同领域当日仅允许 1 个自选任务
    - 自动通知教练（知情，非审核）
    - 自动更新关注领域（数据闭环）

    积分: 3~5 pts（由 source=user_selected + difficulty 决定）
    """
    try:
        task = task_service.user_self_add_task(
            db=db,
            user_id=current_user.id,
            domain=body.domain,
            title=body.title,
            description=body.description,
            difficulty=body.difficulty,
            rx_id=body.rx_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "task": task_service._task_to_dict(task),
        "message": f"已添加「{body.title}」到今日任务",
    }


@router.patch("/focus-areas")
async def update_focus_areas(
    body: FocusAreasRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    更新用户关注领域（原则二：关注问题直接导出任务）

    写入 BehavioralProfile.primary_domains
    下次生成任务时优先从这些领域推荐（原则二铁律）
    """
    cleaned = body.domains

    profile = (
        db.query(BehavioralProfile)
        .filter(BehavioralProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        profile = BehavioralProfile(
            user_id=current_user.id,
            primary_domains=cleaned,
        )
        db.add(profile)
    else:
        profile.primary_domains = cleaned

    db.commit()
    logger.info(f"关注领域更新: user={current_user.id}, domains={cleaned}")

    return {
        "success": True,
        "focus_domains": cleaned,
        "domain_names": {d: DOMAIN_NAMES.get(d, d) for d in cleaned},
        "message": "关注领域已更新，下次任务生成将优先推荐这些领域",
    }


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: int,
    body: CompleteRequest = CompleteRequest(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    完成一个微行动任务

    积分差异化（原则一铁律）:
      来源权重：coach_assigned(5) > ai_recommended(4) > user_selected(3) > 计划(3) > 系统(2)
      难度加成：challenging(+2) / moderate(+1) / easy(+0)
    完成后自动反哺 BehavioralProfile（数据闭环）
    """
    try:
        task = task_service.complete_task(
            db, task_id, current_user.id,
            note=body.note,
            mood_score=body.mood_score,
        )

        # 差异化积分（原则一：来源 × 难度权重）
        points = task_service.get_completion_points(task)
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

        return {
            "success": True,
            "task": task_service._task_to_dict(task),
            "points_earned": points,
            "message": f"任务已完成，获得 {points} 成长积分",
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
    """
    跳过一个微行动任务

    连续跳过3次同领域 → 自动调整该领域在关注列表中的优先级（数据闭环）
    """
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
    """获取统计数据：连续天数 / 完成率 / 领域分布"""
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
    """
    教练为学员指派微行动（原则一 L1 + 原则四：AI→审核→推送）

    铁律：
    - 教练在指派前，应先通过 copilot_prescription_service 获取 AI 建议
    - auto_approve=False（默认）：进入 coach_push_queue 等待审核
    - auto_approve=True：促进师已审核，直接推送（需 coach 级别以上）
    - 禁止绕过 coach_push_queue 直接写入学员任务
    """
    from core.models import User
    student = db.query(User).filter(User.id == body.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    if body.domain not in VALID_DOMAINS:
        raise HTTPException(status_code=400, detail=f"无效领域，可选: {', '.join(sorted(VALID_DOMAINS))}")

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
            "domain_name": DOMAIN_NAMES.get(body.domain, body.domain),
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
            "message": "微行动已提交审批队列，待促进师审核后推送",
        }
