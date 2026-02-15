# -*- coding: utf-8 -*-
"""日志脱敏工具 (FIX-15)"""


def mask_username(username: str) -> str:
    """admin → ad***n"""
    if not username:
        return "***"
    if len(username) <= 2:
        return username[0] + "*"
    return username[:2] + "***" + username[-1]


def mask_email(email: str) -> str:
    """user@example.com → us***r@ex***e.com"""
    if not email or "@" not in email:
        return "***"
    local, domain = email.rsplit("@", 1)
    return mask_username(local) + "@" + mask_username(domain)


def mask_ip(ip: str) -> str:
    """192.168.1.100 → 192.168.***.100"""
    if not ip:
        return "***"
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.{parts[3]}"
    return ip[:4] + "***"
