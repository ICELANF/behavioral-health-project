# -*- coding: utf-8 -*-
"""
API 路由定义

定义所有 REST API 端点
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from .schemas import (
    ChatRequest,
    ChatResponse,
    DecomposeRequest,
    DecomposeResponse,
    HealthCheckResponse,
    ErrorResponse,
    ExpertsListResponse,
    ExpertInfo,
    OctopusChatRequest,
    OctopusChatResponse,
    ClampedTask,
    ReasoningStepModel,
)
from agents.octopus_engine import OctopusClampingEngine, get_clamping_engine
from .session import session_manager, Session
from .services import TaskDecomposer, calculate_average_efficacy, count_categories


# =============================================================================
# 路由器实例
# =============================================================================

router = APIRouter(prefix="/api/v1", tags=["v1"])


# =============================================================================
# 依赖注入
# =============================================================================

# 全局状态（在 main.py 中初始化）
_orchestrator = None
_task_decomposer = None
_config = None


def get_orchestrator():
    """获取 Orchestrator 实例"""
    if _orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="服务尚未初始化，请稍后再试"
        )
    return _orchestrator


def get_decomposer():
    """获取 TaskDecomposer 实例"""
    if _task_decomposer is None:
        raise HTTPException(
            status_code=503,
            detail="任务分解服务尚未初始化"
        )
    return _task_decomposer


def init_dependencies(orchestrator, config: dict):
    """初始化依赖

    在应用启动时调用
    """
    global _orchestrator, _task_decomposer, _config
    _orchestrator = orchestrator
    _config = config
    _task_decomposer = TaskDecomposer(config)


# =============================================================================
# 健康检查
# =============================================================================

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="健康检查",
    description="检查服务状态和已加载的专家数量"
)
async def health_check():
    """健康检查端点"""
    experts_count = 0
    if _orchestrator:
        experts_count = len(_orchestrator.registry)

    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        experts_loaded=experts_count,
        timestamp=datetime.now()
    )


# =============================================================================
# 专家列表
# =============================================================================

@router.get(
    "/experts",
    response_model=ExpertsListResponse,
    summary="获取专家列表",
    description="获取所有可用的专家信息"
)
async def list_experts(orchestrator=Depends(get_orchestrator)):
    """获取专家列表"""
    experts_data = orchestrator.get_available_experts()

    experts = [
        ExpertInfo(
            id=e["id"],
            name=e["name"],
            description=e.get("description", "")
        )
        for e in experts_data
    ]

    return ExpertsListResponse(
        experts=experts,
        count=len(experts)
    )


# =============================================================================
# Chat 接口
# =============================================================================

@router.post(
    "/chat",
    response_model=OctopusChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        503: {"model": ErrorResponse, "description": "服务不可用"},
    },
    summary="八爪鱼智能对话",
    description="与教练组进行对话，集成效能感限幅引擎，返回结构化任务"
)
async def chat(
    request: OctopusChatRequest,
    orchestrator=Depends(get_orchestrator)
):
    """八爪鱼智能对话接口

    - 自动路由到合适的专家
    - 集成效能感限幅 (Octopus Clamping)
    - 返回 reasoning_path 和 clamped_tasks
    - 支持穿戴设备数据 (wearable_data) 输入
    """
    # 获取或创建会话
    session = session_manager.get_or_create_session(request.session_id)

    # 记录用户消息
    session.add_message("user", request.message)

    try:
        # 1. 获取专家响应
        if request.expert_id:
            expert_config = orchestrator.registry.get_config(request.expert_id)
            if not expert_config:
                raise HTTPException(
                    status_code=400,
                    detail=f"未找到专家: {request.expert_id}"
                )
            response_text = orchestrator.direct_chat(request.expert_id, request.message)
            primary_expert = expert_config.name
            primary_expert_id = request.expert_id
            consulted_experts = []
            routing_confidence = 1.0
        else:
            orch_result = orchestrator.process_query(request.message)
            response_text = orch_result.final_response
            primary_expert = orch_result.primary_expert
            primary_expert_id = orch_result.primary_expert_id
            consulted_experts = orch_result.consulted_experts
            routing_confidence = orch_result.routing_confidence

        # 2. 生成原始任务列表（模拟从专家响应中提取）
        # 实际生产中应该从 LLM 解析或专家系统返回
        raw_tasks = [
            {"id": 1, "content": "深度冥想20分钟", "difficulty": 4, "type": "mental"},
            {"id": 2, "content": "记录一次情绪日志", "difficulty": 2, "type": "mental"},
            {"id": 3, "content": "进行3次深呼吸", "difficulty": 1, "type": "mental"},
            {"id": 4, "content": "户外散步15分钟", "difficulty": 2, "type": "physical"},
            {"id": 5, "content": "与朋友聊天10分钟", "difficulty": 3, "type": "social"},
        ]

        # 3. 初始化八爪鱼限幅引擎
        clamping_engine = get_clamping_engine(
            user_id=session.session_id,
            efficacy_score=request.efficacy_score
        )

        # 4. 执行限幅算法
        wearable_dict = request.wearable_data.model_dump() if request.wearable_data else None
        clamping_result = clamping_engine.octopus_clamping(raw_tasks, wearable_dict)

        # 5. 构建外部钩子
        external_hooks = {
            "show_video": clamping_result.final_efficacy < 30,
            "clinical_alert": clamping_result.final_efficacy < 10,
            "suggest_break": clamping_result.wearable_impact and clamping_result.wearable_impact.get("hr", 0) > 100
        }

        # 6. 转换任务格式
        clamped_tasks = [
            ClampedTask(
                id=t["id"],
                content=t["content"],
                difficulty=t["difficulty"],
                type=t.get("type", "general")
            )
            for t in clamping_result.clamped_tasks
        ]

        # 7. 转换推理路径格式
        reasoning_path = [
            ReasoningStepModel(
                phase=step["phase"],
                input=step["input"],
                output=step["output"],
                decision=step["decision"],
                timestamp=step["timestamp"]
            )
            for step in clamping_result.reasoning_path
        ]

        # 8. 构建响应
        result = OctopusChatResponse(
            session_id=session.session_id,
            status="success",
            response=response_text,
            clamped_tasks=clamped_tasks,
            reasoning_path=reasoning_path,
            input_efficacy=request.efficacy_score,
            final_efficacy=clamping_result.final_efficacy,
            clamping_level=clamping_result.clamping_level,
            primary_expert=primary_expert,
            primary_expert_id=primary_expert_id,
            consulted_experts=consulted_experts,
            external_hooks=external_hooks,
            wearable_impact=clamping_result.wearable_impact,
            timestamp=datetime.now()
        )

        # 记录助手回复
        session.add_message(
            "assistant",
            result.response,
            expert_id=result.primary_expert_id
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理请求时发生错误: {str(e)}"
        )


# =============================================================================
# Decompose 接口
# =============================================================================

@router.post(
    "/decompose",
    response_model=DecomposeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        503: {"model": ErrorResponse, "description": "服务不可用"},
    },
    summary="任务分解",
    description="将健康建议拆解为可执行的原子任务列表"
)
async def decompose_advice(
    request: DecomposeRequest,
    decomposer=Depends(get_decomposer)
):
    """任务分解接口

    - 将长建议拆解为具体任务
    - 每个任务包含效能评分
    - 支持个性化分解
    """
    try:
        # 调用分解器
        tasks = decomposer.decompose(
            advice_text=request.advice_text,
            max_tasks=request.max_tasks,
            include_efficacy=request.include_efficacy,
            user_context=request.user_context
        )

        # 计算统计信息
        avg_efficacy = None
        if request.include_efficacy:
            avg_efficacy = calculate_average_efficacy(tasks)

        categories_summary = count_categories(tasks)

        return DecomposeResponse(
            original_advice=request.advice_text,
            tasks=tasks,
            task_count=len(tasks),
            categories_summary=categories_summary,
            average_efficacy=avg_efficacy,
            timestamp=datetime.now()
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"任务分解失败: {str(e)}"
        )


# =============================================================================
# 会话管理
# =============================================================================

@router.delete(
    "/session/{session_id}",
    summary="删除会话",
    description="删除指定的会话及其历史记录"
)
async def delete_session(session_id: str):
    """删除会话"""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"会话不存在: {session_id}"
        )
    return {"message": "会话已删除", "session_id": session_id}


@router.post(
    "/session/reset-all",
    summary="重置所有会话",
    description="清空所有会话（管理接口）"
)
async def reset_all_sessions():
    """重置所有会话"""
    count = session_manager.get_session_count()
    session_manager.clear_all()

    if _orchestrator:
        _orchestrator.reset_all()

    return {"message": f"已清空 {count} 个会话"}
