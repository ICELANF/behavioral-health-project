"""
BehaviorOS v32 — API 端点测试
==============================
ComputeRxRequest 需要 agent_type 字段
RxPrescriptionDTO 字段: confidence (不是 confidence_score)

运行:
  python -m pytest tests/test_v32_api.py -v -s
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
# 1. Route Registration
# =====================================================================

def test_route_registration():
    print("\n--- 1. Route Registration ---")

    from behavior_rx.api.rx_routes import router

    routes = list(router.routes)
    assert len(routes) >= 8
    PASS(f"total routes: {len(routes)}")

    paths = [r.path for r in routes if hasattr(r, "path")]
    methods_map = {}
    for r in routes:
        if hasattr(r, "path") and hasattr(r, "methods"):
            for m in r.methods:
                methods_map[f"{m} {r.path}"] = True

    assert any("/compute" in p for p in paths)
    PASS("POST /compute registered")

    assert any("/strategies" in p for p in paths)
    PASS("GET /strategies registered")

    assert any("/agents/status" in p for p in paths)
    PASS("GET /agents/status registered")

    assert router.prefix == "/api/v1/rx" or any("/api/v1/rx" in str(getattr(r, "path", "")) for r in routes)
    PASS(f"prefix = {router.prefix}")

    assert "Behavioral Prescription" in (router.tags or [])
    PASS("tag = Behavioral Prescription")


# =====================================================================
# 2. Request/Response Models
# =====================================================================

def test_request_response_models():
    print("\n--- 2. Request/Response Models ---")

    from behavior_rx.core.rx_schemas import (
        ComputeRxRequest, ComputeRxResponse,
        RxContext, BigFiveProfile, ExpertAgentType,
        RxListResponse, StrategyTemplateResponse,
        HandoffRequest, HandoffResponse, HandoffListResponse,
    )

    # ComputeRxRequest — 需要 context + agent_type
    ctx = RxContext(
        user_id=uuid.uuid4(),
        ttm_stage=3,
        personality=BigFiveProfile(),
        capacity_score=0.5,
    )
    req = ComputeRxRequest(context=ctx, agent_type=ExpertAgentType.BEHAVIOR_COACH)
    assert req.context.ttm_stage == 3
    assert req.agent_type == ExpertAgentType.BEHAVIOR_COACH
    PASS("ComputeRxRequest construction ok")

    # ComputeRxResponse
    assert hasattr(ComputeRxResponse, "model_fields")
    assert "prescription" in ComputeRxResponse.model_fields
    PASS("ComputeRxResponse has 'prescription' field")

    # HandoffRequest
    assert "from_agent" in HandoffRequest.model_fields
    assert "to_agent" in HandoffRequest.model_fields
    assert "handoff_type" in HandoffRequest.model_fields
    PASS("HandoffRequest fields verified")

    # HandoffResponse
    assert "handoff_id" in HandoffResponse.model_fields
    assert "status" in HandoffResponse.model_fields
    PASS("HandoffResponse fields verified")

    # List responses
    assert "items" in RxListResponse.model_fields
    assert "total" in RxListResponse.model_fields
    PASS("RxListResponse fields verified")

    assert "items" in HandoffListResponse.model_fields
    PASS("HandoffListResponse fields verified")


# =====================================================================
# 3. API Endpoints (TestClient)
# =====================================================================

def test_api_endpoints():
    print("\n--- 3. API Endpoints ---")

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("fastapi/httpx not installed")

    from behavior_rx.api.rx_routes import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)

    # GET /strategies — may need query params
    r = client.get("/api/v1/rx/strategies")
    assert r.status_code in [200, 422]
    PASS(f"GET /strategies → status={r.status_code}")

    # GET /agents/status
    r2 = client.get("/api/v1/rx/agents/status")
    assert r2.status_code == 200
    PASS(f"GET /agents/status → status={r2.status_code}")

    # POST /compute — no body → 422
    r3 = client.post("/api/v1/rx/compute")
    assert r3.status_code in [422, 500]
    PASS(f"POST /compute → status={r3.status_code} (path exists)")

    # POST /handoff
    r4 = client.post("/api/v1/rx/handoff")
    assert r4.status_code in [422, 500]
    PASS(f"POST /handoff → status={r4.status_code} (path exists)")

    # POST /collaborate
    r5 = client.post("/api/v1/rx/collaborate")
    assert r5.status_code in [422, 500]
    PASS(f"POST /collaborate → status={r5.status_code} (path exists)")


# =====================================================================
# 4. Dependency Injection
# =====================================================================

def test_dependency_injection():
    print("\n--- 4. Dependency Injection ---")

    from behavior_rx.api.rx_routes import get_rx_engine, get_handoff_service, get_orchestrator

    e1 = get_rx_engine()
    assert e1 is not None
    PASS("get_rx_engine() returns instance")

    e2 = get_rx_engine()
    assert e1 is e2
    PASS("get_rx_engine() is singleton")

    hs = get_handoff_service()
    assert hs is not None
    PASS("get_handoff_service() returns instance")

    orch = get_orchestrator()
    assert orch is not None
    PASS("get_orchestrator() returns instance")


# =====================================================================
# 5. API-Engine Integration
# =====================================================================

def test_api_engine_integration():
    print("\n--- 5. API-Engine Integration ---")

    from behavior_rx.api.rx_routes import get_rx_engine
    from behavior_rx.core.rx_schemas import (
        RxContext, BigFiveProfile, ExpertAgentType,
    )

    engine = get_rx_engine()

    ctx = RxContext(
        user_id=uuid.uuid4(),
        ttm_stage=2,
        stage_readiness=0.5,
        personality=BigFiveProfile(O=65, C=70, E=50, A=55, N=35),
        capacity_score=0.6,
    )

    rx = engine.compute_rx(context=ctx, agent_type=ExpertAgentType.BEHAVIOR_COACH)

    assert rx is not None
    assert rx.ttm_stage == 2
    # 实际字段: confidence (不是 confidence_score)
    assert rx.confidence > 0
    PASS(f"engine compute ok: confidence={rx.confidence:.2f}")

    assert rx.agent_type == ExpertAgentType.BEHAVIOR_COACH
    PASS("agent_type matches")

    assert rx.strategy_type is not None
    PASS(f"strategy_type={rx.strategy_type.value}")

    assert rx.communication_style is not None
    PASS(f"communication_style={rx.communication_style.value}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
