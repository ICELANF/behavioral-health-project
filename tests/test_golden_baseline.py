"""
Phase 0 — 核心链路 Golden Test

三条链路基线:
  1. chat 对话链路
  2. assessment 评估链路 (via submit_assessment)
  3. device-sync 设备同步链路

验收: 响应结构正确 + 关键字段存在 + 无异常
"""
import pytest


def _get_master_agent():
    try:
        from core.agents.registry import AgentRegistry
        from core.agents.startup import register_all_agents
        registry = AgentRegistry()
        register_all_agents(registry)
        registry.freeze()
        from core.agents.master_agent import MasterAgent
        return MasterAgent(registry=registry)
    except ImportError:
        pass
    try:
        from core.master_agent_unified import get_master_agent
        return get_master_agent()
    except ImportError:
        pass
    from core.agents.master_agent import MasterAgent
    return MasterAgent()


@pytest.fixture(scope="module")
def agent():
    return _get_master_agent()


# ═══════════════════════════════════════════════
# Golden 1: Chat 对话链路
# ═══════════════════════════════════════════════

class TestChatGolden:

    def test_chat_returns_response_string(self, agent):
        """chat() 返回非空字符串"""
        if hasattr(agent, "chat"):
            result = agent.chat(user_id=1, message="我最近血糖偏高怎么办")
            assert isinstance(result, str)
            assert len(result) > 0
        else:
            pytest.skip("agent 无 chat() 方法")

    def test_process_returns_required_keys(self, agent):
        """process() 必须返回核心 key"""
        result = agent.process(
            user_id=1,
            message="我最近睡眠不太好",
            profile={"current_stage": "S2"},
        )
        required_keys = ["response", "risk_level", "agents_used"]
        for key in required_keys:
            assert key in result, f"process() 缺少 key: {key}"

    def test_process_response_nonempty(self, agent):
        result = agent.process(
            user_id=1,
            message="帮我制定一个运动计划",
            profile={"current_stage": "S3"},
        )
        assert len(result.get("response", "")) > 0

    def test_process_agents_used_nonempty(self, agent):
        result = agent.process(
            user_id=1,
            message="我的血糖13.5了",
            profile={"current_stage": "S2"},
            device_data={"cgm_value": 13.5},
        )
        assert len(result.get("agents_used", [])) > 0

    def test_normal_message_not_critical(self, agent):
        """普通消息不应触发 critical"""
        result = agent.process(
            user_id=1,
            message="今天天气真好",
            profile={"current_stage": "S3"},
        )
        assert result.get("risk_level") != "critical"


# ═══════════════════════════════════════════════
# Golden 2: Assessment 评估链路
# ═══════════════════════════════════════════════

class TestAssessmentGolden:

    def test_submit_assessment_returns_dict(self, agent):
        if not hasattr(agent, "submit_assessment"):
            pytest.skip("agent 无 submit_assessment()")
        result = agent.submit_assessment(
            user_id=1,
            assessment_data={
                "type": "big5",
                "scores": {"O": 3.5, "C": 4.0, "E": 3.0, "A": 3.5, "N": 2.5},
            },
        )
        assert isinstance(result, dict)
        assert "response" in result


# ═══════════════════════════════════════════════
# Golden 3: Device-Sync 设备同步链路
# ═══════════════════════════════════════════════

class TestDeviceSyncGolden:

    def test_sync_device_data_returns_dict(self, agent):
        if not hasattr(agent, "sync_device_data"):
            pytest.skip("agent 无 sync_device_data()")
        result = agent.sync_device_data(
            user_id=1,
            device_data={"cgm_value": 7.2, "hrv_sdnn": 45, "sleep_hours": 7.5, "steps": 8000},
        )
        assert isinstance(result, dict)
        assert "response" in result

    def test_abnormal_device_data_triggers_findings(self, agent):
        """异常设备数据应产生洞察"""
        result = agent.process(
            user_id=1,
            message="查看我的数据",
            device_data={"cgm_value": 15.0, "hrv_sdnn": 20, "sleep_hours": 4},
            profile={"current_stage": "S3"},
        )
        insights = result.get("insights", [])
        # 至少应有血糖和睡眠的洞察
        assert len(insights) >= 2, f"异常数据仅产生 {len(insights)} 条洞察"
