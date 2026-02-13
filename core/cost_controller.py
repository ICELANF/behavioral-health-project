"""
V007 Step 06 / Phase A
Cost Controller: LLM调用预算管理
"""

import logging
from datetime import date
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MODEL_COST_TABLE = {
    'deepseek-chat':     (0.001, 0.002),
    'deepseek-coder':    (0.001, 0.002),
    'qwen-plus':         (0.004, 0.012),
    'qwen-turbo':        (0.0008, 0.002),
    'qwen-max':          (0.02, 0.06),
    'gpt-4o':            (0.0375, 0.15),
    'gpt-4o-mini':       (0.00225, 0.009),
    'ollama-local':      (0.0, 0.0),
}

DOWNGRADE_PATH = [
    'gpt-4o', 'qwen-max', 'qwen-plus',
    'deepseek-chat', 'qwen-turbo', 'ollama-local',
]


class CostController:
    def __init__(self, db_session: Session):
        self._db = db_session

    def check_budget(self, tenant_id: str, user_id: Optional[int],
                     requested_model: str, estimated_tokens: int = 1000) -> Dict[str, Any]:
        budget = self._get_active_budget(tenant_id, user_id)

        if not budget:
            return {"allowed": True, "model": requested_model, "downgraded": False,
                    "reason": "no_budget_configured", "remaining_tokens": -1, "usage_ratio": 0.0}

        remaining = budget.remaining_tokens
        ratio = budget.usage_ratio

        if ratio < 0.8:
            return {"allowed": True, "model": requested_model, "downgraded": False,
                    "reason": "within_budget", "remaining_tokens": remaining,
                    "usage_ratio": round(ratio, 4)}

        if ratio < 1.0:
            downgraded_model = self._find_cheaper_model(requested_model)
            logger.warning(f"Budget tight ({ratio:.1%}): downgrading {requested_model} -> {downgraded_model}")
            return {"allowed": True, "model": downgraded_model, "downgraded": True,
                    "reason": f"budget_tight_{ratio:.0%}", "remaining_tokens": remaining,
                    "usage_ratio": round(ratio, 4)}

        action = budget.overflow_action or 'downgrade'
        if action == 'block':
            return {"allowed": False, "model": requested_model, "downgraded": False,
                    "reason": "budget_exhausted_blocked", "remaining_tokens": 0,
                    "usage_ratio": round(ratio, 4)}
        if action == 'queue':
            return {"allowed": False, "model": requested_model, "downgraded": False,
                    "reason": "budget_exhausted_queued", "remaining_tokens": 0,
                    "usage_ratio": round(ratio, 4)}

        cheapest = DOWNGRADE_PATH[-1]
        return {"allowed": True, "model": cheapest, "downgraded": True,
                "reason": "budget_exhausted_downgraded", "remaining_tokens": 0,
                "usage_ratio": round(ratio, 4)}

    def record_usage(self, tenant_id: str, user_id: Optional[int],
                     model: str, input_tokens: int, output_tokens: int) -> Dict[str, Any]:
        total_tokens = input_tokens + output_tokens
        cost = self._calculate_cost(model, input_tokens, output_tokens)

        budget = self._get_active_budget(tenant_id, user_id)
        if budget:
            budget.used_tokens = (budget.used_tokens or 0) + total_tokens
            budget.used_cost_cny = float(budget.used_cost_cny or 0) + cost
            self._db.commit()

            return {"tokens_used": total_tokens, "cost_cny": round(cost, 4),
                    "new_ratio": round(budget.usage_ratio, 4),
                    "remaining_tokens": budget.remaining_tokens}

        return {"tokens_used": total_tokens, "cost_cny": round(cost, 4),
                "new_ratio": 0.0, "remaining_tokens": -1}

    def get_usage_report(self, tenant_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        from core.models import CostBudgetLedger

        query = self._db.query(CostBudgetLedger).filter(
            CostBudgetLedger.tenant_id == tenant_id,
            CostBudgetLedger.is_active == True,
        )
        if user_id:
            query = query.filter(CostBudgetLedger.user_id == user_id)
        budgets = query.all()

        report = {"tenant_id": tenant_id, "user_id": user_id,
                  "budgets": [], "total_used_tokens": 0, "total_cost_cny": 0.0}

        for b in budgets:
            report['budgets'].append({
                "type": b.budget_type,
                "max_tokens": b.max_tokens,
                "used_tokens": b.used_tokens,
                "remaining_tokens": b.remaining_tokens,
                "usage_ratio": round(b.usage_ratio, 4),
                "max_cost_cny": float(b.max_cost_cny) if b.max_cost_cny else None,
                "used_cost_cny": float(b.used_cost_cny) if b.used_cost_cny else 0,
                "period": f"{b.period_start} ~ {b.period_end}",
                "overflow_action": b.overflow_action,
            })
            report['total_used_tokens'] += b.used_tokens or 0
            report['total_cost_cny'] += float(b.used_cost_cny) if b.used_cost_cny else 0

        report['total_cost_cny'] = round(report['total_cost_cny'], 4)
        return report

    def apply_budget(self, selected_agents: list, context: Dict[str, Any]) -> Dict[str, Any]:
        tenant_id = context.get('tenant_id', '')
        user_id = context.get('user_id')
        model = context.get('preferred_model', 'deepseek-chat')
        budget_check = self.check_budget(tenant_id, user_id, model)
        return {
            "primary_agent": selected_agents[0] if selected_agents else None,
            "secondary_agents": selected_agents[1:] if len(selected_agents) > 1 else [],
            "model": budget_check['model'],
            "budget_status": budget_check,
        }

    def _get_active_budget(self, tenant_id: str, user_id: Optional[int]):
        from core.models import CostBudgetLedger
        today = date.today()

        query = self._db.query(CostBudgetLedger).filter(
            CostBudgetLedger.tenant_id == tenant_id,
            CostBudgetLedger.is_active == True,
            CostBudgetLedger.period_start <= today,
            CostBudgetLedger.period_end >= today,
        )

        if user_id:
            user_budget = query.filter(CostBudgetLedger.user_id == user_id).first()
            if user_budget:
                return user_budget

        return query.filter(CostBudgetLedger.user_id == None).first()

    @staticmethod
    def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        rates = MODEL_COST_TABLE.get(model, (0.001, 0.002))
        return (input_tokens / 1000 * rates[0]) + (output_tokens / 1000 * rates[1])

    @staticmethod
    def _find_cheaper_model(current_model: str) -> str:
        try:
            idx = DOWNGRADE_PATH.index(current_model)
            if idx < len(DOWNGRADE_PATH) - 1:
                return DOWNGRADE_PATH[idx + 1]
        except ValueError:
            pass
        return 'qwen-turbo'
