"""
行为健康数字平台 - v14 API 路由
v14 API Routes

[v14-NEW] 新增API端点

路由前缀: /api/v2/
（独立于v11的 /api/v1/）

使用方式：
    # 在main.py中
    from api.v14.routes import router as v14_router
    app.include_router(v14_router, prefix="/api/v2")
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


router = APIRouter(tags=["v14"])

# ============================================
# [v14-NEW] 导入质量审计路由
# ============================================
try:
    from api.v14.quality_routes import router as quality_router
    QUALITY_ROUTES_AVAILABLE = True
except ImportError:
    QUALITY_ROUTES_AVAILABLE = False
    logger.warning("[v14] 质量审计路由未加载")

# ============================================
# [v14-NEW] 导入披露控制路由
# ============================================
try:
    from api.v14.disclosure_routes import router as disclosure_router
    DISCLOSURE_ROUTES_AVAILABLE = True
except ImportError:
    DISCLOSURE_ROUTES_AVAILABLE = False
    logger.warning("[v14] 披露控制路由未加载")


# ============================================
# 请求/响应模型
# ============================================

class TriggerEventRequest(BaseModel):
    """触发事件请求"""
    user_id: int
    event_type: str  # CGM, TASK, USAGE, EMOTION, RHYTHM
    event_name: str
    event_value: Dict[str, Any] = {}
    level: str = "info"  # info, warn, risk, critical
    source: str = "api"


class RhythmProcessRequest(BaseModel):
    """节律处理请求"""
    user_id: int
    domain: str  # cgm, task, activity
    data: List[float] = []
    hours: int = 24


class AgentProcessRequest(BaseModel):
    """Agent处理请求"""
    user_id: int
    message: str
    original_response: str = ""
    context: Dict[str, Any] = {}


# ============================================
# 版本与状态
# ============================================

@router.get("/status")
async def get_v14_status():
    """获取v14版本状态"""
    from core.v14 import get_version_info, check_dependencies
    
    info = get_version_info()
    issues = check_dependencies()
    
    return {
        "status": "ok",
        "version": info["version"],
        "base_version": info.get("base_version", "v11"),
        "v11_features": info["v11_features"],
        "v14_features": info["v14_features"],
        "dependency_issues": issues,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def v14_health_check():
    """v14健康检查"""
    from core.v14 import (
        is_feature_enabled, 
        get_rhythm_engine, 
        get_trigger_router,
        get_agent_enhancer
    )
    
    modules = {
        "config": True,
        "rhythm_engine": get_rhythm_engine() is not None if is_feature_enabled("ENABLE_RHYTHM_MODEL") else "disabled",
        "trigger_router": get_trigger_router() is not None if is_feature_enabled("ENABLE_TRIGGER_EVENT_ROUTING") else "disabled",
        "agent_enhancer": get_agent_enhancer() is not None if is_feature_enabled("ENABLE_V14_AGENTS") or is_feature_enabled("ENABLE_SAFETY_AGENT") else "disabled"
    }
    
    return {
        "status": "healthy",
        "modules": modules,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/features")
async def get_features():
    """获取功能开关状态"""
    from core.v14 import get_active_features
    
    return {
        "active_features": get_active_features(),
        "timestamp": datetime.now().isoformat()
    }


# ============================================
# Trigger 事件路由
# ============================================

@router.post("/trigger/emit")
async def emit_trigger_event(request: TriggerEventRequest):
    """
    发射触发事件
    
    需要启用: ENABLE_TRIGGER_EVENT_ROUTING
    """
    from core.v14 import is_feature_enabled, get_trigger_router, TriggerEventType, TriggerLevel
    
    if not is_feature_enabled("ENABLE_TRIGGER_EVENT_ROUTING"):
        raise HTTPException(status_code=501, detail="Trigger事件路由未启用")
    
    router_instance = get_trigger_router()
    if not router_instance:
        raise HTTPException(status_code=503, detail="Trigger路由器初始化失败")
    
    try:
        event_type = TriggerEventType(request.event_type)
        level = TriggerLevel(request.level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的事件类型或等级: {e}")
    
    event = router_instance.emit_event(
        user_id=request.user_id,
        event_type=event_type,
        event_name=request.event_name,
        event_value=request.event_value,
        level=level,
        source=request.source
    )
    
    if not event:
        raise HTTPException(status_code=500, detail="事件创建失败")
    
    return {
        "success": True,
        "event": event.to_dict()
    }


@router.post("/trigger/process")
async def process_trigger_events():
    """
    处理所有待处理的触发事件
    
    需要启用: ENABLE_TRIGGER_EVENT_ROUTING
    """
    from core.v14 import is_feature_enabled, get_trigger_router
    
    if not is_feature_enabled("ENABLE_TRIGGER_EVENT_ROUTING"):
        raise HTTPException(status_code=501, detail="Trigger事件路由未启用")
    
    router_instance = get_trigger_router()
    if not router_instance:
        raise HTTPException(status_code=503, detail="Trigger路由器初始化失败")
    
    results = router_instance.process_pending_events()
    
    return {
        "success": True,
        "processed_count": len(results),
        "results": results
    }


@router.get("/trigger/stats")
async def get_trigger_stats():
    """获取Trigger统计信息"""
    from core.v14 import is_feature_enabled, get_trigger_router
    
    if not is_feature_enabled("ENABLE_TRIGGER_EVENT_ROUTING"):
        return {"status": "disabled"}
    
    router_instance = get_trigger_router()
    if not router_instance:
        return {"status": "error", "message": "路由器未初始化"}
    
    return {
        "status": "ok",
        "stats": router_instance.get_event_stats()
    }


# ============================================
# 节律模型
# ============================================

@router.post("/rhythm/detect")
async def detect_rhythm(request: RhythmProcessRequest):
    """
    检测用户节律
    
    需要启用: ENABLE_RHYTHM_MODEL
    """
    from core.v14 import is_feature_enabled, get_rhythm_engine, RhythmDomain
    
    if not is_feature_enabled("ENABLE_RHYTHM_MODEL"):
        raise HTTPException(status_code=501, detail="节律模型未启用")
    
    engine = get_rhythm_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="节律引擎初始化失败")
    
    try:
        domain = RhythmDomain(request.domain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的节律域: {request.domain}")
    
    # 根据域类型调用不同方法
    if domain == RhythmDomain.CGM:
        signal = engine.detect_cgm_rhythm(request.user_id, request.data, request.hours)
    elif domain == RhythmDomain.TASK:
        # data应该是布尔值列表，这里转换
        task_results = [bool(v) for v in request.data]
        signal = engine.detect_task_rhythm(request.user_id, task_results, request.hours // 24)
    elif domain == RhythmDomain.ACTIVITY:
        signal = engine.detect_activity_rhythm(request.user_id, request.hours)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的节律域: {domain}")
    
    # 应用策略
    policy_result = engine.apply_policy(signal)
    
    return {
        "success": True,
        "signal": signal.to_dict(),
        "policy": policy_result
    }


@router.get("/rhythm/current/{user_id}")
async def get_current_rhythm(user_id: int):
    """获取用户当前节律状态"""
    from core.v14 import is_feature_enabled, get_rhythm_engine
    
    if not is_feature_enabled("ENABLE_RHYTHM_MODEL"):
        return {"status": "disabled"}
    
    engine = get_rhythm_engine()
    if not engine:
        return {"status": "error", "message": "引擎未初始化"}
    
    phase = engine.get_current_phase(user_id)
    history = engine.get_user_history(user_id, limit=10)
    
    return {
        "user_id": user_id,
        "current_phase": phase.value if phase else "unknown",
        "history": [s.to_dict() for s in history]
    }


# ============================================
# Agent 增强
# ============================================

@router.post("/agent/process")
async def process_with_agents(request: AgentProcessRequest):
    """
    使用v14 Agent处理消息
    
    SafetyAgent始终启用，其他Agent根据配置
    """
    from core.v14 import is_feature_enabled, get_agent_enhancer
    
    enhancer = get_agent_enhancer()
    
    if not enhancer:
        # 即使Agent未启用，也返回原始响应
        return {
            "success": True,
            "enhanced": False,
            "response": request.original_response,
            "reason": "agent_disabled"
        }
    
    result = enhancer.process(
        user_id=request.user_id,
        message=request.message,
        original_response=request.original_response,
        context=request.context
    )
    
    return {
        "success": True,
        "enhanced": result["modified"],
        "response": result["enhanced_response"],
        "action": result["final_action"],
        "agent_outputs": result["agent_outputs"]
    }


@router.post("/agent/safety-check")
async def safety_check(user_id: int, message: str):
    """
    安全检查（SafetyAgent独立接口）
    
    此接口始终可用（SafetyAgent始终启用）
    """
    from core.v14.agents import SafetyAgent
    
    agent = SafetyAgent()
    output = agent.process(user_id, message, {})
    
    return {
        "user_id": user_id,
        "is_safe": output.action.value != "escalate",
        "action": output.action.value,
        "confidence": output.confidence,
        "metadata": output.metadata
    }


# ============================================
# 整合接口
# ============================================

@router.post("/integrated/process")
async def integrated_process(
    user_id: int,
    message: str,
    glucose_value: Optional[float] = None,
    context: Dict[str, Any] = {}
):
    """
    整合处理接口
    
    自动调用：
    1. TriggerEngine（v11）识别血糖触发
    2. TriggerRouter（v14）事件路由
    3. RhythmEngine（v14）节律检测
    4. AgentEnhancer（v14）安全检查
    5. DecisionCore（v11）生成响应
    """
    from core.v14 import (
        is_feature_enabled,
        get_trigger_router,
        get_rhythm_engine,
        get_agent_enhancer
    )
    
    result = {
        "user_id": user_id,
        "message": message,
        "v11_processing": {},
        "v14_processing": {},
        "final_response": ""
    }
    
    # 1. v11: TriggerEngine 血糖识别
    if glucose_value is not None:
        from core.trigger_engine import get_trigger_engine
        trigger_engine = get_trigger_engine()
        triggers = trigger_engine.recognize_glucose_triggers([glucose_value])
        result["v11_processing"]["triggers"] = [t.to_dict() for t in triggers]
        
        # 2. v14: TriggerRouter 事件路由
        if is_feature_enabled("ENABLE_TRIGGER_EVENT_ROUTING"):
            router = get_trigger_router()
            if router and triggers:
                for trigger in triggers:
                    if trigger.tag_id == "low_glucose":
                        router.emit_cgm_low(user_id, glucose_value)
                    elif trigger.tag_id == "high_glucose":
                        router.emit_cgm_high(user_id, glucose_value)
                
                events = router.process_pending_events()
                result["v14_processing"]["trigger_events"] = events
    
    # 3. v14: RhythmEngine 节律检测
    if is_feature_enabled("ENABLE_RHYTHM_MODEL") and glucose_value:
        rhythm_engine = get_rhythm_engine()
        if rhythm_engine:
            signal = rhythm_engine.detect_cgm_rhythm(user_id, [glucose_value])
            policy = rhythm_engine.apply_policy(signal)
            result["v14_processing"]["rhythm"] = {
                "signal": signal.to_dict(),
                "policy": policy
            }
    
    # 4. v14: AgentEnhancer 安全检查
    enhancer = get_agent_enhancer()
    if enhancer:
        agent_result = enhancer.process(
            user_id=user_id,
            message=message,
            original_response="",
            context=context
        )
        result["v14_processing"]["agent"] = {
            "action": agent_result["final_action"],
            "modified": agent_result["modified"]
        }
        
        # 如果需要升级到人工
        if agent_result["final_action"] == "escalate":
            result["final_response"] = agent_result["enhanced_response"]
            result["escalated"] = True
            return result
    
    # 5. v11: DecisionCore 生成响应
    try:
        from core.decision_core import DecisionCore
        from core.decision_models import DecisionContext, BloodGlucoseData
        
        decision_core = DecisionCore()
        ctx = DecisionContext(
            user_id=user_id,
            user_name=context.get("user_name", f"用户{user_id}"),
            current_glucose=BloodGlucoseData(value=glucose_value) if glucose_value else None,
            behavioral_tags=context.get("tags", [])
        )
        
        response = await decision_core.decide_intervention(ctx)
        result["v11_processing"]["decision"] = response
        result["final_response"] = response.get("content", "")
        
    except Exception as e:
        logger.error(f"[v14] DecisionCore调用失败: {e}")
        result["error"] = str(e)
    
    return result


# ============================================
# [v14-NEW] 包含质量审计路由
# ============================================
if QUALITY_ROUTES_AVAILABLE:
    router.include_router(quality_router)
    logger.info("[v14] 质量审计路由已加载: /api/v2/quality/*")

# ============================================
# [v14-NEW] 包含披露控制路由
# ============================================
if DISCLOSURE_ROUTES_AVAILABLE:
    router.include_router(disclosure_router)
    logger.info("[v14] 披露控制路由已加载: /api/v2/disclosure/*")
