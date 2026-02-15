"""
test_master_agent_unified.py — 统一 MasterAgent 合并验证测试

覆盖:
  1. v6 核心功能 (process 9步流水线)
  2. v0 兼容 API (chat, process_json, sync_device_data...)
  3. 单例管理 (get_master_agent / get_agent_master)
  4. 降级保护 (v0 不可用时优雅降级)
  5. 类型桥接 (v0 UserInput → v6 dict)
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime

try:
    from core.master_agent_unified import (
        UnifiedMasterAgent, get_master_agent, get_agent_master, MasterAgent,
    )
    HAS_UNIFIED = True
except ImportError:
    HAS_UNIFIED = False

pytestmark = pytest.mark.skipif(not HAS_UNIFIED, reason="master_agent_unified not importable")


# =====================================================================
# 1. 初始化
# =====================================================================

class TestUnifiedInit:

    def test_class_exists(self):
        """UnifiedMasterAgent 类可导入"""
        assert UnifiedMasterAgent is not None

    def test_alias_matches(self):
        """MasterAgent = UnifiedMasterAgent"""
        assert MasterAgent is UnifiedMasterAgent

    def test_inherits_v6(self):
        """继承 v6 MasterAgent"""
        from core.agents.master_agent import MasterAgent as V6
        assert issubclass(UnifiedMasterAgent, V6)

    def test_init_with_db(self, db):
        """带 db_session 初始化"""
        agent = UnifiedMasterAgent(db_session=db)
        assert agent is not None
        assert hasattr(agent, "router")
        assert hasattr(agent, "coordinator")
        assert hasattr(agent, "policy_gate")

    def test_init_without_db(self):
        """无 db_session 初始化 (硬编码 Agent)"""
        agent = UnifiedMasterAgent()
        assert agent is not None
        assert len(agent._agents) == 12


# =====================================================================
# 2. v6 核心 — process()
# =====================================================================

class TestV6Process:

    def test_process_returns_dict(self):
        """process() 返回 dict"""
        agent = UnifiedMasterAgent()
        result = agent.process(
            user_id=1, message="你好",
            profile={"current_stage": "S0"},
        )
        assert isinstance(result, dict)
        assert "response" in result
        assert "agents_used" in result
        assert "processing_time_ms" in result

    def test_process_safety_integration(self):
        """process() 包含安全管线结果"""
        agent = UnifiedMasterAgent()
        result = agent.process(
            user_id=1, message="测试消息",
            profile={},
        )
        # safety 字段应存在 (即使为空)
        assert isinstance(result, dict)

    def test_process_with_device_data(self):
        """process() 带设备数据"""
        agent = UnifiedMasterAgent()
        result = agent.process(
            user_id=1, message="我的血糖怎么样",
            profile={},
            device_data={"cgm_value": 7.2, "hrv_sdnn": 45},
        )
        assert isinstance(result, dict)

    def test_process_with_tenant_ctx(self):
        """process() 带租户上下文"""
        agent = UnifiedMasterAgent()
        result = agent.process(
            user_id=1, message="测试",
            profile={},
            tenant_ctx={"tenant_id": "test_tenant"},
        )
        assert isinstance(result, dict)


# =====================================================================
# 3. v0 兼容 API
# =====================================================================

class TestV0CompatAPI:

    def test_chat_returns_str(self):
        """chat() 返回字符串"""
        agent = UnifiedMasterAgent()
        result = agent.chat(user_id=1, message="你好教练")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_chat_with_efficacy(self):
        """chat() 接受 efficacy_score"""
        agent = UnifiedMasterAgent()
        result = agent.chat(user_id=1, message="我今天状态不好", efficacy_score=30.0)
        assert isinstance(result, str)

    def test_process_json(self):
        """process_json() JSON入口"""
        agent = UnifiedMasterAgent()
        result = agent.process_json({
            "user_id": "test_user",
            "message": "你好",
            "profile": {},
        })
        assert isinstance(result, dict)
        assert "response" in result

    def test_process_json_alt_fields(self):
        """process_json() 兼容 content/query/text 字段"""
        agent = UnifiedMasterAgent()
        for key in ("content", "query", "text"):
            result = agent.process_json({
                "user_id": "test",
                key: "测试消息",
            })
            assert isinstance(result, dict)

    def test_process_with_pipeline(self):
        """process_with_pipeline() 返回 (result, summary) 元组"""
        agent = UnifiedMasterAgent()
        result, summary = agent.process_with_pipeline({
            "user_id": "test",
            "message": "测试",
        })
        assert isinstance(result, dict)
        assert isinstance(summary, dict)
        assert "steps_completed" in summary
        assert summary["steps_completed"] == 9

    def test_route_agents(self):
        """route_agents() 显式路由"""
        agent = UnifiedMasterAgent()
        result = agent.route_agents(
            message="血糖偏高",
            profile={"risk_level": "high"},
        )
        assert isinstance(result, dict)
        assert "agents" in result
        assert "primary" in result
        assert isinstance(result["agents"], list)

    def test_coordinate(self):
        """coordinate() 协调结果"""
        agent = UnifiedMasterAgent()
        # 空列表不应崩溃
        result = agent.coordinate([])
        assert isinstance(result, dict)

    def test_sync_device_data(self):
        """sync_device_data() 设备同步"""
        agent = UnifiedMasterAgent()
        result = agent.sync_device_data(
            user_id=1,
            device_data={"cgm_value": 6.5, "steps": 8000},
        )
        assert isinstance(result, dict)

    def test_submit_assessment(self):
        """submit_assessment() 评估提交"""
        agent = UnifiedMasterAgent()
        result = agent.submit_assessment(
            user_id=1,
            assessment_data={"type": "baps_big5", "scores": {}},
        )
        assert isinstance(result, dict)

    def test_report_task_completion(self):
        """report_task_completion() 任务上报"""
        agent = UnifiedMasterAgent()
        result = agent.report_task_completion(
            user_id=1, task_id="task_001",
            completion_data={"status": "completed"},
        )
        assert isinstance(result, dict)


# =====================================================================
# 4. v0 UserInput 桥接
# =====================================================================

class TestV0InputBridge:

    def test_process_with_user_input_object(self):
        """process(user_input=UserInput(...)) v0 风格调用"""
        try:
            from core.master_agent_v0 import UserInput, InputType
        except ImportError:
            pytest.skip("v0 UserInput not available")

        agent = UnifiedMasterAgent()
        ui = UserInput(
            user_id="test_user",
            input_type=InputType.TEXT,
            content="你好",
            efficacy_score=65.0,
        )
        result = agent.process(user_input=ui)
        assert isinstance(result, dict)
        assert "response" in result

    def test_v0_device_data_conversion(self):
        """v0 DeviceData → v6 dict 转换"""
        agent = UnifiedMasterAgent()

        # Mock v0 DeviceData with cgm
        class MockCGM:
            current_glucose = 7.5
            trend = "rising"
            time_in_range_percent = 65.0

        class MockDevice:
            cgm = MockCGM()
            hrv = None
            sleep = None
            activity = None

        result = agent._convert_v0_device_data_obj(MockDevice())
        assert result["cgm_value"] == 7.5
        assert result["cgm_trend"] == "rising"

    def test_dict_device_data_passthrough(self):
        """dict 设备数据直接透传"""
        agent = UnifiedMasterAgent()
        dd = {"cgm_value": 6.0, "steps": 5000}
        result = agent._convert_v0_device_data_obj(dd)
        assert result is dd


# =====================================================================
# 5. 单例管理
# =====================================================================

class TestSingletonManagement:

    def test_get_master_agent(self):
        """get_master_agent() 返回 UnifiedMasterAgent"""
        import core.master_agent_unified as mod
        mod._unified_agent = None  # 重置
        agent = get_master_agent()
        assert isinstance(agent, UnifiedMasterAgent)

    def test_get_master_agent_singleton(self):
        """get_master_agent() 返回同一实例"""
        import core.master_agent_unified as mod
        mod._unified_agent = None
        a1 = get_master_agent()
        a2 = get_master_agent()
        assert a1 is a2

    def test_get_agent_master_alias(self):
        """get_agent_master() 是 get_master_agent() 的别名"""
        import core.master_agent_unified as mod
        mod._unified_agent = None
        a1 = get_master_agent()
        a2 = get_agent_master()
        assert a1 is a2


# =====================================================================
# 6. 降级保护
# =====================================================================

class TestGracefulDegradation:

    def test_chat_error_returns_fallback(self):
        """chat() 异常时返回降级消息"""
        agent = UnifiedMasterAgent()
        # 模拟 process 异常
        with patch.object(agent, "process", side_effect=Exception("test error")):
            result = agent.chat(user_id=1, message="test")
            assert isinstance(result, str)
            assert "抱歉" in result

    def test_daily_push_error_fallback(self):
        """get_daily_push_content() 异常降级"""
        agent = UnifiedMasterAgent()
        # 不加载 v0
        agent._v0_instance = MagicMock()
        agent._v0_instance.get_daily_push_content.side_effect = Exception("v0 error")
        result = agent.get_daily_push_content(user_id=1)
        assert isinstance(result, dict)
        assert "message" in result

    def test_action_plan_fallback(self):
        """create_action_plan() 降级返回简化计划"""
        agent = UnifiedMasterAgent()
        # 模拟 v0 不可用
        agent._v0_instance = MagicMock()
        agent._v0_instance.create_action_plan.side_effect = Exception("v0 error")
        result = agent.create_action_plan(stage="contemplation")
        assert isinstance(result, dict)
        assert result.get("fallback") is True

    def test_daily_briefing_fallback(self):
        """generate_daily_briefing() 降级返回基础简报"""
        agent = UnifiedMasterAgent()
        agent._v0_instance = MagicMock()
        agent._v0_instance.generate_daily_briefing.side_effect = Exception("v0 error")
        result = agent.generate_daily_briefing(user_id=1)
        assert isinstance(result, dict)
        assert result.get("fallback") is True
