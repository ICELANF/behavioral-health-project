"""
V007 Step 07 / Phase A
Policy Engine: 统一策略决策引擎 (核心中枢)
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class Event:
    id: str = ''
    type: str = 'user_message'
    content: str = ''
    domain_keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]


@dataclass
class UserContext:
    user_id: int = 0
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    current_stage: str = 'S0'
    risk_level: str = 'normal'
    domain: str = ''
    preferred_model: str = 'deepseek-chat'
    daily_token_usage_ratio: float = 0.0
    user_tags: List[str] = field(default_factory=list)
    behavioral_profile: Dict[str, Any] = field(default_factory=dict)

    def to_eval_context(self) -> dict:
        return {
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'stage': self.current_stage,
            'risk_level': self.risk_level,
            'domain': self.domain,
            'daily_token_usage_ratio': self.daily_token_usage_ratio,
            'user_tags': self.user_tags,
            **self.behavioral_profile,
        }


@dataclass
class ExecutionPlan:
    primary_agent: str
    secondary_agents: List[str]
    model: str
    intensity: int = 3
    trace_id: str = ''
    budget_status: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_downgraded(self) -> bool:
        return self.budget_status.get('downgraded', False)


class PolicyEngine:
    """
    V007 策略决策引擎

    5-step pipeline:
    1. Collect applicable rules (RuleRegistry)
    2. Build agent candidates (ApplicabilityMatrix)
    3. Conflict arbitration (ConflictResolver)
    4. Cost control (CostController)
    5. Record DecisionTrace
    """

    def __init__(self, db_session: Session, rule_registry=None,
                 conflict_resolver=None, trace_recorder=None, cost_controller=None):
        self._db = db_session

        from core.rule_registry import RuleRegistry
        from core.conflict_resolver import ConflictResolver
        from core.decision_trace import DecisionTraceRecorder
        from core.cost_controller import CostController

        self.rule_registry = rule_registry or RuleRegistry(
            db_session_factory=lambda: db_session
        )
        self.conflict_resolver = conflict_resolver or ConflictResolver(
            db_session=db_session
        )
        self.trace_recorder = trace_recorder or DecisionTraceRecorder(
            db_session=db_session
        )
        self.cost_controller = cost_controller or CostController(
            db_session=db_session
        )

    def evaluate(self, event: Event, context: UserContext) -> ExecutionPlan:
        start_time = time.time()
        from core.conflict_resolver import AgentCandidate, ArbitrationContext

        # Step 1: Collect rules
        eval_context = context.to_eval_context()
        rules = self.rule_registry.get_applicable_rules(
            tenant_id=context.tenant_id, context=eval_context
        )
        logger.info(f"PolicyEngine Step1: {len(rules)} rules matched")

        for rule in rules:
            if rule['action_type'] == 'block':
                logger.warning(f"BLOCKED by rule: {rule['rule_name']}")
                return self._make_blocked_plan(rule, event, context)

        # Step 2: Build candidates
        candidates = self._build_candidates(event, context, rules)
        logger.info(f"PolicyEngine Step2: {len(candidates)} agent candidates")

        if not candidates:
            return self._make_fallback_plan(event, context)

        # Step 3: Conflict resolution
        arb_context = ArbitrationContext(
            user_stage=context.current_stage,
            risk_level=context.risk_level,
            tenant_id=context.tenant_id,
            domain_keywords=event.domain_keywords,
        )
        resolution = self.conflict_resolver.resolve(candidates, rules, arb_context)
        logger.info(f"PolicyEngine Step3: strategy={resolution.strategy_used}, "
                     f"winner={resolution.primary_agent.agent_id}")

        # Step 4: Cost control
        budget_result = self.cost_controller.check_budget(
            tenant_id=context.tenant_id or '',
            user_id=context.user_id,
            requested_model=context.preferred_model,
        )

        if not budget_result['allowed']:
            budget_result['model'] = 'ollama-local'
            budget_result['allowed'] = True

        # Step 5: Record trace
        latency_ms = int((time.time() - start_time) * 1000)

        trace_id = self.trace_recorder.record(
            event_id=event.id,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            session_id=context.session_id,
            triggered_agents=[
                {"agent_id": c.agent_id, "score": c.score,
                 "reason": c.metadata.get('match_reason', '')}
                for c in candidates
            ],
            policy_applied=[
                {"rule_id": r['id'], "rule_name": r['rule_name'], "matched": True}
                for r in rules
            ],
            rule_weights=resolution.weights,
            conflict_resolution=resolution.detail,
            final_output=resolution.primary_agent.agent_id,
            secondary_agents=[a.agent_id for a in resolution.secondary_agents],
            llm_model=budget_result['model'],
            latency_ms=latency_ms,
        )

        plan = ExecutionPlan(
            primary_agent=resolution.primary_agent.agent_id,
            secondary_agents=[a.agent_id for a in resolution.secondary_agents],
            model=budget_result['model'],
            trace_id=trace_id,
            budget_status=budget_result,
            metadata={
                "strategy_used": resolution.strategy_used,
                "candidates_count": len(candidates),
                "rules_matched": len(rules),
                "latency_ms": latency_ms,
            }
        )

        logger.info(f"PolicyEngine complete: primary={plan.primary_agent}, "
                     f"model={plan.model}, trace={trace_id[:8]}...")
        return plan

    def _build_candidates(self, event, context, rules):
        from core.conflict_resolver import AgentCandidate

        try:
            from core.models import AgentApplicabilityMatrix
            matrices = self._db.query(AgentApplicabilityMatrix).filter(
                AgentApplicabilityMatrix.is_enabled == True
            ).all()
        except Exception:
            matrices = []

        candidates = []
        for m in matrices:
            if not m.is_applicable(context.current_stage, context.risk_level):
                continue

            if m.contraindications:
                skip = False
                for contra in m.contraindications:
                    if self._check_contraindication(contra, context):
                        skip = True
                        break
                if skip:
                    continue

            score = self._calc_score(m, event, rules, context)
            candidate = AgentCandidate(
                agent_id=m.agent_id, score=score,
                domain=event.domain_keywords[0] if event.domain_keywords else '',
                risk_level=context.risk_level,
                is_medical=self._is_medical_agent(m.agent_id),
                stage_effectiveness=self._get_stage_effectiveness(m.agent_id, context.current_stage),
                metadata={'intensity_level': m.intensity_level, 'stage_range': m.stage_range,
                          'match_reason': f"Matrix match: stage={m.stage_range}, risk={m.risk_level}"},
            )
            candidates.append(candidate)

        for rule in rules:
            if rule['action_type'] == 'select_agent':
                params = rule['action_params']
                agent_id = params.get('agent_id')
                if agent_id and not any(c.agent_id == agent_id for c in candidates):
                    candidates.append(AgentCandidate(
                        agent_id=agent_id, score=rule['priority'] / 100.0,
                        is_medical=self._is_medical_agent(agent_id),
                        metadata={'match_reason': f"Rule forced: {rule['rule_name']}"},
                    ))

        return candidates

    def _calc_score(self, matrix, event, rules, context) -> float:
        base = 0.5
        for rule in rules:
            prefer = rule.get('action_params', {}).get('prefer_agents', [])
            if matrix.agent_id in prefer:
                base += 0.2
        base += self._get_stage_effectiveness(matrix.agent_id, context.current_stage) * 0.3
        if matrix.intensity_level:
            base += (1 - abs(matrix.intensity_level - 3) / 5) * 0.1
        return round(min(base, 1.0), 4)

    MEDICAL_AGENTS = {'glucose', 'blood_pressure', 'medication', 'crisis',
                       'nutrition_medical', 'exercise_medical'}

    def _is_medical_agent(self, agent_id: str) -> bool:
        return agent_id in self.MEDICAL_AGENTS

    def _get_stage_effectiveness(self, agent_id: str, stage: str) -> float:
        stage_map = {
            'motivation':  {'S0': 0.9, 'S1': 0.8, 'S2': 0.5, 'S3': 0.3},
            'education':   {'S0': 0.7, 'S1': 0.9, 'S2': 0.6, 'S3': 0.4},
            'glucose':     {'S2': 0.5, 'S3': 0.8, 'S4': 0.9, 'S5': 0.7},
            'exercise':    {'S2': 0.6, 'S3': 0.9, 'S4': 0.8, 'S5': 0.7},
            'nutrition':   {'S1': 0.5, 'S2': 0.7, 'S3': 0.9, 'S4': 0.8},
            'emotion':     {'S0': 0.8, 'S1': 0.7, 'S2': 0.6, 'S3': 0.5},
            'crisis':      {'S0': 1.0, 'S1': 1.0, 'S2': 1.0, 'S3': 1.0,
                            'S4': 1.0, 'S5': 1.0, 'S6': 1.0},
        }
        return stage_map.get(agent_id, {}).get(stage, 0.3)

    def _check_contraindication(self, contra: dict, context: UserContext) -> bool:
        ctype = contra.get('type')
        cvalue = contra.get('value')
        if ctype == 'stage' and context.current_stage == cvalue:
            return True
        if ctype == 'risk_level' and context.risk_level == cvalue:
            return True
        if ctype == 'tag' and cvalue in context.user_tags:
            return True
        return False

    def _make_blocked_plan(self, rule, event, context) -> ExecutionPlan:
        trace_id = self.trace_recorder.record(
            event_id=event.id, user_id=context.user_id,
            tenant_id=context.tenant_id, session_id=context.session_id,
            triggered_agents=[], policy_applied=[{
                "rule_id": rule['id'], "rule_name": rule['rule_name'], "matched": True}],
            rule_weights={},
            conflict_resolution={"strategy": "blocked", "reason": rule['rule_name']},
            final_output="BLOCKED",
        )
        return ExecutionPlan(
            primary_agent="BLOCKED", secondary_agents=[], model='none',
            trace_id=trace_id, metadata={"blocked_by": rule['rule_name']},
        )

    def _make_fallback_plan(self, event, context) -> ExecutionPlan:
        default_agent = 'behavior_rx'
        logger.warning(f"No candidates, falling back to {default_agent}")
        return ExecutionPlan(
            primary_agent=default_agent, secondary_agents=[],
            model=context.preferred_model, metadata={"fallback": True},
        )
