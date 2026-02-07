# -*- coding: utf-8 -*-
"""
内容等级门控服务

根据用户角色等级控制内容访问权限：
- 每条内容有对应等级要求（L0~L5）
- 用户等级 >= 内容等级即可访问
- 不满足则返回锁定状态 + 解锁提示
"""

from core.models import User, UserRole


# 角色→等级数字映射（复用 UserRole 枚举）
ROLE_LEVEL_MAP = {
    "observer": 0,
    "grower": 1,
    "sharer": 2,
    "coach": 3,
    "promoter": 4,
    "supervisor": 4,
    "master": 5,
    "admin": 99,
}

# 等级代码→数字映射
LEVEL_CODE_MAP = {
    "L0": 0,
    "L1": 1,
    "L2": 2,
    "L3": 3,
    "L4": 4,
    "L5": 5,
}

# 等级标签
LEVEL_LABELS = {
    0: "观察员",
    1: "成长者",
    2: "分享者",
    3: "教练",
    4: "促进师",
    5: "大师",
}


def get_user_level(user: User) -> int:
    """从 User 对象获取等级数字"""
    if user and user.role:
        role_str = user.role.value if isinstance(user.role, UserRole) else str(user.role)
        return ROLE_LEVEL_MAP.get(role_str, 0)
    return 0


def level_code_to_int(level_code: str) -> int:
    """将 L0~L5 等级代码转为数字，无效值返回 0"""
    return LEVEL_CODE_MAP.get(level_code, 0)


def can_access_content(user_level: int, content_level: str) -> bool:
    """检查用户是否有权访问指定等级内容"""
    required = level_code_to_int(content_level)
    return user_level >= required


def get_access_status(user_level: int, content_level: str) -> dict:
    """
    返回内容访问状态

    Returns:
        {
            "accessible": bool,
            "reason": str | None,
            "unlock_level": str | None,      # e.g. "L2"
            "unlock_level_label": str | None, # e.g. "分享者"
        }
    """
    required = level_code_to_int(content_level)
    if user_level >= required:
        return {
            "accessible": True,
            "reason": None,
            "unlock_level": None,
            "unlock_level_label": None,
        }

    unlock_label = LEVEL_LABELS.get(required, content_level)
    return {
        "accessible": False,
        "reason": f"需完成{content_level} {unlock_label}才能解锁",
        "unlock_level": content_level,
        "unlock_level_label": unlock_label,
    }
