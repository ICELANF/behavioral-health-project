# -*- coding: utf-8 -*-
"""
动机 x 人格 双维度处方匹配服务

数据源: kms/motivation_personality_matrix.json
- 5 种动机类型 (M1-M5)
- 5 种人格原型 (P1-P5)
- 25 格处方策略矩阵

用法:
    from core.personality_matrix import get_prescription_strategy, classify_personality

    p_type = classify_personality({"E": 24, "N": -31, "C": 2, "A": -3, "O": 5})
    # => "P4" (社交领袖)

    strategy = get_prescription_strategy("P4", "M1")
    # => {"entry": "...", "prescription": "...", "format": "...", "caution": "...", "xzb_tone": "..."}
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_MATRIX_FILE = Path(__file__).resolve().parent.parent / "kms" / "motivation_personality_matrix.json"
_data: Optional[dict] = None


def _load():
    global _data
    if _data is not None:
        return _data
    with open(_MATRIX_FILE, encoding="utf-8") as f:
        _data = json.load(f)
    logger.info("Loaded motivation x personality matrix: %d motivation types, %d archetypes",
                len(_data.get("motivation_types", {})),
                len(_data.get("personality_archetypes", {})))
    return _data


def get_motivation_types() -> dict:
    """返回 5 种动机类型定义 (M1-M5)"""
    return _load()["motivation_types"]


def get_personality_archetypes() -> dict:
    """返回 5 种人格原型定义 (P1-P5)"""
    return _load()["personality_archetypes"]


def get_prescription_strategy(p_type: str, m_type: str) -> Optional[dict]:
    """
    根据人格原型 + 动机类型，返回处方策略

    Args:
        p_type: P1-P5 (稳定执行者/开放探索者/完美主义者/社交领袖/内向独立者)
        m_type: M1-M5 (健康守护/家庭责任/自由成就/平静安宁/意义探索)

    Returns:
        dict with keys: entry, prescription, format, caution, xzb_tone
        None if combination not found
    """
    matrix = _load().get("matrix", {})
    row = matrix.get(p_type)
    if not row:
        return None
    return row.get(m_type)


def classify_personality(scores: dict) -> str:
    """
    根据大五人格得分，分类到 P1-P5 原型

    Args:
        scores: {"E": int, "N": int, "C": int, "A": int, "O": int}

    Returns:
        "P1"-"P5" 原型编码
    """
    E = scores.get("E", 0)
    N = scores.get("N", 0)
    C = scores.get("C", 0)
    A = scores.get("A", 0)
    O = scores.get("O", 0)

    # P3: 完美主义者 — 高神经质 + (高尽责 或 高宜人)
    if N >= 8 and (C >= 15 or A >= 30):
        return "P3"

    # P1: 稳定执行者 — 高稳定 + 高尽责
    if N <= -15 and C >= 15:
        return "P1"

    # P4: 社交领袖 — 高外向 + 情绪稳定
    if E >= 15 and N <= -5:
        return "P4"

    # P2: 开放探索者 — 高开放 + 情绪稳定
    if O >= 15 and N <= -10:
        return "P2"

    # P5: 内向独立者 — 内向 + (低尽责 或 低宜人)
    if E <= -10:
        return "P5"

    # 默认: 按最突出维度
    if C >= 15:
        return "P1"
    if O >= 15:
        return "P2"
    if E >= 15:
        return "P4"

    return "P5"


def classify_motivation(keywords: list[str]) -> str:
    """
    根据用户输入关键词，匹配动机类型

    Args:
        keywords: 用户回答中提取的关键词列表

    Returns:
        "M1"-"M5" 动机编码
    """
    types = _load()["motivation_types"]
    scores = {}

    for m_id, m_def in types.items():
        triggers = m_def.get("trigger_keywords", [])
        score = sum(1 for kw in keywords if any(t in kw for t in triggers))
        scores[m_id] = score

    if not any(scores.values()):
        return "M1"  # 默认健康守护型

    return max(scores, key=scores.get)
