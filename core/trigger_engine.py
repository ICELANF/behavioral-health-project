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
    """轻量化 Trigger 识别引擎（验证版）"""

    def __init__(self):
        logger.info("Trigger 引擎初始化完成")

    async def recognize_triggers(self, user_id, **kwargs):
        """验证期间直接返回空列表，不触发复杂逻辑"""
        return []

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

# 全局单例
_trigger_engine = None

def get_trigger_engine() -> TriggerEngine:
    global _trigger_engine
    if _trigger_engine is None:
        _trigger_engine = TriggerEngine()
    return _trigger_engine