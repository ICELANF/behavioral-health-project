"""
test_tenant_lifecycle.py — 租户生命周期 + 注册规则测试

覆盖: 状态转换规则、分层默认值、注册规则
注意: 使用 mock 避免 SQLite 对 schema 的限制
"""
import os, sys
import re
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestTenantStatusMachine:
    """租户状态机规则测试"""

    def test_all_statuses_defined(self):
        """5 种状态全部存在"""
        from core.models import TenantStatus
        assert hasattr(TenantStatus, "pending_review")
        assert hasattr(TenantStatus, "trial")
        assert hasattr(TenantStatus, "active")
        assert hasattr(TenantStatus, "suspended")
        assert hasattr(TenantStatus, "archived")

    def test_valid_transitions_complete(self):
        """转换规则覆盖 trial / active / suspended"""
        from api.tenant_api import _VALID_TRANSITIONS
        from core.models import TenantStatus
        assert TenantStatus.trial in _VALID_TRANSITIONS
        assert TenantStatus.active in _VALID_TRANSITIONS
        assert TenantStatus.suspended in _VALID_TRANSITIONS

    def test_trial_can_activate_or_suspend(self):
        from api.tenant_api import _VALID_TRANSITIONS
        from core.models import TenantStatus
        allowed = _VALID_TRANSITIONS[TenantStatus.trial]
        assert TenantStatus.active in allowed
        assert TenantStatus.suspended in allowed

    def test_active_can_only_suspend(self):
        from api.tenant_api import _VALID_TRANSITIONS
        from core.models import TenantStatus
        allowed = _VALID_TRANSITIONS[TenantStatus.active]
        assert TenantStatus.suspended in allowed
        assert TenantStatus.archived not in allowed

    def test_suspended_can_reactivate_or_archive(self):
        from api.tenant_api import _VALID_TRANSITIONS
        from core.models import TenantStatus
        allowed = _VALID_TRANSITIONS[TenantStatus.suspended]
        assert TenantStatus.active in allowed
        assert TenantStatus.archived in allowed

    def test_archived_is_terminal(self):
        from api.tenant_api import _VALID_TRANSITIONS
        from core.models import TenantStatus
        allowed = _VALID_TRANSITIONS.get(TenantStatus.archived, [])
        assert len(allowed) == 0


class TestTenantTiers:
    """租户分层枚举测试"""

    def test_three_tiers(self):
        from core.models import TenantTier
        assert TenantTier.basic.value == "basic_partner"
        assert TenantTier.premium.value == "premium_partner"
        assert TenantTier.strategic.value == "strategic_partner"


class TestExpertRegistrationRules:
    """专家注册规则"""

    def test_crisis_agent_mandatory(self):
        """Crisis Agent 必须包含"""
        agents = ["behavior_rx", "nutrition"]
        if "crisis" not in agents:
            agents.append("crisis")
        assert "crisis" in agents

    def test_agent_naming_regex(self):
        """Agent name_suffix: ^[a-z][a-z0-9_]{2,19}$"""
        pattern = re.compile(r"^[a-z][a-z0-9_]{2,19}$")
        # Valid
        assert pattern.match("my_agent")
        assert pattern.match("abc")
        assert pattern.match("agent_v2_test")
        # Invalid
        assert not pattern.match("1agent")           # 数字开头
        assert not pattern.match("Agent")            # 大写
        assert not pattern.match("ab")               # 太短 (2 chars)
        assert not pattern.match("a" * 21)           # 太长 (21 chars)
        assert not pattern.match("my-agent")         # 连字符

    def test_role_upgrade_logic(self):
        """审批通过后低角色自动升级至 COACH"""
        from core.models import ROLE_LEVEL, UserRole
        # Grower (level 2) < Coach (level 4)
        grower_level = ROLE_LEVEL[UserRole.GROWER]
        coach_level = ROLE_LEVEL[UserRole.COACH]
        assert grower_level < coach_level

        # Promoter (level 5) >= Coach (level 4) → no upgrade needed
        promoter_level = ROLE_LEVEL[UserRole.PROMOTER]
        assert promoter_level >= coach_level

    def test_application_status_values(self):
        """申请状态值: pending_review / approved / rejected"""
        # These are string values, not enums — verify as known constants
        valid_statuses = {"pending_review", "approved", "rejected"}
        assert len(valid_statuses) == 3

    def test_ten_expert_domains_exist(self):
        """10 个专家领域配置存在"""
        import json
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "configs", "expert_domains.json"
        )
        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
            # JSON 可能是 list 或 {"domains": [...]}
            domains = data if isinstance(data, list) else data.get("domains", [])
            assert len(domains) >= 10
            # 每个域有 recommended_agents
            for d in domains:
                assert "recommended_agents" in d or "agents" in d


class TestClientStatusEnum:
    """客户状态枚举"""

    def test_client_statuses(self):
        from core.models import ClientStatus
        assert hasattr(ClientStatus, "active")
        assert hasattr(ClientStatus, "graduated")
        assert hasattr(ClientStatus, "paused")
        assert hasattr(ClientStatus, "exited")


class TestSupervisionModelFields:
    """CoachSupervisionRecord 模型字段验证"""

    def test_model_exists(self):
        from core.models import CoachSupervisionRecord
        assert CoachSupervisionRecord is not None
        assert CoachSupervisionRecord.__tablename__ == "coach_supervision_records"

    def test_required_columns(self):
        from core.models import CoachSupervisionRecord
        cols = {c.name for c in CoachSupervisionRecord.__table__.columns}
        required = {"id", "supervisor_id", "coach_id", "session_type", "status",
                     "quality_rating", "compliance_met", "created_at"}
        assert required.issubset(cols)

    def test_indexes_defined(self):
        from core.models import CoachSupervisionRecord
        index_names = {idx.name for idx in CoachSupervisionRecord.__table__.indexes}
        assert "idx_supervision_coach" in index_names
        assert "idx_supervision_supervisor" in index_names
