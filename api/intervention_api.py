# -*- coding: utf-8 -*-
"""
干预包管理 API (只读，数据来自 configs/intervention_packs.json)

端点:
- GET  /api/v1/interventions              — 列表（支持 domain/coach_level 筛选）
- GET  /api/v1/interventions/match        — 匹配（trigger_tag + behavior_stage + coach_level）
- GET  /api/v1/interventions/{pack_id}    — 详情
"""
import os
import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

router = APIRouter(prefix="/api/v1/interventions", tags=["干预包"])

# ── 加载干预包配置 ──
_PACKS: List[dict] = []
_config_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "configs", "intervention_packs.json"
)
try:
    with open(_config_path, "r", encoding="utf-8") as f:
        _PACKS = json.load(f)
    print(f"[API] 已加载 {len(_PACKS)} 个干预包配置")
except Exception as e:
    print(f"[API] 加载干预包配置失败: {e}")

# 教练等级顺序
_LEVEL_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}


def _level_gte(user_level: str, required_level: str) -> bool:
    """判断 user_level >= required_level"""
    return _LEVEL_ORDER.get(user_level, 0) >= _LEVEL_ORDER.get(required_level, 0)


@router.get("/match")
async def match_interventions(
    trigger_tag: str = Query(..., description="触发标签"),
    behavior_stage: str = Query(..., description="行为阶段"),
    coach_level: Optional[str] = Query(None, description="教练等级"),
    risk_level: Optional[str] = Query(None, description="风险等级"),
):
    """根据触发标签和行为阶段匹配干预包，返回 MatchResult 列表"""
    results = []
    for pack in _PACKS:
        if not pack.get("is_active", True):
            continue
        # 触发标签匹配
        if trigger_tag not in pack.get("trigger_tags", []):
            continue
        # 行为阶段匹配
        if behavior_stage not in pack.get("applicable_stages", []):
            continue
        # 风险等级匹配（可选）
        if risk_level and risk_level not in pack.get("risk_levels", []):
            continue

        # 判断教练等级是否足够
        can_execute = True
        reason = None
        if coach_level:
            required = pack.get("coach_level_min", "L0")
            if not _level_gte(coach_level, required):
                can_execute = False
                reason = f"需要 {required} 及以上等级，当前为 {coach_level}"

        # 筛选匹配的教练动作（按行为阶段过滤）
        matched_actions = []
        for action in pack.get("coach_actions", []):
            action_stages = action.get("behavior_stage", [])
            if not action_stages or behavior_stage in action_stages:
                matched_actions.append(action)

        results.append({
            "pack": pack,
            "matchedActions": matched_actions,
            "canExecute": can_execute,
            "reason": reason,
        })

    # 按优先级排序
    results.sort(key=lambda r: r["pack"].get("priority", 99))
    return results


@router.get("/{pack_id}")
async def get_intervention_pack(pack_id: str):
    """获取单个干预包详情"""
    for pack in _PACKS:
        if pack.get("pack_id") == pack_id:
            return pack
    raise HTTPException(status_code=404, detail="干预包不存在")


@router.get("")
async def list_intervention_packs(
    domain: Optional[str] = Query(None, description="触发域筛选"),
    coach_level: Optional[str] = Query(None, description="教练等级筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
):
    """获取干预包列表"""
    result = []
    for pack in _PACKS:
        if is_active is not None and pack.get("is_active") != is_active:
            continue
        if domain and pack.get("trigger_domain") != domain:
            continue
        if coach_level and not _level_gte(coach_level, pack.get("coach_level_min", "L0")):
            continue
        result.append(pack)
    return result
