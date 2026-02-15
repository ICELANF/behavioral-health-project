"""
观察员分层访问控制中间件
契约来源: Sheet③ 访客与入口契约 · A节
实现范围:
  - 免注册游客 vs 注册观察员 两级访问分层
  - 体验版评估限1次 (HF-20快筛)
  - AI体验对话限3轮
  - 转化钩子引导 (注册/升级引导)
"""

from __future__ import annotations
import time
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, Depends
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

# ──────────────────────────────────────────────
# 1. 访问层级定义 (对齐 Sheet③ A节)
# ──────────────────────────────────────────────

class AccessTier(str, Enum):
    """观察员两级访问层:
    - PUBLIC:  免注册游客 — 仅 T1 公开内容
    - REGISTERED: 注册观察员 — T1 深度 + 体验评估 + 3轮AI
    """
    PUBLIC = "public"
    REGISTERED = "registered_observer"


# ──────────────────────────────────────────────
# 2. 公开路由白名单 (无 auth 守卫)
# ──────────────────────────────────────────────

PUBLIC_ROUTE_PREFIXES = [
    # Sheet③: H5公开路由, 无auth守卫
    "/v1/content/public",          # T1 公开科普文章/案例故事
    "/v1/expert-hub",              # 专家中心浏览
    "/v1/coach-directory",         # 教练名录浏览
    "/v1/expert-studio",           # 专家工作室页面(只读)
    "/v1/auth/register",           # 注册端点
    "/v1/auth/login",              # 登录端点
    "/v1/auth/verify-code",        # 验证码验证
    "/v1/health/check",             # 健康检查 (不能用/v1/health, 会匹配/v1/health-data)
    "/docs",                       # API 文档
    "/openapi.json",               # OpenAPI schema
]

# 注册观察员专属路由 (需 auth, 角色≥Observer)
OBSERVER_REGISTERED_ROUTES = [
    "/v1/content/detail",          # T1 深度案例详情
    "/v1/knowledge/search",        # 公开知识库检索
    "/v1/assessment/trial",        # 体验版 HF-20 (限1次)
    "/v1/chat/trial",              # AI 体验对话 (限3轮)
    "/v1/content/bookmark",        # 案例收藏
]

# 成长者+ 才能访问的路由 (角色≥Grower)
GROWER_PLUS_ROUTES_PREFIX = [
    "/v1/assessment/full",         # 完整评估 COM-B/TTM
    "/v1/chat/agent",              # 12 Agent 完整对话
    "/v1/health-data",             # 健康数据管理
    "/v1/micro-action",            # 微行动
    "/v1/challenge",               # 挑战
    "/v1/checkin",                 # 签到
    "/v1/learning",                # 课程学习
    "/v1/leaderboard",             # 排行榜
]


# ──────────────────────────────────────────────
# 3. 体验版限制追踪 (Redis + DB 双层)
# ──────────────────────────────────────────────

