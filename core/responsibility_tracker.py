"""
V4.0 Responsibility Auto-Tracking Service — 责任自动追踪

Sheet ⑥ 责任追踪契约:
  成长者 GRW-01~06: 数据录入/方案交互/持续学习/社区规范/配合教练/安全告知
  分享者 SHR-01~05: 内容真实/同道者带教/不传播未证实信息/社区贡献/示范作用
  教练   COA-01~10: 学员关怀/消息响应/告警处理/专业准确/持续学习/评估跟进/伦理/转介/带教质量/数据安全
  促进师 PRO-01~07: 督导/内容证据/Agent质量/工作室运营/培训义务/知识贡献/利益冲突
  大师   MAS-01~06: 行业引领/标准维护/高级督导/人才培养/知识贡献/生态建设
"""
from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.models import ResponsibilityMetric, User, ROLE_LEVEL_STR

logger = logging.getLogger(__name__)

# ── Metric Definitions ───────────────────────────────────
METRIC_DEFINITIONS = {
    # Grower metrics
    "GRW-01": {"label": "如实记录健康数据", "threshold": 3, "unit": "次/周", "roles": ["grower"],
               "alert_rule": "连续7天无录入→温和提醒"},
    "GRW-02": {"label": "积极参与方案交互", "threshold": 0.6, "unit": "完成率", "roles": ["grower"],
               "alert_rule": "连续3天未交互→AI推送"},
    "GRW-03": {"label": "持续学习", "threshold": 30, "unit": "分钟/周", "roles": ["grower"],
               "alert_rule": "连续2周未学习→引导推送"},
    "GRW-04": {"label": "遵守社区规范", "threshold": 0.03, "unit": "拦截率上限", "roles": ["grower"],
               "alert_rule": ">5%→内容警告"},
    "GRW-05": {"label": "配合教练指导", "threshold": 0.8, "unit": "回复率", "roles": ["grower"],
               "alert_rule": "连续3条未复→教练提醒"},
    "GRW-06": {"label": "安全告知", "threshold": 0, "unit": "触发次数", "roles": ["grower"],
               "alert_rule": "高风险→即时通知"},
    # Sharer metrics
    "SHR-01": {"label": "内容真实准确", "threshold": 0.8, "unit": "通过率", "roles": ["sharer"],
               "alert_rule": "连续3篇退回→内容培训"},
    "SHR-02": {"label": "同道者带教责任", "threshold": 0.6, "unit": "毕业率", "roles": ["sharer"],
               "alert_rule": "低于50%→影响晋级"},
    "SHR-03": {"label": "不传播未证实信息", "threshold": 0, "unit": "拦截次数", "roles": ["sharer"],
               "alert_rule": "单月>2次→培训提醒"},
    "SHR-04": {"label": "社区积极贡献", "threshold": 3, "unit": "回复/周", "roles": ["sharer"],
               "alert_rule": "连续2周无回复→温和引导"},
    "SHR-05": {"label": "示范作用", "threshold": 0.7, "unit": "月活跃度", "roles": ["sharer"],
               "alert_rule": "连续月<50%→提醒"},
    # Coach metrics
    "COA-01": {"label": "学员关怀(定期查看数据)", "threshold": 1, "unit": "次/周/学员", "roles": ["coach"],
               "alert_rule": "连续2周未查看→黄色"},
    "COA-02": {"label": "消息及时响应", "threshold": 24, "unit": "小时", "roles": ["coach"],
               "alert_rule": "超48h→红色告警"},
    "COA-03": {"label": "告警及时处理", "threshold": 4, "unit": "小时(高风险)", "roles": ["coach"],
               "alert_rule": "超时→升级Admin"},
    "COA-04": {"label": "专业准确性", "threshold": 0.05, "unit": "拦截率上限", "roles": ["coach"],
               "alert_rule": ">10%→培训提醒"},
    "COA-05": {"label": "持续学习(1500学分)", "threshold": 25, "unit": "学分/季度", "roles": ["coach"],
               "alert_rule": "连续2季度不达标→复评"},
    "COA-06": {"label": "评估跟进", "threshold": 7, "unit": "天", "roles": ["coach"],
               "alert_rule": "超14天→自动提醒"},
    "COA-07": {"label": "伦理遵守", "threshold": 0, "unit": "投诉/月", "roles": ["coach"],
               "alert_rule": "单月≥2→督导介入"},
    "COA-08": {"label": "转介义务", "threshold": 1.0, "unit": "合规率", "roles": ["coach"],
               "alert_rule": "未转介→培训触发"},
    "COA-09": {"label": "带教质量", "threshold": 0.7, "unit": "毕业率", "roles": ["coach"],
               "alert_rule": "低于阈值→影响晋级"},
    "COA-10": {"label": "数据安全", "threshold": 0, "unit": "越权次数", "roles": ["coach"],
               "alert_rule": "异常→锁定+通知Admin"},
    # Promoter metrics
    "PRO-01": {"label": "督导下级教练", "threshold": 2, "unit": "次/月", "roles": ["promoter", "supervisor"],
               "alert_rule": "不达标→季度考核扣分"},
    "PRO-02": {"label": "内容证据分级", "threshold": 0.7, "unit": "T1+T2占比", "roles": ["promoter", "supervisor"],
               "alert_rule": "T3+T4>50%→审查"},
    "PRO-03": {"label": "Agent质量", "threshold": 4.0, "unit": "平均评分", "roles": ["promoter", "supervisor"],
               "alert_rule": "<3.5→模板下架审查"},
    "PRO-04": {"label": "工作室运营", "threshold": 0.5, "unit": "月活跃", "roles": ["promoter", "supervisor"],
               "alert_rule": "<30%→运营建议推送"},
    "PRO-05": {"label": "培训义务", "threshold": 1, "unit": "次/季度", "roles": ["promoter", "supervisor"],
               "alert_rule": "连续2季0→降级预警"},
    "PRO-06": {"label": "知识贡献", "threshold": 1, "unit": "篇/月", "roles": ["promoter", "supervisor"],
               "alert_rule": "连续3月0→贡献提醒"},
    "PRO-07": {"label": "利益冲突披露", "threshold": 1, "unit": "半年更新", "roles": ["promoter", "supervisor"],
               "alert_rule": "过期→限制部分权限"},
    # Master metrics
    "MAS-01": {"label": "行业引领(持续产出)", "threshold": 1, "unit": "篇/季度", "roles": ["master"],
               "alert_rule": "连续2季0→影响力评估"},
    "MAS-02": {"label": "标准维护参与", "threshold": 1, "unit": "次/半年", "roles": ["master"],
               "alert_rule": "1年未参→治理讨论邀请"},
    "MAS-03": {"label": "高级督导", "threshold": 2, "unit": "次/季度", "roles": ["master"],
               "alert_rule": "连续2季0→督导提醒"},
    "MAS-04": {"label": "人才培养", "threshold": 2, "unit": "名L4+/年", "roles": ["master"],
               "alert_rule": "持续无培养→评估讨论"},
    "MAS-05": {"label": "知识贡献", "threshold": 2, "unit": "篇/月", "roles": ["master"],
               "alert_rule": "连续3月不达标→沟通"},
    "MAS-06": {"label": "生态建设", "threshold": 1, "unit": "项/季度", "roles": ["master"],
               "alert_rule": "连续2季0→引导讨论"},
}


