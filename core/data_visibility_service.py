# -*- coding: utf-8 -*-
"""
字段级数据可见性过滤

根据查看者的等级控制行为画像字段的可见性：
- L3 教练：可见 TTM阶段、BPT6、SPI、CAPACITY、风险等级
-           不可见 Big5原始分、心理健康标记
- L4 促进师：同L3
- L5 大师：全部字段
- L99 管理员：全部字段
"""

from core.content_access_service import get_user_level
from core.models import User

# 字段可见性规则: min_level 表示需要 >= 该等级才可查看 (1-indexed: coach=4, master=6)
FIELD_VISIBILITY = {
    "big5_scores": {"min_level": 6, "label": "Big5人格原始分"},          # L5 大师
    "big5_raw": {"min_level": 6, "label": "Big5人格原始分"},              # L5 大师
    "psychological_level": {"min_level": 6, "label": "心理健康层级"},      # L5 大师
    "psychological_level_label": {"min_level": 6, "label": "心理健康层级标签"},  # L5 大师
    "risk_flags": {"min_level": 4, "label": "风险标记"},                  # L3 教练
    "spi_score": {"min_level": 4, "label": "SPI分数"},                    # L3 教练
    "bpt6_type": {"min_level": 4, "label": "行为类型"},                   # L3 教练
    "bpt6_scores": {"min_level": 4, "label": "行为类型分数"},              # L3 教练
    "capacity_weak": {"min_level": 4, "label": "改变能力薄弱项"},          # L3 教练
    "capacity_strong": {"min_level": 4, "label": "改变能力优势项"},        # L3 教练
    "capacity_dimensions": {"min_level": 4, "label": "改变能力维度"},      # L3 教练
    "capacity_total": {"min_level": 4, "label": "改变能力总分"},           # L3 教练
}


def filter_profile_fields(profile_dict: dict, viewer_level: int) -> dict:
    """
    根据查看者等级过滤行为画像字段

    Args:
        profile_dict: 行为画像字典数据
        viewer_level: 查看者等级数字 (0~99)

    Returns:
        过滤后的字典，被限制的字段值设为 None
    """
    if not profile_dict:
        return profile_dict

    filtered = dict(profile_dict)

    for field_name, rules in FIELD_VISIBILITY.items():
        if field_name in filtered and viewer_level < rules["min_level"]:
            filtered[field_name] = None

    return filtered


def filter_nested_profile(data: dict, viewer_level: int) -> dict:
    """
    过滤嵌套结构中的行为画像数据

    处理 behavioral_profile 这种嵌套 key 的情况
    """
    if not data:
        return data

    result = dict(data)

    # 直接过滤顶层
    result = filter_profile_fields(result, viewer_level)

    # 过滤 behavioral_profile 子对象
    if "behavioral_profile" in result and isinstance(result["behavioral_profile"], dict):
        result["behavioral_profile"] = filter_profile_fields(
            result["behavioral_profile"], viewer_level
        )

    return result


def get_hidden_fields(viewer_level: int) -> list:
    """
    获取对当前等级隐藏的字段列表

    Returns:
        [{"field": "big5_scores", "label": "Big5人格原始分", "min_level": 5}, ...]
    """
    hidden = []
    for field_name, rules in FIELD_VISIBILITY.items():
        if viewer_level < rules["min_level"]:
            hidden.append({
                "field": field_name,
                "label": rules["label"],
                "min_level": rules["min_level"],
            })
    return hidden
