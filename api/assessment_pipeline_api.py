# -*- coding: utf-8 -*-
"""
评估全流程 API
Assessment Pipeline API - 打通"评估 → 阶段判定 → 行为画像 → 领域干预"完整管道

端点:
- POST /api/v1/assessment/evaluate — 完整评估流水线
- GET  /api/v1/assessment/profile/{user_id} — 获取行为画像
- GET  /api/v1/assessment/intervention-plan/{user_id} — 获取当前干预计划
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
from core.baps.scoring_engine import BAPSScoringEngine
from core.behavioral_profile_service import BehavioralProfileService
from core.brain.stage_runtime import StageRuntimeBuilder, StageInput
from core.brain.policy_gate import RuntimePolicyGate
from core.intervention_matcher import InterventionMatcher
from core.behavior_facts_service import BehaviorFactsService
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(prefix="/api/v1/assessment", tags=["评估管道"])

# 全局实例
scoring_engine = BAPSScoringEngine()
profile_service = BehavioralProfileService()
stage_runtime = StageRuntimeBuilder()
policy_gate = RuntimePolicyGate()
intervention_matcher = InterventionMatcher()
behavior_facts_service = BehaviorFactsService()


# ============ Pydantic 模型 ============

class EvaluateRequest(BaseModel):
    """完整评估请求"""
    # TTM7 必填 (阶段判定基础)
    ttm7: Dict[str, int] = Field(..., description="TTM7答案 {TTM01:1-5, ...TTM21:1-5}")

    # 以下选填 (首次评估建议全部提供)
    big_five: Optional[Dict[str, int]] = Field(None, description="大五人格答案 (50题)")
    bpt6: Optional[Dict[str, int]] = Field(None, description="BPT-6答案 (18题)")
    capacity: Optional[Dict[str, int]] = Field(None, description="CAPACITY答案 (32题)")
    spi: Optional[Dict[str, int]] = Field(None, description="SPI答案 (50题)")

    # 行为事实 (设备/行为记录提供，首次评估可不填)
    behavior_facts: Optional[Dict[str, Any]] = Field(None, description="行为事实 {action_completed_7d, streak_days, ...}")

    class Config:
        json_schema_extra = {
            "example": {
                "ttm7": {"TTM01": 3, "TTM02": 2, "TTM03": 2, "TTM04": 1, "TTM05": 2, "TTM06": 1,
                         "TTM07": 4, "TTM08": 3, "TTM09": 3, "TTM10": 2, "TTM11": 3, "TTM12": 2,
                         "TTM13": 3, "TTM14": 4, "TTM15": 3, "TTM16": 2, "TTM17": 3, "TTM18": 2,
                         "TTM19": 3, "TTM20": 4, "TTM21": 4},
                "big_five": None,
                "bpt6": None,
                "capacity": None,
                "spi": None,
                "behavior_facts": {"action_completed_7d": 0, "streak_days": 0}
            }
        }


# ============ TTM7 题目端点 ============

@router.get("/ttm7-questions")
async def get_ttm7_questions():
    """
    获取 TTM7 改变阶段评估题目列表 (21 题, 7 组)。

    无需认证，供 BehaviorAssessment.vue 动态加载。
    """
    try:
        from core.baps.questionnaires import TTM7Questionnaire
        q = TTM7Questionnaire()
        items = q.get_items()
        # 映射为前端期望的格式: {id, group, text}
        GROUP_MAP = {
            "precontemplation": "第1组", "resistance": "第2组",
            "contemplation": "第3组", "preparation": "第4组",
            "action": "第5组", "maintenance": "第6组",
            "termination": "第7组",
        }
        questions = []
        for item in items:
            questions.append({
                "id": item.get("id", ""),
                "group": GROUP_MAP.get(item.get("dimension", ""), item.get("dimension", "")),
                "text": item.get("text", ""),
            })
        return {"questions": questions, "total": len(questions), "source": "backend"}
    except Exception:
        pass

    # Fallback: 内置标准 TTM7 题目
    return {
        "questions": [
            {"id": "TTM01", "group": "第1组", "text": "我觉得我的生活方式没什么需要改变的"},
            {"id": "TTM02", "group": "第1组", "text": "我没有改变日常习惯的想法"},
            {"id": "TTM03", "group": "第1组", "text": "别人说我需要改变，但我不这样认为"},
            {"id": "TTM04", "group": "第2组", "text": "我知道有些习惯可能不好，但我不想改"},
            {"id": "TTM05", "group": "第2组", "text": "改变太难了，我还没准备好"},
            {"id": "TTM06", "group": "第2组", "text": "现在不是改变的好时机"},
            {"id": "TTM07", "group": "第3组", "text": "我开始意识到改变可能对我有好处"},
            {"id": "TTM08", "group": "第3组", "text": "我在考虑是不是该做些改变"},
            {"id": "TTM09", "group": "第3组", "text": "我偶尔会尝试一些改变，但没有坚持"},
            {"id": "TTM10", "group": "第4组", "text": "我打算在近期开始做一些改变"},
            {"id": "TTM11", "group": "第4组", "text": "我在为改变做准备，比如收集信息"},
            {"id": "TTM12", "group": "第4组", "text": "我已经有了一个初步的行动计划"},
            {"id": "TTM13", "group": "第5组", "text": "我已经开始改变一些具体的习惯了"},
            {"id": "TTM14", "group": "第5组", "text": "我正在积极尝试新的健康行为"},
            {"id": "TTM15", "group": "第5组", "text": "虽然有困难，但我在坚持新习惯"},
            {"id": "TTM16", "group": "第6组", "text": "新的健康习惯已经成为我日常的一部分"},
            {"id": "TTM17", "group": "第6组", "text": "我已经坚持改变超过一个月了"},
            {"id": "TTM18", "group": "第6组", "text": "即使遇到困难，我也能继续保持好习惯"},
            {"id": "TTM19", "group": "第7组", "text": "健康的生活方式对我来说已经很自然"},
            {"id": "TTM20", "group": "第7组", "text": "我不再需要刻意提醒自己保持好习惯"},
            {"id": "TTM21", "group": "第7组", "text": "我经常帮助身边的人也开始改变"},
        ],
        "total": 21,
        "source": "builtin",
    }


# ============ 评估流水线端点 ============

@router.post("/evaluate")
async def evaluate_full_pipeline(
    request: EvaluateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    完整评估流水线

    流程:
    1. BAPS 评分 (TTM7必填 + BIG5/BPT6/CAPACITY/SPI选填)
    2. BehavioralProfileService 生成/更新画像
    3. StageRuntimeBuilder 判定阶段
    4. InterventionMatcher 匹配干预
    5. PolicyGate 过闸
    6. 返回: 画像摘要 + 干预计划

    首次评估: 提交全部5套问卷答案 + TTM7
    后续评估: 仅需 TTM7 (其他维度从画像中读取)
    """
    user_id = current_user.id

    try:
        # === Step 1: BAPS 评分 ===
        ttm7_result = scoring_engine.score_ttm7(request.ttm7, str(user_id))

        big5_result = None
        bpt6_result = None
        capacity_result = None
        spi_result = None

        if request.big_five:
            big5_result = scoring_engine.score_big_five(request.big_five, str(user_id))
        if request.bpt6:
            bpt6_result = scoring_engine.score_bpt6(request.bpt6, str(user_id))
        if request.capacity:
            capacity_result = scoring_engine.score_capacity(request.capacity, str(user_id))
        if request.spi:
            spi_result = scoring_engine.score_spi(request.spi, str(user_id))

        # === Step 2: 生成/更新行为画像 ===
        profile = profile_service.generate_profile(
            db=db,
            user_id=user_id,
            ttm7_result=ttm7_result,
            big5_result=big5_result,
            bpt6_result=bpt6_result,
            capacity_result=capacity_result,
            spi_result=spi_result,
        )

        # === Step 3: StageRuntimeBuilder 阶段判定 ===
        # 从微行动系统获取真实行为事实
        db_facts = behavior_facts_service.get_facts(db, user_id)
        # 合并: 请求中的 behavior_facts 优先（允许前端覆盖）
        facts = request.behavior_facts or {}
        stage_input = StageInput(
            user_id=user_id,
            current_stage=profile.current_stage.value,
            stage_hypothesis=ttm7_result.current_stage,
            belief_score=facts.get("belief_score", (profile.spi_score or 0) / 100),
            awareness_score=facts.get("awareness_score", 0.0),
            capability_score=facts.get("capability_score", 0.0),
            action_completed_7d=facts.get("action_completed_7d", db_facts.action_completed_7d),
            action_interrupt_72h=facts.get("action_interrupt_72h", db_facts.action_interrupt_72h),
            streak_days=facts.get("streak_days", db_facts.streak_days),
            spi_score=profile.spi_score or 0,
        )

        runtime_state, decision_logs = stage_runtime.build(stage_input)

        # 如果阶段变更，更新画像
        if runtime_state.is_transition:
            profile_service.update_stage(
                db=db,
                user_id=user_id,
                new_stage=runtime_state.confirmed_stage,
                confidence=profile.stage_confidence,
                stability=runtime_state.stability,
            )
        # 更新风险标记
        if runtime_state.risk_flags:
            profile_service.update_risk_flags(db, user_id, runtime_state.risk_flags)

        # === Step 4: InterventionMatcher 匹配干预 ===
        target_domains = profile.primary_domains or ["nutrition", "exercise", "sleep"]
        intervention_plan = intervention_matcher.match(
            user_id=user_id,
            current_stage=runtime_state.confirmed_stage,
            psychological_level=profile.psychological_level.value if profile.psychological_level else "L3",
            bpt6_type=profile.bpt6_type or "mixed",
            spi_score=profile.spi_score or 0,
            target_domains=target_domains,
        )

        # === Step 5: PolicyGate 过闸 ===
        policy_decision = policy_gate.evaluate(
            runtime_state=runtime_state,
            recommended_mode=profile.interaction_mode.value if profile.interaction_mode else "empathy",
        )
        intervention_plan.policy_decision = policy_decision.action.value

        # === Step 6: 提交 & 返回 ===
        db.commit()

        return {
            "success": True,
            "user_id": user_id,
            # 画像摘要
            "profile": profile_service.get_profile_summary(db, user_id),
            # 阶段判定
            "stage_decision": {
                "from_stage": runtime_state.previous_stage,
                "to_stage": runtime_state.confirmed_stage,
                "is_transition": runtime_state.is_transition,
                "stability": runtime_state.stability,
                "risk_flags": runtime_state.risk_flags,
                "reason": runtime_state.decision_reason,
            },
            # 策略闸门
            "policy": {
                "action": policy_decision.action.value,
                "reason": policy_decision.reason,
                "intervention_allowed": policy_decision.intervention_allowed,
                "allowed_modes": policy_decision.allowed_modes,
                "escalation_target": policy_decision.escalation_target,
            },
            # 干预计划
            "intervention_plan": intervention_matcher.plan_to_dict(intervention_plan),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"评估失败: {str(e)}")


