"""
行为健康数字平台 - 决策引擎主入口
Behavioral Health Platform - Decision Engine Main Entry

版本: v14 (融合版)
- v11: Dify深度集成 + Ollama回退 + 患者H5
- v14: + 事件路由 + 节律模型 + Agent增强 + 安全兜底

端口: 8002
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import os
import httpx
import uvicorn
from loguru import logger

from core.decision_core import DecisionCore
from core.decision_models import DecisionContext, BloodGlucoseData

# ============================================
# 环境配置
# ============================================
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")

# ============================================
# [v14-NEW] 加载v14功能配置
# ============================================
try:
    from core.v14 import (
        get_version_info, 
        is_feature_enabled,
        get_agent_enhancer,
        get_trigger_router,
        print_feature_status
    )
    V14_AVAILABLE = True
    version_info = get_version_info()
    logger.info(f"[v14] 模块加载成功, 当前版本: {version_info['version']}")
except ImportError as e:
    V14_AVAILABLE = False
    logger.warning(f"[v14] 模块加载失败，使用v11功能: {e}")

# ============================================
# FastAPI 应用
# ============================================
app = FastAPI(
    title="行为健康数字平台 API",
    version="14.0.0" if V14_AVAILABLE else "11.0.0",
    description="融合v11 + v14功能的行为健康决策引擎"
)

# --- 生产级中间件 (CORS白名单 + 安全头 + 日志 + 限流 + Sentry) ---
from core.middleware import setup_production_middleware
setup_production_middleware(app)

# 初始化决策核心
decision_core = DecisionCore()

# ============================================
# [v11] 尝试挂载设备触发路由
# ============================================
try:
    from api.device_trigger import router as device_router
    app.include_router(device_router, prefix="/api/v1")
    logger.info("[v11] device_trigger 路由已加载")
except ImportError as e:
    logger.warning(f"[v11] device_trigger 路由未加载（缺少依赖）: {e}")

# ============================================
# [v14-NEW] 挂载v14 API路由
# ============================================
if V14_AVAILABLE:
    try:
        from api.v14.routes import router as v14_router
        app.include_router(v14_router, prefix="/api/v2", tags=["v14"])
        logger.info("[v14] v2 API路由已加载")
    except ImportError as e:
        logger.warning(f"[v14] v2 API路由加载失败: {e}")

# ============================================
# 全局状态缓存
# ============================================
latest_health_state = {
    "current_glucose": 0,
    "ai_content": "等待数据接入...",
    "strategy_name": "系统初始化",
    "history": [5.5, 6.0, 5.8],
    "timestamps": ["00:00", "04:00", "08:00"],
}


# ============================================
# 数据模型
# ============================================
class HealthDataInput(BaseModel):
    user_id: int
    user_name: str
    current_glucose: float
    behavioral_tags: List[str] = []


# ============================================
# 基础接口
# ============================================
@app.get("/")
def read_root():
    """根路径 - 状态检查"""
    response = {
        "status": "online", 
        "message": "行为健康决策引擎已就绪",
        "version": "v14" if V14_AVAILABLE else "v11"
    }
    
    if V14_AVAILABLE:
        response["v14_features"] = get_version_info().get("v14_features", {})
    
    return response


@app.get("/health")
def health_check():
    """基础健康检查（快速）"""
    return {
        "status": "healthy",
        "version": "v16" if V14_AVAILABLE else "v11",
        "v14_available": V14_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/health")
async def comprehensive_health():
    """综合健康检查（检测所有依赖）"""
    from core.health import full_health_check
    return await full_health_check()


# ============================================
# [v11] 核心接口（保留原有功能）
# ============================================

@app.post("/intervene")
async def get_intervention(data: HealthDataInput):
    """
    接收数据并生成干预建议
    
    [v14-ENHANCED] 增加事件路由和安全检查
    """
    try:
        # [v14-NEW] 发射CGM事件到路由器
        if V14_AVAILABLE and is_feature_enabled("ENABLE_TRIGGER_EVENT_ROUTING"):
            router = get_trigger_router()
            if router:
                if data.current_glucose < 3.9:
                    router.emit_cgm_low(data.user_id, data.current_glucose)
                elif data.current_glucose > 10.0:
                    router.emit_cgm_high(data.user_id, data.current_glucose)
                # 处理事件
                router.process_pending_events()
        
        # [v11] 原有决策逻辑
        context = DecisionContext(
            user_id=data.user_id,
            user_name=data.user_name,
            current_glucose=BloodGlucoseData(value=data.current_glucose),
            behavioral_tags=data.behavioral_tags,
        )
        result = await decision_core.decide_intervention(context)

        # 更新全局缓存
        global latest_health_state
        latest_health_state["current_glucose"] = data.current_glucose
        latest_health_state["ai_content"] = result["content"]
        latest_health_state["strategy_name"] = result["strategy_name"]

        # 更新历史数据（滚动保持最后 20 条）
        now_str = datetime.now().strftime("%H:%M:%S")
        latest_health_state["history"].append(data.current_glucose)
        latest_health_state["timestamps"].append(now_str)
        if len(latest_health_state["history"]) > 20:
            latest_health_state["history"].pop(0)
            latest_health_state["timestamps"].pop(0)

        # 返回结果附带历史数据
        result["history"] = latest_health_state["history"]
        result["timestamps"] = latest_health_state["timestamps"]
        
        # [v14-NEW] 添加版本标记
        result["version"] = "v14" if V14_AVAILABLE else "v11"

        return result
    except Exception as e:
        logger.error(f"干预生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/latest_status")
async def get_latest():
    """供前端轮询最新状态"""
    return latest_health_state


@app.post("/chat")
async def chat_with_coach(data: dict):
    """AI 教练对话（SSE 流式返回）"""
    user_message = data.get("message")
    user_id = data.get("user_id", "1001")

    async def event_stream():
        try:
            async for chunk in decision_core.dify_client.stream_chat(
                user_input=user_message,
                user_id=str(user_id),
                context_data={"context": "用户正在与健康教练直接对话"},
            ):
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/chat_sync")
async def chat_with_coach_sync(data: dict):
    """
    AI 教练对话（非流式，兼容旧前端）
    
    [v11] 优先调用 Dify，Dify 不可用时自动回退 Ollama 本地模型
    [v14-ENHANCED] 增加安全检查
    """
    user_message = data.get("message")
    user_id = data.get("user_id", "1001")

    # [v14-NEW] 安全检查（SafetyAgent）
    if V14_AVAILABLE:
        enhancer = get_agent_enhancer()
        if enhancer:
            safety_result = enhancer.process(
                user_id=int(user_id) if str(user_id).isdigit() else 1001,
                message=user_message,
                original_response="",
                context={}
            )
            # 如果需要升级到人工
            if safety_result["final_action"] == "escalate":
                return {
                    "reply": safety_result["enhanced_response"],
                    "source": "safety_agent",
                    "escalated": True
                }

    # [v11] 构造健康教练系统提示
    system_prompt = (
        "你是一位专业的行为健康教练，擅长健康管理、饮食指导、运动建议和心理支持。"
        "请用温暖专业的语气回答用户的健康相关问题。回答简洁实用，控制在200字以内。"
        f"当前用户血糖状态：{latest_health_state.get('ai_content', '暂无数据')}"
    )

    # 1. 快速检测 Dify 是否可达（2秒超时）
    dify_available = False
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as probe:
            r = await probe.get(f"{decision_core.dify_client.base_url}/parameters",
                                headers=decision_core.dify_client.headers)
            dify_available = r.status_code == 200
    except Exception:
        pass

    # 2. Dify 可达时优先使用
    if dify_available:
        try:
            response = await decision_core.dify_client.generate_intervention(
                user_input=user_message,
                user_id=str(user_id),
                context_data={"context": "用户正在与健康教练直接对话"},
            )
            answer = response.get("answer", "")
            if answer and answer not in ("未获取到回复内容。", "系统繁忙，请稍后再试。"):
                return {"reply": answer, "source": "dify"}
        except Exception:
            pass

    # 3. 回退 Ollama 本地模型
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            result = resp.json()
            return {"reply": result["message"]["content"], "source": "ollama"}
    except Exception as e:
        return {"reply": f"教练暂时无法响应: {str(e)}", "source": "error"}


# ============================================
# [v16-NEW] 注册 Admin 行为配置路由 + 状态同步
# ============================================
try:
    from api.v14.admin_routes import router as admin_behavior_router
    app.include_router(admin_behavior_router, prefix="/api/v1")
    logger.info("[v16] Admin行为配置路由已加载")
except ImportError as e:
    logger.warning(f"[v16] Admin行为配置路由加载失败: {e}")

# 启动行为引擎配置监控（热重载）
try:
    from services.logic_engine import start_config_watcher
    start_config_watcher(interval=30)
    logger.info("[v16] 行为引擎配置监控已启动")
except ImportError as e:
    logger.warning(f"[v16] 行为引擎未加载: {e}")


# ============================================
# 启动
# ============================================
if __name__ == "__main__":
    # 打印版本信息
    if V14_AVAILABLE:
        print_feature_status()

    uvicorn.run(app, host="0.0.0.0", port=8002)
