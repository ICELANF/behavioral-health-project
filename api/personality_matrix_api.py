# -*- coding: utf-8 -*-
"""
动机 x 人格 双维度处方匹配 API

端点:
    GET  /api/v1/personality-matrix/motivation-types    动机类型列表
    GET  /api/v1/personality-matrix/archetypes          人格原型列表
    POST /api/v1/personality-matrix/classify             分类 + 返回处方策略
    POST /api/v1/personality-matrix/strategy             指定 P/M 查处方
"""

import logging
from typing import Optional

from fastapi import APIRouter, Body
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/personality-matrix",
    tags=["Personality Matrix"],
)


class ClassifyRequest(BaseModel):
    big5_scores: dict  # {"E": int, "N": int, "C": int, "A": int, "O": int}
    motivation_keywords: list[str] = []  # 用户回答关键词
    motivation_type: Optional[str] = None  # 直接指定 M1-M5 (优先)


class StrategyRequest(BaseModel):
    personality_type: str  # P1-P5
    motivation_type: str   # M1-M5


@router.get("/motivation-types")
async def get_motivation_types():
    """返回 5 种动机类型定义"""
    from core.personality_matrix import get_motivation_types
    return {"types": get_motivation_types()}


@router.get("/archetypes")
async def get_archetypes():
    """返回 5 种人格原型定义"""
    from core.personality_matrix import get_personality_archetypes
    return {"archetypes": get_personality_archetypes()}


@router.post("/classify")
async def classify_and_match(req: ClassifyRequest):
    """
    根据大五得分 + 动机关键词，自动分类并返回处方策略

    入参:
        big5_scores: {"E": 24, "N": -31, "C": 2, "A": -3, "O": 5}
        motivation_keywords: ["健康", "家人"] 或 motivation_type: "M1"
    """
    from core.personality_matrix import (
        classify_personality, classify_motivation, get_prescription_strategy,
        get_personality_archetypes, get_motivation_types,
    )

    p_type = classify_personality(req.big5_scores)
    m_type = req.motivation_type or classify_motivation(req.motivation_keywords)

    strategy = get_prescription_strategy(p_type, m_type)

    archetypes = get_personality_archetypes()
    motiv_types = get_motivation_types()

    return {
        "personality_type": p_type,
        "personality_name": archetypes.get(p_type, {}).get("name", ""),
        "personality_desc": archetypes.get(p_type, {}).get("desc", ""),
        "motivation_type": m_type,
        "motivation_name": motiv_types.get(m_type, {}).get("name", ""),
        "strategy": strategy,
    }


@router.post("/strategy")
async def get_strategy(req: StrategyRequest):
    """直接查询指定 P x M 组合的处方策略"""
    from core.personality_matrix import get_prescription_strategy
    strategy = get_prescription_strategy(req.personality_type, req.motivation_type)
    if not strategy:
        return {"error": f"No strategy for {req.personality_type} x {req.motivation_type}"}
    return {"strategy": strategy}
