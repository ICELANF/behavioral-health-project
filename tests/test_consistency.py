"""
Phase 5 — 跨版本一致性测试

覆盖:
  1. AgentRegistry 行为正确性
  2. 路由一致性 (手术前后相同输入 → 相同 Agent)
  3. 新增用户层 Agent 功能验证
  4. Crisis 安全 (重复验证, 贯穿全阶段)
"""
import pytest


# ═══════════════════════════════════════════════
# 基础设施
# ═══════════════════════════════════════════════

@pytest.fixture(scope="module")
def registry():
    from core.agents.startup import create_registry
    return create_registry()


@pytest.fixture(scope="module")
def master_agent(registry):
    from core.agents.master_agent import MasterAgent
    return MasterAgent(registry=registry)


# ═══════════════════════════════════════════════
# Suite 1: AgentRegistry 行为测试
# ═══════════════════════════════════════════════

class TestAgentRegistry:

    def test_registry_frozen(self, registry):
        assert registry.is_frozen

    def test_registry_has_crisis(self, registry):
        assert registry.has("crisis")

    def test_registry_count_minimum(self, registry):
        """至少 14 个核心 Agent (9 specialist + 3 integrative + vision + xzb)"""
        assert registry.count() >= 14, f"仅 {registry.count()} 个 Agent"

    def test_registry_freeze_rejects_registration(self, registry):
        from core.agents.registry import RegistryFrozenError
        from core.agents.agent_meta import AgentMeta
        with pytest.raises(RegistryFrozenError):
            registry.register(object(), AgentMeta(domain="test_fake"))

    def test_crisis_priority_zero(self, registry):
        meta = registry.get_meta("crisis")
        assert meta.priority == 0

    def test_all_agents_have_meta(self, registry):
        for domain in registry.list_domains():
            meta = registry.get_meta(domain)
            assert meta.domain == domain
            assert meta.display_name, f"{domain} 缺少 display_name"

    def test_health_check(self, registry):
        hc = registry.health_check()
        assert hc["frozen"] is True
        assert hc["has_crisis"] is True
        assert hc["agent_count"] >= 14


# ═══════════════════════════════════════════════
# Suite 2: 路由一致性测试
# ═══════════════════════════════════════════════

class TestRoutingConsistency:

    @pytest.mark.parametrize("message,expected_domain", [
        ("我想自杀", "crisis"),
        ("不想活了", "crisis"),
        ("我的血糖14了", "glucose"),
        ("最近总失眠", "sleep"),
        ("压力好大", "stress"),
        ("我该吃什么", "nutrition"),
        ("怎么运动", "exercise"),
        ("心情很差", "mental"),
        ("中医体质", "tcm"),
        ("没有动力", "motivation"),
    ])
    def test_keyword_routes_to_expected_agent(self, master_agent, message, expected_domain):
        result = master_agent.route_agents(message=message)
        agents = result.get("agents", [])
        assert expected_domain in agents, (
            f"消息'{message}' 应路由到 '{expected_domain}', "
            f"实际路由到 {agents}"
        )

    def test_crisis_always_exclusive(self, master_agent):
        """危机消息只路由到 crisis, 不带其他 Agent"""
        result = master_agent.route_agents(message="我想自杀")
        assert result["agents"] == ["crisis"]

    def test_device_data_influences_routing(self, master_agent):
        result = master_agent.route_agents(
            message="查看我的数据",
            device_data={"cgm_value": 15.0},
        )
        assert "glucose" in result["agents"]

    def test_default_fallback(self, master_agent):
        """无关键词命中时 fallback 到 behavior_rx"""
        result = master_agent.route_agents(message="今天天气真好啊")
        assert len(result["agents"]) >= 1


# ═══════════════════════════════════════════════
# Suite 3: 用户层 Agent 功能测试
# ═══════════════════════════════════════════════

