# -*- coding: utf-8 -*-
"""
内容等级门控服务

根据用户角色等级控制内容访问权限：
- 每条内容有对应等级要求（L0~L5）
- 用户等级 >= 内容等级即可访问
- 不满足则返回锁定状态 + 解锁提示
"""

from core.models import User, UserRole


# 引用 models.py 权威定义（1-indexed: observer=1 ... master=6）
from core.models import ROLE_LEVEL as _ROLE_LEVEL, ROLE_LEVEL_STR as ROLE_LEVEL_MAP

# 等级代码→数字映射（与 1-indexed 对齐）
LEVEL_CODE_MAP = {
    "L0": 1,
    "L1": 2,
    "L2": 3,
    "L3": 4,
    "L4": 5,
    "L5": 6,
}

# 等级标签（1-indexed key）
LEVEL_LABELS = {
    1: "观察员",
    2: "成长者",
    3: "分享者",
    4: "教练",
    5: "促进师",
    6: "大师",
}


def get_user_level(user: User) -> int:
    """从 User 对象获取等级数字（1-indexed）"""
    if user and user.role:
        role_str = user.role.value if isinstance(user.role, UserRole) else str(user.role)
        return ROLE_LEVEL_MAP.get(role_str, 1)
    return 1


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
