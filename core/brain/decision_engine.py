# core/brain/decision_engine.py
from typing import Dict, Any, Optional
from datetime import datetime

# SOP 6.2 公共防火墙：这些 UI 来源直接返回 SILENCE，不经过大脑判定
FIREWALL_SILENT_SOURCES = {"UI-1"}

# L6 英雄之旅叙事模板
HERO_JOURNEY_TEMPLATES = {
    "S2_to_S3": (
        "你已经走过了准备期的考验，内心的信念之火已被点燃。"
        "现在，你正式踏上行动的旅程——这是英雄之旅中最关键的一步。"
        "每一个小小的行动，都是你迈向新生活的勋章。"
    ),
}


class BehavioralBrain:
    def __init__(self, config: Dict[str, Any]):
        self.config = config  # 来源于 configs/spi_mapping.json

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
    # 核心判定：TTM 阶段跃迁
    # ------------------------------------------------------------------
    def evaluate_transition(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        输入: 包含 belief, action_count_3d, current_stage 的字典
        输出: 判定后的阶段及建议动作
        """
        last_stage = current_state.get("current_stage", "S0")
        belief = current_state.get("belief", 0.0)
        actions = current_state.get("action_count_3d", 0)

        target_stage = last_stage
        triggered = False

        # 判定 S2 -> S3 的核心转化逻辑
        if last_stage == "S2":
            thresholds = self.config.get("thresholds", {}).get("S2_to_S3", {})
            min_belief = thresholds.get("min_belief", 0.6)
            min_capability = thresholds.get("min_capability", 0.5)
            if belief >= min_belief and actions >= 1:
                target_stage = "S3"
                triggered = True

        return {
            "from_stage": last_stage,
            "to_stage": target_stage,
            "is_transition": triggered,
            "timestamp": datetime.now().isoformat(),
            "spi_summary": {"belief": belief, "actions": actions},
        }

    # ------------------------------------------------------------------
    # L6 热重写：英雄之旅叙事化
    # ------------------------------------------------------------------
    def l6_humanize(self, transition_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        如果发生阶段跃迁，用英雄之旅风格的叙事替换原始数据，
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
        3. L6 英雄之旅叙事重写
        """
        # Step 1: 防火墙
        firewall = self.firewall_check(source_ui)
        if firewall is not None:
            return firewall

        # Step 2: 核心判定
        transition = self.evaluate_transition(current_state)

        # Step 3: L6 叙事化
        return self.l6_humanize(transition)