class ResponsibilityTracker:
    """责任自动追踪服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_metrics(self, user_id: int) -> dict:
        """获取用户所有责任指标的当前状态"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "用户不存在"}

        role = user.role.value if hasattr(user.role, 'value') else user.role
        applicable = {
            code: defn for code, defn in METRIC_DEFINITIONS.items()
            if role in defn["roles"]
        }

        today = date.today()
        period_start = today - timedelta(days=30)

        metrics = []
        for code, defn in applicable.items():
            # Get latest metric record
            record = self.db.query(ResponsibilityMetric).filter(
                ResponsibilityMetric.user_id == user_id,
                ResponsibilityMetric.metric_code == code,
                ResponsibilityMetric.period_start >= period_start,
            ).order_by(ResponsibilityMetric.created_at.desc()).first()

            metrics.append({
                "code": code,
                "label": defn["label"],
                "threshold": defn["threshold"],
                "unit": defn["unit"],
                "alert_rule": defn["alert_rule"],
                "current_value": record.metric_value if record else None,
                "status": record.status if record else "no_data",
                "last_updated": record.updated_at.isoformat() if record and record.updated_at else None,
            })

        # Calculate overall health
        total = len(metrics)
        healthy = sum(1 for m in metrics if m["status"] == "healthy")
        warning = sum(1 for m in metrics if m["status"] == "warning")
        critical = sum(1 for m in metrics if m["status"] == "critical")

        return {
            "user_id": user_id,
            "role": role,
            "total_metrics": total,
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "no_data": total - healthy - warning - critical,
            "health_score": round(healthy / total * 100, 1) if total > 0 else 0,
            "metrics": metrics,
        }

    def record_metric(self, user_id: int, metric_code: str, value: float,
                      period_start: date = None, period_end: date = None) -> dict:
        """记录一条责任指标数据"""
        defn = METRIC_DEFINITIONS.get(metric_code)
        if not defn:
            return {"error": f"未知指标: {metric_code}"}

        today = date.today()
        if not period_start:
            period_start = today - timedelta(days=7)
        if not period_end:
            period_end = today

        threshold = defn["threshold"]
        # Determine status
        if metric_code in ("GRW-04", "SHR-03", "COA-04", "COA-07", "COA-10"):
            # Lower is better
            if value <= threshold:
                status = "healthy"
            elif value <= threshold * 2:
                status = "warning"
            else:
                status = "critical"
        else:
            # Higher is better
            if value >= threshold:
                status = "healthy"
            elif value >= threshold * 0.5:
                status = "warning"
            else:
                status = "critical"

        record = ResponsibilityMetric(
            user_id=user_id,
            metric_code=metric_code,
            metric_value=value,
            threshold_value=threshold,
            status=status,
            period_start=period_start,
            period_end=period_end,
        )
        self.db.add(record)
        self.db.flush()

        return {
            "id": record.id,
            "metric_code": metric_code,
            "value": value,
            "threshold": threshold,
            "status": status,
            "label": defn["label"],
        }

    def get_governance_health(self) -> dict:
        """获取平台整体治理健康状态（管理员视图）"""
        today = date.today()
        period_start = today - timedelta(days=30)

        # Count by status
        status_counts = self.db.query(
            ResponsibilityMetric.status,
            func.count(ResponsibilityMetric.id),
        ).filter(
            ResponsibilityMetric.period_start >= period_start,
        ).group_by(ResponsibilityMetric.status).all()

        counts = {s: c for s, c in status_counts}

        # Critical users
        critical_users = self.db.query(
            ResponsibilityMetric.user_id,
            func.count(ResponsibilityMetric.id).label("cnt"),
        ).filter(
            ResponsibilityMetric.status == "critical",
            ResponsibilityMetric.period_start >= period_start,
        ).group_by(ResponsibilityMetric.user_id).order_by(
            func.count(ResponsibilityMetric.id).desc()
        ).limit(10).all()

        return {
            "period": f"{period_start.isoformat()} ~ {today.isoformat()}",
            "total_records": sum(counts.values()),
            "healthy": counts.get("healthy", 0),
            "warning": counts.get("warning", 0),
            "critical": counts.get("critical", 0),
            "critical_users": [
                {"user_id": uid, "critical_count": cnt}
                for uid, cnt in critical_users
            ],
        }

    def get_all_definitions(self) -> dict:
        """获取所有责任指标定义"""
        by_role = {}
        for code, defn in METRIC_DEFINITIONS.items():
            for role in defn["roles"]:
                by_role.setdefault(role, []).append({
                    "code": code,
                    "label": defn["label"],
                    "threshold": defn["threshold"],
                    "unit": defn["unit"],
                    "alert_rule": defn["alert_rule"],
                })
        return by_role
