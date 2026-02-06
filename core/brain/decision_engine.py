# core/brain/decision_engine.py
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from core.brain.stage_runtime import StageRuntimeBuilder, StageInput, RuntimeState
from core.brain.policy_gate import RuntimePolicyGate, PolicyDecision, PolicyDecisionType

# SOP 6.2 公共防火墙：这些 UI 来源直接返回 SILENCE，不经过大脑判定
FIREWALL_SILENT_SOURCES = {"UI-1"}

# L6 成长之旅叙事模板 — 覆盖全部阶段跃迁
HERO_JOURNEY_TEMPLATES = {
    "S0_to_S1": (
        "一粒种子在黑暗中悄悄裂开了壳。"
        "你开始注意到一些以前忽略的信号——这就是觉醒的第一道光。"
        "不需要急于行动，先让这份觉察陪伴你。"
    ),
    "S1_to_S2": (
        "从抗拒到愿意倾听，这本身就是一次了不起的跨越。"
        "你不再紧紧关着心门，而是留了一道缝。"
        "阳光正从那道缝隙中照进来。"
    ),
    "S2_to_S3": (
        "你已经走过了准备期的考验，内心的信念之火已被点燃。"
        "现在，你正式踏上行动的旅程——这是成长之旅中最关键的一步。"
        "每一个小小的行动，都是你迈向新生活的勋章。"
    ),
    "S3_to_S4": (
        "从勉强接受到主动尝试，你跨过了最难的那道坎。"
        "你不再是被推着前行的旅人，而是自己选择了方向。"
        "这份主动，是你送给自己最好的礼物。"
    ),
    "S4_to_S5": (
        "当尝试变成了习惯，当坚持不再需要意志力——"
        "你正在经历从量变到质变的美妙蜕变。"
        "规律践行的你，已经是自己生活的主人。"
    ),
    "S5_to_S6": (
        "从刻意坚持到自然而然，你已经将健康融入了生命的节奏。"
        "这不再是一项任务，而是你本来的样子。"
        "恭喜你，完成了一段真正的内在成长之旅。"
    ),
}


