"""
中医骨科康复 — 教练层 Agent (3个)

#31 tcm_ortho_expert — 中医骨伤科辨证+穴位处方+推拿手法+外用方
#32 pain_management_expert — 多维疼痛评估+中西结合镇痛+慢性疼痛管理
#33 ortho_rehab_planner — 骨科康复方案编制(1-12周分期)+运动与功法融合

教练层规则:
  - review_required = True (所有输出必须经supervisor_reviewer审核)
  - 输出JSON格式 (供教练端解析展示)
  - 可调用其他Agent协作
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# 基础设施导入
try:
    from app.agents.base import BaseAgent, AgentResponse
    from app.agents.registry import register_agent, get_agent
    from app.services.llm_service import get_llm_response
    from app.services.audit import log_agent_action
except ImportError:
    class AgentResponse:
        def __init__(self, content: str = "", metadata: dict = None,
                     handoff: str = "", halt: bool = False):
            self.content = content
            self.metadata = metadata or {}
            self.handoff = handoff
            self.halt = halt

    class BaseAgent:
        name: str = ""
        layer: str = ""
        domain: str = ""
        review_required: bool = True

        async def process_message(self, user_id, message, context=None):
            raise NotImplementedError

    def register_agent(cls):
        return cls

    async def get_agent(name):
        return None

    async def get_llm_response(prompt, system_prompt="", **kwargs):
        return "{}"

    async def log_agent_action(agent, user_id, action, detail=""):
        logger.info(f"[AUDIT] {agent}.{action} user={user_id}: {detail}")


from core.safety.safety_rules_ortho import get_ortho_safety_gate, SafetyLevel
from core.engines.pain_engines import (
    PainScaleEngine, PainAssessEngine, TCMSyndromeEngine, RehabStageEngine,
)
from core.agents.prompts_tcm_ortho import (
    TCM_ORTHO_EXPERT_PROMPT, PAIN_MANAGEMENT_EXPERT_PROMPT,
    ORTHO_REHAB_PLANNER_PROMPT,
)


# ================================================================
# #31 tcm_ortho_expert — 中医骨伤科辨证
# ================================================================

@register_agent
class TCMOrthoExpert(BaseAgent):
    """
    教练层 — 中医骨伤科专家

    核心: 辨证分析 → 穴位处方 → 推拿方案 → 外用方
    安全: 骨折/脱位→影像先行, 神经损伤→转诊, 孕妇禁穴
    协作: tcm_expert(内治), rehab_expert(康复), supervisor(审核)
    """
    name = "tcm_ortho_expert"
    layer = "教练"
    domain = "tcm_ortho_pro"
    review_required = True

    def __init__(self):
        self.safety_gate = get_ortho_safety_gate()
        self.syndrome_engine = TCMSyndromeEngine()

    async def process_message(
        self,
        user_id: int,
        message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResponse:
        context = context or {}
        user_tags = context.get("user_tags", [])

        # ── 安全门 ──
        safety = self.safety_gate.check(message, user_tags)
        if safety.should_halt:
            await log_agent_action(
                self.name, user_id, "SAFETY_HALT",
                str(safety.triggered_rules)
            )
            return AgentResponse(
                content=safety.response_template,
                handoff="crisis_responder",
                halt=True,
                metadata={"safety_level": safety.level.name},
            )

        # ── 辨证引擎 ──
        symptoms = context.get("symptoms", [])
        location = context.get("pain_location", "")
        llm_syndrome = context.get("llm_syndrome_override")

        syndrome_result = self.syndrome_engine.evaluate(
            symptoms=symptoms,
            primary_syndrome=llm_syndrome,
            location=location,
            user_id=user_id,
        )

        # ── LLM 深度辨证 (补充引擎结果) ──
        llm_input = (
            f"患者信息:\n"
            f"  症状: {symptoms}\n"
            f"  部位: {location}\n"
            f"  病史: {context.get('medical_history', '未提供')}\n"
            f"  舌脉: {context.get('tongue_pulse', '未提供')}\n\n"
            f"引擎初步辨证: {syndrome_result.classification}\n"
            f"候选证型: {syndrome_result.scores.get('candidates', [])}\n\n"
            f"教练问题: {message}\n\n"
            f"请输出完整的辨证分析和治疗方案(JSON格式)。"
        )

        llm_response = await get_llm_response(
            prompt=llm_input,
            system_prompt=TCM_ORTHO_EXPERT_PROMPT,
            temperature=0.3,
            max_tokens=2048,
        )

        # ── 构建结构化输出 ──
        acupoints = syndrome_result.metadata.get("acupoints", [])
        local_acupoints = syndrome_result.metadata.get("local_acupoints", [])
        externals = syndrome_result.metadata.get("external_prescriptions", [])

        # 特殊人群禁忌过滤
        contraindications = []
        if safety.level == SafetyLevel.L4_SPECIAL_POP:
            contraindications = safety.contraindications
            # 从穴位处方中移除禁忌穴位
            acupoints = [
                ap for ap in acupoints
                if ap["name"] not in contraindications
            ]

        structured_output = {
            "syndrome_analysis": {
                "primary": syndrome_result.classification,
                "candidates": syndrome_result.scores.get("candidates", []),
                "basis": symptoms,
                "llm_analysis": llm_response,
            },
            "acupoint_prescription": {
                "main_points": acupoints,
                "local_points": local_acupoints,
                "total_count": len(acupoints) + len(local_acupoints),
            },
            "external_prescription": externals,
            "contraindications": contraindications,
            "safety_notes": self._generate_safety_notes(
                syndrome_result.classification, user_tags, location
            ),
            "review_required": True,
            "referrals": self._check_referrals(context),
        }

        await log_agent_action(
            self.name, user_id, "SYNDROME_ANALYSIS",
            f"证型={syndrome_result.classification} "
            f"穴位={len(acupoints)+len(local_acupoints)} "
            f"外用={len(externals)}"
        )

        return AgentResponse(
            content=json.dumps(structured_output, ensure_ascii=False, indent=2),
            metadata={
                "output_type": "structured_json",
                "syndrome": syndrome_result.classification,
                "review_required": True,
            },
        )

    def _generate_safety_notes(
        self, syndrome: str, user_tags: list, location: str
    ) -> list[str]:
        """生成安全注意事项"""
        notes = [
            "本方案需经健康教练审核后方可执行",
            "穴位操作建议在专业人员指导下进行",
            "外用药请先小面积试用，观察有无过敏反应",
        ]
        if "pregnant" in user_tags:
            notes.insert(0, "⚠️ 孕妇禁忌穴位已从处方中移除")
        if "osteoporosis_severe" in user_tags:
            notes.insert(0, "⚠️ 严重骨质疏松, 禁用正骨手法和暴力推拿")
        if "腰" in location:
            notes.append("腰部手法操作前建议排除腰椎不稳/滑脱")
        if "颈" in location:
            notes.append("颈部手法前建议排除椎动脉型颈椎病")
        return notes

    def _check_referrals(self, context: dict) -> list[dict]:
        """检查是否需要协作转介"""
        referrals = []
        if context.get("need_internal_medicine"):
            referrals.append({
                "target_agent": "tcm_expert",
                "reason": "需要中药内服方案配合",
            })
        if context.get("is_postop") or context.get("need_rehab_plan"):
            referrals.append({
                "target_agent": "rehab_expert",
                "reason": "需要现代康复方案协作",
            })
        return referrals


# ================================================================
# #32 pain_management_expert — 疼痛管理专家
# ================================================================

@register_agent
class PainManagementExpert(BaseAgent):
    """
    教练层 — 疼痛管理专家

    核心: 多维评估 → 分级干预 → 中西结合 → 慢性管理
    安全: VAS≥8→转诊, 阿片依赖→警报, 感觉异常→神内
    协作: behavior_coach(行为), adherence_monitor(用药), mental_expert(心理)
    """
    name = "pain_management_expert"
    layer = "教练"
    domain = "pain_mgmt"
    review_required = True

    def __init__(self):
        self.safety_gate = get_ortho_safety_gate()
        self.pain_scale = PainScaleEngine()
        self.pain_assess = PainAssessEngine()

    async def process_message(
        self,
        user_id: int,
        message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResponse:
        context = context or {}
        user_tags = context.get("user_tags", [])

        # ── 安全门 ──
        pain_score = context.get("pain_score", 0)
        safety = self.safety_gate.check(message, user_tags, pain_score)
        if safety.should_halt:
            await log_agent_action(self.name, user_id, "SAFETY_HALT")
            return AgentResponse(
                content=safety.response_template,
                handoff="crisis_responder", halt=True,
            )

        # ── 疼痛量化评估 ──
        nrs = context.get("pain_score", 5)
        location = context.get("pain_location", "")
        duration = context.get("duration_days", 0)
        fi = context.get("functional_impact", {})

        scale_result = self.pain_scale.evaluate(
            nrs=nrs, location=location, duration_days=duration,
            functional_impact=fi, user_id=user_id,
        )

        # ── 综合疼痛评估 ──
        description = context.get("pain_description", message)
        pcs_answers = context.get("pcs_answers")
        pseq_answers = context.get("pseq_answers")

        assess_result = self.pain_assess.evaluate(
            pain_description=description,
            nrs_score=nrs,
            pcs_answers=pcs_answers,
            pseq_answers=pseq_answers,
            user_id=user_id,
        )

        # ── LLM 生成干预方案 ──
        llm_input = (
            f"疼痛评估结果:\n"
            f"  NRS: {nrs}/10 ({scale_result.classification})\n"
            f"  部位: {location}\n"
            f"  持续: {duration}天 ({'慢性' if duration >= 90 else '急性/亚急性'})\n"
            f"  类型: {assess_result.scores.get('pain_type', '未定')}\n"
            f"  PCS: {assess_result.scores.get('pcs_level', '未评估')}\n"
            f"  PSEQ: {assess_result.scores.get('pseq_level', '未评估')}\n"
            f"  综合风险: {assess_result.scores.get('risk_level', '未定')}\n\n"
            f"功能影响: {fi}\n"
            f"教练问题: {message}\n\n"
            f"请制定分级干预方案(JSON格式)。"
        )

        llm_response = await get_llm_response(
            prompt=llm_input,
            system_prompt=PAIN_MANAGEMENT_EXPERT_PROMPT,
            temperature=0.3,
        )

        # ── 构建结构化输出 ──
        intervention_level = self._determine_intervention_level(nrs, assess_result)
        referrals = self._determine_referrals(assess_result, context)

        structured_output = {
            "pain_assessment": {
                "nrs": nrs,
                "intensity": scale_result.classification,
                "type": assess_result.scores.get("pain_type", ""),
                "chronicity": "慢性" if duration >= 90 else ("亚急性" if duration >= 14 else "急性"),
                "pcs_level": assess_result.scores.get("pcs_level", ""),
                "pseq_level": assess_result.scores.get("pseq_level", ""),
                "risk_level": assess_result.scores.get("risk_level", ""),
                "functional_impact": fi,
            },
            "intervention_plan": {
                "level": intervention_level,
                "llm_plan": llm_response,
                "engine_recommendations": (
                    scale_result.recommendations + assess_result.recommendations
                ),
            },
            "monitoring": {
                "reassess_interval_days": 7 if nrs >= 7 else (14 if nrs >= 4 else 30),
                "alert_criteria": self._get_alert_criteria(nrs, assess_result),
            },
            "referrals": referrals,
            "review_required": True,
        }

        if safety.level == SafetyLevel.L2_REFER:
            structured_output["safety_alert"] = {
                "level": "L2_REFER",
                "message": safety.response_template,
                "department": safety.refer_department,
            }

        await log_agent_action(
            self.name, user_id, "PAIN_ASSESSMENT",
            f"NRS={nrs} type={assess_result.scores.get('pain_type')} "
            f"risk={assess_result.scores.get('risk_level')} "
            f"intervention={intervention_level}"
        )

        return AgentResponse(
            content=json.dumps(structured_output, ensure_ascii=False, indent=2),
            metadata={"output_type": "structured_json", "review_required": True},
        )

    def _determine_intervention_level(
        self, nrs: int, assess: Any
    ) -> str:
        risk = assess.scores.get("risk_level", "低")
        if nrs >= 8 or risk == "高":
            return "重度干预(建议就医+过渡缓解)"
        elif nrs >= 4 or risk == "中":
            return "中度干预(功法+外用+穴位+行为)"
        else:
            return "轻度干预(功法+日常调理)"

    def _determine_referrals(
        self, assess: Any, context: dict
    ) -> list[dict]:
        referrals = []
        if assess.scores.get("pcs_level") == "临床显著":
            referrals.append({
                "target_agent": "mental_expert",
                "reason": "疼痛灾难化程度临床显著, 需心理评估",
                "priority": "high",
            })
        if assess.scores.get("pseq_level") == "低":
            referrals.append({
                "target_agent": "behavior_coach",
                "reason": "疼痛自效能低, 需行为干预策略",
                "priority": "medium",
            })
        duration = context.get("duration_days", 0)
        if duration >= 90 and context.get("has_medication"):
            referrals.append({
                "target_agent": "adherence_monitor",
                "reason": "慢性疼痛有用药方案, 需依从性监测",
                "priority": "medium",
            })
        return referrals

    def _get_alert_criteria(self, nrs: int, assess: Any) -> list[str]:
        alerts = ["NRS评分连续上升超过2分", "新出现神经症状(麻木/无力)"]
        if nrs >= 6:
            alerts.append("疼痛影响基本生活自理")
        if assess.scores.get("pcs_level") in ["临界", "临床显著"]:
            alerts.append("出现情绪崩溃/绝望表达")
        return alerts


# ================================================================
# #33 ortho_rehab_planner — 骨科康复方案规划
# ================================================================

@register_agent
class OrthoRehabPlanner(BaseAgent):
    """
    教练层 — 骨科康复方案规划

    核心: 分期方案(1-12周) → 运动+功法融合 → 进度评估 → 动态调整
    安全: 停滞/恶化→升级, 术后→医嘱约束, 急性期→最低强度
    协作: exercise_expert(运动), tcm_ortho_expert(中医), chronic_manager(多病),
          supervisor_reviewer(审核)
    """
    name = "ortho_rehab_planner"
    layer = "教练"
    domain = "ortho_rehab"
    review_required = True

    def __init__(self):
        self.safety_gate = get_ortho_safety_gate()
        self.rehab_engine = RehabStageEngine()

    async def process_message(
        self,
        user_id: int,
        message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResponse:
        context = context or {}
        user_tags = context.get("user_tags", [])

        # ── 安全门 ──
        safety = self.safety_gate.check(message, user_tags)
        if safety.should_halt:
            await log_agent_action(self.name, user_id, "SAFETY_HALT")
            return AgentResponse(
                content=safety.response_template,
                handoff="crisis_responder", halt=True,
            )

        # ── 分期评估 ──
        onset_days = context.get("onset_days", 14)
        is_postop = context.get("is_postop", False)
        nrs = context.get("pain_score", 5)
        rom_pct = context.get("rom_pct", 50.0)
        strength_pct = context.get("strength_pct", 50.0)
        diagnosis = context.get("diagnosis", "")

        stage_result = self.rehab_engine.evaluate(
            onset_days=onset_days,
            diagnosis=diagnosis,
            is_postop=is_postop,
            nrs_current=nrs,
            rom_pct=rom_pct,
            strength_pct=strength_pct,
            user_id=user_id,
        )

        rehab_detail = stage_result.metadata.get("rehab_detail", {})

        # ── LLM 生成完整方案 ──
        llm_input = (
            f"康复评估:\n"
            f"  诊断: {diagnosis}\n"
            f"  发病/术后: {onset_days}天 {'(术后)' if is_postop else ''}\n"
            f"  当前阶段: {stage_result.classification}\n"
            f"  NRS: {nrs}/10\n"
            f"  ROM恢复: {rom_pct}%\n"
            f"  肌力恢复: {strength_pct}%\n"
            f"  进度: {stage_result.scores.get('progress_pct', 0)}%\n\n"
            f"允许活动: {rehab_detail.get('allowed_activities', [])}\n"
            f"禁止活动: {rehab_detail.get('prohibited_activities', [])}\n"
            f"中医方法: {rehab_detail.get('tcm_methods', [])}\n\n"
            f"教练需求: {message}\n\n"
            f"请制定完整的分期康复方案(JSON格式)。"
        )

        llm_response = await get_llm_response(
            prompt=llm_input,
            system_prompt=ORTHO_REHAB_PLANNER_PROMPT,
            temperature=0.3,
            max_tokens=3000,
        )

        # ── 构建结构化输出 ──
        structured_output = {
            "rehab_assessment": {
                "diagnosis": diagnosis,
                "onset_days": onset_days,
                "is_postop": is_postop,
                "current_stage": stage_result.classification,
                "week": stage_result.scores.get("week", 1),
                "progress_pct": stage_result.scores.get("progress_pct", 0),
                "nrs": nrs,
                "rom_pct": rom_pct,
                "strength_pct": strength_pct,
            },
            "current_stage_protocol": {
                "allowed_activities": rehab_detail.get("allowed_activities", []),
                "prohibited_activities": rehab_detail.get("prohibited_activities", []),
                "functional_goals": rehab_detail.get("functional_goals", []),
                "tcm_methods": rehab_detail.get("tcm_methods", []),
            },
            "llm_plan": llm_response,
            "engine_recommendations": stage_result.recommendations,
            "stage_transition": self._check_stage_transition(
                stage_result, nrs, rom_pct, strength_pct
            ),
            "referrals": self._check_referrals(context, stage_result),
            "review_required": True,
        }

        if safety.level == SafetyLevel.L4_SPECIAL_POP:
            structured_output["special_population_notes"] = {
                "contraindications": safety.contraindications,
                "response": safety.response_template,
            }

        await log_agent_action(
            self.name, user_id, "REHAB_PLAN",
            f"stage={stage_result.classification} "
            f"progress={stage_result.scores.get('progress_pct')}% "
            f"week={stage_result.scores.get('week')}"
        )

        return AgentResponse(
            content=json.dumps(structured_output, ensure_ascii=False, indent=2),
            metadata={"output_type": "structured_json", "review_required": True},
        )

    def _check_stage_transition(
        self, stage_result: Any, nrs: int,
        rom_pct: float, strength_pct: float,
    ) -> dict:
        """检查是否满足阶段进阶/退阶条件"""
        stage = stage_result.classification
        transition = {"action": "maintain", "reason": "维持当前阶段"}

        if stage == "急性期" and nrs <= 4:
            transition = {
                "action": "advance",
                "target": "亚急性期",
                "reason": "疼痛控制良好(NRS≤4), 可考虑进入亚急性期",
            }
        elif stage == "亚急性期" and rom_pct >= 50 and nrs <= 5:
            transition = {
                "action": "advance",
                "target": "恢复期",
                "reason": f"ROM恢复{rom_pct}%, NRS≤5, 可进入恢复期",
            }
        elif stage == "恢复期" and rom_pct >= 80 and strength_pct >= 70:
            transition = {
                "action": "advance",
                "target": "强化期",
                "reason": f"ROM={rom_pct}%, 肌力={strength_pct}%, 达标进入强化期",
            }
        elif stage == "强化期" and rom_pct >= 95 and strength_pct >= 90:
            transition = {
                "action": "advance",
                "target": "维持期",
                "reason": "功能基本恢复, 进入维持期",
            }

        # 退阶检查
        if nrs >= 7 and stage not in ["急性期", "亚急性期"]:
            transition = {
                "action": "regress",
                "target": "亚急性期",
                "reason": f"疼痛加重(NRS={nrs}), 建议回退到亚急性期",
                "alert": True,
            }

        return transition

    def _check_referrals(
        self, context: dict, stage_result: Any
    ) -> list[dict]:
        referrals = []
        # 需要运动处方
        if stage_result.classification in ["恢复期", "强化期", "维持期"]:
            referrals.append({
                "target_agent": "exercise_expert",
                "reason": "需要制定详细的渐进性运动处方",
            })
        # 需要中医方案配合
        referrals.append({
            "target_agent": "tcm_ortho_expert",
            "reason": "需要匹配本期的中医治疗方案",
        })
        # 有共病
        if context.get("comorbidities"):
            referrals.append({
                "target_agent": "chronic_manager",
                "reason": f"存在共病: {context['comorbidities']}, 需多病协管",
            })
        # 最终审核
        referrals.append({
            "target_agent": "supervisor_reviewer",
            "reason": "康复方案需5维审核后下发",
        })
        return referrals
