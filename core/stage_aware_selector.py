"""
V007 Step 11 / Phase B
StageAwareSelector: 阶段驱动Agent选择
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class AgentSelection:
    agent_id: str
    score: float
    stage_effectiveness: float
    intensity: int
    should_escalate: bool = False
    escalation_target: Optional[str] = None
    protocol_name: Optional[str] = None
    evidence_tier: Optional[str] = None
    reason: str = ''


class StageAwareSelector:
    """阶段驱动Agent选择器"""

    def __init__(self, db_session: Session):
        self._db = db_session

    def select(self, user_stage: str, risk_level: str,
               domain_keywords: List[str],
               user_context: Dict[str, Any] = None) -> List[AgentSelection]:
        user_context = user_context or {}

        stage_agents = self._get_stage_agents(user_stage)
        logger.info(f"StageSelector Step1: {len(stage_agents)} agents for stage {user_stage}")

        if not stage_agents:
            return []

        filtered = self._exclude_contraindicated(stage_agents, user_context)
        logger.info(f"StageSelector Step2: {len(filtered)} after contraindication check")

        self._adjust_for_risk(filtered, risk_level)
        self._bind_protocols(filtered, user_stage, risk_level)
        self._bind_evidence(filtered)

        filtered.sort(key=lambda a: a.score, reverse=True)
        return filtered

    def _get_stage_agents(self, user_stage: str) -> List[AgentSelection]:
        try:
            from core.models import StageApplicability
            rows = self._db.query(StageApplicability).filter(
                StageApplicability.stage_code == user_stage,
            ).order_by(StageApplicability.effectiveness_score.desc()).all()
        except Exception:
            return self._fallback_stage_agents(user_stage)

        results = []
        for row in rows:
            results.append(AgentSelection(
                agent_id=row.agent_id, score=row.effectiveness_score,
                stage_effectiveness=row.effectiveness_score,
                intensity=row.recommended_intensity,
                reason=f"Primary for {user_stage}" if row.is_primary else f"Applicable for {user_stage}",
            ))

        return results if results else self._fallback_stage_agents(user_stage)

    def _exclude_contraindicated(self, agents, user_context):
        if not user_context:
            return agents
        try:
            from core.models import Contraindication
        except ImportError:
            return agents

        filtered = []
        for agent in agents:
            contras = self._db.query(Contraindication).filter(
                Contraindication.agent_id == agent.agent_id
            ).all() if self._db else []

            is_contraindicated = False
            for c in contras:
                if self._matches_contraindication(c, user_context):
                    if c.severity == 'block':
                        is_contraindicated = True
                        logger.warning(f"Agent {agent.agent_id} blocked: "
                                       f"contraindication {c.condition_type}={c.condition_value}")
                        if c.alternative_agent_id:
                            filtered.append(AgentSelection(
                                agent_id=c.alternative_agent_id,
                                score=agent.score * 0.8,
                                stage_effectiveness=agent.stage_effectiveness * 0.8,
                                intensity=agent.intensity,
                                reason=f"Alternative for contraindicated {agent.agent_id}",
                            ))
                        break
                    elif c.severity == 'warning':
                        agent.score *= 0.7
                        agent.reason += f" (warning: {c.reason})"

            if not is_contraindicated:
                filtered.append(agent)

        return filtered

    def _adjust_for_risk(self, agents, risk_level):
        try:
            from core.models import RiskBoundary
        except ImportError:
            return

        risk_order = {'low': 0, 'normal': 1, 'high': 2, 'critical': 3}
        current_risk = risk_order.get(risk_level, 1)

        for agent in agents:
            boundaries = self._db.query(RiskBoundary).filter(
                RiskBoundary.agent_id == agent.agent_id,
                RiskBoundary.is_enabled == True,
            ).all() if self._db else []

            for rb in boundaries:
                max_risk = risk_order.get(rb.max_risk_level, 1)
                if current_risk > max_risk:
                    agent.should_escalate = True
                    agent.escalation_target = rb.escalation_target
                    agent.score *= 0.3
                    agent.reason += f" -> ESCALATE to {rb.escalation_target}"

    def _bind_protocols(self, agents, user_stage, risk_level):
        try:
            from core.models import InterventionProtocol
        except ImportError:
            return

        for agent in agents:
            protocols = self._db.query(InterventionProtocol).filter(
                InterventionProtocol.agent_id == agent.agent_id,
                InterventionProtocol.is_enabled == True,
            ).all() if self._db else []

            for p in protocols:
                agent.protocol_name = p.protocol_name
                if p.intensity_range:
                    parts = p.intensity_range.split('-')
                    if len(parts) == 2:
                        min_i, max_i = int(parts[0]), int(parts[1])
                        agent.intensity = max(min_i, min(agent.intensity, max_i))
                break

    def _bind_evidence(self, agents):
        try:
            from core.models import EvidenceTierBinding
        except ImportError:
            return

        for agent in agents:
            binding = self._db.query(EvidenceTierBinding).filter(
                EvidenceTierBinding.agent_id == agent.agent_id
            ).first() if self._db else None

            if binding:
                agent.evidence_tier = binding.evidence_tier
                tier_bonus = {'T1': 0.1, 'T2': 0.05, 'T3': 0, 'T4': -0.05, 'T5': -0.1}
                agent.score += tier_bonus.get(binding.evidence_tier, 0)

    def _matches_contraindication(self, contra, user_context):
        ctype = contra.condition_type
        cval = contra.condition_value
        if ctype == 'medical' and cval in user_context.get('medical_conditions', []):
            return True
        if ctype == 'psychological' and cval in user_context.get('psych_conditions', []):
            return True
        if ctype == 'stage' and cval == user_context.get('current_stage'):
            return True
        if ctype == 'behavioral' and cval in user_context.get('behavioral_flags', []):
            return True
        return False

    def _fallback_stage_agents(self, user_stage: str) -> List[AgentSelection]:
        stage_map = {
            'S0': [('motivation', 0.9), ('education', 0.7), ('emotion', 0.8)],
            'S1': [('education', 0.9), ('motivation', 0.8), ('emotion', 0.7)],
            'S2': [('nutrition', 0.7), ('exercise', 0.6), ('education', 0.6)],
            'S3': [('exercise', 0.9), ('nutrition', 0.9), ('glucose', 0.8)],
            'S4': [('glucose', 0.9), ('exercise', 0.8), ('nutrition', 0.8)],
            'S5': [('glucose', 0.7), ('exercise', 0.7), ('behavior_rx', 0.9)],
        }
        agents = stage_map.get(user_stage, [('behavior_rx', 0.5)])
        return [
            AgentSelection(agent_id=aid, score=score, stage_effectiveness=score,
                           intensity=3, reason=f"Fallback for {user_stage}")
            for aid, score in agents
        ]