class BehavioralBrain:
    def __init__(self, config: Dict[str, Any]):
        self.config = config  # 来源于 configs/spi_mapping.json
        self.stage_runtime = StageRuntimeBuilder()
        self.policy_gate = RuntimePolicyGate()

    # ------------------------------------------------------------------
    # SOP 6.2 公共防火墙
    # ------------------------------------------------------------------
    def firewall_check(self, source_ui: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        SOP 6.2: 如果请求来自公共 UI (UI-1)，直接返回 SILENCE，
        绕过大脑判定层，保护核心决策引擎不被公共流量触达。
        """
        if source_ui in FIREWALL_SILENT_SOURCES:
            return {
                "action": "SILENCE",
                "bypass_brain": True,
                "source": source_ui,
                "reason": "SOP 6.2: public UI source filtered",
            }
        return None

    # ------------------------------------------------------------------
    # 核心判定：TTM 阶段跃迁 (兼容旧接口)
    # ------------------------------------------------------------------
    def evaluate_transition(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        输入: 包含 belief, action_count_3d, current_stage 的字典
        输出: 判定后的阶段及建议动作

        兼容旧接口，内部委托给 StageRuntimeBuilder
        """
        last_stage = current_state.get("current_stage", "S0")
        belief = current_state.get("belief", 0.0)
        actions = current_state.get("action_count_3d", 0)
        capability = current_state.get("capability", 0.0)
        awareness = current_state.get("awareness", 0.0)
        streak_days = current_state.get("streak_days", 0)
        spi_score = current_state.get("spi_score", 0.0)
        interrupt_72h = current_state.get("action_interrupt_72h", False)

        # 简单启发式: 根据当前阶段推测下一阶段
        thresholds = self.config.get("thresholds", {})
        stage_order = ["S0", "S1", "S2", "S3", "S4", "S5", "S6"]
        current_idx = stage_order.index(last_stage) if last_stage in stage_order else 0
        next_stage = stage_order[min(current_idx + 1, 6)]

        # 使用 StageRuntimeBuilder
        stage_input = StageInput(
            user_id=0,  # 旧接口不传 user_id
            current_stage=last_stage,
            stage_hypothesis=next_stage,
            belief_score=belief,
            awareness_score=awareness,
            capability_score=capability,
            action_completed_7d=actions,
            action_interrupt_72h=interrupt_72h,
            streak_days=streak_days,
            spi_score=spi_score,
        )

        runtime_state, logs = self.stage_runtime.build(stage_input)

        return {
            "from_stage": runtime_state.previous_stage,
            "to_stage": runtime_state.confirmed_stage,
            "is_transition": runtime_state.is_transition,
            "stability": runtime_state.stability,
            "risk_flags": runtime_state.risk_flags,
            "decision_reason": runtime_state.decision_reason,
            "timestamp": datetime.now().isoformat(),
            "spi_summary": {"belief": belief, "actions": actions},
            "_decision_logs": logs,
        }

    # ------------------------------------------------------------------
    # 新接口: 基于行为画像的完整处理
    # ------------------------------------------------------------------
    def process_with_profile(
        self,
        source_ui: Optional[str],
        behavioral_profile: Dict[str, Any],
        behavior_facts: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        基于行为画像的完整处理流水线:

        1. SOP 6.2 防火墙检查
        2. StageRuntimeBuilder.build() — 阶段判定
        3. RuntimePolicyGate.evaluate() — 策略闸门
        4. L6 叙事化
        5. 返回: 决策结果 + 干预许可

        Args:
            source_ui: 来源 UI 标识
            behavioral_profile: 用户行为画像 (从 BehavioralProfile 获取)
            behavior_facts: 行为事实 (7天行为数、连续天数、中断等)
        """
        # Step 1: 防火墙
        firewall = self.firewall_check(source_ui)
        if firewall is not None:
            return firewall

        # Step 2: StageRuntimeBuilder
        current_stage = behavioral_profile.get("current_stage", "S0")
        stage_hypothesis = behavioral_profile.get("stage_hypothesis", current_stage)
        spi_score = behavioral_profile.get("spi_score", 0.0)
        interaction_mode = behavioral_profile.get("interaction_mode", "empathy")

        stage_input = StageInput(
            user_id=behavioral_profile.get("user_id", 0),
            current_stage=current_stage,
            stage_hypothesis=stage_hypothesis,
            belief_score=behavior_facts.get("belief_score", 0.0),
            awareness_score=behavior_facts.get("awareness_score", 0.0),
            capability_score=behavior_facts.get("capability_score", 0.0),
            action_completed_7d=behavior_facts.get("action_completed_7d", 0),
            action_interrupt_72h=behavior_facts.get("action_interrupt_72h", False),
            streak_days=behavior_facts.get("streak_days", 0),
            spi_score=spi_score,
        )

        runtime_state, decision_logs = self.stage_runtime.build(stage_input)

        # Step 3: PolicyGate
        policy_decision = self.policy_gate.evaluate(
            runtime_state=runtime_state,
            recommended_mode=interaction_mode,
            source=source_ui,
        )

        # Step 4: L6 叙事化
        narrative = None
        if runtime_state.is_transition:
            key = f"{runtime_state.previous_stage}_to_{runtime_state.confirmed_stage}"
            narrative = HERO_JOURNEY_TEMPLATES.get(
                key,
                "你正在经历一次重要的蜕变，每一步都值得被铭记。"
            )

        # Step 5: 组合返回
        return {
            "user_id": behavioral_profile.get("user_id"),
            "source_ui": source_ui,
            # 阶段判定
            "from_stage": runtime_state.previous_stage,
            "to_stage": runtime_state.confirmed_stage,
            "is_transition": runtime_state.is_transition,
            "stability": runtime_state.stability,
            "risk_flags": runtime_state.risk_flags,
            "decision_reason": runtime_state.decision_reason,
            # 策略闸门
            "policy_action": policy_decision.action.value,
            "policy_reason": policy_decision.reason,
            "intervention_allowed": policy_decision.intervention_allowed,
            "escalation_target": policy_decision.escalation_target,
            "allowed_modes": policy_decision.allowed_modes,
            # 叙事
            "narrative": narrative,
            # 时间
            "timestamp": datetime.now().isoformat(),
            # 调试
            "_decision_logs": decision_logs,
        }

    # ------------------------------------------------------------------
    # L6 热重写：成长之旅叙事化
    # ------------------------------------------------------------------
    def l6_humanize(self, transition_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        如果发生阶段跃迁，用成长之旅风格的叙事替换原始数据，
        让患者端看到的是温暖的故事而不是冰冷的 JSON 指标。
        """
        result = dict(transition_result)
        if result.get("is_transition"):
            key = f"{result['from_stage']}_to_{result['to_stage']}"
            narrative = HERO_JOURNEY_TEMPLATES.get(
                key,
                "你正在经历一次重要的蜕变，每一步都值得被铭记。"
            )
            result["narrative"] = narrative
        return result

    # ------------------------------------------------------------------
    # 统一入口：防火墙 → 判定 → 叙事化
    # ------------------------------------------------------------------
    def process(self, source_ui: Optional[str], current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        完整处理流水线:
        1. SOP 6.2 防火墙检查
        2. TTM 阶段跃迁判定
        3. L6 成长之旅叙事重写
        """
        # Step 1: 防火墙
        firewall = self.firewall_check(source_ui)
        if firewall is not None:
            return firewall

        # Step 2: 核心判定
        transition = self.evaluate_transition(current_state)

        # Step 3: L6 叙事化
        return self.l6_humanize(transition)

    # ------------------------------------------------------------------
    # 周报：过去 7 天行为趋势分析 (DB-backed)
    # ------------------------------------------------------------------
    def analyze_weekly_trend(self, user_id: str) -> Dict[str, Any]:
        """
        从 behavior_traces 表中提取过去 7 天的记录，
        生成一段回顾式的人文摘要，供周报或教练端使用。

        返回:
          - total_evaluations / transition_count / avg_belief
          - transitions: 跃迁详情列表
          - belief_trend: 信念分数变化 (起始 → 最终)
          - period: 时间区间
          - summary + weekly_narrative: 人文风格的周回顾摘要
        """
        from core.database import get_db_session
        from core.models import BehaviorTrace

        cutoff = datetime.utcnow() - timedelta(days=7)

        with get_db_session() as db:
            traces = (
                db.query(BehaviorTrace)
                .filter(
                    BehaviorTrace.user_id == user_id,
                    BehaviorTrace.timestamp >= cutoff,
                )
                .order_by(BehaviorTrace.timestamp.asc())
                .all()
            )

        # 转为字典列表供 generate_weekly_insight 复用
        history = [
            {
                "from_stage": t.from_stage,
                "to_stage": t.to_stage,
                "is_transition": t.is_transition,
                "belief": t.belief_score or 0.0,
                "actions": t.action_count or 0,
                "timestamp": t.timestamp.isoformat() if t.timestamp else "",
            }
            for t in traces
        ]

        if not traces:
            return {
                "user_id": user_id,
                "period": "Past 7 Days",
                "total_evaluations": 0,
                "transition_count": 0,
                "avg_belief": 0.0,
                "transitions": [],
                "belief_trend": None,
                "summary": "本周你保持了静默，但每一个蓄势待发的日子都算数。",
                "weekly_narrative": "本周你保持了静默，但每一个蓄势待发的日子都算数。",
            }

        # 统计
        transitions = [
            {
                "from": t.from_stage,
                "to": t.to_stage,
                "belief": t.belief_score,
                "time": t.timestamp.isoformat(),
            }
            for t in traces if t.is_transition
        ]

        belief_scores = [t.belief_score for t in traces if t.belief_score is not None]
        belief_start = belief_scores[0] if belief_scores else None
        belief_end = belief_scores[-1] if belief_scores else None
        avg_belief = round(sum(belief_scores) / len(belief_scores), 2) if belief_scores else 0.0

        # 生成人文摘要
        summary = self._compose_weekly_narrative(
            total=len(traces),
            transitions=transitions,
            belief_start=belief_start,
            belief_end=belief_end,
            avg_belief=avg_belief,
        )

        return {
            "user_id": user_id,
            "period": "Past 7 Days",
            "total_evaluations": len(traces),
            "transition_count": len(transitions),
            "avg_belief": avg_belief,
            "transitions": transitions,
            "belief_trend": {"start": belief_start, "end": belief_end},
            "summary": summary,
            "weekly_narrative": summary,
        }

    # ------------------------------------------------------------------
    # 周报叙事 (async，接受预取列表，供外部调用)
    # ------------------------------------------------------------------
    async def generate_weekly_insight(self, history: list) -> Dict[str, Any]:
        """
        周报叙事算法：将 7 天的 BehaviorTrace 列表提炼为人文摘要。
        接受已查询好的 history 字典列表，不直接访问数据库。
        """
        if not history:
            return {
                "period": "Past 7 Days",
                "avg_belief": 0.0,
                "transition_count": 0,
                "weekly_narrative": "本周你保持了静默，但每一个蓄势待发的日子都算数。",
            }

        # 1. 寻找高光时刻 (跃迁)
        transitions = [h for h in history if h.get("is_transition")]

        # 2. 统计能量值 (Belief 趋势)
        avg_belief = round(
            sum(h.get("belief", 0) for h in history) / len(history), 2
        )

        # 3. 构造人文叙事 — 三级分层
        if transitions:
            last_t = transitions[-1]
            date_str = last_t.get("timestamp", "")[:10]
            summary = (
                f"这是值得铭记的一周！你在 {date_str} 完成了从 "
                f"{last_t['from_stage']} 到 {last_t['to_stage']} 的跨越。"
            )
        elif avg_belief > 0.7:
            summary = (
                "本周你虽然没有阶段性的跳变，但你的信念指数持续处于高位，"
                "正如黎明前的曙光。"
            )
        else:
            summary = (
                "本周是沉淀的一周。"
                "英雄在行动前，总需要漫长的冥想来积蓄力量。"
            )

        return {
            "period": "Past 7 Days",
            "avg_belief": avg_belief,
            "transition_count": len(transitions),
            "weekly_narrative": summary,
        }

    # ------------------------------------------------------------------
    # 周叙事生成器 (内部方法，被 analyze_weekly_trend 调用)
    # ------------------------------------------------------------------
    @staticmethod
    def _compose_weekly_narrative(
        total: int,
        transitions: List[Dict],
        belief_start: Optional[float],
        belief_end: Optional[float],
        avg_belief: float = 0.0,
    ) -> str:
        """将统计数据编织成一段回顾式人文叙事（三级分层）。"""
        parts: List[str] = []

        # 开篇
        parts.append(f"过去一周，系统共记录了 {total} 次行为评估。")

        # 跃迁亮点 — 带具体日期
        if transitions:
            last_t = transitions[-1]
            date_str = last_t.get("time", "")[:10]
            parts.append(
                f"你在 {date_str} 从 {last_t['from']} 阶段成功迈入了 {last_t['to']} 阶段，"
                f"这是一次值得庆祝的进步。"
            )
            if len(transitions) > 1:
                parts.append(f"本周共完成了 {len(transitions)} 次阶段跃迁！")
        elif avg_belief > 0.7:
            # 高信念但无跃迁
            parts.append(
                "虽然本周没有发生阶段跃迁，但你的信念指数持续处于高位，"
                "正如黎明前的曙光。"
            )
        else:
            # 沉淀期
            parts.append(
                "本周是沉淀的一周。"
                "英雄在行动前，总需要漫长的冥想来积蓄力量。"
            )

        # 信念变化
        if belief_start is not None and belief_end is not None:
            delta = belief_end - belief_start
            if delta > 0.05:
                parts.append(
                    f"你的信念指数从 {belief_start:.2f} 上升到 {belief_end:.2f}，"
                    "内心的力量在稳步增长。"
                )
            elif delta < -0.05:
                parts.append(
                    f"信念指数有所波动（{belief_start:.2f} → {belief_end:.2f}），"
                    "这很正常，低谷之后往往是新的攀升。"
                )
            else:
                parts.append(
                    f"信念指数保持稳定在 {belief_end:.2f} 附近，状态平稳。"
                )

        # 结尾鼓励
        parts.append("继续前行，你的每一步都被铭记。")

        return "".join(parts)
