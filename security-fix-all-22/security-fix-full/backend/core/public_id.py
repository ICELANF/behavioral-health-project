"""
Public ID 工具 (FIX-17)

对外接口使用 UUID public_id, 内部使用整数 id
"""
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status


def resolve_public_id(db: Session, model, public_id: str) -> int:
    """
    将 public_id (UUID) 解析为内部 integer id

    用法:
        user_id = resolve_public_id(db, User, request_path_param)
    """
    try:
        uid = UUID(public_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户标识符"
        )

    record = db.query(model).filter(model.public_id == uid).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return record.id
