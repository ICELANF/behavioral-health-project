"""
V4.0 双轨晋级引擎 — Dual-Track Promotion Engine

Sheet ④ 核心逻辑:
  晋级 = 积分轨达标(门槛) ∧ 成长轨验证通过(判定)

四种状态:
  状态1 正常成长 (normal_growth):    积分未达标 + 成长未验证
  状态2 等待验证 (waiting_verify):   积分达标 + 成长未过
  状态3 成长先到 (growth_first):     积分未达 + 成长通过
  状态4 晋级就绪 (promotion_ready):  双轨均达标

固化话术 (从Sheet ④):
  状态1: 你正在成长的路上, 每一步都有价值。继续保持!
  状态2: 您的活跃度已经达标! 接下来需要完成成长验证。
  状态3: 太棒了! 您的能力已经得到验证。继续日常活动很快就能达标。
  状态4: 恭喜! 您已满足全部晋级条件! 准备好仪式了吗?
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from core.models import (
    User, UserRole, ROLE_LEVEL, ROLE_LEVEL_STR,
    DualTrackStatus, CompanionRelation, UserCredit,
)

logger = logging.getLogger(__name__)

# ── Points Track Thresholds (Sheet ④/⑪) ──────────────────
POINTS_THRESHOLDS = {
    # target_level: {growth, contribution, influence}
    2: {"growth": 100, "contribution": 0, "influence": 0},           # L0→L1
    3: {"growth": 300, "contribution": 50, "influence": 0},          # L1→L2 (非硬性)
    4: {"growth": 800, "contribution": 100, "influence": 0},         # L2→L3
    5: {"growth": 1500, "contribution": 500, "influence": 200},      # L3→L4
    6: {"growth": 3000, "contribution": 1500, "influence": 800},     # L4→L5
}

# ── Growth Track Requirements (Sheet ④/⑪) ─────────────────
GROWTH_REQUIREMENTS = {
    2: {  # L0→L1
        "companions": {"count": 4, "quality": "2人开始行为尝试"},
        "behavior": "S0-S4全阶段完成, 1项行为稳定90天",
        "assessment": "基础课程20学时, 行为链测评通过",
        "label": "破壳者",
        "emoji": "🐣",
    },
    3: {  # L1→L2
        "companions": {"count": 4, "quality": "2人完成S0-S3, 1人达S4"},
        "behavior": "陪伴时长≥50h, 正确转介≥3个",
        "assessment": "分享者培训40学时, 伦理边界测试100%",
        "label": "传灯者",
        "emoji": "🕯️",
        "note": "积分非硬性门槛, 核心=自愿意愿+贡献行为证明",
    },
    4: {  # L2→L3
        "companions": {"count": 4, "quality": "2人通过考核, 1人具备教练潜力"},
        "behavior": "独立≥10案例, ≥3人S0-S4跃迁",
        "assessment": "400分制≥240: 理论≥90, 技能≥90, 综合≥60, 伦理100%",
        "label": "持杖者",
        "emoji": "🪄",
    },
    5: {  # L3→L4
        "companions": {"count": 4, "quality": "2人独立执业, 1人项目负责人"},
        "behavior": "≥2组织级项目, 服务≥100人",
        "assessment": "促进师认证考试, 高级伦理测试, 方案设计答辩",
        "label": "立柱者",
        "emoji": "🏛️",
    },
    6: {  # L4→L5
        "companions": {"count": 4, "quality": "2人区域标杆, 1人大师潜力"},
        "behavior": "促进师≥24月, 带教≥15名L3+≥4名L4",
        "assessment": "大师认证考试, 方法论同行评审, 专家委员会全票",
        "label": "归源者",
        "emoji": "🌊",
    },
}

# ── Status Messages (固化话术) ────────────────────────────
STATUS_MESSAGES = {
    "normal_growth": "你正在成长的路上, 每一步都有价值。继续保持!",
    "waiting_verify": "您的活跃度已经达标! 接下来需要完成以下成长验证——"
                      "这些验证确保您不仅做了很多, 而且真正成长为下一级所需要的人。",
    "growth_first": "太棒了! 您的能力已经得到验证。"
                    "积分只是确保您有足够的平台参与度, 继续日常活动很快就能达到。",
    "promotion_ready": "恭喜! 您已满足全部晋级条件! 准备好仪式了吗?",
}


class DualTrackEngine:
    """双轨晋级引擎"""

    def __init__(self, db: Session):
        self.db = db

    def check_dual_track(self, user_id: int) -> dict:
        """检查用户的双轨晋级状态"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "用户不存在"}

        current_role = user.role.value if hasattr(user.role, 'value') else user.role
        current_level = ROLE_LEVEL_STR.get(current_role, 1)
        target_level = current_level + 1

        if target_level > 6:
            return {
                "user_id": user_id,
                "current_level": current_level,
                "status": "max_level",
                "message": "已达最高级别",
            }

        # Check points track
        points_result = self._check_points_track(user_id, target_level)

        # Check growth track
        growth_result = self._check_growth_track(user_id, target_level)

        # Determine status
        pts_passed = points_result["passed"]
        grw_passed = growth_result["passed"]

        if pts_passed and grw_passed:
            status = "promotion_ready"
        elif pts_passed and not grw_passed:
            status = "waiting_verify"
        elif not pts_passed and grw_passed:
            status = "growth_first"
        else:
            status = "normal_growth"

        # Update or create dual track status record
        dts = self.db.query(DualTrackStatus).filter(
            DualTrackStatus.user_id == user_id,
            DualTrackStatus.target_level == target_level,
        ).first()
        if not dts:
            dts = DualTrackStatus(user_id=user_id, target_level=target_level)
            self.db.add(dts)

        dts.points_track_passed = pts_passed
        dts.growth_track_passed = grw_passed
        dts.status = status
        dts.gap_analysis = {
            "points": points_result.get("gaps", {}),
            "growth": growth_result.get("gaps", {}),
        }
        if pts_passed:
            dts.points_checked_at = datetime.utcnow()
        if grw_passed:
            dts.growth_checked_at = datetime.utcnow()
        self.db.flush()

        req = GROWTH_REQUIREMENTS.get(target_level, {})
        return {
            "user_id": user_id,
            "current_level": current_level,
            "current_role": current_role,
            "target_level": target_level,
            "target_label": req.get("label", ""),
            "target_emoji": req.get("emoji", ""),
            "status": status,
            "message": STATUS_MESSAGES[status],
            "points_track": points_result,
            "growth_track": growth_result,
        }

    def _check_points_track(self, user_id: int, target_level: int) -> dict:
        """检查积分轨"""
        thresholds = POINTS_THRESHOLDS.get(target_level, {})
        if not thresholds:
            return {"passed": True, "gaps": {}}

        # Get user's current points
        from core.models import UserPoint
        user_points = self.db.query(UserPoint).filter(
            UserPoint.user_id == user_id
        ).first()

        current = {
            "growth": user_points.growth_points if user_points else 0,
            "contribution": user_points.contribution_points if user_points else 0,
            "influence": user_points.influence_points if user_points else 0,
        }

        gaps = {}
        passed = True
        for dim, required in thresholds.items():
            if required > 0:
                actual = current.get(dim, 0)
                if actual < required:
                    passed = False
                    gaps[dim] = {"current": actual, "required": required, "gap": required - actual}

        # L1→L2 special: points are not hard threshold
        if target_level == 3:
            passed = True  # Always pass for L1→L2 (advisory only)

        return {
            "passed": passed,
            "current": current,
            "thresholds": thresholds,
            "gaps": gaps,
            "advisory_only": target_level == 3,
        }

    def _check_growth_track(self, user_id: int, target_level: int) -> dict:
        """检查成长轨"""
        req = GROWTH_REQUIREMENTS.get(target_level, {})
        if not req:
            return {"passed": True, "gaps": {}}

        gaps = {}
        checks = {}

        # Check companions
        comp_req = req.get("companions", {})
        if comp_req:
            graduated_count = self.db.query(CompanionRelation).filter(
                CompanionRelation.mentor_id == user_id,
                CompanionRelation.status == "graduated",
            ).count()

            total_count = self.db.query(CompanionRelation).filter(
                CompanionRelation.mentor_id == user_id,
            ).count()

            comp_required = comp_req.get("count", 4)
            comp_passed = total_count >= comp_required
            checks["companions"] = {
                "passed": comp_passed,
                "total": total_count,
                "graduated": graduated_count,
                "required": comp_required,
                "quality_requirement": comp_req.get("quality", ""),
            }
            if not comp_passed:
                gaps["companions"] = f"需{comp_required}名同道者, 当前{total_count}名"

        # Check behavior/practice (requires manual verification)
        checks["behavior"] = {
            "passed": None,  # Requires manual review
            "requirement": req.get("behavior", ""),
            "note": "需教练/督导审核确认",
        }

        # Check assessment/certification (requires manual verification)
        checks["assessment"] = {
            "passed": None,  # Requires manual review
            "requirement": req.get("assessment", ""),
            "note": "需考试系统确认",
        }

        # Growth track passes only if companions met (other checks are manual)
        passed = checks.get("companions", {}).get("passed", False)

        return {
            "passed": passed,
            "checks": checks,
            "gaps": gaps,
            "label": req.get("label", ""),
            "note": req.get("note", ""),
        }

    def get_gap_analysis(self, user_id: int) -> dict:
        """生成详细差距分析报告"""
        result = self.check_dual_track(user_id)
        if "error" in result:
            return result

        gaps_list = []
        # Points gaps
        for dim, gap in result.get("points_track", {}).get("gaps", {}).items():
            gaps_list.append({
                "dimension": f"积分轨·{dim}",
                "current": gap["current"],
                "required": gap["required"],
                "gap": gap["gap"],
                "actionable": True,
            })

        # Growth gaps
        for key, msg in result.get("growth_track", {}).get("gaps", {}).items():
            gaps_list.append({
                "dimension": f"成长轨·{key}",
                "description": msg,
                "actionable": key == "companions",
            })

        return {
            "user_id": user_id,
            "status": result["status"],
            "message": result["message"],
            "target_level": result["target_level"],
            "target_label": result["target_label"],
            "gaps": gaps_list,
            "total_gaps": len(gaps_list),
        }
