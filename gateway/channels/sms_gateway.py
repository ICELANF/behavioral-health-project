"""
Aliyun SMS Gateway — raw HTTP + HMAC (no heavy SDK).
Graceful no-op when not configured.
"""
import hashlib
import hmac
import base64
import os
import time
import uuid
from urllib.parse import quote

import httpx
from loguru import logger

ALIYUN_ACCESS_KEY_ID = os.getenv("ALIYUN_SMS_ACCESS_KEY_ID", "")
ALIYUN_ACCESS_KEY_SECRET = os.getenv("ALIYUN_SMS_ACCESS_KEY_SECRET", "")
ALIYUN_SMS_SIGN_NAME = os.getenv("ALIYUN_SMS_SIGN_NAME", "")

_SMS_ENDPOINT = "https://dysmsapi.aliyuncs.com"


def is_configured() -> bool:
    return bool(ALIYUN_ACCESS_KEY_ID and ALIYUN_ACCESS_KEY_SECRET and ALIYUN_SMS_SIGN_NAME)


def _percent_encode(s: str) -> str:
    return quote(str(s), safe="").replace("+", "%20").replace("*", "%2A").replace("%7E", "~")


def _sign(params: dict) -> str:
    """Compute Aliyun API HMAC-SHA1 signature."""
    sorted_qs = "&".join(f"{_percent_encode(k)}={_percent_encode(params[k])}" for k in sorted(params))
    string_to_sign = f"GET&{_percent_encode('/')}&{_percent_encode(sorted_qs)}"
    h = hmac.new(
        (ALIYUN_ACCESS_KEY_SECRET + "&").encode(),
        string_to_sign.encode(),
        hashlib.sha1,
    )
    return base64.b64encode(h.digest()).decode()


async def send_sms(phone: str, template_code: str, params: dict) -> bool:
    """
    Send SMS via Aliyun.

    Args:
        phone: Mobile number (e.g. "13800138000")
        template_code: Aliyun template code (e.g. "SMS_123456")
        params: Template variables (e.g. {"code": "123456"})

    Returns True on success.
    """
    if not is_configured():
        logger.debug("SMS gateway not configured, skipping")
        return False

    import json
    common = {
        "AccessKeyId": ALIYUN_ACCESS_KEY_ID,
        "Action": "SendSms",
        "Format": "JSON",
        "PhoneNumbers": phone,
        "RegionId": "cn-hangzhou",
        "SignName": ALIYUN_SMS_SIGN_NAME,
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": uuid.uuid4().hex,
        "SignatureVersion": "1.0",
        "TemplateCode": template_code,
        "TemplateParam": json.dumps(params, ensure_ascii=False),
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "Version": "2017-05-25",
    }
    common["Signature"] = _sign(common)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(_SMS_ENDPOINT, params=common)
            data = resp.json()
        if data.get("Code") == "OK":
            logger.info(f"SMS sent: phone={phone[-4:]}, tpl={template_code}")
            return True
        logger.warning(f"SMS error: {data}")
    except Exception as e:
        logger.warning(f"SMS send failed: {e}")
    return False
