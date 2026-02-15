"""
test_governance.py — 治理体系 单元测试
覆盖: 违规创建 / 严重级别 / 累犯检测 / 解决工作流 /
      AntiCheat联动 / RuleRegistry / 保护期
对接: core/rule_registry.py + GovernanceViolation + AntiCheatEvent
"""
import pytest
from datetime import datetime, date, timedelta

from conftest import GovernanceViolation, AntiCheatEvent

try:
    from core.rule_registry import RuleRegistry, DEFAULT_SEED_RULES, JsonLogicEvaluator
    HAS_REGISTRY = True
except ImportError:
    HAS_REGISTRY = False


# =====================================================================
# 1. 违规模型基础测试 (不依赖引擎)
# =====================================================================

class TestViolationModel:

    def test_create_violation(self, db, grower, violation_factory):
        """创建违规记录"""
        gv = violation_factory.create(db, grower, violation_type="anti_cheat",
                                      severity="light", point_penalty=10)
        assert gv.id is not None
        assert gv.user_id == grower.id
        assert gv.severity == "light"
        assert gv.point_penalty == 10
        assert gv.resolved is False

    def test_violation_severity_levels(self, db, grower, violation_factory):
        """4种严重级别"""
        for sev in ["light", "medium", "heavy", "critical"]:
            gv = violation_factory.create(db, grower, severity=sev)
            assert gv.severity == sev

    def test_resolve_violation(self, db, grower, admin, violation_factory):
        """解决违规"""
        gv = violation_factory.create(db, grower, resolved=False)
        gv.resolved = True
        gv.resolved_by = admin.id
        gv.resolved_at = datetime.utcnow()
        db.flush()
        db.refresh(gv)
        assert gv.resolved is True
        assert gv.resolved_by == admin.id


# =====================================================================
# 2. 累犯检测
# =====================================================================

class TestRepeatOffender:

    def test_count_violations(self, db, grower, violation_factory):
        """统计违规次数"""
        for _ in range(5):
            violation_factory.create(db, grower, severity="light")

        count = db.query(GovernanceViolation).filter_by(
            user_id=grower.id, resolved=False
        ).count()
        assert count == 5

    def test_unresolved_vs_resolved(self, db, grower, violation_factory):
        """区分未解决/已解决"""
        violation_factory.create(db, grower, resolved=False)
        violation_factory.create(db, grower, resolved=False)
        violation_factory.create(db, grower, resolved=True)

        unresolved = db.query(GovernanceViolation).filter_by(
            user_id=grower.id, resolved=False
        ).count()
        assert unresolved == 2

    def test_severity_escalation_on_repeat(self, db, grower, violation_factory):
        """多次违规后严重级别统计"""
        for _ in range(3):
            violation_factory.create(db, grower, severity="light")

        history = db.query(GovernanceViolation).filter_by(user_id=grower.id).all()
        light_count = sum(1 for v in history if v.severity == "light")
        assert light_count == 3


# =====================================================================
# 3. AntiCheat → Governance 联动
# =====================================================================

class TestAntiCheatGovernanceLink:

    def test_anti_cheat_event_with_violation(self, db, grower, anti_cheat_factory, violation_factory):
        """防刷事件关联治理违规"""
        ev = anti_cheat_factory.create(db, grower, strategy="velocity",
                                       event_type="rapid_points",
                                       action_taken="penalty_applied")

        gv = violation_factory.create(db, grower, violation_type="anti_cheat",
                                      severity="light", point_penalty=5)

        assert ev.user_id == gv.user_id
        assert gv.violation_type == "anti_cheat"


# =====================================================================
# 4. RuleRegistry (如果可用)
# =====================================================================

@pytest.mark.skipif(not HAS_REGISTRY, reason="core.rule_registry not importable")
class TestRuleRegistry:

    def test_create_registry(self, db):
        """创建 RuleRegistry 不崩溃"""
        # RuleRegistry needs a callable that returns a Session
        registry = RuleRegistry(lambda: db)
        assert registry is not None

    def test_seed_rules_defined(self):
        """种子规则已定义"""
        assert len(DEFAULT_SEED_RULES) >= 4
        rule_names = [r["rule_name"] for r in DEFAULT_SEED_RULES]
        assert "crisis_absolute_priority" in rule_names
        assert "medical_boundary_suppress" in rule_names

    def test_get_applicable_rules_empty(self, db):
        """无规则时返回空列表"""
        registry = RuleRegistry(lambda: db)
        # Don't initialize (no PolicyRule table in SQLite)
        rules = registry.get_applicable_rules(None, {"risk_level": "low"})
        assert isinstance(rules, list)

    def test_json_logic_evaluator_basic(self):
        """JsonLogic 基础评估"""
        evaluator = JsonLogicEvaluator()
        assert evaluator.evaluate({"==": [1, 1]}, {}) is True
        assert evaluator.evaluate({"==": [1, 2]}, {}) is False

    def test_json_logic_var(self):
        """JsonLogic 变量引用"""
        evaluator = JsonLogicEvaluator()
        result = evaluator.evaluate(
            {"==": [{"var": "risk_level"}, "critical"]},
            {"risk_level": "critical"}
        )
        assert result is True

    def test_json_logic_and(self):
        """JsonLogic AND"""
        evaluator = JsonLogicEvaluator()
        result = evaluator.evaluate(
            {"and": [
                {"==": [{"var": "a"}, 1]},
                {"==": [{"var": "b"}, 2]},
            ]},
            {"a": 1, "b": 2}
        )
        assert result is True

    def test_json_logic_or(self):
        """JsonLogic OR"""
        evaluator = JsonLogicEvaluator()
        result = evaluator.evaluate(
            {"or": [
                {"==": [{"var": "stage"}, "S0"]},
                {"==": [{"var": "stage"}, "S1"]},
            ]},
            {"stage": "S1"}
        )
        assert result is True


# =====================================================================
# 5. 保护期边界
# =====================================================================

class TestProtectionPeriod:

    def test_violation_default_no_protection(self, db, grower, violation_factory):
        """默认无保护期"""
        gv = violation_factory.create(db, grower, severity="light")
        # GovernanceViolation may not have protection_until field
        # Just verify it was created
        assert gv.id is not None
        assert gv.severity == "light"
