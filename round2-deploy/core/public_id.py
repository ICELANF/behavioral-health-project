# -*- coding: utf-8 -*-
"""Public ID 工具 (FIX-17) — 对外 UUID, 内部 int"""
from uuid import UUID
from fastapi import HTTPException, status


def resolve_public_id(db, model, public_id_str: str) -> int:
    """将 public_id (UUID) 解析为内部 integer id"""
    try:
        uid = UUID(public_id_str)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="无效的用户标识符")

    record = db.query(model).filter(model.public_id == uid).first()
    if not record:
        raise HTTPException(status_code=404, detail="用户不存在")
    return record.id
