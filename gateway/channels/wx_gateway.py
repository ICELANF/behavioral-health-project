"""
WeChat Official Account Gateway
- OAuth 2.0 (code → access_token + openid + unionid)
- Template message push
- JSSDK ticket & signature
"""
import hashlib
import os
import time
import uuid
from typing import Optional

import httpx
from loguru import logger

# ── Config ──
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")

# In-memory token cache (7200s TTL)
_token_cache: dict = {"access_token": "", "expires_at": 0}
_ticket_cache: dict = {"ticket": "", "expires_at": 0}

_BASE = "https://api.weixin.qq.com"


def is_configured() -> bool:
    return bool(WECHAT_APP_ID and WECHAT_APP_SECRET)


async def _get_access_token() -> Optional[str]:
    """Server-side access_token with 7200s cache."""
    if not is_configured():
        return None
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["access_token"]

    url = (
        f"{_BASE}/cgi-bin/token"
        f"?grant_type=client_credential"
        f"&appid={WECHAT_APP_ID}"
        f"&secret={WECHAT_APP_SECRET}"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
        if "access_token" in data:
            _token_cache["access_token"] = data["access_token"]
            _token_cache["expires_at"] = now + data.get("expires_in", 7200)
            return data["access_token"]
        logger.warning(f"WeChat token error: {data}")
    except Exception as e:
        logger.warning(f"WeChat token request failed: {e}")
    return None


# ─── OAuth ────────────────────────────────────────

def get_oauth_url(redirect_uri: str, state: str = "") -> Optional[str]:
    """Generate WeChat OAuth2 authorization URL."""
    if not is_configured():
        return None
    from urllib.parse import quote
    return (
        f"https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={WECHAT_APP_ID}"
        f"&redirect_uri={quote(redirect_uri)}"
        f"&response_type=code"
        f"&scope=snsapi_userinfo"
        f"&state={state or 'bhp'}"
        f"#wechat_redirect"
    )


async def exchange_code(code: str) -> Optional[dict]:
    """Exchange authorization code for access_token + openid + unionid."""
    if not is_configured():
        return None
    url = (
        f"{_BASE}/sns/oauth2/access_token"
        f"?appid={WECHAT_APP_ID}"
        f"&secret={WECHAT_APP_SECRET}"
        f"&code={code}"
        f"&grant_type=authorization_code"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
        if "openid" in data:
            return {
                "access_token": data["access_token"],
                "openid": data["openid"],
                "unionid": data.get("unionid"),
            }
        logger.warning(f"WeChat code exchange error: {data}")
    except Exception as e:
        logger.warning(f"WeChat code exchange failed: {e}")
    return None


async def get_user_info(access_token: str, openid: str) -> Optional[dict]:
    """Fetch user profile (nickname, avatar)."""
    url = f"{_BASE}/sns/userinfo?access_token={access_token}&openid={openid}&lang=zh_CN"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
        if "nickname" in data:
            return {
                "nickname": data.get("nickname", ""),
                "avatar": data.get("headimgurl", ""),
                "unionid": data.get("unionid"),
            }
    except Exception as e:
        logger.warning(f"WeChat user info failed: {e}")
    return None


# ─── Template Message ─────────────────────────────

async def send_template_message(
    openid: str,
    template_id: str,
    data: dict,
    url: str = "",
) -> bool:
    """Send a template message via WeChat Official Account."""
    token = await _get_access_token()
    if not token:
        return False
    api_url = f"{_BASE}/cgi-bin/message/template/send?access_token={token}"
    payload = {
        "touser": openid,
        "template_id": template_id,
        "url": url,
        "data": data,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(api_url, json=payload)
            result = resp.json()
        if result.get("errcode") == 0:
            return True
        logger.warning(f"WeChat template send error: {result}")
    except Exception as e:
        logger.warning(f"WeChat template send failed: {e}")
    return False


# ─── JSSDK ────────────────────────────────────────

async def get_jsapi_ticket() -> Optional[str]:
    """Get JSSDK ticket (cached 7200s)."""
    now = time.time()
    if _ticket_cache["ticket"] and _ticket_cache["expires_at"] > now + 60:
        return _ticket_cache["ticket"]

    token = await _get_access_token()
    if not token:
        return None
    url = f"{_BASE}/cgi-bin/ticket/getticket?access_token={token}&type=jsapi"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
        if data.get("errcode") == 0:
            _ticket_cache["ticket"] = data["ticket"]
            _ticket_cache["expires_at"] = now + data.get("expires_in", 7200)
            return data["ticket"]
    except Exception as e:
        logger.warning(f"WeChat JSAPI ticket failed: {e}")
    return None


async def sign_jsapi(page_url: str) -> Optional[dict]:
    """Generate JSSDK config signature for wx.config()."""
    ticket = await get_jsapi_ticket()
    if not ticket:
        return None
    nonce = uuid.uuid4().hex[:16]
    timestamp = str(int(time.time()))
    raw = f"jsapi_ticket={ticket}&noncestr={nonce}&timestamp={timestamp}&url={page_url}"
    signature = hashlib.sha1(raw.encode()).hexdigest()
    return {
        "appId": WECHAT_APP_ID,
        "timestamp": timestamp,
        "nonceStr": nonce,
        "signature": signature,
    }
