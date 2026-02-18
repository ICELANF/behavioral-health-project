"""
飞轮API路由注册
将5个飞轮模块的router挂载到FastAPI主应用

使用方式 (在 main.py 或 app_factory.py 中):
    from api.flywheel_routes import register_flywheel_routes
    register_flywheel_routes(app)
"""

from fastapi import FastAPI


def register_flywheel_routes(app: FastAPI) -> None:
    """
    注册全部飞轮API路由

    端点统计:
      Observer:  3 端点  /api/v1/observer/*  + /api/v1/assessment/*
      Grower:    5 端点  /api/v1/daily-tasks/* + /api/v1/user/* + /api/v1/coach-tip/* + /api/v1/weekly-summary
      Coach:     4 端点  /api/v1/coach/*
      Expert:    4 端点  /api/v1/expert/*
      Admin:    12 端点  /api/v1/admin/*
      ─────────────────
      合计:     28 端点
    """
    from api.observer_flywheel_api import router as observer_router
    from api.grower_flywheel_api import router as grower_router
    from api.coach_flywheel_api import router as coach_router
    from api.expert_flywheel_api import router as expert_router
    from api.admin_flywheel_api import router as admin_router

    app.include_router(observer_router)
    app.include_router(grower_router)
    app.include_router(coach_router)
    app.include_router(expert_router)
    app.include_router(admin_router)


# ═══════════════════════════════════════════════════
# 独立启动 (开发调试用)
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn

    app = FastAPI(
        title="BHP V5.0 飞轮API",
        version="5.0.0",
        description="行健平台飞轮效应API — 5角色×28端点",
        docs_url="/docs",
    )

    register_flywheel_routes(app)

    # 健康检查
    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "version": "5.0.0",
            "flywheel_endpoints": 28,
            "roles": ["observer", "grower", "coach", "expert", "admin"],
        }

    # CORS (开发环境)
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uvicorn.run(app, host="0.0.0.0", port=8010)
