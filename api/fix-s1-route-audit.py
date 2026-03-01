"""
S1 修复: main.py 路由注册审计
=================================
注入到 main.py 启动流程中:
1. 记录每个路由模块注册成功/失败
2. 暴露 GET /api/v1/system/routes 端点
3. 暴露 GET /api/v1/system/health 端点

部署: 复制到 api/route_audit.py, 在 main.py 末尾 import
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

logger = logging.getLogger("route_audit")

# 全局注册表
_route_registry = {
    "registered": [],
    "failed": [],
    "startup_time": None,
}

router = APIRouter(prefix="/api/v1/system", tags=["system"])


def record_success(module_name: str, endpoint_count: int = 0):
    """记录成功注册的路由模块"""
    _route_registry["registered"].append({
        "module": module_name,
        "endpoints": endpoint_count,
        "time": datetime.now().isoformat(),
    })


def record_failure(module_name: str, error: str):
    """记录失败的路由模块"""
    _route_registry["failed"].append({
        "module": module_name,
        "error": str(error)[:200],
        "time": datetime.now().isoformat(),
    })
    logger.error(f"[ROUTE FAIL] {module_name}: {error}")


def audit_startup(app):
    """
    在 app 启动后扫描所有已注册路由, 生成审计报告
    在 main.py 的 app 创建之后调用: audit_startup(app)
    """
    _route_registry["startup_time"] = datetime.now().isoformat()

    # 扫描 app 上所有路由
    all_routes = []
    for route in app.routes:
        if hasattr(route, "methods"):
            for method in route.methods:
                all_routes.append({
                    "method": method,
                    "path": route.path,
                    "name": route.name or "",
                })

    _route_registry["total_routes"] = len(all_routes)
    _route_registry["all_routes"] = all_routes

    # 打印启动摘要
    ok = len(_route_registry["registered"])
    fail = len(_route_registry["failed"])
    total = _route_registry["total_routes"]

    print(f"\n{'='*60}")
    print(f"[ROUTE AUDIT] Startup Complete")
    print(f"  Modules OK:     {ok}")
    print(f"  Modules FAILED: {fail}")
    print(f"  Total Routes:   {total}")

    if _route_registry["failed"]:
        print(f"\n  FAILED MODULES:")
        for f in _route_registry["failed"]:
            print(f"    ✗ {f['module']}: {f['error'][:80]}")

    print(f"{'='*60}\n")


@router.get("/routes")
async def get_routes():
    """返回所有已注册路由的审计信息"""
    return JSONResponse(content={
        "startup_time": _route_registry.get("startup_time"),
        "modules_ok": len(_route_registry["registered"]),
        "modules_failed": len(_route_registry["failed"]),
        "total_routes": _route_registry.get("total_routes", 0),
        "registered": _route_registry["registered"],
        "failed": _route_registry["failed"],
    })


@router.get("/health")
async def system_health():
    """系统综合健康检查"""
    checks = {}

    # 1. 数据库
    try:
        from core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)[:100]}"

    # 2. Redis
    try:
        import redis
        import os
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)[:100]}"

    # 3. 路由模块
    failed = len(_route_registry.get("failed", []))
    checks["route_modules"] = "healthy" if failed == 0 else f"degraded: {failed} modules failed"

    # 总体状态
    all_healthy = all("healthy" in str(v) for v in checks.values())

    return JSONResponse(content={
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "total_routes": _route_registry.get("total_routes", 0),
        "failed_modules": _route_registry.get("failed", []),
        "timestamp": datetime.now().isoformat(),
    })


@router.get("/routes/frontend-contract")
async def frontend_contract_check(request: Request):
    """
    前后端契约校验:
    检查前端定义的所有端点是否在后端存在
    """
    # 前端定义的所有端点 (从8个API模块提取)
    frontend_endpoints = [
        # auth.ts
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/register"),
        ("POST", "/api/v1/auth/wechat/miniprogram"),
        ("GET",  "/api/v1/auth/me"),
        ("POST", "/api/v1/auth/logout"),
        ("POST", "/api/v1/auth/refresh"),
        # coach.ts
        ("GET",  "/api/v1/coach/dashboard"),
        ("GET",  "/api/v1/coach/students"),
        ("GET",  "/api/v1/coach/push-queue"),
        ("POST", "/api/v1/coach/push-queue/{id}/approve"),
        ("POST", "/api/v1/coach/push-queue/{id}/reject"),
        ("GET",  "/api/v1/coach/assessments"),
        ("POST", "/api/v1/coach/assessments/{id}/review"),
        ("GET",  "/api/v1/coach/performance"),
        # assessment.ts
        ("GET",  "/api/v1/assessment-assignments/my"),
        ("POST", "/api/v1/assessment-assignments/{id}/submit"),
        ("GET",  "/api/v1/assessment-assignments/{id}/result"),
        # companion.ts
        ("GET",  "/api/v1/companions"),
        ("POST", "/api/v1/companions/invite"),
        ("GET",  "/api/v1/companions/invitations"),
        ("POST", "/api/v1/companions/invitations/{id}/accept"),
        ("POST", "/api/v1/companions/invitations/{id}/reject"),
        # exam.ts
        ("GET",  "/api/v1/exams"),
        ("POST", "/api/v1/exams/{examId}/start"),
        ("POST", "/api/v1/exam-sessions/{sessionId}/answer"),
        ("POST", "/api/v1/exam-sessions/{sessionId}/finish"),
        ("GET",  "/api/v1/exam-sessions/my"),
        # journey.ts
        ("GET",  "/api/v1/journey/overview"),
        ("GET",  "/api/v1/journey/progress"),
        ("POST", "/api/v1/journey/promotion/apply"),
        ("GET",  "/api/v1/journey/promotion/history"),
        # learning.ts
        ("GET",  "/api/v1/content/courses"),
        ("GET",  "/api/v1/content/recommended"),
        ("GET",  "/api/v1/learning/my"),
        ("GET",  "/api/v1/learning/credits"),
        # profile.ts
        ("GET",  "/api/v1/profile"),
        ("PUT",  "/api/v1/profile"),
        ("GET",  "/api/v1/profile/certifications"),
        ("GET",  "/api/v1/profile/leaderboard"),
        ("POST", "/api/v1/profile/change-password"),
        ("GET",  "/api/v1/profile/settings"),
        ("PUT",  "/api/v1/profile/settings"),
    ]

    # 获取后端所有路由
    backend_paths = set()
    for route in request.app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods:
                # 标准化路径: 去掉path参数的名字差异
                import re
                normalized = re.sub(r'\{[^}]+\}', '{id}', route.path)
                backend_paths.add((method, normalized))

    # 对比
    matched = []
    missing = []
    for method, path in frontend_endpoints:
        normalized = path.replace("{examId}", "{id}").replace("{sessionId}", "{id}").replace("{contentId}", "{id}")
        import re
        normalized = re.sub(r'\{[^}]+\}', '{id}', normalized)
        found = (method, normalized) in backend_paths
        entry = {"method": method, "path": path, "status": "LIVE" if found else "MISSING"}
        if found:
            matched.append(entry)
        else:
            missing.append(entry)

    return JSONResponse(content={
        "total_frontend_endpoints": len(frontend_endpoints),
        "matched": len(matched),
        "missing": len(missing),
        "coverage": f"{len(matched)*100//len(frontend_endpoints)}%",
        "missing_endpoints": missing,
        "matched_endpoints": matched,
    })
