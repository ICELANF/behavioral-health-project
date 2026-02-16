"""
综合健康检查端点
Comprehensive Health Check Endpoint

检测所有依赖服务的连通性：
- Database (SQLite/PostgreSQL)
- Redis
- Dify
- Ollama
"""
import os
import time
from datetime import datetime
from typing import Dict, Any

import httpx
from loguru import logger


async def check_database() -> Dict[str, Any]:
    """检查数据库连接"""
    try:
        from core.database import check_database_connection
        ok = check_database_connection()
        return {"status": "ok" if ok else "error"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


async def check_redis() -> Dict[str, Any]:
    """检查 Redis 连接"""
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD", "")
    else:
        redis_host = redis_url
        redis_port = 6379
        redis_password = ""

    try:
        import redis as redis_lib
        if redis_url:
            r = redis_lib.from_url(redis_url, socket_timeout=3)
        else:
            r = redis_lib.Redis(host=redis_host, port=redis_port, password=redis_password, socket_timeout=3)
        r.ping()
        return {"status": "ok", "host": redis_host}
    except ImportError:
        return {"status": "skip", "detail": "redis package not installed"}
    except Exception as e:
        return {"status": "warn", "detail": str(e)}


async def check_ollama() -> Dict[str, Any]:
    """检查 Ollama 连接"""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                model_names = [m["name"] for m in models[:5]]
                return {"status": "ok", "models": model_names}
            return {"status": "warn", "status_code": resp.status_code}
    except Exception as e:
        return {"status": "warn", "detail": str(e)}


async def check_dify() -> Dict[str, Any]:
    """检查 Dify 连接"""
    dify_url = os.getenv("DIFY_API_URL", "http://localhost:8080/v1")
    dify_key = os.getenv("DIFY_API_KEY", "")
    if not dify_key:
        return {"status": "skip", "detail": "DIFY_API_KEY not configured"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {"Authorization": f"Bearer {dify_key}"}
            resp = await client.get(f"{dify_url}/parameters", headers=headers)
            return {"status": "ok" if resp.status_code == 200 else "degraded"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


async def full_health_check() -> Dict[str, Any]:
    """
    综合健康检查

    Returns:
        包含所有服务状态的字典
    """
    start = time.time()

    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "ollama": await check_ollama(),
        "dify": await check_dify(),
    }

    # 计算整体状态 ("skip" 视为正常，不影响总体评估)
    statuses = [v["status"] for v in checks.values()]
    active_statuses = [s for s in statuses if s != "skip"]
    if all(s == "ok" for s in active_statuses):
        overall = "healthy"
    elif any(s == "error" for s in statuses):
        # 如果只有 redis 和 dify 出错，仍可降级运行
        critical_errors = [
            k for k, v in checks.items()
            if v["status"] == "error" and k == "database"
        ]
        overall = "unhealthy" if critical_errors else "degraded"
    else:
        overall = "degraded"

    return {
        "status": overall,
        "version": os.getenv("APP_VERSION", "16.0.0"),
        "timestamp": datetime.now().isoformat(),
        "response_time_ms": round((time.time() - start) * 1000, 1),
        "checks": checks,
    }
