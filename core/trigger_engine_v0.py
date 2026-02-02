"""
Trigger 识别引擎
Trigger Recognition Engine

基于多模态系统输出，识别用户行为、生理、心理触发标签
这是 L2 评估层的核心组件
"""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from core.multimodal_client import get_multimodal_client


# ============================================
# Trigger 分类体系
# ============================================

class TriggerCategory(Enum):
    """Trigger 类别"""
    PHYSIOLOGICAL = "physiological"  # 生理类
    PSYCHOLOGICAL = "psychological"  # 心理类
    BEHAVIORAL = "behavioral"        # 行为类
    ENVIRONMENTAL = "environmental"  # 环境类


class TriggerSeverity(Enum):
    """Trigger 严重程度"""
    CRITICAL = "critical"  # 危急
    HIGH = "high"          # 高
    MODERATE = "moderate"  # 中
    LOW = "low"            # 低


@dataclass
class Trigger:
    """Trigger 标签"""
    tag_id: str                          # 标签ID
    name: str                            # 标签名称
    category: TriggerCategory            # 类别
    severity: TriggerSeverity            # 严重程度
    confidence: float = 1.0              # 置信度 0-1
    source: str = "multimodal"           # 来源
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag_id": self.tag_id,
            "name": self.name,
            "category": self.category.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata
        }


# ============================================
# Trigger 字典定义
# ============================================

# 生理类 Trigger
PHYSIOLOGICAL_TRIGGERS = {
    # 血糖相关
    "high_glucose": {
        "name": "高血糖",
        "severity": TriggerSeverity.HIGH,
        "threshold": {"value": ">10.0", "unit": "mmol/L"}
    },
    "low_glucose": {
        "name": "低血糖",
        "severity": TriggerSeverity.CRITICAL,
        "threshold": {"value": "<3.9", "unit": "mmol/L"}
    },
    "glucose_spike": {
        "name": "血糖波动",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"variation": ">3.0", "unit": "mmol/L"}
    },

    # HRV相关
    "low_hrv": {
        "name": "低心率变异性",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"sdnn": "<30", "unit": "ms"}
    },
    "high_stress_hrv": {
        "name": "压力指标异常",
        "severity": TriggerSeverity.HIGH,
        "threshold": {"stress_index": ">80"}
    },

    # 心率相关
    "high_heartrate": {
        "name": "心率过高",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"hr": ">100", "unit": "bpm"}
    },
    "low_heartrate": {
        "name": "心率过低",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"hr": "<60", "unit": "bpm"}
    },

    # 睡眠相关
    "poor_sleep": {
        "name": "睡眠质量差",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"efficiency": "<70", "unit": "%"}
    },
}

# 心理类 Trigger
PSYCHOLOGICAL_TRIGGERS = {
    # 情绪相关
    "high_anxiety": {
        "name": "高焦虑",
        "severity": TriggerSeverity.HIGH,
        "threshold": {"emotion": "anxious", "confidence": ">0.6"}
    },
    "depression_sign": {
        "name": "抑郁倾向",
        "severity": TriggerSeverity.HIGH,
        "threshold": {"emotion": "sad", "duration": ">7days"}
    },
    "stress_overload": {
        "name": "压力过载",
        "severity": TriggerSeverity.HIGH,
        "threshold": {"stress_level": ">80"}
    },
    "negative_sentiment": {
        "name": "负面情绪",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"sentiment": "negative", "score": "<-0.5"}
    },

    # 动机相关
    "low_motivation": {
        "name": "动机低下",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"motivation_score": "<30"}
    },

    # 风险信号
    "crisis_keyword": {
        "name": "危机关键词",
        "severity": TriggerSeverity.CRITICAL,
        "threshold": {"risk_score": ">0.5"}
    },
}

