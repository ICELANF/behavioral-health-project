"""
Token 安全存储 (FIX-13)
存储 SHA-256 哈希而非明文, 数据库泄露不暴露有效 token
"""
import hashlib
from sqlalchemy.orm import Session


def hash_token(token: str) -> str:
    """SHA-256 哈希 token"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def store_session_token(
    db: Session,
    session_model,
    session_id: str,
    user_id: int,
    access_token: str,
    refresh_token: str,
    ip_address: str = None,
    user_agent: str = None,
    expires_at=None,
):
    """
    创建会话记录 — 仅存储 token 哈希

    用法:
        from core.token_storage import store_session_token
        store_session_token(db, UserSession, sid, uid, at, rt, ...)
    """
    session = session_model(
        session_id=session_id,
        user_id=user_id,
        token=hash_token(access_token),       # 哈希存储
        refresh_token=hash_token(refresh_token),  # 哈希存储
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True,
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    return session


def verify_session_token(
    db: Session,
    session_model,
    token: str,
) -> bool:
    """验证 token 是否有活跃会话"""
    token_hash = hash_token(token)
    session = db.query(session_model).filter(
        session_model.token == token_hash,
        session_model.is_active == True,
    ).first()
    return session is not None
