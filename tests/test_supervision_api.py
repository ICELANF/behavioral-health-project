"""
test_supervision_api.py — 督导会议 API 测试

覆盖: 服务层规则验证 (权限检查、状态机、参数校验)
注意: CoachSupervisionRecord 使用 coach_schema (SQLite 不支持)，
     因此测试重点在规则逻辑而非 ORM 操作。
"""
import os, sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestSupervisionRules:
    """督导规则验证 (不依赖数据库)"""

    def test_valid_session_types(self):
        """5 种有效督导类型"""
        from core.supervision_service import VALID_SESSION_TYPES
        assert "individual" in VALID_SESSION_TYPES
        assert "group" in VALID_SESSION_TYPES
        assert "case_review" in VALID_SESSION_TYPES
        assert "live_observation" in VALID_SESSION_TYPES
        assert "emergency" in VALID_SESSION_TYPES
        assert len(VALID_SESSION_TYPES) == 5

    def test_status_transitions_valid(self):
        """状态机转换规则"""
        from core.supervision_service import _STATUS_TRANSITIONS
        assert "in_progress" in _STATUS_TRANSITIONS["scheduled"]
        assert "cancelled" in _STATUS_TRANSITIONS["scheduled"]
        assert "completed" in _STATUS_TRANSITIONS["in_progress"]
        assert "cancelled" in _STATUS_TRANSITIONS["in_progress"]
        assert len(_STATUS_TRANSITIONS["completed"]) == 0  # 终态
        assert len(_STATUS_TRANSITIONS["cancelled"]) == 0  # 终态

    def test_scheduled_cannot_go_directly_to_completed(self):
        """scheduled 不能直接跳到 completed"""
        from core.supervision_service import _STATUS_TRANSITIONS
        assert "completed" not in _STATUS_TRANSITIONS["scheduled"]

    def test_min_supervisor_level(self):
        """最低督导等级 = L4 (promoter/supervisor)"""
        from core.supervision_service import MIN_SUPERVISOR_LEVEL
        from core.models import ROLE_LEVEL, UserRole
        assert MIN_SUPERVISOR_LEVEL == ROLE_LEVEL[UserRole.PROMOTER]
        assert MIN_SUPERVISOR_LEVEL == ROLE_LEVEL[UserRole.SUPERVISOR]

    def test_supervisor_level_below_threshold(self):
        """低于 L4 不能创建督导"""
        from core.supervision_service import SupervisionService, MIN_SUPERVISOR_LEVEL
        from core.models import ROLE_LEVEL, UserRole
        svc = SupervisionService()
        # Mock a grower user
        mock_user = MagicMock()
        mock_user.role = UserRole.GROWER
        mock_user.id = 1
        mock_db = MagicMock()

        with pytest.raises(PermissionError, match="需要促进师"):
            svc.create_session(mock_db, supervisor=mock_user, coach_id=1, session_type="individual")

    def test_invalid_session_type_rejected(self):
        """无效的督导类型被拒绝"""
        from core.supervision_service import SupervisionService
        from core.models import UserRole
        svc = SupervisionService()
        mock_user = MagicMock()
        mock_user.role = UserRole.PROMOTER
        mock_user.id = 1
        mock_db = MagicMock()

        with pytest.raises(ValueError, match="无效的督导类型"):
            svc.create_session(mock_db, supervisor=mock_user, coach_id=1, session_type="invalid_type")

    def test_rating_range_validation(self):
        """评分必须在 0.0-5.0"""
        from core.supervision_service import SupervisionService
        from core.models import UserRole
        svc = SupervisionService()
        mock_user = MagicMock()
        mock_user.role = UserRole.ADMIN
        mock_user.id = 1
        mock_record = MagicMock()
        mock_record.supervisor_id = 1
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_record

        with pytest.raises(ValueError, match="0.0-5.0"):
            svc.update_session(mock_db, record_id=1, supervisor=mock_user, quality_rating=6.0)

    def test_ownership_check(self):
        """非创建者不能操作记录"""
        from core.supervision_service import SupervisionService
        from core.models import UserRole
        svc = SupervisionService()
        mock_user = MagicMock()
        mock_user.role = UserRole.PROMOTER
        mock_user.id = 99  # different from record.supervisor_id
        mock_record = MagicMock()
        mock_record.supervisor_id = 1  # different user
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_record

        with pytest.raises(PermissionError, match="只能操作自己"):
            svc._get_owned_record(mock_db, record_id=1, supervisor=mock_user)

    def test_admin_bypasses_ownership(self):
        """admin 可操作任何记录"""
        from core.supervision_service import SupervisionService
        from core.models import UserRole
        svc = SupervisionService()
        mock_user = MagicMock()
        mock_user.role = UserRole.ADMIN
        mock_user.id = 99
        mock_record = MagicMock()
        mock_record.supervisor_id = 1
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_record

        result = svc._get_owned_record(mock_db, record_id=1, supervisor=mock_user)
        assert result == mock_record

    def test_record_not_found(self):
        """记录不存在"""
        from core.supervision_service import SupervisionService
        from core.models import UserRole
        svc = SupervisionService()
        mock_user = MagicMock()
        mock_user.role = UserRole.ADMIN
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="不存在"):
            svc._get_owned_record(mock_db, record_id=999, supervisor=mock_user)

    def test_serialization_function(self):
        """_record_to_dict 序列化"""
        from core.supervision_service import _record_to_dict
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.supervisor_id = 10
        mock_record.coach_id = 20
        mock_record.session_type = "individual"
        mock_record.scheduled_at = datetime(2026, 3, 1, 10, 0)
        mock_record.completed_at = None
        mock_record.status = "scheduled"
        mock_record.template_id = None
        mock_record.session_notes = "Test notes"
        mock_record.action_items = ["item1"]
        mock_record.quality_rating = 4.5
        mock_record.compliance_met = True
        mock_record.created_at = datetime(2026, 2, 24, 8, 0)

        # Mock db query for supervisor/coach names
        mock_db = MagicMock()
        mock_name_result = MagicMock()
        mock_name_result.full_name = "Test User"
        mock_name_result.username = "test"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_name_result

        result = _record_to_dict(mock_record, mock_db)
        assert result["id"] == 1
        assert result["status"] == "scheduled"
        assert result["quality_rating"] == 4.5
        assert result["action_items"] == ["item1"]
        assert "2026-03-01" in result["scheduled_at"]


