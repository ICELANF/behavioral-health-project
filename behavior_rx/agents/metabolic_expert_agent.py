"""
BehaviorOS — MetabolicExpertAgent 代谢内分泌专家
=================================================
定位: 代谢数据 × 行为处方 = 个性化代谢行为干预
冰山模型: 用户看到血糖/营养建议 ← 行为处方(隐藏) ← 行为诊断(基座)

核心职责:
  - 血糖趋势解读 & 行为归因
  - 营养行为处方 (饮食行为化)
  - 运动代谢处方 (运动行为化)
  - 体重管理行为 (减重行为链)
  - 代谢综合征多维协同
  - 药物-行为整合

专家规则: ~20 条
绑定维度: glucose / weight / bp / nutrition / exercise / adherence
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
    CommunicationStyle,
)

logger = logging.getLogger(__name__)


class MetabolicExpertAgent(BaseExpertAgent):
    """
    代谢内分泌专家Agent

    冰山模型示例:
      水面上 (用户看到):
        "你的空腹血糖连续3天偏高,可能和晚餐时间过晚有关。
         建议试试把晚餐提前到6:30之前,先坚持3天看看效果。"

      水面下 (行为处方):
        strategy=stimulus_control, intensity=moderate
        micro_action: "晚餐时间提前到6:30"
        trigger: "设置6:00闹钟提醒准备晚餐"
        reward: "3天达标→积分奖励"
    """

    @property
    def agent_type(self) -> ExpertAgentType:
        return ExpertAgentType.METABOLIC_EXPERT

    # ---------------------------------------------------------------
    # 领域专业包装 (冰山模型)
    # ---------------------------------------------------------------

    def apply_domain(
        self,
        rx: RxPrescriptionDTO,
        context: RxContext,
        user_input: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], str]:
        """
        代谢领域包装 — 血糖/营养/运动的专业语言

        行为处方完全隐藏: 用户只看到代谢管理建议
        """
        stage = context.ttm_stage
        domain_data = context.domain_data
        glucose_data = domain_data.get("glucose", {})
        weight_data = domain_data.get("weight", {})

        domain_content = {
            "domain": "metabolic",
            "stage": f"S{stage}",
            "rx_strategy_hidden": rx.strategy_type.value,
        }

        # ---- 低阶段 (S0-S2): 认知为主, 数据辅助 ----
        if stage <= 2:
            content, message = self._low_stage_metabolic(
                rx, context, glucose_data, weight_data
            )
        # ---- 行动阶段 (S3): 具体饮食/运动行为 ----
        elif stage == 3:
            content, message = self._action_stage_metabolic(
                rx, context, glucose_data, weight_data
            )
        # ---- 维持阶段 (S4+): 习惯巩固 + 数据自主 ----
        else:
            content, message = self._maintenance_stage_metabolic(
                rx, context, glucose_data, weight_data
            )

        domain_content.update(content)

        user_message = self.adapt_message_style(message, rx.communication_style)
        return domain_content, user_message

    def _low_stage_metabolic(
        self, rx, context, glucose_data, weight_data
    ) -> Tuple[Dict, str]:
        """S0-S2: 代谢认知教育"""
        fasting = glucose_data.get("fasting_avg", 0)
        hba1c = glucose_data.get("hba1c", 0)

        content = {
            "focus": "metabolic_awareness",
            "data_presentation": {
                "fasting_glucose": fasting,
                "hba1c": hba1c,
                "interpretation": self._interpret_glucose(fasting, hba1c),
            },
            "educational_content": [
                "血糖数值的含义和目标范围",
                "饮食-血糖的基本关系",
                "日常活动对血糖的影响",
            ],
        }

        if context.ttm_stage == 0:
            message = (
                "让我带你了解一下你的血糖数据意味着什么。"
                f"你最近的空腹血糖平均值是{fasting}mmol/L。"
                "了解这些数字背后的意义,是管理健康的基础。"
            )
        elif context.ttm_stage == 1:
            message = (
                f"你的空腹血糖{fasting}mmol/L,"
                f"{'偏高' if fasting > 6.1 else '在正常范围'}。"
                "你知道吗,饮食和运动习惯的小调整,往往能带来明显的血糖改善。"
                "很多人在了解这一点后,都选择了尝试改变。"
                "你觉得你现在处于什么状态?"
            )
        else:
            message = (
                "你已经了解了血糖管理的重要性,现在是制定具体计划的好时机。"
                "我们可以从一个小目标开始——"
                "你觉得饮食和运动,哪个方面你更愿意先尝试?"
            )

        return content, message

    def _action_stage_metabolic(
        self, rx, context, glucose_data, weight_data
    ) -> Tuple[Dict, str]:
        """S3: 具体代谢行为执行"""
        fasting = glucose_data.get("fasting_avg", 0)
        postprandial = glucose_data.get("postprandial_avg", 0)

        # 行为处方 → 具体营养/运动建议 (隐藏行为策略)
        micro_actions_visible = []
        for ma in rx.micro_actions:
            micro_actions_visible.append({
                "suggestion": ma.action,
                "when": ma.trigger,
                "difficulty_label": (
                    "简单" if ma.difficulty < 0.3
                    else "中等" if ma.difficulty < 0.6
                    else "有挑战"
                ),
                "duration": f"{ma.duration_min}分钟",
            })

        content = {
            "focus": "metabolic_action",
            "glucose_status": {
                "fasting": fasting,
                "postprandial": postprandial,
                "trend": glucose_data.get("trend", "stable"),
            },
            "actionable_suggestions": micro_actions_visible,
            "monitoring_plan": {
                "frequency": "每日",
                "key_metrics": ["空腹血糖", "餐后2h血糖"],
            },
        }

        suggestions = [ma["suggestion"] for ma in micro_actions_visible[:2]]
        message = (
            f"根据你的血糖趋势,我有几个具体建议:\n\n"
            + "\n".join(f"• {s}" for s in suggestions)
            + "\n\n这些建议都是根据你的情况量身定制的,从最容易的开始做就好。"
        )

        return content, message

    def _maintenance_stage_metabolic(
        self, rx, context, glucose_data, weight_data
    ) -> Tuple[Dict, str]:
        """S4+: 代谢习惯维持"""
        content = {
            "focus": "metabolic_maintenance",
            "habit_status": "consolidating",
            "long_term_metrics": {
                "hba1c_target": "< 7.0%",
                "weight_trend": weight_data.get("trend", "stable"),
            },
            "relapse_prevention": {
                "high_risk_scenarios": ["节假日", "压力大时", "旅行"],
                "coping_plan": "已建立",
            },
        }

        message = (
            "你的代谢管理习惯已经开始稳定了!继续保持。"
            "记住,偶尔的波动是正常的,重要的是整体趋势。"
            "有没有最近遇到什么特别的挑战?"
        )

        return content, message

    def _interpret_glucose(self, fasting: float, hba1c: float) -> str:
        if fasting <= 6.1 and hba1c <= 6.5:
            return "血糖控制良好"
        elif fasting <= 7.0 and hba1c <= 7.0:
            return "血糖轻度偏高,有改善空间"
        elif fasting <= 10.0:
            return "血糖偏高,建议关注饮食和运动"
        else:
            return "血糖明显偏高,建议咨询医生"

    # ---------------------------------------------------------------
    # 专家规则集 (~20 条)
    # ---------------------------------------------------------------

    def _get_expert_rules(self) -> List[ExpertRule]:
        return [
            ExpertRule(
                rule_id="ME-001", name="空腹高血糖干预",
                condition="fasting_glucose > 7.0",
                action="focus_fasting_intervention",
                priority=8, bind_dimension="glucose",
            ),
            ExpertRule(
                rule_id="ME-002", name="餐后高峰追踪",
                condition="postprandial_glucose > 10.0",
                action="focus_postprandial_tracking",
                priority=8, bind_dimension="glucose",
            ),
            ExpertRule(
                rule_id="ME-003", name="低阶段认知拦截",
                condition="stage <= 1 and readiness < 0.4",
                action="force_strategy:consciousness_raising",
                priority=9, bind_dimension="stage",
            ),
            ExpertRule(
                rule_id="ME-004", name="高尽责性数据模式",
                condition="conscientiousness > 65",
                action="enhance_data_mode",
                priority=5, bind_dimension="personality",
            ),
            ExpertRule(
                rule_id="ME-005", name="体重平台期策略切换",
                condition="weight_plateau_days > 14",
                action="switch_weight_strategy",
                priority=7, bind_dimension="weight",
            ),
            ExpertRule(
                rule_id="ME-006", name="低血糖安全",
                condition="glucose_min < 3.9",
                action="hypoglycemia_safety_alert",
                priority=10, bind_dimension="glucose",
            ),
            ExpertRule(
                rule_id="ME-007", name="代谢综合征多维合并",
                condition="metabolic_syndrome_components >= 3",
                action="metabolic_syndrome_coordination",
                priority=8, bind_dimension="metabolic",
            ),
            ExpertRule(
                rule_id="ME-008", name="饮食依从低",
                condition="diet_adherence < 0.4",
                action="force_strategy:stimulus_control",
                priority=7, bind_dimension="nutrition",
            ),
            ExpertRule(
                rule_id="ME-009", name="运动量不足",
                condition="weekly_exercise_min < 90",
                action="enhance_exercise_behavior",
                priority=6, bind_dimension="exercise",
            ),
            ExpertRule(
                rule_id="ME-010", name="药物依从性问题",
                condition="medication_adherence < 0.7",
                action="trigger_adherence_handoff",
                priority=8, bind_dimension="adherence",
            ),
            ExpertRule(
                rule_id="ME-011", name="HbA1c改善正反馈",
                condition="hba1c_delta < -0.3",
                action="positive_reinforcement",
                priority=6, bind_dimension="glucose",
            ),
            ExpertRule(
                rule_id="ME-012", name="HbA1c恶化预警",
                condition="hba1c_delta > 0.5",
                action="escalate_intervention",
                priority=8, bind_dimension="glucose",
            ),
            ExpertRule(
                rule_id="ME-013", name="高神经质饮食焦虑",
                condition="neuroticism > 70 and 'diet_anxiety' in barriers",
                action="force_strategy:cognitive_restructuring",
                priority=7, bind_dimension="personality/nutrition",
            ),
            ExpertRule(
                rule_id="ME-014", name="BMI高危",
                condition="bmi > 30",
                action="weight_management_priority",
                priority=7, bind_dimension="weight",
            ),
            ExpertRule(
                rule_id="ME-015", name="血压协同",
                condition="systolic_bp > 140 or diastolic_bp > 90",
                action="bp_coordination",
                priority=7, bind_dimension="bp",
            ),
            ExpertRule(
                rule_id="ME-016", name="行动期习惯叠加",
                condition="stage == 3 and capacity > 0.5",
                action="force_strategy:habit_stacking",
                priority=6, bind_dimension="stage",
            ),
            ExpertRule(
                rule_id="ME-017", name="维持期复发预防",
                condition="stage >= 4 and stage_stability < 0.5",
                action="force_strategy:relapse_prevention",
                priority=7, bind_dimension="stage",
            ),
            ExpertRule(
                rule_id="ME-018", name="监测数据缺失",
                condition="monitoring_days_missing > 3",
                action="encourage_self_monitoring",
                priority=6, bind_dimension="monitoring",
            ),
            ExpertRule(
                rule_id="ME-019", name="遗忘障碍→习惯叠加",
                condition="'forgetfulness' in barriers",
                action="force_strategy:habit_stacking",
                priority=7, bind_dimension="barriers",
            ),
            ExpertRule(
                rule_id="ME-020", name="经济障碍响应",
                condition="'economic' in barriers",
                action="economic_barrier_response",
                priority=6, bind_dimension="barriers",
            ),
        ]

    # ---------------------------------------------------------------
    # 领域事实构建
    # ---------------------------------------------------------------

    def _build_domain_facts(
        self, context: RxContext, user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        domain = context.domain_data
        glucose = domain.get("glucose", {})
        weight = domain.get("weight", {})

        return {
            "stage": context.ttm_stage,
            "readiness": context.stage_readiness,
            "stage_stability": context.stage_stability,
            "self_efficacy": context.self_efficacy,
            "capacity": context.capacity_score,
            "neuroticism": context.personality.N,
            "conscientiousness": context.personality.C,
            "barriers": context.active_barriers,
            # 代谢指标
            "fasting_glucose": glucose.get("fasting_avg", 5.5),
            "postprandial_glucose": glucose.get("postprandial_avg", 7.0),
            "glucose_min": glucose.get("min", 4.0),
            "hba1c": glucose.get("hba1c", 6.5),
            "hba1c_delta": glucose.get("hba1c_delta", 0),
            # 体重
            "bmi": weight.get("bmi", 24),
            "weight_plateau_days": weight.get("plateau_days", 0),
            # 血压
            "systolic_bp": domain.get("bp", {}).get("systolic", 120),
            "diastolic_bp": domain.get("bp", {}).get("diastolic", 80),
            # 行为
            "diet_adherence": domain.get("diet_adherence", 0.5),
            "medication_adherence": domain.get("medication_adherence", 0.8),
            "weekly_exercise_min": domain.get("weekly_exercise_min", 150),
            "monitoring_days_missing": domain.get("monitoring_days_missing", 0),
            "metabolic_syndrome_components": domain.get("met_syndrome_count", 0),
        }
