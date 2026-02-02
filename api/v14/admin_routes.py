"""
行为健康数字平台 - Admin 端配置接口
Admin Behavior Configuration API

[v15-NEW] Admin API

路由前缀: /api/v1/admin/behavior/

端点：
- GET /rules - 获取当前母库逻辑
- PUT /rules - 更新母库逻辑
- POST /rules/validate - 验证逻辑表达式
- GET /actions - 获取动作包列表
- GET /stages - 获取阶段定义
- POST /rules/reload - 热重载配置
- GET /sync/pending - 获取待审核事件
- GET /sync/view/{event_id} - 获取事件视图
"""
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
import json

# 导入服务
try:
    from services.logic_engine import (
        get_behavior_engine,
        BehaviorLibrary,
        RuleValidator
    )
    LOGIC_ENGINE_AVAILABLE = True
except ImportError:
    LOGIC_ENGINE_AVAILABLE = False
    logger.warning("[AdminAPI] 逻辑引擎未加载")

try:
    from services.state_sync import (
        get_state_sync_manager,
        EventType,
        ViewRole
    )
    STATE_SYNC_AVAILABLE = True
except ImportError:
    STATE_SYNC_AVAILABLE = False
    logger.warning("[AdminAPI] 状态同步未加载")


router = APIRouter(prefix="/admin/behavior", tags=["admin", "behavior"])


# ============================================
# 请求模型
# ============================================

class ValidateConditionRequest(BaseModel):
    """验证条件表达式请求"""
    condition: str
    test_context: Optional[Dict[str, Any]] = None


class UpdateRulesRequest(BaseModel):
    """更新规则请求"""
    rules_json: Dict[str, Any]
    author: Optional[str] = None


class ProcessEventRequest(BaseModel):
    """处理事件请求"""
    user_id: int
    event_type: str
    raw_data: Dict[str, Any]
    trigger_id: Optional[str] = None
    action_id: Optional[str] = None


# ============================================
# 母库配置 API
# ============================================

@router.get("/rules")
async def get_behavior_rules():
    """
    获取当前母库逻辑
    
    GET /api/v1/admin/behavior/rules
    """
    if not LOGIC_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="逻辑引擎未加载")
    
    engine = get_behavior_engine()
    
    if not engine.library:
        raise HTTPException(status_code=404, detail="母库未加载")
    
    return {
        "success": True,
        "data": {
            "version": engine.library.version,
            "name": engine.library.name,
            "stages": {k: v.dict() for k, v in engine.library.stages.items()},
            "triggers": [t.dict() for t in engine.library.triggers],
            "action_packages": {k: v.dict() for k, v in engine.library.action_packages.items()},
            "updated_at": engine.library.updated_at.isoformat() if engine.library.updated_at else None
        }
    }


@router.put("/rules")
async def update_behavior_rules(request: UpdateRulesRequest):
    """
    更新母库逻辑
    
    PUT /api/v1/admin/behavior/rules
    """
    if not LOGIC_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="逻辑引擎未加载")
    
    try:
        # 验证新配置
        new_library = BehaviorLibrary(**request.rules_json)
        valid, errors = RuleValidator.validate_library(new_library)
        
        if not valid:
            return {
                "success": False,
                "errors": errors
            }
        
        # 写入配置文件
        engine = get_behavior_engine()
        config_path = engine.config_path
        
        # 添加元信息
        request.rules_json['updated_at'] = datetime.now().isoformat()
        if request.author:
            request.rules_json['author'] = request.author
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(request.rules_json, f, ensure_ascii=False, indent=2)
        
        # 重新加载
        engine.reload()
        
        return {
            "success": True,
            "message": "母库配置已更新",
            "version": new_library.version
        }
        
    except Exception as e:
        logger.error(f"[AdminAPI] 更新母库失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rules/validate")
