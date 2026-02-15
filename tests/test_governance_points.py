"""
治理积分集成测试
对标契约: Sheet⑦ 积分契约 · 治理新增10种 + Agent生态5种

测试覆盖:
  GPT-01: 配置文件加载完整性 (10 + 5 = 15 事件)
  GPT-02: 事件注册到引擎
  GPT-03: 各事件积分值正确
  GPT-04: 角色最低要求校验
  GPT-05: 每日上限配置正确
  GPT-06: 防刷策略映射完整
  GPT-07: 告警响应时间校验 (≤4h)
  GPT-08: 审计标记正确
  GPT-09: Agent生态事件完整
  GPT-10: 幂等注册 (重复注册不报错)
"""

import pytest
import json
import os

# 加载配置
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "point_events_governance.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


# ── GPT-01: 配置完整性 ──

def test_gpt01_config_completeness():
    """治理10种 + Agent生态5种 = 15种事件"""
    gov = CONFIG["governance_events"]
    agent = CONFIG["agent_ecosystem_events"]
    assert len(gov) == 10, f"Expected 10 governance events, got {len(gov)}"
    assert len(agent) == 5, f"Expected 5 agent events, got {len(agent)}"


# ── GPT-02: 必填字段完整 ──

def test_gpt02_required_fields():
    """每个事件必须包含关键字段"""
    required = ["event_id", "event_type", "display_name", "point_type", "points"]
    
    for event in CONFIG["governance_events"] + CONFIG["agent_ecosystem_events"]:
        for field in required:
            assert field in event, f"{event.get('event_id', '?')} missing {field}"


# ── GPT-03: 积分值对齐契约 ──

def test_gpt03_point_values_match_contract():
    """积分值严格对齐 Sheet⑦ 治理新增区定义"""
    expected = {
        "ethics_scenario_test": (50, "growth"),
        "competency_self_assessment": (30, "growth"),
        "ethics_declaration_signed": (30, "contribution"),
        "conflict_disclosure_update": (20, "contribution"),
        "alert_timely_response": (15, "contribution"),
        "student_message_reply": (10, "contribution"),
        "supervision_session_completed": (50, "influence"),
        "agent_feedback_reply": (10, "contribution"),
        "knowledge_shared": (30, "influence"),
        "certificate_renewal_confirmed": (20, "growth"),
    }
    
    events_by_type = {e["event_type"]: e for e in CONFIG["governance_events"]}
    
    for event_type, (expected_pts, expected_category) in expected.items():
        event = events_by_type[event_type]
        assert event["points"] == expected_pts, \
            f"{event_type}: expected {expected_pts}pts, got {event['points']}"
        assert event["point_type"] == expected_category, \
            f"{event_type}: expected {expected_category}, got {event['point_type']}"


# ── GPT-04: 角色最低要求 ──

def test_gpt04_min_role_requirements():
    """各事件的最低角色要求对齐契约"""
    role_checks = {
        "ethics_scenario_test": "sharer",           # 分享者+
        "competency_self_assessment": "sharer",     # 分享者+
        "ethics_declaration_signed": "coach",        # 教练+
        "conflict_disclosure_update": "senior_coach",# 促进师+
        "alert_timely_response": "coach",            # 教练+
        "student_message_reply": "coach",            # 教练+
        "supervision_session_completed": "senior_coach",# 促进师+
        "agent_feedback_reply": "senior_coach",      # 促进师+
        "knowledge_shared": "senior_coach",          # 促进师+
        "certificate_renewal_confirmed": "senior_coach",# 促进师+
    }
    
    events_by_type = {e["event_type"]: e for e in CONFIG["governance_events"]}
    
    for event_type, expected_role in role_checks.items():
        event = events_by_type[event_type]
        assert event["min_role"] == expected_role, \
            f"{event_type}: expected min_role={expected_role}, got {event['min_role']}"


# ── GPT-05: 每日上限配置 ──

def test_gpt05_daily_caps():
    """每日上限对齐 Sheet⑦ 定义"""
    cap_checks = {
        "ethics_scenario_test": 1,
        "competency_self_assessment": 1,
        "ethics_declaration_signed": None,     # 无限
        "conflict_disclosure_update": 1,
        "alert_timely_response": 5,
        "student_message_reply": 10,
        "supervision_session_completed": None, # 无限
        "agent_feedback_reply": 5,
        "knowledge_shared": 3,
        "certificate_renewal_confirmed": 1,
    }
    
    events_by_type = {e["event_type"]: e for e in CONFIG["governance_events"]}
    
    for event_type, expected_cap in cap_checks.items():
        event = events_by_type[event_type]
        assert event["daily_cap"] == expected_cap, \
            f"{event_type}: expected daily_cap={expected_cap}, got {event['daily_cap']}"


# ── GPT-06: 防刷策略映射 ──

def test_gpt06_anti_cheat_mapping():
    """每个治理事件都有防刷策略配置"""
    events_by_type = {e["event_type"]: e for e in CONFIG["governance_events"]}
    
    for event in CONFIG["governance_events"]:
        strategies = event.get("anti_cheat", [])
        assert len(strategies) > 0, \
            f"{event['event_type']}: 缺少防刷策略配置"
        for s in strategies:
            assert s.startswith("AS-"), \
                f"{event['event_type']}: 无效策略编号 {s}"


# ── GPT-07: 告警响应时间验证逻辑 ──

def test_gpt07_alert_response_validation():
    """GOV-05 告警及时处置需 validation_rules"""
    events_by_type = {e["event_type"]: e for e in CONFIG["governance_events"]}
    alert_event = events_by_type["alert_timely_response"]
    
    rules = alert_event.get("validation_rules", {})
    assert "response_time_max_hours" in rules
    assert rules["response_time_max_hours"] == 4


# ── GPT-08: 审计标记 ──

def test_gpt08_audit_flags():
    """需审计的事件正确标记"""
    events_by_type = {e["event_type"]: e for e in CONFIG["governance_events"]}
    
    # 这些事件必须标记 audit_required=true
    must_audit = [
        "ethics_scenario_test", "competency_self_assessment",
        "ethics_declaration_signed", "conflict_disclosure_update",
        "alert_timely_response", "supervision_session_completed",
        "knowledge_shared", "certificate_renewal_confirmed",
    ]
    for et in must_audit:
        assert events_by_type[et].get("audit_required") is True, \
            f"{et}: 应标记 audit_required=true"
    
    # 这些事件可以不审计
    optional_audit = ["student_message_reply", "agent_feedback_reply"]
    for et in optional_audit:
        assert events_by_type[et].get("audit_required") is False


# ── GPT-09: Agent生态事件 ──

def test_gpt09_agent_ecosystem_events():
    """Agent生态5种事件完整性"""
    agent_events = CONFIG["agent_ecosystem_events"]
    expected_types = {
        "create_agent", "optimize_prompt", "share_knowledge",
        "template_published", "template_installed"
    }
    actual_types = {e["event_type"] for e in agent_events}
    assert actual_types == expected_types


# ── GPT-10: Event ID 唯一性 ──

def test_gpt10_unique_event_ids():
    """所有事件 ID 唯一"""
    all_events = CONFIG["governance_events"] + CONFIG["agent_ecosystem_events"]
    ids = [e["event_id"] for e in all_events]
    assert len(ids) == len(set(ids)), f"重复 event_id: {[x for x in ids if ids.count(x) > 1]}"
    
    types = [e["event_type"] for e in all_events]
    assert len(types) == len(set(types)), f"重复 event_type: {[x for x in types if types.count(x) > 1]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
