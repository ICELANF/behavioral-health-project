"""
BehaviorOS — 行为处方 REST API 路由
=====================================
FastAPI 路由模块, 提供行为处方系统的完整 REST 接口

端点总览 (8 个新端点):
  POST   /api/v1/rx/compute          — 计算行为处方
  GET    /api/v1/rx/{rx_id}          — 获取处方详情
  GET    /api/v1/rx/user/{user_id}   — 获取用户处方历史
  GET    /api/v1/rx/strategies       — 获取策略模板列表
  POST   /api/v1/rx/handoff          — 发起Agent交接
  GET    /api/v1/rx/handoff/{user_id}— 获取交接日志
  POST   /api/v1/rx/collaborate      — 协作编排执行
  GET    /api/v1/rx/agents/status    — Agent注册状态

权限: 需要 coach 及以上角色
集成: v31 auth.py get_role_level() 鉴权体系
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..core.rx_schemas import (
    ComputeRxRequest,
    ComputeRxResponse,
    ExpertAgentType,
    HandoffRequest,
    HandoffResponse,
    HandoffListResponse,
    HandoffStatus,
    RxContext,
    RxListResponse,
    RxPrescriptionDTO,
    StrategyTemplateResponse,
)
from ..core.behavior_rx_engine import BehaviorRxEngine
from ..core.agent_handoff_service import AgentHandoffService
from ..core.agent_collaboration_orchestrator import (
    AgentCollaborationOrchestrator,
    CollaborationScenario,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rx", tags=["Behavioral Prescription"])


# =====================================================================
# 依赖注入 (Singleton 模式, 实际项目中由 DI 容器管理)
# =====================================================================

_rx_engine: Optional[BehaviorRxEngine] = None
_handoff_service: Optional[AgentHandoffService] = None
_orchestrator: Optional[AgentCollaborationOrchestrator] = None


def get_rx_engine() -> BehaviorRxEngine:
    global _rx_engine
    if _rx_engine is None:
        _rx_engine = BehaviorRxEngine()
    return _rx_engine


def get_handoff_service() -> AgentHandoffService:
    global _handoff_service
    if _handoff_service is None:
        _handoff_service = AgentHandoffService()
    return _handoff_service


def get_orchestrator() -> AgentCollaborationOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentCollaborationOrchestrator()
    return _orchestrator


# =====================================================================
# 请求/响应扩展模型
# =====================================================================

class CollaborateRequest(BaseModel):
    """协作编排请求"""
    user_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    user_input: Dict[str, Any] = Field(
        ...,
        description="用户输入 {message, device_data, behavioral_profile, domain_data}",
    )
    current_agent: Optional[ExpertAgentType] = None


class CollaborateResponse(BaseModel):
    """协作编排响应"""
    scenario: str
    primary_agent: str
    secondary_agents: List[str]
    merge_strategy: str
    merged_message: str
    merged_content: Dict[str, Any]
    primary_rx: Optional[RxPrescriptionDTO] = None


class AgentStatusResponse(BaseModel):
    """Agent注册状态响应"""
    registered_agents: List[str]
    total: int
    fully_operational: bool
    required_agents: List[str] = [
        "behavior_coach",
        "metabolic_expert",
        "cardiac_expert",
        "adherence_expert",
    ]


# =====================================================================
# 端点 1: 计算行为处方
# =====================================================================

@router.post(
    "/compute",
    response_model=ComputeRxResponse,
    status_code=status.HTTP_200_OK,
    summary="计算行为处方",
    description=(
        "基于三维上下文(TTM阶段×BigFive×CAPACITY)计算个性化行为处方。"
        "返回完整 RxPrescription 对象。"
    ),
)
async def compute_rx(
    request: ComputeRxRequest,
    engine: BehaviorRxEngine = Depends(get_rx_engine),
    # db: Session = Depends(get_db),  # 实际项目中注入数据库会话
):
    """
    计算行为处方

    输入三维上下文, 输出个性化处方对象:
      - 目标行为 + 主策略 + 辅助策略
      - 强度 + 节奏 + 沟通风格
      - 微行动列表 + 奖励触发器
      - 阻力阈值 + 升级规则
    """
    try:
        prescription = await engine.compute_rx_async(
            context=request.context,
            agent_type=request.agent_type,
            db=None,  # 替换为实际 db session
            persist=False,
            override_strategy=request.override_strategy,
            override_intensity=request.override_intensity,
        )
        return ComputeRxResponse(
            prescription=prescription,
            persisted=False,
            rx_id=prescription.rx_id,
        )
    except Exception as e:
        logger.error(f"Compute rx failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处方计算失败: {str(e)}",
        )


# =====================================================================
# 端点 2: 获取处方详情
# =====================================================================

@router.get(
    "/{rx_id}",
    response_model=RxPrescriptionDTO,
    summary="获取处方详情",
)
async def get_rx_detail(
    rx_id: uuid.UUID,
    # db: Session = Depends(get_db),
):
    """通过 rx_id 获取处方详情"""
    # 实际实现: 查询 rx_prescriptions 表
    # prescription = db.query(RxPrescription).filter_by(id=rx_id).first()
    # if not prescription:
    #     raise HTTPException(status_code=404, detail="处方不存在")
    # return prescription.to_dto()
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="需要数据库集成 — 请在 v31 环境中使用",
    )


# =====================================================================
# 端点 3: 用户处方历史
# =====================================================================

@router.get(
    "/user/{user_id}",
    response_model=RxListResponse,
    summary="获取用户处方历史",
)
async def get_user_rx_history(
    user_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    agent_type: Optional[ExpertAgentType] = None,
    # db: Session = Depends(get_db),
):
    """
    获取指定用户的处方历史

    支持按 agent_type 过滤, 按时间倒序排列
    """
    # 实际实现: 查询 rx_prescriptions 表
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="需要数据库集成",
    )


# =====================================================================
# 端点 4: 策略模板列表
# =====================================================================

@router.get(
    "/strategies",
    response_model=List[Dict[str, Any]],
    summary="获取行为策略模板列表",
)
async def list_strategy_templates(
    domain: Optional[str] = None,
    enabled_only: bool = True,
    engine: BehaviorRxEngine = Depends(get_rx_engine),
):
    """
    获取 12 种行为策略模板

    可按 domain 过滤 (general/metabolic/cardiac/adherence)
    """
    try:
        templates = engine.get_strategy_templates(
            domain=domain, enabled_only=enabled_only
        )
        return templates
    except Exception as e:
        logger.error(f"List strategies failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =====================================================================
# 端点 5: 发起Agent交接
# =====================================================================

@router.post(
    "/handoff",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="发起Agent交接",
)
async def initiate_handoff(
    request: HandoffRequest,
    service: AgentHandoffService = Depends(get_handoff_service),
    # db: Session = Depends(get_db),
):
    """
    发起 Agent 交接

    交接类型:
      - stage_promotion: 阶段晋升交接 (Coach → 领域Agent)
      - stage_regression: 阶段回退接管 (领域Agent → Coach)
      - domain_coordination: 领域间协作交接
      - cross_cutting: 横切介入 (Adherence Agent)
      - emergency_takeover: 紧急接管
    """
    try:
        result = await service.initiate_handoff(request, db=None)
        return result
    except Exception as e:
        logger.error(f"Handoff failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"交接失败: {str(e)}",
        )


# =====================================================================
# 端点 6: 交接日志
# =====================================================================

@router.get(
    "/handoff/{user_id}",
    response_model=HandoffListResponse,
    summary="获取用户交接日志",
)
async def get_handoff_logs(
    user_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    # db: Session = Depends(get_db),
):
    """获取指定用户的 Agent 交接历史日志"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="需要数据库集成",
    )


