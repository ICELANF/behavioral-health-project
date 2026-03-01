"""
S4 修复: Agent 健康监控
=================================
检查所有已注册 Agent 的运行态健康

部署: 复制到 api/agent_health.py, 在 main.py 中注册
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
import os

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/agents/health")
async def agent_health_check():
    """检查所有Agent和外部依赖的健康状态"""
    results = {}
    overall = "healthy"

    # 1. 检查 AgentRegistry
    try:
        from api.main import _registry
        if _registry is not None:
            agent_count = _registry.count() if hasattr(_registry, 'count') else 'unknown'
            results["agent_registry"] = {
                "status": "healthy",
                "agent_count": agent_count,
            }
        else:
            results["agent_registry"] = {"status": "not_initialized"}
            overall = "degraded"
    except Exception as e:
        results["agent_registry"] = {"status": "error", "detail": str(e)[:100]}
        overall = "degraded"

    # 2. 检查 Ollama 连通性
    try:
        import httpx
        ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{ollama_url}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                results["ollama"] = {
                    "status": "healthy",
                    "url": ollama_url,
                    "models_available": len(models),
                }
            else:
                results["ollama"] = {"status": "degraded", "http_code": resp.status_code}
                overall = "degraded"
    except Exception as e:
        results["ollama"] = {"status": "unreachable", "detail": str(e)[:100]}
        # Ollama是可选的, 不影响overall
        if overall == "healthy":
            overall = "degraded"

    # 3. 检查 Claude API (仅检查key是否配置)
    try:
        from api.config import DIFY_API_KEY
        has_key = bool(DIFY_API_KEY and len(DIFY_API_KEY) > 10)
        results["claude_api"] = {
            "status": "configured" if has_key else "not_configured",
            "key_present": has_key,
        }
        if not has_key:
            overall = "degraded"
    except Exception:
        results["claude_api"] = {"status": "config_not_found"}

    # 4. 检查 Qdrant
    try:
        import httpx
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{qdrant_url}/collections")
            if resp.status_code == 200:
                collections = resp.json().get("result", {}).get("collections", [])
                results["qdrant"] = {
                    "status": "healthy",
                    "collections": len(collections),
                }
            else:
                results["qdrant"] = {"status": "degraded", "http_code": resp.status_code}
                overall = "degraded"
    except Exception as e:
        results["qdrant"] = {"status": "unreachable", "detail": str(e)[:100]}
        overall = "degraded"

    # 5. 检查 MasterAgent
    try:
        from api.main import _master_agent
        if _master_agent is not None:
            results["master_agent"] = {"status": "healthy", "initialized": True}
        else:
            results["master_agent"] = {"status": "not_initialized"}
    except Exception as e:
        results["master_agent"] = {"status": "error", "detail": str(e)[:100]}

    return JSONResponse(content={
        "overall": overall,
        "checks": results,
        "timestamp": datetime.now().isoformat(),
    })