class TrialLimitTracker:
    """
    追踪注册观察员的体验版使用次数。
    契约规则:
      - 体验版评估: 限1次 (HF-20快筛)
      - AI体验对话: 限3轮
    
    存储策略:
      - Redis: 快速读取 (TTL=30天, 降级回退DB)
      - DB:    持久化 (observer_trial_usage 表)
    """
    
    TRIAL_ASSESSMENT_LIMIT = 1    # Sheet③: 体验版评估限1次
    TRIAL_CHAT_LIMIT = 3          # Sheet③: AI体验对话限3轮
    REDIS_TTL = 60 * 60 * 24 * 30  # 30天
    
    def __init__(self, redis_client=None, db_session_factory=None):
        self.redis = redis_client
        self.db_session_factory = db_session_factory
    
    async def check_trial_assessment(self, user_id: int) -> dict:
        """检查是否还能做体验版评估"""
        used = await self._get_usage(user_id, "trial_assessment")
        remaining = max(0, self.TRIAL_ASSESSMENT_LIMIT - used)
        return {
            "allowed": remaining > 0,
            "used": used,
            "limit": self.TRIAL_ASSESSMENT_LIMIT,
            "remaining": remaining,
            "upgrade_hint": "注册获取完整报告" if remaining == 0 else None,
        }
    
    async def check_trial_chat(self, user_id: int) -> dict:
        """检查是否还能做AI体验对话"""
        used = await self._get_usage(user_id, "trial_chat_rounds")
        remaining = max(0, self.TRIAL_CHAT_LIMIT - used)
        return {
            "allowed": remaining > 0,
            "used": used,
            "limit": self.TRIAL_CHAT_LIMIT,
            "remaining": remaining,
            "upgrade_hint": "注册解锁完整AI服务" if remaining == 0 else None,
        }
    
    async def consume_trial_assessment(self, user_id: int) -> bool:
        """消耗一次体验评估额度"""
        check = await self.check_trial_assessment(user_id)
        if not check["allowed"]:
            return False
        await self._increment_usage(user_id, "trial_assessment")
        return True
    
    async def consume_trial_chat_round(self, user_id: int) -> bool:
        """消耗一轮AI对话额度"""
        check = await self.check_trial_chat(user_id)
        if not check["allowed"]:
            return False
        await self._increment_usage(user_id, "trial_chat_rounds")
        return True
    
    # ── 存储层 ──
    
    async def _get_usage(self, user_id: int, usage_type: str) -> int:
        """获取使用次数, Redis优先, DB回退"""
        redis_key = f"trial:{user_id}:{usage_type}"
        
        # 尝试 Redis
        if self.redis:
            try:
                val = await self.redis.get(redis_key)
                if val is not None:
                    return int(val)
            except Exception:
                pass  # Redis降级, 回退DB
        
        # 回退 DB
        if self.db_session_factory:
            async with self.db_session_factory() as session:
                from app.models.observer_trial import ObserverTrialUsage
                stmt = select(ObserverTrialUsage.count).where(
                    ObserverTrialUsage.user_id == user_id,
                    ObserverTrialUsage.usage_type == usage_type,
                )
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                count = row if row is not None else 0
                
                # 回填 Redis
                if self.redis:
                    try:
                        await self.redis.setex(redis_key, self.REDIS_TTL, str(count))
                    except Exception:
                        pass
                return count
        
        return 0
    
    async def _increment_usage(self, user_id: int, usage_type: str) -> None:
        """递增使用次数"""
        redis_key = f"trial:{user_id}:{usage_type}"
        
        # DB 持久化
        if self.db_session_factory:
            async with self.db_session_factory() as session:
                from app.models.observer_trial import ObserverTrialUsage
                stmt = select(ObserverTrialUsage).where(
                    ObserverTrialUsage.user_id == user_id,
                    ObserverTrialUsage.usage_type == usage_type,
                )
                result = await session.execute(stmt)
                record = result.scalar_one_or_none()
                if record:
                    record.count += 1
                    record.last_used_at = datetime.utcnow()
                else:
                    session.add(ObserverTrialUsage(
                        user_id=user_id,
                        usage_type=usage_type,
                        count=1,
                        last_used_at=datetime.utcnow(),
                    ))
                await session.commit()
        
        # Redis 同步
        if self.redis:
            try:
                await self.redis.incr(redis_key)
                await self.redis.expire(redis_key, self.REDIS_TTL)
            except Exception:
                pass


# ──────────────────────────────────────────────
# 4. 核心访问控制中间件
# ──────────────────────────────────────────────

