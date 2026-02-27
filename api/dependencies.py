"""
API依赖项
API Dependencies

提供API端点的通用依赖项，如认证、授权等
"""
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from loguru import logger

from core.database import get_db
from core.models import User, UserRole
from core.auth import verify_token_with_blacklist

# OAuth2密码模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    可选认证 — 有 token 则返回 User，无 token 或无效则返回 None。
    用于公开浏览但登录用户可获得增强体验的端点。
    """
    if not token:
        return None
    try:
        payload = verify_token_with_blacklist(token, "access")
        if payload is None:
            return None
        user_id = payload.get("user_id") or payload.get("sub")
        if user_id is None:
            return None
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user and user.is_active:
            return user
        return None
    except (JWTError, Exception):
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前认证用户

    从JWT token中解析用户信息并验证

    Args:
        token: JWT access token
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 验证Token（含黑名单检查）
        payload = verify_token_with_blacklist(token, "access")
        if payload is None:
            raise credentials_exception

        # 获取用户ID (兼容 V1 user_id 和 V3 sub)
        user_id = payload.get("user_id") or payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)

        # 从数据库获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用"
            )

        return user

    except JWTError:
        raise credentials_exception
    except Exception as e:
        logger.error(f"获取当前用户失败: {str(e)}")
        raise credentials_exception


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    要求管理员权限

    Args:
        current_user: 当前用户

    Returns:
        User: 管理员用户

    Raises:
        HTTPException: 非管理员用户
    """
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_coach_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    要求教练或管理员权限

    Args:
        current_user: 当前用户

    Returns:
        User: 教练或管理员用户

    Raises:
        HTTPException: 非教练/管理员用户
    """
    if current_user.role.value not in ["coach", "supervisor", "promoter", "master", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教练或管理员权限"
        )
    return current_user


def require_roles(allowed_roles: List[UserRole]):
    """
    角色白名单依赖工厂 — 返回 Depends 可用的函数

    用法: current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.COACH]))
    """
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(r.name for r in allowed_roles)}"
            )
        return current_user
    return _checker


def resolve_tenant_ctx(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Optional[dict]:
    """
    解析当前用户的租户路由上下文。
    1. 用户是专家(ExpertTenant.expert_user_id) → 自己的 tenant_id
    2. 用户是租户客户(TenantClient active) → 所属 tenant_id
    3. 无关联 → None (使用平台默认)
    """
    try:
        from core.models import ExpertTenant, TenantClient
        from core.agent_template_service import get_tenant_routing_context

        # 1. 用户是专家 → 自己的 tenant
        tenant = db.query(ExpertTenant).filter(
            ExpertTenant.expert_user_id == current_user.id,
        ).first()
        if tenant:
            return get_tenant_routing_context(tenant.id, db)

        # 2. 用户是租户客户
        client = db.query(TenantClient).filter(
            TenantClient.user_id == current_user.id,
            TenantClient.status == "active",
        ).first()
        if client:
            ctx = get_tenant_routing_context(client.tenant_id, db)
            # 注入 XZB 行智诊疗专家绑定 (如租户专家有 XZB 画像)
            ctx = _inject_xzb_context(ctx, client.tenant_id, db)
            return ctx

        # 3. 普通用户 — 检查直接 XZB 专家绑定
        xzb_expert_id = getattr(current_user, "xzb_expert_id", None)
        if xzb_expert_id:
            return {"xzb_expert_id": str(xzb_expert_id)}

        return None
    except Exception as e:
        logger.warning("resolve_tenant_ctx 失败 (降级到平台默认): %s", e)
        return None


def _inject_xzb_context(ctx: Optional[dict], tenant_id, db: Session) -> dict:
    """将租户专家的 XZB 画像注入路由上下文"""
    ctx = ctx or {}
    try:
        from core.models import ExpertTenant
        tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
        if tenant:
            expert_user = db.query(User).filter(User.id == tenant.expert_user_id).first()
            xzb_id = getattr(expert_user, "xzb_expert_id", None) if expert_user else None
            if xzb_id:
                ctx["xzb_expert_id"] = str(xzb_id)
    except Exception as e:
        logger.debug("_inject_xzb_context: %s", e)
    return ctx


# ══════════════════════════════════════════════
# V3 Dependencies (merged from bhp_v3)
# ══════════════════════════════════════════════

try:
    from core.llm.client import LLMClient
    from core.llm.router import LLMRouter
    from core.llm.coach_agent import CoachAgent
    from core.rag.vector_store import QdrantStore
    from core.rag.pipeline import RAGPipeline, RAGConfig
    from core.rag.knowledge_loader import KnowledgeLoader
    from core.diagnostic_pipeline import DiagnosticPipeline
    from functools import lru_cache as _lru_cache
    import os as _os

    @_lru_cache()
    def get_llm_client() -> LLMClient:
        return LLMClient()

    @_lru_cache()
    def get_llm_router() -> LLMRouter:
        return LLMRouter(get_llm_client())

    @_lru_cache()
    def get_qdrant_store() -> QdrantStore:
        url = _os.environ.get("QDRANT_URL", "http://qdrant:6333")
        return QdrantStore(base_url=url)

    @_lru_cache()
    def get_rag_pipeline() -> RAGPipeline:
        return RAGPipeline(get_llm_client(), get_llm_router(), get_qdrant_store(), RAGConfig())

    @_lru_cache()
    def get_coach_agent() -> CoachAgent:
        return CoachAgent(llm_client=get_llm_client(), router=get_llm_router(), rag_pipeline=get_rag_pipeline())

    @_lru_cache()
    def get_knowledge_loader() -> KnowledgeLoader:
        return KnowledgeLoader(get_llm_client(), get_qdrant_store())

    def get_diagnostic_pipeline():
        return DiagnosticPipeline()

except ImportError:
    pass  # v3 LLM/RAG modules not available in this environment
