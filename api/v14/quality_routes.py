"""
行为健康数字平台 - 质量审计 API
Quality Audit API Service

[v14-NEW] 质量审计模块

路由前缀: /api/v2/quality/
（整合到v14 API体系）

特点：
- 异步后台审计，不阻塞前端
- 支持单条和批量审计
- 与Trace系统深度绑定
- 审计结果可供专家二次复核
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
import asyncio

from quality.schema import (
    AuditRequest,
    BatchAuditRequest,
    QualityAuditResult,
    AuditGrade
)
from quality.llm_judge import LLMJudge, BatchLLMJudge, get_llm_judge


router = APIRouter(prefix="/quality", tags=["quality"])


# ============================================
# 内存存储（生产环境应替换为数据库）
# ============================================
_audit_results: Dict[str, QualityAuditResult] = {}
_pending_audits: Dict[str, str] = {}  # trace_id -> status


# ============================================
# API端点
# ============================================

@router.post("/audit")
async def start_quality_audit(
    payload: AuditRequest,
    background_tasks: BackgroundTasks,
    sync: bool = Query(False, description="是否同步执行（阻塞等待结果）")
):
    """
    启动质量审计
    
    - sync=False (默认): 异步执行，立即返回，结果通过 /audit/result 查询
    - sync=True: 同步执行，等待结果返回
    
    Args:
        payload: 审计请求
        sync: 是否同步执行
    
    Returns:
        异步: {"status": "audit_started", "trace_id": "..."}
        同步: QualityAuditResult
    """
    trace_id = payload.trace_id
    
    if not trace_id:
        raise HTTPException(status_code=400, detail="Missing trace_id")
    
    if not payload.response_text:
        raise HTTPException(status_code=400, detail="Missing response_text")
    
    # 同步执行
    if sync:
        judge = get_llm_judge()
        result = await judge.evaluate_from_request(payload)
        _audit_results[trace_id] = result
        return result.to_dict()
    
    # 异步执行
    async def run_audit():
        try:
            _pending_audits[trace_id] = "running"
            judge = get_llm_judge()
            result = await judge.evaluate_from_request(payload)
            _audit_results[trace_id] = result
            _pending_audits[trace_id] = "completed"
            logger.info(f"[Quality] 审计完成: trace={trace_id} grade={result.final_grade.value}")
        except Exception as e:
            _pending_audits[trace_id] = f"error: {str(e)}"
            logger.error(f"[Quality] 审计失败: trace={trace_id} error={e}")
    
    _pending_audits[trace_id] = "pending"
    background_tasks.add_task(run_audit)
    
    return {
        "status": "audit_started",
        "trace_id": trace_id,
        "message": "审计已在后台启动，请稍后查询结果"
    }


@router.post("/audit-batch")
async def batch_quality_audit(
    payload: BatchAuditRequest,
    background_tasks: BackgroundTasks
):
    """
    批量质量审计（异步）
    
    Args:
        payload: 批量审计请求
    
    Returns:
        批量审计状态
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="No items to audit")
    
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    trace_ids = [item.trace_id for item in payload.items]
    
    async def run_batch_audit():
        judge = get_llm_judge()
        batch_judge = BatchLLMJudge(judge, concurrency=3)
        
        for trace_id in trace_ids:
            _pending_audits[trace_id] = "running"
        
        try:
            results = await batch_judge.evaluate_batch(payload.items)
            for result in results:
                _audit_results[result.trace_id] = result
                _pending_audits[result.trace_id] = "completed"
            
            logger.info(f"[Quality] 批量审计完成: batch={batch_id} count={len(results)}")
        except Exception as e:
            for trace_id in trace_ids:
                _pending_audits[trace_id] = f"error: {str(e)}"
            logger.error(f"[Quality] 批量审计失败: batch={batch_id} error={e}")
    
    for trace_id in trace_ids:
        _pending_audits[trace_id] = "pending"
    
    background_tasks.add_task(run_batch_audit)
    
    return {
        "status": "batch_started",
        "batch_id": batch_id,
        "trace_ids": trace_ids,
        "count": len(trace_ids),
        "priority": payload.priority
    }


