"""
F-006: Risk Levels Schema — R0-R4 风险等级定义 + 设备告警阈值

Source: 契约注册表 ⑧ 安全管线 Sheet + configs/alert_thresholds.json
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    R0 = "R0"  # 正常
    R1 = "R1"  # 轻度 — 记录 + 提示
    R2 = "R2"  # 中度 — 通知教练 + 增强监测
    R3 = "R3"  # 高度 — 强制教练介入 + 限制Agent自主
    R4 = "R4"  # 危机 — CrisisAgent接管 + 紧急联系人 + 24h响应


class EscalationAction(str, Enum):
    log_only = "log_only"
    notify_user = "notify_user"
    notify_coach = "notify_coach"
    force_coach = "force_coach"
    crisis_takeover = "crisis_takeover"
    emergency_contact = "emergency_contact"


class RiskLevelDefinition(BaseModel):
    """风险等级完整定义"""
    level: RiskLevel
    label_zh: str
    response_time_hours: Optional[int] = None
    actions: List[EscalationAction]
    agent_autonomy: str  # full / limited / supervised / none
    coach_required: bool = False
    supervisor_notify: bool = False


RISK_DEFINITIONS: List[RiskLevelDefinition] = [
    RiskLevelDefinition(
        level=RiskLevel.R0, label_zh="正常",
        actions=[EscalationAction.log_only],
        agent_autonomy="full",
    ),
    RiskLevelDefinition(
        level=RiskLevel.R1, label_zh="轻度风险",
        response_time_hours=24,
        actions=[EscalationAction.log_only, EscalationAction.notify_user],
        agent_autonomy="full",
    ),
    RiskLevelDefinition(
        level=RiskLevel.R2, label_zh="中度风险",
        response_time_hours=4,
        actions=[EscalationAction.notify_user, EscalationAction.notify_coach],
        agent_autonomy="limited", coach_required=True,
    ),
    RiskLevelDefinition(
        level=RiskLevel.R3, label_zh="高度风险",
        response_time_hours=1,
        actions=[EscalationAction.force_coach, EscalationAction.notify_coach],
        agent_autonomy="supervised", coach_required=True, supervisor_notify=True,
    ),
    RiskLevelDefinition(
        level=RiskLevel.R4, label_zh="危机",
        response_time_hours=1,
        actions=[EscalationAction.crisis_takeover, EscalationAction.emergency_contact],
        agent_autonomy="none", coach_required=True, supervisor_notify=True,
    ),
]


class DeviceThreshold(BaseModel):
    """设备告警阈值"""
    data_type: str
    metric: str
    unit: str
    r1_range: Optional[str] = None
    r2_range: Optional[str] = None
    r3_range: Optional[str] = None
    r4_range: Optional[str] = None


DEVICE_THRESHOLDS: List[DeviceThreshold] = [
    DeviceThreshold(
        data_type="glucose", metric="血糖", unit="mmol/L",
        r1_range="7.0-10.0 或 3.5-3.9",
        r2_range="10.1-13.9 或 3.0-3.4",
        r3_range="14.0-16.6 或 2.5-2.9",
        r4_range=">16.7 或 <2.5",
    ),
    DeviceThreshold(
        data_type="heart_rate", metric="心率", unit="bpm",
        r1_range="100-110 或 50-55",
        r2_range="111-130 或 45-49",
        r3_range="131-150 或 40-44",
        r4_range=">150 或 <40",
    ),
    DeviceThreshold(
        data_type="blood_pressure_sys", metric="收缩压", unit="mmHg",
        r1_range="140-159 或 90-99",
        r2_range="160-179 或 80-89",
        r3_range="180-199 或 70-79",
        r4_range=">=200 或 <70",
    ),
    DeviceThreshold(
        data_type="blood_pressure_dia", metric="舒张压", unit="mmHg",
        r1_range="90-99",
        r2_range="100-109",
        r3_range="110-119",
        r4_range=">=120",
    ),
    DeviceThreshold(
        data_type="spo2", metric="血氧", unit="%",
        r1_range="93-95",
        r2_range="90-92",
        r3_range="85-89",
        r4_range="<85",
    ),
]
