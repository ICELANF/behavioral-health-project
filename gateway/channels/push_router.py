"""
Unified push notification router.

Resolution order:
1. Explicit channel → use it
2. user.preferred_channel → use it
3. Cascade: wechat → sms → email → in-app only

Always writes in-app notification regardless of external channel success.
"""
from typing import Optional

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def send_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    body: str,
    channel: Optional[str] = None,
    template_data: Optional[dict] = None,
) -> dict:
    """
    Send a push notification via the best available channel.

    Returns: {"channel_used": str, "success": bool, "fallback": bool}
    """
    result = {"channel_used": "in_app", "success": True, "fallback": False}

    # Always write in-app notification
    try:
        await db.execute(
            text("""
                INSERT INTO notifications (user_id, title, body, type, priority, is_read, created_at)
                VALUES (:uid, :title, :body, 'push', 'normal', false, NOW())
            """),
            {"uid": user_id, "title": title, "body": body},
        )
    except Exception as e:
        logger.warning(f"In-app notification insert failed: {e}")
        result["success"] = False

    # Resolve user preferences
    try:
        row = await db.execute(
            text("SELECT wx_openid, phone, email, preferred_channel FROM users WHERE id = :uid"),
            {"uid": user_id},
        )
        user = row.mappings().first()
    except Exception:
        user = None

    if not user:
        return result

    # Determine target channel
    target = channel or user.get("preferred_channel") or None
    wx_openid = user.get("wx_openid")
    phone = user.get("phone")
    email = user.get("email")

    # Cascade logic
    channels_to_try = []
    if target == "wechat" and wx_openid:
        channels_to_try = ["wechat"]
    elif target == "sms" and phone:
        channels_to_try = ["sms"]
    elif target == "email" and email:
        channels_to_try = ["email"]
    elif target and target != "app":
        # Explicit channel but missing data, cascade
        channels_to_try = []
        if wx_openid:
            channels_to_try.append("wechat")
        if phone:
            channels_to_try.append("sms")
        if email:
            channels_to_try.append("email")
        result["fallback"] = True
    else:
        # Auto: try all available
        if wx_openid:
            channels_to_try.append("wechat")
        elif phone:
            channels_to_try.append("sms")
        elif email:
            channels_to_try.append("email")

    # Attempt external push
    for ch in channels_to_try:
        sent = False
        try:
            if ch == "wechat":
                from gateway.channels.wx_gateway import send_template_message
                tpl_data = template_data or {
                    "title": {"value": title},
                    "content": {"value": body[:200]},
                }
                sent = await send_template_message(
                    openid=wx_openid,
                    template_id="general_notice",
                    data=tpl_data,
                )
            elif ch == "sms":
                from gateway.channels.sms_gateway import send_sms
                sent = await send_sms(
                    phone=phone,
                    template_code="SMS_BHP_NOTIFY",
                    params={"title": title[:20], "content": body[:60]},
                )
            elif ch == "email":
                from gateway.channels.email_gateway import send_email
                sent = await send_email(
                    to=email,
                    subject=title,
                    body_html=f"<h3>{title}</h3><p>{body}</p>",
                )
        except Exception as e:
            logger.debug(f"Push via {ch} failed: {e}")

        if sent:
            result["channel_used"] = ch
            return result

    return result
