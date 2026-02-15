"""
健康检查路由
路径前缀: /api/v3
"""
import time
import os
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas import APIResponse
from api.dependencies import get_qdrant_store, get_llm_router
from core.rag.vector_store import QdrantStore
from core.llm.router import LLMRouter

router = APIRouter(tags=["系统"])

_START_TIME = time.time()


@router.get("/health", summary="健康检查")
def health_check():
    """轻量健康检查 (不查外部依赖)"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(time.time() - _START_TIME),
    }


@router.get("/api/v3/status", response_model=APIResponse, summary="系统状态 (含依赖检查)")
def system_status(
    db: Session = Depends(get_db),
    store: QdrantStore = Depends(get_qdrant_store),
    router_inst: LLMRouter = Depends(get_llm_router),
):
    """
    完整系统状态:
    - 数据库连接
    - Qdrant 向量库
    - LLM 路由统计
    - 环境变量检查
    """
    checks = {}

    # DB
    try:
        db.execute("SELECT 1" if hasattr(db, "execute") else None)
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}

    # Qdrant
    try:
        info = store.collection_info()
        checks["qdrant"] = {"status": "ok", "points": info.get("points_count", 0)}
    except Exception as e:
        checks["qdrant"] = {"status": "error", "detail": str(e)}

    # LLM API Keys
    dashscope_key = bool(os.environ.get("DASHSCOPE_API_KEY"))
    deepseek_key = bool(os.environ.get("DEEPSEEK_API_KEY"))
    checks["llm_keys"] = {
        "dashscope": "configured" if dashscope_key else "missing",
        "deepseek": "configured" if deepseek_key else "missing",
    }

    # Router stats
    checks["llm_router"] = router_inst.get_stats()

    all_ok = all(
        c.get("status") == "ok"
        for c in [checks.get("database", {}), checks.get("qdrant", {})]
    )

    return APIResponse(
        ok=all_ok,
        data={
            "uptime_seconds": int(time.time() - _START_TIME),
            "checks": checks,
            "version": "3.1.0",
        },
        message="all systems operational" if all_ok else "degraded",
    )
