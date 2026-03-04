# -*- coding: utf-8 -*-
"""
就医管理 API

用药管理 + 就诊记录 — 成长者自我管理与依从性跟踪

端点:
  GET  /api/v1/medical/medications          — 我的用药列表
  POST /api/v1/medical/medications          — 添加药物
  PUT  /api/v1/medical/medications/{id}     — 更新用药（含打卡）
  DELETE /api/v1/medical/medications/{id}   — 停用

  GET  /api/v1/medical/visits               — 我的就诊记录
  POST /api/v1/medical/visits               — 新增就诊记录
  GET  /api/v1/medical/visits/{id}/summary  — 就诊摘要（带给教练/医生查看）

  GET  /api/v1/medical/adherence            — 用药依从统计
"""

from typing import Optional, List, Any
from datetime import date, datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text
from loguru import logger

from core.database import get_db
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/medical", tags=["就医管理"])

ENSURE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS user_medications (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    name        VARCHAR(100) NOT NULL,
    dosage      VARCHAR(50),
    frequency   VARCHAR(50),
    start_date  DATE,
    end_date    DATE,
    is_active    BOOLEAN DEFAULT TRUE,
    note         TEXT,
    reminder_time TIME,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE user_medications ADD COLUMN IF NOT EXISTS reminder_time TIME;

CREATE TABLE IF NOT EXISTS medication_logs (
    id            SERIAL PRIMARY KEY,
    medication_id INTEGER NOT NULL,
    user_id       INTEGER NOT NULL,
    taken_at      TIMESTAMPTZ DEFAULT NOW(),
    taken         BOOLEAN DEFAULT TRUE,
    note          TEXT
);

CREATE TABLE IF NOT EXISTS medical_visits (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL,
    visit_date    DATE NOT NULL,
    hospital      VARCHAR(100),
    department    VARCHAR(80),
    doctor_name   VARCHAR(50),
    chief_complaint TEXT,
    diagnosis     TEXT,
    prescription  TEXT,
    next_visit    DATE,
    attachments   JSONB DEFAULT '[]',
    is_shared     BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
"""


def _ensure_tables(db: Session):
    try:
        db.execute(sa_text(ENSURE_TABLES_SQL))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"[Medical] ensure_tables warn: {e}")


# ─── Pydantic Models ──────────────────────────────────────────

class MedicationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    note: Optional[str] = None
    reminder_time: Optional[str] = None   # "HH:MM" 格式，如 "08:30"


class MedicationUpdate(BaseModel):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    note: Optional[str] = None


class MedicationCheckin(BaseModel):
    taken: bool = True
    note: Optional[str] = None


class VisitCreate(BaseModel):
    visit_date: date
    hospital: Optional[str] = None
    department: Optional[str] = None
    doctor_name: Optional[str] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    next_visit: Optional[date] = None
    is_shared: bool = False


# ─── Medications ─────────────────────────────────────────────

@router.get("/medications")
def list_medications(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    _ensure_tables(db)
    try:
        where = "WHERE user_id = :uid"
        if active_only:
            where += " AND is_active = TRUE"
        rows = db.execute(sa_text(f"""
            SELECT id, name, dosage, frequency, start_date, end_date,
                   is_active, note, reminder_time, created_at
            FROM user_medications
            {where}
            ORDER BY is_active DESC, created_at DESC
        """), {"uid": current_user.id}).mappings().all()
        items = [dict(r) for r in rows]
        # attach last-taken for each med
        for item in items:
            last = db.execute(sa_text("""
                SELECT taken_at, taken FROM medication_logs
                WHERE medication_id = :mid ORDER BY taken_at DESC LIMIT 1
            """), {"mid": item["id"]}).mappings().first()
            item["last_taken_at"] = last["taken_at"] if last else None
            item["last_taken"] = last["taken"] if last else None
        return {"items": items, "total": len(items)}
    except Exception as e:
        logger.error(f"[Medical] list_medications: {e}")
        raise HTTPException(status_code=500, detail="获取用药列表失败")


@router.post("/medications")
def add_medication(
    body: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    _ensure_tables(db)
    try:
        row = db.execute(sa_text("""
            INSERT INTO user_medications (user_id, name, dosage, frequency, start_date, end_date, note, reminder_time)
            VALUES (:uid, :name, :dosage, :freq, :start_d, :end_d, :note, :reminder)
            RETURNING id, name, dosage, frequency, start_date, is_active, reminder_time, created_at
        """), {
            "uid": current_user.id,
            "name": body.name,
            "dosage": body.dosage,
            "freq": body.frequency,
            "start_d": body.start_date,
            "end_d": body.end_date,
            "note": body.note,
            "reminder": body.reminder_time,
        }).mappings().first()
        db.commit()
        return {"success": True, "medication": dict(row)}
    except Exception as e:
        db.rollback()
        logger.error(f"[Medical] add_medication: {e}")
        raise HTTPException(status_code=500, detail="添加失败")


@router.put("/medications/{med_id}")
def update_medication(
    med_id: int,
    body: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    _ensure_tables(db)
    try:
        sets = ["updated_at = NOW()"]
        params: dict = {"id": med_id, "uid": current_user.id}
        if body.dosage is not None:
            sets.append("dosage = :dosage"); params["dosage"] = body.dosage
        if body.frequency is not None:
            sets.append("frequency = :frequency"); params["frequency"] = body.frequency
        if body.end_date is not None:
            sets.append("end_date = :end_date"); params["end_date"] = body.end_date
        if body.is_active is not None:
            sets.append("is_active = :is_active"); params["is_active"] = body.is_active
        if body.note is not None:
            sets.append("note = :note"); params["note"] = body.note
        db.execute(sa_text(f"""
            UPDATE user_medications SET {', '.join(sets)}
            WHERE id = :id AND user_id = :uid
        """), params)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        logger.error(f"[Medical] update_medication: {e}")
        raise HTTPException(status_code=500, detail="更新失败")


@router.post("/medications/{med_id}/checkin")
def medication_checkin(
    med_id: int,
    body: MedicationCheckin,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    _ensure_tables(db)
    try:
        db.execute(sa_text("""
            INSERT INTO medication_logs (medication_id, user_id, taken, note)
            VALUES (:mid, :uid, :taken, :note)
        """), {"mid": med_id, "uid": current_user.id, "taken": body.taken, "note": body.note})
        db.commit()
        return {"success": True, "taken": body.taken}
    except Exception as e:
        db.rollback()
        logger.error(f"[Medical] checkin: {e}")
        raise HTTPException(status_code=500, detail="打卡失败")


@router.delete("/medications/{med_id}")
def deactivate_medication(
    med_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    _ensure_tables(db)
    try:
        db.execute(sa_text("""
            UPDATE user_medications SET is_active = FALSE, updated_at = NOW()
            WHERE id = :id AND user_id = :uid
        """), {"id": med_id, "uid": current_user.id})
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="停用失败")


# ─── Adherence Stats ─────────────────────────────────────────

@router.get("/adherence")
def get_adherence(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    _ensure_tables(db)
    try:
        total_logs = db.execute(sa_text("""
            SELECT COUNT(*) as total, SUM(CASE WHEN taken THEN 1 ELSE 0 END) as taken_count
            FROM medication_logs
            WHERE user_id = :uid AND taken_at >= NOW() - INTERVAL ':days days'
        """), {"uid": current_user.id, "days": days}).mappings().first()
        total = total_logs["total"] or 0
        taken = total_logs["taken_count"] or 0
        rate = round(taken / total * 100, 1) if total > 0 else None
        active_count = db.execute(sa_text("""
            SELECT COUNT(*) FROM user_medications WHERE user_id = :uid AND is_active = TRUE
        """), {"uid": current_user.id}).scalar() or 0
        return {
            "period_days": days,
            "active_medications": active_count,
            "adherence_rate": rate,
            "taken": taken,
            "total_expected": total,
        }
    except Exception as e:
        logger.error(f"[Medical] adherence: {e}")
        return {"period_days": days, "active_medications": 0, "adherence_rate": None}


# ─── Visits ──────────────────────────────────────────────────

@router.get("/visits")
def list_visits(
    limit: int = 20,
    skip: int = 0,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    _ensure_tables(db)
    try:
        rows = db.execute(sa_text("""
            SELECT id, visit_date, hospital, department, doctor_name,
                   chief_complaint, diagnosis, prescription, next_visit,
                   is_shared, created_at
            FROM medical_visits
            WHERE user_id = :uid
            ORDER BY visit_date DESC
            LIMIT :limit OFFSET :skip
        """), {"uid": current_user.id, "limit": limit, "skip": skip}).mappings().all()
        return {"items": [dict(r) for r in rows]}
    except Exception as e:
        logger.error(f"[Medical] list_visits: {e}")
        raise HTTPException(status_code=500, detail="获取就诊记录失败")


@router.post("/visits")
def add_visit(
    body: VisitCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    _ensure_tables(db)
    try:
        row = db.execute(sa_text("""
            INSERT INTO medical_visits
              (user_id, visit_date, hospital, department, doctor_name,
               chief_complaint, diagnosis, prescription, next_visit, is_shared)
            VALUES
              (:uid, :visit_date, :hospital, :dept, :doc,
               :chief, :diag, :rx, :next_v, :shared)
            RETURNING id, visit_date, hospital, created_at
        """), {
            "uid": current_user.id,
            "visit_date": body.visit_date,
            "hospital": body.hospital,
            "dept": body.department,
            "doc": body.doctor_name,
            "chief": body.chief_complaint,
            "diag": body.diagnosis,
            "rx": body.prescription,
            "next_v": body.next_visit,
            "shared": body.is_shared,
        }).mappings().first()
        db.commit()
        return {"success": True, "visit": dict(row)}
    except Exception as e:
        db.rollback()
        logger.error(f"[Medical] add_visit: {e}")
        raise HTTPException(status_code=500, detail="添加就诊记录失败")


@router.get("/visits/{visit_id}/summary")
def visit_summary(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """就诊摘要 — 可分享给医生 / 教练查看"""
    _ensure_tables(db)
    try:
        v = db.execute(sa_text("""
            SELECT * FROM medical_visits WHERE id = :id AND user_id = :uid
        """), {"id": visit_id, "uid": current_user.id}).mappings().first()
        if not v:
            raise HTTPException(status_code=404, detail="就诊记录不存在")
        meds = db.execute(sa_text("""
            SELECT name, dosage, frequency FROM user_medications
            WHERE user_id = :uid AND is_active = TRUE
        """), {"uid": current_user.id}).mappings().all()
        return {
            "visit": dict(v),
            "active_medications": [dict(m) for m in meds],
            "summary_text": _build_summary(v, meds),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Medical] visit_summary: {e}")
        raise HTTPException(status_code=500, detail="获取摘要失败")


def _build_summary(v: Any, meds: Any) -> str:
    lines = []
    if v.get("visit_date"):
        lines.append(f"就诊日期：{v['visit_date']}")
    if v.get("hospital"):
        lines.append(f"医院/科室：{v['hospital']} {v.get('department', '')}")
    if v.get("chief_complaint"):
        lines.append(f"主诉：{v['chief_complaint']}")
    if v.get("diagnosis"):
        lines.append(f"诊断：{v['diagnosis']}")
    if v.get("prescription"):
        lines.append(f"处方：{v['prescription']}")
    if meds:
        med_list = "、".join(f"{m['name']}({m.get('dosage','')} {m.get('frequency','')})" for m in meds)
        lines.append(f"在用药物：{med_list}")
    if v.get("next_visit"):
        lines.append(f"下次复诊：{v['next_visit']}")
    return "\n".join(lines)
