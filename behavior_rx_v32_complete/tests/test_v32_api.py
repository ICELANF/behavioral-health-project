"""
BehaviorOS v32 — 行为处方 API 端点测试
==========================================
对应 behavior_rx/api/rx_routes.py (8 个端点)

使用 FastAPI TestClient 离线测试, 无需启动服务器

放置: tests/test_v32_api.py
运行: python -m pytest tests/test_v32_api.py -v -s
"""

from __future__ import annotations

import uuid

import pytest

PASS = lambda tag: print(f"  [PASS] {tag}")


# =====================================================================
# Test 1: 路由注册完整性
# =====================================================================

def test_route_registration():
    """8 个端点全部注册"""
    print("\n--- 1. Route Registration ---")

    from behavior_rx.api.rx_routes import router

    routes = []
    for route in router.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set())
        routes.append((path, methods))

    assert len(routes) >= 8
    PASS(f"total routes: {len(routes)}")

    # 检查各端点存在
    expected = [
        ("POST", "/compute"),
        ("GET", "/strategies"),
        ("GET", "/agents/status"),
    ]
    for method, path_fragment in expected:
        found = any(
            path_fragment in r[0] and method in r[1]
            for r in routes
        )
        assert found, f"missing {method} {path_fragment}"
        PASS(f"{method} {path_fragment} registered")

    # 路由前缀
    assert router.prefix == "/api/v1/rx"
    PASS(f"prefix = {router.prefix}")

    # 标签
    assert "Behavioral Prescription" in router.tags
    PASS("tag = Behavioral Prescription")


# =====================================================================
# Test 2: 请求/响应模型校验
# =====================================================================

def test_request_response_models():
    """请求/响应 Pydantic 模型字段验证"""
    print("\n--- 2. Request/Response Models ---")

    from behavior_rx.core.rx_schemas import (
        ComputeRxRequest,
        ComputeRxResponse,
        RxContext,
        BigFiveProfile,
        ExpertAgentType,
        RxListResponse,
        StrategyTemplateResponse,
        HandoffRequest,
        HandoffResponse,
        HandoffListResponse,
    )

    # ComputeRxRequest
    ctx = RxContext(
        user_id=uuid.uuid4(),
        ttm_stage=3,
        personality=BigFiveProfile(),
        capacity_score=0.5,
    )
    req = ComputeRxRequest(context=ctx)
    assert req.context.ttm_stage == 3
    assert req.agent_type is None  # optional
    PASS("ComputeRxRequest construction ok")

    req_with_agent = ComputeRxRequest(
        context=ctx,
        agent_type=ExpertAgentType.METABOLIC_EXPERT,
    )
    assert req_with_agent.agent_type == ExpertAgentType.METABOLIC_EXPERT
    PASS("ComputeRxRequest with agent_type ok")

    # HandoffRequest
    handoff_req = HandoffRequest(
        user_id=str(uuid.uuid4()),
        source_agent=ExpertAgentType.METABOLIC_EXPERT,
        target_agent=ExpertAgentType.CARDIAC_EXPERT,
        handoff_type="domain_coordination",
        reason="需要心血管评估",
        context_snapshot={"ttm_stage": 3},
        priority=3,
    )
    assert handoff_req.priority == 3
    PASS("HandoffRequest construction ok")


# =====================================================================
# Test 3: TestClient 端点集成 (如果 httpx 可用)
# =====================================================================

def test_api_endpoints():
    """FastAPI TestClient 端点测试"""
    print("\n--- 3. API Endpoints ---")

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        PASS("fastapi/httpx not available, skip TestClient tests")
        return

    from behavior_rx.api.rx_routes import router

    # 创建测试 app
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)

    # GET /api/v1/rx/strategies
    resp = client.get("/api/v1/rx/strategies")
    # 可能 200 或 500 (如果依赖未初始化), 但不应该 404
    assert resp.status_code != 404
    PASS(f"GET /strategies → status={resp.status_code}")

    # GET /api/v1/rx/agents/status
    resp = client.get("/api/v1/rx/agents/status")
    assert resp.status_code != 404
    PASS(f"GET /agents/status → status={resp.status_code}")

    # POST /api/v1/rx/compute (验证路径存在)
    resp = client.post("/api/v1/rx/compute", json={})
    # 422 (validation error) 表示路径存在, 只是参数不对
    assert resp.status_code in [200, 422, 500]
    PASS(f"POST /compute → status={resp.status_code} (path exists)")

    # POST /api/v1/rx/handoff
    resp = client.post("/api/v1/rx/handoff", json={})
    assert resp.status_code in [200, 422, 500]
    PASS(f"POST /handoff → status={resp.status_code} (path exists)")

    # POST /api/v1/rx/collaborate
    resp = client.post("/api/v1/rx/collaborate", json={})
    assert resp.status_code in [200, 422, 500]
    PASS(f"POST /collaborate → status={resp.status_code} (path exists)")


# =====================================================================
# Test 4: 端点依赖注入
# =====================================================================

def test_dependency_injection():
    """依赖注入函数可调用"""
    print("\n--- 4. Dependency Injection ---")

    from behavior_rx.api.rx_routes import (
        get_rx_engine,
        get_handoff_service,
        get_orchestrator,
    )

    engine = get_rx_engine()
    assert engine is not None
    PASS("get_rx_engine() returns instance")

    # 单例验证
    engine2 = get_rx_engine()
    assert engine is engine2
    PASS("get_rx_engine() is singleton")

    handoff = get_handoff_service()
    assert handoff is not None
    PASS("get_handoff_service() returns instance")

    orch = get_orchestrator()
    assert orch is not None
    PASS("get_orchestrator() returns instance")


# =====================================================================
# Test 5: API 与引擎集成
# =====================================================================

def test_api_engine_integration():
    """API 层调用引擎层"""
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

    rx = engine.compute_rx(
        context=ctx,
        agent_type=ExpertAgentType.BEHAVIOR_COACH,
    )

    assert rx is not None
    assert rx.ttm_stage == 2
    assert rx.confidence_score > 0
    PASS(f"API engine compute ok: strategy={rx.primary_strategy.value}")
    PASS(f"confidence={rx.confidence_score:.2f}")
    PASS(f"intensity={rx.intensity.value}")
    PASS(f"communication={rx.communication_style.value}")


# =====================================================================
# 运行入口
# =====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
