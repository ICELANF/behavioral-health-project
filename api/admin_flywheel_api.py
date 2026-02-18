"""
Admin 飞轮 API — 指挥中心 Dashboard
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

from datetime import date, datetime
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

from api.dependencies import require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin-flywheel"])


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
# 1. GET /kpi/realtime
# ═══════════════════════════════════════════════════
@router.get("/kpi/realtime", response_model=list[CoreKPI])
async def get_realtime_kpi(admin_user=Depends(require_admin)):
    """4大核心KPI — 5s轮询"""
    return [
        CoreKPI(icon="👥", value="1,247", label="DAU (全渠道)", sub="App 680 · 微信 402 · 小程序 165", trend_dir="up", trend_pct=12.0, status="good"),
        CoreKPI(icon="🔄", value="34.2%", label="Observer→Grower 转化", sub="本周 vs 上周 +5.1pp", trend_dir="up", trend_pct=5.1, status="good"),
        CoreKPI(icon="📊", value="78.5%", label="7日留存率", sub="Grower角色", trend_dir="down", trend_pct=2.3, status="warn"),
        CoreKPI(icon="🤖", value="1.8s", label="AI平均响应", sub="P95: 3.2s · 超时率: 0.3%", trend_dir="up", trend_pct=0.5, status="good"),
    ]


# ═══════════════════════════════════════════════════
# 2. GET /channels/health
# ═══════════════════════════════════════════════════
@router.get("/channels/health", response_model=list[ChannelHealth])
async def get_channels_health(admin_user=Depends(require_admin)):
    """渠道健康 — 10s轮询"""
    return [
        ChannelHealth(icon="📱", name="H5 移动端", status="healthy", status_label="正常", dau="680", msg_today="3,420", avg_reply="1.6s"),
        ChannelHealth(icon="💬", name="微信服务号", status="healthy", status_label="正常", dau="402", msg_today="1,890", avg_reply="2.1s"),
        ChannelHealth(icon="🟢", name="微信小程序", status="healthy", status_label="正常", dau="165", msg_today="720", avg_reply="1.4s"),
        ChannelHealth(icon="👔", name="企业微信", status="degraded", status_label="告警", dau="23", msg_today="156", avg_reply="4.2s", error_rate=0.08),
    ]


# ═══════════════════════════════════════════════════
# 3. GET /funnel
# ═══════════════════════════════════════════════════
@router.get("/funnel", response_model=list[FunnelStep])
async def get_funnel(admin_user=Depends(require_admin)):
    """转化漏斗 — 1h刷新"""
    return [
        FunnelStep(label="访问", count="5,280", pct=100, color="#93c5fd"),
        FunnelStep(label="注册(Observer)", count="2,140", pct=40, color="#60a5fa", conv_rate="40.5"),
        FunnelStep(label="完成评估", count="892", pct=17, color="#3b82f6", conv_rate="41.7"),
        FunnelStep(label="升级Grower", count="731", pct=14, color="#2563eb", conv_rate="81.9"),
        FunnelStep(label="7日活跃", count="574", pct=11, color="#1d4ed8", conv_rate="78.5"),
    ]


# ═══════════════════════════════════════════════════
# 4. GET /agents/monitor
# ═══════════════════════════════════════════════════
@router.get("/agents/monitor", response_model=list[AgentStatus])
async def get_agents_monitor(admin_user=Depends(require_admin)):
    """33Agent状态 — 10s轮询"""
    agents = []
    # 用户层 14
    user_agents = [
        ("health_assistant", "健康助手"), ("crisis_responder", "危机响应"),
        ("onboarding_guide", "引导向导"), ("nutrition_guide", "营养指导"),
        ("exercise_guide", "运动指导"), ("sleep_guide", "睡眠指导"),
        ("emotion_support", "情绪支持"), ("tcm_wellness", "中医养生"),
        ("motivation_support", "动机支持"), ("habit_tracker", "习惯追踪"),
        ("community_guide", "同道者引导"), ("content_recommender", "内容推荐"),
        ("pain_relief_guide", "疼痛缓解"), ("rehab_exercise_guide", "康复运动"),
    ]
    for aid, name in user_agents:
        status = "slow" if aid == "exercise_guide" else "ok"
        agents.append(AgentStatus(id=aid, name=name, layer="用户层", status=status, status_label="响应慢" if status == "slow" else "正常", p95_ms=3800 if status == "slow" else 1200, calls_today=45))
    
    # 教练层 10
    coach_agents = [
        ("behavior_coach", "行为教练"), ("assessment_engine", "评估引擎"),
        ("rx_composer", "处方编写"), ("stage_tracker", "阶段追踪"),
        ("progress_analyzer", "进度分析"), ("risk_detector", "风险检测"),
        ("quality_auditor", "质量审计"), ("coach_advisor", "教练顾问"),
        ("report_generator", "报告生成"), ("binding_manager", "绑定管理"),
    ]
    for aid, name in coach_agents:
        agents.append(AgentStatus(id=aid, name=name, layer="教练层", status="ok", status_label="正常", calls_today=20))
    
    # 系统层 4
    system_agents = [
        ("scheduler_agent", "调度Agent"), ("data_sync_agent", "数据同步"),
        ("notification_agent", "通知Agent"), ("audit_logger", "审计日志"),
    ]
    for aid, name in system_agents:
        agents.append(AgentStatus(id=aid, name=name, layer="系统层", status="ok", status_label="正常", calls_today=100))
    
    # 中医骨科 5
    tcm_agents = [
        ("tcm_ortho_expert", "中医骨科专家"), ("pain_management_expert", "疼痛管理专家"),
        ("ortho_rehab_planner", "骨科康复规划"), ("tcm_exercise_guide", "传统功法指导"),
        ("meridian_acupoint", "经络穴位"),
    ]
    for i, (aid, name) in enumerate(tcm_agents):
        status = "error" if i == 2 else "ok"
        agents.append(AgentStatus(id=aid, name=name, layer="中医骨科", status=status, status_label="异常" if status == "error" else "正常", calls_today=8))
    
    return agents


# ═══════════════════════════════════════════════════
# 5. GET /agents/performance
# ═══════════════════════════════════════════════════
@router.get("/agents/performance", response_model=list[AgentPerf])
async def get_agents_performance(top_n: int = 5, admin_user=Depends(require_admin)):
    """Agent P95排行 — 1min刷新"""
    return [
        AgentPerf(name="vlm_service (食物)", agent_id="nutrition_guide", p95=3800, avg=2100, calls=320),
        AgentPerf(name="tcm_ortho_expert", agent_id="tcm_ortho_expert", p95=2400, avg=1800, calls=45),
        AgentPerf(name="emotion_support", agent_id="emotion_support", p95=1900, avg=1200, calls=180),
        AgentPerf(name="rx_composer", agent_id="rx_composer", p95=1600, avg=900, calls=95),
        AgentPerf(name="nutrition_guide", agent_id="nutrition_guide", p95=1200, avg=800, calls=410),
    ][:top_n]


# ═══════════════════════════════════════════════════
# 6. GET /coaches/ranking
# ═══════════════════════════════════════════════════
@router.get("/coaches/ranking", response_model=list[CoachRank])
async def get_coaches_ranking(admin_user=Depends(require_admin)):
    """教练效率排行 — 5min刷新"""
    return [
        CoachRank(name="张教练", coach_id=201, students=45, today_reviewed=34, avg_seconds=28, approval_rate=0.91),
        CoachRank(name="李教练", coach_id=202, students=38, today_reviewed=29, avg_seconds=35, approval_rate=0.88),
        CoachRank(name="王教练", coach_id=203, students=42, today_reviewed=22, avg_seconds=42, approval_rate=0.85),
        CoachRank(name="陈教练", coach_id=204, students=30, today_reviewed=18, avg_seconds=55, approval_rate=0.82),
    ]


# ═══════════════════════════════════════════════════
# 7. GET /safety/24h
# ═══════════════════════════════════════════════════
@router.get("/safety/24h", response_model=list[SafetyMetric])
async def get_safety_24h(admin_user=Depends(require_admin)):
    """安全红线S1-S6 24小时触发统计 — 1min刷新"""
    return [
        SafetyMetric(rule="S1", label="医疗边界", count=3, last_triggered="14:32"),
        SafetyMetric(rule="S2", label="隐私保护", count=0),
        SafetyMetric(rule="S3", label="危机检测", count=1, last_triggered="09:15"),
        SafetyMetric(rule="S4", label="内容合规", count=0),
        SafetyMetric(rule="S5", label="数据最小化", count=0),
        SafetyMetric(rule="S6", label="微信合规", count=2, last_triggered="11:40"),
    ]


# ═══════════════════════════════════════════════════
# 8. GET /alerts/active
# ═══════════════════════════════════════════════════
@router.get("/alerts/active", response_model=list[Alert])
async def get_active_alerts(admin_user=Depends(require_admin)):
    """活跃告警 — 5s轮询"""
    return [
        Alert(id="alt_001", level="critical", message="VLM服务响应超时 >5s (影响图片识别)", source="bhp-vlm", time="2分钟前"),
        Alert(id="alt_002", level="warning", message="微信服务号模板消息发送失败率升高至8%", source="bhp-wx-gateway", time="15分钟前"),
    ]


# ═══════════════════════════════════════════════════
# 9. POST /alerts/{alert_id}/dismiss
# ═══════════════════════════════════════════════════
@router.post("/alerts/{alert_id}/dismiss", response_model=AlertDismissResponse)
async def dismiss_alert(alert_id: str = Path(...), admin_user=Depends(require_admin)):
    """关闭告警"""
    return AlertDismissResponse(success=True, alert_id=alert_id)


# ═══════════════════════════════════════════════════
# 10. GET /users/overview
# ═══════════════════════════════════════════════════
@router.get("/users/overview", response_model=UserOverview)
async def get_users_overview(admin_user=Depends(require_admin)):
    """用户总览"""
    return UserOverview(
        total_users=3840,
        by_role={"Observer": 1420, "Grower": 1650, "Coach": 45, "Expert": 12, "Admin": 3},
        by_stage={"S0": 420, "S1": 380, "S2": 520, "S3": 680, "S4": 450, "S5": 280, "S6": 110},
        new_today=47,
        active_today=1247,
    )


# ═══════════════════════════════════════════════════
# 11. GET /system/containers
# ═══════════════════════════════════════════════════
@router.get("/system/containers", response_model=list[ContainerStatus])
async def get_container_status(admin_user=Depends(require_admin)):
    """容器状态"""
    return [
        ContainerStatus(name="bhp-api", port="8000", status="running", uptime="3d 12h", cpu_pct=24.5, mem_mb=512),
        ContainerStatus(name="bhp-h5", port="5173", status="running", uptime="3d 12h", cpu_pct=2.1, mem_mb=64),
        ContainerStatus(name="bhp-admin-portal", port="5174", status="running", uptime="3d 12h", cpu_pct=1.8, mem_mb=58),
        ContainerStatus(name="bhp-wx-gateway", port="8080", status="running", uptime="1d 4h", cpu_pct=8.3, mem_mb=128),
        ContainerStatus(name="bhp-asr", port="8002", status="running", uptime="1d 4h", cpu_pct=15.2, mem_mb=1024),
        ContainerStatus(name="bhp-vlm", port="8004", status="error", uptime="0h (restarting)", cpu_pct=0, mem_mb=0),
        ContainerStatus(name="bhp-tts", port="8003", status="running", uptime="1d 4h", cpu_pct=5.1, mem_mb=256),
    ]


# ═══════════════════════════════════════════════════
# 12. GET /audit-log/recent
# ═══════════════════════════════════════════════════
@router.get("/audit-log/recent", response_model=list[dict])
async def get_recent_audit_log(limit: int = 20, admin_user=Depends(require_admin)):
    """最近审计日志"""
    return [
        {"time": "14:35", "user": "张教练", "action": "approve_review", "target": "rv_001", "detail": "通过王阿姨AI回复"},
        {"time": "14:32", "user": "system", "action": "safety_trigger", "target": "S1", "detail": "nutrition_guide触及医疗边界"},
        {"time": "14:28", "user": "王专家", "action": "audit_verdict", "target": "au_001", "detail": "合格通过，评分4/5"},
        {"time": "14:15", "user": "system", "action": "alert_fired", "target": "alt_001", "detail": "VLM服务超时"},
    ]