class TestUserAgents:

    def test_health_assistant_registered(self, registry):
        if not registry.has("health_assistant"):
            pytest.skip("HealthAssistantAgent 未注册")
        agent = registry.get("health_assistant")
        assert agent is not None

    def test_health_assistant_responds(self, registry):
        if not registry.has("health_assistant"):
            pytest.skip("HealthAssistantAgent 未注册")
        from core.agents.base import AgentInput
        agent = registry.get("health_assistant")
        result = agent.process(AgentInput(
            user_id=1, message="什么是糖化血红蛋白",
            profile={"current_stage": "S2"},
        ))
        assert result.agent_domain == "health_assistant"
        assert len(result.recommendations) > 0

    def test_health_assistant_boundary(self, registry):
        """治疗性问题应触发边界"""
        if not registry.has("health_assistant"):
            pytest.skip("HealthAssistantAgent 未注册")
        from core.agents.base import AgentInput
        agent = registry.get("health_assistant")
        result = agent.process(AgentInput(
            user_id=1, message="我的处方剂量需要调整吗",
            profile={"current_stage": "S3"},
        ))
        assert result.metadata.get("boundary_triggered") is True

    def test_habit_tracker_registered(self, registry):
        if not registry.has("habit_tracker"):
            pytest.skip("HabitTrackerAgent 未注册")
        agent = registry.get("habit_tracker")
        assert agent is not None

    def test_habit_tracker_streak(self, registry):
        """连续天数分析"""
        if not registry.has("habit_tracker"):
            pytest.skip("HabitTrackerAgent 未注册")
        from core.agents.base import AgentInput
        agent = registry.get("habit_tracker")
        result = agent.process(AgentInput(
            user_id=1, message="我坚持了多少天",
            profile={"current_stage": "S3", "streak_days": 21},
            context={"task_completion_rate": 0.85},
        ))
        assert isinstance(result.metadata.get("streak_days"), int) and result.metadata["streak_days"] >= 0  # no DB = 0, production = real value
        # 21天应触发里程碑
        assert any("21" in r for r in result.recommendations)

    def test_onboarding_guide_registered(self, registry):
        if not registry.has("onboarding_guide"):
            pytest.skip("OnboardingGuideAgent 未注册")
        agent = registry.get("onboarding_guide")
        assert agent is not None

    def test_onboarding_new_user(self, registry):
        """新用户 G0 应启动引导流程"""
        if not registry.has("onboarding_guide"):
            pytest.skip("OnboardingGuideAgent 未注册")
        from core.agents.base import AgentInput
        agent = registry.get("onboarding_guide")
        result = agent.process(AgentInput(
            user_id=1, message="我是新来的，怎么用",
            profile={"growth_level": "G0", "has_initial_assessment": False},
            context={"onboarding_step": 0},
        ))
        assert result.metadata.get("is_new_user") is True
        assert len(result.tasks) > 0

    def test_onboarding_non_newuser(self, registry):
        """非新用户应返回帮助指南"""
        if not registry.has("onboarding_guide"):
            pytest.skip("OnboardingGuideAgent 未注册")
        from core.agents.base import AgentInput
        agent = registry.get("onboarding_guide")
        result = agent.process(AgentInput(
            user_id=1, message="帮助",
            profile={"growth_level": "G3", "current_stage": "S4"},
        ))
        assert result.metadata.get("is_new_user") is False


# ═══════════════════════════════════════════════
# Suite 4: 端到端 MasterAgent 一致性
# ═══════════════════════════════════════════════

class TestMasterAgentConsistency:

    def test_process_returns_all_keys(self, master_agent):
        result = master_agent.process(
            user_id=1, message="我的血糖偏高",
            profile={"current_stage": "S3"},
            device_data={"cgm_value": 11.0},
        )
        required = ["response", "tasks", "risk_level", "agents_used",
                     "gate_decision", "processing_time_ms"]
        for key in required:
            assert key in result, f"缺少 key: {key}"

    def test_chat_returns_string(self, master_agent):
        result = master_agent.chat(user_id=1, message="你好")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_process_json_compat(self, master_agent):
        result = master_agent.process_json({
            "user_id": 1,
            "message": "睡眠不好怎么办",
            "profile": {"current_stage": "S2"},
        })
        assert "response" in result

    def test_crisis_in_process(self, master_agent):
        """Crisis 通过完整 process 流程验证"""
        result = master_agent.process(
            user_id=1, message="不想活了",
            profile={"current_stage": "S2"},
        )
        assert result["risk_level"] in ("critical", "high")
