"""
治理仪表盘 + 教练KPI红绿灯
契约来源: Sheet⑩ 治理健康仪表盘(P0) + 教练KPI红绿灯仪表盘(P1)

功能:
  1. KPI红绿灯系统 — 10项KPI实时监控
  2. 责任健康聚合 — 多角色多维度聚合视图
  3. 告警升级管道 — 黄→红→升级Admin/督导
  4. 仪表盘数据API — 前端可视化数据源

依赖:
  - ResponsibilityTracker (Week3 Module 2)
  - AuditLogger (Week1 Task4)
  - StageEngine (Week3 Module 1)
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from responsibility_tracker import (
    ResponsibilityTracker, HealthColor, UserHealthReport,
    RESPONSIBILITY_REGISTRY, LEVEL_TO_ROLE,
)


# ══════════════════════════════════════════
# 1. KPI 红绿灯定义 (教练10项)
# ══════════════════════════════════════════

@dataclass
class KPIDefinition:
    """KPI指标定义"""
    kpi_id: str
    name: str
    description: str
    green_rule: str
    yellow_rule: str
    red_rule: str
    data_source: str
    auto_escalation: bool = False
    escalation_target: str = ""


COACH_KPI_DEFINITIONS: List[KPIDefinition] = [
    KPIDefinition("KPI-01", "学员查看率", "定期查看学员健康数据",
                   "每周≥1次/学员", "有学员本周未查看", "连续2周未查看某学员",
                   "StudentHealthData日志"),
    KPIDefinition("KPI-02", "消息响应时效", "学员消息平均响应时间",
                   "≤24小时", "24-48小时", "超48小时",
                   "Messages API", True, "Admin"),
    KPIDefinition("KPI-03", "告警处置时效", "高风险告警处理速度",
                   "高风险≤4h, 普通≤24h", "高风险4-8h", "高风险>8h未处理",
                   "DeviceAlerts API", True, "Admin"),
    KPIDefinition("KPI-04", "安全合规率", "输出安全管线拦截率",
                   "<5%", "5-10%", ">10%",
                   "SafetyLog"),
    KPIDefinition("KPI-05", "学分进度", "季度培训学分完成度",
                   "≥25学分/季", "<20学分/季", "连续2季度不达标",
                   "Credits API"),
    KPIDefinition("KPI-06", "评估跟进", "学员评估审核时效",
                   "≤7天", "7-14天", ">14天",
                   "AssessmentAssignment"),
    KPIDefinition("KPI-07", "投诉记录", "学员投诉数",
                   "0投诉/月", "1投诉/月", "≥2投诉/月",
                   "SafetyLog+Complaint", True, "督导"),
    KPIDefinition("KPI-08", "转介合规", "超范围对话正确转介",
                   "100%转介", "偶有延迟", "未转介",
                   "AgentRouter+Safety"),
    KPIDefinition("KPI-09", "带教质量", "同道者毕业率+质量分",
                   "毕业率≥70%, 质量≥3.5", "毕业率60-70%", "低于60%",
                   "CompanionRelation"),
    KPIDefinition("KPI-10", "数据安全", "越权访问检测",
                   "0越权", "—", "任何越权",
                   "AuditLog+RBAC", True, "Admin"),
]


@dataclass
class KPIResult:
    """单项KPI评估结果"""
    kpi_id: str
    name: str
    color: HealthColor
    current_value: Any
    green_rule: str
    detail: str = ""
    needs_escalation: bool = False
    escalation_target: str = ""


# ══════════════════════════════════════════
# 2. 治理仪表盘引擎
# ══════════════════════════════════════════

class GovernanceDashboard:
    """
    治理仪表盘引擎。
    
    提供:
      1. 教练个人KPI红绿灯
      2. 组织级责任健康概览
      3. 告警聚合与升级
      4. 趋势分析数据
    """
    
    def __init__(self, tracker: ResponsibilityTracker = None):
        self.tracker = tracker or ResponsibilityTracker()
    
    # ── 2.1 教练KPI红绿灯 ──
    
    async def get_coach_kpi_dashboard(
        self, coach_id: int, metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        教练10项KPI红绿灯仪表盘。
        
        Returns: {kpis, overall_color, health_score, alerts, summary}
        """
        kpi_results = []
        
        for kpi_def in COACH_KPI_DEFINITIONS:
            result = self._evaluate_kpi(kpi_def, metrics)
            kpi_results.append(result)
        
        green = sum(1 for k in kpi_results if k.color == HealthColor.GREEN)
        yellow = sum(1 for k in kpi_results if k.color == HealthColor.YELLOW)
        red = sum(1 for k in kpi_results if k.color == HealthColor.RED)
        total = len(kpi_results)
        
        score = ((green * 100 + yellow * 60 + red * 20) / total) if total > 0 else 0
        
        overall = HealthColor.RED if red > 0 else (HealthColor.YELLOW if yellow > 0 else HealthColor.GREEN)
        
        escalations = [k for k in kpi_results if k.needs_escalation]
        
        return {
            "coach_id": coach_id,
            "kpis": [
                {
                    "kpi_id": k.kpi_id,
                    "name": k.name,
                    "color": k.color.value,
                    "current_value": k.current_value,
                    "green_rule": k.green_rule,
                    "detail": k.detail,
                    "needs_escalation": k.needs_escalation,
                    "escalation_target": k.escalation_target,
                }
                for k in kpi_results
            ],
            "summary": {
                "overall_color": overall.value,
                "health_score": round(score, 1),
                "green": green,
                "yellow": yellow,
                "red": red,
            },
            "escalations": [
                {"kpi_id": k.kpi_id, "name": k.name, "target": k.escalation_target}
                for k in escalations
            ],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def _evaluate_kpi(self, kpi_def: KPIDefinition, metrics: Dict) -> KPIResult:
        """评估单项KPI"""
        # KPI→指标映射
        kpi_metric_map = {
            "KPI-01": "student_data_view_frequency",
            "KPI-02": "avg_response_time_hours",
            "KPI-03": "alert_response_time",
            "KPI-04": "safety_pipeline_interception_rate",
            "KPI-05": "quarterly_credits",
            "KPI-06": "assessment_review_days",
            "KPI-07": "monthly_complaint_count",
            "KPI-08": "out_of_scope_referral_rate",
            "KPI-09": "mentee_quality_score",
            "KPI-10": "unauthorized_access_count",
        }
        
        metric_key = kpi_metric_map.get(kpi_def.kpi_id, "")
        value = metrics.get(metric_key)
        
        color = self._judge_kpi_color(kpi_def.kpi_id, value)
        
        needs_escalation = (color == HealthColor.RED and kpi_def.auto_escalation)
        
        return KPIResult(
            kpi_id=kpi_def.kpi_id,
            name=kpi_def.name,
            color=color,
            current_value=value,
            green_rule=kpi_def.green_rule,
            detail=kpi_def.red_rule if color == HealthColor.RED else "",
            needs_escalation=needs_escalation,
            escalation_target=kpi_def.escalation_target if needs_escalation else "",
        )
    
    def _judge_kpi_color(self, kpi_id: str, value: Any) -> HealthColor:
        if value is None:
            return HealthColor.YELLOW
        
        rules = {
            "KPI-01": lambda v: HealthColor.GREEN if v >= 1 else (HealthColor.YELLOW if v > 0 else HealthColor.RED),
            "KPI-02": lambda v: HealthColor.GREEN if v <= 24 else (HealthColor.YELLOW if v <= 48 else HealthColor.RED),
            "KPI-03": lambda v: HealthColor.GREEN if v <= 4 else (HealthColor.YELLOW if v <= 8 else HealthColor.RED),
            "KPI-04": lambda v: HealthColor.GREEN if v < 0.05 else (HealthColor.YELLOW if v <= 0.10 else HealthColor.RED),
            "KPI-05": lambda v: HealthColor.GREEN if v >= 25 else (HealthColor.YELLOW if v >= 20 else HealthColor.RED),
            "KPI-06": lambda v: HealthColor.GREEN if v <= 7 else (HealthColor.YELLOW if v <= 14 else HealthColor.RED),
            "KPI-07": lambda v: HealthColor.GREEN if v == 0 else (HealthColor.YELLOW if v <= 1 else HealthColor.RED),
            "KPI-08": lambda v: HealthColor.GREEN if v >= 1.0 else (HealthColor.YELLOW if v >= 0.8 else HealthColor.RED),
            "KPI-09": lambda v: HealthColor.GREEN if v >= 3.5 else (HealthColor.YELLOW if v >= 3.0 else HealthColor.RED),
            "KPI-10": lambda v: HealthColor.GREEN if v == 0 else HealthColor.RED,
        }
        
        judge_fn = rules.get(kpi_id)
        if judge_fn and isinstance(value, (int, float)):
            return judge_fn(value)
        return HealthColor.YELLOW
    
    # ── 2.2 组织级聚合 ──
    
    async def get_org_overview(
        self, reports: List[UserHealthReport]
    ) -> Dict[str, Any]:
        """组织级责任健康概览"""
        role_stats = {}
        
        for report in reports:
            role = report.role
            if role not in role_stats:
                role_stats[role] = {
                    "total": 0, "green": 0, "yellow": 0, "red": 0,
                    "avg_score": 0, "scores": [],
                }
            
            stats = role_stats[role]
            stats["total"] += 1
            stats["scores"].append(report.health_score)
            
            if report.overall_color == HealthColor.GREEN:
                stats["green"] += 1
            elif report.overall_color == HealthColor.YELLOW:
                stats["yellow"] += 1
            else:
                stats["red"] += 1
        
        # 计算平均分
        for role, stats in role_stats.items():
            scores = stats.pop("scores")
            stats["avg_score"] = round(sum(scores) / len(scores), 1) if scores else 0
        
        # 全局 top 告警项 (按红色频率)
        alert_frequency = {}
        for report in reports:
            for item in report.items:
                if item.color == HealthColor.RED:
                    key = item.code
                    if key not in alert_frequency:
                        alert_frequency[key] = {"code": key, "title": item.title, "count": 0}
                    alert_frequency[key]["count"] += 1
        
        top_alerts = sorted(alert_frequency.values(), key=lambda x: -x["count"])[:10]
        
        total_users = len(reports)
        total_green = sum(s["green"] for s in role_stats.values())
        total_red = sum(s["red"] for s in role_stats.values())
        
        return {
            "total_users": total_users,
            "overall_health_rate": round(total_green / total_users * 100, 1) if total_users else 0,
            "red_alert_count": total_red,
            "role_breakdown": role_stats,
            "top_alerts": top_alerts,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    
    # ── 2.3 告警管道 ──
    
    async def process_alerts(
        self, reports: List[UserHealthReport]
    ) -> List[Dict[str, Any]]:
        """处理告警升级"""
        alerts = []
        
        for report in reports:
            for item in report.items:
                if item.color == HealthColor.RED and item.needs_action:
                    # 查找责任项定义
                    reg_item = next(
                        (r for r in RESPONSIBILITY_REGISTRY if r.code == item.code), None
                    )
                    
                    alert = {
                        "user_id": report.user_id,
                        "role": report.role,
                        "level": report.level,
                        "code": item.code,
                        "title": item.title,
                        "message": item.alert_message,
                        "current_value": item.current_value,
                        "threshold": item.threshold_desc,
                        "severity": "high",
                        "auto_escalation": reg_item.escalation_target if reg_item else "",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    alerts.append(alert)
        
        return alerts


# ══════════════════════════════════════════
# 3. 仪表盘 API 端点
# ══════════════════════════════════════════

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/v1/governance", tags=["governance-dashboard"])


class CoachKPIRequest(BaseModel):
    coach_id: int
    metrics: Dict[str, Any]


class OrgOverviewRequest(BaseModel):
    user_reports: List[Dict]  # 简化: 预计算的报告


@router.get("/responsibility/{user_id}")
async def get_responsibility_report(user_id: int, level: str = "L1"):
    """获取用户责任健康报告"""
    tracker = ResponsibilityTracker()
    report = await tracker.generate_health_report(user_id, level)
    return {
        "user_id": report.user_id,
        "role": report.role,
        "level": report.level,
        "overall_color": report.overall_color.value,
        "health_score": report.health_score,
        "green": report.green_count,
        "yellow": report.yellow_count,
        "red": report.red_count,
        "items": [
            {
                "code": i.code, "title": i.title, "color": i.color.value,
                "current_value": i.current_value, "threshold": i.threshold_desc,
                "alert": i.alert_message,
            }
            for i in report.items
        ],
    }


@router.post("/coach-kpi")
async def get_coach_kpi(req: CoachKPIRequest):
    """教练KPI红绿灯仪表盘"""
    dashboard = GovernanceDashboard()
    return await dashboard.get_coach_kpi_dashboard(req.coach_id, req.metrics)


@router.get("/responsibility-registry")
async def get_registry():
    """责任注册表概览"""
    tracker = ResponsibilityTracker()
    return tracker.get_all_registry_stats()


@router.get("/responsibility-registry/{role}")
async def get_role_responsibilities(role: str):
    """按角色查询责任项"""
    tracker = ResponsibilityTracker()
    items = tracker.get_responsibilities_for_role(role)
    if not items:
        raise HTTPException(404, f"Role not found: {role}")
    return {"role": role, "items": items, "count": len(items)}


@router.get("/kpi-definitions")
async def get_kpi_definitions():
    """KPI定义列表"""
    return {
        "kpis": [
            {
                "kpi_id": k.kpi_id, "name": k.name, "description": k.description,
                "green_rule": k.green_rule, "yellow_rule": k.yellow_rule,
                "red_rule": k.red_rule, "auto_escalation": k.auto_escalation,
            }
            for k in COACH_KPI_DEFINITIONS
        ],
        "total": len(COACH_KPI_DEFINITIONS),
    }
