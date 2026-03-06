# -*- coding: utf-8 -*-
"""
手机号注册 / 登录 API
api/phone_auth_api.py

端点：
  POST /api/v1/auth/phone/send-code     发送验证码
  POST /api/v1/auth/phone/register      手机号注册
  POST /api/v1/auth/phone/login         手机号登录
"""

import os
import re
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.database import get_db
from api.auth import create_access_token, create_refresh_token
from api.sms_service import (
    generate_code, send_sms_code, save_code,
    verify_code, check_daily_limit, SMS_PROVIDER
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth/phone", tags=["手机号认证"])

PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


def _validate_phone(phone: str) -> str:
    phone = phone.strip()
    if not PHONE_RE.match(phone):
        raise HTTPException(status_code=422, detail="手机号格式不正确")
    return phone


def _get_user_by_phone(db: Session, phone: str):
    return db.execute(
        text("SELECT * FROM users WHERE phone = :phone"),
        {"phone": phone}
    ).fetchone()


def _build_token_response(user_row, access_token: str, refresh_token: str) -> dict:
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user_row.id,
            "username": user_row.username,
            "phone": user_row.phone,
            "nickname": user_row.nickname,
            "role": str(user_row.role),
            "current_stage": user_row.current_stage,
        }
    }


# ── 请求模型 ──────────────────────────────────────────

class SendCodeRequest(BaseModel):
    phone: str = Field(..., description="手机号")
    purpose: str = Field("register", description="register / login")

    @validator("purpose")
    def purpose_valid(cls, v):
        if v not in ("register", "login"):
            raise ValueError("purpose 只能是 register 或 login")
        return v


class PhoneRegisterRequest(BaseModel):
    phone: str
    code: str = Field(..., min_length=4, max_length=8)
    nickname: Optional[str] = Field(None, max_length=32)


class PhoneLoginRequest(BaseModel):
    phone: str
    code: str = Field(..., min_length=4, max_length=8)


# ── 端点 ──────────────────────────────────────────────

@router.post("/send-code", summary="发送验证码")
async def send_code(req: SendCodeRequest, db: Session = Depends(get_db)):
    phone = _validate_phone(req.phone)

    if not check_daily_limit(db, phone):
        raise HTTPException(status_code=429, detail="今日发送次数已达上限")

    if req.purpose == "register":
        if _get_user_by_phone(db, phone):
            raise HTTPException(status_code=409, detail="该手机号已注册，请直接登录")

    if req.purpose == "login":
        if not _get_user_by_phone(db, phone):
            raise HTTPException(status_code=404, detail="该手机号未注册，请先注册")

    code = generate_code()
    save_code(db, phone, code, req.purpose)
    ok = await send_sms_code(phone, code, req.purpose)

    if not ok:
        raise HTTPException(status_code=500, detail="短信发送失败，请稍后重试")

    resp = {"message": "验证码已发送", "expire_minutes": 5}
    if SMS_PROVIDER == "mock":
        resp["debug_code"] = code
        resp["notice"] = "测试模式，生产环境不返回验证码"
    return resp


@router.post("/register", summary="手机号注册")
async def phone_register(req: PhoneRegisterRequest, db: Session = Depends(get_db)):
    phone = _validate_phone(req.phone)

    if _get_user_by_phone(db, phone):
        raise HTTPException(status_code=409, detail="该手机号已注册")

    valid, err = verify_code(db, phone, req.code, purpose="register")
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    suffix = uuid.uuid4().hex[:6]
    auto_username = f"u_{phone[-4:]}_{suffix}"
    auto_email = f"{phone}@bhp.local"
    nickname = req.nickname or f"用户{phone[-4:]}"

    try:
        result = db.execute(text("""
            INSERT INTO users (
                username, email, phone, password_hash,
                nickname, is_active, is_verified,
                role, current_stage, growth_level,
                growth_points, created_at, updated_at
            ) VALUES (
                :username, :email, :phone, NULL,
                :nickname, true, true,
                'observer', 'S0', 'G0',
                0, now(), now()
            ) RETURNING id, username, phone, nickname, role, current_stage
        """), {
            "username": auto_username,
            "email": auto_email,
            "phone": phone,
            "nickname": nickname,
        })
        db.commit()
        user = result.fetchone()
    except Exception as e:
        db.rollback()
        logger.error(f"[PhoneRegister] 创建用户失败: {e}")
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试")

    # ✅ 修复：使用正确签名 create_access_token(user_id, role)
    access_token = create_access_token(user.id, str(user.role))
    refresh_token = create_refresh_token(user.id, str(user.role))

    logger.info(f"[PhoneRegister] 新用户注册: id={user.id} phone={phone}")
    return {"message": "注册成功", **_build_token_response(user, access_token, refresh_token)}


@router.post("/login", summary="手机号登录")
async def phone_login(req: PhoneLoginRequest, db: Session = Depends(get_db)):
    phone = _validate_phone(req.phone)

    user = _get_user_by_phone(db, phone)
    if not user:
        raise HTTPException(status_code=404, detail="该手机号未注册")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    valid, err = verify_code(db, phone, req.code, purpose="login")
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    db.execute(text("UPDATE users SET last_login_at = now() WHERE id = :id"), {"id": user.id})
    db.commit()

    # ✅ 修复：使用正确签名
    access_token = create_access_token(user.id, str(user.role))
    refresh_token = create_refresh_token(user.id, str(user.role))

    logger.info(f"[PhoneLogin] 登录成功: id={user.id} phone={phone}")
    return {"message": "登录成功", **_build_token_response(user, access_token, refresh_token)}
