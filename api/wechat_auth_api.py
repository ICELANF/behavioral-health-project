"""
WeChat OAuth + Phone Verification API

Endpoints:
  GET  /api/v1/auth/wechat/login       — Generate OAuth URL
  GET  /api/v1/auth/wechat/callback     — OAuth callback → JWT
  POST /api/v1/auth/wechat/bind         — Bind WeChat to existing account
  POST /api/v1/auth/wechat/unbind       — Remove binding
  GET  /api/v1/wechat/jsapi-ticket      — JSSDK signature
  POST /api/v1/auth/verify-phone        — Send SMS verification code
  POST /api/v1/auth/verify-phone/confirm — Verify code + link phone
"""
import random
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from core.database import get_async_db
from core.models import User

router = APIRouter(tags=["WeChat Auth"])


# ── Schemas ──

class BindRequest(BaseModel):
    code: str

class PhoneSendRequest(BaseModel):
    phone: str

class PhoneVerifyRequest(BaseModel):
    phone: str
    code: str


# ── Helper: create JWT ──

def _create_token(user_id: int, username: str, role: str) -> str:
    from jose import jwt
    import os
    secret = os.getenv("SECRET_KEY", "bhp-secret-key-change-in-production")
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": datetime.utcnow().timestamp() + 86400,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


# ═══════════════════════════════════════════════════
# WeChat OAuth
# ═══════════════════════════════════════════════════

@router.get("/api/v1/auth/wechat/login")
async def wechat_login(redirect_uri: str = Query(..., description="H5 redirect after auth")):
    """Generate WeChat OAuth URL or indicate not configured."""
    from gateway.channels.wx_gateway import get_oauth_url, is_configured
    if not is_configured():
        return {"message": "WeChat not configured", "configured": False}

    state = uuid.uuid4().hex[:8]
    oauth_url = get_oauth_url(redirect_uri, state)
    return {"oauth_url": oauth_url, "state": state}


@router.get("/api/v1/auth/wechat/callback")
async def wechat_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: AsyncSession = Depends(get_async_db),
):
    """Exchange code → find/create user → JWT → redirect."""
    from gateway.channels.wx_gateway import exchange_code, get_user_info

    token_data = await exchange_code(code)
    if not token_data:
        raise HTTPException(400, "WeChat authorization failed")

    openid = token_data["openid"]
    unionid = token_data.get("unionid")

    # Try to find existing user by openid or unionid
    user_row = None
    result = await db.execute(
        text("SELECT id, username, role::text AS role FROM users WHERE wx_openid = :oid LIMIT 1"),
        {"oid": openid},
    )
    user_row = result.mappings().first()

    if not user_row and unionid:
        result = await db.execute(
            text("SELECT id, username, role::text AS role FROM users WHERE union_id = :uid LIMIT 1"),
            {"uid": unionid},
        )
        user_row = result.mappings().first()

    if user_row:
        # Existing user — sync latest WeChat profile (avatar/nickname)
        try:
            wx_info = await get_user_info(token_data["access_token"], openid) or {}
            wx_nick = wx_info.get("nickname", "")
            wx_avatar = wx_info.get("avatar", "")
            if wx_nick or wx_avatar:
                await db.execute(
                    text("""
                        UPDATE users
                        SET nickname   = COALESCE(NULLIF(:nick, ''), nickname),
                            avatar_url = COALESCE(NULLIF(:av, ''), avatar_url),
                            updated_at = NOW()
                        WHERE id = :uid
                    """),
                    {"nick": wx_nick, "av": wx_avatar, "uid": user_row["id"]},
                )
                await db.commit()
        except Exception as e:
            logger.warning(f"WeChat profile sync failed for user {user_row['id']}: {e}")

        # Issue token
        jwt_token = _create_token(user_row["id"], user_row["username"], user_row["role"])
        return RedirectResponse(f"/?token={jwt_token}")

    # New user — get profile from WeChat
    wx_info = await get_user_info(token_data["access_token"], openid) or {}
    nickname = wx_info.get("nickname", "")
    avatar = wx_info.get("avatar", "")

    username = f"wx_{openid[:8]}"
    fake_email = f"{username}@wx.placeholder.local"
    # Use bcrypt hash of a random password (user can set later)
    from passlib.hash import bcrypt
    pw_hash = bcrypt.hash(uuid.uuid4().hex)

    await db.execute(
        text("""
            INSERT INTO users (username, email, password_hash, role, is_active, nickname, avatar_url,
                               wx_openid, union_id, preferred_channel, created_at, updated_at)
            VALUES (:un, :em, :pw, 'OBSERVER', true, :nick, :av,
                    :oid, :uid, 'wechat', NOW(), NOW())
        """),
        {
            "un": username, "em": fake_email, "pw": pw_hash,
            "nick": nickname, "av": avatar, "oid": openid, "uid": unionid,
        },
    )
    await db.commit()

    # Fetch newly created user
    result = await db.execute(
        text("SELECT id, username, role::text AS role FROM users WHERE wx_openid = :oid LIMIT 1"),
        {"oid": openid},
    )
    new_user = result.mappings().first()
    jwt_token = _create_token(new_user["id"], new_user["username"], new_user["role"])
    logger.info(f"WeChat new user created: {username}")
    return RedirectResponse(f"/?token={jwt_token}")