class ObserverTieringMiddleware:
    """
    观察员分层访问控制中间件。
    
    访问矩阵 (对齐 Sheet⑤ 服务权益):
    ┌────────────────┬────────┬──────────┬────────┐
    │ 资源           │ 免注册 │ 注册观察 │ 成长者+│
    ├────────────────┼────────┼──────────┼────────┤
    │ T1公开科普      │  ✅    │   ✅     │  ✅   │
    │ 专家中心浏览    │  ✅    │   ✅     │  ✅   │
    │ 深度案例详情    │  ❌    │   ✅     │  ✅   │
    │ 公开知识库检索  │  ❌    │   ✅     │  ✅   │
    │ 体验版HF-20    │  ❌    │ 🔓限1次  │  ✅   │
    │ AI体验对话      │  ❌    │ 🔓限3轮  │  ✅   │
    │ 完整评估/AI对话 │  ❌    │   ❌     │  ✅   │
    └────────────────┴────────┴──────────┴────────┘
    """
    
    # 角色层级 (对齐 Sheet① role_level)
    ROLE_LEVELS = {
        "admin": 99,
        "supervisor": 98,  # 特殊
        "observer": 1,
        "grower": 2,
        "sharer": 3,
        "coach": 4,
        "senior_coach": 5,
        "master": 6,
    }
    
    def __init__(self, trial_tracker: TrialLimitTracker):
        self.trial_tracker = trial_tracker
    
    def is_public_route(self, path: str) -> bool:
        """判断是否为公开路由(无需认证)"""
        return any(path.startswith(prefix) for prefix in PUBLIC_ROUTE_PREFIXES)
    
    def get_role_level(self, user_role: Optional[str]) -> int:
        """获取角色等级"""
        if not user_role:
            return 0  # 未认证=公共游客
        return self.ROLE_LEVELS.get(user_role.lower(), 0)
    
    async def check_access(self, request: Request, user=None) -> dict:
        """
        核心访问检查逻辑。
        
        Returns:
            {
                "allowed": bool,
                "tier": AccessTier,
                "reason": str | None,
                "upgrade_action": str | None,   # 转化钩子
                "trial_status": dict | None,     # 体验版状态
            }
        """
        path = request.url.path
        
        # 1. 公开路由 → 放行
        if self.is_public_route(path):
            return {
                "allowed": True,
                "tier": AccessTier.PUBLIC,
                "reason": None,
                "upgrade_action": None,
                "trial_status": None,
            }
        
        # 2. 无认证用户 → 引导注册
        if user is None:
            return {
                "allowed": False,
                "tier": AccessTier.PUBLIC,
                "reason": "此功能需要注册账号",
                "upgrade_action": "register",
                "trial_status": None,
            }
        
        role_level = self.get_role_level(getattr(user, "role", None))
        
        # 3. 成长者+路由检查
        is_grower_route = any(
            path.startswith(prefix) for prefix in GROWER_PLUS_ROUTES_PREFIX
        )
        if is_grower_route and role_level < 2:
            return {
                "allowed": False,
                "tier": AccessTier.REGISTERED,
                "reason": "此功能需要成长者及以上角色",
                "upgrade_action": "become_grower",
                "trial_status": None,
            }
        
        # 4. 体验版评估限制
        if path.startswith("/v1/assessment/trial"):
            if role_level >= 2:
                # 成长者+不受限
                return {"allowed": True, "tier": AccessTier.REGISTERED,
                        "reason": None, "upgrade_action": None, "trial_status": None}
            
            trial_status = await self.trial_tracker.check_trial_assessment(user.id)
            if not trial_status["allowed"]:
                return {
                    "allowed": False,
                    "tier": AccessTier.REGISTERED,
                    "reason": "体验版评估已使用完毕",
                    "upgrade_action": "become_grower",
                    "trial_status": trial_status,
                }
            return {
                "allowed": True,
                "tier": AccessTier.REGISTERED,
                "reason": None,
                "upgrade_action": None,
                "trial_status": trial_status,
            }
        
        # 5. AI体验对话限制
        if path.startswith("/v1/chat/trial"):
            if role_level >= 2:
                return {"allowed": True, "tier": AccessTier.REGISTERED,
                        "reason": None, "upgrade_action": None, "trial_status": None}
            
            trial_status = await self.trial_tracker.check_trial_chat(user.id)
            if not trial_status["allowed"]:
                return {
                    "allowed": False,
                    "tier": AccessTier.REGISTERED,
                    "reason": "AI体验对话已达上限",
                    "upgrade_action": "become_grower",
                    "trial_status": trial_status,
                }
            return {
                "allowed": True,
                "tier": AccessTier.REGISTERED,
                "reason": None,
                "upgrade_action": None,
                "trial_status": trial_status,
            }
        
        # 6. 注册观察员专属路由 → 放行
        is_observer_route = any(
            path.startswith(prefix) for prefix in OBSERVER_REGISTERED_ROUTES
        )
        if is_observer_route:
            return {
                "allowed": True,
                "tier": AccessTier.REGISTERED,
                "reason": None,
                "upgrade_action": None,
                "trial_status": None,
            }
        
        # 7. 其他路由 → 标准RBAC放行
        return {
            "allowed": True,
            "tier": AccessTier.REGISTERED if role_level == 1 else AccessTier.PUBLIC,
            "reason": None,
            "upgrade_action": None,
            "trial_status": None,
        }


# ──────────────────────────────────────────────
# 5. FastAPI 依赖注入
# ──────────────────────────────────────────────

async def require_observer_access(request: Request):
    """
    FastAPI Depends 依赖: 观察员分层访问检查。
    
    用法:
        @router.get("/v1/assessment/trial")
        async def trial_assessment(access=Depends(require_observer_access)):
            ...
    """
    from app.core.deps import get_current_user_optional, get_trial_tracker
    
    user = await get_current_user_optional(request)
    tracker = get_trial_tracker()
    middleware = ObserverTieringMiddleware(tracker)
    
    result = await middleware.check_access(request, user)
    
    if not result["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "access_denied",
                "message": result["reason"],
                "upgrade_action": result["upgrade_action"],
                "trial_status": result.get("trial_status"),
            }
        )
    
    return result