# 行为类 Trigger
BEHAVIORAL_TRIGGERS = {
    # 依从性相关
    "task_failure": {
        "name": "任务失败",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"consecutive_failures": ">=3"}
    },
    "missing_checkin": {
        "name": "漏打卡",
        "severity": TriggerSeverity.LOW,
        "threshold": {"days_missing": ">=2"}
    },
    "low_adherence": {
        "name": "依从性低",
        "severity": TriggerSeverity.HIGH,
        "threshold": {"adherence_rate": "<50", "unit": "%"}
    },

    # 饮食相关
    "high_gi_meal": {
        "name": "高GI饮食",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"gi_level": "high"}
    },
    "irregular_meal": {
        "name": "饮食不规律",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"meal_time_variance": ">2hours"}
    },

    # 运动相关
    "sedentary": {
        "name": "久坐",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"activity_level": "<3000", "unit": "steps/day"}
    },
}

# 环境类 Trigger
ENVIRONMENTAL_TRIGGERS = {
    "support_lack": {
        "name": "缺乏支持",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"social_support": "<30"}
    },
    "resource_barrier": {
        "name": "资源障碍",
        "severity": TriggerSeverity.MODERATE,
        "threshold": {"resource_score": "<30"}
    },
}


# ============================================
# Trigger 识别引擎
# ============================================

