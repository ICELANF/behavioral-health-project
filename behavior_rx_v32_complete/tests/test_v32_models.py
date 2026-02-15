"""
BehaviorOS v32 — 行为处方数据模型 & 迁移测试
================================================
对应 behavior_rx/migrations/031_behavior_rx_foundation.py
     behavior_rx/core/rx_models.py

放置: tests/test_v32_models.py
运行: python -m pytest tests/test_v32_models.py -v -s
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

PASS = lambda tag: print(f"  [PASS] {tag}")


# =====================================================================
# Test 1: ORM 模型结构
# =====================================================================

def test_rx_models():
    """ORM 模型完整性检查"""
    print("\n--- 1. Rx ORM Models ---")

    from behavior_rx.core.rx_models import (
        RxPrescription,
        RxStrategyTemplate,
        AgentHandoffLog,
    )

    # RxPrescription 字段
    rx = RxPrescription
    assert hasattr(rx, "__tablename__")
    PASS(f"RxPrescription table={rx.__tablename__}")

    expected_columns = [
        "rx_id", "user_id", "session_id", "ttm_stage",
        "primary_strategy", "intensity", "communication_style",
        "confidence_score", "created_at",
    ]
    actual_columns = [c.name for c in rx.__table__.columns]
    for col in expected_columns:
        assert col in actual_columns, f"missing column: {col}"
    PASS(f"RxPrescription has {len(actual_columns)} columns, all expected present")

    # RxStrategyTemplate 字段
    tpl = RxStrategyTemplate
    assert hasattr(tpl, "__tablename__")
    tpl_columns = [c.name for c in tpl.__table__.columns]
    assert "strategy_type" in tpl_columns
    assert "applicable_stages" in tpl_columns
    PASS(f"RxStrategyTemplate has {len(tpl_columns)} columns")

    # AgentHandoffLog 字段
    log = AgentHandoffLog
    assert hasattr(log, "__tablename__")
    log_columns = [c.name for c in log.__table__.columns]
    assert "source_agent" in log_columns
    assert "target_agent" in log_columns
    assert "handoff_type" in log_columns
    assert "status" in log_columns
    PASS(f"AgentHandoffLog has {len(log_columns)} columns")


# =====================================================================
# Test 2: 枚举在 ORM 中正确映射
# =====================================================================

def test_model_enums():
    """ORM 枚举映射"""
    print("\n--- 2. Model Enums ---")

    from behavior_rx.core.rx_schemas import (
        RxStrategyType,
        RxIntensity,
        CommunicationStyle,
        ExpertAgentType,
        HandoffType,
        HandoffStatus,
    )

    # 所有枚举值应为字符串
    for strategy in RxStrategyType:
        assert isinstance(strategy.value, str)
    PASS(f"RxStrategyType: {len(RxStrategyType)} values, all str")

    for intensity in RxIntensity:
        assert isinstance(intensity.value, str)
    PASS(f"RxIntensity: {len(RxIntensity)} values")

    for style in CommunicationStyle:
        assert isinstance(style.value, str)
    PASS(f"CommunicationStyle: {len(CommunicationStyle)} values")

    for agent in ExpertAgentType:
        assert isinstance(agent.value, str)
    PASS(f"ExpertAgentType: {len(ExpertAgentType)} values")

    for ht in HandoffType:
        assert isinstance(ht.value, str)
    PASS(f"HandoffType: {len(HandoffType)} values")

    for hs in HandoffStatus:
        assert isinstance(hs.value, str)
    PASS(f"HandoffStatus: {len(HandoffStatus)} values")


# =====================================================================
# Test 3: 迁移脚本结构
# =====================================================================

def test_migration_031():
    """迁移 031 结构验证"""
    print("\n--- 3. Migration 031 ---")

    import importlib
    import os

    # 尝试直接导入
    migration_path = os.path.join(
        os.path.dirname(__file__), "..",
        "behavior_rx", "migrations", "031_behavior_rx_foundation.py",
    )

    if not os.path.exists(migration_path):
        alt_paths = [
            "behavior_rx/migrations/031_behavior_rx_foundation.py",
            "migrations/031_behavior_rx_foundation.py",
        ]
        for p in alt_paths:
            if os.path.exists(p):
                migration_path = p
                break

    assert os.path.exists(migration_path), f"migration file not found"
    PASS("031_behavior_rx_foundation.py exists")

    # 读取并检查关键内容
    with open(migration_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "rx_prescriptions" in content
    PASS("creates rx_prescriptions table")

    assert "rx_strategy_template" in content or "rx_strategy_templates" in content
    PASS("creates rx_strategy_template(s) table")

    assert "agent_handoff_log" in content or "agent_handoff_logs" in content
    PASS("creates agent_handoff_log(s) table")

    assert "def upgrade" in content
    PASS("has upgrade() function")

    assert "def downgrade" in content
    PASS("has downgrade() function")


# =====================================================================
# Test 4: Pydantic DTO 序列化/反序列化
# =====================================================================

def test_dto_serialization():
    """DTO 序列化/反序列化"""
    print("\n--- 4. DTO Serialization ---")

    from behavior_rx.core.rx_schemas import (
        RxContext, BigFiveProfile, RxPrescriptionDTO,
        MicroAction, ExpertAgentType, RxStrategyType,
        RxIntensity, CommunicationStyle,
    )

    # RxContext → dict → RxContext
    ctx = RxContext(
        user_id=uuid.uuid4(),
        ttm_stage=3,
        stage_readiness=0.7,
        personality=BigFiveProfile(O=60, C=55, E=45, A=70, N=40),
        capacity_score=0.6,
        self_efficacy=0.7,
        domain_data={"test": True},
        active_barriers=["time"],
    )
    ctx_dict = ctx.model_dump()
    ctx_restored = RxContext(**ctx_dict)
    assert ctx_restored.ttm_stage == 3
    assert ctx_restored.personality.O == 60
    assert ctx_restored.active_barriers == ["time"]
    PASS("RxContext round-trip ok")

    # BigFiveProfile methods
    bf = BigFiveProfile(O=80, C=60, E=40, A=50, N=30)
    assert bf.dominant_trait() == "O"
    bf_dict = bf.model_dump()
    assert bf_dict["O"] == 80
    PASS("BigFiveProfile methods + serialization ok")

    # MicroAction
    ma = MicroAction(
        action_id="ma-001",
        title="饭后散步",
        description="午饭后步行15分钟",
        difficulty=0.3,
        duration_minutes=15,
        frequency="daily",
        trigger_cue="午饭结束铃声",
        reward_suggestion="记录步数",
    )
    ma_dict = ma.model_dump()
    assert ma_dict["duration_minutes"] == 15
    assert ma_dict["trigger_cue"] == "午饭结束铃声"
    PASS("MicroAction serialization ok")


# =====================================================================
# Test 5: 与现有模块兼容性
# =====================================================================

def test_existing_compatibility():
    """与现有 v31 模块兼容性"""
    print("\n--- 5. Compatibility Check ---")

    # behavior_rx 包可导入
    import behavior_rx
    PASS("behavior_rx package importable")

    # 核心模块
    from behavior_rx.core.rx_schemas import RxContext
    PASS("behavior_rx.core.rx_schemas importable")

    from behavior_rx.core.rx_models import RxPrescription
    PASS("behavior_rx.core.rx_models importable")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    PASS("behavior_rx.core.behavior_rx_engine importable")

    from behavior_rx.core.agent_handoff_service import AgentHandoffService
    PASS("behavior_rx.core.agent_handoff_service importable")

    from behavior_rx.core.agent_collaboration_orchestrator import AgentCollaborationOrchestrator
    PASS("behavior_rx.core.agent_collaboration_orchestrator importable")

    from behavior_rx.core.rx_conflict_resolver import RxConflictResolver
    PASS("behavior_rx.core.rx_conflict_resolver importable")

    # Agent 模块
    from behavior_rx.agents.base_expert_agent import BaseExpertAgent
    PASS("behavior_rx.agents.base_expert_agent importable")

    from behavior_rx.agents.behavior_coach_agent import BehaviorCoachAgent
    PASS("behavior_rx.agents.behavior_coach_agent importable")

    from behavior_rx.agents.metabolic_expert_agent import MetabolicExpertAgent
    PASS("behavior_rx.agents.metabolic_expert_agent importable")

    from behavior_rx.agents.cardiac_expert_agent import CardiacExpertAgent
    PASS("behavior_rx.agents.cardiac_expert_agent importable")

    from behavior_rx.agents.adherence_expert_agent import AdherenceExpertAgent
    PASS("behavior_rx.agents.adherence_expert_agent importable")

    # API 模块
    from behavior_rx.api.rx_routes import router
    PASS("behavior_rx.api.rx_routes importable")

    # Patch 模块
    from behavior_rx.patches.master_agent_integration import setup_expert_agents
    PASS("behavior_rx.patches.master_agent_integration importable")

    # 检查不干扰现有模块 (如果存在)
    try:
        from core.stage_mapping import stage_resolver
        PASS("existing core.stage_mapping still works")
    except ImportError:
        PASS("core.stage_mapping not in scope (ok for isolated test)")

    try:
        from baps.spi_calculator import calculate_spi_full
        PASS("existing baps.spi_calculator still works")
    except ImportError:
        PASS("baps.spi_calculator not in scope (ok for isolated test)")


# =====================================================================
# 运行入口
# =====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
