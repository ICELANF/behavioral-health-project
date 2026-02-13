"""
BehaviorOS — 行为处方 REST API 路由 (v32 完善版)
==================================================
FastAPI 路由模块, 提供行为处方系统的完整 REST 接口

端点总览 (8 个端点):
  POST   /api/v1/rx/compute          — 计算行为处方 (含DB持久化)
  GET    /api/v1/rx/strategies       — 获取策略模板列表
  GET    /api/v1/rx/agents/status    — Agent注册状态
  GET    /api/v1/rx/user/{user_id}   — 获取用户处方历史 (DB查询)
  POST   /api/v1/rx/handoff          — 发起Agent交接 (DB持久化)
  GET    /api/v1/rx/handoff/{user_id}— 获取交接日志 (DB查询)
  POST   /api/v1/rx/collaborate      — 协作编排执行
  GET    /api/v1/rx/{rx_id}          — 获取处方详情 (DB查询, 须放最后)

权限: 需要 coach 及以上角色 (require_coach_or_admin)
鉴权: JWT Bearer Token (api/dependencies.py)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .rx_schemas import (
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
    RxStrategyType,
    RxIntensity,
    CommunicationStyle,
    MicroAction,
    RewardTrigger,
    EscalationRule,
    StrategyTemplateResponse,
)
from .rx_models import (
    RxPrescription,
    RxStrategyTemplate,
    AgentHandoffLog,
)
from .behavior_rx_engine import BehaviorRxEngine
from .agent_handoff_service import AgentHandoffService
from .agent_collaboration_orchestrator import (
    AgentCollaborationOrchestrator,
    CollaborationScenario,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rx", tags=["Behavioral Prescription"])


# =====================================================================
# 依赖注入 — 支持 main.py lifespan 注入 + 懒加载降级
# =====================================================================

_rx_engine: Optional[BehaviorRxEngine] = None
_handoff_service: Optional[AgentHandoffService] = None
_orchestrator: Optional[AgentCollaborationOrchestrator] = None


def set_shared_instances(
    engine: BehaviorRxEngine,
    handoff: AgentHandoffService,
    orchestrator: AgentCollaborationOrchestrator,
):
    """由 main.py lifespan 调用, 注入已初始化(含已注册Agent)的实例"""
    global _rx_engine, _handoff_service, _orchestrator
    _rx_engine = engine
    _handoff_service = handoff
    _orchestrator = orchestrator
    logger.info("rx_routes: shared instances injected from lifespan")


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


# DB Session 依赖
def get_db():
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Auth 依赖
def get_current_coach():
    """coach+ 权限守卫 — 延迟导入避免循环"""
    from api.dependencies import require_coach_or_admin
    return require_coach_or_admin


# =====================================================================
# ORM → DTO 转换
# =====================================================================

def _rx_orm_to_dto(rx: RxPrescription) -> RxPrescriptionDTO:
    """将 ORM RxPrescription 转换为 Pydantic DTO"""
    # secondary_strategies: JSONB list of strings → List[RxStrategyType]
    secondary = []
    if rx.secondary_strategies:
        for s in rx.secondary_strategies:
            try:
                secondary.append(RxStrategyType(s))
            except ValueError:
                pass

    # micro_actions: JSONB list of dicts → List[MicroAction]
    micro_actions = []
    if rx.micro_actions:
        for ma in rx.micro_actions:
            try:
                micro_actions.append(MicroAction(**ma))
            except Exception:
                pass

    # reward_triggers: JSONB list of dicts → List[RewardTrigger]
    reward_triggers = []
    if rx.reward_triggers:
        for rt in rx.reward_triggers:
            try:
                reward_triggers.append(RewardTrigger(**rt))
            except Exception:
                pass

    # escalation_rules: JSONB list of dicts → List[EscalationRule]
    escalation_rules = []
    if rx.escalation_rules:
        for er in rx.escalation_rules:
            try:
                escalation_rules.append(EscalationRule(**er))
            except Exception:
                pass

    return RxPrescriptionDTO(
        rx_id=rx.id,
        agent_type=ExpertAgentType(rx.agent_type.value
                                   if hasattr(rx.agent_type, 'value')
                                   else rx.agent_type),
        goal_behavior=rx.goal_behavior,
        strategy_type=RxStrategyType(rx.strategy_type.value
                                     if hasattr(rx.strategy_type, 'value')
                                     else rx.strategy_type),
        secondary_strategies=secondary,
        intensity=RxIntensity(rx.intensity.value
                              if hasattr(rx.intensity, 'value')
                              else rx.intensity),
        pace=rx.pace or "standard",
        communication_style=CommunicationStyle(
            rx.communication_style.value
            if hasattr(rx.communication_style, 'value')
            else rx.communication_style),
        micro_actions=micro_actions,
        reward_triggers=reward_triggers,
        resistance_threshold=rx.resistance_threshold or 0.3,
        escalation_rules=escalation_rules,
        domain_context=rx.domain_context or {},
        ttm_stage=rx.ttm_stage,
        confidence=0.8,
        reasoning="",
    )


def _handoff_orm_to_dict(h: AgentHandoffLog) -> Dict[str, Any]:
    """将 ORM AgentHandoffLog 转换为 dict"""
    return {
        "id": str(h.id),
        "user_id": str(h.user_id),
        "session_id": str(h.session_id) if h.session_id else None,
        "from_agent": h.from_agent.value if hasattr(h.from_agent, 'value') else h.from_agent,
        "to_agent": h.to_agent.value if hasattr(h.to_agent, 'value') else h.to_agent,
        "handoff_type": h.handoff_type.value if hasattr(h.handoff_type, 'value') else h.handoff_type,
        "status": h.status.value if hasattr(h.status, 'value') else h.status,
        "trigger_reason": h.trigger_reason,
        "trigger_data": h.trigger_data or {},
        "rx_context": h.rx_context or {},
        "rx_prescription_id": str(h.rx_prescription_id) if h.rx_prescription_id else None,
        "outcome": h.outcome or {},
        "resolution_notes": h.resolution_notes,
        "initiated_at": h.initiated_at.isoformat() if h.initiated_at else None,
        "completed_at": h.completed_at.isoformat() if h.completed_at else None,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }


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
# 端点 1: 计算行为处方 (POST)
# =====================================================================

@router.post(
    "/compute",
    response_model=ComputeRxResponse,
    status_code=status.HTTP_200_OK,
    summary="计算行为处方",
    description=(
        "基于三维上下文(TTM阶段×BigFive×CAPACITY)计算个性化行为处方。"
        "返回完整 RxPrescription 对象, 同时持久化到数据库。"
    ),
)
async def compute_rx(
    request: ComputeRxRequest,
    db: Session = Depends(get_db),
    engine: BehaviorRxEngine = Depends(get_rx_engine),
    _user=Depends(get_current_coach()),
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
            db=db,
            persist=True,
            override_strategy=request.override_strategy,
            override_intensity=request.override_intensity,
        )
        return ComputeRxResponse(
            prescription=prescription,
            persisted=True,
            rx_id=prescription.rx_id,
        )
    except Exception as e:
        logger.error(f"Compute rx failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处方计算失败: {str(e)}",
        )


# =====================================================================
# 端点 2: 策略模板列表 (GET 固定路径 — 须在 /{rx_id} 之前)
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
    公开端点, 无需认证。
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
# 端点 3: Agent注册状态 (GET 固定路径 — 须在 /{rx_id} 之前)
# =====================================================================

@router.get(
    "/agents/status",
    response_model=AgentStatusResponse,
    summary="获取Agent注册状态",
)
async def get_agents_status(
    orchestrator: AgentCollaborationOrchestrator = Depends(get_orchestrator),
    _user=Depends(get_current_coach()),
):
    """获取 4 款专家 Agent 的注册状态"""
    registered = orchestrator.get_registered_agents()
    return AgentStatusResponse(
        registered_agents=registered,
        total=len(registered),
        fully_operational=orchestrator.is_fully_operational(),
    )


# =====================================================================
# 端点 4: 用户处方历史 (GET /user/{user_id})
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
    db: Session = Depends(get_db),
    _user=Depends(get_current_coach()),
):
    """
    获取指定用户的处方历史

    支持按 agent_type 过滤, 按时间倒序排列
    """
    try:
        query = db.query(RxPrescription).filter(
            RxPrescription.user_id == user_id
        )
        if agent_type:
            query = query.filter(RxPrescription.agent_type == agent_type.value)

        total = query.count()
        rows = (
            query
            .order_by(RxPrescription.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [_rx_orm_to_dto(r) for r in rows]
        return RxListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"Get user rx history failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取处方历史失败: {str(e)}",
        )


# =====================================================================
# 端点 5: 发起Agent交接 (POST)
# =====================================================================

@router.post(
    "/handoff",
    response_model=HandoffResponse,
    status_code=status.HTTP_201_CREATED,
    summary="发起Agent交接",
)
async def initiate_handoff(
    request: HandoffRequest,
    db: Session = Depends(get_db),
    service: AgentHandoffService = Depends(get_handoff_service),
    _user=Depends(get_current_coach()),
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
        result = await service.initiate_handoff(request, db=db)
        return result
    except Exception as e:
        logger.error(f"Handoff failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"交接失败: {str(e)}",
        )


# =====================================================================
# 端点 6: 交接日志 (GET /handoff/{user_id})
# =====================================================================

@router.get(
    "/handoff/{user_id}",
    response_model=HandoffListResponse,
    summary="获取用户交接日志",
)
async def get_handoff_logs(
    user_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(get_current_coach()),
):
    """获取指定用户的 Agent 交接历史日志"""
    try:
        rows = (
            db.query(AgentHandoffLog)
            .filter(AgentHandoffLog.user_id == user_id)
            .order_by(AgentHandoffLog.initiated_at.desc())
            .limit(limit)
            .all()
        )
        total = (
            db.query(AgentHandoffLog)
            .filter(AgentHandoffLog.user_id == user_id)
            .count()
        )
        items = [_handoff_orm_to_dict(h) for h in rows]
        return HandoffListResponse(items=items, total=total)
    except Exception as e:
        logger.error(f"Get handoff logs failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取交接日志失败: {str(e)}",
        )


# =====================================================================
# 端点 7: 协作编排 (POST)
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
    db: Session = Depends(get_db),
    orchestrator: AgentCollaborationOrchestrator = Depends(get_orchestrator),
    _user=Depends(get_current_coach()),
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
            db=db,
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
# 端点 8: 获取处方详情 (GET /{rx_id} — 放最后, 避免吞其他路由)
# =====================================================================

@router.get(
    "/{rx_id}",
    response_model=RxPrescriptionDTO,
    summary="获取处方详情",
)
async def get_rx_detail(
    rx_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user=Depends(get_current_coach()),
):
    """通过 rx_id 获取处方详情"""
    try:
        rx = db.query(RxPrescription).filter(
            RxPrescription.id == rx_id
        ).first()
        if not rx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"处方 {rx_id} 不存在",
            )
        return _rx_orm_to_dto(rx)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get rx detail failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取处方详情失败: {str(e)}",
        )
