"""
BehaviorOS — AdherenceExpertAgent 就医依从性专家
=================================================
定位: 横切面Agent — 跨越所有领域和阶段, 确保医嘱行为链连续性
核心洞察: "不依从 = 行为链设计不当" 而非 "患者不配合"

核心职责:
  - 服药行为链 (habit_stacking + stimulus_control)
  - 就诊行为规划 (decisional_balance + self_liberation)
  - 检查恐惧脱敏 (cognitive_restructuring + systematic_desensitization)
  - 医嘱翻译为行为 (consciousness_raising)
  - 依从障碍诊断 (5类障碍 × 策略映射)
  - 多药管理
  - 经济障碍应对

五类依从行为:
  1. 服药 (Medication) — 最高频
  2. 就诊 (Clinic visits) — 定期复查
  3. 检查 (Tests/Labs) — 恐惧脱敏
  4. 饮食医嘱 (Dietary orders) — 行为翻译
  5. 运动医嘱 (Exercise orders) — 行为翻译

五类依从障碍 × 策略映射:
  遗忘 → habit_stacking + stimulus_control
  恐惧 → cognitive_restructuring + systematic_desensitization
  认知 → consciousness_raising + decisional_balance
  经济 → problem_solving + resource_linking
  关系 → assertiveness_training + social_support

专家规则: ~22 条
绑定维度: medication / visit / check / diet_order / exercise_order / barrier
"""

from __future__ import annotations

import logging
from datetime import datetime
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
# 依从性领域常量
# =====================================================================

# 依从评估量表阈值 (MMAS-8 Morisky 量表)
MMAS_HIGH_ADHERENCE = 8.0     # 满分
MMAS_MEDIUM = 6.0             # 中等
MMAS_LOW = 4.0                # 低依从

# 就诊逾期阈值 (天)
VISIT_OVERDUE_WARNING = 7     # 逾期提醒
VISIT_OVERDUE_ALERT = 14      # 逾期警告
VISIT_OVERDUE_CRITICAL = 30   # 严重逾期

# 服药漏服阈值
MISSED_DOSE_WARNING = 2       # 7天内漏服2次以上
MISSED_DOSE_ALERT = 4         # 7天内漏服4次以上

# 障碍类型枚举
BARRIER_TYPES = [
    "forgetfulness",  # 遗忘型
    "fear",           # 恐惧型
    "cognitive",      # 认知型 (不理解为什么要服药/检查)
    "economic",       # 经济型 (费用障碍)
    "relational",     # 关系型 (与医生关系不良)
]

# 障碍 → 策略映射
BARRIER_STRATEGY_MAP = {
    "forgetfulness": [RxStrategyType.HABIT_STACKING, RxStrategyType.STIMULUS_CONTROL],
    "fear": [RxStrategyType.COGNITIVE_RESTRUCTURING,
             RxStrategyType.SYSTEMATIC_DESENSITIZATION],
    "cognitive": [RxStrategyType.CONSCIOUSNESS_RAISING,
                  RxStrategyType.DECISIONAL_BALANCE],
    "economic": [RxStrategyType.SELF_MONITORING],  # + problem_solving (非标准12策略)
    "relational": [RxStrategyType.SELF_LIBERATION],  # + assertiveness_training
}


