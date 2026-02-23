# -*- coding: utf-8 -*-
"""
评估推送 → 审核 → 下发 API
Assessment Assignment Pipeline API

教练选择评估量表推送给学员 → 学员完成评估 → 自动生成管理目标/行为处方/指导建议
→ 教练审核修改 → 推送给学员

端点:
- POST   /assign             — 教练推送评估给学员
- GET    /my-pending         — 学员查看待完成的评估任务
- POST   /{id}/submit        — 学员提交评估答案
- GET    /review-list        — 教练查看待审核的评估
- PUT    /review-items/{id}  — 教练审核单条内容
- POST   /{id}/push          — 教练推送审核结果给学员
- GET    /{id}/result        — 学员查看已推送的结果
"""
import os
import sys
from typing import Dict, Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db
from core.models import (
    AssessmentAssignment, CoachReviewItem, CoachMessage, User
)
from core.baps.scoring_engine import BAPSScoringEngine
from core.behavioral_profile_service import BehavioralProfileService
from core.brain.stage_runtime import StageRuntimeBuilder, StageInput
from core.brain.policy_gate import RuntimePolicyGate
from core.intervention_matcher import InterventionMatcher
from core.behavior_facts_service import BehaviorFactsService
from core.high_freq_question_service import HighFreqQuestionService
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(prefix="/api/v1/assessment-assignments", tags=["评估推送与审核"])

# 复用现有管道服务实例
scoring_engine = BAPSScoringEngine()
profile_service = BehavioralProfileService()
stage_runtime = StageRuntimeBuilder()
policy_gate = RuntimePolicyGate()
intervention_matcher = InterventionMatcher()
behavior_facts_service = BehaviorFactsService()
high_freq_service = HighFreqQuestionService()

VALID_SCALES = {"ttm7", "big5", "bpt6", "capacity", "spi"}
MAX_PUSH_ITEMS = 3  # 每次推送最多不超过3项
DOMAIN_NAME_MAP = {
    "nutrition": "营养管理",
    "exercise": "运动管理",
    "sleep": "睡眠管理",
    "emotion": "情绪管理",
    "stress": "压力管理",
    "cognitive": "认知管理",
    "social": "社交管理",
    "tcm": "中医调理",
}


# ============ Pydantic 模型 ============

class CustomQuestion(BaseModel):
    text: str = Field(..., description="题目文本")
    scale_type: str = Field(default="likert5", description="评分类型: likert5")


class AssignRequest(BaseModel):
    student_id: int
    scales: List[str] = Field(default=[], description="整套量表列表")
    question_preset: Optional[str] = Field(None, description="高频预设: hf20 / hf50")
    question_ids: Optional[List[str]] = Field(None, description="自选题目ID列表")
    custom_questions: Optional[List[CustomQuestion]] = Field(None, description="自由组合题目（教练自定义，最多3道）")
    note: Optional[str] = None


class SubmitRequest(BaseModel):
    ttm7: Optional[Dict[str, int]] = None
    big_five: Optional[Dict[str, int]] = None
    bpt6: Optional[Dict[str, int]] = None
    capacity: Optional[Dict[str, int]] = None
    spi: Optional[Dict[str, int]] = None
    individual_answers: Optional[Dict[str, int]] = Field(None, description="题目ID→分值（高频题目）")
    custom_answers: Optional[Dict[str, int]] = Field(None, description="自由组合题目ID→分值")


class ReviewItemUpdate(BaseModel):
    status: str = Field(..., description="approved / modified / rejected")
    coach_content: Optional[Dict[str, Any]] = None
    coach_note: Optional[str] = None


# ============ 端点 ============

