"""
Contract API — 用户契约生命周期 + 伦理声明

基于契约注册表 ②③④ Sheet:
- 用户契约签署/查询/续期
- 伦理声明签署 (Coach 5条 / Promoter 7条)
"""
from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from loguru import logger

from api.dependencies import get_current_user, get_db, require_admin
from core.models import User, UserContract, EthicalDeclaration
from schemas.contract_types import (
    ContractType, ContractStatus, COACH_5_CLAUSES, PROMOTER_7_CLAUSES,
)

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])


@router.get("/my")
def my_contracts(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取我的契约列表"""
    q = db.query(UserContract).filter(UserContract.user_id == current_user.id)
    if status:
        q = q.filter(UserContract.status == status)
    contracts = q.order_by(desc(UserContract.signed_at)).all()

    return {
        "total": len(contracts),
        "contracts": [
            {
                "id": c.id,
                "contract_type": c.contract_type,
                "role_at_signing": c.role_at_signing,
                "level_at_signing": c.level_at_signing,
                "status": c.status,
                "signed_at": str(c.signed_at),
                "expires_at": str(c.expires_at) if c.expires_at else None,
            }
            for c in contracts
        ],
    }


@router.post("/sign")
def sign_contract(
    contract_type: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """签署契约"""
    # Check if already has active contract of this type
    existing = db.query(UserContract).filter(
        UserContract.user_id == current_user.id,
        UserContract.contract_type == contract_type,
        UserContract.status == "active",
    ).first()

    if existing:
        return {"error": "已有生效中的同类契约", "existing_id": existing.id}

    contract = UserContract(
        user_id=current_user.id,
        contract_type=contract_type,
        role_at_signing=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        level_at_signing=0,
        content_snapshot={"type": contract_type, "version": "v4.0"},
        status="active",
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    try:
        from core.models import PointTransaction
        db.add(PointTransaction(
            user_id=current_user.id,
            action="contract_sign",
            point_type="growth",
            amount=5,
        ))
        db.commit()
    except Exception as e:
        logger.warning(f"积分记录失败: {e}")

    return {
        "success": True,
        "contract_id": contract.id,
        "contract_type": contract.contract_type,
        "signed_at": str(contract.signed_at),
    }


@router.get("/ethical/clauses")
def get_ethical_clauses(
    declaration_type: str = Query("coach_5clause"),
    current_user: User = Depends(get_current_user),
):
    """获取伦理声明条款"""
    if declaration_type == "promoter_7clause":
        clauses = PROMOTER_7_CLAUSES
    else:
        clauses = COACH_5_CLAUSES

    return {
        "declaration_type": declaration_type,
        "total_clauses": len(clauses),
        "clauses": [
            {"clause_id": c.clause_id, "text": c.text_zh, "category": c.category}
            for c in clauses
        ],
    }


@router.post("/ethical/sign")
def sign_ethical_declaration(
    declaration_type: str = Query("coach_5clause"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """签署伦理声明"""
    if declaration_type == "promoter_7clause":
        clauses = PROMOTER_7_CLAUSES
    else:
        clauses = COACH_5_CLAUSES

    declaration = EthicalDeclaration(
        user_id=current_user.id,
        declaration_type=declaration_type,
        clauses=[{"clause_id": c.clause_id, "text": c.text_zh} for c in clauses],
        total_clauses=len(clauses),
        accepted_all=True,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent", "")[:300] if request else None,
    )
    db.add(declaration)
    db.commit()
    db.refresh(declaration)

    return {
        "success": True,
        "declaration_id": declaration.id,
        "declaration_type": declaration_type,
        "total_clauses": len(clauses),
        "signed_at": str(declaration.signed_at),
    }


@router.get("/ethical/my")
def my_ethical_declarations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取我的伦理声明记录"""
    declarations = db.query(EthicalDeclaration).filter(
        EthicalDeclaration.user_id == current_user.id,
    ).order_by(desc(EthicalDeclaration.signed_at)).all()

    return {
        "total": len(declarations),
        "declarations": [
            {
                "id": d.id,
                "declaration_type": d.declaration_type,
                "total_clauses": d.total_clauses,
                "accepted_all": d.accepted_all,
                "signed_at": str(d.signed_at),
                "revoked_at": str(d.revoked_at) if d.revoked_at else None,
            }
            for d in declarations
        ],
    }


@router.get("/types")
def contract_types_catalog(
    current_user: User = Depends(get_current_user),
):
    """获取契约类型目录"""
    return {
        "contract_types": [
            {"code": t.value, "label": t.value.replace("_", " ").title()}
            for t in ContractType
        ],
        "ethical_types": [
            {"code": "coach_5clause", "label": "教练伦理声明 (5条)", "clauses": 5},
            {"code": "promoter_7clause", "label": "推广者伦理声明 (7条)", "clauses": 7},
        ],
    }
