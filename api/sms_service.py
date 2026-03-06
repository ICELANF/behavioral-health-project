# -*- coding: utf-8 -*-
"""
短信验证码服务
api/sms_service.py

当前模式：MOCK（固定验证码 888888）
切换真实短信：设置环境变量 SMS_PROVIDER=aliyun，并配置对应 KEY
"""

import os
import random
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ── 配置 ──────────────────────────────────────────────
SMS_PROVIDER = os.getenv("SMS_PROVIDER", "mock")          # mock / aliyun / tencent
SMS_EXPIRE_MINUTES = int(os.getenv("SMS_EXPIRE_MINUTES", "5"))
SMS_MAX_ATTEMPTS = int(os.getenv("SMS_MAX_ATTEMPTS", "5"))
SMS_DAILY_LIMIT = int(os.getenv("SMS_DAILY_LIMIT", "10"))

# 阿里云短信配置（SMS_PROVIDER=aliyun 时生效）
ALIYUN_ACCESS_KEY_ID = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
ALIYUN_ACCESS_KEY_SECRET = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
ALIYUN_SMS_SIGN = os.getenv("ALIYUN_SMS_SIGN", "行健平台")
ALIYUN_SMS_TEMPLATE = os.getenv("ALIYUN_SMS_TEMPLATE", "SMS_xxxxxxx")

# MOCK 固定验证码（仅开发/测试环境）
MOCK_CODE = os.getenv("SMS_MOCK_CODE", "888888")


# ── 验证码生成 ─────────────────────────────────────────
def generate_code() -> str:
    """生成6位数字验证码"""
    if SMS_PROVIDER == "mock":
        return MOCK_CODE
    return str(random.randint(100000, 999999))


# ── 发送短信 ──────────────────────────────────────────
async def send_sms_code(phone: str, code: str, purpose: str = "register") -> bool:
    """
    发送短信验证码

    Args:
        phone: 手机号（11位）
        code: 验证码
        purpose: 用途 register/login/bind

    Returns:
        True=发送成功, False=失败
    """
    if SMS_PROVIDER == "mock":
        logger.info(f"[SMS MOCK] phone={phone} code={code} purpose={purpose}")
        return True

    elif SMS_PROVIDER == "aliyun":
        return await _send_aliyun(phone, code)

    else:
        logger.error(f"[SMS] 未知 provider: {SMS_PROVIDER}")
        return False


async def _send_aliyun(phone: str, code: str) -> bool:
    """阿里云短信发送（预留实现）"""
    try:
        # pip install alibabacloud-dysmsapi20170525
        from alibabacloud_dysmsapi20170525.client import Client
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_dysmsapi20170525 import models as dysms_models

        config = open_api_models.Config(
            access_key_id=ALIYUN_ACCESS_KEY_ID,
            access_key_secret=ALIYUN_ACCESS_KEY_SECRET,
            endpoint="dysmsapi.aliyuncs.com"
        )
        client = Client(config)
        request = dysms_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=ALIYUN_SMS_SIGN,
            template_code=ALIYUN_SMS_TEMPLATE,
            template_param=f'{{"code":"{code}"}}'
        )
        resp = client.send_sms(request)
        if resp.body.code == "OK":
            logger.info(f"[SMS Aliyun] 发送成功: {phone}")
            return True
        else:
            logger.error(f"[SMS Aliyun] 发送失败: {resp.body.message}")
            return False
    except Exception as e:
        logger.error(f"[SMS Aliyun] 异常: {e}")
        return False


# ── 数据库操作 ─────────────────────────────────────────
def save_code(db: Session, phone: str, code: str, purpose: str = "register"):
    """保存验证码到数据库（覆盖同手机号同用途的旧记录）"""
    from sqlalchemy import text

    # 让旧的同类验证码失效
    db.execute(text("""
        UPDATE sms_verification_codes
        SET is_used = true
        WHERE phone = :phone AND purpose = :purpose AND is_used = false
    """), {"phone": phone, "purpose": purpose})

    expires_at = datetime.utcnow() + timedelta(minutes=SMS_EXPIRE_MINUTES)

    db.execute(text("""
        INSERT INTO sms_verification_codes (phone, code, purpose, is_used, attempts, expires_at, created_at)
        VALUES (:phone, :code, :purpose, false, 0, :expires_at, now())
    """), {"phone": phone, "code": code, "purpose": purpose, "expires_at": expires_at})

    db.commit()


def verify_code(db: Session, phone: str, code: str, purpose: str = "register") -> tuple[bool, str]:
    """
    验证码校验

    Returns:
        (is_valid, error_message)
    """
    from sqlalchemy import text

    row = db.execute(text("""
        SELECT id, code, is_used, attempts, expires_at
        FROM sms_verification_codes
        WHERE phone = :phone AND purpose = :purpose AND is_used = false
        ORDER BY created_at DESC
        LIMIT 1
    """), {"phone": phone, "purpose": purpose}).fetchone()

    if not row:
        return False, "验证码不存在或已失效"

    if row.is_used:
        return False, "验证码已使用"

    if datetime.utcnow() > row.expires_at:
        return False, "验证码已过期"

    if row.attempts >= SMS_MAX_ATTEMPTS:
        return False, "验证码错误次数过多，请重新获取"

    if row.code != code:
        # 增加错误次数
        db.execute(text("""
            UPDATE sms_verification_codes SET attempts = attempts + 1 WHERE id = :id
        """), {"id": row.id})
        db.commit()
        remaining = SMS_MAX_ATTEMPTS - row.attempts - 1
        return False, f"验证码错误，还可尝试 {remaining} 次"

    # 验证成功，标记为已用
    db.execute(text("""
        UPDATE sms_verification_codes SET is_used = true WHERE id = :id
    """), {"id": row.id})
    db.commit()
    return True, ""


def check_daily_limit(db: Session, phone: str) -> bool:
    """检查今日发送次数是否超限"""
    from sqlalchemy import text

    result = db.execute(text("""
        SELECT COUNT(*) as cnt
        FROM sms_verification_codes
        WHERE phone = :phone AND created_at >= CURRENT_DATE
    """), {"phone": phone}).fetchone()

    return result.cnt < SMS_DAILY_LIMIT
