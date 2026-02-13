"""
V007 Step 03 / Phase A
Rule Registry: 规则注册中心
"""

import logging
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ─── JSON-Logic 求值器 ────────────────────────────────

class JsonLogicEvaluator:
    """
    简化版 JSON-Logic 求值器
    支持: ==, !=, >, <, >=, <=, in, and, or, not, var
    """

    @staticmethod
    def evaluate(logic: dict, data: dict) -> bool:
        if not isinstance(logic, dict):
            return bool(logic)

        op = list(logic.keys())[0]
        values = logic[op]

        if op == 'var':
            keys = values.split('.') if isinstance(values, str) else [values]
            result = data
            for k in keys:
                if isinstance(result, dict):
                    result = result.get(k)
                else:
                    return None
            return result

        if op == 'and':
            return all(JsonLogicEvaluator.evaluate(v, data) for v in values)

        if op == 'or':
            return any(JsonLogicEvaluator.evaluate(v, data) for v in values)

        if op in ('not', '!'):
            val = values if not isinstance(values, list) else values[0]
            return not JsonLogicEvaluator.evaluate(val, data)

        if isinstance(values, list) and len(values) == 2:
            a = JsonLogicEvaluator.evaluate(values[0], data) \
                if isinstance(values[0], dict) else values[0]
            b = JsonLogicEvaluator.evaluate(values[1], data) \
                if isinstance(values[1], dict) else values[1]

            ops = {
                '==': lambda x, y: x == y,
                '!=': lambda x, y: x != y,
                '>':  lambda x, y: x > y,
                '<':  lambda x, y: x < y,
                '>=': lambda x, y: x >= y,
                '<=': lambda x, y: x <= y,
                'in': lambda x, y: x in y if y else False,
            }
            if op in ops:
                try:
                    return ops[op](a, b)
                except (TypeError, ValueError):
                    return False

        logger.warning(f"Unsupported JSON-Logic operator: {op}")
        return False


# ─── 规则缓存 ──────────────────────────────────────────

class RuleCache:
    """线程安全的规则内存缓存"""

    def __init__(self):
        self._rules: Dict[int, dict] = {}
        self._lock = threading.RLock()
        self._last_refresh: Optional[datetime] = None

    def load(self, rules: List[dict]):
        with self._lock:
            self._rules = {r['id']: r for r in rules}
            self._last_refresh = datetime.utcnow()
            logger.info(f"RuleCache loaded {len(self._rules)} rules")

    def get_all(self) -> List[dict]:
        with self._lock:
            return list(self._rules.values())

    def get_by_type(self, rule_type: str) -> List[dict]:
        with self._lock:
            return [r for r in self._rules.values()
                    if r['rule_type'] == rule_type and r['is_enabled']]

    def invalidate(self, rule_id: int):
        with self._lock:
            self._rules.pop(rule_id, None)

    def upsert(self, rule: dict):
        with self._lock:
            self._rules[rule['id']] = rule


# ─── 规则注册中心 ──────────────────────────────────────