@router.post("/assign")
async def assign_assessment(
    request: AssignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """教练推送评估给学员（支持量表 + 高频题目 + 上限3验证）"""
    has_scales = bool(request.scales)
    has_preset = bool(request.question_preset)
    has_question_ids = bool(request.question_ids)
    has_custom = bool(request.custom_questions)

    # 至少选一项
    if not has_scales and not has_preset and not has_question_ids and not has_custom:
        raise HTTPException(status_code=400, detail="至少选择一项：量表/高频预设/自选题目/自由组合")

    # 验证量表
    if has_scales:
        invalid = set(request.scales) - VALID_SCALES
        if invalid:
            raise HTTPException(status_code=400, detail=f"无效量表: {invalid}")

    # 验证高频预设
    if has_preset and request.question_preset not in ("hf20", "hf50"):
        raise HTTPException(status_code=400, detail="无效预设，可选: hf20 / hf50")

    # 验证自由组合题目
    if has_custom:
        if len(request.custom_questions) > MAX_PUSH_ITEMS:
            raise HTTPException(
                status_code=400,
                detail=f"自由组合题目最多{MAX_PUSH_ITEMS}道"
            )
        for cq in request.custom_questions:
            if not cq.text.strip():
                raise HTTPException(status_code=400, detail="题目文本不能为空")

    # 计算总推送项数（量表每个算1项，预设算1项，自选题目整体算1项，自由组合算1项）
    total_items = len(request.scales)
    if has_preset:
        total_items += 1
    if has_question_ids:
        total_items += 1
    if has_custom:
        total_items += 1

    if total_items > MAX_PUSH_ITEMS:
        raise HTTPException(
            status_code=400,
            detail=f"每次推送最多{MAX_PUSH_ITEMS}项，当前{total_items}项。建议精简推送内容。"
        )

    # 验证学员存在
    student = db.query(User).filter(User.id == request.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    # 检查是否有未完成的评估
    existing = db.query(AssessmentAssignment).filter(
        AssessmentAssignment.coach_id == current_user.id,
        AssessmentAssignment.student_id == request.student_id,
        AssessmentAssignment.status == "pending",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该学员已有待完成的评估任务")

    # scales 字段存储复合JSON
    scales_data = {
        "scales": request.scales,
        "question_preset": request.question_preset,
        "question_ids": request.question_ids,
        "custom_questions": [
            {"id": f"CQ{i+1}", "text": cq.text.strip(), "scale_type": cq.scale_type}
            for i, cq in enumerate(request.custom_questions)
        ] if has_custom else None,
    }

    assignment = AssessmentAssignment(
        coach_id=current_user.id,
        student_id=request.student_id,
        scales=scales_data,
        note=request.note,
        status="pending",
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {
        "success": True,
        "assignment_id": assignment.id,
        "message": f"已推送评估给 {student.full_name or student.username}",
    }


@router.get("/my-pending")
async def get_my_pending_assignments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """学员查看待完成的评估任务"""
    assignments = db.query(AssessmentAssignment).filter(
        AssessmentAssignment.student_id == current_user.id,
        AssessmentAssignment.status == "pending",
    ).order_by(AssessmentAssignment.created_at.desc()).all()

    result = []
    for a in assignments:
        coach = db.query(User).filter(User.id == a.coach_id).first()
        # scales 可能是旧格式(list)或新格式(dict)
        scales_data = a.scales
        if isinstance(scales_data, list):
            scales_data = {"scales": scales_data, "question_preset": None, "question_ids": None}
        result.append({
            "id": a.id,
            "coach_name": coach.full_name or coach.username if coach else "未知教练",
            "scales": scales_data,
            "note": a.note,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return {"assignments": result}


@router.post("/{assignment_id}/submit")
async def submit_assessment(
    assignment_id: int,
    request: SubmitRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """学员提交评估答案，触发管道生成处方"""
    assignment = db.query(AssessmentAssignment).filter(
        AssessmentAssignment.id == assignment_id,
        AssessmentAssignment.student_id == current_user.id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="评估任务不存在或无权操作")
    if assignment.status != "pending":
        raise HTTPException(status_code=400, detail="该评估任务已完成")

    user_id = current_user.id

    try:
        # === 自由组合题目结果 ===
        custom_result = None
        if request.custom_answers:
            scales_info = assignment.scales if isinstance(assignment.scales, dict) else {}
            custom_qs = scales_info.get("custom_questions", [])
            custom_result = {
                "type": "custom_assessment",
                "answers": request.custom_answers,
                "questions": custom_qs,
                "summary": {
                    "total": len(request.custom_answers),
                    "avg_score": round(sum(request.custom_answers.values()) / max(len(request.custom_answers), 1), 2),
                },
            }

        # === 高频题目部分评分 ===
        partial_result = None
        if request.individual_answers:
            question_ids = list(request.individual_answers.keys())
            partial_result = high_freq_service.score_partial_answers(
                request.individual_answers, question_ids
            )

        # === 复用评估管道（如果有整套量表答案）===
        has_full_scales = request.ttm7 is not None

        # Step 1: BAPS 评分
        ttm7_result = scoring_engine.score_ttm7(request.ttm7, str(user_id)) if request.ttm7 else None
        big5_result = scoring_engine.score_big_five(request.big_five, str(user_id)) if request.big_five else None
        bpt6_result = scoring_engine.score_bpt6(request.bpt6, str(user_id)) if request.bpt6 else None
        capacity_result = scoring_engine.score_capacity(request.capacity, str(user_id)) if request.capacity else None
        spi_result = scoring_engine.score_spi(request.spi, str(user_id)) if request.spi else None

        # 如果只有自由组合题目答案，使用简化管道
        if not has_full_scales and not partial_result and custom_result:
            pipeline_result = {
                "type": "custom_assessment",
                "custom_scores": custom_result,
                "message": "自由组合题目已完成，等待教练查看",
            }
            assignment.pipeline_result = pipeline_result
            assignment.status = "completed"
            assignment.completed_at = datetime.utcnow()
            db.commit()
            return {
                "success": True,
                "assignment_id": assignment.id,
                "pipeline_result": pipeline_result,
                "message": "评估完成，等待教练审核",
            }

        # 如果只有部分题目答案（无整套量表），使用简化管道
        if not has_full_scales and partial_result:
            pipeline_result = {
                "type": "partial_assessment",
                "partial_scores": partial_result,
                "message": "部分题目评分完成，维度信号已生成",
            }
            if custom_result:
                pipeline_result["custom_scores"] = custom_result
            assignment.pipeline_result = pipeline_result
            assignment.status = "completed"
            assignment.completed_at = datetime.utcnow()
            db.commit()
            return {
                "success": True,
                "assignment_id": assignment.id,
                "pipeline_result": pipeline_result,
                "message": "部分评估完成，等待教练审核",
            }

        # Step 2: 生成/更新行为画像
        profile = profile_service.generate_profile(
            db=db, user_id=user_id,
            ttm7_result=ttm7_result,
            big5_result=big5_result,
            bpt6_result=bpt6_result,
            capacity_result=capacity_result,
            spi_result=spi_result,
        )

        # Step 3: 阶段判定
        db_facts = behavior_facts_service.get_facts(db, user_id)
        stage_input = StageInput(
            user_id=user_id,
            current_stage=profile.current_stage.value,
            stage_hypothesis=ttm7_result.current_stage,
            belief_score=(profile.spi_score or 0) / 100,
            awareness_score=0.0,
            capability_score=0.0,
            action_completed_7d=db_facts.action_completed_7d,
            action_interrupt_72h=db_facts.action_interrupt_72h,
            streak_days=db_facts.streak_days,
            spi_score=profile.spi_score or 0,
        )
        runtime_state, decision_logs = stage_runtime.build(stage_input)

        if runtime_state.is_transition:
            profile_service.update_stage(
                db=db, user_id=user_id,
                new_stage=runtime_state.confirmed_stage,
                confidence=profile.stage_confidence,
                stability=runtime_state.stability,
            )
        if runtime_state.risk_flags:
            profile_service.update_risk_flags(db, user_id, runtime_state.risk_flags)

        # Step 4: 干预匹配
        target_domains = profile.primary_domains or ["nutrition", "exercise", "sleep"]
        intervention_plan = intervention_matcher.match(
            user_id=user_id,
            current_stage=runtime_state.confirmed_stage,
            psychological_level=profile.psychological_level.value if profile.psychological_level else "L3",
            bpt6_type=profile.bpt6_type or "mixed",
            spi_score=profile.spi_score or 0,
            target_domains=target_domains,
        )

        # Step 5: PolicyGate
        policy_decision = policy_gate.evaluate(
            runtime_state=runtime_state,
            recommended_mode=profile.interaction_mode.value if profile.interaction_mode else "empathy",
        )
        intervention_plan.policy_decision = policy_decision.action.value

        # 构建管道完整输出
        profile_summary = profile_service.get_profile_summary(db, user_id)
        plan_dict = intervention_matcher.plan_to_dict(intervention_plan)

        pipeline_result = {
            "type": "full_assessment",
            "profile": profile_summary,
            "stage_decision": {
                "from_stage": runtime_state.previous_stage,
                "to_stage": runtime_state.confirmed_stage,
                "is_transition": runtime_state.is_transition,
                "stability": runtime_state.stability,
            },
            "intervention_plan": plan_dict,
        }
        # 合并部分题目评分结果
        if partial_result:
            pipeline_result["partial_scores"] = partial_result
        if custom_result:
            pipeline_result["custom_scores"] = custom_result

        # === 保存到 assignment ===
        assignment.pipeline_result = pipeline_result
        assignment.status = "completed"
        assignment.completed_at = datetime.utcnow()

        # === 拆解管道输出 → CoachReviewItem ===
        domain_interventions = plan_dict.get("domain_interventions", [])
        for di in domain_interventions:
            domain = di.get("domain", "unknown")
            domain_name = di.get("domain_name", DOMAIN_NAME_MAP.get(domain, domain))

            # goal 条目
            core_goal = di.get("core_goal")
            if core_goal:
                db.add(CoachReviewItem(
                    assignment_id=assignment.id,
                    category="goal",
                    domain=domain,
                    original_content={
                        "domain_name": domain_name,
                        "core_goal": core_goal,
                        "strategy": di.get("strategy_name", ""),
                    },
                    status="pending",
                ))

            # prescription 条目
            recommended = di.get("recommended_behaviors", [])
            contraindicated = di.get("contraindicated_behaviors", [])
            if recommended or contraindicated:
                db.add(CoachReviewItem(
                    assignment_id=assignment.id,
                    category="prescription",
                    domain=domain,
                    original_content={
                        "domain_name": domain_name,
                        "recommended_behaviors": recommended,
                        "contraindicated_behaviors": contraindicated,
                    },
                    status="pending",
                ))

            # suggestion 条目
            advice_list = di.get("advice", [])
            if advice_list:
                db.add(CoachReviewItem(
                    assignment_id=assignment.id,
                    category="suggestion",
                    domain=domain,
                    original_content={
                        "domain_name": domain_name,
                        "advice": advice_list,
                    },
                    status="pending",
                ))

        db.commit()

        return {
            "success": True,
            "assignment_id": assignment.id,
            "pipeline_result": pipeline_result,
            "message": "评估完成，等待教练审核",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"评估提交失败: {str(e)}")


@router.get("/review-list")
async def get_review_list(
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """教练查看待审核的评估（status=completed）"""
    assignments = db.query(AssessmentAssignment).filter(
        AssessmentAssignment.coach_id == current_user.id,
        AssessmentAssignment.status.in_(["completed", "reviewed"]),
    ).order_by(AssessmentAssignment.completed_at.desc()).all()

    result = []
    for a in assignments:
        student = db.query(User).filter(User.id == a.student_id).first()
        items = db.query(CoachReviewItem).filter(
            CoachReviewItem.assignment_id == a.id
        ).all()

        result.append({
            "id": a.id,
            "student_id": a.student_id,
            "student_name": student.full_name or student.username if student else "未知",
            "scales": a.scales,
            "note": a.note,
            "status": a.status,
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            "review_items": [
                {
                    "id": item.id,
                    "category": item.category,
                    "domain": item.domain,
                    "original_content": item.original_content,
                    "coach_content": item.coach_content,
                    "status": item.status,
                    "coach_note": item.coach_note,
                }
                for item in items
            ],
        })

    return {"assignments": result}


@router.put("/review-items/{item_id}")
async def update_review_item(
    item_id: int,
    request: ReviewItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """教练审核单条内容"""
    item = db.query(CoachReviewItem).filter(CoachReviewItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="审核条目不存在")

    # 验证归属
    assignment = db.query(AssessmentAssignment).filter(
        AssessmentAssignment.id == item.assignment_id,
        AssessmentAssignment.coach_id == current_user.id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="无权审核此条目")

    if request.status not in ("approved", "modified", "rejected"):
        raise HTTPException(status_code=400, detail="status 必须为 approved/modified/rejected")

    if request.status == "modified" and not request.coach_content:
        raise HTTPException(status_code=400, detail="修改状态必须提供 coach_content")

    item.status = request.status
    item.coach_content = request.coach_content
    item.coach_note = request.coach_note
    item.updated_at = datetime.utcnow()

    db.commit()
    return {"success": True, "item_id": item.id, "status": item.status}


@router.post("/{assignment_id}/push")
async def push_reviewed_result(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """教练推送审核结果给学员"""
    assignment = db.query(AssessmentAssignment).filter(
        AssessmentAssignment.id == assignment_id,
        AssessmentAssignment.coach_id == current_user.id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="评估任务不存在或无权操作")
    if assignment.status not in ("completed", "reviewed"):
        raise HTTPException(status_code=400, detail="该评估任务状态不支持推送")

    # 检查所有 review_items 是否已审核
    items = db.query(CoachReviewItem).filter(
        CoachReviewItem.assignment_id == assignment_id
    ).all()

    pending_items = [i for i in items if i.status == "pending"]
    if pending_items:
        raise HTTPException(
            status_code=400,
            detail=f"还有 {len(pending_items)} 条未审核内容，请先完成审核"
        )

    # 更新状态为已审核（实际推送在审批通过后执行）
    assignment.status = "reviewed"

    # 进入审批队列（AI→审核→推送原则，不直接创建 CoachMessage）
    student = db.query(User).filter(User.id == assignment.student_id).first()
    approved_count = len([i for i in items if i.status in ("approved", "modified")])

    from core.coach_push_queue_service import create_queue_item
    create_queue_item(
        db=db,
        coach_id=current_user.id,
        student_id=assignment.student_id,
        source_type="assessment_push",
        title="评估结果通知",
        content=f"您的行为评估已完成审核，共 {approved_count} 条管理方案待推送，请查看。",
        content_extra={
            "assignment_id": assignment_id,
            "approved_count": approved_count,
        },
        priority="normal",
    )

    db.commit()

    return {
        "success": True,
        "assignment_id": assignment_id,
        "message": f"评估结果已提交审批队列，审批通过后将推送给 {student.full_name or student.username if student else '学员'}",
    }


@router.get("/{assignment_id}/result")
async def get_assignment_result(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """学员查看已推送的结果"""
    assignment = db.query(AssessmentAssignment).filter(
        AssessmentAssignment.id == assignment_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="评估任务不存在")

    # 学员只能看自己的; 教练可看自己推的
    if current_user.id != assignment.student_id and current_user.id != assignment.coach_id:
        if current_user.role.value not in ("admin",):
            raise HTTPException(status_code=403, detail="无权查看")

    if assignment.status not in ("pushed", "reviewed", "completed"):
        raise HTTPException(status_code=400, detail="评估结果尚未就绪")

    items = db.query(CoachReviewItem).filter(
        CoachReviewItem.assignment_id == assignment_id
    ).all()

    # 构建最终内容（coach_content 优先，fallback original_content）
    goals = []
    prescriptions = []
    suggestions = []

    for item in items:
        if item.status == "rejected":
            continue
        content = item.coach_content if item.coach_content else item.original_content
        entry = {
            "id": item.id,
            "domain": item.domain,
            "content": content,
            "coach_note": item.coach_note,
            "is_modified": item.status == "modified",
        }
        if item.category == "goal":
            goals.append(entry)
        elif item.category == "prescription":
            prescriptions.append(entry)
        elif item.category == "suggestion":
            suggestions.append(entry)

    coach = db.query(User).filter(User.id == assignment.coach_id).first()

    return {
        "assignment_id": assignment_id,
        "status": assignment.status,
        "coach_name": coach.full_name or coach.username if coach else "未知",
        "pushed_at": assignment.pushed_at.isoformat() if assignment.pushed_at else None,
        "goals": goals,
        "prescriptions": prescriptions,
        "suggestions": suggestions,
        "profile_summary": assignment.pipeline_result.get("profile") if assignment.pipeline_result else None,
        "stage_decision": assignment.pipeline_result.get("stage_decision") if assignment.pipeline_result else None,
    }


@router.get("/pushed-list")
async def get_pushed_list(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """学员查看所有已推送的评估结果列表"""
    assignments = db.query(AssessmentAssignment).filter(
        AssessmentAssignment.student_id == current_user.id,
        AssessmentAssignment.status == "pushed",
    ).order_by(AssessmentAssignment.pushed_at.desc()).all()

    result = []
    for a in assignments:
        coach = db.query(User).filter(User.id == a.coach_id).first()
        result.append({
            "id": a.id,
            "coach_name": coach.full_name or coach.username if coach else "未知",
            "scales": a.scales,
            "pushed_at": a.pushed_at.isoformat() if a.pushed_at else None,
        })

    return {"assignments": result}
