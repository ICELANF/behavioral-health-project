"""
CR-15 修复: governance_health_check 定期检查服务
契约要求: ⑥责任追踪契约 — 治理健康度定期巡检
审计状态: ❌未实现 → ✅已对齐
文件: core/governance_health_check.py (新建)
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

# ── 健康度指标枚举 ──────────────────────────────────────
class HealthStatus(str, Enum):
    HEALTHY = "healthy"          # 所有指标正常
    DEGRADED = "degraded"        # 部分指标异常但不影响核心功能
    CRITICAL = "critical"        # 关键指标异常, 需立即干预
    UNKNOWN = "unknown"          # 无法评估(数据不足)


class HealthDimension(str, Enum):
    """治理健康度 6 维度 — 对应 ResponsibilityMetric 模型"""
    CONTRACT_COMPLIANCE = "contract_compliance"      # 契约遵从率
    AUDIT_COVERAGE = "audit_coverage"                # 审计覆盖率
    VIOLATION_TREND = "violation_trend"              # 违规趋势
    RESPONSE_LATENCY = "response_latency"            # 治理响应时效
    COACH_ACCOUNTABILITY = "coach_accountability"    # 教练履责率
    DATA_INTEGRITY = "data_integrity"                # 数据完整性


# ── 检查结果模型 ─────────────────────────────────────────
@dataclass
class DimensionResult:
    dimension: HealthDimension
    status: HealthStatus
    score: float                  # 0.0 ~ 1.0
    detail: str = ""
    checked_at: datetime = field(default_factory=datetime.utcnow)
    sample_size: int = 0


@dataclass
class HealthCheckReport:
    overall_status: HealthStatus
    dimensions: list[DimensionResult]
    checked_at: datetime
    next_check_at: datetime
    summary: str = ""

    @property
    def overall_score(self) -> float:
        if not self.dimensions:
            return 0.0
        return sum(d.score for d in self.dimensions) / len(self.dimensions)

    def to_dict(self) -> dict:
        return {
            "overall_status": self.overall_status.value,
            "overall_score": round(self.overall_score, 3),
            "checked_at": self.checked_at.isoformat(),
            "next_check_at": self.next_check_at.isoformat(),
            "summary": self.summary,
            "dimensions": [
                {
                    "dimension": d.dimension.value,
                    "status": d.status.value,
                    "score": round(d.score, 3),
                    "detail": d.detail,
                    "sample_size": d.sample_size,
                }
                for d in self.dimensions
            ],
        }


# ── 阈值配置 ─────────────────────────────────────────────
THRESHOLDS = {
    HealthDimension.CONTRACT_COMPLIANCE: {"healthy": 0.95, "degraded": 0.80},
    HealthDimension.AUDIT_COVERAGE: {"healthy": 0.90, "degraded": 0.70},
    HealthDimension.VIOLATION_TREND: {"healthy": 0.90, "degraded": 0.70},
    HealthDimension.RESPONSE_LATENCY: {"healthy": 0.85, "degraded": 0.60},
    HealthDimension.COACH_ACCOUNTABILITY: {"healthy": 0.90, "degraded": 0.75},
    HealthDimension.DATA_INTEGRITY: {"healthy": 0.95, "degraded": 0.85},
}

CHECK_INTERVAL_HOURS = 6  # 每6小时检查一次


def _score_to_status(dimension: HealthDimension, score: float) -> HealthStatus:
    t = THRESHOLDS[dimension]
    if score >= t["healthy"]:
        return HealthStatus.HEALTHY
    elif score >= t["degraded"]:
        return HealthStatus.DEGRADED
    else:
        return HealthStatus.CRITICAL


# ── 核心检查服务 ──────────────────────────────────────────
class GovernanceHealthCheckService:
    """
    治理健康度定期检查服务

    设计原则:
    - 6维度全覆盖(契约遵从/审计覆盖/违规趋势/响应时效/教练履责/数据完整)
    - 每个维度独立评分(0~1), 汇总为整体状态
    - 支持定时调度(Celery Beat)和手动触发(API)
    - 检查结果写入 ResponsibilityMetric 表
    """

    def __init__(self, db: Session):
        self.db = db

    def run_full_check(self) -> HealthCheckReport:
        """执行全量健康检查 — 6维度"""
        now = datetime.utcnow()
        results = []

        results.append(self._check_contract_compliance())
        results.append(self._check_audit_coverage())
        results.append(self._check_violation_trend())
        results.append(self._check_response_latency())
        results.append(self._check_coach_accountability())
        results.append(self._check_data_integrity())

        overall = self._aggregate_status(results)
        report = HealthCheckReport(
            overall_status=overall,
            dimensions=results,
            checked_at=now,
            next_check_at=now + timedelta(hours=CHECK_INTERVAL_HOURS),
            summary=self._build_summary(results),
        )

        self._persist_report(report)
        return report

    # ── 维度1: 契约遵从率 ──
    def _check_contract_compliance(self) -> DimensionResult:
        """检查用户契约签署和遵从情况"""
        dim = HealthDimension.CONTRACT_COMPLIANCE
        try:
            # 统计活跃用户中已签署契约的比例
            from core.models import User, UserContract
            total = self.db.scalar(
                select(func.count(User.id)).where(User.is_active == True)
            )
            if not total or total == 0:
                return DimensionResult(dim, HealthStatus.UNKNOWN, 0.0,
                                       "无活跃用户数据", sample_size=0)
            signed = self.db.scalar(
                select(func.count(UserContract.id)).where(
                    UserContract.status == "active"
                )
            )
            score = (signed or 0) / total
            status = _score_to_status(dim, score)
            return DimensionResult(
                dim, status, score,
                f"活跃用户{total}, 已签约{signed}",
                sample_size=total,
            )
        except Exception as e:
            return DimensionResult(dim, HealthStatus.UNKNOWN, 0.0,
                                   f"检查异常: {e}", sample_size=0)

    # ── 维度2: 审计覆盖率 ──
    def _check_audit_coverage(self) -> DimensionResult:
        """检查审计日志覆盖关键操作的比例"""
        dim = HealthDimension.AUDIT_COVERAGE
        try:
            from core.models import BehaviorAuditLog
            window = datetime.utcnow() - timedelta(hours=CHECK_INTERVAL_HOURS)

            # 近一周期内审计日志条数
            audit_count = self.db.scalar(
                select(func.count(BehaviorAuditLog.id)).where(
                    BehaviorAuditLog.created_at >= window
                )
            )
            # 与预期操作量对比(基于API调用日志)
            from core.models import UserActivityLog
            activity_count = self.db.scalar(
                select(func.count(UserActivityLog.id)).where(
                    UserActivityLog.created_at >= window
                )
            )
            if not activity_count or activity_count == 0:
                return DimensionResult(dim, HealthStatus.UNKNOWN, 1.0,
                                       "周期内无活动", sample_size=0)
            score = min((audit_count or 0) / activity_count, 1.0)
            return DimensionResult(
                dim, _score_to_status(dim, score), score,
                f"审计{audit_count}条/活动{activity_count}条",
                sample_size=activity_count,
            )
        except Exception as e:
            return DimensionResult(dim, HealthStatus.UNKNOWN, 0.0,
                                   f"检查异常: {e}")

    # ── 维度3: 违规趋势 ──
    def _check_violation_trend(self) -> DimensionResult:
        """对比本周期与上周期违规数量, 趋势向好=高分"""
        dim = HealthDimension.VIOLATION_TREND
        try:
            from core.models import GovernanceViolation
            now = datetime.utcnow()
            current_window = now - timedelta(hours=CHECK_INTERVAL_HOURS)
            prev_window = current_window - timedelta(hours=CHECK_INTERVAL_HOURS)

            current_count = self.db.scalar(
                select(func.count(GovernanceViolation.id)).where(
                    GovernanceViolation.created_at >= current_window
                )
            ) or 0
            prev_count = self.db.scalar(
                select(func.count(GovernanceViolation.id)).where(
                    and_(
                        GovernanceViolation.created_at >= prev_window,
                        GovernanceViolation.created_at < current_window,
                    )
                )
            ) or 0

            if prev_count == 0 and current_count == 0:
                score = 1.0
                detail = "无违规记录"
            elif prev_count == 0:
                score = 0.5
                detail = f"新增{current_count}条违规(前期无记录)"
            else:
                ratio = current_count / prev_count
                score = max(0.0, min(1.0, 1.0 - (ratio - 1.0)))
                trend = "↓下降" if ratio < 1 else ("→持平" if ratio == 1 else "↑上升")
                detail = f"本期{current_count}/前期{prev_count} ({trend})"

            return DimensionResult(
                dim, _score_to_status(dim, score), score, detail,
                sample_size=current_count + prev_count,
            )
        except Exception as e:
            return DimensionResult(dim, HealthStatus.UNKNOWN, 0.0,
                                   f"检查异常: {e}")

    # ── 维度4: 治理响应时效 ──
    def _check_response_latency(self) -> DimensionResult:
        """检查违规事件的平均响应时间是否在SLA内"""
        dim = HealthDimension.RESPONSE_LATENCY
        try:
            from core.models import GovernanceViolation
            window = datetime.utcnow() - timedelta(hours=CHECK_INTERVAL_HOURS * 4)

            result = self.db.execute(
                select(GovernanceViolation).where(
                    and_(
                        GovernanceViolation.created_at >= window,
                        GovernanceViolation.resolved_at.isnot(None),
                    )
                )
            )
            violations = result.scalars().all()

            if not violations:
                return DimensionResult(dim, HealthStatus.HEALTHY, 1.0,
                                       "无需响应的违规", sample_size=0)

            SLA_HOURS = 24
            within_sla = sum(
                1 for v in violations
                if (v.resolved_at - v.created_at).total_seconds() <= SLA_HOURS * 3600
            )
            score = within_sla / len(violations)
            return DimensionResult(
                dim, _score_to_status(dim, score), score,
                f"SLA内{within_sla}/{len(violations)}, SLA={SLA_HOURS}h",
                sample_size=len(violations),
            )
        except Exception as e:
            return DimensionResult(dim, HealthStatus.UNKNOWN, 0.0,
                                   f"检查异常: {e}")

    # ── 维度5: 教练履责率 ──
    def _check_coach_accountability(self) -> DimensionResult:
        """检查教练是否按时完成待办推送和学员反馈"""
        dim = HealthDimension.COACH_ACCOUNTABILITY
        try:
            from core.models import CoachPushQueue
            window = datetime.utcnow() - timedelta(hours=CHECK_INTERVAL_HOURS * 4)

            total = self.db.scalar(
                select(func.count(CoachPushQueue.id)).where(
                    CoachPushQueue.created_at >= window
                )
            )
            if not total or total == 0:
                return DimensionResult(dim, HealthStatus.HEALTHY, 1.0,
                                       "无待处理推送", sample_size=0)

            completed = self.db.scalar(
                select(func.count(CoachPushQueue.id)).where(
                    and_(
                        CoachPushQueue.created_at >= window,
                        CoachPushQueue.status == "completed",
                    )
                )
            )
            score = (completed or 0) / total
            return DimensionResult(
                dim, _score_to_status(dim, score), score,
                f"完成{completed}/{total}",
                sample_size=total,
            )
        except Exception as e:
            return DimensionResult(dim, HealthStatus.UNKNOWN, 0.0,
                                   f"检查异常: {e}")

    # ── 维度6: 数据完整性 ──
    def _check_data_integrity(self) -> DimensionResult:
        """检查关键数据字段的完整性(非空率)"""
        dim = HealthDimension.DATA_INTEGRITY
        try:
            from core.models import User, JourneyStageV4
            total_users = self.db.scalar(
                select(func.count(User.id)).where(User.is_active == True)
            )
            if not total_users or total_users == 0:
                return DimensionResult(dim, HealthStatus.UNKNOWN, 0.0,
                                       "无活跃用户", sample_size=0)

            # 检查关键字段: journey_stage 必须存在
            has_stage = self.db.scalar(
                select(func.count(JourneyStageV4.id))
            )
            score = min((has_stage or 0) / total_users, 1.0)
            return DimensionResult(
                dim, _score_to_status(dim, score), score,
                f"阶段记录{has_stage}/用户{total_users}",
                sample_size=total_users,
            )
        except Exception as e:
            return DimensionResult(dim, HealthStatus.UNKNOWN, 0.0,
                                   f"检查异常: {e}")

    # ── 汇总 ──
    def _aggregate_status(self, results: list[DimensionResult]) -> HealthStatus:
        statuses = [r.status for r in results]
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        return HealthStatus.DEGRADED

    def _build_summary(self, results: list[DimensionResult]) -> str:
        critical = [r for r in results if r.status == HealthStatus.CRITICAL]
        degraded = [r for r in results if r.status == HealthStatus.DEGRADED]
        parts = []
        if critical:
            dims = ", ".join(r.dimension.value for r in critical)
            parts.append(f"🔴严重: {dims}")
        if degraded:
            dims = ", ".join(r.dimension.value for r in degraded)
            parts.append(f"🟡降级: {dims}")
        if not parts:
            parts.append("🟢全部健康")
        return "; ".join(parts)

    def _persist_report(self, report: HealthCheckReport):
        """将检查结果写入 ResponsibilityMetric 表"""
        try:
            from core.models import ResponsibilityMetric
            metric = ResponsibilityMetric(
                metric_type="governance_health_check",
                value=report.overall_score,
                status=report.overall_status.value,
                detail=report.to_dict(),
                checked_at=report.checked_at,
            )
            self.db.add(metric)
            self.db.commit()
        except Exception:
            self.db.rollback()