class RuleRegistry:
    """策略规则注册中心"""

    def __init__(self, db_session_factory):
        self._db_factory = db_session_factory
        self._cache = RuleCache()
        self._evaluator = JsonLogicEvaluator()

    def initialize(self):
        """启动时加载所有规则到内存"""
        db = self._db_factory()
        try:
            from core.models import PolicyRule
            rows = db.query(PolicyRule).filter(
                PolicyRule.is_enabled == True
            ).order_by(PolicyRule.priority.desc()).all()

            rules = [self._to_dict(r) for r in rows]
            self._cache.load(rules)
        except Exception as e:
            logger.warning(f"RuleRegistry.initialize failed (table may not exist): {e}")
            self._cache.load([])
        finally:
            try:
                db.close()
            except Exception:
                pass

    def refresh(self):
        """热刷新"""
        logger.info("RuleRegistry: hot refresh triggered")
        self.initialize()

    def get_applicable_rules(
        self,
        tenant_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[dict]:
        all_rules = self._cache.get_all()
        matched = []

        for rule in all_rules:
            if not rule['is_enabled']:
                continue
            if rule['tenant_id'] is not None and rule['tenant_id'] != tenant_id:
                continue
            try:
                if self._evaluator.evaluate(rule['condition_expr'], context):
                    matched.append(rule)
            except Exception as e:
                logger.error(f"Rule {rule['rule_name']} evaluation error: {e}")
                continue

        matched.sort(key=lambda r: (
            r['priority'],
            1 if r['tenant_id'] else 0
        ), reverse=True)

        return matched

    # ─── CRUD ───────────────────────────────

    def create_rule(self, db: Session, data: dict) -> dict:
        from core.models import PolicyRule

        rule = PolicyRule(
            rule_name=data['rule_name'],
            rule_type=data['rule_type'],
            condition_expr=data['condition_expr'],
            action_type=data['action_type'],
            action_params=data['action_params'],
            priority=data.get('priority', 50),
            tenant_id=data.get('tenant_id'),
            evidence_tier=data.get('evidence_tier'),
            description=data.get('description'),
            created_by=data.get('created_by'),
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)

        rule_dict = self._to_dict(rule)
        self._cache.upsert(rule_dict)
        logger.info(f"Rule created: {rule.rule_name} (id={rule.id})")
        return rule_dict

    def update_rule(self, db: Session, rule_id: int, data: dict) -> Optional[dict]:
        from core.models import PolicyRule

        rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()
        if not rule:
            return None

        for key in ['rule_name', 'rule_type', 'condition_expr', 'action_type',
                     'action_params', 'priority', 'is_enabled', 'evidence_tier',
                     'description']:
            if key in data:
                setattr(rule, key, data[key])

        db.commit()
        db.refresh(rule)

        rule_dict = self._to_dict(rule)
        self._cache.upsert(rule_dict)
        logger.info(f"Rule updated: {rule.rule_name} (id={rule.id})")
        return rule_dict

    def delete_rule(self, db: Session, rule_id: int) -> bool:
        from core.models import PolicyRule

        rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()
        if not rule:
            return False

        db.delete(rule)
        db.commit()
        self._cache.invalidate(rule_id)
        logger.info(f"Rule deleted: id={rule_id}")
        return True

    def test_rule(self, rule_id: int, test_context: dict) -> dict:
        all_rules = self._cache.get_all()
        rule = next((r for r in all_rules if r['id'] == rule_id), None)
        if not rule:
            return {"matched": False, "error": "Rule not found"}

        try:
            matched = self._evaluator.evaluate(rule['condition_expr'], test_context)
            return {"matched": matched, "rule": rule, "context": test_context}
        except Exception as e:
            return {"matched": False, "error": str(e)}

    @staticmethod
    def _to_dict(rule) -> dict:
        return {
            'id': rule.id,
            'rule_name': rule.rule_name,
            'rule_type': rule.rule_type,
            'condition_expr': rule.condition_expr,
            'action_type': rule.action_type,
            'action_params': rule.action_params,
            'priority': rule.priority,
            'tenant_id': rule.tenant_id,
            'is_enabled': rule.is_enabled,
            'evidence_tier': rule.evidence_tier,
            'description': rule.description,
        }


# ─── 默认种子规则 ──────────────────────────────────────

DEFAULT_SEED_RULES = [
    {
        "rule_name": "crisis_absolute_priority",
        "rule_type": "safety",
        "condition_expr": {"==": [{"var": "risk_level"}, "critical"]},
        "action_type": "select_agent",
        "action_params": {"agent_id": "crisis", "force": True},
        "priority": 100,
        "description": "CrisisAgent absolute priority in critical state",
    },
    {
        "rule_name": "medical_boundary_suppress",
        "rule_type": "safety",
        "condition_expr": {
            "and": [
                {"==": [{"var": "risk_level"}, "high"]},
                {"in": [{"var": "domain"}, ["glucose", "blood_pressure", "medication"]]}
            ]
        },
        "action_type": "escalate",
        "action_params": {"escalate_to": "medical_review", "block_non_medical": True},
        "priority": 95,
        "description": "Suppress non-medical agents in high-risk medical scenarios",
    },
    {
        "rule_name": "early_stage_gentle_intensity",
        "rule_type": "stage",
        "condition_expr": {
            "or": [
                {"==": [{"var": "stage"}, "S0"]},
                {"==": [{"var": "stage"}, "S1"]}
            ]
        },
        "action_type": "select_agent",
        "action_params": {"max_intensity": 2, "prefer_agents": ["motivation", "education"]},
        "priority": 60,
        "description": "Limit intensity for pre-contemplation/contemplation stages",
    },
    {
        "rule_name": "cost_daily_limit_default",
        "rule_type": "cost",
        "condition_expr": {">=": [{"var": "daily_token_usage_ratio"}, 0.9]},
        "action_type": "cost_limit",
        "action_params": {"downgrade_model": "qwen-turbo", "max_tokens_per_call": 500},
        "priority": 70,
        "description": "Downgrade model when daily budget exceeds 90%",
    },
]
