"""
V007 Step 05 / Phase A
Decision Trace: 决策追踪器
"""

import logging
import uuid
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DecisionTraceRecorder:
    """决策追踪记录器"""

    def __init__(self, db_session: Session):
        self._db = db_session

    def record(
        self, event_id: str, user_id: int,
        tenant_id: Optional[str], session_id: Optional[str],
        triggered_agents: List[dict], policy_applied: List[dict],
        rule_weights: Dict[str, float],
        conflict_resolution: Optional[dict],
        final_output: str,
        secondary_agents: Optional[List[str]] = None,
        llm_model: Optional[str] = None,
        token_cost: int = 0, latency_ms: int = 0,
    ) -> str:
        from core.models import DecisionTrace

        trace = DecisionTrace(
            id=uuid.uuid4(),
            event_id=event_id,
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            triggered_agents=triggered_agents,
            policy_applied=policy_applied,
            rule_weights=rule_weights,
            conflict_resolution=conflict_resolution,
            final_output=final_output,
            secondary_agents=secondary_agents,
            llm_model=llm_model,
            token_cost=token_cost,
            latency_ms=latency_ms,
        )

        self._db.add(trace)
        self._db.commit()

        logger.info(
            f"DecisionTrace recorded: {trace.id} | "
            f"user={user_id} | final={final_output} | "
            f"candidates={len(triggered_agents)} | cost={token_cost}t"
        )
        return str(trace.id)

    def query_by_user(self, user_id: int, limit: int = 20, offset: int = 0) -> List[dict]:
        from core.models import DecisionTrace

        rows = self._db.query(DecisionTrace).filter(
            DecisionTrace.user_id == user_id
        ).order_by(DecisionTrace.created_at.desc()).offset(offset).limit(limit).all()

        return [self._to_dict(r) for r in rows]

    def query_by_agent(self, agent_id: str, tenant_id=None, limit: int = 50) -> Dict[str, Any]:
        from core.models import DecisionTrace

        query = self._db.query(DecisionTrace)
        if tenant_id:
            query = query.filter(DecisionTrace.tenant_id == tenant_id)

        traces = query.order_by(DecisionTrace.created_at.desc()).limit(limit * 3).all()

        stats = {
            "agent_id": agent_id,
            "total_decisions": len(traces),
            "triggered_count": 0,
            "selected_as_primary": 0,
            "selected_as_secondary": 0,
            "rejected_count": 0,
            "rejection_reasons": [],
            "avg_score_when_triggered": 0,
            "competing_winners": {},
            "recent_traces": [],
        }

        triggered_scores = []
        for t in traces:
            triggered = t.triggered_agents or []
            agent_entry = next((a for a in triggered if a.get('agent_id') == agent_id), None)

            if agent_entry:
                stats['triggered_count'] += 1
                triggered_scores.append(agent_entry.get('score', 0))

                if t.final_output == agent_id:
                    stats['selected_as_primary'] += 1
                elif agent_id in (t.secondary_agents or []):
                    stats['selected_as_secondary'] += 1
                else:
                    stats['rejected_count'] += 1
                    cr = t.conflict_resolution or {}
                    stats['rejection_reasons'].append({
                        "trace_id": str(t.id),
                        "winner": t.final_output,
                        "strategy": cr.get('strategy', 'unknown'),
                        "reason": cr.get('reason', 'unknown'),
                    })
                    stats['competing_winners'][t.final_output] = \
                        stats['competing_winners'].get(t.final_output, 0) + 1

        if triggered_scores:
            stats['avg_score_when_triggered'] = round(
                sum(triggered_scores) / len(triggered_scores), 4
            )

        stats['recent_traces'] = [
            self._to_dict(t) for t in traces[:5]
            if any(a.get('agent_id') == agent_id for a in (t.triggered_agents or []))
        ][:5]

        return stats

    def get_explainable_trace(self, trace_id: str) -> Optional[dict]:
        from core.models import DecisionTrace

        trace = self._db.query(DecisionTrace).filter(
            DecisionTrace.id == trace_id
        ).first()
        if not trace:
            return None

        explanation = self._generate_explanation(trace)
        result = self._to_dict(trace)
        result['explanation'] = explanation
        return result

    def _generate_explanation(self, trace) -> dict:
        triggered = trace.triggered_agents or []
        policies = trace.policy_applied or []
        cr = trace.conflict_resolution or {}
        lines = []

        if triggered:
            agent_names = [a.get('agent_id') for a in triggered]
            lines.append(f"Triggered {len(triggered)} candidate agents: {', '.join(agent_names)}")

        matched_rules = [p for p in policies if p.get('matched')]
        if matched_rules:
            rule_names = [p.get('rule_name') for p in matched_rules]
            lines.append(f"Matched {len(matched_rules)} rules: {', '.join(rule_names)}")

        if cr:
            strategy = cr.get('strategy', 'unknown')
            reason = cr.get('reason', '')
            lines.append(f"Strategy [{strategy}]: {reason}")

        lines.append(f"Final: {trace.final_output}")
        if trace.secondary_agents:
            lines.append(f"Secondary: {', '.join(trace.secondary_agents)}")

        return {
            "summary": lines[0] if lines else "No explanation available",
            "details": lines,
            "cost_info": f"{trace.token_cost} tokens, {trace.latency_ms}ms",
        }

    @staticmethod
    def _to_dict(trace) -> dict:
        return {
            'id': str(trace.id),
            'event_id': trace.event_id,
            'user_id': trace.user_id,
            'tenant_id': trace.tenant_id,
            'session_id': trace.session_id,
            'triggered_agents': trace.triggered_agents,
            'policy_applied': trace.policy_applied,
            'rule_weights': trace.rule_weights,
            'conflict_resolution': trace.conflict_resolution,
            'final_output': trace.final_output,
            'secondary_agents': trace.secondary_agents,
            'llm_model': trace.llm_model,
            'token_cost': trace.token_cost,
            'latency_ms': trace.latency_ms,
            'created_at': trace.created_at.isoformat() if trace.created_at else None,
        }
