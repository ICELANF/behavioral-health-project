"""
BehaviorOS v32 — ORM 模型 & 迁移测试
=====================================
匹配实际字段: id (不是 rx_id), strategy_type (不是 primary_strategy)

运行:
  python -m pytest tests/test_v32_models.py -v -s
"""

import os
import sys
import uuid

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PASS = lambda tag: print(f"  [PASS] {tag}")


# =====================================================================
# 1. ORM Models
# =====================================================================

def test_rx_models():
    print("\n--- 1. Rx ORM Models ---")

    from behavior_rx.core.rx_models import (
        RxPrescription, RxStrategyTemplate, AgentHandoffLog,
    )

    # RxPrescription
    rx = RxPrescription
    assert hasattr(rx, "__tablename__")
    PASS(f"RxPrescription table={rx.__tablename__}")

    # 实际列名: id (不是 rx_id), strategy_type (不是 primary_strategy)
    expected_columns = [
        "id", "user_id", "session_id", "agent_type", "ttm_stage",
        "strategy_type", "intensity", "communication_style",
    ]
    actual_columns = [c.name for c in rx.__table__.columns]
    for col in expected_columns:
        assert col in actual_columns, f"missing column: {col}"
    PASS(f"RxPrescription columns verified: {len(actual_columns)} total")

    # RxStrategyTemplate
    st = RxStrategyTemplate
    assert hasattr(st, "__tablename__")
    st_cols = [c.name for c in st.__table__.columns]
    assert "strategy_type" in st_cols
    assert "evidence_tier" in st_cols
    PASS(f"RxStrategyTemplate table={st.__tablename__}, cols={len(st_cols)}")

    # AgentHandoffLog
    ahl = AgentHandoffLog
    assert hasattr(ahl, "__tablename__")
    ahl_cols = [c.name for c in ahl.__table__.columns]
    assert "from_agent" in ahl_cols
    assert "to_agent" in ahl_cols
    assert "handoff_type" in ahl_cols
    PASS(f"AgentHandoffLog table={ahl.__tablename__}, cols={len(ahl_cols)}")


# =====================================================================
# 2. Enums
# =====================================================================

def test_model_enums():
    print("\n--- 2. Model Enums ---")

    from behavior_rx.core.rx_schemas import (
        RxStrategyType, RxIntensity, CommunicationStyle,
        ExpertAgentType, HandoffType, HandoffStatus,
    )

    assert len(RxStrategyType) == 12
    assert all(isinstance(s.value, str) for s in RxStrategyType)
    PASS("RxStrategyType: 12 values, all str")

    assert len(RxIntensity) == 5;      PASS("RxIntensity: 5 values")
    assert len(CommunicationStyle) == 6; PASS("CommunicationStyle: 6 values")
    assert len(ExpertAgentType) == 4;  PASS("ExpertAgentType: 4 values")
    assert len(HandoffType) == 6;      PASS("HandoffType: 6 values")
    assert len(HandoffStatus) == 6;    PASS("HandoffStatus: 6 values")


# =====================================================================
# 3. Migration 031
# =====================================================================