class TriggerEngine:
    """
    Trigger 识别引擎

    基于多模态系统输出，自动识别 Trigger 标签
    """

    def __init__(self):
        self.multimodal_client = get_multimodal_client()
        self.trigger_dict = self._build_trigger_dict()
        logger.info("Trigger 引擎初始化完成")

    def _build_trigger_dict(self) -> Dict[str, Dict]:
        """构建完整 Trigger 字典"""
        return {
            **PHYSIOLOGICAL_TRIGGERS,
            **PSYCHOLOGICAL_TRIGGERS,
            **BEHAVIORAL_TRIGGERS,
            **ENVIRONMENTAL_TRIGGERS
        }

    # ============================================
    # 主入口：识别 Triggers
    # ============================================

    async def recognize_triggers(
        self,
        user_id: int,
        text_content: Optional[str] = None,
        hrv_values: Optional[List[float]] = None,
        glucose_values: Optional[List[float]] = None,
        user_profile: Optional[Dict] = None
    ) -> List[Trigger]:
        """
        综合识别 Triggers

        Args:
            user_id: 用户ID
            text_content: 文本消息
            hrv_values: HRV数据
            glucose_values: 血糖数据
            user_profile: 用户画像

        Returns:
            Trigger 列表
        """
        triggers: List[Trigger] = []

        # 1. 文本 Trigger 识别
        if text_content:
            text_triggers = await self._recognize_text_triggers(
                text_content, user_id
            )
            triggers.extend(text_triggers)

        # 2. HRV Trigger 识别
        if hrv_values:
            hrv_triggers = await self._recognize_hrv_triggers(
                hrv_values, user_id
            )
            triggers.extend(hrv_triggers)

        # 3. 血糖 Trigger 识别
        if glucose_values:
            glucose_triggers = await self._recognize_glucose_triggers(
                glucose_values, user_id
            )
            triggers.extend(glucose_triggers)

        # 4. 用户画像 Trigger 识别
        if user_profile:
            profile_triggers = self._recognize_profile_triggers(user_profile)
            triggers.extend(profile_triggers)

        # 去重
        triggers = self._deduplicate_triggers(triggers)

        logger.info(f"用户 {user_id} 识别到 {len(triggers)} 个 Triggers")
        return triggers

    # ============================================
    # 文本 Trigger 识别
    # ============================================

    async def _recognize_text_triggers(
        self,
        content: str,
        user_id: int
    ) -> List[Trigger]:
        """基于文本识别心理/情绪 Triggers"""
        triggers = []

        # 调用多模态API
        text_result = await self.multimodal_client.process_text(
            content, user_id
        )

        if not text_result:
            return triggers

        # 提取情绪
        primary_emotion = text_result.get("primary_emotion", "")
        emotions = text_result.get("emotions", {})
        sentiment = text_result.get("sentiment", "")
        sentiment_score = text_result.get("sentiment_score", 0.0)
        risk_score = text_result.get("risk_score", 0.0)

        # 识别焦虑
        if primary_emotion == "anxious" and emotions.get("anxious", 0) > 0.6:
            triggers.append(Trigger(
                tag_id="high_anxiety",
                name="高焦虑",
                category=TriggerCategory.PSYCHOLOGICAL,
                severity=TriggerSeverity.HIGH,
                confidence=emotions.get("anxious", 0),
                metadata={"emotion": primary_emotion, "score": emotions.get("anxious")}
            ))

        # 识别抑郁
        if primary_emotion == "sad" and emotions.get("sad", 0) > 0.6:
            triggers.append(Trigger(
                tag_id="depression_sign",
                name="抑郁倾向",
                category=TriggerCategory.PSYCHOLOGICAL,
                severity=TriggerSeverity.HIGH,
                confidence=emotions.get("sad", 0),
                metadata={"emotion": primary_emotion, "score": emotions.get("sad")}
            ))

        # 识别负面情绪
        if sentiment == "negative" and sentiment_score < -0.5:
            triggers.append(Trigger(
                tag_id="negative_sentiment",
                name="负面情绪",
                category=TriggerCategory.PSYCHOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=abs(sentiment_score),
                metadata={"sentiment": sentiment, "score": sentiment_score}
            ))

        # 识别危机信号
        if risk_score > 0.5:
            triggers.append(Trigger(
                tag_id="crisis_keyword",
                name="危机关键词",
                category=TriggerCategory.PSYCHOLOGICAL,
                severity=TriggerSeverity.CRITICAL,
                confidence=risk_score,
                metadata={"risk_score": risk_score}
            ))

        # 基于关键词的识别（补充API未能捕获的场景）
        content_lower = content.lower()

        # 识别压力过载
        stress_keywords = ["压力大", "压力特别大", "受不了", "崩溃", "撑不住", "压力山大"]
        if any(kw in content for kw in stress_keywords):
            triggers.append(Trigger(
                tag_id="stress_overload",
                name="压力过载",
                category=TriggerCategory.PSYCHOLOGICAL,
                severity=TriggerSeverity.HIGH,
                confidence=0.8,
                metadata={"detection_method": "keyword", "source": "text"}
            ))

        # 识别工作压力
        work_stress_keywords = ["加班", "工作压力", "职场", "工作太忙", "天天加班"]
        if any(kw in content for kw in work_stress_keywords):
            triggers.append(Trigger(
                tag_id="work_stress",
                name="工作压力",
                category=TriggerCategory.ENVIRONMENTAL,
                severity=TriggerSeverity.MODERATE,
                confidence=0.8,
                metadata={"detection_method": "keyword", "source": "text"}
            ))

        # 识别睡眠质量差
        sleep_keywords = ["没睡好", "睡不好", "失眠", "睡不着", "半夜醒", "晚上也睡不好"]
        if any(kw in content for kw in sleep_keywords):
            triggers.append(Trigger(
                tag_id="poor_sleep",
                name="睡眠质量差",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=0.8,
                metadata={"detection_method": "keyword", "source": "text"}
            ))

        # 识别动机低下
        motivation_keywords = ["什么都不想做", "不想动", "没劲", "没动力", "很疲惫"]
        if any(kw in content for kw in motivation_keywords):
            triggers.append(Trigger(
                tag_id="low_motivation",
                name="动机低下",
                category=TriggerCategory.PSYCHOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=0.8,
                metadata={"detection_method": "keyword", "source": "text"}
            ))

        return triggers

    # ============================================
    # HRV Trigger 识别
    # ============================================

    async def _recognize_hrv_triggers(
        self,
        values: List[float],
        user_id: int
    ) -> List[Trigger]:
        """基于HRV识别生理 Triggers"""
        triggers = []

        # 调用多模态API
        hrv_result = await self.multimodal_client.process_heartrate(
            values, user_id
        )

        if not hrv_result:
            return triggers

        # 提取指标
        hrv_sdnn = hrv_result.get("hrv_sdnn", 0)
        heart_rate = hrv_result.get("heart_rate", 0)
        anomalies = hrv_result.get("anomalies", [])

        # 低HRV
        if hrv_sdnn < 30:
            triggers.append(Trigger(
                tag_id="low_hrv",
                name="低心率变异性",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=1.0,
                metadata={"hrv_sdnn": hrv_sdnn, "threshold": 30}
            ))

        # 心率过高
        if heart_rate > 100:
            triggers.append(Trigger(
                tag_id="high_heartrate",
                name="心率过高",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=1.0,
                metadata={"heart_rate": heart_rate, "threshold": 100}
            ))

        # 心率过低
        if heart_rate < 60 and heart_rate > 0:
            triggers.append(Trigger(
                tag_id="low_heartrate",
                name="心率过低",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=1.0,
                metadata={"heart_rate": heart_rate, "threshold": 60}
            ))

        return triggers

    # ============================================
    # 血糖 Trigger 识别
    # ============================================

    async def _recognize_glucose_triggers(
        self,
        values: List[float],
        user_id: int
    ) -> List[Trigger]:
        """基于血糖识别生理 Triggers"""
        triggers = []

        # 调用多模态API
        glucose_result = await self.multimodal_client.process_glucose(
            values, user_id
        )

        if not glucose_result:
            return triggers

        # 计算统计值
        if not values:
            return triggers

        avg_glucose = sum(values) / len(values)
        max_glucose = max(values)
        min_glucose = min(values)
        variation = max_glucose - min_glucose

        # 高血糖
        if max_glucose > 10.0:
            triggers.append(Trigger(
                tag_id="high_glucose",
                name="高血糖",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.HIGH,
                confidence=1.0,
                metadata={"max_glucose": max_glucose, "threshold": 10.0}
            ))

        # 低血糖
        if min_glucose < 3.9:
            triggers.append(Trigger(
                tag_id="low_glucose",
                name="低血糖",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.CRITICAL,
                confidence=1.0,
                metadata={"min_glucose": min_glucose, "threshold": 3.9}
            ))

        # 血糖波动
        if variation > 3.0:
            triggers.append(Trigger(
                tag_id="glucose_spike",
                name="血糖波动",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=1.0,
                metadata={"variation": variation, "threshold": 3.0}
            ))

        return triggers

    # ============================================
    # 用户画像 Trigger 识别
    # ============================================

    def _recognize_profile_triggers(
        self,
        profile: Dict
    ) -> List[Trigger]:
        """基于用户画像识别行为 Triggers"""
        triggers = []

        # 提取行为状态
        behavior = profile.get("behavior", {})
        adherence_rate = behavior.get("adherence_rate", 100)

        # 低依从性
        if adherence_rate < 50:
            triggers.append(Trigger(
                tag_id="low_adherence",
                name="依从性低",
                category=TriggerCategory.BEHAVIORAL,
                severity=TriggerSeverity.HIGH,
                confidence=1.0,
                metadata={"adherence_rate": adherence_rate, "threshold": 50}
            ))

        return triggers

    # ============================================
    # 工具方法
    # ============================================

    def _deduplicate_triggers(self, triggers: List[Trigger]) -> List[Trigger]:
        """去重 Triggers"""
        seen = set()
        unique_triggers = []

        for trigger in triggers:
            if trigger.tag_id not in seen:
                seen.add(trigger.tag_id)
                unique_triggers.append(trigger)

        return unique_triggers

    def get_trigger_definition(self, tag_id: str) -> Optional[Dict]:
        """获取 Trigger 定义"""
        return self.trigger_dict.get(tag_id)

    def get_all_triggers(self) -> Dict[str, Dict]:
        """获取所有 Trigger 定义"""
        return self.trigger_dict


# ============================================
# 全局单例
# ============================================

_trigger_engine: Optional[TriggerEngine] = None


def get_trigger_engine() -> TriggerEngine:
    """获取 Trigger 引擎单例"""
    global _trigger_engine
    if _trigger_engine is None:
        _trigger_engine = TriggerEngine()
    return _trigger_engine
