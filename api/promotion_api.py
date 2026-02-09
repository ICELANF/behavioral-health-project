# -*- coding: utf-8 -*-
"""
晋级系统 API

晋级进度查询、晋级申请、审核
"""

import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from core.database import get_db
from api.dependencies import get_current_user, require_coach_or_admin
from core.models import User, PromotionApplication, PromotionStatus, ROLE_LEVEL
from core.promotion_service import check_promotion_eligibility

router = APIRouter(prefix="/api/v1/promotion", tags=["晋级系统"])

# 加载晋级规则
_rules_path = Path(__file__).parent.parent / "configs" / "promotion_rules.json"
_RULES = {}
if _rules_path.exists():
    with open(_rules_path, "r", encoding="utf-8") as f:
        _RULES = json.load(f)


@router.get("/progress")
def get_promotion_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户晋级进度（四维雷达数据）"""
    row = db.execute(
        text("SELECT * FROM v_promotion_progress WHERE user_id = :uid"),
        {"uid": current_user.id}
    ).mappings().first()

    if not row:
        return {"user_id": current_user.id, "message": "暂无数据"}

    progress = dict(row)

    # 匹配当前适用的晋级规则
    current_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    applicable_rule = None
    for rule in _RULES.get("rules", []):
        if rule["from_role"] == current_role.lower():
            applicable_rule = rule
            break

    progress["next_level_rule"] = applicable_rule
    return progress


@router.get("/rules")
def get_promotion_rules(
    current_user: User = Depends(get_current_user),
):
    """获取所有晋级规则配置"""
    return _RULES.get("rules", [])


@router.get("/check")
def check_eligibility(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """校验当前用户晋级资格（不提交申请）"""
    eligible, result = check_promotion_eligibility(db, current_user)
    return result


@router.post("/apply")
def apply_for_promotion(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交晋级申请（自动校验条件）"""
    # 先校验资格
    eligible, check_result = check_promotion_eligibility(db, current_user)

    if not eligible:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "不满足晋级条件",
                "check_result": check_result,
            }
        )

    current_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)

    # 查找适用规则
    rule = None
    for r in _RULES.get("rules", []):
        if r["from_role"] == current_role.lower():
            rule = r
            break

    if not rule:
        raise HTTPException(400, "当前角色无可用晋级路径")

    # 检查是否已有待审核申请 (ORM)
    pending = db.query(PromotionApplication).filter(
        PromotionApplication.user_id == current_user.id,
        PromotionApplication.status == PromotionStatus.PENDING,
    ).first()

    if pending:
        raise HTTPException(409, "已有待审核的晋级申请")

    # 获取当前进度快照
    progress = db.execute(
        text("SELECT * FROM v_promotion_progress WHERE user_id = :uid"),
        {"uid": current_user.id}
    ).mappings().first()

    if not progress:
        raise HTTPException(400, "无法获取晋级进度数据")

    p = dict(progress)
    from_role = current_role.upper()
    to_role = rule["to_role"].upper()

    # 创建申请 (ORM)
    app = PromotionApplication(
        user_id=current_user.id,
        from_role=from_role,
        to_role=to_role,
        credit_snapshot={
            "total_credits": float(p.get("total_credits", 0) or 0),
            "mandatory_credits": float(p.get("mandatory_credits", 0) or 0),
            "m1": float(p.get("m1_credits", 0) or 0),
            "m2": float(p.get("m2_credits", 0) or 0),
            "m3": float(p.get("m3_credits", 0) or 0),
            "m4": float(p.get("m4_credits", 0) or 0),
        },
        point_snapshot={
            "growth": float(p.get("growth_points", 0) or 0),
            "contribution": float(p.get("contribution_points", 0) or 0),
            "influence": float(p.get("influence_points", 0) or 0),
        },
        companion_snapshot={
            "graduated": int(p.get("companions_graduated", 0) or 0),
            "active": int(p.get("companions_active", 0) or 0),
            "avg_quality": float(p["companion_avg_quality"]) if p.get("companion_avg_quality") else None,
        },
        check_result=check_result,
        status=PromotionStatus.PENDING,
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    return {
        "message": "晋级申请已提交",
        "application_id": str(app.id),
        "from": rule["from_role"],
        "to": rule["to_role"],
    }


@router.get("/applications")
def list_promotion_applications(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """查看晋级申请列表（教练/管理员）"""
    sql = (
        "SELECT pa.*, u.username "
        "FROM promotion_applications pa "
        "JOIN users u ON pa.user_id = u.id"
    )
    params = {}

    if status:
        sql += " WHERE pa.status = :st"
        params["st"] = status

    sql += " ORDER BY pa.created_at DESC"
    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.post("/review/{application_id}")
def review_promotion(
    application_id: str,
    action: str,
    comment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """审核晋级申请"""
    if action not in ("approved", "rejected"):
        raise HTTPException(400, "action 必须是 approved 或 rejected")

    app = db.query(PromotionApplication).filter(
        PromotionApplication.id == application_id,
        PromotionApplication.status == PromotionStatus.PENDING,
    ).first()

    if not app:
        raise HTTPException(404, "申请不存在或已处理")

    from datetime import datetime
    app.status = PromotionStatus.APPROVED if action == "approved" else PromotionStatus.REJECTED
    app.reviewer_id = current_user.id
    app.review_comment = comment
    app.reviewed_at = datetime.utcnow()

    # 如果通过，更新用户角色
    if action == "approved":
        user = db.query(User).filter(User.id == app.user_id).first()
        if user:
            user.role = app.to_role

    db.commit()
    return {"message": f"申请已{action}", "application_id": application_id}