async def validate_behavior_rules(request: ValidateConditionRequest):
    """
    验证逻辑表达式是否合法
    
    POST /api/v1/admin/behavior/rules/validate
    
    防止专家写错 Python 表达式导致系统崩溃
    """
    if not LOGIC_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="逻辑引擎未加载")
    
    # 验证语法和安全性
    valid, error = RuleValidator.validate_condition(request.condition)
    
    result = {
        "condition": request.condition,
        "valid": valid,
        "error": error
    }
    
    # 如果提供了测试上下文，尝试执行
    if valid and request.test_context:
        try:
            from services.logic_engine.behavior_engine import ConditionEvaluator
            
            test_result = ConditionEvaluator.evaluate(
                request.condition,
                user=request.test_context.get('user', {}),
                snippet=request.test_context.get('snippet', {}),
                data=request.test_context.get('data', {}),
                context=request.test_context.get('context', {})
            )
            result["test_result"] = test_result
            result["test_context"] = request.test_context
            
        except Exception as e:
            result["test_error"] = str(e)
    
    return result


@router.post("/rules/reload")
async def reload_behavior_rules():
    """
    热重载配置
    
    POST /api/v1/admin/behavior/rules/reload
    """
    if not LOGIC_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="逻辑引擎未加载")
    
    engine = get_behavior_engine()
    success = engine.reload()
    
    if success:
        return {
            "success": True,
            "message": "配置重载成功",
            "stages_count": len(engine.library.stages) if engine.library else 0,
            "triggers_count": len(engine.library.triggers) if engine.library else 0,
            "actions_count": len(engine.library.action_packages) if engine.library else 0
        }
    else:
        raise HTTPException(status_code=500, detail="配置重载失败")


# ============================================
# 动作包和阶段 API
# ============================================

@router.get("/actions")
async def get_action_packages():
    """
    获取动作包列表
    
    GET /api/v1/admin/behavior/actions
    """
    if not LOGIC_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="逻辑引擎未加载")
    
    engine = get_behavior_engine()
    
    return {
        "success": True,
        "actions": engine.list_all_actions()
    }


@router.get("/actions/{action_id}")
async def get_action_by_id(action_id: str):
    """获取单个动作包"""
    if not LOGIC_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="逻辑引擎未加载")
    
    engine = get_behavior_engine()
    action = engine.get_action_by_id(action_id)
    
    if not action:
        raise HTTPException(status_code=404, detail=f"动作包不存在: {action_id}")
    
    return {
        "success": True,
        "action": action.dict()
    }


@router.get("/stages")
async def get_stage_definitions():
    """
    获取阶段定义
    
    GET /api/v1/admin/behavior/stages
    """
    if not LOGIC_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="逻辑引擎未加载")
    
    engine = get_behavior_engine()
    
    if not engine.library:
        return {"success": True, "stages": {}}
    
    return {
        "success": True,
        "stages": {k: v.dict() for k, v in engine.library.stages.items()}
    }


@router.get("/stages/{stage_id}")
async def get_stage_by_id(stage_id: str):
    """获取单个阶段定义"""
    if not LOGIC_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="逻辑引擎未加载")
    
    engine = get_behavior_engine()
    stage_info = engine.get_stage_info(stage_id)
    
    if not stage_info:
        raise HTTPException(status_code=404, detail=f"阶段不存在: {stage_id}")
    
    return {
        "success": True,
        "stage": stage_info
    }


@router.get("/triggers")
async def get_trigger_rules():
    """
    获取触发规则列表
    
    GET /api/v1/admin/behavior/triggers
    """
    if not LOGIC_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="逻辑引擎未加载")
    
    engine = get_behavior_engine()
    
    return {
        "success": True,
        "triggers": engine.list_all_triggers()
    }


@router.get("/triggers/for-stage/{stage_id}")
async def get_triggers_for_stage(stage_id: str):
    """获取适用于指定阶段的触发规则"""
    if not LOGIC_ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="逻辑引擎未加载")
    
    engine = get_behavior_engine()
    triggers = engine.get_applicable_triggers(stage_id)
    
    return {
        "success": True,
        "stage_id": stage_id,
        "triggers": [t.dict() for t in triggers]
    }


