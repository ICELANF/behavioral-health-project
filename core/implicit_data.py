"""
隐式数据采集与分析服务
来源: §12 六种隐式数据源 + §16.1 Gap #11

6种隐式数据源:
  1. CONV     — 对话内容分析 (chat_messages)
  2. TASK     — 任务执行表现 (user_tasks)
  3. DEVICE   — 可穿戴设备数据 (health_data)
  4. TRIGGER  — 触发事件历史 (trigger_records)
  5. INTERACT — 交互行为模式 (user_activity)
  6. PROFILE  — 用户画像提取 (user_profile)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime, timedelta


# ── 数据源定义 ──

class ImplicitSource(str, Enum):
    CONV = "conv"           # 对话内容分析
    TASK = "task"           # 任务执行表现
    DEVICE = "device"       # 可穿戴设备数据
    TRIGGER = "trigger"     # 触发事件历史
    INTERACT = "interact"   # 交互行为模式
    PROFILE = "profile"     # 用户画像提取


@dataclass
class ImplicitSourceConfig:
    source_id: ImplicitSource
    db_table: str
    update_frequency: str      # "realtime" | "daily" | "on_detection"
    collection_window_days: int
    fields: list[str]


# §12 表格定义
SOURCE_CONFIGS: dict[ImplicitSource, ImplicitSourceConfig] = {
    ImplicitSource.CONV: ImplicitSourceConfig(
        source_id=ImplicitSource.CONV,
        db_table="chat_messages",
        update_frequency="realtime",
        collection_window_days=14,
        fields=["text", "sentiment", "intent", "keywords", "emotion_score"],
    ),
    ImplicitSource.TASK: ImplicitSourceConfig(
        source_id=ImplicitSource.TASK,
        db_table="user_tasks",
        update_frequency="daily",
        collection_window_days=30,
        fields=["completion_rate", "streak_days", "skip_count", "avg_completion_time"],
    ),
    ImplicitSource.DEVICE: ImplicitSourceConfig(
        source_id=ImplicitSource.DEVICE,
        db_table="health_data",
        update_frequency="realtime",
        collection_window_days=7,
        fields=["cgm_value", "hrv_sdnn", "steps", "sleep_hours"],
    ),
    ImplicitSource.TRIGGER: ImplicitSourceConfig(
        source_id=ImplicitSource.TRIGGER,
        db_table="trigger_records",
        update_frequency="realtime",
        collection_window_days=30,
        fields=["trigger_id", "trigger_count", "risk_level"],
    ),
    ImplicitSource.INTERACT: ImplicitSourceConfig(
        source_id=ImplicitSource.INTERACT,
        db_table="user_activity",
        update_frequency="daily",
        collection_window_days=14,
        fields=["daily_active_time", "message_count", "response_latency"],
    ),
    ImplicitSource.PROFILE: ImplicitSourceConfig(
        source_id=ImplicitSource.PROFILE,
        db_table="user_profile",
        update_frequency="on_detection",
        collection_window_days=90,
        fields=["stated_goals", "value_keywords", "identity_expressions"],
    ),
}


# ── 隐式数据提取器 ──

@dataclass
class ImplicitDataPoint:
    source: ImplicitSource
    user_id: int
    field_name: str
    value: Any
    confidence: float          # 0.0-1.0
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    method: str = ""           # 提取方法名


class ImplicitDataExtractor:
    """
    从6种数据源提取隐式数据, 用于免问卷画像更新
    """

    # ── CONV: 对话分析 ──

    # 阻抗信号 → L1-L2
    RESISTANCE_PATTERNS = ["不想", "不行", "做不到", "别管我", "没用的", "懒得"]
    # 矛盾信号 → L2-L3
    AMBIVALENCE_PATTERNS = ["也许", "可能", "但是", "一方面", "另一方面", "不确定"]
    # 接受信号 → L3
    ACCEPTANCE_PATTERNS = ["试试看", "先做一点", "可以接受", "愿意尝试"]
    # 价值关键词 → 动因识别
    VALUE_KEYWORDS = ["健康", "家人", "家庭", "自由", "生活质量", "有意义", "重要"]
    # 身份表达 → 内化信号 L4-L5
    IDENTITY_PATTERNS = ["我想成为", "我希望是", "我要做一个", "更好的自己"]

    def extract_from_conversation(self, user_id: int,
                                   messages: list[str]) -> list[ImplicitDataPoint]:
        """从对话内容提取隐式数据"""
        results = []
        full_text = " ".join(messages)

        # 情感/意图提取
        sentiment = self._analyze_sentiment(full_text)
        results.append(ImplicitDataPoint(
            source=ImplicitSource.CONV, user_id=user_id,
            field_name="sentiment", value=sentiment,
            confidence=0.7, method="keyword_sentiment",
        ))

        # 阻抗检测
        resistance_count = sum(1 for p in self.RESISTANCE_PATTERNS if p in full_text)
        if resistance_count > 0:
            results.append(ImplicitDataPoint(
                source=ImplicitSource.CONV, user_id=user_id,
                field_name="resistance_signal", value=resistance_count,
                confidence=0.65, method="pattern_match",
            ))

        # 矛盾检测
        ambivalence_count = sum(1 for p in self.AMBIVALENCE_PATTERNS if p in full_text)
        if ambivalence_count > 0:
            results.append(ImplicitDataPoint(
                source=ImplicitSource.CONV, user_id=user_id,
                field_name="ambivalence_signal", value=ambivalence_count,
                confidence=0.60, method="pattern_match",
            ))

        # 接受信号
        acceptance_count = sum(1 for p in self.ACCEPTANCE_PATTERNS if p in full_text)
        if acceptance_count > 0:
            results.append(ImplicitDataPoint(
                source=ImplicitSource.CONV, user_id=user_id,
                field_name="acceptance_signal", value=acceptance_count,
                confidence=0.65, method="pattern_match",
            ))

        # 价值关键词
        value_hits = [kw for kw in self.VALUE_KEYWORDS if kw in full_text]
        if value_hits:
            results.append(ImplicitDataPoint(
                source=ImplicitSource.CONV, user_id=user_id,
                field_name="value_keywords", value=value_hits,
                confidence=0.65, method="keyword_extraction",
            ))

        # 身份表达
        identity_hits = [p for p in self.IDENTITY_PATTERNS if p in full_text]
        if identity_hits:
            results.append(ImplicitDataPoint(
                source=ImplicitSource.CONV, user_id=user_id,
                field_name="identity_expressions", value=identity_hits,
                confidence=0.60, method="identity_detection",
            ))

        return results

    # ── TASK: 任务执行分析 ──

    def extract_from_tasks(self, user_id: int,
                            task_records: list[dict]) -> list[ImplicitDataPoint]:
        """从任务执行数据推断行为阶段"""
        results = []
        if not task_records:
            return results

        total = len(task_records)
        completed = sum(1 for t in task_records if t.get("completed"))
        completion_rate = completed / total if total > 0 else 0

        results.append(ImplicitDataPoint(
            source=ImplicitSource.TASK, user_id=user_id,
            field_name="completion_rate", value=round(completion_rate, 3),
            confidence=0.85, method="task_stats",
        ))

        # 连续天数
        streak = self._calc_streak(task_records)
        results.append(ImplicitDataPoint(
            source=ImplicitSource.TASK, user_id=user_id,
            field_name="streak_days", value=streak,
            confidence=0.9, method="streak_calculation",
        ))

        # 跳过次数
        skip_count = sum(1 for t in task_records if t.get("status") == "skipped")
        results.append(ImplicitDataPoint(
            source=ImplicitSource.TASK, user_id=user_id,
            field_name="skip_count", value=skip_count,
            confidence=0.9, method="skip_counting",
        ))

        # 行为阶段推断
        inferred_stage = self._infer_stage_from_tasks(completion_rate, streak)
        results.append(ImplicitDataPoint(
            source=ImplicitSource.TASK, user_id=user_id,
            field_name="inferred_stage", value=inferred_stage,
            confidence=0.70, method="task_stage_inference",
        ))

        return results

    # ── DEVICE: 设备数据分析 ──

    def extract_from_device(self, user_id: int,
                             device_data: dict) -> list[ImplicitDataPoint]:
        """从可穿戴设备数据提取健康指标"""
        results = []
        for field_name in ["cgm_value", "hrv_sdnn", "steps", "sleep_hours"]:
            value = device_data.get(field_name)
            if value is not None:
                results.append(ImplicitDataPoint(
                    source=ImplicitSource.DEVICE, user_id=user_id,
                    field_name=field_name, value=value,
                    confidence=0.90, method="device_sync",
                ))
        return results

    # ── INTERACT: 交互行为分析 ──

    def extract_from_interaction(self, user_id: int,
                                  activity: dict) -> list[ImplicitDataPoint]:
        """从交互行为推断用户参与度"""
        results = []
        active_time = activity.get("daily_active_time", 0)
        msg_count = activity.get("message_count", 0)

        results.append(ImplicitDataPoint(
            source=ImplicitSource.INTERACT, user_id=user_id,
            field_name="engagement_level",
            value="high" if active_time > 30 else ("medium" if active_time > 10 else "low"),
            confidence=0.80, method="engagement_scoring",
        ))
        results.append(ImplicitDataPoint(
            source=ImplicitSource.INTERACT, user_id=user_id,
            field_name="message_count", value=msg_count,
            confidence=0.90, method="activity_counting",
        ))
        return results

    # ── 隐式心理层级推断 ──

    def infer_psychological_level(self,
                                   conv_data: list[ImplicitDataPoint],
                                   task_data: list[ImplicitDataPoint]) -> dict:
        """
        综合多源数据推断心理准备度层级 (L1-L5)
        confidence_threshold: 0.70 — 低于此值需要显式问卷确认
        """
        signals = {}
        for dp in conv_data + task_data:
            signals[dp.field_name] = dp.value

        resistance = signals.get("resistance_signal", 0)
        ambivalence = signals.get("ambivalence_signal", 0)
        acceptance = signals.get("acceptance_signal", 0)
        completion_rate = signals.get("completion_rate", 0)
        streak = signals.get("streak_days", 0)

        # 推断逻辑
        if resistance >= 3:
            level, confidence = "L1", 0.75
        elif ambivalence >= 2 and resistance >= 1:
            level, confidence = "L2", 0.65
        elif acceptance >= 1 and completion_rate < 0.6:
            level, confidence = "L3", 0.60
        elif completion_rate >= 0.6 and streak >= 3:
            level, confidence = "L4", 0.70
        elif completion_rate >= 0.85 and streak >= 30:
            level, confidence = "L5", 0.75
        else:
            level, confidence = "L2", 0.50  # 默认

        return {
            "inferred_level": level,
            "confidence": confidence,
            "verification_required": confidence < 0.70,
            "signals_used": list(signals.keys()),
        }

    # ── 辅助方法 ──

    def _analyze_sentiment(self, text: str) -> str:
        neg_kw = ["不想", "烦", "累", "讨厌", "焦虑", "压力", "痛苦"]
        pos_kw = ["开心", "进步", "坚持", "完成", "好", "不错", "感谢"]
        neg = sum(1 for kw in neg_kw if kw in text)
        pos = sum(1 for kw in pos_kw if kw in text)
        if neg > pos + 1:
            return "negative"
        elif pos > neg + 1:
            return "positive"
        return "neutral"

    def _calc_streak(self, records: list[dict]) -> int:
        completed_dates = sorted(set(
            r["date"] for r in records if r.get("completed") and r.get("date")
        ), reverse=True)
        if not completed_dates:
            return 0
        streak = 1
        for i in range(1, len(completed_dates)):
            if (completed_dates[i - 1] - completed_dates[i]).days == 1:
                streak += 1
            else:
                break
        return streak

    def _infer_stage_from_tasks(self, rate: float, streak: int) -> str:
        if rate < 0.1:
            return "S0"
        elif rate < 0.3:
            return "S1"
        elif rate < 0.5:
            return "S2"
        elif rate < 0.7 and streak < 7:
            return "S3"
        elif rate >= 0.7 and streak >= 7:
            return "S4"
        elif rate >= 0.85 and streak >= 30:
            return "S5"
        return "S2"


# 单例
implicit_data_extractor = ImplicitDataExtractor()
