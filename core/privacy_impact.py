# -*- coding: utf-8 -*-
"""
privacy_impact.py — 隐私影响评估 (PIA / DPIA) 框架

实现《个人信息保护法》和 GDPR 要求的隐私影响评估流程:
  - PIA (Privacy Impact Assessment) — 个保法要求
  - DPIA (Data Protection Impact Assessment) — GDPR 要求
  - privacy_impact 评分模型
  - data_protection_impact 合规检查清单

每个新功能上线前必须通过 PIA 评估。
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PIALevel(Enum):
    """PIA 评估等级 (隐私评估分级)"""
    LOW = "low"           # 低风险 — 无需额外措施
    MODERATE = "moderate"  # 中风险 — 需数据最小化
    HIGH = "high"         # 高风险 — 需加密+审批
    CRITICAL = "critical"  # 极高风险 — 需 DPIA + DPO 审批


@dataclass
class PIACheckItem:
    """PIA 检查项"""
    item_id: str
    category: str        # data_collection / data_processing / data_sharing / data_retention
    description: str
    privacy_impact_score: float  # 0-10, 影响程度
    mitigation: str      # 缓解措施
    compliant: bool = False


@dataclass
class PIAAssessment:
    """隐私影响评估报告 (PIA Report)"""
    assessment_id: str
    feature_name: str
    assessor: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    data_types_involved: List[str] = field(default_factory=list)
    check_items: List[PIACheckItem] = field(default_factory=list)
    overall_level: PIALevel = PIALevel.LOW
    dpia_required: bool = False
    approved: bool = False
    approval_notes: str = ""

    @property
    def privacy_impact_total(self) -> float:
        if not self.check_items:
            return 0
        return sum(c.privacy_impact_score for c in self.check_items) / len(self.check_items)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "feature_name": self.feature_name,
            "assessor": self.assessor,
            "data_types": self.data_types_involved,
            "overall_level": self.overall_level.value,
            "privacy_impact_score": round(self.privacy_impact_total, 2),
            "dpia_required": self.dpia_required,
            "items_count": len(self.check_items),
            "compliant_count": sum(1 for c in self.check_items if c.compliant),
            "approved": self.approved,
        }


# ══════════════════════════════════════════════════════════════
# PIA 标准检查清单 (data_protection_impact checklist)
# ══════════════════════════════════════════════════════════════

PIA_STANDARD_CHECKS = [
    PIACheckItem("PIA-01", "data_collection", "是否收集最小必要个人信息", 3.0, "数据最小化原则"),
    PIACheckItem("PIA-02", "data_collection", "是否告知用户数据收集目的", 4.0, "隐私声明+知情同意"),
    PIACheckItem("PIA-03", "data_processing", "健康数据是否加密处理", 8.0, "AES-256加密+字段级加密"),
    PIACheckItem("PIA-04", "data_processing", "AI模型是否处理敏感信息", 7.0, "数据脱敏+匿名化"),
    PIACheckItem("PIA-05", "data_sharing", "是否与第三方共享数据", 6.0, "数据处理协议(DPA)"),
    PIACheckItem("PIA-06", "data_sharing", "跨境数据传输是否合规", 8.0, "SCC条款+本地化部署"),
    PIACheckItem("PIA-07", "data_retention", "数据保存期限是否明确", 4.0, "保存期限策略+自动清理"),
    PIACheckItem("PIA-08", "data_retention", "用户注销后数据是否删除", 5.0, "DSAR响应机制"),
]


def run_privacy_impact_assessment(
    feature_name: str,
    assessor: str,
    data_types: List[str],
    involves_health_data: bool = True,
    involves_cross_border: bool = False,
) -> PIAAssessment:
    """执行隐私影响评估 (PIA)

    根据《个保法》第55条，处理敏感个人信息前应当进行个人信息保护影响评估。
    """
    import uuid
    assessment = PIAAssessment(
        assessment_id=f"PIA-{uuid.uuid4().hex[:8]}",
        feature_name=feature_name,
        assessor=assessor,
        data_types_involved=data_types,
        check_items=list(PIA_STANDARD_CHECKS),
    )

    # 根据数据类型确定风险等级
    if involves_health_data and involves_cross_border:
        assessment.overall_level = PIALevel.CRITICAL
        assessment.dpia_required = True
    elif involves_health_data:
        assessment.overall_level = PIALevel.HIGH
        assessment.dpia_required = True
    elif involves_cross_border:
        assessment.overall_level = PIALevel.MODERATE
    else:
        assessment.overall_level = PIALevel.LOW

    logger.info("PIA completed: feature=%s, level=%s, dpia_required=%s",
                feature_name, assessment.overall_level.value, assessment.dpia_required)
    return assessment


def check_dpia_required(data_types: List[str]) -> bool:
    """检查是否需要 DPIA (Data Protection Impact Assessment)"""
    sensitive_types = {"health_data", "biometric", "genetic", "mental_health", "medication"}
    return bool(set(data_types) & sensitive_types)
