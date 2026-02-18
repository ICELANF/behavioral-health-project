"""
Expert 飞轮 API — 统一审核工作台
端点:
  GET  /api/v1/expert/audit-queue       → 审核队列(含安全检查)
  POST /api/v1/expert/audit/:id/verdict → 提交裁决
  GET  /api/v1/expert/quality-metrics   → 质量指标
  GET  /api/v1/expert/agent-anomalies   → Agent异常列表
"""

from datetime import date, datetime
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from api.dependencies import require_coach_or_admin

router = APIRouter(prefix="/api/v1/expert", tags=["expert-flywheel"])


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
# GET /audit-queue
# ═══════════════════════════════════════════════════
@router.get("/audit-queue", response_model=AuditQueueResponse)
async def get_audit_queue(
    type_filter: Optional[str] = Query(None),
    risk_filter: Optional[str] = Query(None),
    agent_filter: Optional[str] = Query(None),
    expert_user=Depends(require_coach_or_admin),
):
    """
    获取审核队列
    
    入队来源:
    1. quality_auditor Agent自动标记的AI输出
    2. safety_gate触发的安全事件
    3. 教练escalate的复杂case
    4. 系统抽检(随机10%对话)
    
    排序: risk降序 → time升序
    """
    items = [
        AuditItem(
            id="au_001", title="王阿姨血糖对话 — 疑似越界", type="ai_dialogue", type_icon="💬",
            agent="nutrition_guide", user_name="王阿姨", user_stage="S1/L2",
            risk="high", time="14:32",
            dialogue=[
                DialogueMessage(id=1, role="user", text="我血糖空腹8.5，是不是该加药了？"),
                DialogueMessage(id=2, role="ai", text="您的空腹血糖偏高。建议您先尝试在餐后30分钟散步15分钟。如果持续偏高，建议咨询您的主治医生。⚠️ 以上为AI生成的健康建议，不构成医疗诊断。"),
            ],
            safety_flags=[
                SafetyFlag(rule="S1-医疗边界", description="用户询问用药调整，AI涉及药物话题", action="已添加免责声明"),
            ],
        ),
        AuditItem(
            id="au_002", title="李大爷运动处方 — 强度偏高", type="prescription", type_icon="📋",
            agent="rx_composer", user_name="李大爷", user_stage="S2/L3",
            risk="medium", time="11:20",
            rx_fields=[
                RxReviewField(key="target", label="目标行为", value="每日快走30分钟", flagged=True, flag_reason="S2阶段建议≤15分钟"),
                RxReviewField(key="frequency", label="频次", value="每天"),
                RxReviewField(key="time_place", label="时间地点", value="晚饭后小区步道"),
                RxReviewField(key="trigger", label="启动线索", value="放下碗筷→换鞋→出门"),
                RxReviewField(key="obstacle", label="障碍预案", value="下雨改室内踏步"),
                RxReviewField(key="support", label="支持", value="老伴陪同"),
            ],
            evidence_level=2,
        ),
    ]
    
    if type_filter:
        items = [i for i in items if i.type == type_filter]
    if risk_filter:
        items = [i for i in items if i.risk == risk_filter]
    if agent_filter and agent_filter != "all":
        items = [i for i in items if i.agent == agent_filter]
    
    risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda x: risk_order.get(x.risk, 9))
    
    return AuditQueueResponse(
        items=items,
        total=len(items),
        by_type={"ai_dialogue": 5, "prescription": 2, "agent_behavior": 1, "content": 0, "safety": 2},
        by_risk={"critical": 2, "high": 3, "medium": 3, "low": 0},
    )


# ═══════════════════════════════════════════════════
# POST /audit/{audit_id}/verdict
# ═══════════════════════════════════════════════════
@router.post("/audit/{audit_id}/verdict", response_model=VerdictResponse)
async def submit_verdict(
    audit_id: str = Path(...),
    req: VerdictRequest = ...,
    expert_user=Depends(require_coach_or_admin),
):
    """
    提交审核裁决
    
    pass: 合格通过 → 记录质量分数
    revise: 退回修改 → 通知相关Agent重新生成
    block: 拦截禁用 → 从系统中移除 + 安全审计日志
    """
    return VerdictResponse(
        success=True,
        audit_id=audit_id,
        verdict=req.verdict,
        next_id="au_002",
        message="已" + {"pass": "通过", "revise": "退回", "block": "拦截"}.get(req.verdict, ""),
    )


# ═══════════════════════════════════════════════════
# GET /quality-metrics
# ═══════════════════════════════════════════════════
@router.get("/quality-metrics", response_model=QualityMetricsResponse)
async def get_quality_metrics(expert_user=Depends(require_coach_or_admin)):
    """质量指标总览 — ExpertAuditWorkbench 顶部"""
    return QualityMetricsResponse(
        today_audited=23,
        pass_rate=0.87,
        pending_queue=8,
        redline_blocked=2,
        agent_anomaly_count=1,
        by_type={
            "ai_dialogue": {"audited": 12, "pass_rate": 0.83},
            "prescription": {"audited": 8, "pass_rate": 0.92},
            "agent_behavior": {"audited": 3, "pass_rate": 0.85},
        },
        trend_7d=[
            {"date": "02-11", "audited": 18, "pass_rate": 0.82},
            {"date": "02-12", "audited": 21, "pass_rate": 0.85},
            {"date": "02-13", "audited": 25, "pass_rate": 0.88},
            {"date": "02-14", "audited": 19, "pass_rate": 0.84},
            {"date": "02-15", "audited": 22, "pass_rate": 0.86},
            {"date": "02-16", "audited": 20, "pass_rate": 0.90},
            {"date": "02-17", "audited": 23, "pass_rate": 0.87},
        ],
    )


# ═══════════════════════════════════════════════════
# GET /agent-anomalies
# ═══════════════════════════════════════════════════
@router.get("/agent-anomalies", response_model=list[AgentAnomaly])
async def get_agent_anomalies(expert_user=Depends(require_coach_or_admin)):
    """Agent异常列表 — 供Expert审查Agent行为"""
    return [
        AgentAnomaly(
            agent_id="nutrition_guide", agent_name="营养指导",
            anomaly_type="boundary_violation", severity="warning",
            description="近24h内3次触及S1医疗边界(用户问药物时回复涉及具体药名)",
            sample_count=3, first_seen="2026-02-17T08:22:00", last_seen="2026-02-17T14:32:00",
        ),
    ]
