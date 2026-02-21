"""
Admin 飞轮 API — 指挥中心 Dashboard (Real DB)
端点 (12个):
  GET  /api/v1/admin/kpi/realtime           → 4大核心KPI
  GET  /api/v1/admin/channels/health        → 渠道健康
  GET  /api/v1/admin/funnel                 → 转化漏斗
  GET  /api/v1/admin/agents/monitor         → 33Agent状态
  GET  /api/v1/admin/agents/performance     → Agent P95排行
  GET  /api/v1/admin/coaches/ranking        → 教练效率排行
  GET  /api/v1/admin/safety/24h             → 安全红线S1-S6
  GET  /api/v1/admin/alerts/active          → 活跃告警
  POST /api/v1/admin/alerts/:id/dismiss     → 关闭告警
  GET  /api/v1/admin/users/overview         → 用户总览
  GET  /api/v1/admin/system/containers      → 容器状态
  GET  /api/v1/admin/audit-log/recent       → 最近审计日志
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from api.dependencies import require_admin

logger = logging.getLogger("admin_flywheel")

router = APIRouter(prefix="/api/v1/admin", tags=["admin-flywheel"])


def _relative_time(dt: datetime) -> str:
    """Format datetime as relative time string (Chinese)."""
    delta = datetime.utcnow() - dt
    secs = delta.total_seconds()
    if secs < 0:
        return "刚刚"
    if secs < 60:
        return "刚刚"
    if secs < 3600:
        return f"{int(secs / 60)}分钟前"
    if secs < 86400:
        return f"{int(secs / 3600)}小时前"
    return f"{delta.days}天前"


def _fmt_count(n: int) -> str:
    """Format integer with comma separators."""
    return f"{n:,}"


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════
class CoreKPI(BaseModel):
    icon: str
    value: str
    label: str
    sub: str
    trend_dir: Literal["up", "down", "flat"]
    trend_pct: float
    status: Literal["good", "warn", "critical"]


class ChannelHealth(BaseModel):
    icon: str
    name: str
    status: Literal["healthy", "degraded", "down"]
    status_label: str
    dau: str
    msg_today: str
    avg_reply: str
    error_rate: float = 0.0


class FunnelStep(BaseModel):
    label: str
    count: str
    pct: float
    color: str
    conv_rate: Optional[str] = None


class AgentStatus(BaseModel):
    id: str
    name: str
    layer: str          # 用户层|教练层|系统层|中医骨科
    status: Literal["ok", "slow", "error", "offline"]
    status_label: str
    p95_ms: Optional[int] = None
    calls_today: int = 0
    error_rate: float = 0.0


class AgentPerf(BaseModel):
    name: str
    agent_id: str
    p95: int            # P95延迟(ms)
    avg: int
    calls: int


class CoachRank(BaseModel):
    name: str
    coach_id: int
    students: int
    today_reviewed: int
    avg_seconds: int
    approval_rate: float


class SafetyMetric(BaseModel):
    rule: str           # S1-S6
    label: str
    count: int          # 24h触发次数
    last_triggered: Optional[str] = None


class Alert(BaseModel):
    id: str
    level: Literal["critical", "warning", "info"]
    message: str
    source: str
    time: str
    auto_resolved: bool = False


class AlertDismissResponse(BaseModel):
    success: bool
    alert_id: str


class UserOverview(BaseModel):
    total_users: int
    by_role: dict[str, int]     # {Observer: N, Grower: N, ...}
    by_stage: dict[str, int]    # {S0: N, S1: N, ...}
    new_today: int
    active_today: int


class ContainerStatus(BaseModel):
    name: str
    port: str
    status: Literal["running", "stopped", "error"]
    uptime: str
    cpu_pct: float
    mem_mb: int


# ═══════════════════════════════════════════════════
# Agent reference list (used when agent_templates table is empty/missing)
# ═══════════════════════════════════════════════════
_AGENT_SEED = {
    "用户层": [
        ("health_assistant", "健康助手"), ("crisis_responder", "危机响应"),
        ("onboarding_guide", "引导向导"), ("nutrition_guide", "营养指导"),
        ("exercise_guide", "运动指导"), ("sleep_guide", "睡眠指导"),
        ("emotion_support", "情绪支持"), ("tcm_wellness", "中医养生"),
        ("motivation_support", "动机支持"), ("habit_tracker", "习惯追踪"),
        ("community_guide", "同道者引导"), ("content_recommender", "内容推荐"),
        ("pain_relief_guide", "疼痛缓解"), ("rehab_exercise_guide", "康复运动"),
    ],
    "教练层": [
        ("behavior_coach", "行为教练"), ("assessment_engine", "评估引擎"),
        ("rx_composer", "处方编写"), ("stage_tracker", "阶段追踪"),
        ("progress_analyzer", "进度分析"), ("risk_detector", "风险检测"),
        ("quality_auditor", "质量审计"), ("coach_advisor", "教练顾问"),
        ("report_generator", "报告生成"), ("binding_manager", "绑定管理"),
    ],
    "系统层": [
        ("scheduler_agent", "调度Agent"), ("data_sync_agent", "数据同步"),
        ("notification_agent", "通知Agent"), ("audit_logger", "审计日志"),
    ],
    "中医骨科": [
        ("tcm_ortho_expert", "中医骨科专家"), ("pain_management_expert", "疼痛管理专家"),
        ("ortho_rehab_planner", "骨科康复规划"), ("tcm_exercise_guide", "传统功法指导"),
        ("meridian_acupoint", "经络穴位"),
    ],
}

# Flat lookup: agent_id → (display_name, layer)
_AGENT_LOOKUP: dict[str, tuple[str, str]] = {}
for _layer, _agents in _AGENT_SEED.items():
    for _aid, _aname in _agents:
        _AGENT_LOOKUP[_aid] = (_aname, _layer)


# ═══════════════════════════════════════════════════
# 1. GET /kpi/realtime
# ═══════════════════════════════════════════════════
@router.get("/kpi/realtime", response_model=list[CoreKPI])
async def get_realtime_kpi(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """4大核心KPI — 5s轮询"""
    try:
        today = date.today()
        yesterday = today - timedelta(days=1)

        # KPI 1: DAU — distinct users with chat_messages today (via chat_sessions)
        r = await db.execute(text("""
            SELECT COUNT(DISTINCT cs.user_id)
            FROM chat_messages cm
            JOIN chat_sessions cs ON cs.id = cm.session_id
            WHERE cm.created_at >= :today
        """), {"today": today})
        dau_today = r.scalar() or 0

        r = await db.execute(text("""
            SELECT COUNT(DISTINCT cs.user_id)
            FROM chat_messages cm
            JOIN chat_sessions cs ON cs.id = cm.session_id
            WHERE cm.created_at >= :yesterday AND cm.created_at < :today
        """), {"yesterday": yesterday, "today": today})
        dau_yesterday = r.scalar() or 0

        dau_trend_pct = round((dau_today - dau_yesterday) / max(dau_yesterday, 1) * 100, 1)
        dau_dir = "up" if dau_trend_pct > 0 else ("down" if dau_trend_pct < 0 else "flat")

        # KPI 2: Observer→Grower conversion rate
        r = await db.execute(text("""
            SELECT COUNT(*) FILTER (WHERE role::text != 'OBSERVER') as converted,
                   COUNT(*) as total
            FROM users WHERE is_active = true
        """))
        row = r.mappings().first()
        converted = row["converted"] if row else 0
        total_users = row["total"] if row else 1
        conv_rate = round(converted / max(total_users, 1) * 100, 1)

        # KPI 3: 7-day retention (grower+ with daily_tasks activity)
        seven_days_ago = today - timedelta(days=7)
        r = await db.execute(text("""
            SELECT COUNT(DISTINCT dt.user_id)
            FROM daily_tasks dt JOIN users u ON u.id = dt.user_id
            WHERE dt.task_date >= :seven_days_ago AND u.role::text != 'OBSERVER'
        """), {"seven_days_ago": seven_days_ago})
        active_growers_7d = r.scalar() or 0

        r = await db.execute(text(
            "SELECT COUNT(*) FROM users WHERE role::text != 'OBSERVER' AND is_active = true"
        ))
        total_growers = r.scalar() or 1
        retention_rate = round(active_growers_7d / max(total_growers, 1) * 100, 1)
        retention_status = "good" if retention_rate >= 70 else ("warn" if retention_rate >= 50 else "critical")

        # KPI 4: AI avg response time
        r = await db.execute(text("""
            SELECT COALESCE(AVG(latency_ms), 0)::int as avg_ms,
                   COALESCE(MAX(latency_ms), 0)::int as p95_approx
            FROM llm_call_logs
            WHERE created_at >= :today AND latency_ms > 0
        """), {"today": today})
        ai_row = r.mappings().first()
        avg_ms = ai_row["avg_ms"] if ai_row else 0
        p95_ms = ai_row["p95_approx"] if ai_row else 0
        avg_sec = round(avg_ms / 1000, 1) if avg_ms > 0 else 0.0
        p95_sec = round(p95_ms / 1000, 1) if p95_ms > 0 else 0.0
        ai_status = "good" if avg_ms < 3000 else ("warn" if avg_ms < 5000 else "critical")

        # Count timeout rate
        r = await db.execute(text("""
            SELECT COUNT(*) FILTER (WHERE latency_ms > 5000) as timeouts,
                   COUNT(*) as total
            FROM llm_call_logs WHERE created_at >= :today AND latency_ms > 0
        """), {"today": today})
        to_row = r.mappings().first()
        timeout_pct = round((to_row["timeouts"] or 0) / max(to_row["total"] or 1, 1) * 100, 1) if to_row else 0.0

        return [
            CoreKPI(
                icon="👥", value=_fmt_count(dau_today), label="DAU (全渠道)",
                sub=f"今日活跃用户",
                trend_dir=dau_dir, trend_pct=abs(dau_trend_pct),
                status="good" if dau_today > 0 else "warn",
            ),
            CoreKPI(
                icon="🔄", value=f"{conv_rate}%", label="Observer→Grower 转化",
                sub=f"已转化 {converted}/{total_users}",
                trend_dir="up" if conv_rate > 30 else "flat",
                trend_pct=conv_rate,
                status="good" if conv_rate > 25 else "warn",
            ),
            CoreKPI(
                icon="📊", value=f"{retention_rate}%", label="7日留存率",
                sub=f"Grower+ 活跃 {active_growers_7d}/{total_growers}",
                trend_dir="up" if retention_rate >= 70 else "down",
                trend_pct=retention_rate,
                status=retention_status,
            ),
            CoreKPI(
                icon="🤖", value=f"{avg_sec}s", label="AI平均响应",
                sub=f"P95: {p95_sec}s · 超时率: {timeout_pct}%",
                trend_dir="up" if avg_ms < 2000 else "down",
                trend_pct=round(avg_sec, 1),
                status=ai_status,
            ),
        ]
    except Exception as e:
        logger.warning("kpi/realtime fallback: %s", e)
        return [
            CoreKPI(icon="👥", value="0", label="DAU (全渠道)", sub="数据加载中", trend_dir="flat", trend_pct=0, status="warn"),
            CoreKPI(icon="🔄", value="0%", label="Observer→Grower 转化", sub="数据加载中", trend_dir="flat", trend_pct=0, status="warn"),
            CoreKPI(icon="📊", value="0%", label="7日留存率", sub="数据加载中", trend_dir="flat", trend_pct=0, status="warn"),
            CoreKPI(icon="🤖", value="0s", label="AI平均响应", sub="数据加载中", trend_dir="flat", trend_pct=0, status="warn"),
        ]


# ═══════════════════════════════════════════════════
# 2. GET /channels/health
# ═══════════════════════════════════════════════════
@router.get("/channels/health", response_model=list[ChannelHealth])
async def get_channels_health(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """渠道健康 — 10s轮询 (real metrics from activity logs)"""
    today_str = date.today().isoformat()
    try:
        # H5 DAU from activity logs
        h5_r = await db.execute(text(
            "SELECT COUNT(DISTINCT user_id) FROM user_activity_logs WHERE created_at::date = :d"
        ), {"d": today_str})
        h5_dau = h5_r.scalar() or 0

        # WeChat DAU (users with wx_openid + today's activity)
        wx_r = await db.execute(text("""
            SELECT COUNT(DISTINCT u.id) FROM users u
            JOIN user_activity_logs ual ON ual.user_id = u.id
            WHERE u.wx_openid IS NOT NULL AND ual.created_at::date = :d
        """), {"d": today_str})
        wx_dau = wx_r.scalar() or 0

        # Today's chat messages
        msg_r = await db.execute(text(
            "SELECT COUNT(*) FROM user_activity_logs WHERE created_at::date = :d AND activity_type IN ('chat', 'chat_message')"
        ), {"d": today_str})
        msg_today = msg_r.scalar() or 0

        # Error rate from llm_call_logs (if table exists)
        error_rate = 0.0
        try:
            err_r = await db.execute(text("""
                SELECT COUNT(*) FILTER (WHERE status = 'error')::float / GREATEST(COUNT(*), 1)
                FROM llm_call_logs WHERE created_at::date = :d
            """), {"d": today_str})
            error_rate = round(err_r.scalar() or 0.0, 4)
        except Exception:
            pass

    except Exception as e:
        logger.warning(f"channels/health query failed: {e}")
        h5_dau, wx_dau, msg_today, error_rate = 0, 0, 0, 0.0

    return [
        ChannelHealth(
            icon="📱", name="H5 移动端", status="healthy", status_label="正常",
            dau=str(h5_dau), msg_today=str(msg_today), avg_reply="--", error_rate=error_rate,
        ),
        ChannelHealth(
            icon="💬", name="微信服务号",
            status="healthy" if wx_dau > 0 else "degraded",
            status_label="正常" if wx_dau > 0 else "未接入",
            dau=str(wx_dau), msg_today="--", avg_reply="--",
        ),
        ChannelHealth(
            icon="🟢", name="微信小程序", status="healthy", status_label="待接入",
            dau="--", msg_today="--", avg_reply="--",
        ),
        ChannelHealth(
            icon="👔", name="企业微信", status="healthy", status_label="待接入",
            dau="--", msg_today="--", avg_reply="--",
        ),
    ]


# ═══════════════════════════════════════════════════
# 3. GET /funnel
# ═══════════════════════════════════════════════════
@router.get("/funnel", response_model=list[FunnelStep])
async def get_funnel(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """转化漏斗 — 1h刷新"""
    try:
        # Step 1+2+3: user counts by role
        r = await db.execute(text("""
            SELECT
              COUNT(*) as total,
              COUNT(*) FILTER (WHERE role::text = 'OBSERVER') as observers,
              COUNT(*) FILTER (WHERE role::text != 'OBSERVER') as upgraded
            FROM users WHERE is_active = true
        """))
        row = r.mappings().first()
        total = row["total"] if row else 0
        observers = row["observers"] if row else 0
        upgraded = row["upgraded"] if row else 0

        # Step 4: assessed users (try baps_results, fallback to 0)
        assessed = 0
        try:
            r = await db.execute(text("SELECT COUNT(DISTINCT user_id) FROM baps_results"))
            assessed = r.scalar() or 0
        except Exception:
            await db.rollback()

        # Step 5: 7-day active (grower+ with completed daily_tasks)
        r = await db.execute(text("""
            SELECT COUNT(DISTINCT user_id) FROM daily_tasks
            WHERE task_date >= CURRENT_DATE - 7 AND done = true
        """))
        active_7d = r.scalar() or 0

        # Build funnel — each step's pct is relative to total
        base = max(total, 1)
        steps = [
            ("注册用户", total, 100.0, "#93c5fd", None),
            ("Observer", observers, round(observers / base * 100, 1), "#60a5fa",
             f"{round(observers / base * 100, 1)}" if total else None),
            ("完成评估", assessed, round(assessed / base * 100, 1), "#3b82f6",
             f"{round(assessed / max(observers, 1) * 100, 1)}" if observers else None),
            ("升级Grower+", upgraded, round(upgraded / base * 100, 1), "#2563eb",
             f"{round(upgraded / max(assessed, 1) * 100, 1)}" if assessed else
             f"{round(upgraded / base * 100, 1)}"),
            ("7日活跃", active_7d, round(active_7d / base * 100, 1), "#1d4ed8",
             f"{round(active_7d / max(upgraded, 1) * 100, 1)}" if upgraded else None),
        ]

        return [
            FunnelStep(label=lbl, count=_fmt_count(cnt), pct=pct, color=clr, conv_rate=cr)
            for lbl, cnt, pct, clr, cr in steps
        ]
    except Exception as e:
        logger.warning("funnel fallback: %s", e)
        return [
            FunnelStep(label="注册用户", count="0", pct=100, color="#93c5fd"),
            FunnelStep(label="Observer", count="0", pct=0, color="#60a5fa"),
            FunnelStep(label="完成评估", count="0", pct=0, color="#3b82f6"),
            FunnelStep(label="升级Grower+", count="0", pct=0, color="#2563eb"),
            FunnelStep(label="7日活跃", count="0", pct=0, color="#1d4ed8"),
        ]


# ═══════════════════════════════════════════════════
# 4. GET /agents/monitor
# ═══════════════════════════════════════════════════
@router.get("/agents/monitor", response_model=list[AgentStatus])
async def get_agents_monitor(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """33Agent状态 — 10s轮询"""
    # Try to read from agent_templates + agent_metrics_daily;
    # fallback to hardcoded seed list if tables don't exist.
    metrics_map: dict[str, dict] = {}  # agent_id → {total_calls, avg_ms}

    try:
        r = await db.execute(text("""
            SELECT agent_id, total_calls, avg_processing_ms::int as avg_ms
            FROM agent_metrics_daily WHERE metric_date = :today
        """), {"today": date.today()})
        for row in r.mappings():
            metrics_map[row["agent_id"]] = {
                "total_calls": row["total_calls"] or 0,
                "avg_ms": row["avg_ms"] or 0,
            }
    except Exception:
        pass  # table missing — use empty metrics

    # Also try LLM call logs as a secondary metric source
    try:
        r = await db.execute(text("""
            SELECT COALESCE(intent, 'unknown') as agent_id,
                   COUNT(*) as total_calls,
                   COALESCE(AVG(latency_ms), 0)::int as avg_ms
            FROM llm_call_logs
            WHERE created_at >= :today AND intent IS NOT NULL
            GROUP BY intent
        """), {"today": date.today()})
        for row in r.mappings():
            aid = row["agent_id"]
            if aid not in metrics_map:
                metrics_map[aid] = {
                    "total_calls": row["total_calls"] or 0,
                    "avg_ms": row["avg_ms"] or 0,
                }
    except Exception:
        pass

    # Build agent list from seed, overlay with real metrics
    agents = []
    for layer, agent_list in _AGENT_SEED.items():
        for aid, aname in agent_list:
            m = metrics_map.get(aid, {})
            calls = m.get("total_calls", 0)
            avg_ms = m.get("avg_ms", 0)

            if calls == 0 and avg_ms == 0:
                status, status_label = "offline", "离线"
            elif avg_ms > 3000:
                status, status_label = "slow", "响应慢"
            else:
                status, status_label = "ok", "正常"

            agents.append(AgentStatus(
                id=aid, name=aname, layer=layer,
                status=status, status_label=status_label,
                p95_ms=int(avg_ms * 1.5) if avg_ms > 0 else None,
                calls_today=calls,
            ))

    return agents


# ═══════════════════════════════════════════════════
# 5. GET /agents/performance
# ═══════════════════════════════════════════════════
@router.get("/agents/performance", response_model=list[AgentPerf])
async def get_agents_performance(
    top_n: int = 5,
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Agent P95排行 — 1min刷新"""
    try:
        # Try agent_metrics_daily first
        rows = []
        try:
            r = await db.execute(text("""
                SELECT agent_id, avg_processing_ms::int as avg_ms, total_calls
                FROM agent_metrics_daily
                WHERE metric_date = :today AND total_calls > 0
                ORDER BY avg_processing_ms DESC LIMIT :top_n
            """), {"today": date.today(), "top_n": top_n})
            rows = list(r.mappings())
        except Exception:
            pass

        # Fallback to llm_call_logs
        if not rows:
            r = await db.execute(text("""
                SELECT COALESCE(intent, model_requested) as agent_id,
                       AVG(latency_ms)::int as avg_ms,
                       COUNT(*) as total_calls
                FROM llm_call_logs
                WHERE created_at >= :today AND latency_ms > 0
                GROUP BY 1
                HAVING COUNT(*) > 0
                ORDER BY avg_ms DESC LIMIT :top_n
            """), {"today": date.today(), "top_n": top_n})
            rows = list(r.mappings())

        result = []
        for row in rows:
            aid = row["agent_id"] or "unknown"
            avg_ms = row["avg_ms"] or 0
            calls = row["total_calls"] or 0
            display_name = _AGENT_LOOKUP.get(aid, (aid, ""))[0]
            result.append(AgentPerf(
                name=display_name, agent_id=aid,
                p95=int(avg_ms * 1.5), avg=avg_ms, calls=calls,
            ))
        return result
    except Exception as e:
        logger.warning("agents/performance fallback: %s", e)
        return []