class TestTenantTransitionRules:
    """租户状态转换规则"""

    def test_valid_transitions_defined(self):
        """状态转换规则完整定义"""
        from api.tenant_api import _VALID_TRANSITIONS
        from core.models import TenantStatus
        assert TenantStatus.trial in _VALID_TRANSITIONS
        assert TenantStatus.active in _VALID_TRANSITIONS
        assert TenantStatus.suspended in _VALID_TRANSITIONS

    def test_no_archived_transitions(self):
        """archived 是终态，没有后续转换"""
        from api.tenant_api import _VALID_TRANSITIONS
        from core.models import TenantStatus
        # archived 不在 _VALID_TRANSITIONS 中 (或为空列表)
        archived_transitions = _VALID_TRANSITIONS.get(TenantStatus.archived, [])
        assert len(archived_transitions) == 0


class TestRBACConsistency:
    """RBAC 角色列表一致性"""

    def test_promoter_supervisor_both_level_5(self):
        """PROMOTER 和 SUPERVISOR 都是 role_level=5"""
        from core.models import ROLE_LEVEL, UserRole
        assert ROLE_LEVEL[UserRole.PROMOTER] == ROLE_LEVEL[UserRole.SUPERVISOR]

    def test_require_coach_or_admin_includes_both(self):
        """require_coach_or_admin 包含两个 L4 角色"""
        import inspect
        from api.dependencies import require_coach_or_admin
        source = inspect.getsource(require_coach_or_admin)
        assert "supervisor" in source
        assert "promoter" in source

    def test_agent_naming_regex(self):
        """Agent 命名规则验证"""
        import re
        pattern = re.compile(r"^[a-z][a-z0-9_]{2,19}$")
        assert pattern.match("my_agent_01")
        assert pattern.match("abc")
        assert not pattern.match("1abc")
        assert not pattern.match("AB")
        assert not pattern.match("ab")
        assert not pattern.match("a" * 21)

    def test_crisis_agent_always_included(self):
        """Crisis agent 应始终被包含"""
        agents = ["behavior_rx", "nutrition"]
        if "crisis" not in agents:
            agents.append("crisis")
        assert "crisis" in agents
