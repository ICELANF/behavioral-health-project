"""
BehaviorOS — BehaviorCoachAgent 行为阶段教练
=============================================
定位: 上游前置Agent — 负责 S0-S2 认知准备
特色: 唯一一款行为处方「半透明」的Agent

核心职责:
  - 阶段评估 & 认知激活 (S0)
  - 决策平衡 & 动机强化 (S1)
  - 自我效能建设 & 行动承诺 (S2)
  - 阶段就绪后交接给领域 Agent (S3+)

专家规则: ~15 条
绑定维度: stage / personality / readiness / efficacy / resistance
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from .base_expert_agent import BaseExpertAgent, ExpertRule, AgentResponse
from ..core.rx_schemas import (
    ExpertAgentType,
    RxContext,
    RxPrescriptionDTO,
    RxStrategyType,
    CommunicationStyle,
)

logger = logging.getLogger(__name__)


class BehaviorCoachAgent(BaseExpertAgent):
    """
    行为阶段教练 — 行为处方「半透明」Agent

    冰山模型差异:
      - 其他3款Agent: 行为处方完全隐藏在专业内容之下
      - 本Agent: 行为处方半透明 — 用户能感知到行为科学方法论

    处理流程:
      S0(前意识) → 意识提升/情绪唤醒
      S1(意识)   → 决策平衡/自我再评价
      S2(准备)   → 自我解放/认知重构/行动计划
      S3+(就绪)  → 交接给领域Agent
    """

    @property
    def agent_type(self) -> ExpertAgentType:
        return ExpertAgentType.BEHAVIOR_COACH

    # ---------------------------------------------------------------
    # 领域专业包装 (半透明模式)
    # ---------------------------------------------------------------

    def apply_domain(
        self,
        rx: RxPrescriptionDTO,
        context: RxContext,
        user_input: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], str]:
        """
        行为教练的领域包装 — 半透明模式

        用户看到的内容中会包含行为科学术语,
        但以教练对话方式呈现, 不是学术讲座。
        """
        stage = context.ttm_stage
        message_parts = []

        # ---- S0: 前意识 — 温和唤醒 ----
        if stage == 0:
            domain_content = self._stage_s0_content(rx, context, user_input)
            message_parts.append(
                self._format_s0_message(rx, context, user_input)
            )

        # ---- S1: 意识 — 深化认知 + 决策引导 ----
        elif stage == 1:
            domain_content = self._stage_s1_content(rx, context, user_input)
            message_parts.append(
                self._format_s1_message(rx, context, user_input)
            )

        # ---- S2: 准备 — 承诺 + 计划 ----
        elif stage == 2:
            domain_content = self._stage_s2_content(rx, context, user_input)
            message_parts.append(
                self._format_s2_message(rx, context, user_input)
            )

        # ---- S3+: 已就绪 — 准备交接 ----
        else:
            domain_content = self._stage_ready_content(rx, context)
            message_parts.append(
                "你已经做好了行动的准备!接下来我会把你交给专业领域的教练,"
                "他/她会为你制定具体的执行方案。"
            )

        user_message = self.adapt_message_style(
            "\n\n".join(message_parts),
            rx.communication_style,
        )

        return domain_content, user_message

    # ---------------------------------------------------------------
    # S0 前意识期内容
    # ---------------------------------------------------------------

    def _stage_s0_content(
        self, rx: RxPrescriptionDTO, context: RxContext, user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "stage": "S0_precontemplation",
            "approach": "awareness_activation",
            "strategy_visible": rx.strategy_type.value,
            "key_message": "了解现状是改变的第一步",
            "cognitive_tasks": [
                {
                    "task": "健康风险认知",
                    "description": "通过简短信息了解当前健康状况的含义",
                    "micro_actions": [ma.model_dump() for ma in rx.micro_actions[:2]],
                }
            ],
            "avoid": [
                "不要催促行动",
                "不要使用恐吓语言",
                "不要给出具体行为指令",
            ],
            "next_milestone": "从'不知道'到'知道'",
        }

    def _format_s0_message(
        self, rx: RxPrescriptionDTO, context: RxContext, user_input: Dict[str, Any]
    ) -> str:
        if rx.communication_style == CommunicationStyle.EMPATHETIC:
            return (
                "我理解健康管理这件事可能让你感觉还比较遥远。"
                "没关系,我们不需要马上做什么改变。"
                "现在最重要的是,让你了解一些关于自己健康的信息。"
                "你知道吗,很多和你情况类似的人,在了解了这些信息之后,"
                "都发现其实改变并没有想象中那么难。"
            )
        elif rx.communication_style == CommunicationStyle.DATA_DRIVEN:
            return (
                "让我们先看看你的健康数据。"
                "了解数据背后的含义,是做出任何决定的前提。"
                "今天我们不谈改变,只谈事实。"
            )
        else:
            return (
                "欢迎你来到这里。"
                "今天我们不需要做任何决定,只是聊聊天,了解一些信息。"
                "准备好了吗?"
            )

    # ---------------------------------------------------------------
    # S1 意识期内容
    # ---------------------------------------------------------------

    def _stage_s1_content(
        self, rx: RxPrescriptionDTO, context: RxContext, user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "stage": "S1_contemplation",
            "approach": "cognitive_deepening",
            "strategy_visible": rx.strategy_type.value,
            "key_message": "改变的好处和困难都值得认真思考",
            "cognitive_tasks": [
                {
                    "task": "决策分析",
                    "description": "权衡改变的利弊",
                    "micro_actions": [ma.model_dump() for ma in rx.micro_actions],
                },
                {
                    "task": "自我反思",
                    "description": "思考理想的未来自己",
                },
            ],
            "ambivalence_normal": True,
            "next_milestone": "从'矛盾'到'倾向改变'",
        }

    def _format_s1_message(
        self, rx: RxPrescriptionDTO, context: RxContext, user_input: Dict[str, Any]
    ) -> str:
        return (
            "我看到你已经在思考改变这件事了,这本身就很了不起。"
            "很多人在这个阶段会感到矛盾——觉得改变有好处,但也有顾虑。"
            "这种感觉完全正常。\n\n"
            "让我们试试一个方法:把改变的好处和困难都列出来,"
            "然后给每一项打个重要性分数。"
            "这样我们就能更清楚地看到,对你来说最重要的是什么。"
        )

    # ---------------------------------------------------------------
    # S2 准备期内容
    # ---------------------------------------------------------------

    def _stage_s2_content(
        self, rx: RxPrescriptionDTO, context: RxContext, user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "stage": "S2_preparation",
            "approach": "commitment_building",
            "strategy_visible": rx.strategy_type.value,
            "key_message": "做出你的第一个具体承诺",
            "action_planning": {
                "first_step": rx.micro_actions[0].model_dump() if rx.micro_actions else {},
                "commitment_type": "private" if context.personality.is_low("E") else "public",
                "timeline": "本周内开始",
            },
            "self_efficacy_builders": [
                "回顾过去成功的改变经历",
                "从最小的行动开始",
                "寻找支持者",
            ],
            "next_milestone": "从'打算做'到'开始做'",
        }

    def _format_s2_message(
        self, rx: RxPrescriptionDTO, context: RxContext, user_input: Dict[str, Any]
    ) -> str:
        first_action = rx.micro_actions[0].action if rx.micro_actions else "一个小小的健康行为"
        return (
            f"你已经准备好迈出第一步了!这个阶段最重要的事情就是:"
            f"做出一个具体的、可执行的承诺。\n\n"
            f"我建议你从这个开始: {first_action}\n\n"
            f"这个任务被设计得很简单,因为最重要的不是做多少,"
            f"而是「开始做」这件事本身。"
            f"一旦你迈出第一步,后面的路会比你想象的更顺畅。"
        )

    # ---------------------------------------------------------------
    # S3+ 就绪内容 (准备交接)
    # ---------------------------------------------------------------

    def _stage_ready_content(
        self, rx: RxPrescriptionDTO, context: RxContext
    ) -> Dict[str, Any]:
        return {
            "stage": "S3_plus_ready",
            "approach": "handoff_preparation",
            "readiness_confirmed": True,
            "handoff_target": self._determine_handoff_domain(context),
            "rx_context_for_handoff": {
                "stage": context.ttm_stage,
                "readiness": context.stage_readiness,
                "personality_dominant": context.personality.dominant_trait(),
                "capacity": context.capacity_score,
                "self_efficacy": context.self_efficacy,
            },
        }

    def _determine_handoff_domain(self, context: RxContext) -> str:
        primary = context.domain_data.get("primary_domain", "metabolic")
        return primary

    # ---------------------------------------------------------------
    # 专家规则集 (~15 条)
    # ---------------------------------------------------------------

    def _get_expert_rules(self) -> List[ExpertRule]:
        return [
            # ---- 低阶段认知优先 ----
            ExpertRule(
                rule_id="BC-001",
                name="低阶段认知优先",
                condition="stage <= 1 and readiness < 0.4",
                action="force_strategy:consciousness_raising",
                priority=9,
                bind_dimension="stage/readiness",
                description="S0-S1且就绪度低→强制意识提升策略",
            ),
            ExpertRule(
                rule_id="BC-002",
                name="高神经质情绪支持",
                condition="stage <= 2 and neuroticism > 65",
                action="force_intensity:low",
                priority=8,
                bind_dimension="personality",
                description="高N低阶段→降低强度,共情优先",
            ),
            ExpertRule(
                rule_id="BC-003",
                name="决策矛盾检测",
                condition="stage == 1 and readiness > 0.3 and readiness < 0.6",
                action="force_strategy:decisional_balance",
                priority=7,
                bind_dimension="stage/readiness",
                description="S1矛盾期→决策平衡策略",
            ),
            ExpertRule(
                rule_id="BC-004",
                name="自我效能建设",
                condition="stage == 2 and self_efficacy < 0.4",
                action="enhance_self_efficacy",
                priority=8,
                bind_dimension="efficacy",
                description="S2准备期但效能低→增强自我效能",
            ),
            ExpertRule(
                rule_id="BC-005",
                name="阶段提升催化",
                condition="stage == 2 and readiness > 0.7 and self_efficacy > 0.5",
                action="catalyze_stage_transition",
                priority=7,
                bind_dimension="stage/readiness/efficacy",
                description="S2就绪度高→催化向S3过渡",
            ),
            ExpertRule(
                rule_id="BC-006",
                name="交接就绪判定",
                condition="stage >= 3 and readiness > 0.6",
                action="prepare_handoff",
                priority=9,
                bind_dimension="stage/readiness",
                description="S3+且就绪→准备交接领域Agent",
            ),
            ExpertRule(
                rule_id="BC-007",
                name="阻力超标策略切换",
                condition="resistance > resistance_threshold",
                action="switch_strategy",
                priority=8,
                bind_dimension="resistance",
                description="阻力超标→切换策略",
            ),
            ExpertRule(
                rule_id="BC-008",
                name="高开放性探索模式",
                condition="openness > 70 and stage <= 2",
                action="enhance_exploration",
                priority=5,
                bind_dimension="personality",
                description="高O低阶段→增加探索性内容",
            ),
            ExpertRule(
                rule_id="BC-009",
                name="高尽责性数据模式",
                condition="conscientiousness > 70",
                action="enhance_data_presentation",
                priority=5,
                bind_dimension="personality",
                description="高C→增加数据和证据呈现",
            ),
            ExpertRule(
                rule_id="BC-010",
                name="复发检测回拉",
                condition="stage >= 3 and stage_stability < 0.3",
                action="relapse_intervention",
                priority=9,
                bind_dimension="stage/stability",
                description="S3+但稳定性差→复发预防干预",
            ),
            ExpertRule(
                rule_id="BC-011",
                name="自我效能崩塌紧急响应",
                condition="self_efficacy < 0.15",
                action="emergency_efficacy_support",
                priority=10,
                bind_dimension="efficacy",
                description="效能极低→紧急效能支持",
            ),
            ExpertRule(
                rule_id="BC-012",
                name="恐惧障碍检测",
                condition="'fear' in barriers",
                action="force_strategy:cognitive_restructuring",
                priority=7,
                bind_dimension="barriers",
                description="恐惧障碍→认知重构",
            ),
            ExpertRule(
                rule_id="BC-013",
                name="认知障碍检测",
                condition="'cognitive' in barriers",
                action="force_strategy:consciousness_raising",
                priority=7,
                bind_dimension="barriers",
                description="认知障碍→意识提升",
            ),
            ExpertRule(
                rule_id="BC-014",
                name="低动机检测",
                condition="'low_motivation' in barriers and stage <= 1",
                action="force_strategy:dramatic_relief",
                priority=6,
                bind_dimension="barriers",
                description="低动机S0-S1→情绪唤醒",
            ),
            ExpertRule(
                rule_id="BC-015",
                name="长期停滞检测",
                condition="stage == 1 and stage_stability > 0.8",
                action="break_stagnation",
                priority=6,
                bind_dimension="stage/stability",
                description="S1长期停滞→打破停滞",
            ),
        ]

    # ---------------------------------------------------------------
    # 领域事实构建
    # ---------------------------------------------------------------

    def _build_domain_facts(
        self, context: RxContext, user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "stage": context.ttm_stage,
            "readiness": context.stage_readiness,
            "stage_stability": context.stage_stability,
            "self_efficacy": context.self_efficacy,
            "neuroticism": context.personality.N,
            "openness": context.personality.O,
            "conscientiousness": context.personality.C,
            "extraversion": context.personality.E,
            "agreeableness": context.personality.A,
            "capacity": context.capacity_score,
            "barriers": context.active_barriers,
            "resistance": user_input.get("domain_data", {}).get("resistance_score", 0),
            "resistance_threshold": 0.3,
        }
