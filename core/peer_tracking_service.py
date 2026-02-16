"""
CR-28 修复: 同道者追踪系统补全
契约要求: ⑪教练体系管理 — 同道者追踪系统需≥2模式匹配
审计状态: ⚠️部分对齐(1/2) → ✅已对齐(2/2)
缺失模式: 同道者匹配算法 + 追踪生命周期管理

文件: core/peer_tracking_service.py (补丁)
      api/companion_api.py (补丁)
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session


# ═══════════════════════════════════════════════════════
# 模式2: 同道者匹配算法 + 生命周期管理
# (模式1: 基础CRUD已存在, 此为补全)
# ═══════════════════════════════════════════════════════

class CompanionMatchStrategy(str, Enum):
    """匹配策略"""
    STAGE_PROXIMITY = "stage_proximity"        # 阶段相近优先
    BEHAVIOR_SIMILARITY = "behavior_similarity" # 行为特征相似
    GOAL_ALIGNMENT = "goal_alignment"           # 目标一致性
    COMPLEMENTARY = "complementary"             # 互补型配对


class CompanionLifecycleState(str, Enum):
    """同道关系生命周期"""
    PENDING = "pending"           # 待确认
    ACTIVE = "active"             # 活跃中
    COOLING = "cooling"           # 冷却期(互动减少)
    DORMANT = "dormant"           # 休眠(>14天无互动)
    DISSOLVED = "dissolved"       # 已解除


class PeerTrackingService:
    """
    同道者追踪服务 — CR-28 补全实现

    核心能力:
    1. 多维匹配算法(阶段/行为/目标/互补)
    2. 生命周期状态机(pending→active→cooling→dormant→dissolved)
    3. 互动质量追踪(频次/深度/互惠性)
    4. 自动降级与重激活
    """

    # ── 匹配权重 ──
    MATCH_WEIGHTS = {
        "stage_distance": 0.30,       # 阶段距离(越近越好)
        "behavior_similarity": 0.25,  # BPT-6 行为类型相似度
        "goal_overlap": 0.25,         # 目标重叠度
        "activity_level": 0.10,       # 活跃度匹配
        "timezone_proximity": 0.10,   # 时区接近度
    }

    # ── 生命周期阈值 ──
    COOLING_THRESHOLD_DAYS = 7     # 7天无互动进入冷却
    DORMANT_THRESHOLD_DAYS = 14    # 14天无互动进入休眠
    AUTO_DISSOLVE_DAYS = 30        # 30天休眠自动解除

    def __init__(self, db: Session):
        self.db = db

    # ─────────────────────────────────────────────────
    # 匹配算法
    # ─────────────────────────────────────────────────
    def find_matches(
        self,
        user_id: int,
        strategy: CompanionMatchStrategy = CompanionMatchStrategy.STAGE_PROXIMITY,
        top_k: int = 5,
    ) -> list[dict]:
        """
        为用户寻找最佳同道者候选

        Returns: [{"user_id": int, "score": float, "reasons": [...]}]
        """
        from core.models import (
            User, JourneyStageV4, BehavioralStage,
            CompanionStatus, UserActivityLog,
        )

        # 获取当前用户画像
        user_profile = self._build_user_profile(user_id)
        if not user_profile:
            return []

        # 获取候选池: 同角色、活跃、非已配对
        existing_companions = self._get_existing_companion_ids(user_id)
        candidates = self.db.execute(
            select(User).where(
                and_(
                    User.is_active == True,
                    User.id != user_id,
                    User.id.notin_(existing_companions),
                    User.role.in_(["grower", "coach"]),
                )
            ).limit(100)
        )
        candidate_users = candidates.scalars().all()

        # 计算匹配分数
        scored = []
        for candidate in candidate_users:
            cand_profile = self._build_user_profile(candidate.id)
            if not cand_profile:
                continue
            score, reasons = self._compute_match_score(
                user_profile, cand_profile, strategy
            )
            scored.append({
                "user_id": candidate.id,
                "display_name": candidate.display_name or f"用户{candidate.id}",
                "score": round(score, 3),
                "reasons": reasons,
                "stage": cand_profile.get("stage", "unknown"),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _build_user_profile(self, user_id: int) -> Optional[dict]:
        """构建用户匹配画像"""
        from core.models import User, JourneyStageV4

        user = self.db.get(User, user_id)
        if not user:
            return None

        stage_result = self.db.execute(
            select(JourneyStageV4).where(
                JourneyStageV4.user_id == user_id
            ).order_by(JourneyStageV4.updated_at.desc()).limit(1)
        )
        stage = stage_result.scalar_one_or_none()

        return {
            "user_id": user_id,
            "stage": stage.current_stage if stage else "S0",
            "stage_numeric": self._stage_to_numeric(
                stage.current_stage if stage else "S0"
            ),
            "role": user.role,
            "bpt_type": getattr(user, "bpt_type", None),
            "goals": getattr(user, "goals", []) or [],
            "activity_score": self._get_activity_score(user_id),
        }

    def _stage_to_numeric(self, stage: str) -> int:
        mapping = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5}
        return mapping.get(stage, 0)

    def _get_activity_score(self, user_id: int) -> float:
        """近7天活跃度(0~1)"""
        from core.models import UserActivityLog
        window = datetime.utcnow() - timedelta(days=7)
        count = self.db.scalar(
            select(func.count(UserActivityLog.id)).where(
                and_(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.created_at >= window,
                )
            )
        )
        return min((count or 0) / 50.0, 1.0)  # 50次/周为满分

    def _get_existing_companion_ids(self, user_id: int) -> list[int]:
        from core.models import CompanionStatus
        result = self.db.execute(
            select(CompanionStatus.companion_id).where(
                and_(
                    CompanionStatus.user_id == user_id,
                    CompanionStatus.status.in_(["pending", "active", "cooling"]),
                )
            )
        )
        return [r[0] for r in result.all()]

    def _compute_match_score(
        self, profile_a: dict, profile_b: dict,
        strategy: CompanionMatchStrategy,
    ) -> tuple[float, list[str]]:
        """多维匹配打分"""
        scores = {}
        reasons = []
        w = self.MATCH_WEIGHTS

        # 阶段距离
        stage_diff = abs(profile_a["stage_numeric"] - profile_b["stage_numeric"])
        stage_score = max(0, 1.0 - stage_diff * 0.25)
        scores["stage_distance"] = stage_score
        if stage_score >= 0.75:
            reasons.append(f"阶段相近({profile_a['stage']}↔{profile_b['stage']})")

        # 行为类型相似度(BPT-6)
        bpt_a, bpt_b = profile_a.get("bpt_type"), profile_b.get("bpt_type")
        if bpt_a and bpt_b:
            bpt_score = 1.0 if bpt_a == bpt_b else 0.5
        else:
            bpt_score = 0.5  # 无数据时中性分
        scores["behavior_similarity"] = bpt_score
        if bpt_score >= 0.8:
            reasons.append("行为特征相似")

        # 目标重叠
        goals_a = set(profile_a.get("goals", []))
        goals_b = set(profile_b.get("goals", []))
        if goals_a and goals_b:
            overlap = len(goals_a & goals_b) / max(len(goals_a | goals_b), 1)
        else:
            overlap = 0.3
        scores["goal_overlap"] = overlap
        if overlap >= 0.5:
            reasons.append(f"目标重合{overlap:.0%}")

        # 活跃度匹配
        act_diff = abs(profile_a.get("activity_score", 0) -
                       profile_b.get("activity_score", 0))
        act_score = max(0, 1.0 - act_diff * 2)
        scores["activity_level"] = act_score

        # 时区(默认相同, 后续扩展)
        scores["timezone_proximity"] = 0.8

        # 策略加权
        if strategy == CompanionMatchStrategy.STAGE_PROXIMITY:
            w = {**w, "stage_distance": 0.50, "behavior_similarity": 0.15}
        elif strategy == CompanionMatchStrategy.BEHAVIOR_SIMILARITY:
            w = {**w, "behavior_similarity": 0.45, "stage_distance": 0.15}
        elif strategy == CompanionMatchStrategy.GOAL_ALIGNMENT:
            w = {**w, "goal_overlap": 0.45, "stage_distance": 0.15}

        total = sum(scores.get(k, 0) * v for k, v in w.items())
        if not reasons:
            reasons.append("综合匹配")
        return total, reasons

    # ─────────────────────────────────────────────────
    # 生命周期管理
    # ─────────────────────────────────────────────────
    def update_lifecycle_states(self) -> dict:
        """
        批量更新同道关系生命周期状态
        用于定时任务(每日执行)

        状态机: pending→active→cooling→dormant→dissolved
        """
        from core.models import CompanionStatus
        now = datetime.utcnow()
        stats = {"cooling": 0, "dormant": 0, "dissolved": 0, "reactivated": 0}

        # 获取所有活跃关系
        result = self.db.execute(
            select(CompanionStatus).where(
                CompanionStatus.status.in_(["active", "cooling", "dormant"])
            )
        )
        relationships = result.scalars().all()

        for rel in relationships:
            last_interaction = rel.last_interaction_at or rel.created_at
            days_silent = (now - last_interaction).days

            old_state = rel.status

            if rel.status == "active" and days_silent >= self.COOLING_THRESHOLD_DAYS:
                rel.status = "cooling"
                rel.state_changed_at = now
                stats["cooling"] += 1

            elif rel.status == "cooling" and days_silent >= self.DORMANT_THRESHOLD_DAYS:
                rel.status = "dormant"
                rel.state_changed_at = now
                stats["dormant"] += 1

            elif rel.status == "dormant" and days_silent >= self.AUTO_DISSOLVE_DAYS:
                rel.status = "dissolved"
                rel.dissolved_at = now
                rel.dissolve_reason = "auto_timeout"
                stats["dissolved"] += 1

            # 重激活: 有新互动则恢复
            elif rel.status in ("cooling", "dormant") and days_silent < self.COOLING_THRESHOLD_DAYS:
                rel.status = "active"
                rel.state_changed_at = now
                stats["reactivated"] += 1

        self.db.commit()
        return stats

    def record_interaction(
        self,
        user_id: int,
        companion_id: int,
        interaction_type: str = "message",
        quality_score: Optional[float] = None,
    ) -> bool:
        """
        记录同道互动 — 更新追踪指标

        interaction_type: message | reaction | challenge_collab | milestone_cheer
        quality_score: 0.0~1.0 (AI评估互动质量)
        """
        from core.models import CompanionStatus
        now = datetime.utcnow()

        result = self.db.execute(
            select(CompanionStatus).where(
                and_(
                    or_(
                        and_(CompanionStatus.user_id == user_id,
                             CompanionStatus.companion_id == companion_id),
                        and_(CompanionStatus.user_id == companion_id,
                             CompanionStatus.companion_id == user_id),
                    ),
                    CompanionStatus.status.in_(["active", "cooling", "dormant"]),
                )
            )
        )
        rel = result.scalar_one_or_none()
        if not rel:
            return False

        # 更新互动指标
        rel.last_interaction_at = now
        rel.interaction_count = (rel.interaction_count or 0) + 1
        if quality_score is not None:
            # 移动平均
            old_avg = rel.avg_quality_score or 0.5
            n = rel.interaction_count
            rel.avg_quality_score = old_avg + (quality_score - old_avg) / n

        # 互惠性检查: 记录谁发起
        if user_id == rel.user_id:
            rel.initiator_count_a = (rel.initiator_count_a or 0) + 1
        else:
            rel.initiator_count_b = (rel.initiator_count_b or 0) + 1
        total_init = (rel.initiator_count_a or 0) + (rel.initiator_count_b or 0)
        if total_init > 0:
            rel.reciprocity_score = 1.0 - abs(
                (rel.initiator_count_a or 0) / total_init - 0.5
            ) * 2

        # 重激活
        if rel.status in ("cooling", "dormant"):
            rel.status = "active"
            rel.state_changed_at = now

        self.db.commit()
        return True

    def get_companion_dashboard(self, user_id: int) -> dict:
        """获取用户的同道仪表盘"""
        from core.models import CompanionRelation
        result = self.db.execute(
            select(CompanionRelation).where(
                and_(
                    or_(
                        CompanionRelation.mentor_id == user_id,
                        CompanionRelation.mentee_id == user_id,
                    ),
                    CompanionRelation.status != "dissolved",
                )
            )
        )
        rels = result.scalars().all()

        active = [r for r in rels if r.status == "active"]
        cooling = [r for r in rels if r.status == "cooling"]
        dormant = [r for r in rels if r.status == "dormant"]

        return {
            "total_companions": len(rels),
            "active": len(active),
            "cooling": len(cooling),
            "dormant": len(dormant),
            "avg_reciprocity": (
                sum(r.reciprocity_score or 0 for r in active) / len(active)
                if active else 0
            ),
            "avg_quality": (
                sum(r.avg_quality_score or 0 for r in active) / len(active)
                if active else 0
            ),
            "companions": [
                {
                    "companion_id": (
                        r.mentee_id if r.mentor_id == user_id else r.mentor_id
                    ),
                    "status": r.status,
                    "quality": round(float(r.quality_score or 0), 2),
                }
                for r in rels
            ],
        }
