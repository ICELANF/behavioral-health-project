"""
V007 Step 12 / Phase B
Auto-Exit Handler: 自动退出与转交机制
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class ExitDecision:
    should_exit: bool
    reason: str
    escalation_target: Optional[str] = None
    alert_message: Optional[str] = None
    severity: str = 'normal'
    original_agent_id: str = ''


class AutoExitHandler:
    """自动退出处理器"""

    def __init__(self, db_session: Session):
        self._db = db_session
        self._boundaries_cache: Dict[str, List[dict]] = {}

    def check_exit(self, agent_id: str, user_input: str,
                   user_context: Dict[str, Any],
                   device_data: Optional[Dict[str, Any]] = None) -> ExitDecision:
        boundaries = self._get_boundaries(agent_id)

        if not boundaries:
            return ExitDecision(should_exit=False, reason='no_boundary_configured')

        for boundary in boundaries:
            exit_checks = [
                self._check_keyword_trigger(boundary, user_input),
                self._check_data_trigger(boundary, device_data),
                self._check_risk_level(boundary, user_context),
                self._check_behavioral_trigger(boundary, user_context),
            ]

            for decision in exit_checks:
                if decision.should_exit:
                    decision.original_agent_id = agent_id
                    logger.warning(
                        f"AUTO-EXIT: Agent [{agent_id}] -> [{decision.escalation_target}] "
                        f"reason: {decision.reason}"
                    )
                    return decision

        return ExitDecision(should_exit=False, reason='all_checks_passed')

    def execute_exit(self, decision: ExitDecision,
                     session_context: Dict[str, Any]) -> Dict[str, Any]:
        if not decision.should_exit:
            return {"transferred_to": None}

        handoff = {
            "transferred_to": decision.escalation_target,
            "transferred_from": decision.original_agent_id,
            "reason": decision.reason,
            "severity": decision.severity,
            "handoff_message": self._build_handoff_message(decision),
            "original_context": session_context,
            "alert_sent": False,
        }

        if decision.severity == 'critical':
            self._send_alert(decision, session_context)
            handoff["alert_sent"] = True

        return handoff

    def _check_keyword_trigger(self, boundary, user_input):
        exit_cond = boundary.get('auto_exit_condition', {})
        keywords = exit_cond.get('keywords', [])

        if not keywords or not user_input:
            return ExitDecision(should_exit=False, reason='')

        input_lower = user_input.lower()
        for kw in keywords:
            if kw.lower() in input_lower:
                return ExitDecision(
                    should_exit=True,
                    reason=f"Keyword trigger: '{kw}' detected",
                    escalation_target=boundary.get('escalation_target'),
                    alert_message=boundary.get('alert_message'),
                    severity='critical' if boundary.get('risk_type') == 'medical_emergency' else 'warning',
                )

        return ExitDecision(should_exit=False, reason='')

    def _check_data_trigger(self, boundary, device_data):
        if not device_data:
            return ExitDecision(should_exit=False, reason='')

        exit_cond = boundary.get('auto_exit_condition', {})

        glucose = device_data.get('blood_glucose')
        if glucose is not None:
            low = exit_cond.get('blood_glucose_below')
            high = exit_cond.get('blood_glucose_above')
            if low and glucose < low:
                return ExitDecision(
                    should_exit=True,
                    reason=f"Blood glucose {glucose} < {low} (hypoglycemia)",
                    escalation_target=boundary.get('escalation_target'),
                    severity='critical',
                )
            if high and glucose > high:
                return ExitDecision(
                    should_exit=True,
                    reason=f"Blood glucose {glucose} > {high} (severe hyperglycemia)",
                    escalation_target=boundary.get('escalation_target'),
                    severity='critical',
                )

        systolic = device_data.get('blood_pressure_systolic')
        if systolic is not None:
            bp_high = exit_cond.get('systolic_above')
            if bp_high and systolic > bp_high:
                return ExitDecision(
                    should_exit=True,
                    reason=f"Systolic BP {systolic} > {bp_high}",
                    escalation_target=boundary.get('escalation_target'),
                    severity='critical',
                )

        heart_rate = device_data.get('heart_rate')
        if heart_rate is not None:
            hr_high = exit_cond.get('heart_rate_above', 150)
            hr_low = exit_cond.get('heart_rate_below', 40)
            if heart_rate > hr_high or heart_rate < hr_low:
                return ExitDecision(
                    should_exit=True,
                    reason=f"Heart rate {heart_rate} out of safe range",
                    escalation_target=boundary.get('escalation_target'),
                    severity='critical',
                )

        return ExitDecision(should_exit=False, reason='')

    def _check_risk_level(self, boundary, user_context):
        risk_order = {'low': 0, 'normal': 1, 'high': 2, 'critical': 3}
        current_risk = risk_order.get(user_context.get('risk_level', 'normal'), 1)
        max_risk = risk_order.get(boundary.get('max_risk_level', 'high'), 2)

        if current_risk > max_risk:
            return ExitDecision(
                should_exit=True,
                reason=f"Risk level {user_context.get('risk_level')} exceeds max {boundary.get('max_risk_level')}",
                escalation_target=boundary.get('escalation_target'),
                severity='warning' if current_risk == 2 else 'critical',
            )

        return ExitDecision(should_exit=False, reason='')

    def _check_behavioral_trigger(self, boundary, user_context):
        exit_cond = boundary.get('auto_exit_condition', {})
        behavioral_flags = exit_cond.get('behavioral_flags', [])
        user_flags = user_context.get('behavioral_flags', [])

        for flag in behavioral_flags:
            if flag in user_flags:
                return ExitDecision(
                    should_exit=True,
                    reason=f"Behavioral flag detected: {flag}",
                    escalation_target=boundary.get('escalation_target'),
                    severity='warning',
                )

        return ExitDecision(should_exit=False, reason='')

    def _get_boundaries(self, agent_id: str) -> List[dict]:
        if agent_id in self._boundaries_cache:
            return self._boundaries_cache[agent_id]

        try:
            from core.models import RiskBoundary
            rows = self._db.query(RiskBoundary).filter(
                RiskBoundary.agent_id == agent_id,
                RiskBoundary.is_enabled == True,
            ).all()

            boundaries = [{
                'risk_type': r.risk_type,
                'max_risk_level': r.max_risk_level,
                'escalation_target': r.escalation_target,
                'auto_exit_condition': r.auto_exit_condition or {},
                'alert_message': r.alert_message,
            } for r in rows]

            self._boundaries_cache[agent_id] = boundaries
            return boundaries
        except Exception:
            return []

    def _build_handoff_message(self, decision):
        return (
            f"Agent [{decision.original_agent_id}] detected boundary exceeded, "
            f"auto-transferred to [{decision.escalation_target}]. "
            f"Reason: {decision.reason}. Severity: {decision.severity}"
        )

    def _send_alert(self, decision, context):
        logger.critical(
            f"CRITICAL ALERT: Agent {decision.original_agent_id} "
            f"auto-exit to {decision.escalation_target}. "
            f"User: {context.get('user_id')}. Reason: {decision.reason}"
        )