def test_migration_031():
    print("\n--- 3. Migration 031 ---")

    migration_path = os.path.join(
        ROOT, "behavior_rx", "migrations", "031_behavior_rx_foundation.py"
    )
    assert os.path.exists(migration_path)
    PASS("031_behavior_rx_foundation.py exists")

    with open(migration_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "rx_prescriptions" in content;     PASS("creates rx_prescriptions table")
    assert "rx_strategy_template" in content;  PASS("creates rx_strategy_template(s) table")
    assert "agent_handoff_log" in content;     PASS("creates agent_handoff_log(s) table")
    assert "def upgrade" in content;           PASS("has upgrade() function")
    assert "def downgrade" in content;         PASS("has downgrade() function")


# =====================================================================
# 4. DTO Serialization
# =====================================================================

def test_dto_serialization():
    print("\n--- 4. DTO Serialization ---")

    from behavior_rx.core.rx_schemas import (
        RxContext, BigFiveProfile, RxPrescriptionDTO,
        MicroAction, ExpertAgentType, RxStrategyType,
        RxIntensity, CommunicationStyle,
    )

    # RxContext round-trip
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

    # BigFiveProfile
    bf = BigFiveProfile(O=80, C=60, E=40, A=50, N=30)
    assert bf.dominant_trait() == "O"
    bf_dict = bf.model_dump()
    assert bf_dict["O"] == 80
    PASS("BigFiveProfile methods + serialization ok")

    # MicroAction — 实际字段: action, difficulty, trigger, duration_min, frequency, domain
    ma = MicroAction(
        action="饭后散步15分钟",
        difficulty=0.3,
        trigger="午饭结束",
        duration_min=15,
        frequency="daily",
        domain="metabolic",
    )
    ma_dict = ma.model_dump()
    assert ma_dict["action"] == "饭后散步15分钟"
    assert ma_dict["difficulty"] == 0.3
    ma_restored = MicroAction(**ma_dict)
    assert ma_restored.action == ma.action
    PASS("MicroAction round-trip ok")

    # RxPrescriptionDTO
    rx = RxPrescriptionDTO(
        rx_id=uuid.uuid4(),
        agent_type=ExpertAgentType.BEHAVIOR_COACH,
        goal_behavior="建立每日运动习惯",
        strategy_type=RxStrategyType.HABIT_STACKING,
        intensity=RxIntensity.MODERATE,
        communication_style=CommunicationStyle.EMPATHETIC,
        ttm_stage=3,
        confidence=0.85,
        reasoning="test serialization",
    )
    rx_dict = rx.model_dump()
    rx_restored = RxPrescriptionDTO(**rx_dict)
    assert rx_restored.strategy_type == RxStrategyType.HABIT_STACKING
    assert rx_restored.agent_type == ExpertAgentType.BEHAVIOR_COACH
    assert rx_restored.confidence == 0.85
    PASS("RxPrescriptionDTO round-trip ok")


# =====================================================================
# 5. Compatibility Check
# =====================================================================

def test_existing_compatibility():
    print("\n--- 5. Compatibility Check ---")

    modules = [
        ("behavior_rx", "包根"),
        ("behavior_rx.core.rx_schemas", "Pydantic Schemas"),
        ("behavior_rx.core.rx_models", "ORM 模型"),
        ("behavior_rx.core.behavior_rx_engine", "处方引擎"),
        ("behavior_rx.core.agent_handoff_service", "交接服务"),
        ("behavior_rx.core.agent_collaboration_orchestrator", "协作编排"),
        ("behavior_rx.core.rx_conflict_resolver", "冲突解决"),
        ("behavior_rx.agents.base_expert_agent", "Agent基类"),
        ("behavior_rx.agents.behavior_coach_agent", "行为教练"),
        ("behavior_rx.agents.metabolic_expert_agent", "代谢专家"),
        ("behavior_rx.agents.cardiac_expert_agent", "心血管专家"),
        ("behavior_rx.agents.adherence_expert_agent", "依从性专家"),
        ("behavior_rx.api.rx_routes", "FastAPI路由"),
        ("behavior_rx.patches.master_agent_integration", "MasterAgent集成"),
    ]

    for mod, desc in modules:
        try:
            __import__(mod)
            PASS(f"{mod} importable")
        except ImportError as e:
            pytest.fail(f"import {mod} failed: {e}")

    # 检查现有模块兼容性(如果存在)
    try:
        import core.stage_mapping
        PASS("existing core.stage_mapping still works")
    except ImportError:
        PASS("core.stage_mapping not present (ok in isolation)")

    try:
        import baps.spi_calculator
        PASS("existing baps.spi_calculator still works")
    except ImportError:
        PASS("baps.spi_calculator not present (ok in isolation)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
