"""
四层诊断-处方-养成管道 — 完整闭环编排器
放置: api/core/diagnostic_pipeline.py

Layer 1: 行为诊断 (BAPS)        → BehavioralProfile
Layer 2: SPI评估                → spi_score + L1-L5
Layer 3: 能力与支持诊断          → Layer3DiagnosticReport
Layer 4: 行为处方 + 养成         → InterventionPlan + DailyTasks
"""
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field

from core.stage_mapping import stage_resolver
from baps.spi_calculator import calculate_spi_full, calculate_spi_quick, get_prescription_difficulty
from baps.cause_scoring import score_change_causes
from baps.health_competency_assessment import assess_health_competency
from baps.obstacle_assessment import score_obstacles
from baps.urgency_assessment import score_urgency, score_obstacles_v2
from core.diagnostics.cognitive_assessment import (
    score_hbm, ATTRIBUTION_INTERVENTION, TIME_ORIENTATION_INTERVENTION,
)
from core.diagnostics.capability_assessment import score_comb, score_self_efficacy
from core.diagnostics.support_assessment import score_support_system
from core.intervention_combinations import (
    EnhancedInterventionMatcher, S_TO_STAGE5, CATEGORY_DOMAIN,
)
from core.incentive_integration import get_rx_context_from_incentive


# ══════════════════════════════════════════════
# 管道数据容器
# ══════════════════════════════════════════════

@dataclass
class Layer1Result:
    """Layer 1: 行为诊断输出"""
    behavioral_stage: str = "S0"
    bpt_type: str = "mixed"
    big5_profile: dict = field(default_factory=dict)
    capacity_scores: dict = field(default_factory=dict)
    health_competency: dict = field(default_factory=dict)


@dataclass
class Layer2Result:
    """Layer 2: SPI评估输出"""
    spi_score: float = 0.0
    spi_method: str = "quick"
    readiness_level: str = "L1"
    psychological_level: int = 1
    trigger_scores: dict = field(default_factory=dict)
    cause_analysis: dict = field(default_factory=dict)
    urgency: dict = field(default_factory=dict)
    success_level: str = "very_low"


@dataclass
class Layer3Result:
    """Layer 3: 能力与支持诊断输出"""
    hbm: dict = field(default_factory=dict)
    attribution: str = "behavioral"
    time_orientation: str = "future"
    comb: dict = field(default_factory=dict)
    self_efficacy: dict = field(default_factory=dict)
    support: dict = field(default_factory=dict)
    obstacles: dict = field(default_factory=dict)
    strengths: list = field(default_factory=list)
    weaknesses: list = field(default_factory=list)
    priority_interventions: list = field(default_factory=list)


@dataclass
class Layer4Result:
    """Layer 4: 行为处方输出"""
    difficulty: str = "minimal"
    intensity_coefficient: float = 0.2
    max_daily_tasks: int = 1
    interaction_mode: str = "empathy"
    coach_questions: list = field(default_factory=list)
    rx_adjustments: list = field(default_factory=list)
    cultivation_stage: str = "startup"
    monitoring_config: dict = field(default_factory=dict)
    incentive_context: dict = field(default_factory=dict)


@dataclass
class PipelineResult:
    """完整管道输出"""
    user_id: int
    timestamp: datetime
    layer1: Layer1Result
    layer2: Layer2Result
    layer3: Layer3Result | None
    layer4: Layer4Result
    completeness: dict = field(default_factory=dict)


# ══════════════════════════════════════════════
# 养成阶段监测配置
# ══════════════════════════════════════════════

CULTIVATION_MONITORING: dict[str, dict] = {
    "startup": {
        "daily": True,
        "weekly": True,
        "monthly": True,
        "coach_contact_freq": "3次/周",
    },
    "adaptation": {
        "daily": True,
        "weekly": True,
        "monthly": True,
        "coach_contact_freq": "2次/周",
    },
    "stability": {
        "daily": False,
        "weekly": True,
        "monthly": True,
        "coach_contact_freq": "1次/周",
    },
    "internalization": {
        "daily": False,
        "weekly": False,
        "monthly": True,
        "coach_contact_freq": "1次/月",
    },
}


# ══════════════════════════════════════════════
# 管道编排器
# ══════════════════════════════════════════════

