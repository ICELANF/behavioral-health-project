"""
F-003: Point Events Schema — 积分事件定义

Source: 契约注册表 ⑤ 积分体系 Sheet + configs/point_events.json
三类积分: growth(成长) + contribution(贡献) + influence(影响力)
V4.0新增: awareness(觉察) + governance(治理)
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PointCategory(str, Enum):
    growth = "growth"              # 成长积分
    contribution = "contribution"  # 贡献积分
    influence = "influence"        # 影响力积分
    awareness = "awareness"        # V4.0 觉察积分
    governance = "governance"      # V4.0 治理积分


class AntiCheatStrategy(str, Enum):
    """六种防刷策略 (AS-01 ~ AS-06)"""
    AS01_daily_cap = "AS01"            # 日上限封顶
    AS02_quality_weight = "AS02"       # 质量加权 (高质量×1.5, 低质量×0.3)
    AS03_time_decay = "AS03"           # 时间衰减 (重复行为递减)
    AS04_cross_validation = "AS04"     # 交叉验证 (设备+行为+反馈三角)
    AS05_growth_track = "AS05"         # 成长轨验证 (纯积分不算真成长)
    AS06_anomaly_detection = "AS06"    # 异常检测 (统计偏离告警)


class PointEventDefinition(BaseModel):
    """积分事件完整定义"""
    event_code: str = Field(..., pattern=r"^[A-Z_]+$")
    label_zh: str
    category: PointCategory
    base_points: int
    daily_cap: Optional[int] = None  # AS-01
    quality_multiplier: bool = False  # AS-02
    time_decay: bool = False          # AS-03
    cross_validation: bool = False    # AS-04
    min_role: str = "observer"


# ── V4.0 Awareness Point Events ─────────────
AWARENESS_EVENTS = [
    PointEventDefinition(
        event_code="REFLECTION_JOURNAL", label_zh="反思日记",
        category=PointCategory.awareness, base_points=5, daily_cap=3,
    ),
    PointEventDefinition(
        event_code="PATTERN_RECOGNITION", label_zh="模式识别",
        category=PointCategory.awareness, base_points=8, daily_cap=2,
        quality_multiplier=True,
    ),
    PointEventDefinition(
        event_code="INSIGHT_SHARE", label_zh="洞察分享",
        category=PointCategory.awareness, base_points=10, daily_cap=2,
        quality_multiplier=True, cross_validation=True,
    ),
    PointEventDefinition(
        event_code="EMOTION_NAMING", label_zh="情绪命名",
        category=PointCategory.awareness, base_points=3, daily_cap=5,
    ),
    PointEventDefinition(
        event_code="BEHAVIOR_OBSERVATION", label_zh="行为观察",
        category=PointCategory.awareness, base_points=5, daily_cap=3,
    ),
    PointEventDefinition(
        event_code="IDENTITY_REFLECTION", label_zh="身份反思",
        category=PointCategory.awareness, base_points=15, daily_cap=1,
        quality_multiplier=True,
    ),
]

# ── V4.0 Governance Point Events ─────────────
GOVERNANCE_EVENTS = [
    PointEventDefinition(
        event_code="GOV_ETHICS_COMPLIANCE", label_zh="伦理合规",
        category=PointCategory.governance, base_points=20,
        min_role="coach",
    ),
    PointEventDefinition(
        event_code="GOV_CREDENTIAL_VERIFY", label_zh="资质验证",
        category=PointCategory.governance, base_points=15,
        min_role="coach",
    ),
    PointEventDefinition(
        event_code="GOV_ALERT_RESPONSE", label_zh="告警响应",
        category=PointCategory.governance, base_points=10,
        min_role="coach", time_decay=True,
    ),
    PointEventDefinition(
        event_code="GOV_SUPERVISION_SESSION", label_zh="督导会话",
        category=PointCategory.governance, base_points=25,
        min_role="promoter",
    ),
    PointEventDefinition(
        event_code="GOV_KNOWLEDGE_SHARE", label_zh="知识贡献",
        category=PointCategory.governance, base_points=12,
        min_role="sharer", quality_multiplier=True,
    ),
]

# ── P1 行为联动积分事件 ─────────────
BEHAVIOR_LINKAGE_EVENTS = [
    PointEventDefinition(
        event_code="ASSESSMENT_SUBMIT", label_zh="完成评估提交",
        category=PointCategory.growth, base_points=5, daily_cap=3,
    ),
    PointEventDefinition(
        event_code="MICRO_ACTION_COMPLETE", label_zh="完成微行动任务",
        category=PointCategory.growth, base_points=3, daily_cap=10,
    ),
    PointEventDefinition(
        event_code="CHALLENGE_CHECKIN", label_zh="挑战每日打卡",
        category=PointCategory.growth, base_points=3, daily_cap=5,
    ),
    PointEventDefinition(
        event_code="CHALLENGE_COMPLETE", label_zh="完成整个挑战",
        category=PointCategory.growth, base_points=10, daily_cap=1,
    ),
    PointEventDefinition(
        event_code="REFLECTION_CREATE", label_zh="创建反思日志",
        category=PointCategory.awareness, base_points=5, daily_cap=3,
    ),
    PointEventDefinition(
        event_code="CONTRACT_SIGN", label_zh="签署契约",
        category=PointCategory.growth, base_points=5, daily_cap=1,
    ),
    PointEventDefinition(
        event_code="COMPANION_ADD", label_zh="建立同伴关系",
        category=PointCategory.contribution, base_points=3, daily_cap=3,
    ),
    PointEventDefinition(
        event_code="CONTRIBUTION_SUBMIT", label_zh="提交知识贡献",
        category=PointCategory.contribution, base_points=5, daily_cap=3,
    ),
    PointEventDefinition(
        event_code="FOOD_RECOGNIZE", label_zh="食物识别使用",
        category=PointCategory.growth, base_points=2, daily_cap=5,
    ),
    PointEventDefinition(
        event_code="PEER_ACCEPT", label_zh="接受同伴匹配",
        category=PointCategory.contribution, base_points=3, daily_cap=3,
    ),
]
