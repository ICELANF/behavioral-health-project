"""
V007 Step 09 / Phase A
Policy API: 策略管理API端点 (FastAPI 版)

功能: 规则CRUD、策略模拟、DecisionTrace查询、成本报告、
     规则热刷新、种子规则初始化
"""

import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, require_admin
from core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/policy", tags=["V007 Policy Engine"])


# ═══════════════════════════════════════════════
# Pydantic Schemas
# ═══════════════════════════════════════════════

class RuleCreateRequest(BaseModel):
    rule_name: str = Field(..., description="规则名称")
    rule_type: str = Field(..., description="规则类型: platform/tenant/emergency/dynamic")
    condition_expr: Dict[str, Any] = Field(..., description="JSON-Logic 条件表达式")
    action_type: str = Field(..., description="动作类型: select_agent/block/adjust_weight/downgrade_model")
    action_params: Dict[str, Any] = Field(default_factory=dict, description="动作参数")
    priority: int = Field(50, ge=0, le=100, description="优先级 0-100")
    tenant_id: Optional[str] = Field(None, description="租户ID (平台规则为空)")
    is_enabled: bool = Field(True)
    evidence_tier: Optional[str] = Field(None, description="证据等级: T1-T5")
    description: Optional[str] = None


class RuleUpdateRequest(BaseModel):
    rule_name: Optional[str] = None
    condition_expr: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    action_params: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    is_enabled: Optional[bool] = None
    evidence_tier: Optional[str] = None
    description: Optional[str] = None


class RuleTestRequest(BaseModel):
    context: Dict[str, Any] = Field(..., description="测试上下文")


class SimulateRequest(BaseModel):
    event: Dict[str, Any] = Field(default_factory=dict, description="事件数据")
    context: Dict[str, Any] = Field(default_factory=dict, description="用户上下文")


# ═══════════════════════════════════════════════
# 1. 规则 CRUD
# ═══════════════════════════════════════════════

