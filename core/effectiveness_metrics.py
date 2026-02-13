"""
V007 Step 13 / Phase C
Effectiveness Metrics: 效果量化体系 (6 metrics)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EffectivenessMetrics:
    """效果量化引擎 — 6 metrics"""

    def __init__(self, db_session: Session):
        self._db = db_session

    # === 1. IES (Intervention Effectiveness Score) ===

    def calc_ies(self, user_id: int, agent_id: str, period_days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=period_days)

        stage_delta = self._calc_stage_delta(user_id, agent_id, cutoff)
        task_completion = self._calc_task_completion(user_id, cutoff)
        data_trend = self._calc_data_trend(user_id, cutoff)

        ies = round(stage_delta * 0.4 + task_completion * 0.3 + data_trend * 0.3, 4)

        return {
            "user_id": user_id, "agent_id": agent_id,
            "ies_score": ies, "period_days": period_days,
            "components": {
                "stage_delta": round(stage_delta, 4),
                "task_completion": round(task_completion, 4),
                "data_trend": round(data_trend, 4),
            },
            "interpretation": self._interpret_ies(ies),
        }

    # === 2. Stage Transition Rate ===

    def calc_stage_transition_rate(self, user_id=None, agent_id=None,
                                    period_days: int = 90) -> Dict[str, Any]:
        try:
            from core.models import PolicyStageTransitionLog
        except ImportError:
            return {"rate": 0, "error": "PolicyStageTransitionLog not available"}

        cutoff = datetime.utcnow() - timedelta(days=period_days)
        query = self._db.query(PolicyStageTransitionLog).filter(
            PolicyStageTransitionLog.created_at >= cutoff
        )
        if user_id:
            query = query.filter(PolicyStageTransitionLog.user_id == user_id)
        if agent_id:
            query = query.filter(PolicyStageTransitionLog.trigger_agent_id == agent_id)

        transitions = query.all()
        stage_order = {'S0': 0, 'S1': 1, 'S2': 2, 'S3': 3, 'S4': 4, 'S5': 5, 'S6': 6}

        forward = backward = 0
        for t in transitions:
            from_val = stage_order.get(t.from_stage, 0)
            to_val = stage_order.get(t.to_stage, 0)
            if to_val > from_val:
                forward += 1
            elif to_val < from_val:
                backward += 1

        rate = (forward - backward) / max(period_days, 1)

        return {
            "stage_transition_rate": round(rate, 6),
            "forward_transitions": forward,
            "backward_transitions": backward,
            "net_transitions": forward - backward,
            "period_days": period_days,
            "total_transitions": len(transitions),
        }

    # === 3. Adherence Index ===

    def calc_adherence_index(self, user_id: int, period_days: int = 30) -> Dict[str, Any]:
        task_rate = self._calc_task_completion(
            user_id, datetime.utcnow() - timedelta(days=period_days))
        challenge_rate = 0.5  # placeholder

        index = round(task_rate * 0.6 + challenge_rate * 0.4, 4)

        return {
            "user_id": user_id, "adherence_index": index,
            "task_completion_rate": round(task_rate, 4),
            "challenge_completion_rate": round(challenge_rate, 4),
            "period_days": period_days,
            "level": self._adherence_level(index),
        }

    # === 4. Risk Reduction Index ===

    def calc_risk_reduction(self, user_id: int, period_days: int = 30) -> Dict[str, Any]:
        trend = self._calc_data_trend(
            user_id, datetime.utcnow() - timedelta(days=period_days))
        risk_delta = -trend

        return {
            "user_id": user_id,
            "risk_reduction_index": round(risk_delta, 4),
            "interpretation": "improved" if risk_delta < 0 else "worsened" if risk_delta > 0 else "stable",
            "period_days": period_days,
        }

    # === 5. Expert ROI ===

    def calc_expert_roi(self, agent_id: str, tenant_id=None,
                         period_days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=period_days)

        try:
            from core.models import PolicyInterventionOutcome, DecisionTrace

            avg_ies = self._db.query(
                func.avg(PolicyInterventionOutcome.ies_score)
            ).filter(
                PolicyInterventionOutcome.agent_id == agent_id,
                PolicyInterventionOutcome.created_at >= cutoff,
            ).scalar() or 0

            cost_query = self._db.query(
                func.avg(DecisionTrace.token_cost)
            ).filter(
                DecisionTrace.final_output == agent_id,
                DecisionTrace.created_at >= cutoff,
            )
            if tenant_id:
                cost_query = cost_query.filter(DecisionTrace.tenant_id == tenant_id)
            avg_cost = cost_query.scalar() or 1

            user_count = self._db.query(
                func.count(func.distinct(DecisionTrace.user_id))
            ).filter(
                DecisionTrace.final_output == agent_id,
                DecisionTrace.created_at >= cutoff,
            ).scalar() or 0

        except Exception:
            avg_ies = 0
            avg_cost = 1
            user_count = 0

        roi = round(float(avg_ies) / max(float(avg_cost) / 1000, 0.001), 4)

        return {
            "agent_id": agent_id, "expert_roi": roi,
            "avg_ies": round(float(avg_ies), 4),
            "avg_token_cost": round(float(avg_cost), 2),
            "users_served": user_count,
            "period_days": period_days,
        }

    # === 6. Ecosystem Health Score ===

    def calc_ecosystem_health(self, tenant_id=None, period_days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=period_days)

        try:
            from core.models import DecisionTrace

            query = self._db.query(DecisionTrace).filter(
                DecisionTrace.created_at >= cutoff
            )
            if tenant_id:
                query = query.filter(DecisionTrace.tenant_id == tenant_id)

            traces = query.all()
            total = len(traces)

            if total == 0:
                return {"score": 0, "message": "No data in period"}

            active_agents = set(t.final_output for t in traces)
            agent_diversity = min(len(active_agents) / 12, 1.0)

            conflicts = sum(1 for t in traces if t.conflict_resolution)
            conflict_rate = conflicts / total

            avg_latency = sum(t.latency_ms or 0 for t in traces) / total
            unique_users = len(set(t.user_id for t in traces))

        except Exception:
            return {"score": 0.5, "message": "Calculation error"}

        health = round(
            agent_diversity * 0.3 +
            (1 - min(conflict_rate, 1.0)) * 0.2 +
            (1 - min(avg_latency / 5000, 1.0)) * 0.2 +
            min(unique_users / 100, 1.0) * 0.3,
            4
        )

        return {
            "ecosystem_health_score": health,
            "components": {
                "agent_diversity": round(agent_diversity, 4),
                "conflict_rate": round(conflict_rate, 4),
                "avg_latency_ms": round(avg_latency, 1),
                "unique_users": unique_users,
                "total_decisions": total,
                "active_agents": list(active_agents),
            },
            "tenant_id": tenant_id,
            "period_days": period_days,
        }

    # === Full Report ===

    def generate_full_report(self, user_id: int, agent_id: str,
                              period_days: int = 30) -> Dict[str, Any]:
        return {
            "report_type": "effectiveness_full",
            "generated_at": datetime.utcnow().isoformat(),
            "user_id": user_id, "agent_id": agent_id,
            "period_days": period_days,
            "metrics": {
                "ies": self.calc_ies(user_id, agent_id, period_days),
                "stage_transition": self.calc_stage_transition_rate(user_id, agent_id, period_days),
                "adherence": self.calc_adherence_index(user_id, period_days),
                "risk_reduction": self.calc_risk_reduction(user_id, period_days),
                "expert_roi": self.calc_expert_roi(agent_id, period_days=period_days),
            }
        }

    # === Internal ===

    def _calc_stage_delta(self, user_id, agent_id, cutoff):
        try:
            from core.models import PolicyStageTransitionLog
            transitions = self._db.query(PolicyStageTransitionLog).filter(
                PolicyStageTransitionLog.user_id == user_id,
                PolicyStageTransitionLog.trigger_agent_id == agent_id,
                PolicyStageTransitionLog.created_at >= cutoff,
            ).all()

            if not transitions:
                return 0.0

            stage_order = {'S0': 0, 'S1': 1, 'S2': 2, 'S3': 3, 'S4': 4, 'S5': 5, 'S6': 6}
            total_delta = sum(
                stage_order.get(t.to_stage, 0) - stage_order.get(t.from_stage, 0)
                for t in transitions
            )
            return max(-1.0, min(1.0, total_delta / max(len(transitions), 1) / 3))
        except Exception:
            return 0.0

    def _calc_task_completion(self, user_id, cutoff):
        return 0.6  # placeholder

    def _calc_data_trend(self, user_id, cutoff):
        return 0.1  # placeholder

    @staticmethod
    def _interpret_ies(ies):
        if ies >= 0.7: return "significant_improvement"
        elif ies >= 0.3: return "clear_improvement"
        elif ies >= 0.1: return "slight_improvement"
        elif ies >= -0.1: return "no_change"
        elif ies >= -0.3: return "slight_decline"
        else: return "clear_decline"

    @staticmethod
    def _adherence_level(index):
        if index >= 0.8: return "excellent"
        elif index >= 0.6: return "good"
        elif index >= 0.4: return "moderate"
        else: return "low"
