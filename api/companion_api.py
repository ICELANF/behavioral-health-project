# -*- coding: utf-8 -*-
"""
同道者关系 API

同道者关系管理、统计查询、管理端查看
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from core.database import get_db
from api.dependencies import get_current_user, require_admin, require_coach_or_admin
from core.models import User, CompanionRelation, CompanionStatus

router = APIRouter(prefix="/api/v1/companions", tags=["同道者关系"])


@router.get("/my-mentees")
def get_my_mentees(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我带教的同道者列表"""
    q = db.query(CompanionRelation).filter(
        CompanionRelation.mentor_id == current_user.id
    )
    if status:
        q = q.filter(CompanionRelation.status == status)
    q = q.order_by(CompanionRelation.started_at.desc())

    relations = q.all()
    result = []
    for cr in relations:
        mentee = db.query(User).filter(User.id == cr.mentee_id).first()
        result.append({
            "id": str(cr.id),
            "mentee_id": cr.mentee_id,
            "mentee_name": mentee.username if mentee else None,
            "mentee_current_role": mentee.role.value if mentee and hasattr(mentee.role, 'value') else (str(mentee.role) if mentee else None),
            "mentor_role": cr.mentor_role,
            "mentee_role": cr.mentee_role,
            "status": cr.status,
            "quality_score": float(cr.quality_score) if cr.quality_score else None,
            "started_at": str(cr.started_at) if cr.started_at else None,
            "graduated_at": str(cr.graduated_at) if cr.graduated_at else None,
            "notes": cr.notes,
        })
    return result


@router.get("/my-mentors")
def get_my_mentors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的导师列表"""
    relations = db.query(CompanionRelation).filter(
        CompanionRelation.mentee_id == current_user.id
    ).order_by(CompanionRelation.started_at.desc()).all()

    result = []
    for cr in relations:
        mentor = db.query(User).filter(User.id == cr.mentor_id).first()
        result.append({
            "id": str(cr.id),
            "mentor_id": cr.mentor_id,
            "mentor_name": mentor.username if mentor else None,
            "mentor_current_role": mentor.role.value if mentor and hasattr(mentor.role, 'value') else (str(mentor.role) if mentor else None),
            "mentor_role": cr.mentor_role,
            "mentee_role": cr.mentee_role,
            "status": cr.status,
            "quality_score": float(cr.quality_score) if cr.quality_score else None,
            "started_at": str(cr.started_at) if cr.started_at else None,
            "graduated_at": str(cr.graduated_at) if cr.graduated_at else None,
        })
    return result


@router.get("/stats")
def get_companion_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的同道者统计"""
    row = db.execute(
        text("SELECT * FROM v_companion_stats WHERE mentor_id = :mid"),
        {"mid": current_user.id}
    ).mappings().first()

    return dict(row) if row else {
        "mentor_id": current_user.id,
        "graduated_count": 0,
        "active_count": 0,
        "dropped_count": 0,
        "avg_quality": None,
    }


@router.post("/invite")
def invite_mentee(
    mentee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """邀请同道者(建立带教关系)"""
    if mentee_id == current_user.id:
        raise HTTPException(400, "不能带教自己")

    mentee = db.query(User).filter(User.id == mentee_id).first()
    if not mentee:
        raise HTTPException(404, "用户不存在")

    # 检查是否已存在关系 (ORM)
    existing = db.query(CompanionRelation).filter(
        CompanionRelation.mentor_id == current_user.id,
        CompanionRelation.mentee_id == mentee_id,
    ).first()

    if existing:
        raise HTTPException(409, "带教关系已存在")

    mentor_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    mentee_role_str = mentee.role.value if hasattr(mentee.role, 'value') else str(mentee.role)

    cr = CompanionRelation(
        mentor_id=current_user.id,
        mentee_id=mentee_id,
        mentor_role=mentor_role,
        mentee_role=mentee_role_str,
        status=CompanionStatus.ACTIVE.value,
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)
    return {"message": "带教关系已建立", "id": str(cr.id), "mentee_id": mentee_id}


# ─── Admin / Coach endpoints ───


@router.get("/all")
def admin_list_all_relations(
    status: Optional[str] = None,
    mentor_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """管理员/教练查看所有同道者关系"""
    q = db.query(CompanionRelation)
    if status:
        q = q.filter(CompanionRelation.status == status)
    if mentor_id:
        q = q.filter(CompanionRelation.mentor_id == mentor_id)

    total = q.count()
    relations = q.order_by(CompanionRelation.started_at.desc()).offset(skip).limit(limit).all()

    items = []
    for cr in relations:
        mentor = db.query(User).filter(User.id == cr.mentor_id).first()
        mentee = db.query(User).filter(User.id == cr.mentee_id).first()
        items.append({
            "id": str(cr.id),
            "mentor_id": cr.mentor_id,
            "mentor_name": mentor.username if mentor else None,
            "mentee_id": cr.mentee_id,
            "mentee_name": mentee.username if mentee else None,
            "mentor_role": cr.mentor_role,
            "mentee_role": cr.mentee_role,
            "status": cr.status,
            "quality_score": float(cr.quality_score) if cr.quality_score else None,
            "started_at": str(cr.started_at) if cr.started_at else None,
            "graduated_at": str(cr.graduated_at) if cr.graduated_at else None,
        })

    return {"total": total, "items": items}


@router.put("/{relation_id}/graduate")
def graduate_mentee(
    relation_id: str,
    quality_score: Optional[float] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记同道者毕业"""
    cr = db.query(CompanionRelation).filter(
        CompanionRelation.id == relation_id,
        CompanionRelation.mentor_id == current_user.id,
    ).first()

    if not cr:
        raise HTTPException(404, "带教关系不存在")

    if cr.status == CompanionStatus.GRADUATED.value:
        raise HTTPException(400, "该同道者已毕业")

    cr.status = CompanionStatus.GRADUATED.value
    cr.graduated_at = datetime.utcnow()
    if quality_score is not None:
        cr.quality_score = quality_score
    if notes:
        cr.notes = notes

    db.commit()
    return {"message": "同道者已标记毕业", "id": str(cr.id)}
