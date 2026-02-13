"""
V007 Step 04 / Phase A
Conflict Resolver: 冲突仲裁引擎 (5 strategies)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class AgentCandidate:
    agent_id: str
    score: float
    domain: str = ''
    risk_level: str = 'normal'
    is_medical: bool = False
    stage_effectiveness: float = 0
    history_score: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConflictResolution:
    primary_agent: AgentCandidate
    secondary_agents: List[AgentCandidate]
    strategy_used: str
    weights: Dict[str, float]
    detail: Dict[str, Any]
    losers: List[AgentCandidate] = field(default_factory=list)


@dataclass
class ArbitrationContext:
    user_stage: str = 'S0'
    risk_level: str = 'normal'
    tenant_id: Optional[str] = None
    domain_keywords: List[str] = field(default_factory=list)
    user_history: Dict[str, Any] = field(default_factory=dict)


class ArbitrationStrategy(ABC):
    @abstractmethod
    def resolve(self, candidates, rules, context) -> ConflictResolution:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class WeightedScoreStrategy(ArbitrationStrategy):
    @property
    def name(self) -> str:
        return 'weighted_score'

    def resolve(self, candidates, rules, context):
        W_SCORE = 0.4
        W_STAGE = 0.35
        W_HISTORY = 0.25

        weighted = {}
        for c in candidates:
            final = c.score * W_SCORE + c.stage_effectiveness * W_STAGE + c.history_score * W_HISTORY
            weighted[c.agent_id] = round(final, 4)

        sorted_candidates = sorted(candidates, key=lambda c: weighted[c.agent_id], reverse=True)
        winner = sorted_candidates[0]
        threshold = weighted[winner.agent_id] * 0.9
        secondary = [c for c in sorted_candidates[1:] if weighted[c.agent_id] >= threshold]
        losers = [c for c in sorted_candidates[1:] if weighted[c.agent_id] < threshold]

        return ConflictResolution(
            primary_agent=winner, secondary_agents=secondary,
            strategy_used=self.name, weights=weighted,
            detail={"method": "weighted_sum",
                    "winner_reason": f"{winner.agent_id} scored {weighted[winner.agent_id]:.4f}"},
            losers=losers,
        )


class PriorityTreeStrategy(ArbitrationStrategy):
    @property
    def name(self) -> str:
        return 'priority_tree'

    def resolve(self, candidates, rules, context):
        agent_priority = {}
        for rule in rules:
            if rule.get('action_type') == 'select_agent':
                params = rule.get('action_params', {})
                if 'agent_id' in params:
                    agent_priority[params['agent_id']] = rule.get('priority', 50)

        sorted_c = sorted(candidates, key=lambda c: agent_priority.get(c.agent_id, 50), reverse=True)
        winner = sorted_c[0]
        weights = {c.agent_id: agent_priority.get(c.agent_id, 50) for c in candidates}

        return ConflictResolution(
            primary_agent=winner, secondary_agents=sorted_c[1:3],
            strategy_used=self.name, weights=weights,
            detail={"method": "priority_tree",
                    "winner_reason": f"{winner.agent_id} has priority {weights[winner.agent_id]}"},
            losers=sorted_c[3:],
        )


class MedicalBoundaryStrategy(ArbitrationStrategy):
    @property
    def name(self) -> str:
        return 'medical_boundary'

    def resolve(self, candidates, rules, context):
        medical = [c for c in candidates if c.is_medical]
        non_medical = [c for c in candidates if not c.is_medical]

        if not medical:
            return WeightedScoreStrategy().resolve(candidates, rules, context)

        medical.sort(key=lambda c: c.score, reverse=True)
        winner = medical[0]
        weights = {c.agent_id: (100.0 if c.is_medical else 0.0) for c in candidates}

        return ConflictResolution(
            primary_agent=winner, secondary_agents=medical[1:],
            strategy_used=self.name, weights=weights,
            detail={"method": "medical_boundary_suppress",
                    "suppressed_agents": [c.agent_id for c in non_medical],
                    "winner_reason": f"Medical boundary: {winner.agent_id} takes priority"},
            losers=non_medical,
        )


class TenantOverrideStrategy(ArbitrationStrategy):
    @property
    def name(self) -> str:
        return 'tenant_override'

    def resolve(self, candidates, rules, context):
        tenant_rules = [r for r in rules if r.get('tenant_id') == context.tenant_id]

        if not tenant_rules:
            return WeightedScoreStrategy().resolve(candidates, rules, context)

        forced_agents = []
        for rule in tenant_rules:
            params = rule.get('action_params', {})
            if params.get('force') and 'agent_id' in params:
                forced_agents.append(params['agent_id'])

        if forced_agents:
            forced_candidates = [c for c in candidates if c.agent_id in forced_agents]
            if forced_candidates:
                winner = forced_candidates[0]
                others = [c for c in candidates if c.agent_id != winner.agent_id]
                weights = {c.agent_id: (100.0 if c.agent_id in forced_agents else 10.0)
                           for c in candidates}
                return ConflictResolution(
                    primary_agent=winner, secondary_agents=forced_candidates[1:],
                    strategy_used=self.name, weights=weights,
                    detail={"method": "tenant_override", "tenant_id": context.tenant_id,
                            "winner_reason": f"Tenant override: {winner.agent_id}"},
                    losers=[c for c in others if c not in forced_candidates],
                )

        return WeightedScoreStrategy().resolve(candidates, rules, context)


class RiskSuppressionStrategy(ArbitrationStrategy):
    CRISIS_AGENT_ID = 'crisis'

    @property
    def name(self) -> str:
        return 'risk_suppress'

    def resolve(self, candidates, rules, context):
        crisis = next((c for c in candidates if c.agent_id == self.CRISIS_AGENT_ID), None)

        if not crisis:
            crisis = AgentCandidate(
                agent_id=self.CRISIS_AGENT_ID, score=100.0,
                domain='crisis', is_medical=True,
            )

        others = [c for c in candidates if c.agent_id != self.CRISIS_AGENT_ID]
        weights = {self.CRISIS_AGENT_ID: 100.0}
        weights.update({c.agent_id: 0.0 for c in others})

        return ConflictResolution(
            primary_agent=crisis, secondary_agents=[],
            strategy_used=self.name, weights=weights,
            detail={"method": "risk_absolute_suppress", "risk_level": context.risk_level,
                    "winner_reason": "CRITICAL risk: CrisisAgent absolute priority"},
            losers=others,
        )


class ConflictResolver:
    """冲突仲裁引擎 — 统一入口"""

    STRATEGIES = {
        'weighted_score': WeightedScoreStrategy,
        'priority_tree': PriorityTreeStrategy,
        'medical_boundary': MedicalBoundaryStrategy,
        'tenant_override': TenantOverrideStrategy,
        'risk_suppress': RiskSuppressionStrategy,
    }

    def __init__(self, db_session=None):
        self._db = db_session
        self._strategy_instances = {name: cls() for name, cls in self.STRATEGIES.items()}

    def resolve(self, candidates, rules, context, force_strategy=None) -> ConflictResolution:
        if not candidates:
            raise ValueError("No candidates to resolve")

        if len(candidates) == 1:
            c = candidates[0]
            return ConflictResolution(
                primary_agent=c, secondary_agents=[],
                strategy_used='single_candidate',
                weights={c.agent_id: c.score},
                detail={"method": "single_candidate", "winner_reason": "Only one candidate"},
            )

        if force_strategy and force_strategy in self._strategy_instances:
            strategy = self._strategy_instances[force_strategy]
        else:
            strategy = self._select_strategy(candidates, rules, context)

        logger.info(f"ConflictResolver using strategy: {strategy.name} for {len(candidates)} candidates")
        return strategy.resolve(candidates, rules, context)

    def _select_strategy(self, candidates, rules, context):
        if context.risk_level == 'critical':
            return self._strategy_instances['risk_suppress']

        has_medical = any(c.is_medical for c in candidates)
        if has_medical and context.risk_level in ('high', 'critical'):
            return self._strategy_instances['medical_boundary']

        tenant_rules = [r for r in rules if r.get('tenant_id') == context.tenant_id]
        if tenant_rules and context.tenant_id:
            return self._strategy_instances['tenant_override']

        if self._db:
            strategy_name = self._lookup_conflict_matrix(candidates)
            if strategy_name and strategy_name in self._strategy_instances:
                return self._strategy_instances[strategy_name]

        return self._strategy_instances['weighted_score']

    def _lookup_conflict_matrix(self, candidates):
        if not self._db or len(candidates) < 2:
            return None
        try:
            from core.models import ConflictMatrix
            agent_ids = [c.agent_id for c in candidates]
            row = self._db.query(ConflictMatrix).filter(
                ConflictMatrix.agent_a_id.in_(agent_ids),
                ConflictMatrix.agent_b_id.in_(agent_ids),
                ConflictMatrix.is_enabled == True
            ).first()
            if row:
                return row.resolution_strategy
        except Exception as e:
            logger.warning(f"ConflictMatrix lookup failed: {e}")
        return None
