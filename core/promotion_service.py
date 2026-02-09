# -*- coding: utf-8 -*-
"""
晋级校验服务

校验用户是否满足晋级条件:
- 学分 (总/必修/M1-M4/选修)
- 积分 (growth/contribution/influence)
- 同道者 (毕业数/质量分)
- 实践 (标记为人工审核)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text, func
from loguru import logger

from core.models import (
    User, UserRole, ROLE_LEVEL,
    CompanionRelation, UserCredit, CourseModule,
)


# 加载晋级规则
_rules_path = Path(__file__).parent.parent / "configs" / "promotion_rules.json"
_RULES: Dict = {}
if _rules_path.exists():
    with open(_rules_path, "r", encoding="utf-8") as f:
        _RULES = json.load(f)


def _get_applicable_rule(current_role: str) -> Optional[Dict]:
    """获取当前角色的晋级规则"""
    role_str = current_role.lower()
    for rule in _RULES.get("rules", []):
        if rule["from_role"] == role_str:
            return rule
    return None


def _check_credits(db: Session, user_id: int, rule: Dict) -> Dict[str, Any]:
    """校验学分维度"""
    credit_req = rule.get("credits", {})

    # 从视图获取学分汇总
    row = db.execute(
        sa_text("SELECT * FROM v_user_total_credits WHERE user_id = :uid"),
        {"uid": user_id}
    ).mappings().first()

    if not row:
        current = {
            "total_credits": 0, "mandatory_credits": 0, "elective_credits": 0,
            "m1_credits": 0, "m2_credits": 0, "m3_credits": 0, "m4_credits": 0
        }
    else:
        current = dict(row)

    checks = {}
    fields = [
        ("total_min", "total_credits"),
        ("mandatory_min", "mandatory_credits"),
        ("m1_min", "m1_credits"),
        ("m2_min", "m2_credits"),
        ("m3_min", "m3_credits"),
        ("m4_min", "m4_credits"),
        ("elective_min", "elective_credits"),
    ]
    passed = True
    for req_key, cur_key in fields:
        req_val = credit_req.get(req_key, 0)
        cur_val = float(current.get(cur_key, 0) or 0)
        ok = cur_val >= req_val
        checks[req_key] = {"required": req_val, "current": cur_val, "passed": ok}
        if not ok:
            passed = False

    return {"passed": passed, "checks": checks}


def _check_points(db: Session, user_id: int, rule: Dict) -> Dict[str, Any]:
    """校验积分维度"""
    point_req = rule.get("points", {})

    # 从视图获取积分进度
    row = db.execute(
        sa_text("SELECT * FROM v_promotion_progress WHERE user_id = :uid"),
        {"uid": user_id}
    ).mappings().first()

    if not row:
        current = {"growth_points": 0, "contribution_points": 0, "influence_points": 0}
    else:
        current = dict(row)

    checks = {}
    fields = [
        ("growth_min", "growth_points"),
        ("contribution_min", "contribution_points"),
        ("influence_min", "influence_points"),
    ]
    passed = True
    for req_key, cur_key in fields:
        req_val = point_req.get(req_key, 0)
        cur_val = float(current.get(cur_key, 0) or 0)
        ok = cur_val >= req_val
        checks[req_key] = {"required": req_val, "current": cur_val, "passed": ok}
        if not ok:
            passed = False

    return {"passed": passed, "checks": checks}


def _check_companions(db: Session, user_id: int, rule: Dict) -> Dict[str, Any]:
    """校验同道者维度"""
    comp_req = rule.get("companions", {})
    graduated_min = comp_req.get("graduated_min", 0)
    quality_min = comp_req.get("quality_min")

    # 从视图获取统计
    row = db.execute(
        sa_text("SELECT * FROM v_companion_stats WHERE mentor_id = :mid"),
        {"mid": user_id}
    ).mappings().first()

    if not row:
        graduated = 0
        avg_quality = None
    else:
        graduated = int(row.get("graduated_count", 0) or 0)
        avg_quality = float(row["companion_avg_quality"]) if row.get("companion_avg_quality") else None

    checks = {
        "graduated_min": {
            "required": graduated_min,
            "current": graduated,
            "passed": graduated >= graduated_min,
        }
    }

    passed = checks["graduated_min"]["passed"]

    if quality_min is not None:
        quality_ok = avg_quality is not None and avg_quality >= quality_min
        checks["quality_min"] = {
            "required": quality_min,
            "current": avg_quality,
            "passed": quality_ok,
        }
        if not quality_ok:
            passed = False

    return {"passed": passed, "checks": checks}


def _check_practice(rule: Dict) -> Dict[str, Any]:
    """实践维度 — 标记为人工审核"""
    practice_req = rule.get("practice", {})
    return {
        "passed": None,  # None = 需人工审核
        "requires_manual_review": True,
        "criteria": practice_req,
    }


def check_promotion_eligibility(
    db: Session, user: User
) -> Tuple[bool, Dict[str, Any]]:
    """
    检查用户晋级资格

    Returns:
        (eligible, result_dict)
        eligible: True/False/None (None=需人工审核实践维度)
    """
    current_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    rule = _get_applicable_rule(current_role)

    if not rule:
        return False, {
            "eligible": False,
            "error": "当前角色无可用晋级路径",
            "from_role": current_role,
        }

    credit_result = _check_credits(db, user.id, rule)
    point_result = _check_points(db, user.id, rule)
    companion_result = _check_companions(db, user.id, rule)
    practice_result = _check_practice(rule)

    # 学分+积分+同道者 三个自动维度都通过
    auto_passed = all([
        credit_result["passed"],
        point_result["passed"],
        companion_result["passed"],
    ])

    result = {
        "from_role": rule["from_role"],
        "to_role": rule["to_role"],
        "display": rule.get("display", ""),
        "credits": credit_result,
        "points": point_result,
        "companions": companion_result,
        "practice": practice_result,
        "auto_checks_passed": auto_passed,
        "eligible": auto_passed,  # 实践维度需人工确认
    }

    return auto_passed, result
