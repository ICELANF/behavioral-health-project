# -*- coding: utf-8 -*-
"""
Token 安全存储 (FIX-13)
存储 SHA-256 哈希而非明文, 数据库泄露不暴露有效 token
"""
import hashlib
from sqlalchemy.orm import Session


def hash_token(token: str) -> str:
    """SHA-256 哈希 token"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def store_session_token(db, session_model, **kwargs):
    """
    创建会话记录 — 存储 token 哈希

    用法:
        from core.token_storage import store_session_token, hash_token
        store_session_token(db, UserSession,
            user_id=uid, token=hash_token(access_token), ...)
    """
    session = session_model(**kwargs)
    db.add(session)
    db.commit()
    return session


def verify_session_token(db, session_model, token: str) -> bool:
    """验证 token 是否有活跃会话"""
    token_hash = hash_token(token)
    return db.query(session_model).filter(
        session_model.token == token_hash,
        session_model.is_active == True,
    ).first() is not None
