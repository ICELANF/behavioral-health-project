"""
F-008: Safety Pipeline Schema — 安全管线 L1-L5 配置定义

Source: 契约注册表 ⑧ 安全管线 Sheet + core/safety/
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class SafetyLayer(str, Enum):
    """安全管线层级"""
    L1_input_filter = "L1"    # 输入过滤 (关键词 + PII + 意图)
    L2_rag_safety = "L2"      # RAG 安全 (证据等级 + 过期)
    L3_generation_guard = "L3"  # 生成守卫 (提示注入 + 领域边界)
    L4_output_filter = "L4"   # 输出过滤 (药物剂量 + 绝对声明 + 免责)
    L5_audit_trace = "L5"     # 审计追踪 (全链路日志 + 复盘)


class SeverityLevel(str, Enum):
    critical = "critical"    # 立即阻断 + 上报
    high = "high"            # 标记待审 + 降级回复
    medium = "medium"        # 添加免责声明
    low = "low"              # 通过


class SafetyAction(str, Enum):
    block_and_escalate = "block_and_escalate"
    flag_for_review = "flag_for_review"
    add_disclaimer = "add_disclaimer"
    downgrade_response = "downgrade_response"
    pass_through = "pass_through"


class SafetyLayerConfig(BaseModel):
    """单层安全配置"""
    layer: SafetyLayer
    enabled: bool = True
    description: str
    checks: List[str]
    severity_mapping: Dict[str, SeverityLevel] = {}
    action_on_trigger: SafetyAction = SafetyAction.flag_for_review


SAFETY_PIPELINE_CONFIG: List[SafetyLayerConfig] = [
    SafetyLayerConfig(
        layer=SafetyLayer.L1_input_filter,
        description="输入过滤: 关键词匹配 + PII检测 + 意图分类",
        checks=["keyword_match", "pii_detection", "intent_classification"],
        severity_mapping={
            "crisis_keyword": SeverityLevel.critical,
            "blocked_keyword": SeverityLevel.high,
            "pii_detected": SeverityLevel.medium,
            "medical_advice_intent": SeverityLevel.medium,
        },
    ),
    SafetyLayerConfig(
        layer=SafetyLayer.L2_rag_safety,
        description="RAG安全: 证据等级加权 + 过期文档过滤",
        checks=["evidence_tier_weight", "document_expiry", "source_reliability"],
        severity_mapping={
            "T4_only_sources": SeverityLevel.high,
            "expired_document": SeverityLevel.medium,
        },
    ),
    SafetyLayerConfig(
        layer=SafetyLayer.L3_generation_guard,
        description="生成守卫: 提示注入检测 + 领域边界约束",
        checks=["prompt_injection", "domain_boundary", "response_length"],
        severity_mapping={
            "prompt_injection": SeverityLevel.critical,
            "out_of_domain": SeverityLevel.high,
        },
    ),
    SafetyLayerConfig(
        layer=SafetyLayer.L4_output_filter,
        description="输出过滤: 药物剂量 + 绝对声明 + 诊断声明 + 免责",
        checks=["drug_dosage", "absolute_claim", "diagnostic_statement", "disclaimer"],
        severity_mapping={
            "drug_dosage_found": SeverityLevel.critical,
            "absolute_claim": SeverityLevel.high,
            "diagnostic_statement": SeverityLevel.high,
        },
        action_on_trigger=SafetyAction.block_and_escalate,
    ),
    SafetyLayerConfig(
        layer=SafetyLayer.L5_audit_trace,
        description="审计追踪: 全链路日志 + 复盘分析",
        checks=["full_trace_log", "decision_replay"],
        action_on_trigger=SafetyAction.pass_through,
    ),
]
