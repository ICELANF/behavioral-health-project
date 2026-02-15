"""
BehaviorOS — CardiacExpertAgent 心血管/心脏康复专家
====================================================
定位: 运动处方行为化 — 解决心脏事件后的恐惧-回避循环
冰山模型: 用户看到运动指导/心率安全建议 ← 行为处方(隐藏) ← 行为诊断(基座)

核心职责:
  - 风险分层评估 (低/中/高危)
  - 运动处方行为化 (渐进脱敏)
  - 心率恐惧脱敏 (systematic_desensitization)
  - 血压行为管理
  - 抗凝/用药行为链
  - 紧急事件响应
  - 家属照护者教育

核心挑战: 心脏事件 → 运动恐惧 → 去适应 → 风险升高 → 更恐惧
行为处方打破此循环: 渐进脱敏 + 心率安全锚定 + 自我效能重建

专家规则: ~18 条
绑定维度: cardiac_risk / exercise_hr / bp / medication / fear / activity

康复阶段 × TTM 映射:
  Phase I(住院期, S0-S1) → 意识提升, 情绪疏导
  Phase II-early(居家早期, S1-S2) → 决策平衡, 渐进暴露
  Phase II-rehab(康复训练期, S2-S3) → 运动处方执行, 自我监控
  Phase III(维持期, S4-S5) → 习惯固化, 自主管理
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from .base_expert_agent import BaseExpertAgent, ExpertRule
from ..core.rx_schemas import (
    ExpertAgentType,
    RxContext,
    RxPrescriptionDTO,
    RxStrategyType,
    RxIntensity,
    CommunicationStyle,
    MicroAction,
)

logger = logging.getLogger(__name__)


# =====================================================================
# 心血管领域常量
# =====================================================================

# 运动恐惧量表阈值 (Tampa Scale of Kinesiophobia 简化)
FEAR_SCORE_HIGH = 40          # 高恐惧
FEAR_SCORE_MODERATE = 25      # 中等恐惧
FEAR_SCORE_LOW = 15           # 低恐惧

# 心率安全边界 (Karvonen 公式简化)
HR_SAFETY_MARGIN = 0.85       # 最大心率占比安全上限
RPE_MAX_ALLOWED = 14          # Borg RPE 最大允许值 (6-20 量表)

# 血压阈值
BP_SYS_HIGH = 160             # 收缩压运动禁忌阈值
BP_SYS_ELEVATED = 140         # 收缩压升高阈值
BP_DIA_HIGH = 100             # 舒张压运动禁忌阈值

# 康复阶段
REHAB_PHASE_MAP = {
    "phase_1": {"name": "住院期", "ttm_range": (0, 1), "max_rpe": 11},
    "phase_2_early": {"name": "居家早期", "ttm_range": (1, 2), "max_rpe": 12},
    "phase_2_rehab": {"name": "康复训练期", "ttm_range": (2, 3), "max_rpe": 13},
    "phase_3": {"name": "维持期", "ttm_range": (4, 6), "max_rpe": 14},
}


class CardiacExpertAgent(BaseExpertAgent):
    """
    心血管/心脏康复专家Agent

    行为处方特色:
      - systematic_desensitization 作为核心策略 (运动恐惧脱敏)
      - 三周渐进暴露协议 (Week1: 散步 → Week2: 快走 → Week3: 轻有氧)
      - 心率安全锚定 (将心率区间与安全感绑定)
      - 家属过度保护干预 (识别并处理家属阻碍康复的行为)

    安全优先:
      - 心率超过阈值 → 立即停止指令
      - RPE > 14 → 降级处方强度
      - 胸痛/眩晕 → 触发 AutoExitHandler
      - 收缩压 > 160 → 暂停运动处方
    """

    @property
    def agent_type(self) -> ExpertAgentType:
        return ExpertAgentType.CARDIAC_EXPERT

    # ---------------------------------------------------------------
    # 领域专业包装 (运动处方 + 恐惧脱敏)
    # ---------------------------------------------------------------

    def apply_domain(
        self,
        rx: RxPrescriptionDTO,
        context: RxContext,
        user_input: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], str]:
        """
        将行为处方包装为心血管康复专业内容

        核心转换:
          consciousness_raising → 心脏康复知识科普, 运动益处教育
          systematic_desensitization → 渐进运动暴露方案, 心率区间适应
          self_monitoring → 运动日记, 心率趋势追踪
          stimulus_control → 运动环境优化, 安全信号设置
          contingency_management → 运动里程碑奖励
          relapse_prevention → 恐惧复发预防, 安全预案
        """
        stage = context.ttm_stage
        domain = context.domain_data
        fear_score = domain.get("exercise_fear_score", 20)
        rehab_phase = domain.get("rehab_phase", "phase_2_early")
        resting_hr = domain.get("resting_hr", 70)
        max_hr = domain.get("max_hr", 220 - domain.get("age", 60))
        recent_bp_sys = domain.get("bp_systolic", 130)
        last_event = domain.get("cardiac_event_type", "unknown")
        days_since_event = domain.get("days_since_event", 30)

        # 目标心率区间计算 (Karvonen)
        target_hr_low, target_hr_high = self._compute_target_hr_zone(
            resting_hr, max_hr, rehab_phase
        )

        # 阶段化运动处方
        exercise_rx = self._generate_exercise_rx(
            rx, stage, fear_score, rehab_phase, target_hr_low, target_hr_high
        )

        # 恐惧脱敏方案 (仅 fear_score > MODERATE 时激活)
        desensitization_plan = None
        if fear_score >= FEAR_SCORE_MODERATE:
            desensitization_plan = self._build_desensitization_protocol(
                fear_score, rehab_phase, resting_hr, target_hr_low
            )

        # 安全守护
        safety_notes = self._build_safety_notes(
            recent_bp_sys, domain.get("bp_diastolic", 80),
            resting_hr, max_hr, domain.get("chest_pain_recent", False)
        )

        domain_content = {
            "rehab_phase": rehab_phase,
            "rehab_phase_name": REHAB_PHASE_MAP.get(
                rehab_phase, {}
            ).get("name", rehab_phase),
            "cardiac_event": last_event,
            "days_since_event": days_since_event,
            "exercise_rx": exercise_rx,
            "target_hr_zone": {
                "low": target_hr_low,
                "high": target_hr_high,
                "resting": resting_hr,
                "max": max_hr,
            },
            "fear_level": (
                "high" if fear_score >= FEAR_SCORE_HIGH
                else "moderate" if fear_score >= FEAR_SCORE_MODERATE
                else "low"
            ),
            "fear_score": fear_score,
            "desensitization_plan": desensitization_plan,
            "safety_notes": safety_notes,
            "bp_status": {
                "systolic": recent_bp_sys,
                "diastolic": domain.get("bp_diastolic", 80),
                "exercise_cleared": recent_bp_sys < BP_SYS_HIGH,
            },
            "applied_strategy": rx.strategy_type.value,
        }

        # 用户消息构建
        user_message = self._build_user_message(
            rx, stage, exercise_rx, fear_score,
            target_hr_low, target_hr_high, safety_notes, context
        )

        return domain_content, user_message

    # ---------------------------------------------------------------
    # 运动处方生成
    # ---------------------------------------------------------------

    def _compute_target_hr_zone(
        self, resting_hr: int, max_hr: int, rehab_phase: str
    ) -> Tuple[int, int]:
        """Karvonen 公式计算目标心率区间"""
        hrr = max_hr - resting_hr  # 心率储备
        phase_intensity = {
            "phase_1": (0.30, 0.45),
            "phase_2_early": (0.40, 0.55),
            "phase_2_rehab": (0.50, 0.70),
            "phase_3": (0.60, 0.80),
        }
        low_pct, high_pct = phase_intensity.get(rehab_phase, (0.40, 0.55))
        target_low = int(resting_hr + hrr * low_pct)
        target_high = int(resting_hr + hrr * high_pct)
        # 安全上限
        absolute_max = int(max_hr * HR_SAFETY_MARGIN)
        target_high = min(target_high, absolute_max)
        return target_low, target_high

    def _generate_exercise_rx(
        self,
        rx: RxPrescriptionDTO,
        stage: int,
        fear_score: float,
        rehab_phase: str,
        target_hr_low: int,
        target_hr_high: int,
    ) -> Dict[str, Any]:
        """生成阶段化运动处方"""

        if stage <= 1:
            # S0-S1: 意识提升期 — 不推运动, 仅教育
            return {
                "type": "education",
                "activity": "无运动要求",
                "focus": "了解运动在心脏康复中的益处与安全性",
                "duration_min": 0,
                "frequency": "教育阅读/观看",
                "rpe_target": None,
                "hr_zone": None,
            }

        if stage == 2:
            # S2: 准备期 — 最小剂量暴露
            return {
                "type": "minimal_exposure",
                "activity": "室内平地散步",
                "focus": "建立运动安全感, 心率感知练习",
                "duration_min": 10,
                "frequency": "每日1次",
                "rpe_target": "9-10 (非常轻松)",
                "hr_zone": f"{target_hr_low}-{target_hr_low + 10}",
                "safety_check": "运动前测血压, 全程可对话",
            }

        if stage == 3:
            # S3: 行动期 — 渐进有氧
            if fear_score >= FEAR_SCORE_HIGH:
                return {
                    "type": "graded_exposure",
                    "activity": "平地快走 (恐惧脱敏模式)",
                    "focus": "渐进增加运动强度, 建立心率安全锚",
                    "duration_min": 15,
                    "frequency": "每日1次, 每周增加2分钟",
                    "rpe_target": "10-11 (轻松)",
                    "hr_zone": f"{target_hr_low}-{target_hr_low + 15}",
                    "safety_check": "佩戴心率监测, 有人陪伴",
                }
            return {
                "type": "structured_aerobic",
                "activity": "快走 / 固定自行车",
                "focus": "有氧耐力建设, 心肺功能恢复",
                "duration_min": 20,
                "frequency": "每周3-5次",
                "rpe_target": "11-13 (较轻松至有些费力)",
                "hr_zone": f"{target_hr_low}-{target_hr_high}",
                "safety_check": "佩戴心率监测",
            }

        # S4+: 维持/自主期
        return {
            "type": "maintenance_aerobic",
            "activity": "快走 / 骑车 / 游泳 (任选)",
            "focus": "维持心肺适能, 享受运动",
            "duration_min": 30,
            "frequency": "每周5次",
            "rpe_target": "12-14 (有些费力)",
            "hr_zone": f"{target_hr_low}-{target_hr_high}",
            "safety_check": "自我监控, 异常即停",
        }

    # ---------------------------------------------------------------
    # 渐进脱敏协议 (核心特色)
    # ---------------------------------------------------------------

    def _build_desensitization_protocol(
        self,
        fear_score: float,
        rehab_phase: str,
        resting_hr: int,
        target_hr_low: int,
    ) -> Dict[str, Any]:
        """
        三周渐进运动暴露方案

        基于 systematic_desensitization 理论:
          恐惧层级构建 → 放松训练 → 逐级暴露 → 认知重评
        """
        protocol = {
            "total_weeks": 3,
            "current_fear_score": fear_score,
            "target_fear_score": max(fear_score - 15, FEAR_SCORE_LOW),
            "weeks": [],
        }

        # Week 1: 原地运动 + 心率感知
        protocol["weeks"].append({
            "week": 1,
            "theme": "安全感建立",
            "activities": [
                "原地踏步 (5分钟, 客厅/安全环境)",
                "腹式呼吸练习 (运动前后各3分钟)",
                "心率自测: 运动后摸脉搏, 记录感受",
            ],
            "exposure_level": "最低 (0.2/1.0)",
            "cognitive_anchor": (
                f"我的安静心率是{resting_hr}次/分, "
                f"目标心率{target_hr_low}次/分是安全的"
            ),
            "success_criteria": "完成3次以上, 无不良反应",
        })

        # Week 2: 室内走动 + 心率区间
        protocol["weeks"].append({
            "week": 2,
            "theme": "信心积累",
            "activities": [
                "室内/走廊步行 (10分钟)",
                "佩戴心率带, 观察心率变化",
                "运动后记录: 心率峰值 + 主观感受 (1-10)",
            ],
            "exposure_level": "低 (0.4/1.0)",
            "cognitive_anchor": (
                f"心率升高到{target_hr_low}是正常的运动反应, "
                f"运动后心率会自然恢复"
            ),
            "success_criteria": "完成5次以上, 恐惧感降低≥2分",
        })

        # Week 3: 户外缓走 + 社会支持
        protocol["weeks"].append({
            "week": 3,
            "theme": "扩展信心",
            "activities": [
                "户外平地散步 (15分钟, 有人陪伴)",
                "心率监测全程佩戴, 关注安全区间",
                "向陪伴者分享感受, 获得正面反馈",
            ],
            "exposure_level": "中低 (0.5/1.0)",
            "cognitive_anchor": "我已经安全完成了两周运动, 我的心脏正在变强",
            "success_criteria": "完成4次以上, 恐惧感降低至中度以下",
        })

        return protocol

    # ---------------------------------------------------------------
    # 安全守护
    # ---------------------------------------------------------------

    def _build_safety_notes(
        self,
        bp_sys: int,
        bp_dia: int,
        resting_hr: int,
        max_hr: int,
        chest_pain_recent: bool,
    ) -> List[Dict[str, str]]:
        """生成安全守护提示"""
        notes = []

        if chest_pain_recent:
            notes.append({
                "level": "critical",
                "message": "近期报告胸痛 — 暂停一切运动, 立即就医",
                "action": "auto_exit",
            })

        if bp_sys >= BP_SYS_HIGH:
            notes.append({
                "level": "high",
                "message": f"收缩压{bp_sys}mmHg — 暂停运动处方, 优先血压控制",
                "action": "suspend_exercise_rx",
            })
        elif bp_sys >= BP_SYS_ELEVATED:
            notes.append({
                "level": "moderate",
                "message": f"收缩压{bp_sys}mmHg偏高 — 降低运动强度, 避免等长收缩",
                "action": "reduce_intensity",
            })

        if resting_hr > 100:
            notes.append({
                "level": "moderate",
                "message": f"静息心率{resting_hr}次/分偏高 — 建议就医排查",
                "action": "flag_for_review",
            })

        if not notes:
            notes.append({
                "level": "normal",
                "message": "各项指标在安全范围内, 可按计划运动",
                "action": "proceed",
            })

        return notes

    # ---------------------------------------------------------------
    # 用户消息构建
    # ---------------------------------------------------------------

    def _build_user_message(
        self,
        rx: RxPrescriptionDTO,
        stage: int,
        exercise_rx: Dict[str, Any],
        fear_score: float,
        target_hr_low: int,
        target_hr_high: int,
        safety_notes: List[Dict[str, str]],
        context: RxContext,
    ) -> str:
        """根据阶段和恐惧水平构建用户可见消息"""

        # 安全优先 — 有 critical 直接返回紧急消息
        critical = [n for n in safety_notes if n["level"] == "critical"]
        if critical:
            return (
                "⚠️ 安全提醒: " + critical[0]["message"] + "\n\n"
                "请先确保安全, 如有不适请拨打急救电话。"
                "待医生确认安全后我们再继续康复计划。"
            )

        # 高血压暂停
        high_bp = [n for n in safety_notes if n["action"] == "suspend_exercise_rx"]
        if high_bp:
            return (
                f"📊 您今天的血压偏高({high_bp[0]['message']})。\n\n"
                "今天我们先不安排运动, 专注于放松和血压管理。\n"
                "建议: ① 腹式呼吸5分钟 ② 回忆放松的场景 ③ 2小时后复测血压\n\n"
                "如果血压持续偏高, 建议联系您的医生调整用药。"
            )

        # 阶段化消息
        style = rx.communication_style

        if stage <= 1:
            messages = {
                CommunicationStyle.EMPATHETIC: (
                    "经历了心脏事件后, 担心和恐惧是完全正常的反应。"
                    "很多人都有类似的感受, 您不是一个人。\n\n"
                    "现在最重要的是了解: 适当的运动其实是心脏康复最有效的方法之一。"
                    "研究表明, 坚持心脏康复运动的人, 再次发作的风险可降低25%。\n\n"
                    "我们不急, 先从了解开始。"
                ),
                CommunicationStyle.DATA_DRIVEN: (
                    f"根据您当前的情况: 静息心率正常, "
                    f"安全运动心率区间为{target_hr_low}-{target_hr_high}次/分。\n\n"
                    "数据显示: 心脏康复运动可降低心血管死亡风险20-25%。"
                    "目前阶段无需运动, 我们先建立安全认知基础。"
                ),
            }
            return messages.get(style, messages[CommunicationStyle.EMPATHETIC])

        if stage == 2:
            if fear_score >= FEAR_SCORE_HIGH:
                return (
                    f"我理解运动让您感到紧张 (恐惧评分: {fear_score}/56)。\n\n"
                    "我为您准备了一个非常温和的开始:\n"
                    f"  · {exercise_rx['activity']}\n"
                    f"  · 时长: 仅{exercise_rx['duration_min']}分钟\n"
                    f"  · 心率: 保持在{exercise_rx.get('hr_zone', '安全区间')}以内\n\n"
                    "这就像在客厅散步一样轻松。"
                    "您愿意明天试一试吗? 有任何不适随时停下来。"
                )
            return (
                f"您已经准备好开始了! 这是今天的计划:\n"
                f"  · {exercise_rx['activity']}\n"
                f"  · {exercise_rx['duration_min']}分钟, "
                f"RPE {exercise_rx.get('rpe_target', '轻松')}\n"
                f"  · 安全心率: {exercise_rx.get('hr_zone', '安全区间')}\n\n"
                "运动前记得测血压, 全程保持能正常说话的强度。"
            )

        if stage == 3:
            return (
                f"👏 您在康复运动上做得很好!\n\n"
                f"今天的运动计划:\n"
                f"  · {exercise_rx['activity']}\n"
                f"  · {exercise_rx['duration_min']}分钟, "
                f"RPE {exercise_rx.get('rpe_target', '适度')}\n"
                f"  · 目标心率: {target_hr_low}-{target_hr_high}次/分\n\n"
                f"记住: 心率在这个区间内您是安全的。"
                f"如果感到不适, 慢慢降速, 不要突然停止。"
            )

        # S4+
        return (
            f"🎉 您已经建立了稳定的运动习惯, 非常棒!\n\n"
            f"本周计划: {exercise_rx['activity']}, "
            f"每次{exercise_rx['duration_min']}分钟, "
            f"{exercise_rx['frequency']}。\n"
            f"心率区间: {target_hr_low}-{target_hr_high}次/分。\n\n"
            f"您的心脏正在变得更强壮。继续保持!"
        )

    # ---------------------------------------------------------------
    # 领域事实构建 (用于规则评估)
    # ---------------------------------------------------------------

    def _build_domain_facts(
        self, context: RxContext, user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        domain = context.domain_data
        return {
            "stage": context.ttm_stage,
            "readiness": context.stage_readiness,
            "stability": context.stage_stability,
            "self_efficacy": context.self_efficacy,
            "capacity": context.capacity_score,
            "recent_adherence": context.recent_adherence,
            "risk_level": context.risk_level,
            # 心血管特定
            "exercise_fear_score": domain.get("exercise_fear_score", 20),
            "rehab_phase": domain.get("rehab_phase", "phase_2_early"),
            "bp_systolic": domain.get("bp_systolic", 130),
            "bp_diastolic": domain.get("bp_diastolic", 80),
            "resting_hr": domain.get("resting_hr", 70),
            "exercise_hr": domain.get("exercise_hr", 0),
            "max_hr": domain.get("max_hr", 160),
            "rpe_current": domain.get("rpe_current", 10),
            "chest_pain_recent": domain.get("chest_pain_recent", False),
            "days_since_event": domain.get("days_since_event", 30),
            "exercise_sessions_7d": domain.get("exercise_sessions_7d", 0),
            "medication_adherence": domain.get("medication_adherence", 0.8),
            "family_overprotection": domain.get("family_overprotection", False),
            # 障碍
            "has_fear_barrier": "fear" in context.active_barriers,
            "barriers": context.active_barriers,
            # BigFive
            "high_N": context.personality.is_high("N"),
            "low_E": context.personality.is_low("E"),
            "high_C": context.personality.is_high("C"),
        }

    # ---------------------------------------------------------------
    # 交接指标提取
    # ---------------------------------------------------------------

    def _extract_handoff_metrics(
        self, user_input: Dict[str, Any], context: RxContext
    ) -> Dict[str, Any]:
        """心血管特化交接指标"""
        base = super()._extract_handoff_metrics(user_input, context)
        domain = user_input.get("domain_data", {})
        base.update({
            "exercise_fear_score": domain.get("exercise_fear_score", 20),
            "chest_pain_recent": domain.get("chest_pain_recent", False),
            "bp_systolic": domain.get("bp_systolic", 130),
            "exercise_adherence_7d": domain.get("exercise_sessions_7d", 0) / 5.0,
        })
        return base

    # ---------------------------------------------------------------
    # 专家规则集 (~18 条)
    # ---------------------------------------------------------------

    def _get_expert_rules(self) -> List[ExpertRule]:
        return [
            # ---- 安全优先 (最高优先级) ----
            ExpertRule(
                rule_id="CR-001",
                name="胸痛紧急停止",
                condition="chest_pain_recent == True",
                action="auto_exit",
                priority=10,
                bind_dimension="cardiac_risk",
                description="近期胸痛报告 → 暂停一切运动处方, 触发紧急响应",
            ),
            ExpertRule(
                rule_id="CR-002",
                name="血压超高禁止运动",
                condition="bp_systolic >= 160 or bp_diastolic >= 100",
                action="suspend_exercise_rx",
                priority=9,
                bind_dimension="bp",
                description="收缩压≥160或舒张压≥100 → 暂停运动处方",
            ),
            ExpertRule(
                rule_id="CR-003",
                name="运动心率超标",
                condition="exercise_hr > max_hr * 0.85",
                action="force_intensity:minimal",
                priority=9,
                bind_dimension="exercise_hr",
                description="实时运动心率超过最大心率85% → 强制最低强度",
            ),
            ExpertRule(
                rule_id="CR-004",
                name="RPE过高警告",
                condition="rpe_current > 14",
                action="force_intensity:low",
                priority=8,
                bind_dimension="exercise_hr",
                description="RPE>14 → 降级运动强度",
            ),

            # ---- 恐惧-回避循环 ----
            ExpertRule(
                rule_id="CR-005",
                name="高运动恐惧脱敏启动",
                condition="exercise_fear_score >= 40",
                action="force_strategy:systematic_desensitization",
                priority=8,
                bind_dimension="fear",
                description="恐惧评分≥40 → 强制使用渐进脱敏策略",
            ),
            ExpertRule(
                rule_id="CR-006",
                name="中等恐惧辅助脱敏",
                condition="exercise_fear_score >= 25 and exercise_fear_score < 40",
                action="augment_strategy:cognitive_restructuring",
                priority=6,
                bind_dimension="fear",
                description="中等恐惧 → 认知重构辅助, 修正灾难化思维",
            ),
            ExpertRule(
                rule_id="CR-007",
                name="恐惧-回避循环检测",
                condition=(
                    "exercise_fear_score >= 25 and "
                    "exercise_sessions_7d <= 1 and "
                    "days_since_event > 30"
                ),
                action="activate_desensitization_protocol",
                priority=7,
                bind_dimension="fear",
                description="恐惧+回避+时间足够 → 激活正式脱敏协议",
            ),

            # ---- 阶段适配 ----
            ExpertRule(
                rule_id="CR-008",
                name="低阶段认知优先",
                condition="stage <= 1",
                action="force_strategy:consciousness_raising",
                priority=7,
                bind_dimension="cardiac_risk",
                description="S0-S1 → 不推运动, 仅提供康复教育",
            ),
            ExpertRule(
                rule_id="CR-009",
                name="S2最小暴露准备",
                condition="stage == 2 and readiness > 0.5",
                action="initiate_minimal_exposure",
                priority=6,
                bind_dimension="cardiac_risk",
                description="S2+就绪 → 启动最小剂量运动暴露",
            ),

            # ---- 人格适配 ----
            ExpertRule(
                rule_id="CR-010",
                name="高神经质情绪安抚",
                condition="high_N == True and exercise_fear_score >= 25",
                action="augment_style:empathetic",
                priority=6,
                bind_dimension="fear",
                description="高N+恐惧 → 优先情绪安抚, 延长脱敏周期",
            ),
            ExpertRule(
                rule_id="CR-011",
                name="高尽责性数据驱动",
                condition="high_C == True",
                action="augment_style:data_driven",
                priority=4,
                bind_dimension="cardiac_risk",
                description="高C → 提供详细心率数据和运动日志",
            ),

            # ---- 血压管理 ----
            ExpertRule(
                rule_id="CR-012",
                name="血压升高降强度",
                condition="bp_systolic >= 140 and bp_systolic < 160",
                action="force_intensity:low",
                priority=7,
                bind_dimension="bp",
                description="收缩压140-159 → 降低运动强度",
            ),

            # ---- 家属过度保护 ----
            ExpertRule(
                rule_id="CR-013",
                name="家属过度保护干预",
                condition="family_overprotection == True and stage >= 2",
                action="provide_family_education",
                priority=5,
                bind_dimension="activity",
                description="家属过度保护阻碍康复运动 → 提供家属教育材料",
            ),

            # ---- 用药行为 ----
            ExpertRule(
                rule_id="CR-014",
                name="低用药依从警告",
                condition="medication_adherence < 0.7",
                action="trigger_adherence_crosscut",
                priority=6,
                bind_dimension="medication",
                description="用药依从率<70% → 触发依从性Agent横切介入",
            ),

            # ---- 运动依从监测 ----
            ExpertRule(
                rule_id="CR-015",
                name="运动依从良好表扬",
                condition="exercise_sessions_7d >= 4 and stage >= 3",
                action="positive_reinforcement",
                priority=4,
                bind_dimension="activity",
                description="周运动≥4次 → 正向强化, 强调成就",
            ),
            ExpertRule(
                rule_id="CR-016",
                name="运动中断回归",
                condition=(
                    "exercise_sessions_7d == 0 and "
                    "stage >= 3 and "
                    "days_since_event > 60"
                ),
                action="stage_regression_check",
                priority=7,
                bind_dimension="activity",
                description="行动期运动中断 → 检查阶段回退, 可能恐惧复发",
            ),

            # ---- 康复阶段晋升 ----
            ExpertRule(
                rule_id="CR-017",
                name="Phase II→III就绪",
                condition=(
                    "rehab_phase == 'phase_2_rehab' and "
                    "exercise_sessions_7d >= 3 and "
                    "exercise_fear_score < 25 and "
                    "stage >= 4"
                ),
                action="phase_promotion_ready",
                priority=5,
                bind_dimension="cardiac_risk",
                description="满足Phase III条件 → 提议康复阶段晋升",
            ),

            # ---- 多病共管 ----
            ExpertRule(
                rule_id="CR-018",
                name="合并代谢异常",
                condition=(
                    "'metabolic' in barriers or "
                    "'diabetes' in barriers"
                ),
                action="coordinate_with_metabolic",
                priority=5,
                bind_dimension="cardiac_risk",
                description="合并代谢问题 → 请求代谢Agent协同",
            ),
        ]
