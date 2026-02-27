"""
AgentMeta — Agent 元数据描述

每个注册到 AgentRegistry 的 Agent 都必须附带一份 AgentMeta,
描述其身份、能力、约束, 供 Router / Coordinator / Admin 查询。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class AgentTier(str, Enum):
    """Agent 层级"""
    SAFETY = "safety"           # 安全层: CrisisAgent
    SPECIALIST = "specialist"   # 专科: 9 个领域 Agent
    INTEGRATIVE = "integrative" # 整合: BehaviorRx, Weight, Cardiac, TrustGuide
    USER = "user"               # 用户层: 健康助手, 习惯追踪, 引导
    EXPERT = "expert"           # 动态专家: XZB, BehaviorRx experts


@dataclass(frozen=True)
class AgentMeta:
    """
    Agent 元数据 — 不可变, 注册时定义

    Attributes:
        domain:       唯一领域标识 (注册 key)
        display_name: 中文显示名称
        tier:         Agent 层级
        priority:     路由优先级 (0=最高)
        keywords:     路由关键词列表
        data_fields:  关注的设备数据字段
        evidence_tier: 循证等级 T1/T2/T3/T4
        base_weight:  协调权重 (0-1)
        enable_llm:   是否启用 LLM 增强
        description:  功能描述
        dependencies: 依赖的其他 Agent domain 列表
        version:      Agent 版本
    """
    domain: str
    display_name: str = ""
    tier: AgentTier = AgentTier.SPECIALIST
    priority: int = 5
    keywords: tuple[str, ...] = ()
    data_fields: tuple[str, ...] = ()
    evidence_tier: str = "T3"
    base_weight: float = 0.8
    enable_llm: bool = True
    description: str = ""
    dependencies: tuple[str, ...] = ()
    version: str = "1.0.0"

    def __post_init__(self):
        if not self.domain:
            raise ValueError("AgentMeta.domain 不能为空")