@router.get("/rules")
def list_rules(
    rule_type: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    is_enabled: bool = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """查询策略规则列表"""
    from core.models import PolicyRule

    query = db.query(PolicyRule)
    if rule_type:
        query = query.filter(PolicyRule.rule_type == rule_type)
    if tenant_id:
        query = query.filter(PolicyRule.tenant_id == tenant_id)
    query = query.filter(PolicyRule.is_enabled == is_enabled)

    total = query.count()
    rules = (
        query.order_by(PolicyRule.priority.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "rules": [
            {
                "id": r.id,
                "rule_name": r.rule_name,
                "rule_type": r.rule_type,
                "condition_expr": r.condition_expr,
                "action_type": r.action_type,
                "action_params": r.action_params,
                "priority": r.priority,
                "tenant_id": r.tenant_id,
                "is_enabled": r.is_enabled,
                "evidence_tier": r.evidence_tier,
                "description": r.description,
            }
            for r in rules
        ],
    }


@router.post("/rules", status_code=201)
def create_rule(
    req: RuleCreateRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    """创建新策略规则"""
    from core.rule_registry import RuleRegistry

    registry = RuleRegistry(db_session_factory=lambda: db)
    rule = registry.create_rule(db, req.model_dump(exclude_none=True))

    return {"rule": rule, "message": "Rule created successfully"}


@router.put("/rules/{rule_id}")
def update_rule(
    rule_id: int,
    req: RuleUpdateRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    """更新策略规则"""
    from core.rule_registry import RuleRegistry

    registry = RuleRegistry(db_session_factory=lambda: db)
    rule = registry.update_rule(db, rule_id, req.model_dump(exclude_none=True))

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return {"rule": rule, "message": "Rule updated successfully"}


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    """删除策略规则"""
    from core.rule_registry import RuleRegistry

    registry = RuleRegistry(db_session_factory=lambda: db)
    success = registry.delete_rule(db, rule_id)

    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")

    return {"message": "Rule deleted successfully"}


# ═══════════════════════════════════════════════
# 2. 策略测试 / 模拟
# ═══════════════════════════════════════════════

@router.post("/rules/{rule_id}/test")
def test_rule(
    rule_id: int,
    req: RuleTestRequest,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """测试规则: 给定上下文, 返回匹配结果"""
    from core.rule_registry import RuleRegistry

    registry = RuleRegistry(db_session_factory=lambda: db)
    registry.initialize()

    result = registry.test_rule(rule_id, req.context)
    return result


@router.post("/simulate")
def simulate_policy(
    req: SimulateRequest,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    完整策略模拟: 给定Event和Context, 返回ExecutionPlan
    不实际执行Agent, 仅返回决策结果
    """
    from core.policy_engine import PolicyEngine, Event, UserContext

    event_data = req.event
    ctx_data = req.context

    event = Event(
        type=event_data.get("type", "user_message"),
        content=event_data.get("content", ""),
        domain_keywords=event_data.get("domain_keywords", []),
    )

    context = UserContext(
        user_id=ctx_data.get("user_id", 0),
        tenant_id=ctx_data.get("tenant_id"),
        current_stage=ctx_data.get("current_stage", "S0"),
        risk_level=ctx_data.get("risk_level", "normal"),
        domain=ctx_data.get("domain", ""),
    )

    engine = PolicyEngine(db_session=db)
    engine.rule_registry.initialize()

    plan = engine.evaluate(event, context)

    return {
        "primary_agent": plan.primary_agent,
        "secondary_agents": plan.secondary_agents,
        "model": plan.model,
        "intensity": plan.intensity,
        "trace_id": plan.trace_id,
        "budget_status": plan.budget_status,
        "metadata": plan.metadata,
    }


# ═══════════════════════════════════════════════
# 3. Decision Trace 查询
# ═══════════════════════════════════════════════

@router.get("/traces/user/{user_id}")
def get_user_traces(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """查询用户的决策历史"""
    from core.decision_trace import DecisionTraceRecorder

    recorder = DecisionTraceRecorder(db)
    traces = recorder.query_by_user(user_id, limit=limit, offset=offset)

    return {"traces": traces, "total": len(traces)}


@router.get("/traces/{trace_id}")
def get_trace_detail(
    trace_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """获取可解释的决策追踪详情 (含自然语言说明)"""
    from core.decision_trace import DecisionTraceRecorder

    recorder = DecisionTraceRecorder(db)
    result = recorder.get_explainable_trace(trace_id)

    if not result:
        raise HTTPException(status_code=404, detail="Trace not found")

    return result


@router.get("/traces/agent/{agent_id}/stats")
def get_agent_trace_stats(
    agent_id: str,
    tenant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """查询某Agent的决策统计 — 专家用: '为什么我的Agent没被触发?'"""
    from core.decision_trace import DecisionTraceRecorder

    recorder = DecisionTraceRecorder(db)
    stats = recorder.query_by_agent(agent_id, tenant_id=tenant_id)

    return stats


# ═══════════════════════════════════════════════
# 4. 成本报告
# ═══════════════════════════════════════════════

@router.get("/cost/report")
def get_cost_report(
    tenant_id: str = Query(""),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """获取成本使用报告"""
    from core.cost_controller import CostController

    controller = CostController(db)
    report = controller.get_usage_report(tenant_id, user_id)

    return report


# ═══════════════════════════════════════════════
# 5. 规则热刷新
# ═══════════════════════════════════════════════

@router.post("/rules/refresh")
def refresh_rules(
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    """触发规则热刷新 (无需重启服务)"""
    from core.rule_registry import RuleRegistry

    registry = RuleRegistry(db_session_factory=lambda: db)
    registry.refresh()

    return {"message": "Rules refreshed successfully"}


# ═══════════════════════════════════════════════
# 6. 种子规则初始化
# ═══════════════════════════════════════════════

@router.post("/rules/seed")
def seed_rules(
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    """注入默认种子规则 (首次部署使用)"""
    from core.rule_registry import RuleRegistry, DEFAULT_SEED_RULES

    registry = RuleRegistry(db_session_factory=lambda: db)

    created = 0
    skipped = 0
    for seed in DEFAULT_SEED_RULES:
        try:
            registry.create_rule(db, seed)
            created += 1
        except Exception:
            skipped += 1

    return {
        "message": f"Seed complete: {created} created, {skipped} skipped",
        "total_seeds": len(DEFAULT_SEED_RULES),
    }
