"""
Expert 飞轮 API — 统一审核工作台 (Real DB)
端点:
  GET  /api/v1/expert/audit-queue       → 审核队列(含安全检查)
  POST /api/v1/expert/audit/:id/verdict → 提交裁决
  GET  /api/v1/expert/quality-metrics   → 质量指标
  GET  /api/v1/expert/agent-anomalies   → Agent异常列表
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from api.dependencies import require_coach_or_admin

logger = logging.getLogger("expert_flywheel")

router = APIRouter(prefix="/api/v1/expert", tags=["expert-flywheel"])


def _relative_time(dt: datetime) -> str:
    """Format datetime as relative time string."""
    delta = datetime.utcnow() - dt
    secs = delta.total_seconds()
    if secs < 60:
        return "刚刚"
    if secs < 3600:
        return f"{int(secs / 60)}分钟前"
    if secs < 86400:
        return f"{int(secs / 3600)}小时前"
    return f"{delta.days}天前"


# Agent display name lookup (for when agent_templates table is missing)
_AGENT_NAMES = {
    "health_assistant": "健康助手", "crisis_responder": "危机响应",
    "nutrition_guide": "营养指导", "exercise_guide": "运动指导",
    "sleep_guide": "睡眠指导", "emotion_support": "情绪支持",
    "tcm_wellness": "中医养生", "motivation_support": "动机支持",
    "behavior_coach": "行为教练", "rx_composer": "处方编写",
    "risk_detector": "风险检测", "quality_auditor": "质量审计",
    "tcm_ortho_expert": "中医骨科专家", "pain_management_expert": "疼痛管理专家",
}

# Map safety event_type → anomaly_type
_EVENT_ANOMALY_MAP = {
    "medical_boundary": "boundary_violation",
    "boundary_violation": "boundary_violation",
    "hallucination": "hallucination",
    "slow_response": "slow_response",
    "stage_mismatch": "stage_mismatch",
    "crisis": "boundary_violation",
    "content_violation": "boundary_violation",
    "pii_detected": "boundary_violation",
}


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════
class SafetyFlag(BaseModel):
    rule: str           # S1-S6
    description: str
    action: str         # 已处理的动作


class DialogueMessage(BaseModel):
    id: int
    role: Literal["user", "ai"]
    text: str
    modality: str = "text"


class RxReviewField(BaseModel):
    key: str
    label: str
    value: str
    flagged: bool = False
    flag_reason: Optional[str] = None


class DecisionStep(BaseModel):
    step: int
    action: str
    detail: str
    ok: bool


class AuditHistory(BaseModel):
    verdict: str
    by: str
    time: str


class AuditItem(BaseModel):
    """审核项"""
    id: str
    title: str
    type: Literal["ai_dialogue", "prescription", "agent_behavior", "content", "safety"]
    type_icon: str
    agent: str
    user_name: str
    user_stage: str
    risk: Literal["critical", "high", "medium", "low"]
    time: str

    # 根据type填充
    dialogue: Optional[list[DialogueMessage]] = None
    safety_flags: list[SafetyFlag] = []
    rx_fields: Optional[list[RxReviewField]] = None
    evidence_level: Optional[int] = None
    decision_steps: Optional[list[DecisionStep]] = None
    history: list[AuditHistory] = []


class AuditQueueResponse(BaseModel):
    items: list[AuditItem]
    total: int
    by_type: dict[str, int]
    by_risk: dict[str, int]


class VerdictRequest(BaseModel):
    verdict: Literal["pass", "revise", "block"]
    score: int = 0              # 1-5质量评分
    issues: list[str] = []      # 问题标签
    note: Optional[str] = None


class VerdictResponse(BaseModel):
    success: bool
    audit_id: str
    verdict: str
    next_id: Optional[str] = None
    message: str = ""


class QualityMetricsResponse(BaseModel):
    today_audited: int
    pass_rate: float
    pending_queue: int
    redline_blocked: int
    agent_anomaly_count: int
    by_type: dict[str, dict]    # {type: {audited, pass_rate}}
    trend_7d: list[dict]        # 7天趋势


class AgentAnomaly(BaseModel):
    agent_id: str
    agent_name: str
    anomaly_type: str           # slow_response | hallucination | boundary_violation | stage_mismatch
    severity: str               # critical | warning | info
    description: str
    sample_count: int           # 异常样本数
    first_seen: str
    last_seen: str


# ═══════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════
_TYPE_ICONS = {
    "ai_dialogue": "💬", "prescription": "📋",
    "agent_behavior": "🤖", "content": "📄", "safety": "🛡️",
}

_VALID_TYPES = {"ai_dialogue", "prescription", "agent_behavior", "content", "safety"}
_VALID_RISKS = {"critical", "high", "medium", "low"}


def _parse_audit_type(raw: Optional[str]) -> str:
    """Normalize audit_type to valid enum value."""
    if raw and raw in _VALID_TYPES:
        return raw
    return "safety"


def _parse_risk_level(raw: Optional[str]) -> str:
    """Normalize risk_level to valid enum value."""
    if raw and raw in _VALID_RISKS:
        return raw
    return "medium"


def _build_audit_item_from_row(row: dict) -> AuditItem:
    """Construct an AuditItem from an expert_audit_records row."""
    audit_type = _parse_audit_type(row.get("audit_type"))
    risk = _parse_risk_level(row.get("risk_level"))
    agent_id = row.get("agent_id") or "unknown"
    content_snapshot = row.get("content_snapshot") or {}
    safety_flags_raw = row.get("safety_flags") or []
    created_at = row.get("created_at")

    # Build dialogue from content_snapshot if available
    dialogue = None
    if audit_type == "ai_dialogue" and isinstance(content_snapshot, dict):
        msgs = content_snapshot.get("dialogue") or content_snapshot.get("messages") or []
        if msgs:
            dialogue = [
                DialogueMessage(
                    id=i + 1,
                    role="ai" if m.get("role") == "assistant" else "user",
                    text=m.get("text") or m.get("content") or "",
                )
                for i, m in enumerate(msgs[:10])
            ]

    # Build rx_fields from content_snapshot
    rx_fields = None
    if audit_type == "prescription" and isinstance(content_snapshot, dict):
        raw_fields = content_snapshot.get("rx_fields") or content_snapshot.get("fields") or []
        if raw_fields:
            rx_fields = [
                RxReviewField(
                    key=f.get("key", f"field_{i}"),
                    label=f.get("label", ""),
                    value=str(f.get("value", "")),
                    flagged=f.get("flagged", False),
                    flag_reason=f.get("flag_reason"),
                )
                for i, f in enumerate(raw_fields[:10])
            ]

    # Build safety flags
    flags = []
    if isinstance(safety_flags_raw, list):
        for sf in safety_flags_raw[:6]:
            if isinstance(sf, dict):
                flags.append(SafetyFlag(
                    rule=sf.get("rule", "S1"),
                    description=sf.get("description", ""),
                    action=sf.get("action", ""),
                ))
    elif isinstance(safety_flags_raw, dict):
        for rule, desc in safety_flags_raw.items():
            flags.append(SafetyFlag(rule=rule, description=str(desc), action=""))

    # Title
    user_text = ""
    if isinstance(content_snapshot, dict):
        user_text = content_snapshot.get("user_name") or content_snapshot.get("title") or ""
    title = user_text or f"{agent_id} 审核项"

    return AuditItem(
        id=str(row.get("id", "")),
        title=title,
        type=audit_type,
        type_icon=_TYPE_ICONS.get(audit_type, "🔍"),
        agent=agent_id,
        user_name=content_snapshot.get("user_name", "") if isinstance(content_snapshot, dict) else "",
        user_stage=content_snapshot.get("user_stage", "") if isinstance(content_snapshot, dict) else "",
        risk=risk,
        time=created_at.strftime("%H:%M") if created_at else "",
        dialogue=dialogue,
        safety_flags=flags,
        rx_fields=rx_fields,
        evidence_level=content_snapshot.get("evidence_level") if isinstance(content_snapshot, dict) else None,
    )


# ═══════════════════════════════════════════════════
# GET /audit-queue
# ═══════════════════════════════════════════════════
@router.get("/audit-queue", response_model=AuditQueueResponse)
async def get_audit_queue(
    type_filter: Optional[str] = Query(None),
    risk_filter: Optional[str] = Query(None),
    agent_filter: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter: 'completed' for reviewed items, default=pending"),
    expert_user=Depends(require_coach_or_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """获取审核队列 — 从 expert_audit_records 查询未审核项 (status=completed 返回已审核)"""
    try:
        # Build dynamic WHERE clauses
        if status == "completed":
            conditions = ["verdict IS NOT NULL"]
        else:
            conditions = ["verdict IS NULL"]
        params: dict = {}

        if type_filter and type_filter in _VALID_TYPES:
            conditions.append("audit_type = :type_filter")
            params["type_filter"] = type_filter

        if risk_filter and risk_filter in _VALID_RISKS:
            conditions.append("risk_level = :risk_filter")
            params["risk_filter"] = risk_filter

        if agent_filter and agent_filter != "all":
            conditions.append("agent_id = :agent_filter")
            params["agent_filter"] = agent_filter

        where_clause = " AND ".join(conditions)

        r = await db.execute(text(f"""
            SELECT id, audit_type, agent_id, risk_level,
              content_snapshot, safety_flags, verdict, score, created_at
            FROM expert_audit_records
            WHERE {where_clause}
            ORDER BY CASE risk_level
              WHEN 'critical' THEN 0 WHEN 'high' THEN 1
              WHEN 'medium' THEN 2 ELSE 3
            END, created_at ASC
        """), params)

        items = []
        for row in r.mappings():
            items.append(_build_audit_item_from_row(dict(row)))

        # If empty, also check safety_logs for unresolved high-severity events
        if not items:
            try:
                r2 = await db.execute(text("""
                    SELECT id, event_type, severity, input_text, created_at,
                      filter_details
                    FROM safety_logs
                    WHERE resolved = false AND severity IN ('high', 'critical')
                    ORDER BY created_at DESC LIMIT 20
                """))
                for row in r2.mappings():
                    et = row["event_type"] or "safety"
                    items.append(AuditItem(
                        id=f"sl_{row['id']}",
                        title=f"安全事件: {et}",
                        type="safety",
                        type_icon="🛡️",
                        agent=(row.get("filter_details") or {}).get("agent_id", "system")
                            if isinstance(row.get("filter_details"), dict) else "system",
                        user_name="",
                        user_stage="",
                        risk=_parse_risk_level(row["severity"]),
                        time=row["created_at"].strftime("%H:%M") if row["created_at"] else "",
                        safety_flags=[SafetyFlag(
                            rule=et, description=row["input_text"][:80] if row["input_text"] else "",
                            action="待审核",
                        )],
                    ))
            except Exception:
                pass

        # Aggregate by_type and by_risk
        by_type: dict[str, int] = {t: 0 for t in _VALID_TYPES}
        by_risk: dict[str, int] = {r: 0 for r in _VALID_RISKS}
        for item in items:
            by_type[item.type] = by_type.get(item.type, 0) + 1
            by_risk[item.risk] = by_risk.get(item.risk, 0) + 1

        return AuditQueueResponse(
            items=items, total=len(items),
            by_type=by_type, by_risk=by_risk,
        )
    except Exception as e:
        logger.warning("audit-queue fallback: %s", e)
        return AuditQueueResponse(items=[], total=0, by_type={}, by_risk={})


# ═══════════════════════════════════════════════════
# POST /audit/{audit_id}/verdict
# ═══════════════════════════════════════════════════
@router.post("/audit/{audit_id}/verdict", response_model=VerdictResponse)
async def submit_verdict(
    audit_id: str = Path(...),
    req: VerdictRequest = ...,
    expert_user=Depends(require_coach_or_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """提交审核裁决"""
    try:
        verdict_labels = {"pass": "通过", "revise": "退回", "block": "拦截"}

        if audit_id.startswith("sl_"):
            # Safety log item — mark as resolved
            sl_id = int(audit_id[3:])
            await db.execute(
                text("UPDATE safety_logs SET resolved=true WHERE id=:id"),
                {"id": sl_id},
            )
        else:
            # Expert audit record
            result = await db.execute(text("""
                UPDATE expert_audit_records
                SET verdict=:verdict, score=:score, issues=:issues,
                    note=:note, reviewed_at=NOW()
                WHERE id=:audit_id AND verdict IS NULL
            """), {
                "verdict": req.verdict,
                "score": req.score,
                "issues": req.issues,
                "note": req.note,
                "audit_id": audit_id,
            })

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="审核项不存在或已审核")

        await db.commit()

        # Find next unreviewed item
        next_id = None
        try:
            r = await db.execute(text("""
                SELECT id FROM expert_audit_records
                WHERE verdict IS NULL
                ORDER BY CASE risk_level
                  WHEN 'critical' THEN 0 WHEN 'high' THEN 1
                  WHEN 'medium' THEN 2 ELSE 3
                END, created_at ASC
                LIMIT 1
            """))
            next_row = r.mappings().first()
            if next_row:
                next_id = str(next_row["id"])
        except Exception:
            pass

        return VerdictResponse(
            success=True,
            audit_id=audit_id,
            verdict=req.verdict,
            next_id=next_id,
            message="已" + verdict_labels.get(req.verdict, req.verdict),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("submit_verdict error: %s", e)
        await db.rollback()
        return VerdictResponse(
            success=False, audit_id=audit_id, verdict=req.verdict,
            message=f"操作失败: {e}",
        )


# ═══════════════════════════════════════════════════
# GET /quality-metrics
# ═══════════════════════════════════════════════════
@router.get("/quality-metrics", response_model=QualityMetricsResponse)
async def get_quality_metrics(
    expert_user=Depends(require_coach_or_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """质量指标总览"""
    try:
        today = date.today()

        # Overall metrics
        r = await db.execute(text("""
            SELECT
              COUNT(*) FILTER (WHERE reviewed_at >= :today) as today_audited,
              CASE WHEN COUNT(*) FILTER (WHERE reviewed_at >= :today) > 0
                THEN ROUND(
                  COUNT(*) FILTER (WHERE verdict='pass' AND reviewed_at >= :today)::numeric /
                  COUNT(*) FILTER (WHERE reviewed_at >= :today),
                  2)
                ELSE 0.0
              END as pass_rate,
              COUNT(*) FILTER (WHERE verdict IS NULL) as pending_queue,
              COUNT(*) FILTER (WHERE verdict = 'block') as redline_blocked
            FROM expert_audit_records
        """), {"today": today})
        row = r.mappings().first()

        today_audited = row["today_audited"] if row else 0
        pass_rate = float(row["pass_rate"] or 0) if row else 0.0
        pending_queue = row["pending_queue"] if row else 0
        redline_blocked = row["redline_blocked"] if row else 0

        # Agent anomaly count from safety_logs (high/critical in 24h)
        r = await db.execute(text("""
            SELECT COUNT(DISTINCT COALESCE(filter_details->>'agent_id', event_type))
            FROM safety_logs
            WHERE severity IN ('high', 'critical')
              AND created_at >= NOW() - INTERVAL '24 hours'
        """))
        agent_anomaly_count = r.scalar() or 0

        # By type breakdown
        r = await db.execute(text("""
            SELECT audit_type,
              COUNT(*) FILTER (WHERE reviewed_at >= :today) as audited,
              CASE WHEN COUNT(*) FILTER (WHERE reviewed_at >= :today) > 0
                THEN ROUND(
                  COUNT(*) FILTER (WHERE verdict='pass' AND reviewed_at >= :today)::numeric /
                  COUNT(*) FILTER (WHERE reviewed_at >= :today),
                  2)
                ELSE 0.0
              END as pass_rate
            FROM expert_audit_records
            GROUP BY audit_type
        """), {"today": today})

        by_type = {}
        for trow in r.mappings():
            at = trow["audit_type"] or "other"
            by_type[at] = {
                "audited": trow["audited"] or 0,
                "pass_rate": float(trow["pass_rate"] or 0),
            }

        # 7-day trend
        r = await db.execute(text("""
            SELECT reviewed_at::date as review_date,
              COUNT(*) as audited,
              CASE WHEN COUNT(*) > 0
                THEN ROUND(COUNT(*) FILTER (WHERE verdict='pass')::numeric / COUNT(*), 2)
                ELSE 0.0
              END as pass_rate
            FROM expert_audit_records
            WHERE reviewed_at >= :seven_days_ago AND reviewed_at IS NOT NULL
            GROUP BY reviewed_at::date
            ORDER BY review_date
        """), {"seven_days_ago": today - timedelta(days=7)})

        trend_7d = []
        for trow in r.mappings():
            trend_7d.append({
                "date": trow["review_date"].strftime("%m-%d") if trow["review_date"] else "",
                "audited": trow["audited"] or 0,
                "pass_rate": float(trow["pass_rate"] or 0),
            })

        return QualityMetricsResponse(
            today_audited=today_audited,
            pass_rate=pass_rate,
            pending_queue=pending_queue,
            redline_blocked=redline_blocked,
            agent_anomaly_count=agent_anomaly_count,
            by_type=by_type,
            trend_7d=trend_7d,
        )
    except Exception as e:
        logger.warning("quality-metrics fallback: %s", e)
        return QualityMetricsResponse(
            today_audited=0, pass_rate=0.0, pending_queue=0,
            redline_blocked=0, agent_anomaly_count=0,
            by_type={}, trend_7d=[],
        )


# ═══════════════════════════════════════════════════
# GET /agent-anomalies
# ═══════════════════════════════════════════════════
@router.get("/agent-anomalies", response_model=list[AgentAnomaly])
async def get_agent_anomalies(
    expert_user=Depends(require_coach_or_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Agent异常列表 — 供Expert审查Agent行为"""
    try:
        r = await db.execute(text("""
            SELECT COALESCE(filter_details->>'agent_id', 'unknown') as agent_id,
              event_type, severity, COUNT(*) as sample_count,
              MIN(created_at) as first_seen, MAX(created_at) as last_seen
            FROM safety_logs
            WHERE severity IN ('high', 'critical')
              AND created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY 1, event_type, severity
            ORDER BY sample_count DESC
        """))

        result = []
        for row in r.mappings():
            aid = row["agent_id"] or "unknown"
            et = row["event_type"] or "unknown"
            severity = row["severity"] or "warning"
            if severity not in ("critical", "warning", "info"):
                severity = "warning"

            anomaly_type = _EVENT_ANOMALY_MAP.get(et.lower(), "boundary_violation")

            # Look up agent display name
            agent_name = _AGENT_NAMES.get(aid)
            if not agent_name:
                # Try DB lookup
                try:
                    nr = await db.execute(text(
                        "SELECT display_name FROM agent_templates WHERE agent_id=:aid"
                    ), {"aid": aid})
                    nrow = nr.scalar()
                    agent_name = nrow or aid
                except Exception:
                    agent_name = aid

            first_seen = row["first_seen"]
            last_seen = row["last_seen"]

            result.append(AgentAnomaly(
                agent_id=aid,
                agent_name=agent_name,
                anomaly_type=anomaly_type,
                severity=severity,
                description=f"近24h内{row['sample_count']}次{et}事件",
                sample_count=row["sample_count"] or 0,
                first_seen=first_seen.isoformat() if first_seen else "",
                last_seen=last_seen.isoformat() if last_seen else "",
            ))

        return result
    except Exception as e:
        logger.warning("agent-anomalies fallback: %s", e)
        return []