@router.get("/audit/result/{trace_id}")
async def get_audit_result(trace_id: str):
    """
    获取审计结果
    
    Args:
        trace_id: 追踪ID
    
    Returns:
        审计结果或状态
    """
    # 检查是否有结果
    if trace_id in _audit_results:
        return {
            "status": "completed",
            "result": _audit_results[trace_id].to_dict()
        }
    
    # 检查是否在处理中
    if trace_id in _pending_audits:
        status = _pending_audits[trace_id]
        return {
            "status": status,
            "trace_id": trace_id,
            "message": "审计进行中" if status == "running" else status
        }
    
    raise HTTPException(status_code=404, detail=f"Audit not found: {trace_id}")


@router.get("/audit/status")
async def get_audit_status():
    """
    获取审计系统状态
    
    Returns:
        系统状态统计
    """
    # 统计各状态数量
    status_counts = {}
    for status in _pending_audits.values():
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # 统计各等级数量
    grade_counts = {}
    for result in _audit_results.values():
        grade = result.final_grade.value
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    
    return {
        "total_results": len(_audit_results),
        "pending_audits": len(_pending_audits),
        "status_distribution": status_counts,
        "grade_distribution": grade_counts,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/audit/list")
async def list_audit_results(
    grade: Optional[str] = Query(None, description="筛选等级 (pass/review/fail)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    列出审计结果
    
    Args:
        grade: 筛选等级
        limit: 返回数量
        offset: 偏移量
    
    Returns:
        审计结果列表
    """
    results = list(_audit_results.values())
    
    # 按时间倒序
    results.sort(key=lambda r: r.audited_at, reverse=True)
    
    # 筛选等级
    if grade:
        try:
            target_grade = AuditGrade(grade)
            results = [r for r in results if r.final_grade == target_grade]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid grade: {grade}")
    
    # 分页
    total = len(results)
    results = results[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [r.to_dict() for r in results]
    }


@router.delete("/audit/result/{trace_id}")
async def delete_audit_result(trace_id: str):
    """
    删除审计结果
    
    Args:
        trace_id: 追踪ID
    """
    if trace_id in _audit_results:
        del _audit_results[trace_id]
        if trace_id in _pending_audits:
            del _pending_audits[trace_id]
        return {"status": "deleted", "trace_id": trace_id}
    
    raise HTTPException(status_code=404, detail=f"Audit not found: {trace_id}")


# ============================================
# 专项审计端点
# ============================================

@router.post("/audit/safety-check")
async def safety_focused_audit(
    response_text: str,
    trace_id: Optional[str] = None
):
    """
    安全性专项审计
    
    快速检查响应是否存在安全风险
    """
    from quality.judge_prompt import build_safety_focused_prompt
    
    trace_id = trace_id or f"safety_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    judge = get_llm_judge()
    prompt = build_safety_focused_prompt(response_text)
    
    try:
        raw_output = await judge._call_llm(prompt)
        data = judge._parse_llm_output(raw_output)
        
        return {
            "trace_id": trace_id,
            "is_safe": data.get("is_safe", True),
            "risk_level": data.get("risk_level", "unknown"),
            "issues": data.get("issues", []),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[Quality] 安全检查失败: {e}")
        return {
            "trace_id": trace_id,
            "is_safe": None,
            "risk_level": "unknown",
            "issues": [f"检查失败: {str(e)}"],
            "timestamp": datetime.now().isoformat()
        }


# ============================================
# 与v14 Agent系统集成
# ============================================

@router.post("/audit/with-v14-context")
async def audit_with_v14_context(
    payload: AuditRequest,
    include_rhythm: bool = Query(True, description="是否获取节律状态"),
    include_triggers: bool = Query(True, description="是否获取触发事件")
):
    """
    带v14上下文的审计
    
    自动获取用户的节律状态和触发事件
    """
    try:
        from core.v14 import (
            is_feature_enabled,
            get_rhythm_engine,
            get_trigger_router
        )
        
        # 获取节律状态
        if include_rhythm and is_feature_enabled("ENABLE_RHYTHM_MODEL") and payload.user_id:
            rhythm_engine = get_rhythm_engine()
            if rhythm_engine:
                phase = rhythm_engine.get_current_phase(payload.user_id)
                if phase:
                    payload.rhythm_phase = phase.value
        
        # 获取触发事件（这里简化处理）
        if include_triggers and is_feature_enabled("ENABLE_TRIGGER_EVENT_ROUTING"):
            # 实际应从数据库获取
            payload.trigger_events = []
        
    except ImportError:
        logger.debug("[Quality] v14模块未加载，跳过上下文获取")
    
    # 执行审计
    judge = get_llm_judge()
    result = await judge.evaluate_from_request(payload)
    _audit_results[payload.trace_id] = result
    
    return result.to_dict()
