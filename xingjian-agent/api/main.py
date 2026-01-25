# -*- coding: utf-8 -*-
"""
行健行为教练 - 综合 API 服务入口
集成说明：
1. 继承原有专家协调 (Orchestrator) 逻辑
2. 注入八爪鱼工作流 (Octopus Workflow) 状态机
3. 预留穿戴设备 (Wearable) 与临床干预接口
"""

import sys
import os
import yaml
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 核心逻辑导入
from core.workflow import OctopusWorkflow
from .session import session_manager
from .schemas import ErrorResponse
# 注意：如果 routes 结构有变化，请确保路径正确
try:
    from .routes import router, init_dependencies
except ImportError:
    router = None

# =============================================================================
# 应用配置加载
# =============================================================================

def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config.yaml"
        )
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# =============================================================================
# 生命周期管理 (Lifespan)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：初始化专家系统与八爪鱼引擎"""
    print("\n" + "=" * 60)
    print("  行健行为教练 [八爪鱼引擎版] 启动中...")
    print("=" * 60)

    # 1. 加载配置
    config = load_config()
    
    # 2. 初始化 Orchestrator (专家团)
    orchestrator = None
    try:
        from agents.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator("config.yaml")
        print(f"[OK] 专家系统加载成功 ({len(orchestrator.registry)} 个触角就绪)")
    except Exception as e:
        print(f"[WARN] 专家系统初始化未完全: {e}")

    # 3. 初始化路由依赖
    if router:
        init_dependencies(orchestrator, config)
        print("[OK] API 路由依赖注入完成")

    # 4. 启动会话清理
    session_manager.start_cleanup_task()
    print("[OK] 会话管理系统启动")
    
    print("-" * 60)
    print("  服务就绪: http://localhost:8000/docs")
    print("-" * 60 + "\n")

    yield  # 运行中

    # 关闭阶段
    session_manager.stop_cleanup_task()
    print("\n[INFO] 服务已安全关闭")

# =============================================================================
# 创建 FastAPI 应用
# =============================================================================

app = FastAPI(
    title="行健行为教练 API",
    description="""
## 八爪鱼行为健康干预系统
集成多专家协作与效能感限幅逻辑。

### 核心路径
- **Audit**: 生理数据与意图识别
- **Constraint**: 动态效能限幅 (Efficacy Clamping)
- **Action**: 原子任务拆解与推送
    """,
    version="1.1.0",
    lifespan=lifespan,
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# 异常处理
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="服务器内部错误",
            detail=str(exc),
            timestamp=datetime.now()
        ).model_dump(mode="json")
    )

# =============================================================================
# 八爪鱼扩展路由 (目标 2 & 目标 3 核心)
# =============================================================================

@app.post("/api/v1/behavioral/process", tags=["Octopus Engine"])
async def process_octopus_logic(
    user_id: str = Query(..., description="用户唯一ID"),
    message: str = Body(..., embed=True),
    wearable_data: Dict[str, Any] = Body(None)
):
    """
    八爪鱼全链路干预接口：
    执行：判断 -> 专家路由 -> 任务分解 -> 效能限幅 -> 生成指令
    """
    # 初始化八爪鱼工作流引擎
    wf = OctopusWorkflow(user_id)
    
    # 模拟从专家系统获取的原始建议（实际应从 orchestrator 获取）
    # 这里先使用 workflow 内部的模拟逻辑验证限幅器
    result = wf.process_request(message, wearable_data=wearable_data)
    
    return result

@app.post("/api/v1/telemetry", tags=["Octopus Engine"])
async def ingest_telemetry(user_id: str, data: Dict[str, Any]):
    """
    目标 3：模拟穿戴设备生理数据上报接口 (心率、步数、睡眠)
    """
    # 此处逻辑未来对接 protocols/wearable.py
    print(f"[Telemetry] 接收到用户 {user_id} 数据: {data}")
    return {
        "status": "recorded",
        "timestamp": datetime.now(),
        "impact": "Efficacy score may be adjusted in next workflow cycle"
    }

# =============================================================================
# 原始路由集成
# =============================================================================

if router:
    app.include_router(router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "行健行为教练 (八爪鱼引擎版)",
        "status": "running",
        "endpoints": {
            "chat": "/api/v1/chat",
            "behavioral_engine": "/api/v1/behavioral/process",
            "docs": "/docs"
        }
    }

# =============================================================================
# 启动程序
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
