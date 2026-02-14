# -*- coding: utf-8 -*-
"""
Agent API - 多Agent协作端点

提供Agent管理、任务运行、审核反馈、统计历史等接口。
前端 stores/agent.ts 消费这些端点。
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

import logging

from core.database import get_db
from api.dependencies import get_current_user, resolve_tenant_ctx

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])


# ---------------------------------------------------------------------------
# Pydantic 模型
# ---------------------------------------------------------------------------

class AgentRunRequest(BaseModel):
    agent_type: str = Field(..., description="Agent类型: metabolic/sleep/emotion/motivation等")
    user_id: str = Field(..., description="目标用户ID")
    context: Dict[str, Any] = Field(default_factory=dict)
    expected_output: str = Field("analysis", description="期望输出类型")
    priority: str = Field("normal", description="优先级: low/normal/high")
    coach_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    task_id: str
    reviewer_id: str
    reviewer_role: str
    feedback_type: str = Field(..., description="accept/reject/modify/rate")
    rating: Optional[int] = None
    comment: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# 内存存储 (轻量运行，后续可切换到数据库)
# ---------------------------------------------------------------------------

# 已注册的Agent信息
_registered_agents = [
    {
        "agent_id": "metabolic-agent",
        "agent_type": "metabolic",
        "name": "代谢管理Agent",
        "description": "负责血糖、体重、代谢相关分析与建议",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "sleep-agent",
        "agent_type": "sleep",
        "name": "睡眠管理Agent",
        "description": "负责睡眠质量分析、作息优化建议",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "emotion-agent",
        "agent_type": "emotion",
        "name": "情绪管理Agent",
        "description": "负责情绪评估、压力管理、心理支持",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "motivation-agent",
        "agent_type": "motivation",
        "name": "动机激励Agent",
        "description": "负责行为动机分析、阶段推进、激励策略",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "coaching-agent",
        "agent_type": "coaching",
        "name": "教练风格Agent",
        "description": "负责统一教练风格输出、回复合成",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "nutrition-agent",
        "agent_type": "nutrition",
        "name": "营养管理Agent",
        "description": "负责膳食分析、营养建议",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "exercise-agent",
        "agent_type": "exercise",
        "name": "运动康复Agent",
        "description": "负责运动方案、康复指导",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "tcm-agent",
        "agent_type": "tcm",
        "name": "中医养生Agent",
        "description": "负责中医体质分析、养生建议",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "crisis-agent",
        "agent_type": "crisis",
        "name": "危机干预Agent",
        "description": "负责高风险识别与危机干预",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "behavior-rx-agent",
        "agent_type": "behavior_rx",
        "name": "行为处方Agent",
        "description": "负责行为处方制定、习惯干预、依从性管理、戒烟戒酒等行为改变方案",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "weight-agent",
        "agent_type": "weight",
        "name": "体重管理Agent",
        "description": "负责体重/BMI监测、减重方案、身体成分分析、饮食运动联合干预",
        "version": "1.0.0",
        "status": "online",
    },
    {
        "agent_id": "cardiac-rehab-agent",
        "agent_type": "cardiac_rehab",
        "name": "心脏康复Agent",
        "description": "负责心血管疾病康复评估、运动处方、风险分层、术后康复指导",
        "version": "1.0.0",
        "status": "online",
    },
]

# 执行历史 (内存)
_execution_history: List[Dict[str, Any]] = []
# 待审核队列 (内存)
_pending_reviews: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _run_agent_task(req: AgentRunRequest,
                    tenant_ctx: Optional[Dict] = None) -> Dict[str, Any]:
    """
    执行Agent任务。
    优先 v6 MasterAgent (template-aware + tenant_ctx)，
    失败降级到 v0 MasterAgent，再失败返回模拟结果。
    """
    task_id = str(uuid.uuid4())[:8]
    started_at = datetime.now().isoformat()
    v6_used = False
    agents_used: List[str] = []

    # 优先: v6 MasterAgent (template-aware + tenant_ctx)
    try:
        from api.main import get_agent_master
        agent_master = get_agent_master()
        if agent_master:
            result = agent_master.process(
                user_id=int(req.user_id),
                message=f"[{req.agent_type}] {req.expected_output}",
                context=req.context,
                tenant_ctx=tenant_ctx,
            )
            suggestions = []
            resp_text = result.get("response", "")
            if resp_text:
                suggestions.append({
                    "id": f"sug-{task_id}",
                    "type": "action",
                    "priority": 7,
                    "text": resp_text,
                })
            agents_used = result.get("agents_used", [])
            v6_used = True
            output = {
                "task_id": task_id,
                "agent_id": f"{req.agent_type}-agent",
                "agent_type": req.agent_type,
                "output_type": req.expected_output,
                "confidence": 0.85,
                "suggestions": suggestions,
                "risk_flags": [],
                "need_human_review": False,
                "tenant_ctx_applied": tenant_ctx is not None,
                "agents_used": agents_used,
                "metadata": {
                    "processing_time_ms": result.get("processing_time_ms", 120),
                    "model_version": "agent-master-v6",
                    "llm_enhanced": result.get("llm_enhanced", False),
                },
                "created_at": started_at,
            }
        else:
            raise RuntimeError("v6 not available")
    except Exception:
        # 降级: v0 MasterAgent
        try:
            from core.master_agent import MasterAgent, UserInput, InputType
            agent = MasterAgent()
            user_input = UserInput(
                user_id=req.user_id,
                input_type=InputType.TEXT,
                content=f"[{req.agent_type}] {req.expected_output}",
                session_id=task_id,
            )
            result = agent.process(user_input)
            suggestions = []
            if hasattr(result, 'response') and result.response:
                suggestions.append({
                    "id": f"sug-{task_id}",
                    "type": "action",
                    "priority": 7,
                    "text": getattr(result.response, 'reply', str(result.response)),
                })
            output = {
                "task_id": task_id,
                "agent_id": f"{req.agent_type}-agent",
                "agent_type": req.agent_type,
                "output_type": req.expected_output,
                "confidence": 0.85,
                "suggestions": suggestions,
                "risk_flags": [],
                "need_human_review": False,
                "tenant_ctx_applied": False,
                "agents_used": [req.agent_type],
                "metadata": {
                    "processing_time_ms": 120,
                    "model_version": "xingjian-coach-v1.0",
                },
                "created_at": started_at,
            }
        except Exception:
            # Fallback: 生成模拟结果
            output = {
                "task_id": task_id,
                "agent_id": f"{req.agent_type}-agent",
                "agent_type": req.agent_type,
                "output_type": req.expected_output,
                "confidence": 0.75,
                "suggestions": [
                    {
                        "id": f"sug-{task_id}-1",
                        "type": "action",
                        "priority": 6,
                        "text": f"[{req.agent_type}] 基于用户 {req.user_id} 的数据分析，建议关注当前行为模式并持续跟踪。",
                        "rationale": "基于多维度行为数据综合判断",
                    },
                ],
                "risk_flags": [],
                "need_human_review": req.priority == "high",
                "review_reason": "高优先级任务需教练确认" if req.priority == "high" else None,
                "tenant_ctx_applied": False,
                "agents_used": [],
                "metadata": {
                    "processing_time_ms": 50,
                    "model_version": "fallback-v1.0",
                },
                "created_at": started_at,
            }

    # 记录执行历史
    record = {
        "execution_id": str(uuid.uuid4())[:8],
        "task_id": task_id,
        "agent_id": output["agent_id"],
        "agent_type": req.agent_type,
        "user_id": req.user_id,
        "status": "completed",
        "input_snapshot": req.dict(),
        "output_snapshot": output,
        "started_at": started_at,
        "completed_at": datetime.now().isoformat(),
    }
    _execution_history.append(record)

    # 如果需要审核，加入待审核队列
    if output.get("need_human_review"):
        _pending_reviews.append(record)

    return output


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------

@router.get("/api/v1/agent/list")
async def list_agents(
    current_user=Depends(get_current_user),
    tenant_ctx: Optional[Dict] = Depends(resolve_tenant_ctx),
):
    """获取所有已注册Agent列表 (优先从模板缓存读取)"""
    try:
        from core.agent_template_service import get_cached_templates, is_cache_loaded
        if is_cache_loaded():
            templates = get_cached_templates()
            enabled_set = set((tenant_ctx or {}).get("enabled_agents", []))
            agents = []
            for agent_id, tpl in templates.items():
                # 租户过滤: crisis 始终保留
                if enabled_set and agent_id != "crisis" and agent_id not in enabled_set:
                    continue
                agents.append({
                    "agent_id": f"{agent_id}-agent",
                    "agent_type": agent_id,
                    "name": tpl.get("display_name", agent_id),
                    "description": tpl.get("description", ""),
                    "version": "1.0.0",
                    "status": "online" if tpl.get("is_enabled") else "offline",
                    "agent_type_category": tpl.get("agent_type", "specialist"),
                    "is_preset": tpl.get("is_preset", True),
                    "keywords": tpl.get("keywords", []),
                })
            return {"success": True, "data": agents, "source": "template_cache"}
    except Exception:
        pass

    # 回退到硬编码列表
    return {"success": True, "data": _registered_agents, "source": "hardcoded"}


@router.post("/api/v1/agent/run")
async def run_agent(
    req: AgentRunRequest,
    current_user=Depends(get_current_user),
    tenant_ctx: Optional[Dict] = Depends(resolve_tenant_ctx),
    db: Session = Depends(get_db),
):
    """运行Agent任务 (v6 + tenant_ctx 优先, v0 降级)

    V4.0: Observer 白名单 — Observer 只能使用 TrustGuide Agent，每天限 3 轮。
    """
    # ── V4.0 Observer Trust Mode 白名单 ──────────────────
    if current_user.role.value == "observer":
        from core.models import JourneyState
        from core.agents.trust_guide_agent import TrustGuideAgent
        from datetime import date as date_type

        journey = db.query(JourneyState).filter(
            JourneyState.user_id == current_user.id
        ).first()
        if not journey:
            journey = JourneyState(user_id=current_user.id)
            db.add(journey)
            db.flush()

        # Enforce daily 3-turn limit
        today = date_type.today()
        if journey.observer_last_dialog_date == today:
            if journey.observer_dialog_count >= 3:
                return {
                    "success": False,
                    "error": "observer_daily_limit",
                    "message": "今天的对话次数已达上限（3次），明天再来聊吧。"
                              "记住——你来，我在。",
                }
        else:
            journey.observer_dialog_count = 0
            journey.observer_last_dialog_date = today

        # Run TrustGuide agent
        agent = TrustGuideAgent()
        from core.agents.base import AgentInput
        agent_input = AgentInput(
            user_id=current_user.id,
            message=req.expected_output,
            context={
                **req.context,
                "observer_dialog_count": journey.observer_dialog_count,
            },
        )
        result = agent.process(agent_input)

        # ── 审计日志 ──
        try:
            from core.models import UserActivityLog
            db.add(UserActivityLog(
                user_id=current_user.id,
                activity_type="agent.run",
                detail={
                    "agent_id": "trust_guide",
                    "observer_mode": True,
                    "dialog_count": journey.observer_dialog_count,
                },
                created_at=datetime.utcnow(),
            ))
        except Exception:
            logger.warning("审计日志写入失败")

        # Update dialog count
        journey.observer_dialog_count += 1
        db.commit()

        return {
            "success": True,
            "data": {
                "task_id": str(uuid.uuid4())[:8],
                "agent_id": "trust_guide",
                "agent_type": "trust_guide",
                "output_type": "trust_building",
                "confidence": result.confidence,
                "suggestions": [
                    {"id": "tg-1", "type": "trust", "priority": 10, "text": r}
                    for r in result.recommendations
                ],
                "risk_flags": [],
                "need_human_review": False,
                "observer_trust_mode": True,
                "dialog_remaining": max(0, 3 - journey.observer_dialog_count),
                "metadata": {
                    **result.metadata,
                    "model_version": "trust-guide-v4",
                },
                "created_at": datetime.now().isoformat(),
            },
        }
    # ── End Observer white-list ──────────────────────────

    # ── SafetyPipeline L1: 输入过滤 ──
    _safety_pipeline = None
    _input_category = "normal"
    try:
        from core.safety.pipeline import get_safety_pipeline
        _safety_pipeline = get_safety_pipeline()
        _input_result = _safety_pipeline.process_input(req.expected_output)
        _input_category = _input_result.category
        if not _input_result.safe:
            try:
                from core.models import SafetyLog
                db.add(SafetyLog(
                    user_id=current_user.id if hasattr(current_user, 'id') else None,
                    event_type="input_blocked",
                    severity=_input_result.severity,
                    input_text=req.expected_output[:500],
                    filter_details={"category": _input_result.category, "terms": _input_result.blocked_terms, "source": "agent_run"},
                ))
                db.commit()
            except Exception:
                logger.warning("SafetyLog write failed")
            _safe_reply = _safety_pipeline.get_crisis_response() if _input_result.category == "crisis" else "抱歉，您的消息包含不适当的内容，无法处理。"
            return {"success": False, "error": "safety_blocked", "message": _safe_reply, "safety_filtered": True}
    except Exception as e:
        logger.warning(f"SafetyPipeline input filter degraded: {e}")

    output = _run_agent_task(req, tenant_ctx=tenant_ctx)

    # ── SafetyPipeline L4: 输出过滤 ──
    try:
        if _safety_pipeline and isinstance(output, dict):
            _agent_text = output.get("output", "") or output.get("response", "") or ""
            if _agent_text:
                _output_result = _safety_pipeline.filter_output(_agent_text, _input_category)
                if _output_result.grade == "blocked":
                    _filtered_text = "抱歉，生成的内容未通过安全审核。如需专业建议请咨询医生。"
                elif _output_result.grade == "review_needed":
                    _filtered_text = _output_result.text
                else:
                    _filtered_text = _output_result.text
                if "output" in output:
                    output["output"] = _filtered_text
                elif "response" in output:
                    output["response"] = _filtered_text
                if _output_result.grade in ("blocked", "review_needed"):
                    try:
                        from core.models import SafetyLog
                        db.add(SafetyLog(
                            user_id=current_user.id if hasattr(current_user, 'id') else None,
                            event_type="output_blocked" if _output_result.grade == "blocked" else "output_review",
                            severity="high" if _output_result.grade == "blocked" else "medium",
                            input_text=req.expected_output[:500],
                            output_text=_agent_text[:500],
                            filter_details={"grade": _output_result.grade, "annotations": _output_result.annotations, "source": "agent_run"},
                        ))
                        db.commit()
                    except Exception:
                        logger.warning("SafetyLog write failed (agent output)")
    except Exception as e:
        logger.warning(f"SafetyPipeline output filter degraded: {e}")

    # ── 审计日志 ──
    try:
        from core.models import UserActivityLog
        db.add(UserActivityLog(
            user_id=current_user.id if hasattr(current_user, 'id') else 0,
            activity_type="agent.run",
            detail={
                "input_len": len(req.expected_output) if req.expected_output else 0,
                "tenant_ctx": bool(tenant_ctx),
            },
            created_at=datetime.utcnow(),
        ))
        db.commit()
    except Exception:
        logger.warning("审计日志写入失败")

    return {"success": True, "data": output}


@router.get("/api/v1/agent/pending-reviews")
async def get_pending_reviews(current_user=Depends(get_current_user)):
    """获取待审核的Agent输出"""
    return {"success": True, "data": _pending_reviews}


@router.post("/api/v1/agent/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    current_user=Depends(get_current_user),
):
    """提交Agent输出反馈（审核/评分）"""
    global _pending_reviews
    # 移除对应的待审核项
    before = len(_pending_reviews)
    _pending_reviews = [r for r in _pending_reviews if r["task_id"] != req.task_id]
    removed = before - len(_pending_reviews)

    # 更新执行历史中的状态
    for record in _execution_history:
        if record["task_id"] == req.task_id:
            record["feedback"] = req.dict()
            record["status"] = "reviewed"
            break

    return {
        "success": True,
        "message": f"反馈已记录，{removed} 条待审核项已处理",
    }


@router.get("/api/v1/agent/stats/{agent_id}")
async def get_agent_stats(
    agent_id: str,
    current_user=Depends(get_current_user),
):
    """获取Agent执行统计"""
    records = [r for r in _execution_history if r["agent_id"] == agent_id]
    total = len(records)
    reviewed = sum(1 for r in records if r.get("status") == "reviewed")
    avg_confidence = (
        sum(r["output_snapshot"]["confidence"] for r in records) / total
        if total > 0
        else 0
    )

    return {
        "success": True,
        "data": {
            "agent_id": agent_id,
            "total_executions": total,
            "reviewed": reviewed,
            "pending": total - reviewed,
            "avg_confidence": round(avg_confidence, 2),
        },
    }


@router.get("/api/v1/agent/history")
async def get_history(
    agent_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    current_user=Depends(get_current_user),
):
    """获取Agent执行历史"""
    results = _execution_history[:]
    if agent_id:
        results = [r for r in results if r["agent_id"] == agent_id]
    if user_id:
        results = [r for r in results if r["user_id"] == user_id]
    if status:
        results = [r for r in results if r["status"] == status]
    results = results[-limit:]
    return {"success": True, "data": results}


# ---------------------------------------------------------------------------
# Westworld Sim 注入端点 (测试用)
# ---------------------------------------------------------------------------

# 内存存储：治理日志、行为事件
_governance_log: List[Dict[str, Any]] = []
_behavior_events: List[Dict[str, Any]] = []


@router.post("/api/v1/agent/pending-reviews/inject")
async def inject_pending_review(
    data: Dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    """注入待审案例（仿真测试数据）"""
    record = {
        "execution_id": data.get("trace_id", str(uuid.uuid4())[:8]),
        "task_id": data.get("trace_id", str(uuid.uuid4())[:8]),
        "agent_id": "sim-inject",
        "agent_type": "sim",
        "user_id": data.get("patient_id", ""),
        "status": "pending",
        "input_snapshot": {},
        "output_snapshot": {
            "task_id": data.get("trace_id"),
            "confidence": 0.8,
            "original_l5_output": data.get("original_l5_output", ""),
            "narrative_l6_preview": data.get("narrative_l6_preview", ""),
            "raw_metrics": data.get("raw_metrics", {}),
            "baps_profile": data.get("baps_profile", {}),
            "governance_score": data.get("governance_score", {}),
        },
        "started_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
    }
    _pending_reviews.append(record)
    _execution_history.append(record)
    return {"success": True, "message": "pending review injected"}


@router.post("/api/v1/agent/events/inject")
async def inject_behavior_event(
    data: Dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    """注入行为事件（仿真测试数据）"""
    event = {
        "event_id": str(uuid.uuid4())[:8],
        "user_id": data.get("user_id", ""),
        "day": data.get("day", 0),
        "type": data.get("type", ""),
        "detail": data.get("detail", ""),
        "created_at": datetime.now().isoformat(),
    }
    _behavior_events.append(event)
    return {"success": True, "message": "event injected"}


@router.post("/api/v1/content-governance/audit-log/inject")
async def inject_governance_log(
    data: Dict[str, Any] = Body(...),
    current_user=Depends(get_current_user),
):
    """注入治理评分日志（仿真测试数据）"""
    entry = {
        "log_id": str(uuid.uuid4())[:8],
        "user_id": data.get("userId", ""),
        "day": data.get("day", 0),
        "safety": data.get("safety", 0),
        "accuracy": data.get("accuracy", 0),
        "empathy": data.get("empathy", 0),
        "actionable": data.get("actionable", 0),
        "passed": data.get("passed", False),
        "created_at": datetime.now().isoformat(),
    }
    _governance_log.append(entry)
    return {"success": True, "message": "governance log injected"}


@router.get("/api/v1/agent/status")
async def agent_system_status(current_user=Depends(get_current_user)):
    """获取多Agent系统整体状态"""
    # 检查 v0 MasterAgent 可用性
    master_available = False
    try:
        from core.master_agent import MasterAgent
        _ = MasterAgent()
        master_available = True
    except Exception:
        pass

    # 检查 v6 AgentMaster 可用性
    agent_master_v6 = False
    v6_agent_count = 0
    try:
        from api.main import get_agent_master
        am = get_agent_master()
        if am:
            agent_master_v6 = True
            v6_agent_count = len(am._agents)
    except Exception:
        pass

    # 模板缓存
    template_count = 0
    try:
        from core.agent_template_service import get_cached_templates, is_cache_loaded
        if is_cache_loaded():
            template_count = len(get_cached_templates())
    except Exception:
        pass

    # 检查 Scheduler 状态
    scheduler_running = False
    try:
        from core.scheduler import HAS_APSCHEDULER
        scheduler_running = HAS_APSCHEDULER
    except Exception:
        pass

    online_agents = [a for a in _registered_agents if a["status"] == "online"]

    return {
        "success": True,
        "data": {
            "master_agent": master_available,
            "agent_master_v6": agent_master_v6,
            "v6_agent_count": v6_agent_count,
            "template_cache_count": template_count,
            "scheduler": scheduler_running,
            "agents_online": len(online_agents),
            "agents_total": len(_registered_agents),
            "pending_reviews": len(_pending_reviews),
            "total_executions": len(_execution_history),
        },
    }
