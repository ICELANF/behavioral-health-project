"""
F-005: Assessment Batches Schema — 12批次渐进式评估配置

Source: 契约注册表 ⑦ 采集测评 Sheet
B1-B2 强制, B3-B12 自适应触发
26+ 数据源 × 5量表171题 × 5交付通道
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class BatchTrigger(str, Enum):
    """批次触发方式"""
    mandatory = "mandatory"      # 必填 (B1-B2)
    stage_driven = "stage_driven"  # 阶段驱动
    time_driven = "time_driven"  # 时间驱动
    event_driven = "event_driven"  # 事件驱动
    adaptive = "adaptive"        # 自适应


class DeliveryChannel(str, Enum):
    """交付通道"""
    h5_form = "h5_form"          # H5 表单
    agent_dialog = "agent_dialog"  # Agent 对话嵌入
    device_push = "device_push"  # 设备推送
    coach_assign = "coach_assign"  # 教练推送
    micro_action = "micro_action"  # 微行动嵌入


class AssessmentBatch(BaseModel):
    """评估批次定义"""
    batch_id: str = Field(..., pattern=r"^B\d{1,2}$")
    label_zh: str
    trigger: BatchTrigger
    stage_range: Optional[str] = None  # "s0-s1", "s2-s3", etc.
    day_range: Optional[str] = None    # "1-7", "8-30", etc.
    scales: List[str] = []
    question_count: int = 0
    delivery_channels: List[DeliveryChannel] = []
    validity_days: int = 180
    adaptive_skip: bool = False  # True = skip if data already collected


ASSESSMENT_BATCHES: List[AssessmentBatch] = [
    AssessmentBatch(
        batch_id="B1", label_zh="注册基线",
        trigger=BatchTrigger.mandatory, stage_range="s0",
        scales=["TTM7", "PHQ2"], question_count=23,
        delivery_channels=[DeliveryChannel.h5_form],
        validity_days=365,
    ),
    AssessmentBatch(
        batch_id="B2", label_zh="首周深度",
        trigger=BatchTrigger.mandatory, day_range="1-7",
        scales=["BAPS_CORE", "PHQ9", "GAD7"], question_count=45,
        delivery_channels=[DeliveryChannel.h5_form, DeliveryChannel.agent_dialog],
        validity_days=180,
    ),
    AssessmentBatch(
        batch_id="B3", label_zh="设备基线",
        trigger=BatchTrigger.event_driven, stage_range="s0-s1",
        scales=["DEVICE_BASELINE"], question_count=12,
        delivery_channels=[DeliveryChannel.device_push],
        adaptive_skip=True, validity_days=90,
    ),
    AssessmentBatch(
        batch_id="B4", label_zh="行为链画像",
        trigger=BatchTrigger.stage_driven, stage_range="s1",
        scales=["BEHAVIOR_CHAIN"], question_count=18,
        delivery_channels=[DeliveryChannel.agent_dialog, DeliveryChannel.micro_action],
        validity_days=120,
    ),
    AssessmentBatch(
        batch_id="B5", label_zh="动机评估",
        trigger=BatchTrigger.stage_driven, stage_range="s1-s2",
        scales=["MOTIVATION", "SELF_EFFICACY"], question_count=20,
        delivery_channels=[DeliveryChannel.h5_form],
        validity_days=90,
    ),
    AssessmentBatch(
        batch_id="B6", label_zh="月度复评",
        trigger=BatchTrigger.time_driven, day_range="30-60",
        scales=["TTM7", "PHQ9"], question_count=30,
        delivery_channels=[DeliveryChannel.h5_form, DeliveryChannel.coach_assign],
        adaptive_skip=True, validity_days=60,
    ),
    AssessmentBatch(
        batch_id="B7", label_zh="行为改变评估",
        trigger=BatchTrigger.stage_driven, stage_range="s2-s3",
        scales=["BEHAVIOR_CHANGE", "COMB"], question_count=25,
        delivery_channels=[DeliveryChannel.agent_dialog],
        validity_days=90,
    ),
    AssessmentBatch(
        batch_id="B8", label_zh="认知重构评估",
        trigger=BatchTrigger.adaptive, stage_range="s2-s3",
        scales=["COGNITIVE_RESTRUCTURE"], question_count=15,
        delivery_channels=[DeliveryChannel.agent_dialog],
        adaptive_skip=True, validity_days=60,
    ),
    AssessmentBatch(
        batch_id="B9", label_zh="季度综合评估",
        trigger=BatchTrigger.time_driven, day_range="90-120",
        scales=["BAPS_CORE", "PHQ9", "GAD7", "SELF_EFFICACY"], question_count=50,
        delivery_channels=[DeliveryChannel.h5_form, DeliveryChannel.coach_assign],
        validity_days=90,
    ),
    AssessmentBatch(
        batch_id="B10", label_zh="身份转化评估",
        trigger=BatchTrigger.stage_driven, stage_range="s3-s4",
        scales=["IDENTITY_SHIFT"], question_count=12,
        delivery_channels=[DeliveryChannel.agent_dialog],
        validity_days=120,
    ),
    AssessmentBatch(
        batch_id="B11", label_zh="内化稳定评估",
        trigger=BatchTrigger.stage_driven, stage_range="s4",
        scales=["INTERNALIZATION", "RELAPSE_RISK"], question_count=18,
        delivery_channels=[DeliveryChannel.agent_dialog, DeliveryChannel.coach_assign],
        validity_days=90,
    ),
    AssessmentBatch(
        batch_id="B12", label_zh="毕业评估",
        trigger=BatchTrigger.stage_driven, stage_range="s5",
        scales=["GRADUATION", "BAPS_CORE", "PHQ9"], question_count=35,
        delivery_channels=[DeliveryChannel.h5_form],
        validity_days=365,
    ),
]
