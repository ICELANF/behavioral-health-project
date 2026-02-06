# -*- coding: utf-8 -*-
"""
StageRuntimeBuilder - 阶段运行态引擎

职责:
- 唯一负责写入 current_stage 的组件
- Agent 只能提 stage_hypothesis，由本模块校验后写入
- 验证升级硬条件（只能前进1阶，需行为事实支撑）
- 计算稳定性
- 生成风险标记

设计原则 (来自系统修正版总原则):
  只有 StageRuntimeBuilder 可以写 current_stage
  其他模块只能读取或提出 stage_hypothesis
"""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger

# 加载阈值配置
_CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "configs"
)


def _load_thresholds() -> Dict:
    path = os.path.join(_CONFIG_DIR, "spi_mapping.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("thresholds", {})
    except Exception as e:
        logger.warning(f"Failed to load thresholds: {e}")
        return {}


# 阶段有序列表
STAGE_ORDER = ["S0", "S1", "S2", "S3", "S4", "S5", "S6"]
STAGE_INDEX = {s: i for i, s in enumerate(STAGE_ORDER)}


@dataclass
class StageInput:
    """阶段判定输入"""
    user_id: int
    current_stage: str  # 画像中的当前阶段
    stage_hypothesis: str  # Agent 或评估提出的假设阶段
    # 评估指标
    belief_score: float = 0.0  # SPI 信念分
    awareness_score: float = 0.0  # 觉察度 (TTM7 AW)
    capability_score: float = 0.0  # 能力分
    # 行为事实
    action_completed_7d: int = 0  # 过去7天完成的行为数
    action_interrupt_72h: bool = False  # 72小时内是否有中断
    streak_days: int = 0  # 连续行为天数
    spi_score: float = 0.0  # SPI 总分


@dataclass
class RuntimeState:
    """阶段运行态输出"""
    user_id: int
    confirmed_stage: str  # 最终确认的阶段
    previous_stage: str
    is_transition: bool
    stability: str  # stable / semi_stable / unstable
    risk_flags: List[str] = field(default_factory=list)
    decision_reason: str = ""
    timestamp: str = ""


class StageRuntimeBuilder:
    """
    阶段运行态引擎 - 系统唯一可写 current_stage 的组件
    """

    def __init__(self):
        self.thresholds = _load_thresholds()

    def build(self, input: StageInput) -> Tuple[RuntimeState, List[str]]:
        """
        核心入口: 验证 stage_hypothesis 并生成 RuntimeState

        返回: (RuntimeState, decision_logs)
        """
        logs: List[str] = []
        now = datetime.utcnow()

        current = input.current_stage
        proposed = input.stage_hypothesis
        logs.append(f"Input: current={current}, proposed={proposed}")

        # 1. 验证 stage_hypothesis 合法性
        if proposed not in STAGE_INDEX:
            logs.append(f"REJECT: invalid stage '{proposed}'")
            return self._make_state(input, current, False, "unstable",
                                    f"Invalid stage: {proposed}"), logs

        # 2. 如果相同阶段 → 维持
        if proposed == current:
            stability = self._calc_stability(input)
            risk_flags = self._calc_risk_flags(input)
            logs.append(f"MAINTAIN: stage={current}, stability={stability}")
            return self._make_state(input, current, False, stability,
                                    "Stage maintained", risk_flags), logs

        # 3. 检查升级/降级方向
        current_idx = STAGE_INDEX.get(current, 0)
        proposed_idx = STAGE_INDEX.get(proposed, 0)

        if proposed_idx > current_idx:
            # 升级请求
            allowed, reason = self._upgrade_allowed(input)
            if allowed:
                stability = "semi_stable"  # 刚升级，状态不稳定
                risk_flags = self._calc_risk_flags(input)
                logs.append(f"UPGRADE: {current} -> {proposed}, reason={reason}")
                return self._make_state(input, proposed, True, stability,
                                        reason, risk_flags), logs
            else:
                # 升级被拒 → 维持当前阶段
                stability = self._calc_stability(input)
                risk_flags = self._calc_risk_flags(input)
                logs.append(f"UPGRADE_DENIED: {current} -> {proposed}, reason={reason}")
                return self._make_state(input, current, False, stability,
                                        f"Upgrade denied: {reason}", risk_flags), logs

        else:
            # 降级请求 (回退) — 允许但标记风险
            risk_flags = ["relapse_risk"]
            risk_flags.extend(self._calc_risk_flags(input))
            logs.append(f"DOWNGRADE: {current} -> {proposed}")
            return self._make_state(input, proposed, True, "unstable",
                                    "Stage regression detected", risk_flags), logs

    def _upgrade_allowed(self, input: StageInput) -> Tuple[bool, str]:
        """
        升级硬规则检查:
        1. 只能向前1阶
        2. 7天内有完成行为 (S3+)
        3. 72小时无中断 (S4+)
        4. SPI ≥ 阈值 (如适用)
        5. 连续天数 (S4→S5, S5→S6)
        """
        current_idx = STAGE_INDEX.get(input.current_stage, 0)
        proposed_idx = STAGE_INDEX.get(input.stage_hypothesis, 0)

        # 规则1: 只能前进1阶
        if proposed_idx - current_idx > 1:
            return False, f"Can only advance 1 stage at a time (tried {input.current_stage}->{input.stage_hypothesis})"

        transition_key = f"{input.current_stage}_to_{input.stage_hypothesis}"
        threshold = self.thresholds.get(transition_key, {})

        # 规则: 觉察度 (S0→S1)
        min_aw = threshold.get("min_awareness", 0)
        if min_aw > 0 and input.awareness_score < min_aw:
            return False, f"Awareness {input.awareness_score:.2f} < {min_aw}"

        # 规则: 信念分 (S1+)
        min_belief = threshold.get("min_belief", 0)
        if min_belief > 0 and input.belief_score < min_belief:
            return False, f"Belief {input.belief_score:.2f} < {min_belief}"

        # 规则: 能力分 (S2→S3)
        min_cap = threshold.get("min_capability", 0)
        if min_cap > 0 and input.capability_score < min_cap:
            return False, f"Capability {input.capability_score:.2f} < {min_cap}"

        # 规则: 7天行为数 (S3→S4)
        min_actions = threshold.get("min_actions_7d", 0)
        if min_actions > 0 and input.action_completed_7d < min_actions:
            return False, f"Actions in 7d: {input.action_completed_7d} < {min_actions}"

        # 规则: 连续天数 (S4→S5, S5→S6)
        min_streak = threshold.get("min_streak_days", 0)
        if min_streak > 0 and input.streak_days < min_streak:
            return False, f"Streak days: {input.streak_days} < {min_streak}"

        # 规则: 72小时无中断 (S3+升级)
        if current_idx >= 3 and input.action_interrupt_72h:
            return False, "72h action interrupt detected"

        return True, f"All thresholds met for {transition_key}"

    def _calc_stability(self, input: StageInput) -> str:
        """
        计算阶段稳定性

        stable: SPI高 + 无中断 + 连续行为
        semi_stable: 部分条件满足
        unstable: 多项条件不满足
        """
        score = 0
        # SPI 高分加分
        if input.spi_score >= 50:
            score += 1
        if input.spi_score >= 70:
            score += 1
        # 无中断加分
        if not input.action_interrupt_72h:
            score += 1
        # 7天行为加分
        if input.action_completed_7d >= 3:
            score += 1
        # 连续天数加分
        if input.streak_days >= 7:
            score += 1

        if score >= 4:
            return "stable"
        elif score >= 2:
            return "semi_stable"
        else:
            return "unstable"

    def _calc_risk_flags(self, input: StageInput) -> List[str]:
        """计算风险标记"""
        flags = []

        # 中断风险
        if input.action_interrupt_72h and STAGE_INDEX.get(input.current_stage, 0) >= 3:
            flags.append("dropout_risk")

        # SPI 低分风险
        if input.spi_score < 30:
            flags.append("low_confidence_risk")

        # 行为不足风险
        if input.action_completed_7d == 0 and STAGE_INDEX.get(input.current_stage, 0) >= 4:
            flags.append("relapse_risk")

        return flags

    def _make_state(
        self,
        input: StageInput,
        stage: str,
        is_transition: bool,
        stability: str,
        reason: str,
        risk_flags: Optional[List[str]] = None,
    ) -> RuntimeState:
        return RuntimeState(
            user_id=input.user_id,
            confirmed_stage=stage,
            previous_stage=input.current_stage,
            is_transition=is_transition,
            stability=stability,
            risk_flags=risk_flags or [],
            decision_reason=reason,
            timestamp=datetime.utcnow().isoformat(),
        )
