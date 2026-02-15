"""
V4.0 Script Library API — 话术库 (MEU-32)

Endpoints:
  GET  /scripts           搜索话术
  GET  /scripts/{id}      获取单条话术
  POST /scripts           创建话术 (coach+)
  GET  /domains           所有领域
  GET  /scenarios          所有场景
  POST /seed              初始化种子话术 (admin)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db, require_admin, require_coach_or_admin
from core.models import User
from core.script_library_service import ScriptLibraryService

router = APIRouter(prefix="/api/v1/script-library", tags=["script-library"])


class CreateScriptRequest(BaseModel):
    title: str
    domain: str = "general"
    stage: str = "any"
    scenario: str = "general"
    agency_mode: str = "any"
    opening_line: str
    key_questions: Optional[List[str]] = None
    response_templates: Optional[List[str]] = None
    closing_line: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: str = "basic"
    evidence_source: Optional[str] = None


@router.get("/scripts")
def list_scripts(
    domain: Optional[str] = None,
    stage: Optional[str] = None,
    scenario: Optional[str] = None,
    agency_mode: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """搜索话术"""
    svc = ScriptLibraryService(db)
    return svc.list_scripts(domain, stage, scenario, agency_mode, search, limit, offset)


@router.get("/scripts/{script_id}")
def get_script(
    script_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单条话术 (自动计数使用次数)"""
    svc = ScriptLibraryService(db)
    result = svc.get_script(script_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    db.commit()
    return result


@router.post("/scripts")
def create_script(
    req: CreateScriptRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """创建话术 (教练/管理员)"""
    svc = ScriptLibraryService(db)
    result = svc.create_script(req.model_dump(), created_by=current_user.id)
    db.commit()
    return result


@router.get("/domains")
def get_domains(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有话术领域"""
    svc = ScriptLibraryService(db)
    return {"domains": svc.get_domains()}


@router.get("/scenarios")
def get_scenarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有话术场景"""
    svc = ScriptLibraryService(db)
    return {"scenarios": svc.get_scenarios()}


@router.post("/seed")
def seed_scripts(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """初始化种子话术 (管理员)"""
    svc = ScriptLibraryService(db)
    count = svc.seed_scripts()
    db.commit()
    return {"seeded": count, "message": f"已初始化{count}条种子话术"}