@router.post("/api/v1/auth/wechat/bind")
async def wechat_bind(
    req: BindRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Bind WeChat to an existing authenticated account."""
    from gateway.channels.wx_gateway import exchange_code

    token_data = await exchange_code(req.code)
    if not token_data:
        raise HTTPException(400, "Invalid WeChat code")

    openid = token_data["openid"]
    unionid = token_data.get("unionid")

    # Check if openid already bound to another user
    existing = await db.execute(
        text("SELECT id FROM users WHERE wx_openid = :oid AND id != :uid"),
        {"oid": openid, "uid": current_user.id},
    )
    if existing.first():
        raise HTTPException(409, "This WeChat account is already bound to another user")

    # Get WeChat profile for nickname/avatar sync
    wx_nick = ""
    wx_avatar = ""
    try:
        from gateway.channels.wx_gateway import get_user_info
        wx_info = await get_user_info(token_data["access_token"], openid) or {}
        wx_nick = wx_info.get("nickname", "")
        wx_avatar = wx_info.get("avatar", "")
    except Exception:
        pass

    await db.execute(
        text("""
            UPDATE users SET wx_openid = :oid, union_id = :uid,
                             nickname = COALESCE(NULLIF(:nick, ''), nickname),
                             avatar_url = COALESCE(NULLIF(:av, ''), avatar_url),
                             preferred_channel = COALESCE(preferred_channel, 'wechat'),
                             updated_at = NOW()
            WHERE id = :id
        """),
        {"oid": openid, "uid": unionid, "nick": wx_nick, "av": wx_avatar, "id": current_user.id},
    )
    await db.commit()
    return {"success": True, "openid": openid[:8] + "****"}


@router.post("/api/v1/auth/wechat/unbind")
async def wechat_unbind(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Remove WeChat binding from current account."""
    await db.execute(
        text("""
            UPDATE users SET wx_openid = NULL, union_id = NULL,
                             preferred_channel = CASE WHEN preferred_channel = 'wechat' THEN 'app' ELSE preferred_channel END,
                             updated_at = NOW()
            WHERE id = :id
        """),
        {"id": current_user.id},
    )
    await db.commit()
    return {"success": True}


# ═══════════════════════════════════════════════════
# JSSDK
# ═══════════════════════════════════════════════════

@router.get("/api/v1/wechat/jsapi-ticket")
async def jsapi_ticket(
    url: str = Query(..., description="Current page URL for signing"),
    current_user: User = Depends(get_current_user),
):
    """Get JSSDK config signature for wx.config()."""
    from gateway.channels.wx_gateway import sign_jsapi, is_configured
    if not is_configured():
        return {"configured": False}
    sig = await sign_jsapi(url)
    if not sig:
        raise HTTPException(500, "Failed to generate JSSDK signature")
    return {**sig, "configured": True}


# ═══════════════════════════════════════════════════
# SMS Phone Verification
# ═══════════════════════════════════════════════════

@router.post("/api/v1/auth/verify-phone")
async def send_phone_code(
    req: PhoneSendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Send a 6-digit SMS verification code (rate-limited: 1/phone/60s)."""
    import os
    phone = req.phone.strip()
    if len(phone) < 10:
        raise HTTPException(400, "Invalid phone number")

    # Rate limit via Redis
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        key = f"sms_rate:{phone}"
        if await r.exists(key):
            raise HTTPException(429, "Please wait 60 seconds before requesting a new code")
        code = f"{random.randint(100000, 999999)}"
        await r.setex(f"sms_code:{phone}", 300, code)  # 5min TTL
        await r.setex(key, 60, "1")  # rate limit 60s
        await r.aclose()
    except HTTPException:
        raise
    except Exception:
        # Redis unavailable — generate code in-memory (dev mode)
        code = f"{random.randint(100000, 999999)}"
        logger.warning("Redis unavailable for SMS code, using in-memory fallback")

    # Send SMS
    from gateway.channels.sms_gateway import send_sms, is_configured as sms_configured
    if sms_configured():
        await send_sms(phone, "SMS_BHP_VERIFY", {"code": code})
    else:
        logger.info(f"[DEV] SMS code for {phone}: {code}")

    return {"success": True, "message": "Verification code sent"}


@router.post("/api/v1/auth/verify-phone/confirm")
async def confirm_phone_code(
    req: PhoneVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Verify SMS code and link phone to current user."""
    import os
    phone = req.phone.strip()

    # Verify code
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        stored = await r.get(f"sms_code:{phone}")
        await r.aclose()
        if not stored or stored.decode() != req.code:
            raise HTTPException(400, "Invalid or expired verification code")
    except HTTPException:
        raise
    except Exception:
        logger.warning("Redis unavailable for SMS verify, accepting any code in dev mode")

    # Check if phone already bound
    existing = await db.execute(
        text("SELECT id FROM users WHERE phone = :p AND id != :uid"),
        {"p": phone, "uid": current_user.id},
    )
    if existing.first():
        raise HTTPException(409, "This phone number is already bound to another account")

    await db.execute(
        text("UPDATE users SET phone = :p, updated_at = NOW() WHERE id = :uid"),
        {"p": phone, "uid": current_user.id},
    )
    await db.commit()
    return {"success": True, "phone": phone[:3] + "****" + phone[-4:]}