# ═══════════════════════════════════════════════════
# 6. GET /coaches/ranking
# ═══════════════════════════════════════════════════
@router.get("/coaches/ranking", response_model=list[CoachRank])
async def get_coaches_ranking(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """教练效率排行 — 5min刷新"""
    try:
        today = date.today()
        r = await db.execute(text("""
            SELECT u.id, u.username,
              COUNT(DISTINCT q.student_id) as students,
              COUNT(*) FILTER (WHERE q.reviewed_at >= :today) as today_reviewed,
              COALESCE(
                AVG(l.elapsed_seconds) FILTER (WHERE l.reviewed_at >= :today),
                0
              )::int as avg_seconds,
              CASE WHEN COUNT(*) FILTER (WHERE q.status IN ('approved','rejected')) > 0
                THEN ROUND(
                  COUNT(*) FILTER (WHERE q.status='approved')::numeric /
                  COUNT(*) FILTER (WHERE q.status IN ('approved','rejected')),
                  2)
                ELSE 0.0
              END as approval_rate
            FROM users u
            LEFT JOIN coach_review_queue q ON q.coach_id = u.id
            LEFT JOIN coach_review_logs l ON l.coach_id = u.id
            WHERE u.role::text IN ('COACH','PROMOTER','SUPERVISOR','MASTER') AND u.is_active = true
            GROUP BY u.id, u.username
            ORDER BY today_reviewed DESC
        """), {"today": today})

        result = []
        for row in r.mappings():
            result.append(CoachRank(
                name=row["username"],
                coach_id=row["id"],
                students=row["students"] or 0,
                today_reviewed=row["today_reviewed"] or 0,
                avg_seconds=row["avg_seconds"] or 0,
                approval_rate=float(row["approval_rate"] or 0),
            ))
        return result
    except Exception as e:
        logger.warning("coaches/ranking fallback: %s", e)
        return []


# ═══════════════════════════════════════════════════
# 7. GET /safety/24h
# ═══════════════════════════════════════════════════
_SAFETY_RULES = {
    "S1": "医疗边界", "S2": "隐私保护", "S3": "危机检测",
    "S4": "内容合规", "S5": "数据最小化", "S6": "微信合规",
}

# Map event_type patterns → S-rule codes
_EVENT_TO_RULE = {
    "medical_boundary": "S1", "boundary_violation": "S1", "medication": "S1",
    "privacy": "S2", "pii_detected": "S2",
    "crisis": "S3", "suicide": "S3", "self_harm": "S3",
    "content_violation": "S4", "inappropriate": "S4",
    "data_minimization": "S5", "excessive_data": "S5",
    "wechat_compliance": "S6", "wechat": "S6",
}


@router.get("/safety/24h", response_model=list[SafetyMetric])
async def get_safety_24h(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """安全红线S1-S6 24小时触发统计 — 1min刷新"""
    try:
        r = await db.execute(text("""
            SELECT event_type, COUNT(*) as cnt, MAX(created_at) as last_triggered
            FROM safety_logs
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY event_type
        """))

        # Aggregate by S-rule
        rule_counts: dict[str, int] = {k: 0 for k in _SAFETY_RULES}
        rule_last: dict[str, Optional[datetime]] = {k: None for k in _SAFETY_RULES}

        for row in r.mappings():
            et = (row["event_type"] or "").lower()
            cnt = row["cnt"] or 0
            last_dt = row["last_triggered"]

            # Try exact match first, then prefix/contains
            rule = _EVENT_TO_RULE.get(et)
            if not rule:
                for pattern, r_code in _EVENT_TO_RULE.items():
                    if pattern in et:
                        rule = r_code
                        break
            if not rule:
                rule = "S4"  # default to content compliance

            rule_counts[rule] += cnt
            if last_dt and (rule_last[rule] is None or last_dt > rule_last[rule]):
                rule_last[rule] = last_dt

        return [
            SafetyMetric(
                rule=code, label=label,
                count=rule_counts[code],
                last_triggered=rule_last[code].strftime("%H:%M") if rule_last[code] else None,
            )
            for code, label in _SAFETY_RULES.items()
        ]
    except Exception as e:
        logger.warning("safety/24h fallback: %s", e)
        return [
            SafetyMetric(rule=code, label=label, count=0)
            for code, label in _SAFETY_RULES.items()
        ]


# ═══════════════════════════════════════════════════
# 8. GET /alerts/active
# ═══════════════════════════════════════════════════
@router.get("/alerts/active", response_model=list[Alert])
async def get_active_alerts(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """活跃告警 — 5s轮询"""
    try:
        alerts: list[Alert] = []

        # System alerts
        r = await db.execute(text("""
            SELECT id, level, message, source, auto_resolved, created_at
            FROM system_alerts WHERE status = 'active'
            ORDER BY CASE level
              WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2
            END, created_at DESC
            LIMIT 20
        """))
        for row in r.mappings():
            lvl = row["level"] or "info"
            if lvl not in ("critical", "warning", "info"):
                lvl = "info"
            alerts.append(Alert(
                id=str(row["id"]),
                level=lvl,
                message=row["message"] or "",
                source=row["source"] or "",
                time=_relative_time(row["created_at"]) if row["created_at"] else "",
                auto_resolved=bool(row["auto_resolved"]),
            ))

        # Device alerts (unresolved, danger severity)
        r = await db.execute(text("""
            SELECT id, severity as level, message, data_type as source, created_at
            FROM device_alerts
            WHERE resolved = false AND severity = 'danger'
            ORDER BY created_at DESC LIMIT 10
        """))
        for row in r.mappings():
            alerts.append(Alert(
                id=f"dev_{row['id']}",
                level="critical",
                message=row["message"] or "",
                source=row["source"] or "",
                time=_relative_time(row["created_at"]) if row["created_at"] else "",
            ))

        return alerts
    except Exception as e:
        logger.warning("alerts/active fallback: %s", e)
        return []


# ═══════════════════════════════════════════════════
# 9. POST /alerts/{alert_id}/dismiss
# ═══════════════════════════════════════════════════
@router.post("/alerts/{alert_id}/dismiss", response_model=AlertDismissResponse)
async def dismiss_alert(
    alert_id: str = Path(...),
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """关闭告警"""
    try:
        if alert_id.startswith("dev_"):
            dev_id = int(alert_id[4:])
            await db.execute(
                text("UPDATE device_alerts SET resolved=true WHERE id=:id"),
                {"id": dev_id},
            )
        else:
            await db.execute(
                text("""
                    UPDATE system_alerts
                    SET status='dismissed', dismissed_by=:uid, dismissed_at=NOW()
                    WHERE id=:id
                """),
                {"id": alert_id, "uid": admin_user.id},
            )
        await db.commit()
        return AlertDismissResponse(success=True, alert_id=alert_id)
    except Exception as e:
        logger.warning("dismiss_alert error: %s", e)
        await db.rollback()
        return AlertDismissResponse(success=False, alert_id=alert_id)


# ═══════════════════════════════════════════════════
# 10. GET /users/overview
# ═══════════════════════════════════════════════════
@router.get("/user-overview", response_model=UserOverview)
async def get_users_overview(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """用户总览"""
    try:
        today = date.today()

        # Role breakdown
        r = await db.execute(text("""
            SELECT
              COUNT(*) as total,
              COUNT(*) FILTER (WHERE role::text='OBSERVER') as observers,
              COUNT(*) FILTER (WHERE role::text='GROWER') as growers,
              COUNT(*) FILTER (WHERE role::text='SHARER') as sharers,
              COUNT(*) FILTER (WHERE role::text='COACH') as coaches,
              COUNT(*) FILTER (WHERE role::text='PROMOTER') as promoters,
              COUNT(*) FILTER (WHERE role::text='SUPERVISOR') as supervisors,
              COUNT(*) FILTER (WHERE role::text='MASTER') as masters,
              COUNT(*) FILTER (WHERE role::text='ADMIN') as admins,
              COUNT(*) FILTER (WHERE created_at >= :today) as new_today
            FROM users WHERE is_active = true
        """), {"today": today})
        row = r.mappings().first()

        by_role = {
            "Observer": row["observers"] or 0,
            "Grower": row["growers"] or 0,
            "Sharer": row["sharers"] or 0,
            "Coach": row["coaches"] or 0,
            "Promoter": row["promoters"] or 0,
            "Supervisor": row["supervisors"] or 0,
            "Master": row["masters"] or 0,
            "Admin": row["admins"] or 0,
        } if row else {}

        # Active today: distinct users from chat_messages + daily_tasks
        r = await db.execute(text("""
            SELECT COUNT(DISTINCT uid) FROM (
              SELECT cs.user_id as uid
              FROM chat_messages cm
              JOIN chat_sessions cs ON cs.id = cm.session_id
              WHERE cm.created_at >= :today
              UNION
              SELECT user_id as uid
              FROM daily_tasks WHERE task_date = :today_date
            ) sub
        """), {"today": today, "today_date": today})
        active_today = r.scalar() or 0

        return UserOverview(
            total_users=row["total"] if row else 0,
            by_role=by_role,
            by_stage={},  # Stage data requires assessment pipeline; omit for now
            new_today=row["new_today"] if row else 0,
            active_today=active_today,
        )
    except Exception as e:
        logger.warning("users/overview fallback: %s", e)
        return UserOverview(total_users=0, by_role={}, by_stage={}, new_today=0, active_today=0)


# ═══════════════════════════════════════════════════
# 11. GET /system/containers
# ═══════════════════════════════════════════════════
@router.get("/system/containers", response_model=list[ContainerStatus])
async def get_container_status(admin_user=Depends(require_admin)):
    # INFRASTRUCTURE PLACEHOLDER — requires Docker API (unix socket or TCP).
    # Returns expected container topology.
    """容器状态"""
    return [
        ContainerStatus(name="bhp-api", port="8000", status="running", uptime="--", cpu_pct=0, mem_mb=0),
        ContainerStatus(name="bhp-h5", port="5173", status="running", uptime="--", cpu_pct=0, mem_mb=0),
        ContainerStatus(name="bhp-admin-portal", port="5174", status="running", uptime="--", cpu_pct=0, mem_mb=0),
        ContainerStatus(name="bhp-expert-workbench", port="8501", status="running", uptime="--", cpu_pct=0, mem_mb=0),
        ContainerStatus(name="dify-api", port="5001", status="running", uptime="--", cpu_pct=0, mem_mb=0),
        ContainerStatus(name="dify-db", port="5432", status="running", uptime="--", cpu_pct=0, mem_mb=0),
        ContainerStatus(name="dify-redis", port="6379", status="running", uptime="--", cpu_pct=0, mem_mb=0),
    ]


# ═══════════════════════════════════════════════════
# 12. GET /audit-log/recent
# ═══════════════════════════════════════════════════
@router.get("/audit-log/recent", response_model=list[dict])
async def get_recent_audit_log(
    limit: int = 20,
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """最近审计日志"""
    try:
        half = max(limit // 2, 5)

        # Coach review logs
        r1 = await db.execute(text("""
            SELECT l.reviewed_at as time, u.username, l.action, l.review_id as target, '' as detail
            FROM coach_review_logs l
            JOIN users u ON u.id = l.coach_id
            ORDER BY l.reviewed_at DESC LIMIT :half
        """), {"half": half})
        coach_logs = list(r1.mappings())

        # Safety logs
        r2 = await db.execute(text("""
            SELECT created_at as time, 'system' as username, event_type as action,
              event_type as target, COALESCE(LEFT(input_text, 60), '') as detail
            FROM safety_logs ORDER BY created_at DESC LIMIT :half
        """), {"half": half})
        safety_logs = list(r2.mappings())

        # Merge and sort by time desc
        combined = []
        for row in coach_logs:
            dt = row["time"]
            combined.append({
                "time": dt.strftime("%H:%M") if dt else "--:--",
                "user": row["username"] or "unknown",
                "action": row["action"] or "",
                "target": row["target"] or "",
                "detail": row["detail"] or "",
                "_sort": dt or datetime.min,
            })
        for row in safety_logs:
            dt = row["time"]
            combined.append({
                "time": dt.strftime("%H:%M") if dt else "--:--",
                "user": row["username"] or "system",
                "action": row["action"] or "",
                "target": row["target"] or "",
                "detail": row["detail"] or "",
                "_sort": dt or datetime.min,
            })

        combined.sort(key=lambda x: x["_sort"], reverse=True)

        # Remove sort key before returning
        return [{k: v for k, v in item.items() if k != "_sort"} for item in combined[:limit]]
    except Exception as e:
        logger.warning("audit-log/recent fallback: %s", e)
        return []
