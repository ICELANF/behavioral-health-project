"""
行为模式识别库
来源: §13 行为模式识别库

5种核心行为模式 (§13.1):
  1. overcompensation    — 过度补偿型
  2. stress_avoidance    — 应激逃避型
  3. somatization        — 躯体化型
  4. emotional_dysregulation — 情绪失调型
  5. balanced            — 平衡型

BPT-6 行为分型 (§13.2):
  action | knowledge | emotion | relation | environment | mixed
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── 5种核心行为模式 (§13.1) ──

class BehaviorPattern(str, Enum):
    OVERCOMPENSATION = "overcompensation"            # 过度补偿型
    STRESS_AVOIDANCE = "stress_avoidance"            # 应激逃避型
    SOMATIZATION = "somatization"                    # 躯体化型
    EMOTIONAL_DYSREGULATION = "emotional_dysregulation"  # 情绪失调型
    BALANCED = "balanced"                            # 平衡型


@dataclass
class PatternProfile:
    """行为模式检测结果"""
    primary_pattern: BehaviorPattern
    confidence: float
    secondary_pattern: Optional[BehaviorPattern] = None
    indicators: dict = field(default_factory=dict)
    recommended_experts: list[str] = field(default_factory=list)


# §13.1 模式定义表
PATTERN_DEFINITIONS = {
    BehaviorPattern.OVERCOMPENSATION: {
        "name": "过度补偿型",
        "description": "通过过度行为弥补不安全感",
        "key_indicators": ["hrv_sdnn低", "焦虑高", "精力-情绪差异大"],
        "recommended_experts": ["心理", "营养"],
    },
    BehaviorPattern.STRESS_AVOIDANCE: {
        "name": "应激逃避型",
        "description": "面对压力选择回避和退缩",
        "key_indicators": ["hrv_sdnn低", "压力高", "活动量低", "社交少"],
        "recommended_experts": ["心理", "运动康复"],
    },
    BehaviorPattern.SOMATIZATION: {
        "name": "躯体化型",
        "description": "心理压力通过身体症状表现",
        "key_indicators": ["scl90高", "hrv低", "疼痛多", "频繁就医"],
        "recommended_experts": ["心理", "中医"],
    },
    BehaviorPattern.EMOTIONAL_DYSREGULATION: {
        "name": "情绪失调型",
        "description": "情绪波动大, 难以自我调节",
        "key_indicators": ["情绪变异高", "焦虑/抑郁高", "hrv_rmssd低"],
        "recommended_experts": ["心理"],
    },
    BehaviorPattern.BALANCED: {
        "name": "平衡型",
        "description": "身心状态相对平衡稳定",
        "key_indicators": ["hrv正常", "焦虑低", "精力好", "睡眠好"],
        "recommended_experts": ["营养", "中医"],
    },
}


# ── BPT-6 行为分型 (§13.2) ──

class BPT6Type(str, Enum):
    ACTION = "action"           # 行动型
    KNOWLEDGE = "knowledge"     # 知识型
    EMOTION = "emotion"         # 情感型
    RELATION = "relation"       # 关系型
    ENVIRONMENT = "environment" # 环境型
    MIXED = "mixed"             # 混合型


BPT6_DOMAIN_MAP = {
    BPT6Type.ACTION:      ["exercise", "nutrition"],
    BPT6Type.KNOWLEDGE:   ["cognitive", "nutrition"],
    BPT6Type.EMOTION:     ["emotion", "stress"],
    BPT6Type.RELATION:    ["social", "emotion"],
    BPT6Type.ENVIRONMENT: ["sleep", "nutrition"],
    BPT6Type.MIXED:       ["nutrition", "exercise", "sleep"],
}


# ── 模式检测器 ──

class PatternDetector:
    """
    基于多维度数据检测用户的行为模式

    输入数据:
      - device_data: {hrv_sdnn, hrv_rmssd, steps, sleep_hours, cgm_cv, ...}
      - psych_scores: {anxiety, depression, stress, energy, scl90, ...}
      - task_data: {completion_rate, streak_days, skip_count, ...}
      - social_data: {message_count, support_score, ...}
    """

    # 阈值配置
    HRV_LOW_THRESHOLD = 30           # SDNN < 30ms = 低
    HRV_RMSSD_LOW = 20              # RMSSD < 20ms = 低
    ANXIETY_HIGH = 60               # 焦虑分 > 60 = 高
    DEPRESSION_HIGH = 55            # 抑郁分 > 55 = 高
    STRESS_HIGH = 65                # 压力分 > 65 = 高
    ACTIVITY_LOW = 3000             # 步数 < 3000 = 低活动量
    SCL90_HIGH = 160                # SCL-90 > 160 = 高
    ENERGY_EMOTION_GAP = 20         # 精力-情绪差异 > 20 = 过度补偿信号
    SLEEP_GOOD_MIN = 7.0
    SLEEP_GOOD_MAX = 9.0

    def detect(self,
               device_data: dict = None,
               psych_scores: dict = None,
               task_data: dict = None,
               social_data: dict = None) -> PatternProfile:
        """
        检测主行为模式

        Returns:
            PatternProfile with primary & secondary pattern
        """
        device_data = device_data or {}
        psych_scores = psych_scores or {}
        task_data = task_data or {}
        social_data = social_data or {}

        scores: dict[BehaviorPattern, float] = {p: 0.0 for p in BehaviorPattern}
        indicators: dict[str, any] = {}

        # ── 指标提取 ──
        hrv_sdnn = device_data.get("hrv_sdnn")
        hrv_rmssd = device_data.get("hrv_rmssd")
        steps = device_data.get("steps")
        sleep = device_data.get("sleep_hours")
        anxiety = psych_scores.get("anxiety", 0)
        depression = psych_scores.get("depression", 0)
        stress = psych_scores.get("stress", 0)
        energy = psych_scores.get("energy", 50)
        scl90 = psych_scores.get("scl90", 0)
        social_count = social_data.get("message_count", 0)
        emotion_var = psych_scores.get("emotion_variability", 0)

        # ── 过度补偿型 ──
        if hrv_sdnn is not None and hrv_sdnn < self.HRV_LOW_THRESHOLD:
            scores[BehaviorPattern.OVERCOMPENSATION] += 2
            indicators["hrv_sdnn_low"] = hrv_sdnn
        if anxiety > self.ANXIETY_HIGH:
            scores[BehaviorPattern.OVERCOMPENSATION] += 2
        if abs(energy - (100 - anxiety)) > self.ENERGY_EMOTION_GAP:
            scores[BehaviorPattern.OVERCOMPENSATION] += 3
            indicators["energy_emotion_gap"] = True

        # ── 应激逃避型 ──
        if hrv_sdnn is not None and hrv_sdnn < self.HRV_LOW_THRESHOLD:
            scores[BehaviorPattern.STRESS_AVOIDANCE] += 1.5
        if stress > self.STRESS_HIGH:
            scores[BehaviorPattern.STRESS_AVOIDANCE] += 2
        if steps is not None and steps < self.ACTIVITY_LOW:
            scores[BehaviorPattern.STRESS_AVOIDANCE] += 2
            indicators["low_activity"] = steps
        if social_count < 3:
            scores[BehaviorPattern.STRESS_AVOIDANCE] += 1.5
            indicators["low_social"] = social_count

        # ── 躯体化型 ──
        if scl90 > self.SCL90_HIGH:
            scores[BehaviorPattern.SOMATIZATION] += 3
            indicators["scl90_high"] = scl90
        if hrv_sdnn is not None and hrv_sdnn < self.HRV_LOW_THRESHOLD:
            scores[BehaviorPattern.SOMATIZATION] += 1.5

        # ── 情绪失调型 ──
        if emotion_var > 30:
            scores[BehaviorPattern.EMOTIONAL_DYSREGULATION] += 3
            indicators["emotion_variability_high"] = emotion_var
        if anxiety > self.ANXIETY_HIGH or depression > self.DEPRESSION_HIGH:
            scores[BehaviorPattern.EMOTIONAL_DYSREGULATION] += 2
        if hrv_rmssd is not None and hrv_rmssd < self.HRV_RMSSD_LOW:
            scores[BehaviorPattern.EMOTIONAL_DYSREGULATION] += 1.5

        # ── 平衡型 ──
        balanced_score = 0
        if hrv_sdnn is not None and hrv_sdnn >= 50:
            balanced_score += 2
        if anxiety < 40:
            balanced_score += 1.5
        if sleep is not None and self.SLEEP_GOOD_MIN <= sleep <= self.SLEEP_GOOD_MAX:
            balanced_score += 1.5
        if energy >= 60:
            balanced_score += 1
        scores[BehaviorPattern.BALANCED] = balanced_score

        # ── 选出主/次模式 ──
        sorted_patterns = sorted(scores.items(), key=lambda x: -x[1])
        primary = sorted_patterns[0]
        secondary = sorted_patterns[1] if len(sorted_patterns) > 1 and sorted_patterns[1][1] > 2 else None

        max_possible = 10.0
        confidence = min(primary[1] / max_possible, 1.0)

        defn = PATTERN_DEFINITIONS[primary[0]]

        return PatternProfile(
            primary_pattern=primary[0],
            confidence=round(confidence, 3),
            secondary_pattern=secondary[0] if secondary else None,
            indicators=indicators,
            recommended_experts=defn["recommended_experts"],
        )

    def detect_bpt6(self, bpt6_scores: dict[str, float]) -> dict:
        """
        根据BPT-6问卷结果确定行为分型

        Args:
            bpt6_scores: {"action": 4.2, "knowledge": 3.8, ...} 每维度平均分

        Returns:
            {"dominant": BPT6Type, "scores": dict, "preferred_domains": list}
        """
        if not bpt6_scores:
            return {"dominant": BPT6Type.MIXED, "scores": {}, "preferred_domains": []}

        sorted_types = sorted(bpt6_scores.items(), key=lambda x: -x[1])
        dominant_str = sorted_types[0][0]
        try:
            dominant = BPT6Type(dominant_str)
        except ValueError:
            dominant = BPT6Type.MIXED

        return {
            "dominant": dominant,
            "scores": bpt6_scores,
            "preferred_domains": BPT6_DOMAIN_MAP.get(dominant, []),
        }


# 单例
pattern_detector = PatternDetector()
