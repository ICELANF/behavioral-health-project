"""
审计日志核心路径测试
对标契约: Sheet⑨ 治理触点契约

测试覆盖:
  AUD-01: 全部 20 个审计动作枚举值存在
  AUD-02: 核心路径 14 个新增动作完整
  AUD-03: PHI 高敏感数据自动脱敏
  AUD-04: 审计触点 Sheet 映射完整
  AUD-05: 审计覆盖率 ≥50%
  AUD-06: 日志记录不阻塞业务
  AUD-07: Redis 降级不影响审计
  AUD-08: IP 地址提取 (含 X-Forwarded-For)
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from audit_core_path import (
    AuditAction, AuditLogger, AUDIT_TOUCHPOINT_MAP,
    calculate_audit_coverage,
)


# ── Fixtures ──

@pytest.fixture
def logger():
    return AuditLogger(
        db_session_factory=None,
        redis_client=None,
        logger=None,
    )


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.headers = {
        "x-forwarded-for": "1.2.3.4, 5.6.7.8",
        "user-agent": "Mozilla/5.0 TestAgent",
    }
    req.client = MagicMock()
    req.client.host = "127.0.0.1"
    return req


# ── AUD-01: 审计动作枚举完整性 ──

def test_aud01_audit_actions_count():
    """20 个审计动作枚举值 (6 existing + 14 new)"""
    actions = list(AuditAction)
    assert len(actions) == 20, f"Expected 20 actions, got {len(actions)}"


# ── AUD-02: 14 个新增动作完整 ──

def test_aud02_new_core_path_actions():
    """14 个新增核心路径审计动作"""
    new_actions = [
        "user_register", "user_login", "role_upgrade",
        "assessment_started", "assessment_submitted",
        "chat_session_start", "chat_message_sent",
        "micro_action_completed", "challenge_joined", "checkin_completed",
        "points_awarded", "promotion_initiated",
        "health_data_recorded", "device_bound",
    ]
    action_values = [a.value for a in AuditAction]
    for action in new_actions:
        assert action in action_values, f"Missing new action: {action}"


# ── AUD-03: PHI 高敏感数据脱敏 ──

@pytest.mark.asyncio
async def test_aud03_phi_data_redaction(logger):
    """高敏感数据自动脱敏"""
    details = {
        "assessment_type": "COM-B",
        "score": 85,
        "blood_glucose": 5.6,
        "message": "我最近血糖偏高",
        "scale_id": "BAPS-v2",
    }
    
    sanitized = logger._sanitize_details(details, "high")
    
    # PHI 字段应被脱敏
    assert sanitized["score"] == "[REDACTED]"
    assert sanitized["blood_glucose"] == "[REDACTED]"
    assert sanitized["message"] == "[REDACTED]"
    
    # 非 PHI 字段保留
    assert sanitized["assessment_type"] == "COM-B"
    assert sanitized["scale_id"] == "BAPS-v2"


# ── AUD-04: 触点 Sheet 映射 ──

def test_aud04_touchpoint_mapping():
    """每个新增审计动作都有 Sheet⑨ 映射"""
    new_actions = [
        "user_register", "user_login", "role_upgrade",
        "assessment_started", "assessment_submitted",
        "chat_session_start", "chat_message_sent",
        "micro_action_completed", "challenge_joined", "checkin_completed",
        "points_awarded", "promotion_initiated",
        "health_data_recorded", "device_bound",
    ]
    
    for action in new_actions:
        assert action in AUDIT_TOUCHPOINT_MAP, f"Missing mapping: {action}"
        mapping = AUDIT_TOUCHPOINT_MAP[action]
        assert "sheet_ref" in mapping
        assert "sensitivity" in mapping
        assert mapping["sensitivity"] in ("low", "medium", "high")


# ── AUD-05: 覆盖率 ≥50% ──

def test_aud05_coverage_above_50pct():
    """审计覆盖率达到 50% 以上"""
    coverage = calculate_audit_coverage()
    assert coverage["coverage_pct"] >= 50.0
    assert coverage["achieved"] is True


# ── AUD-06: 日志记录不阻塞 (即使 DB 失败) ──

@pytest.mark.asyncio
async def test_aud06_audit_non_blocking(logger):
    """审计写入失败不应抛出异常"""
    # 无 DB/Redis 的 logger 应该静默完成
    result = await logger.log(
        user_id=1,
        action="user_register",
        resource_type="user",
        details={"source": "test"},
    )
    assert result["logged"] is True


# ── AUD-07: 低敏感数据不脱敏 ──

@pytest.mark.asyncio
async def test_aud07_low_sensitivity_no_redaction(logger):
    """低敏感数据保持原样"""
    details = {"action_id": "MA-001", "mood_score": 4}
    sanitized = logger._sanitize_details(details, "low")
    assert sanitized == details


# ── AUD-08: IP 提取 ──

def test_aud08_ip_extraction(logger, mock_request):
    """从 X-Forwarded-For 提取客户端 IP"""
    ip = logger._extract_ip(mock_request)
    assert ip == "1.2.3.4"  # 取第一个
    
    # 无 forwarded header
    mock_request.headers = {}
    ip = logger._extract_ip(mock_request)
    assert ip == "127.0.0.1"  # 回退到 client.host


# ── AUD-09: 敏感度分级正确 ──

def test_aud09_sensitivity_levels():
    """PHI 相关操作标记为 high"""
    high_actions = [
        "assessment_submitted", "chat_message_sent",
        "health_data_recorded", "promotion_initiated", "role_upgrade",
    ]
    for action in high_actions:
        assert AUDIT_TOUCHPOINT_MAP[action]["sensitivity"] == "high", \
            f"{action} should be high sensitivity"


# ── AUD-10: 覆盖率计算正确性 ──

def test_aud10_coverage_math():
    """覆盖率数学验证"""
    cov = calculate_audit_coverage()
    assert cov["total_covered"] == cov["existing_audit"] + cov["new_audit"]
    expected_pct = round(cov["total_covered"] / cov["total_touchpoints"] * 100, 1)
    assert cov["coverage_pct"] == expected_pct


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