# ============================================
# 状态同步 API
# ============================================

@router.post("/sync/process")
async def process_sync_event(request: ProcessEventRequest):
    """
    处理同步事件
    
    POST /api/v1/admin/behavior/sync/process
    """
    if not STATE_SYNC_AVAILABLE:
        raise HTTPException(status_code=503, detail="状态同步未加载")
    
    try:
        event_type = EventType(request.event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的事件类型: {request.event_type}")
    
    manager = get_state_sync_manager()
    record = manager.process_event(
        user_id=request.user_id,
        event_type=event_type,
        raw_data=request.raw_data,
        trigger_id=request.trigger_id,
        action_id=request.action_id
    )
    
    return {
        "success": True,
        "event_id": record.event_id,
        "record": record.to_dict()
    }


@router.get("/sync/view/{event_id}")
async def get_sync_view(event_id: str, role: str = "patient"):
    """
    获取事件视图
    
    GET /api/v1/admin/behavior/sync/view/{event_id}?role=patient|coach|expert|admin
    """
    if not STATE_SYNC_AVAILABLE:
        raise HTTPException(status_code=503, detail="状态同步未加载")
    
    try:
        view_role = ViewRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的角色: {role}")
    
    manager = get_state_sync_manager()
    view = manager.get_view(event_id, view_role)
    
    if not view:
        raise HTTPException(status_code=404, detail=f"事件不存在: {event_id}")
    
    return {
        "success": True,
        "event_id": event_id,
        "role": role,
        "view": view
    }


@router.get("/sync/user/{user_id}")
async def get_user_sync_events(
    user_id: int,
    role: str = "patient",
    limit: int = Query(10, ge=1, le=100)
):
    """
    获取用户的同步事件列表
    
    GET /api/v1/admin/behavior/sync/user/{user_id}?role=patient&limit=10
    """
    if not STATE_SYNC_AVAILABLE:
        raise HTTPException(status_code=503, detail="状态同步未加载")
    
    try:
        view_role = ViewRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的角色: {role}")
    
    manager = get_state_sync_manager()
    events = manager.get_user_events(user_id, view_role, limit)
    
    return {
        "success": True,
        "user_id": user_id,
        "role": role,
        "events": events
    }


@router.get("/sync/pending")
async def get_pending_reviews():
    """
    获取待审核事件
    
    GET /api/v1/admin/behavior/sync/pending
    """
    if not STATE_SYNC_AVAILABLE:
        raise HTTPException(status_code=503, detail="状态同步未加载")
    
    manager = get_state_sync_manager()
    pending = manager.get_pending_reviews()
    
    return {
        "success": True,
        "total": len(pending),
        "pending": pending
    }


# ============================================
# 状态统计 API
# ============================================

@router.get("/stats")
async def get_behavior_stats():
    """
    获取行为系统统计
    
    GET /api/v1/admin/behavior/stats
    """
    stats = {
        "logic_engine": {
            "available": LOGIC_ENGINE_AVAILABLE
        },
        "state_sync": {
            "available": STATE_SYNC_AVAILABLE
        }
    }
    
    if LOGIC_ENGINE_AVAILABLE:
        engine = get_behavior_engine()
        if engine.library:
            stats["logic_engine"].update({
                "version": engine.library.version,
                "stages_count": len(engine.library.stages),
                "triggers_count": len(engine.library.triggers),
                "actions_count": len(engine.library.action_packages)
            })
    
    if STATE_SYNC_AVAILABLE:
        manager = get_state_sync_manager()
        stats["state_sync"].update({
            "total_records": len(manager._records),
            "pending_reviews": len(manager.get_pending_reviews())
        })
    
    return {
        "success": True,
        "stats": stats
    }
