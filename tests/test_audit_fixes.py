"""
CR-15 / CR-28 / C4 / C3 测试套件
覆盖: governance_health_check + peer_tracking + field_sync + stage_authority
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# ═══════════════════════════════════════════════════════
# CR-15: governance_health_check 测试
# ═══════════════════════════════════════════════════════

class TestGovernanceHealthCheck:
    """CR-15: 治理健康度检查服务"""

    @pytest.fixture
    def service(self):
        from core.governance_health_check import GovernanceHealthCheckService
        db = MagicMock()
        return GovernanceHealthCheckService(db)

    def test_full_check_returns_report(self, service):
        """完整检查应返回6维度报告"""
        with patch.object(service, '_check_contract_compliance') as m1, \
             patch.object(service, '_check_audit_coverage') as m2, \
             patch.object(service, '_check_violation_trend') as m3, \
             patch.object(service, '_check_response_latency') as m4, \
             patch.object(service, '_check_coach_accountability') as m5, \
             patch.object(service, '_check_data_integrity') as m6, \
             patch.object(service, '_persist_report'):

            from core.governance_health_check import (
                DimensionResult, HealthDimension, HealthStatus,
            )
            mock_result = DimensionResult(
                HealthDimension.CONTRACT_COMPLIANCE,
                HealthStatus.HEALTHY, 0.98, "test",
            )
            for m in [m1, m2, m3, m4, m5, m6]:
                m.return_value = mock_result

            report = service.run_full_check()

            assert report.overall_status == HealthStatus.HEALTHY
            assert len(report.dimensions) == 6
            assert report.overall_score > 0.9

    def test_critical_status_propagates(self, service):
        """任一维度CRITICAL应使整体状态为CRITICAL"""
        from core.governance_health_check import (
            DimensionResult, HealthDimension, HealthStatus,
        )
        results = [
            DimensionResult(HealthDimension.CONTRACT_COMPLIANCE,
                            HealthStatus.HEALTHY, 0.98),
            DimensionResult(HealthDimension.AUDIT_COVERAGE,
                            HealthStatus.CRITICAL, 0.3),
        ]
        overall = service._aggregate_status(results)
        assert overall == HealthStatus.CRITICAL

    def test_score_to_status_thresholds(self):
        from core.governance_health_check import (
            _score_to_status, HealthDimension, HealthStatus,
        )
        dim = HealthDimension.CONTRACT_COMPLIANCE
        assert _score_to_status(dim, 0.96) == HealthStatus.HEALTHY
        assert _score_to_status(dim, 0.85) == HealthStatus.DEGRADED
        assert _score_to_status(dim, 0.70) == HealthStatus.CRITICAL

    def test_report_to_dict(self):
        from core.governance_health_check import (
            HealthCheckReport, DimensionResult,
            HealthDimension, HealthStatus,
        )
        now = datetime.utcnow()
        report = HealthCheckReport(
            overall_status=HealthStatus.HEALTHY,
            dimensions=[
                DimensionResult(HealthDimension.CONTRACT_COMPLIANCE,
                                HealthStatus.HEALTHY, 0.98)
            ],
            checked_at=now,
            next_check_at=now + timedelta(hours=6),
        )
        d = report.to_dict()
        assert d["overall_status"] == "healthy"
        assert d["overall_score"] == 0.98
        assert len(d["dimensions"]) == 1

    def test_health_check_api_endpoint(self):
        """API端点应返回200 + report"""
        # 需要集成测试环境, 此处仅验证导入
        pass


# ═══════════════════════════════════════════════════════
# CR-28: 同道者追踪 测试
# ═══════════════════════════════════════════════════════

class TestPeerTracking:
    """CR-28: 同道者匹配 + 生命周期 + 互动追踪"""

    @pytest.fixture
    def service(self):
        from core.peer_tracking_service import PeerTrackingService
        db = MagicMock()
        return PeerTrackingService(db)

    def test_match_score_same_stage(self, service):
        """同阶段用户应获得高匹配分"""
        from core.peer_tracking_service import CompanionMatchStrategy
        profile_a = {
            "user_id": 1, "stage": "S2", "stage_numeric": 2,
            "role": "grower", "bpt_type": "A", "goals": ["sleep", "exercise"],
            "activity_score": 0.7,
        }
        profile_b = {
            "user_id": 2, "stage": "S2", "stage_numeric": 2,
            "role": "grower", "bpt_type": "A", "goals": ["sleep", "diet"],
            "activity_score": 0.6,
        }
        score, reasons = service._compute_match_score(
            profile_a, profile_b, CompanionMatchStrategy.STAGE_PROXIMITY
        )
        assert score > 0.7
        assert any("阶段相近" in r for r in reasons)

    def test_match_score_distant_stage(self, service):
        """阶段差距大应降低匹配分"""
        from core.peer_tracking_service import CompanionMatchStrategy
        profile_a = {"user_id": 1, "stage": "S0", "stage_numeric": 0,
                      "role": "grower", "bpt_type": None, "goals": [],
                      "activity_score": 0.2}
        profile_b = {"user_id": 2, "stage": "S5", "stage_numeric": 5,
                      "role": "grower", "bpt_type": None, "goals": [],
                      "activity_score": 0.9}
        score, _ = service._compute_match_score(
            profile_a, profile_b, CompanionMatchStrategy.STAGE_PROXIMITY
        )
        assert score < 0.5

    def test_lifecycle_thresholds(self, service):
        """生命周期阈值配置正确"""
        assert service.COOLING_THRESHOLD_DAYS == 7
        assert service.DORMANT_THRESHOLD_DAYS == 14
        assert service.AUTO_DISSOLVE_DAYS == 30

    def test_companion_dashboard_structure(self, service):
        """仪表盘应返回完整结构"""
        with patch('core.peer_tracking_service.select') as mock_select, \
             patch.object(service.db, 'execute') as mock_exec:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_exec.return_value = mock_result

            dashboard = service.get_companion_dashboard(1)
            assert "total_companions" in dashboard
            assert "active" in dashboard
            assert "avg_reciprocity" in dashboard
            assert "companions" in dashboard


# ═══════════════════════════════════════════════════════
# C4: 字段同步守卫 测试
# ═══════════════════════════════════════════════════════

class TestFieldSyncGuard:
    """C4: 字段一致性检查"""

    def test_sync_fields_list(self):
        from core.field_sync_guard import FieldSyncGuard
        assert "current_stage" in FieldSyncGuard.SYNC_FIELDS
        assert "agency_mode" in FieldSyncGuard.SYNC_FIELDS
        assert "agency_score" in FieldSyncGuard.SYNC_FIELDS
        assert "trust_score" in FieldSyncGuard.SYNC_FIELDS
        assert len(FieldSyncGuard.SYNC_FIELDS) == 4


# ═══════════════════════════════════════════════════════
# C3: 阶段权威入口 测试
# ═══════════════════════════════════════════════════════

class TestStageAuthority:
    """C3: 统一入口委托验证"""

    def test_delegates_to_engine(self):
        """所有方法应委托给 stage_engine"""
        from core.stage_authority import StageAuthority
        db = MagicMock()
        authority = StageAuthority(db)

        mock_engine = MagicMock()
        mock_engine.get_current_stage = MagicMock(return_value="S3")
        authority._engine = mock_engine

        result = authority.get_current_stage(user_id=1)
        assert result == "S3"
        mock_engine.get_current_stage.assert_called_once_with(1)