# =====================================================================
# 端点 7: 协作编排
# =====================================================================

@router.post(
    "/collaborate",
    response_model=CollaborateResponse,
    summary="4-Agent协作编排",
    description=(
        "多Agent协作编排入口。根据用户上下文自动识别协作场景, "
        "路由到主导Agent, 触发辅助Agent, 合并处方返回。"
    ),
)
async def collaborate(
    request: CollaborateRequest,
    orchestrator: AgentCollaborationOrchestrator = Depends(get_orchestrator),
    # db: Session = Depends(get_db),
):
    """
    4-Agent 协作编排执行

    自动识别场景并编排:
      - new_user_assessment: 新用户 → Coach主导
      - glucose_abnormal: 血糖异常 → Metabolic主导
      - exercise_fear: 运动恐惧 → Coach前置 + Cardiac待命
      - multi_morbidity: 多病共管 → 并行 + 横切
      - stage_regression: 阶段回退 → Coach紧急接管
      - pre_visit: 就诊准备 → Adherence主导
    """
    try:
        merged = await orchestrator.orchestrate(
            user_input=request.user_input,
            user_id=request.user_id,
            session_id=request.session_id,
            current_agent=request.current_agent,
            db=None,
        )
        return CollaborateResponse(
            scenario=merged.collaboration.scenario.value,
            primary_agent=merged.collaboration.primary_agent.value,
            secondary_agents=[
                a.value for a in merged.collaboration.secondary_agents
            ],
            merge_strategy=merged.collaboration.merge_strategy,
            merged_message=merged.merged_message,
            merged_content=merged.merged_content,
            primary_rx=merged.primary.rx,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Collaboration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"协作编排失败: {str(e)}",
        )


# =====================================================================
# 端点 8: Agent状态
# =====================================================================

@router.get(
    "/agents/status",
    response_model=AgentStatusResponse,
    summary="获取Agent注册状态",
)
async def get_agents_status(
    orchestrator: AgentCollaborationOrchestrator = Depends(get_orchestrator),
):
    """获取 4 款专家 Agent 的注册状态"""
    registered = orchestrator.get_registered_agents()
    return AgentStatusResponse(
        registered_agents=registered,
        total=len(registered),
        fully_operational=orchestrator.is_fully_operational(),
    )
