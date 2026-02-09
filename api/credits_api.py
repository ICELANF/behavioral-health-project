# -*- coding: utf-8 -*-
"""
学分管理 API

课程模块浏览、学分记录、学分统计、管理端CRUD
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from pydantic import BaseModel

from core.database import get_db
from api.dependencies import get_current_user, require_admin
from core.models import User, CourseModule, UserCredit

router = APIRouter(prefix="/api/v1/credits", tags=["学分管理"])


# ─── Schemas ───


class ModuleCreateSchema(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    module_type: str  # M1_BEHAVIOR / M2_LIFESTYLE / M3_MINDSET / M4_COACHING
    elective_cat: Optional[str] = None
    tier: Optional[str] = None
    target_role: Optional[str] = None
    credit_value: float = 0
    theory_ratio: Optional[float] = None
    prereq_modules: Optional[str] = None
    content_ref: Optional[str] = None
    sort_order: int = 0


class ModuleUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    module_type: Optional[str] = None
    elective_cat: Optional[str] = None
    tier: Optional[str] = None
    credit_value: Optional[float] = None
    theory_ratio: Optional[float] = None
    prereq_modules: Optional[str] = None
    content_ref: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


# ─── User endpoints ───


@router.get("/modules")
def list_course_modules(
    module_type: Optional[str] = None,
    tier: Optional[str] = None,
    target_role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程模块列表"""
    q = db.query(CourseModule).filter(CourseModule.is_active == True)

    if module_type:
        q = q.filter(CourseModule.module_type == module_type)
    if tier:
        q = q.filter(CourseModule.tier == tier)
    if target_role:
        q = q.filter(CourseModule.target_role == target_role)

    q = q.order_by(CourseModule.sort_order, CourseModule.created_at)
    modules = q.all()

    return [
        {
            "id": str(m.id), "code": m.code, "title": m.title,
            "description": m.description, "module_type": m.module_type,
            "elective_cat": m.elective_cat, "tier": m.tier,
            "target_role": m.target_role, "credit_value": float(m.credit_value or 0),
            "theory_ratio": float(m.theory_ratio) if m.theory_ratio else None,
            "prereq_modules": m.prereq_modules, "content_ref": m.content_ref,
            "sort_order": m.sort_order, "is_active": m.is_active,
        }
        for m in modules
    ]


@router.get("/my")
def get_my_credits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户学分汇总"""
    # 总学分 (view)
    total = db.execute(
        text("SELECT * FROM v_user_total_credits WHERE user_id = :uid"),
        {"uid": current_user.id}
    ).mappings().first()

    # 按模块类型 (view)
    by_type = db.execute(
        text("SELECT * FROM v_user_credit_summary WHERE user_id = :uid"),
        {"uid": current_user.id}
    ).mappings().all()

    return {
        "total": dict(total) if total else {
            "total_credits": 0, "mandatory_credits": 0, "elective_credits": 0,
            "m1_credits": 0, "m2_credits": 0, "m3_credits": 0, "m4_credits": 0
        },
        "by_type": [dict(r) for r in by_type],
    }


@router.get("/my/records")
def get_my_credit_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户学分明细"""
    rows = db.execute(
        text(
            "SELECT uc.*, cm.title AS module_title, cm.module_type, cm.tier "
            "FROM user_credits uc JOIN course_modules cm ON uc.module_id = cm.id "
            "WHERE uc.user_id = :uid ORDER BY uc.completed_at DESC "
            "LIMIT :lim OFFSET :off"
        ),
        {"uid": current_user.id, "lim": limit, "off": skip}
    ).mappings().all()
    return [dict(r) for r in rows]


# ─── Admin endpoints ───


@router.get("/admin/modules")
def admin_list_modules(
    include_inactive: bool = False,
    module_type: Optional[str] = None,
    target_role: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """管理员查看所有课程模块（含停用）"""
    q = db.query(CourseModule)
    if not include_inactive:
        q = q.filter(CourseModule.is_active == True)
    if module_type:
        q = q.filter(CourseModule.module_type == module_type)
    if target_role:
        q = q.filter(CourseModule.target_role == target_role)

    total = q.count()
    modules = q.order_by(CourseModule.sort_order, CourseModule.created_at).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": str(m.id), "code": m.code, "title": m.title,
                "description": m.description, "module_type": m.module_type,
                "elective_cat": m.elective_cat, "tier": m.tier,
                "target_role": m.target_role, "credit_value": float(m.credit_value or 0),
                "theory_ratio": float(m.theory_ratio) if m.theory_ratio else None,
                "prereq_modules": m.prereq_modules, "content_ref": m.content_ref,
                "sort_order": m.sort_order, "is_active": m.is_active,
                "created_at": str(m.created_at) if m.created_at else None,
                "updated_at": str(m.updated_at) if m.updated_at else None,
            }
            for m in modules
        ],
    }


@router.post("/admin/modules")
def admin_create_module(
    data: ModuleCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """管理员创建课程模块"""
    existing = db.query(CourseModule).filter(CourseModule.code == data.code).first()
    if existing:
        raise HTTPException(409, f"模块编码 {data.code} 已存在")

    module = CourseModule(
        code=data.code,
        title=data.title,
        description=data.description,
        module_type=data.module_type,
        elective_cat=data.elective_cat,
        tier=data.tier,
        target_role=data.target_role,
        credit_value=data.credit_value,
        theory_ratio=data.theory_ratio,
        prereq_modules=data.prereq_modules,
        content_ref=data.content_ref,
        sort_order=data.sort_order,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return {"message": "模块已创建", "id": str(module.id), "code": module.code}


@router.put("/admin/modules/{module_id}")
def admin_update_module(
    module_id: str,
    data: ModuleUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """管理员更新课程模块"""
    module = db.query(CourseModule).filter(CourseModule.id == module_id).first()
    if not module:
        raise HTTPException(404, "模块不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(module, key, val)
    module.updated_at = datetime.utcnow()

    db.commit()
    return {"message": "模块已更新", "id": str(module.id)}


@router.delete("/admin/modules/{module_id}")
def admin_delete_module(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """管理员停用课程模块（软删除）"""
    module = db.query(CourseModule).filter(CourseModule.id == module_id).first()
    if not module:
        raise HTTPException(404, "模块不存在")

    module.is_active = False
    module.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "模块已停用", "id": str(module.id)}


@router.get("/admin/stats")
def admin_credit_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """管理员学分统计概览"""
    # 总模块数
    total_modules = db.query(CourseModule).filter(CourseModule.is_active == True).count()

    # 按类型统计
    by_type = db.execute(
        text(
            "SELECT module_type, COUNT(*) AS cnt, SUM(credit_value) AS total_credits "
            "FROM course_modules WHERE is_active = true "
            "GROUP BY module_type ORDER BY module_type"
        )
    ).mappings().all()

    # 学分记录总数
    total_records = db.query(UserCredit).count()

    # 有学分的用户数
    users_with_credits = db.execute(
        text("SELECT COUNT(DISTINCT user_id) AS cnt FROM user_credits")
    ).scalar()

    return {
        "total_modules": total_modules,
        "by_type": [dict(r) for r in by_type],
        "total_credit_records": total_records,
        "users_with_credits": users_with_credits or 0,
    }
