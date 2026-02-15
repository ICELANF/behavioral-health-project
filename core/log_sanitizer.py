"""
日志脱敏工具 (FIX-15)
"""
import re


def mask_username(username: str) -> str:
    """用户名脱敏: admin → ad***n, ab → a*"""
    if not username:
        return "***"
    if len(username) <= 2:
        return username[0] + "*"
    return username[:2] + "***" + username[-1]


def mask_email(email: str) -> str:
    """邮箱脱敏: user@example.com → us***r@e***.com"""
    if not email or "@" not in email:
        return "***"
    local, domain = email.rsplit("@", 1)
    return mask_username(local) + "@" + mask_username(domain)


def mask_ip(ip: str) -> str:
    """IP脱敏: 192.168.1.100 → 192.168.*.100"""
    if not ip:
        return "***"
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.{parts[3]}"
    return ip[:4] + "***"


def sanitize_log(msg: str) -> str:
    """通用日志脱敏: 替换已知敏感模式"""
    # password= 后面的值
    msg = re.sub(r"(password[=:]\s*)(\S+)", r"***", msg, flags=re.I)
    # token= 后面的值
    msg = re.sub(r"(token[=:]\s*)(\S{10})\S+", r"...", msg, flags=re.I)
    return msg
