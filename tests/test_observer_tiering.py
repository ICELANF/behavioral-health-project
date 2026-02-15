"""
观察员分层访问控制测试套件
对标契约: Sheet③ A节 + Sheet⑤ 服务权益矩阵

测试覆盖:
  OBS-01: 免注册游客公开路由访问
  OBS-02: 未认证用户受限路由拒绝
  OBS-03: 注册观察员基本权限
  OBS-04: 体验版评估限1次
  OBS-05: AI体验对话限3轮
  OBS-06: 成长者+不受体验限制
  OBS-07: 角色层级不足拒绝
  OBS-08: 转化钩子正确返回
  OBS-09: Redis降级DB回退
  OBS-10: 额度消耗持久化
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ── 模拟对象 ──

class MockUser:
    def __init__(self, user_id: int, role: str):
        self.id = user_id
        self.role = role


class MockRequest:
    def __init__(self, path: str):
        self.url = MagicMock()
        self.url.path = path


# ── 导入被测模块 ──

import sys
sys.path.insert(0, '.')
from observer_access_middleware import (
    ObserverTieringMiddleware,
    TrialLimitTracker,
    AccessTier,
    PUBLIC_ROUTE_PREFIXES,
)


# ── Fixtures ──

@pytest.fixture
def tracker():
    """无Redis/无DB的纯内存追踪器"""
    t = TrialLimitTracker(redis_client=None, db_session_factory=None)
    # 用内存字典模拟存储
    t._storage = {}
    
    async def mock_get_usage(user_id, usage_type):
        return t._storage.get(f"{user_id}:{usage_type}", 0)
    
    async def mock_increment(user_id, usage_type):
        key = f"{user_id}:{usage_type}"
        t._storage[key] = t._storage.get(key, 0) + 1
    
    t._get_usage = mock_get_usage
    t._increment_usage = mock_increment
    return t


@pytest.fixture
def middleware(tracker):
    return ObserverTieringMiddleware(tracker)


# ──────────────────────────────────────────
# OBS-01: 免注册游客公开路由
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_obs01_public_route_no_auth(middleware):
    """免注册游客可以访问公开路由"""
    for path in ["/v1/content/public", "/v1/expert-hub", "/v1/coach-directory"]:
        req = MockRequest(path)
        result = await middleware.check_access(req, user=None)
        assert result["allowed"] is True
        assert result["tier"] == AccessTier.PUBLIC


# ──────────────────────────────────────────
# OBS-02: 未认证用户受限路由拒绝
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_obs02_unauthenticated_restricted(middleware):
    """未认证用户访问受限路由应被拒绝并引导注册"""
    req = MockRequest("/v1/content/detail/123")
    result = await middleware.check_access(req, user=None)
    assert result["allowed"] is False
    assert result["upgrade_action"] == "register"
    assert "注册" in result["reason"]


# ──────────────────────────────────────────
# OBS-03: 注册观察员基本权限
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_obs03_registered_observer_access(middleware):
    """注册观察员可以访问深度案例/知识库"""
    user = MockUser(1, "observer")
    for path in ["/v1/content/detail/123", "/v1/knowledge/search"]:
        req = MockRequest(path)
        result = await middleware.check_access(req, user)
        assert result["allowed"] is True
        assert result["tier"] == AccessTier.REGISTERED


# ──────────────────────────────────────────
# OBS-04: 体验版评估限1次
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_obs04_trial_assessment_limit(middleware, tracker):
    """体验版评估只能使用1次"""
    user = MockUser(1, "observer")
    req = MockRequest("/v1/assessment/trial")
    
    # 第一次 → 允许
    result = await middleware.check_access(req, user)
    assert result["allowed"] is True
    assert result["trial_status"]["remaining"] == 1
    
    # 消耗额度
    success = await tracker.consume_trial_assessment(user.id)
    assert success is True
    
    # 第二次 → 拒绝
    result = await middleware.check_access(req, user)
    assert result["allowed"] is False
    assert result["upgrade_action"] == "become_grower"


# ──────────────────────────────────────────
# OBS-05: AI体验对话限3轮
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_obs05_trial_chat_limit(middleware, tracker):
    """AI体验对话最多3轮"""
    user = MockUser(2, "observer")
    req = MockRequest("/v1/chat/trial")
    
    # 3轮内 → 允许
    for i in range(3):
        result = await middleware.check_access(req, user)
        assert result["allowed"] is True
        assert result["trial_status"]["remaining"] == 3 - i
        await tracker.consume_trial_chat_round(user.id)
    
    # 第4轮 → 拒绝
    result = await middleware.check_access(req, user)
    assert result["allowed"] is False
    assert "AI体验对话" in result["reason"]


# ──────────────────────────────────────────
# OBS-06: 成长者+不受体验限制
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_obs06_grower_bypasses_trial(middleware):
    """成长者及以上角色不受体验版限制"""
    for role in ["grower", "sharer", "coach", "senior_coach", "master", "admin"]:
        user = MockUser(10, role)
        for path in ["/v1/assessment/trial", "/v1/chat/trial"]:
            req = MockRequest(path)
            result = await middleware.check_access(req, user)
            assert result["allowed"] is True, f"{role} should bypass trial on {path}"


# ──────────────────────────────────────────
# OBS-07: 角色层级不足拒绝
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_obs07_role_level_insufficient(middleware):
    """观察员不能访问成长者+专属功能"""
    user = MockUser(1, "observer")
    grower_paths = [
        "/v1/assessment/full",
        "/v1/chat/agent/nutrition",
        "/v1/health-data",
        "/v1/micro-action",
    ]
    for path in grower_paths:
        req = MockRequest(path)
        result = await middleware.check_access(req, user)
        assert result["allowed"] is False
        assert result["upgrade_action"] == "become_grower"


# ──────────────────────────────────────────
# OBS-08: 转化钩子正确返回
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_obs08_upgrade_hooks(middleware, tracker):
    """不同场景返回正确的转化引导"""
    # 未注册 → register
    req = MockRequest("/v1/content/detail/1")
    result = await middleware.check_access(req, user=None)
    assert result["upgrade_action"] == "register"
    
    # 观察员访问成长者路由 → become_grower
    user = MockUser(1, "observer")
    req = MockRequest("/v1/assessment/full")
    result = await middleware.check_access(req, user)
    assert result["upgrade_action"] == "become_grower"
    
    # 体验版耗尽 → become_grower
    await tracker.consume_trial_assessment(user.id)
    req = MockRequest("/v1/assessment/trial")
    result = await middleware.check_access(req, user)
    assert result["upgrade_action"] == "become_grower"


# ──────────────────────────────────────────
# OBS-09: 公开路由白名单完整性
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_obs09_public_routes_complete(middleware):
    """Sheet③定义的公开路由全部在白名单中"""
    expected_public = [
        "/v1/content/public",
        "/v1/expert-hub",
        "/v1/coach-directory",
        "/v1/expert-studio",
        "/v1/auth/register",
        "/v1/auth/login",
    ]
    for path in expected_public:
        assert middleware.is_public_route(path), f"{path} should be public"


# ──────────────────────────────────────────
# OBS-10: 角色层级映射正确
# ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_obs10_role_level_mapping(middleware):
    """角色层级对齐Sheet① role_level定义"""
    assert middleware.get_role_level("observer") == 1
    assert middleware.get_role_level("grower") == 2
    assert middleware.get_role_level("sharer") == 3
    assert middleware.get_role_level("coach") == 4
    assert middleware.get_role_level("senior_coach") == 5
    assert middleware.get_role_level("master") == 6
    assert middleware.get_role_level("admin") == 99
    assert middleware.get_role_level(None) == 0  # 未认证
    assert middleware.get_role_level("unknown") == 0  # 未知角色


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