class DiagnosticPipeline:
    """
    四层诊断-处方-养成管道

    最小启动: Layer1(TTM7) + Layer2(SPI_quick) → 可生成基础处方
    完整模式: Layer1~3 全部完成 → 精准处方
    """

    def __init__(self, db=None):
        self.db = db
        self.matcher = EnhancedInterventionMatcher(db)

    # ── Layer 1: 行为诊断 ──

    def run_layer1(
        self,
        behavioral_stage: str,
        bpt_type: str = "mixed",
        big5_profile: dict | None = None,
        capacity_scores: dict | None = None,
        health_competency_answers: dict | None = None,
    ) -> Layer1Result:
        result = Layer1Result(
            behavioral_stage=behavioral_stage,
            bpt_type=bpt_type,
            big5_profile=big5_profile or {},
            capacity_scores=capacity_scores or {},
        )

        if health_competency_answers:
            result.health_competency = assess_health_competency(health_competency_answers)

        return result

    # ── Layer 2: SPI 评估 ──

    def run_layer2(
        self,
        *,
        # 完整版参数
        part1_scores: dict[str, int] | None = None,
        part2_scores: list[int] | None = None,
        part3_scores: dict[str, int] | None = None,
        # 快速版参数
        trigger_strength: int | None = None,
        psychological_level: int | None = None,
        capability_resource: int | None = None,
        social_support: int | None = None,
        urgency_val: int | None = None,
    ) -> Layer2Result:
        result = Layer2Result()

        if part1_scores and part2_scores and part3_scores:
            # 完整版
            spi = calculate_spi_full(part1_scores, part2_scores, part3_scores)
            result.spi_score = spi["spi_score"]
            result.spi_method = "full"
            result.readiness_level = spi["readiness_level"]
            result.psychological_level = spi["psychological_level"]
            result.success_level = spi["success_level"]

            # 动因分析
            result.trigger_scores = part1_scores
            result.cause_analysis = score_change_causes(part1_scores)

            # 迫切度
            if part3_scores:
                result.urgency = score_urgency(part3_scores)
        else:
            # 快速版
            spi = calculate_spi_quick(
                trigger_strength or 5,
                psychological_level or 3,
                capability_resource or 5,
                social_support or 5,
                urgency_val or 5,
            )
            result.spi_score = spi["spi_score"]
            result.spi_method = "quick"
            result.readiness_level = spi["readiness_level"]
            result.psychological_level = spi.get("psychological_level", 3)

            if result.spi_score >= 70:
                result.success_level = "high"
            elif result.spi_score >= 50:
                result.success_level = "medium"
            elif result.spi_score >= 30:
                result.success_level = "low"
            else:
                result.success_level = "very_low"

        return result

    # ── Layer 3: 能力与支持诊断 ──

    def run_layer3(
        self,
        hbm_answers: dict[str, list[int]] | None = None,
        attribution: str = "behavioral",
        time_orient: str = "future",
        comb_answers: dict | None = None,
        se_answers: dict[str, int] | None = None,
        support_answers: dict | None = None,
        obstacle_answers: dict | None = None,
        obstacle_version: str = "v2",
    ) -> Layer3Result:
        result = Layer3Result(
            attribution=attribution,
            time_orientation=time_orient,
        )

        if hbm_answers:
            result.hbm = score_hbm(hbm_answers)
            for w in result.hbm.get("weak_dimensions", []):
                result.weaknesses.append(f"HBM-{w}维度偏弱")
            result.priority_interventions.extend(
                result.hbm.get("intervention_priorities", [])[:3]
            )

        # 归因干预
        att_info = ATTRIBUTION_INTERVENTION.get(attribution, {})
        if att_info.get("message"):
            result.priority_interventions.append({
                "dimension": "attribution",
                "strategy": att_info["message"],
            })

        # 时间视角干预
        time_info = TIME_ORIENTATION_INTERVENTION.get(time_orient, "")
        if time_info:
            result.priority_interventions.append({
                "dimension": "time_orientation",
                "strategy": time_info,
            })

        if comb_answers:
            result.comb = score_comb(comb_answers)
            if result.comb.get("bottleneck"):
                result.weaknesses.append(f"COM-B瓶颈: {result.comb['bottleneck']}")

        if se_answers:
            result.self_efficacy = score_self_efficacy(se_answers)
            if result.self_efficacy["level"] == "strong":
                result.strengths.append("自我效能较强")
            elif result.self_efficacy["level"] == "low":
                result.weaknesses.append("自我效能偏低")
                result.priority_interventions.append({
                    "dimension": "self_efficacy",
                    "strategy": "微目标+成功体验",
                })

        if support_answers:
            result.support = score_support_system(support_answers)
            if result.support["support_level"] == "strong":
                result.strengths.append("支持体系充足")
            elif result.support["support_level"] == "weak":
                result.weaknesses.append(
                    f"支持体系薄弱(最弱: {result.support['weakest_layer']})"
                )
                for layer in result.support.get("build_priorities", []):
                    result.priority_interventions.append({
                        "dimension": f"support_{layer}",
                        "strategy": f"加强{layer}圈支持",
                    })

        if obstacle_answers:
            if obstacle_version == "v2":
                result.obstacles = score_obstacles_v2(obstacle_answers)
            else:
                result.obstacles = score_obstacles(obstacle_answers)

        return result

    # ── Layer 4: 处方生成 ──

    def run_layer4(
        self,
        layer1: Layer1Result,
        layer2: Layer2Result,
        layer3: Layer3Result | None = None,
        growth_level: str = "G0",
        streak_days: int = 0,
        cultivation_stage: str = "startup",
    ) -> Layer4Result:
        # 基础: SPI → 难度
        difficulty, intensity, max_tasks = get_prescription_difficulty(layer2.spi_score)

        # 阶段解析
        resolved = stage_resolver.resolve(layer1.behavioral_stage, layer2.readiness_level)

        # 激励上下文
        incentive_ctx = get_rx_context_from_incentive(growth_level, streak_days, {})

        # 激励可能提升 max_tasks
        max_tasks = min(max_tasks, incentive_ctx["max_daily_tasks"])

        # 教练问句
        match_result = self.matcher.match_full(
            stage=layer1.behavioral_stage,
            cause_scores=layer2.trigger_scores or {},
            bpt_type=layer1.bpt_type,
            spi_score=layer2.spi_score,
        )

        # Layer3 影响处方
        rx_adjustments = []
        if layer3:
            # 认知短板 → 追加教育任务
            if layer3.hbm and layer3.hbm.get("dimension_scores", {}).get("self_efficacy", 15) < 9:
                rx_adjustments.append({"type": "add_task", "task": "self_efficacy_building"})

            # 归因偏差
            if layer3.attribution == "fatalistic":
                rx_adjustments.append({"type": "coach_modifier", "modifier": "增强掌控感"})

            # 支持不足
            if layer3.support and layer3.support.get("support_level") == "weak":
                rx_adjustments.append({"type": "add_rx_category", "category": "social_connection"})

            # 障碍调整
            if layer3.obstacles and layer3.obstacles.get("prescription_adjustments"):
                rx_adjustments.extend([
                    {"type": "obstacle_adjustment", **adj}
                    for adj in layer3.obstacles["prescription_adjustments"]
                ])

        result = Layer4Result(
            difficulty=difficulty,
            intensity_coefficient=intensity * incentive_ctx.get("rx_intensity_boost", 1.0),
            max_daily_tasks=max_tasks,
            interaction_mode=match_result["interaction_mode"],
            coach_questions=match_result.get("coach_questions", []),
            rx_adjustments=rx_adjustments,
            cultivation_stage=cultivation_stage,
            monitoring_config=CULTIVATION_MONITORING.get(cultivation_stage, {}),
            incentive_context=incentive_ctx,
        )

        return result

    # ── 完整管道 ──

    def run_full(
        self,
        user_id: int,
        layer1_input: dict,
        layer2_input: dict,
        layer3_input: dict | None = None,
        growth_level: str = "G0",
        streak_days: int = 0,
        cultivation_stage: str = "startup",
    ) -> PipelineResult:
        """一站式运行四层管道"""
        l1 = self.run_layer1(**layer1_input)
        l2 = self.run_layer2(**layer2_input)

        l3 = None
        if layer3_input:
            l3 = self.run_layer3(**layer3_input)

        l4 = self.run_layer4(l1, l2, l3, growth_level, streak_days, cultivation_stage)

        # 完整性判定
        completeness = {
            "layer1_complete": bool(l1.behavioral_stage),
            "layer2_complete": l2.spi_method == "full",
            "layer3_complete": l3 is not None,
            "overall": "full" if (l2.spi_method == "full" and l3) else "minimal",
        }

        return PipelineResult(
            user_id=user_id,
            timestamp=datetime.now(),
            layer1=l1,
            layer2=l2,
            layer3=l3,
            layer4=l4,
            completeness=completeness,
        )

    def run_minimal(
        self,
        user_id: int,
        behavioral_stage: str,
        trigger_strength: int = 5,
        psychological_level: int = 3,
        capability_resource: int = 5,
        social_support: int = 5,
        urgency_val: int = 5,
    ) -> PipelineResult:
        """最小启动: TTM7(7题) + SPI_quick(5题) = 12题 → 基础处方"""
        return self.run_full(
            user_id=user_id,
            layer1_input={"behavioral_stage": behavioral_stage},
            layer2_input={
                "trigger_strength": trigger_strength,
                "psychological_level": psychological_level,
                "capability_resource": capability_resource,
                "social_support": social_support,
                "urgency_val": urgency_val,
            },
        )
