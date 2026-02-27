"""
行为干预计划生成 — 从 V0 MasterAgent 提取

原始位置: core/master_agent_v0.py::create_action_plan()
提取原因: V0 的 6874 行中, 这是独有且有价值的业务逻辑

功能:
  - 根据分析结果 + 用户画像 + 行为阶段 → 生成个性化干预计划
  - 包含完整干预策略库 (§7 行为处方)
"""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── 干预策略库 (从 V0 提取) ──
STAGE_STRATEGIES = {
    "precontemplation": {
        "goal": "提高觉察",
        "approach": "信息提供 + 轻触碰",
        "intensity": "minimal",
        "actions": [
            {"type": "awareness", "description": "分享一个健康小知识", "difficulty": "minimal"},
            {"type": "reflection", "description": "回想今天的一个健康瞬间", "difficulty": "minimal"},
        ],
    },
    "contemplation": {
        "goal": "探索动机",
        "approach": "动机访谈 + 利弊分析",
        "intensity": "soft",
        "actions": [
            {"type": "motivational", "description": "写下改变的3个好处", "difficulty": "easy"},
            {"type": "observation", "description": "记录一天的饮食时间", "difficulty": "easy"},
        ],
    },
    "preparation": {
        "goal": "制定计划",
        "approach": "目标设定 + 资源准备",
        "intensity": "normal",
        "actions": [
            {"type": "planning", "description": "制定本周3个小目标", "difficulty": "moderate"},
            {"type": "environment", "description": "清理冰箱里的不健康食品", "difficulty": "easy"},
            {"type": "social", "description": "告诉一个人你的健康计划", "difficulty": "easy"},
        ],
    },
    "action": {
        "goal": "执行与调整",
        "approach": "行为处方执行 + 自我监测",
        "intensity": "challenge",
        "actions": [
            {"type": "execution", "description": "执行今日行为处方", "difficulty": "moderate"},
            {"type": "monitoring", "description": "记录执行情况和感受", "difficulty": "easy"},
            {"type": "reward", "description": "完成后给自己一个小奖励", "difficulty": "minimal"},
        ],
    },
    "maintenance": {
        "goal": "巩固与预防复发",
        "approach": "习惯强化 + 身份认同",
        "intensity": "normal",
        "actions": [
            {"type": "identity", "description": "写下'我是一个注重健康的人'", "difficulty": "minimal"},
            {"type": "challenge", "description": "尝试一个进阶版行为处方", "difficulty": "hard"},
            {"type": "mentoring", "description": "分享经验帮助一个新手", "difficulty": "moderate"},
        ],
    },
}

# TTM 阶段到策略映射
_STAGE_MAP = {
    "S0": "precontemplation", "S1": "precontemplation",
    "S2": "contemplation", "S3": "preparation",
    "S4": "action", "S5": "maintenance", "S6": "maintenance",
}


def create_action_plan(
    analysis: Optional[Any] = None,
    profile: Dict[str, Any] = None,
    stage: str = "contemplation",
) -> Dict[str, Any]:
    """
    生成个性化行为干预计划

    Args:
        analysis: Agent 分析结果 (可选)
        profile:  用户画像
        stage:    行为阶段 (TTM: S0-S6 或英文阶段名)

    Returns:
        {
            "stage": str,
            "goal": str,
            "approach": str,
            "actions": list[dict],
            "duration_weeks": int,
            "personalization": dict,
        }
    """
    profile = profile or {}

    # 标准化阶段名
    stage_key = _STAGE_MAP.get(stage, stage)
    if stage_key not in STAGE_STRATEGIES:
        stage_key = "contemplation"

    strategy = STAGE_STRATEGIES[stage_key]
    actions = list(strategy["actions"])

    # 个性化调整
    personalization = {}

    # 基于分析结果追加针对性 action
    if analysis:
        findings = getattr(analysis, "findings", []) if hasattr(analysis, "findings") else []
        if isinstance(analysis, dict):
            findings = analysis.get("findings", [])

        for finding in findings[:3]:
            finding_str = str(finding).lower()
            if "血糖" in finding_str:
                actions.append({"type": "glucose_specific",
                                "description": "餐后30分钟散步15分钟", "difficulty": "easy"})
                personalization["glucose_focus"] = True
            elif "睡眠" in finding_str:
                actions.append({"type": "sleep_specific",
                                "description": "睡前90分钟放下手机", "difficulty": "moderate"})
                personalization["sleep_focus"] = True
            elif "压力" in finding_str or "HRV" in finding_str:
                actions.append({"type": "stress_specific",
                                "description": "每天3次4-7-8呼吸练习", "difficulty": "easy"})
                personalization["stress_focus"] = True

    # 基于 SPI 分数调整强度
    spi = profile.get("spi_score", 50)
    if spi < 30:
        actions = [a for a in actions if a.get("difficulty") in ("minimal", "easy")]
        personalization["intensity_adjusted"] = "reduced"
    elif spi > 80:
        personalization["intensity_adjusted"] = "enhanced"

    return {
        "stage": stage_key,
        "goal": strategy["goal"],
        "approach": strategy["approach"],
        "intensity": strategy["intensity"],
        "actions": actions,
        "duration_weeks": 4 if stage_key in ("precontemplation", "contemplation") else 8,
        "personalization": personalization,
    }