class AdherenceExpertAgent(BaseExpertAgent):
    """
    就医依从性专家Agent — 横切面Agent

    与其他3款Agent的关系:
      - 行为教练: 负责认知准备 → 依从Agent确保行为链落地
      - 代谢专家: 制定饮食运动方案 → 依从Agent确保方案执行
      - 心血管专家: 制定运动处方 → 依从Agent确保用药+复查链

    触发机制:
      - 不单独作为入口Agent使用
      - 被其他Agent在检测到依从问题时「横切」触发
      - 也可由系统检测到依从异常时主动触发

    核心重定义:
      传统视角: "患者不依从" — 归因于患者态度/意愿
      BehaviorOS视角: "行为链断裂" — 归因于行为设计, 寻找断点并修复
    """

    @property
    def agent_type(self) -> ExpertAgentType:
        return ExpertAgentType.ADHERENCE_EXPERT

    # ---------------------------------------------------------------
    # 领域专业包装 (依从行为链设计)
    # ---------------------------------------------------------------

    def apply_domain(
        self,
        rx: RxPrescriptionDTO,
        context: RxContext,
        user_input: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], str]:
        """
        将行为处方包装为依从性管理专业内容

        核心转换:
          habit_stacking → 服药+现有习惯绑定 ("饭后刷牙时服药")
          stimulus_control → 药盒位置优化, 视觉提醒设置
          cognitive_restructuring → "这药是毒药"认知矫正
          systematic_desensitization → 抽血/检查恐惧脱敏
          decisional_balance → 服药利弊权衡表
          consciousness_raising → 用白话解释医嘱含义
          self_monitoring → 服药日志, 漏服原因追踪
        """
        stage = context.ttm_stage
        domain = context.domain_data
        barriers = context.active_barriers

        # 依从数据提取
        med_missed_7d = domain.get("medication_missed_7d", 0)
        mmas_score = domain.get("mmas_score", 6.0)
        visit_overdue = domain.get("visit_overdue_days", 0)
        next_visit_date = domain.get("next_visit_date", "")
        medications = domain.get("medications", [])
        pending_tests = domain.get("pending_tests", [])
        diet_orders = domain.get("diet_orders", [])
        exercise_orders = domain.get("exercise_orders", [])

        # 障碍诊断
        diagnosed_barriers = self._diagnose_barriers(
            barriers, med_missed_7d, mmas_score, visit_overdue, domain
        )

        # 行为链设计
        medication_chain = self._design_medication_chain(
            medications, diagnosed_barriers, stage, rx
        )
        visit_plan = self._design_visit_plan(
            visit_overdue, next_visit_date, diagnosed_barriers, stage
        )
        test_plan = self._design_test_plan(
            pending_tests, diagnosed_barriers, stage
        )
        order_translations = self._translate_medical_orders(
            diet_orders, exercise_orders, stage
        )

        domain_content = {
            "adherence_overview": {
                "mmas_score": mmas_score,
                "mmas_level": (
                    "high" if mmas_score >= MMAS_HIGH_ADHERENCE
                    else "medium" if mmas_score >= MMAS_MEDIUM
                    else "low"
                ),
                "med_missed_7d": med_missed_7d,
                "visit_overdue_days": visit_overdue,
                "total_medications": len(medications),
                "pending_tests": len(pending_tests),
            },
            "diagnosed_barriers": diagnosed_barriers,
            "barrier_strategies": {
                b["type"]: [s.value for s in BARRIER_STRATEGY_MAP.get(b["type"], [])]
                for b in diagnosed_barriers
            },
            "medication_chain": medication_chain,
            "visit_plan": visit_plan,
            "test_plan": test_plan,
            "order_translations": order_translations,
            "applied_strategy": rx.strategy_type.value,
        }

        user_message = self._build_user_message(
            rx, stage, diagnosed_barriers, medication_chain,
            visit_plan, med_missed_7d, mmas_score, visit_overdue, context
        )

        return domain_content, user_message

    # ---------------------------------------------------------------
    # 障碍诊断引擎
    # ---------------------------------------------------------------

    def _diagnose_barriers(
        self,
        active_barriers: List[str],
        med_missed_7d: int,
        mmas_score: float,
        visit_overdue: int,
        domain: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """诊断依从障碍类型及严重度"""
        diagnosed = []

        # 遗忘型: 漏服多 + MMAS低 + 无其他明显障碍
        if med_missed_7d >= MISSED_DOSE_WARNING and "forgetfulness" in active_barriers:
            diagnosed.append({
                "type": "forgetfulness",
                "severity": "high" if med_missed_7d >= MISSED_DOSE_ALERT else "moderate",
                "evidence": f"7天漏服{med_missed_7d}次",
                "recommended_strategies": ["habit_stacking", "stimulus_control"],
            })

        # 恐惧型: 检查拖延 + 恐惧关键词
        if "fear" in active_barriers:
            diagnosed.append({
                "type": "fear",
                "severity": "high" if visit_overdue >= VISIT_OVERDUE_ALERT else "moderate",
                "evidence": "检测到就医/检查恐惧信号",
                "recommended_strategies": ["cognitive_restructuring",
                                           "systematic_desensitization"],
            })

        # 认知型: 不理解医嘱
        if "cognitive" in active_barriers:
            diagnosed.append({
                "type": "cognitive",
                "severity": "moderate",
                "evidence": "用户表达对医嘱的困惑或不理解",
                "recommended_strategies": ["consciousness_raising",
                                           "decisional_balance"],
            })

        # 经济型
        if "economic" in active_barriers:
            diagnosed.append({
                "type": "economic",
                "severity": "high",
                "evidence": "用户提及费用困难",
                "recommended_strategies": ["self_monitoring"],  # + resource_linking
            })

        # 通用: 如果没有检测到特定障碍但依从率低
        if not diagnosed and mmas_score < MMAS_MEDIUM:
            diagnosed.append({
                "type": "forgetfulness",  # 默认归因遗忘
                "severity": "moderate",
                "evidence": f"MMAS评分{mmas_score}/8, 未检测到特定障碍",
                "recommended_strategies": ["habit_stacking", "self_monitoring"],
            })

        return diagnosed

    # ---------------------------------------------------------------
    # 服药行为链设计
    # ---------------------------------------------------------------

    def _design_medication_chain(
        self,
        medications: List[Dict[str, Any]],
        barriers: List[Dict[str, Any]],
        stage: int,
        rx: RxPrescriptionDTO,
    ) -> Dict[str, Any]:
        """设计服药行为链"""
        if not medications:
            return {"status": "no_medications", "chain": []}

        # 根据障碍类型选择核心策略
        barrier_types = {b["type"] for b in barriers}

        chain = {
            "status": "active",
            "total_medications": len(medications),
            "chain": [],
        }

        for med in medications:
            med_name = med.get("name", "药物")
            med_time = med.get("time", "morning")
            med_dose = med.get("dose", "按医嘱")

            step = {
                "medication": med_name,
                "dose": med_dose,
                "time": med_time,
            }

            if "forgetfulness" in barrier_types:
                # 习惯叠加策略
                anchor_habits = {
                    "morning": "刷牙后",
                    "noon": "午饭第一口前",
                    "evening": "洗脸后",
                    "bedtime": "放好枕头后",
                }
                anchor = anchor_habits.get(med_time, "固定时间")
                step["habit_stack"] = f"{anchor}→拿药→服药→打勾"
                step["stimulus"] = f"药盒放在{anchor.replace('后', '')}的位置旁边"
                step["cue_type"] = "visual_and_habit"

            elif "fear" in barrier_types:
                # 认知重构
                step["cognitive_reframe"] = (
                    f"{med_name}是保护您健康的工具, "
                    f"像安全带保护驾驶员一样"
                )
                step["gradual_approach"] = (
                    "如果对药物有顾虑, 可以先了解药物作用原理"
                )

            elif "cognitive" in barrier_types:
                step["plain_language"] = (
                    f"{med_name}: {med.get('purpose', '帮助您管理健康状况')}"
                )
                step["why_important"] = med.get("benefit", "降低健康风险")

            chain["chain"].append(step)

        return chain

    # ---------------------------------------------------------------
    # 就诊行为规划
    # ---------------------------------------------------------------

    def _design_visit_plan(
        self,
        visit_overdue: int,
        next_visit_date: str,
        barriers: List[Dict[str, Any]],
        stage: int,
    ) -> Dict[str, Any]:
        """设计就诊行为计划"""
        barrier_types = {b["type"] for b in barriers}

        plan = {
            "visit_overdue_days": visit_overdue,
            "next_visit_date": next_visit_date,
            "urgency": (
                "critical" if visit_overdue >= VISIT_OVERDUE_CRITICAL
                else "warning" if visit_overdue >= VISIT_OVERDUE_WARNING
                else "normal"
            ),
        }

        if visit_overdue >= VISIT_OVERDUE_WARNING:
            # 设计就诊行为链
            plan["visit_chain"] = {
                "steps": [
                    "① 今天: 拨打医院预约电话 (5分钟)",
                    "② 预约后: 手机日历设置提醒 (2分钟)",
                    "③ 就诊前一天: 整理要问医生的问题清单",
                    "④ 就诊当天: 带好所有药盒 + 最近监测记录",
                ],
                "micro_action": "现在就把医院电话存到手机通讯录",
            }

            if "fear" in barrier_types:
                plan["visit_chain"]["fear_management"] = {
                    "pre_visit": "就诊前做3分钟腹式呼吸",
                    "cognitive_prep": "医生是帮助我变得更好的伙伴",
                    "companion": "建议有家人陪同, 帮助记录医嘱",
                }

        return plan

    # ---------------------------------------------------------------
    # 检查计划
    # ---------------------------------------------------------------

    def _design_test_plan(
        self,
        pending_tests: List[Dict[str, Any]],
        barriers: List[Dict[str, Any]],
        stage: int,
    ) -> Dict[str, Any]:
        """设计检查行为计划"""
        if not pending_tests:
            return {"status": "no_pending_tests"}

        barrier_types = {b["type"] for b in barriers}
        plan = {
            "status": "pending",
            "tests": [],
        }

        for test in pending_tests:
            test_info = {
                "name": test.get("name", "检查项目"),
                "due_date": test.get("due_date", "待预约"),
                "purpose": test.get("purpose", "监测健康状况"),
            }

            if "fear" in barrier_types and test.get("type") in ["blood", "invasive"]:
                test_info["desensitization"] = {
                    "step_1": "了解检查过程 (观看科普视频, 2分钟)",
                    "step_2": "想象自己完成检查的场景 (闭眼1分钟)",
                    "step_3": "预约检查 (打电话或线上预约)",
                    "coping": "检查时深呼吸, 看手机分散注意力",
                }

            plan["tests"].append(test_info)

        return plan

    # ---------------------------------------------------------------
    # 医嘱翻译
    # ---------------------------------------------------------------

    def _translate_medical_orders(
        self,
        diet_orders: List[str],
        exercise_orders: List[str],
        stage: int,
    ) -> Dict[str, Any]:
        """将医嘱翻译为具体可执行行为"""
        translations = {"diet": [], "exercise": []}

        # 饮食医嘱翻译
        diet_translation_map = {
            "低盐": "每餐用限盐勺(2g), 不额外加酱油/蚝油",
            "低脂": "肉类选鸡胸/鱼肉, 烹饪用蒸/煮代替煎/炸",
            "低糖": "主食减半, 用杂粮替代白米, 水果选苹果/柚子",
            "高纤维": "每餐加一份蔬菜(拳头大小), 选全麦面包",
            "限水": "准备固定水杯, 记录每次饮水量",
            "控制总热量": "每餐用手掌估算份量, 主食不超过一拳",
        }
        for order in diet_orders:
            for key, translation in diet_translation_map.items():
                if key in order:
                    translations["diet"].append({
                        "original": order,
                        "behavior": translation,
                        "micro_action": f"今天的一小步: {translation.split(',')[0]}",
                    })
                    break
            else:
                translations["diet"].append({
                    "original": order,
                    "behavior": f"按照医嘱执行: {order}",
                    "micro_action": f"今天先了解'{order}'的具体含义",
                })

        # 运动医嘱翻译
        for order in exercise_orders:
            translations["exercise"].append({
                "original": order,
                "behavior": f"将'{order}'分解为每天可完成的小目标",
                "micro_action": "今天先从5分钟散步开始",
            })

        return translations

    # ---------------------------------------------------------------
    # 用户消息构建
    # ---------------------------------------------------------------

    def _build_user_message(
        self,
        rx: RxPrescriptionDTO,
        stage: int,
        barriers: List[Dict[str, Any]],
        medication_chain: Dict[str, Any],
        visit_plan: Dict[str, Any],
        med_missed_7d: int,
        mmas_score: float,
        visit_overdue: int,
        context: RxContext,
    ) -> str:
        """构建用户可见消息"""
        style = rx.communication_style
        parts = []

        # 严重逾期就诊提醒 (最高优先)
        if visit_overdue >= VISIT_OVERDUE_CRITICAL:
            parts.append(
                f"⚠️ 您已经超过{visit_overdue}天没有复查了。"
                f"定期复查对于监测治疗效果非常重要。\n"
                f"建议: 今天就拨打医院电话预约最近的号源。"
            )

        # 服药提醒
        if med_missed_7d >= MISSED_DOSE_ALERT:
            parts.append(
                f"📋 这周有{med_missed_7d}次漏服药物。"
                f"我们一起想办法让服药变得更容易。"
            )

        # 根据障碍类型构建消息
        if barriers:
            primary = barriers[0]
            btype = primary["type"]

            if btype == "forgetfulness" and medication_chain.get("chain"):
                chain = medication_chain["chain"][0]
                habit_stack = chain.get("habit_stack", "")
                if habit_stack:
                    parts.append(
                        f"💡 试试这个方法: {habit_stack}\n"
                        f"把药盒放在最容易看到的位置, "
                        f"让服药变成一个自动化的动作。"
                    )

            elif btype == "fear":
                if style == CommunicationStyle.EMPATHETIC:
                    parts.append(
                        "我理解就医或检查让您感到紧张, 这种感受很正常。\n"
                        "很多人都有类似的经历, 我们可以一步一步来。"
                    )
                else:
                    parts.append(
                        "定期检查是管理健康的重要环节。"
                        "我们可以制定一个让您更舒适的就医计划。"
                    )

            elif btype == "cognitive":
                parts.append(
                    "您对治疗方案有疑问是完全合理的。\n"
                    "了解'为什么'可以帮助您更好地配合治疗。"
                    "我来用简单的话解释一下。"
                )

            elif btype == "economic":
                parts.append(
                    "我理解费用是一个实际的考虑因素。\n"
                    "我们可以和医生讨论是否有同效的平价替代方案, "
                    "或者了解医保报销政策。"
                )

        # 正面强化 (依从良好时)
        if mmas_score >= MMAS_HIGH_ADHERENCE and not barriers:
            parts.append(
                "👏 您的服药和复查做得非常好!\n"
                "这种坚持对您的健康恢复有着实实在在的帮助。"
                "继续保持!"
            )

        # 就诊计划
        if visit_plan.get("visit_chain") and visit_overdue < VISIT_OVERDUE_CRITICAL:
            parts.append(
                f"📅 距离建议复查日已过{visit_overdue}天。\n"
                "一个小建议: 现在就花5分钟预约一下, "
                "把这件事从待办清单上划掉。"
            )

        if not parts:
            parts.append(
                "您的健康管理一切顺利。如果有任何关于服药、"
                "检查或复查的问题, 随时可以问我。"
            )

        return "\n\n".join(parts)

    # ---------------------------------------------------------------
    # 领域事实构建
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
            # 依从特定
            "medication_missed_7d": domain.get("medication_missed_7d", 0),
            "mmas_score": domain.get("mmas_score", 6.0),
            "visit_overdue_days": domain.get("visit_overdue_days", 0),
            "total_medications": len(domain.get("medications", [])),
            "multi_medication": len(domain.get("medications", [])) >= 3,
            "pending_tests_count": len(domain.get("pending_tests", [])),
            "has_diet_orders": len(domain.get("diet_orders", [])) > 0,
            "has_exercise_orders": len(domain.get("exercise_orders", [])) > 0,
            # 障碍
            "has_fear_barrier": "fear" in context.active_barriers,
            "has_forget_barrier": "forgetfulness" in context.active_barriers,
            "has_cognitive_barrier": "cognitive" in context.active_barriers,
            "has_economic_barrier": "economic" in context.active_barriers,
            "barriers": context.active_barriers,
            "barrier_count": len(context.active_barriers),
            # BigFive
            "high_N": context.personality.is_high("N"),
            "low_C": context.personality.is_low("C"),
            "high_C": context.personality.is_high("C"),
            "high_A": context.personality.is_high("A"),
        }

    # ---------------------------------------------------------------
    # 专家规则集 (~22 条)
    # ---------------------------------------------------------------

    def _get_expert_rules(self) -> List[ExpertRule]:
        return [
            # ---- 服药行为 (最高优先) ----
            ExpertRule(
                rule_id="AD-001",
                name="严重漏服警报",
                condition="medication_missed_7d >= 4",
                action="force_strategy:habit_stacking",
                priority=9,
                bind_dimension="medication",
                description="7天内漏服≥4次 → 强制习惯叠加策略, 重建服药链",
            ),
            ExpertRule(
                rule_id="AD-002",
                name="轻度漏服提醒",
                condition="medication_missed_7d >= 2 and medication_missed_7d < 4",
                action="augment_strategy:stimulus_control",
                priority=7,
                bind_dimension="medication",
                description="漏服2-3次 → 增加环境提示, 药盒位置优化",
            ),
            ExpertRule(
                rule_id="AD-003",
                name="多药管理混乱",
                condition="multi_medication == True and medication_missed_7d >= 2",
                action="multi_medication_intervention",
                priority=8,
                bind_dimension="medication",
                description="≥3种药+漏服 → 专项多药管理方案(药物分格盒+时间表)",
            ),
            ExpertRule(
                rule_id="AD-004",
                name="服药零漏服正强化",
                condition="medication_missed_7d == 0 and total_medications >= 1",
                action="positive_reinforcement",
                priority=3,
                bind_dimension="medication",
                description="本周零漏服 → 正面强化, 表扬坚持",
            ),

            # ---- 就诊行为 ----
            ExpertRule(
                rule_id="AD-005",
                name="严重逾期就诊",
                condition="visit_overdue_days >= 30",
                action="urgent_visit_reminder",
                priority=9,
                bind_dimension="visit",
                description="逾期≥30天 → 紧急就诊提醒, 设计即时行动链",
            ),
            ExpertRule(
                rule_id="AD-006",
                name="中度逾期就诊",
                condition="visit_overdue_days >= 14 and visit_overdue_days < 30",
                action="visit_planning",
                priority=7,
                bind_dimension="visit",
                description="逾期14-29天 → 就诊行为规划, 降低预约阻力",
            ),
            ExpertRule(
                rule_id="AD-007",
                name="轻度逾期提醒",
                condition="visit_overdue_days >= 7 and visit_overdue_days < 14",
                action="gentle_visit_nudge",
                priority=5,
                bind_dimension="visit",
                description="逾期7-13天 → 温和提醒, 询问是否需要帮助预约",
            ),

            # ---- 检查恐惧 ----
            ExpertRule(
                rule_id="AD-008",
                name="检查恐惧脱敏",
                condition="has_fear_barrier == True and pending_tests_count > 0",
                action="force_strategy:systematic_desensitization",
                priority=7,
                bind_dimension="check",
                description="恐惧+待检查 → 渐进脱敏: 了解→想象→预约→完成",
            ),
            ExpertRule(
                rule_id="AD-009",
                name="恐惧型就医回避",
                condition="has_fear_barrier == True and visit_overdue_days >= 14",
                action="fear_based_visit_intervention",
                priority=8,
                bind_dimension="visit",
                description="恐惧+就诊逾期 → 认知重构+渐进暴露+陪同建议",
            ),

            # ---- 认知障碍 ----
            ExpertRule(
                rule_id="AD-010",
                name="医嘱理解障碍",
                condition="has_cognitive_barrier == True",
                action="force_strategy:consciousness_raising",
                priority=7,
                bind_dimension="diet_order",
                description="不理解医嘱 → 白话翻译+可视化解释",
            ),
            ExpertRule(
                rule_id="AD-011",
                name="服药必要性质疑",
                condition=(
                    "has_cognitive_barrier == True and "
                    "medication_missed_7d >= 2"
                ),
                action="force_strategy:decisional_balance",
                priority=8,
                bind_dimension="medication",
                description="质疑服药必要性+漏服 → 决策平衡表(利弊分析)",
            ),

            # ---- 经济障碍 ----
            ExpertRule(
                rule_id="AD-012",
                name="经济障碍识别",
                condition="has_economic_barrier == True",
                action="economic_support_referral",
                priority=8,
                bind_dimension="barrier",
                description="经济困难 → 提供替代方案信息, 建议与医生讨论",
            ),
            ExpertRule(
                rule_id="AD-013",
                name="经济导致停药",
                condition=(
                    "has_economic_barrier == True and "
                    "medication_missed_7d >= 4"
                ),
                action="urgent_economic_intervention",
                priority=9,
                bind_dimension="medication",
                description="经济原因停药 → 紧急干预, 建议立即联系医生调整方案",
            ),

            # ---- 人格适配 ----
            ExpertRule(
                rule_id="AD-014",
                name="低尽责性强化提醒",
                condition="low_C == True and medication_missed_7d >= 2",
                action="augment_strategy:stimulus_control",
                priority=6,
                bind_dimension="medication",
                description="低C+漏服 → 增强外部提示(闹钟+药盒+家人提醒)",
            ),
            ExpertRule(
                rule_id="AD-015",
                name="高尽责性数据追踪",
                condition="high_C == True",
                action="augment_strategy:self_monitoring",
                priority=4,
                bind_dimension="medication",
                description="高C → 提供详细依从数据和趋势图表",
            ),
            ExpertRule(
                rule_id="AD-016",
                name="高神经质情绪安抚",
                condition="high_N == True and has_fear_barrier == True",
                action="augment_style:empathetic",
                priority=6,
                bind_dimension="check",
                description="高N+恐惧 → 优先情绪安抚, 延长脱敏节奏",
            ),

            # ---- 低阶段认知拦截 ----
            ExpertRule(
                rule_id="AD-017",
                name="前意识期教育",
                condition="stage <= 1 and recent_adherence < 0.5",
                action="force_strategy:consciousness_raising",
                priority=7,
                bind_dimension="barrier",
                description="S0-S1+低依从 → 不要求行为改变, 仅提供认知教育",
            ),

            # ---- 综合依从指标 ----
            ExpertRule(
                rule_id="AD-018",
                name="整体依从率极低",
                condition="recent_adherence < 0.3",
                action="comprehensive_adherence_review",
                priority=9,
                bind_dimension="barrier",
                description="整体依从率<30% → 全面障碍评估, 可能需要多策略组合",
            ),
            ExpertRule(
                rule_id="AD-019",
                name="依从率良好稳定",
                condition="recent_adherence >= 0.8 and stability > 0.7",
                action="maintenance_mode",
                priority=3,
                bind_dimension="barrier",
                description="依从率高+稳定 → 维持模式, 减少干预频率",
            ),

            # ---- 跨域协作 ----
            ExpertRule(
                rule_id="AD-020",
                name="饮食医嘱行为翻译",
                condition="has_diet_orders == True and has_cognitive_barrier == True",
                action="translate_diet_orders",
                priority=6,
                bind_dimension="diet_order",
                description="有饮食医嘱+认知障碍 → 翻译为具体可执行行为",
            ),
            ExpertRule(
                rule_id="AD-021",
                name="运动医嘱行为翻译",
                condition="has_exercise_orders == True and has_cognitive_barrier == True",
                action="translate_exercise_orders",
                priority=6,
                bind_dimension="exercise_order",
                description="有运动医嘱+认知障碍 → 翻译为具体可执行行为",
            ),
            ExpertRule(
                rule_id="AD-022",
                name="多重障碍组合干预",
                condition="barrier_count >= 3",
                action="multi_barrier_triage",
                priority=8,
                bind_dimension="barrier",
                description="≥3种障碍 → 障碍优先级排序, 逐一突破",
            ),
        ]