@router.get("/profile/me")
async def get_my_behavioral_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取当前用户自己的行为画像 (去诊断化)"""
    result = profile_service.get_profile_summary(db, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="尚未完成评估，暂无行为画像")
    return result


@router.get("/profile/{user_id}")
async def get_behavioral_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取用户行为画像

    - 普通用户只能查看自己的画像 (去诊断化)
    - 教练/管理员可查看任何用户 (完整视图)
    """
    # 权限: 普通用户只能看自己
    if current_user.id != user_id and current_user.role.value not in ("coach", "admin", "supervisor", "promoter"):
        raise HTTPException(status_code=403, detail="无权查看其他用户画像")

    # 教练视图 vs 用户视图
    if current_user.role.value in ("coach", "admin", "supervisor", "promoter"):
        result = profile_service.get_coach_view(db, user_id)
    else:
        result = profile_service.get_profile_summary(db, user_id)

    if not result:
        raise HTTPException(status_code=404, detail="尚未完成评估，暂无行为画像")

    return result


@router.get("/intervention-plan/{user_id}")
async def get_intervention_plan(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取用户当前干预计划

    基于最新行为画像实时生成干预匹配
    """
    # 权限
    if current_user.id != user_id and current_user.role.value not in ("coach", "admin", "supervisor", "promoter"):
        raise HTTPException(status_code=403, detail="无权查看其他用户干预计划")

    profile = profile_service.get_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="尚未完成评估，暂无干预计划")

    target_domains = profile.primary_domains or ["nutrition", "exercise", "sleep"]

    plan = intervention_matcher.match(
        user_id=user_id,
        current_stage=profile.current_stage.value if profile.current_stage else "S0",
        psychological_level=profile.psychological_level.value if profile.psychological_level else "L3",
        bpt6_type=profile.bpt6_type or "mixed",
        spi_score=profile.spi_score or 0,
        target_domains=target_domains,
    )

    return intervention_matcher.plan_to_dict(plan)
