# -*- coding: utf-8 -*-
"""
高频题目查询 API
High-Frequency Question API

端点:
- GET /api/v1/high-freq-questions/presets  — 列出可用预设
- GET /api/v1/high-freq-questions/all      — 获取所有171题（自选模式）
- GET /api/v1/high-freq-questions/by-ids   — 根据ID列表获取题目（行为评估模式）
- GET /api/v1/high-freq-questions/{preset} — 获取某预设的完整题目列表
"""
import os
import sys
from typing import List
from fastapi import APIRouter, HTTPException, Query

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.high_freq_question_service import HighFreqQuestionService

router = APIRouter(prefix="/api/v1/high-freq-questions", tags=["高频题目"])

service = HighFreqQuestionService()


@router.get("/presets")
async def list_presets():
    """列出可用的高频题目预设"""
    return {"presets": service.get_presets()}


@router.get("/all")
async def get_all_questions():
    """获取所有171题（供自选模式使用）"""
    questions = service.get_all_questions()
    return {"questions": questions, "total": len(questions)}


@router.get("/by-ids")
async def get_questions_by_ids(ids: List[str] = Query(..., description="题目ID列表")):
    """根据题目ID列表获取完整题目信息"""
    questions = service.get_questions_by_ids(ids)
    return {"questions": questions, "total": len(questions)}


@router.get("/{preset}")
async def get_preset_items(preset: str):
    """获取某预设的完整题目列表（含题目文本+选项）"""
    items = service.get_preset_items(preset)
    if not items:
        raise HTTPException(status_code=404, detail=f"预设 '{preset}' 不存在或为空")
    return {"preset": preset, "items": items, "total": len(items)}
