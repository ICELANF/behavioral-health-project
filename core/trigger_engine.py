from loguru import logger
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class TriggerCategory(Enum):
    PHYSIOLOGICAL = "physiological"
    PSYCHOLOGICAL = "psychological"
    BEHAVIORAL = "behavioral"
    ENVIRONMENTAL = "environmental"


class TriggerSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


@dataclass
class Trigger:
    tag_id: str
    name: str
    category: TriggerCategory
    severity: TriggerSeverity
    confidence: float = 1.0
    source: str = "direct"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag_id": self.tag_id,
            "name": self.name,
            "category": self.category.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata,
        }


class TriggerEngine:
    """轻量化 Trigger 识别引擎"""

    # Trigger 定义字典：tag_id → 元信息
    TRIGGER_DEFINITIONS: Dict[str, Dict[str, Any]] = {
        # 生理类
        "high_glucose": {
            "name": "高血糖", "category": "physiological", "severity": "high",
            "routed_agents": ["GlucoseAgent", "MetabolicAgent"],
        },
        "low_glucose": {
            "name": "低血糖", "category": "physiological", "severity": "critical",
            "routed_agents": ["CrisisAgent", "GlucoseAgent"],
        },
        "glucose_spike": {
            "name": "血糖波动", "category": "physiological", "severity": "moderate",
            "routed_agents": ["GlucoseAgent", "NutritionAgent"],
        },
        "low_hrv": {
            "name": "低HRV", "category": "physiological", "severity": "moderate",
            "routed_agents": ["StressAgent", "SleepAgent"],
        },
        "high_stress_hrv": {
            "name": "HRV压力指征", "category": "physiological", "severity": "high",
            "routed_agents": ["StressAgent", "MentalHealthAgent"],
        },
        "poor_sleep": {
            "name": "睡眠不佳", "category": "physiological", "severity": "moderate",
            "routed_agents": ["SleepAgent"],
        },
        # 心理类
        "crisis_keyword": {
            "name": "危机关键词", "category": "psychological", "severity": "critical",
            "routed_agents": ["CrisisAgent"],
        },
        "high_anxiety": {
            "name": "高焦虑", "category": "psychological", "severity": "high",
            "routed_agents": ["MentalHealthAgent", "StressAgent"],
        },
        "depression_sign": {
            "name": "抑郁信号", "category": "psychological", "severity": "high",
            "routed_agents": ["MentalHealthAgent", "CrisisAgent"],
        },
        "stress_overload": {
            "name": "压力过载", "category": "psychological", "severity": "high",
            "routed_agents": ["StressAgent", "MentalHealthAgent"],
        },
        "negative_sentiment": {
            "name": "负面情绪", "category": "psychological", "severity": "moderate",
            "routed_agents": ["MentalHealthAgent", "MotivationAgent"],
        },
        "low_motivation": {
            "name": "动机低下", "category": "psychological", "severity": "moderate",
            "routed_agents": ["MotivationAgent", "CoachingAgent"],
        },
        # 行为类
        "work_stress": {
            "name": "工作压力", "category": "behavioral", "severity": "moderate",
            "routed_agents": ["StressAgent", "CoachingAgent"],
        },
        "sedentary": {
            "name": "久坐不动", "category": "behavioral", "severity": "moderate",
            "routed_agents": ["ExerciseAgent"],
        },
        "high_gi_meal": {
            "name": "高GI饮食", "category": "behavioral", "severity": "moderate",
            "routed_agents": ["NutritionAgent", "GlucoseAgent"],
        },
        "task_failure": {
            "name": "任务失败", "category": "behavioral", "severity": "low",
            "routed_agents": ["CoachingAgent", "MotivationAgent"],
        },
        "low_adherence": {
            "name": "依从性低", "category": "behavioral", "severity": "low",
            "routed_agents": ["CoachingAgent", "MotivationAgent"],
        },
    }

    # 文本关键词 → trigger tag_id 映射
    TEXT_KEYWORD_RULES: List[tuple] = [
        # (关键词列表, tag_id, confidence)
        (["不想活", "自杀", "不想活了", "活不下去", "了结", "轻生", "没有意义"], "crisis_keyword", 0.95),
        (["焦虑", "紧张", "害怕", "恐惧", "不安", "担心"], "high_anxiety", 0.80),
        (["抑郁", "绝望", "空虚", "没有希望"], "depression_sign", 0.85),
        (["压力大", "压力特别大", "受不了", "压力", "喘不过气"], "stress_overload", 0.80),
        (["加班", "工作忙", "工作压力", "天天加班"], "work_stress", 0.75),
        (["睡不好", "失眠", "睡不着", "睡眠不好", "没睡好", "辗转反侧"], "poor_sleep", 0.80),
        (["不想做", "没动力", "不想动", "提不起劲", "什么都不想做", "懒得"], "low_motivation", 0.75),
        (["糟糕", "不好", "难过", "伤心", "烦躁", "郁闷", "疲惫"], "negative_sentiment", 0.65),
        (["久坐", "坐着", "没时间运动", "不运动", "没运动"], "sedentary", 0.70),
        (["米饭", "面食", "面包", "蛋糕", "甜食", "奶茶", "可乐", "高GI"], "high_gi_meal", 0.70),
    ]

    def __init__(self):
        logger.info("Trigger 引擎初始化完成")

    async def recognize_triggers(self, user_id, **kwargs) -> List[Trigger]:
        """识别多模态数据中的 Triggers"""
        triggers: List[Trigger] = []
        seen_tag_ids: set = set()

        text_content = kwargs.get("text_content")
        hrv_values = kwargs.get("hrv_values")
        glucose_values = kwargs.get("glucose_values")

        # 1. 文本关键词识别
        if text_content:
            for keywords, tag_id, confidence in self.TEXT_KEYWORD_RULES:
                if tag_id in seen_tag_ids:
                    continue
                for kw in keywords:
                    if kw in text_content:
                        defn = self.TRIGGER_DEFINITIONS[tag_id]
                        triggers.append(Trigger(
                            tag_id=tag_id,
                            name=defn["name"],
                            category=TriggerCategory(defn["category"]),
                            severity=TriggerSeverity(defn["severity"]),
                            confidence=confidence,
                            source="text",
                            metadata={"matched_keyword": kw},
                        ))
                        seen_tag_ids.add(tag_id)
                        break

        # 2. HRV 识别
        if hrv_values and len(hrv_values) >= 3:
            hrv_triggers = self.recognize_hrv_triggers(hrv_values)
            for t in hrv_triggers:
                if t.tag_id not in seen_tag_ids:
                    triggers.append(t)
                    seen_tag_ids.add(t.tag_id)

        # 3. 血糖识别
        if glucose_values and len(glucose_values) >= 1:
            glucose_triggers = self.recognize_glucose_triggers(glucose_values)
            for t in glucose_triggers:
                if t.tag_id not in seen_tag_ids:
                    triggers.append(t)
                    seen_tag_ids.add(t.tag_id)

        return triggers

    def recognize_hrv_triggers(self, hrv_values: List[float]) -> List[Trigger]:
        """基于 HRV 数据识别生理 Triggers"""
        triggers: List[Trigger] = []
        if not hrv_values:
            return triggers

        mean_hrv = sum(hrv_values) / len(hrv_values)

        # 低 HRV（< 65ms 均值）→ 压力/交感兴奋
        if mean_hrv < 65:
            triggers.append(Trigger(
                tag_id="high_stress_hrv",
                name="HRV压力指征",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.HIGH,
                confidence=0.85,
                source="hrv",
                metadata={"mean_hrv": round(mean_hrv, 1), "threshold": 65},
            ))
        elif mean_hrv < 70:
            triggers.append(Trigger(
                tag_id="low_hrv",
                name="低HRV",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=0.75,
                source="hrv",
                metadata={"mean_hrv": round(mean_hrv, 1), "threshold": 70},
            ))

        return triggers

    def recognize_glucose_triggers(
        self,
        glucose_values: List[float],
    ) -> List[Trigger]:
        """
        基于血糖数据识别生理 Triggers（同步版，不依赖 multimodal_client）

        直接根据传入的 glucose_values 计算 max / min / variation，
        保留原 v0 的阈值判断逻辑（3.9 / 10.0 / 3.0）。
        """
        triggers: List[Trigger] = []

        if not glucose_values:
            return triggers

        max_glucose = max(glucose_values)
        min_glucose = min(glucose_values)
        variation = max_glucose - min_glucose

        # 高血糖
        if max_glucose > 10.0:
            triggers.append(Trigger(
                tag_id="high_glucose",
                name="高血糖",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.HIGH,
                confidence=1.0,
                metadata={"max_glucose": max_glucose, "threshold": 10.0},
            ))

        # 低血糖
        if min_glucose < 3.9:
            triggers.append(Trigger(
                tag_id="low_glucose",
                name="低血糖",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.CRITICAL,
                confidence=1.0,
                metadata={"min_glucose": min_glucose, "threshold": 3.9},
            ))

        # 血糖波动
        if variation > 3.0:
            triggers.append(Trigger(
                tag_id="glucose_spike",
                name="血糖波动",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=1.0,
                metadata={"variation": variation, "threshold": 3.0},
            ))

        return triggers

    def get_trigger_definition(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        """获取单个 Trigger 的定义"""
        return self.TRIGGER_DEFINITIONS.get(trigger_id)

    def get_all_triggers(self) -> Dict[str, Dict[str, Any]]:
        """获取所有 Trigger 定义字典"""
        return dict(self.TRIGGER_DEFINITIONS)

# 全局单例
_trigger_engine = None

def get_trigger_engine() -> TriggerEngine:
    global _trigger_engine
    if _trigger_engine is None:
        _trigger_engine = TriggerEngine()
    return _trigger_engine