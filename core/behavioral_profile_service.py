# -*- coding: utf-8 -*-
"""
统一行为画像服务
BehavioralProfileService - 从 BAPS 评估结果生成/更新用户行为画像

职责:
1. 从 BAPS 五套问卷结果 → 生成统一 BehavioralProfile
2. 阶段判定（基于 TTM7）
3. 心理层级判定（基于 SPI）
4. 交互模式判定（基于 Stage × BPT6 type）
5. 领域需求识别（基于 CAPACITY 弱项 + Trigger）
6. 部分更新（设备数据触发时）
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from loguru import logger

from core.models import (
    BehavioralProfile, BehavioralStage, StageStability,
    InteractionMode, PsychologicalLevel, User, JourneyState,
)

# ── Behavioral→Journey stage mapping ────────────────────
# S0 (pre_contemplation) → s0_authorization
# S1 (contemplation)     → s1_awareness
# S2 (preparation)       → s2_trial
# S3 (action)            → s3_pathway
# S4 (maintenance)       → s4_internalization
# S5 (termination)       → s5_graduation
# S6 (内化为常)          → s5_graduation
BEHAVIORAL_TO_JOURNEY = {
    "S0": "s0_authorization",
    "S1": "s1_awareness",
    "S2": "s2_trial",
    "S3": "s3_pathway",
    "S4": "s4_internalization",
    "S5": "s5_graduation",
    "S6": "s5_graduation",
}
from core.baps.scoring_engine import (
    BAPSScoringEngine, TTM7Result, BigFiveResult,
    BPT6Result, CAPACITYResult, SPIResult
)

# 加载 SPI 映射配置
_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs")

def _load_spi_mapping() -> Dict:
    path = os.path.join(_CONFIG_DIR, "spi_mapping.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load spi_mapping.json: {e}, using defaults")
        return {}

SPI_MAPPING = _load_spi_mapping()

# 领域映射: CAPACITY 弱项维度 → 行为领域
CAPACITY_TO_DOMAIN = {
    "C_信心": ["emotion", "cognitive"],
    "A1_觉察": ["cognitive"],
    "A2_资源": ["social"],
    "P_计划": ["nutrition", "exercise"],
    "A3_能力": ["exercise", "nutrition"],
    "C2_应对": ["stress", "emotion"],
    "I_网络": ["social"],
    "T_时间": ["exercise", "sleep"],
    "Y_收益": ["cognitive"],
    # 英文维度名
    "confidence": ["emotion", "cognitive"],
    "awareness": ["cognitive"],
    "resource": ["social"],
    "planning": ["nutrition", "exercise"],
    "ability": ["exercise", "nutrition"],
    "coping": ["stress", "emotion"],
    "network": ["social"],
    "time": ["exercise", "sleep"],
    "yield": ["cognitive"],
}

# BPT6 行为类型 → 适合的首选领域
BPT6_DOMAIN_AFFINITY = {
    "action": ["exercise", "nutrition"],
    "knowledge": ["cognitive", "nutrition"],
    "emotion": ["emotion", "stress"],
    "relation": ["social", "emotion"],
    "environment": ["sleep", "nutrition"],
    "mixed": ["nutrition", "exercise", "sleep"],
}


class BehavioralProfileService:
    """统一行为画像生成与管理服务"""

    def __init__(self):
        self.scoring_engine = BAPSScoringEngine()
        self.spi_mapping = SPI_MAPPING

    @staticmethod
    def _sync_journey_state(db: Session, user_id: int, behavioral_stage: str):
        """同步 BehavioralProfile.current_stage → JourneyState.journey_stage"""
        journey_stage = BEHAVIORAL_TO_JOURNEY.get(behavioral_stage)
        if not journey_stage:
            return
        try:
            journey = db.query(JourneyState).filter(
                JourneyState.user_id == user_id
            ).first()
            if not journey:
                logger.warning(f"Stage sync: user={user_id} JourneyState not found, skipping")
                return
            journey.journey_stage = journey_stage
            logger.info(f"Stage sync: user={user_id} journey={journey_stage} → profile={behavioral_stage}")
        except Exception as e:
            logger.warning(f"Stage sync failed: user={user_id} {e}")

    def generate_profile(
        self,
        db: Session,
        user_id: int,
        ttm7_result: Optional[TTM7Result] = None,
        big5_result: Optional[BigFiveResult] = None,
        bpt6_result: Optional[BPT6Result] = None,
        capacity_result: Optional[CAPACITYResult] = None,
        spi_result: Optional[SPIResult] = None,
        assessment_id: Optional[str] = None,
    ) -> BehavioralProfile:
        """
        从 BAPS 评估结果生成或更新统一行为画像

        至少需要 TTM7 结果来判定阶段，其余可选。
        如果用户已有画像则更新，否则创建新画像。
        """
        # 获取或创建画像
        profile = db.query(BehavioralProfile).filter(
            BehavioralProfile.user_id == user_id
        ).first()

        if not profile:
            profile = BehavioralProfile(user_id=user_id)
            db.add(profile)

        # 1. 阶段判定 (TTM7)
        if ttm7_result:
            profile.current_stage = BehavioralStage(ttm7_result.current_stage)
            profile.stage_confidence = ttm7_result.stage_confidence
            profile.stage_updated_at = datetime.utcnow()
            profile.ttm7_stage_scores = ttm7_result.stage_scores
            profile.ttm7_sub_scores = ttm7_result.sub_scores
            profile.friendly_stage_name = ttm7_result.friendly_name
            profile.friendly_stage_desc = ttm7_result.friendly_description
            # Sync to JourneyState.journey_stage
            self._sync_journey_state(db, user_id, ttm7_result.current_stage)

        # 2. 大五人格
        if big5_result:
            profile.big5_scores = {
                dim: {"score": data.score, "level": data.level}
                for dim, data in big5_result.dimension_scores.items()
            }

        # 3. BPT-6 行为类型
        if bpt6_result:
            profile.bpt6_type = bpt6_result.primary_type
            profile.bpt6_scores = bpt6_result.dimension_scores

        # 4. CAPACITY 改变潜力
        if capacity_result:
            profile.capacity_total = capacity_result.total_score
            profile.capacity_weak = capacity_result.weak_dimensions
            profile.capacity_strong = capacity_result.strong_dimensions

        # 5. SPI 成功可能性
        if spi_result:
            profile.spi_score = spi_result.spi_score
            profile.spi_level = spi_result.success_level

        # 6. 心理层级 (基于 SPI)
        if spi_result:
            profile.psychological_level = self._determine_psychological_level(spi_result)

        # 7. 交互模式 (基于 Stage × BPT6 type)
        stage = profile.current_stage.value if profile.current_stage else "S0"
        bpt6_type = profile.bpt6_type or "mixed"
        profile.interaction_mode = self._determine_interaction_mode(stage, bpt6_type)

        # 8. 领域需求识别
        profile.primary_domains = self._identify_primary_domains(
            capacity_weak=profile.capacity_weak,
            bpt6_type=bpt6_type,
        )

        # 9. 稳定性初始化 (新评估默认 semi_stable)
        if ttm7_result:
            profile.stage_stability = StageStability.SEMI_STABLE

        # 10. 溯源
        if assessment_id:
            profile.last_assessment_id = assessment_id

        profile.updated_at = datetime.utcnow()

        db.flush()
        logger.info(
            f"BehavioralProfile updated: user={user_id}, "
            f"stage={profile.current_stage}, type={profile.bpt6_type}, "
            f"psych_level={profile.psychological_level}, "
            f"domains={profile.primary_domains}"
        )
        return profile

    def get_profile(self, db: Session, user_id: int) -> Optional[BehavioralProfile]:
        """获取用户行为画像"""
        return db.query(BehavioralProfile).filter(
            BehavioralProfile.user_id == user_id
        ).first()

    def update_stage(
        self,
        db: Session,
        user_id: int,
        new_stage: str,
        confidence: float,
        stability: str = "semi_stable",
    ) -> Optional[BehavioralProfile]:
        """
        更新用户阶段 (仅供 StageRuntimeBuilder 调用)

        这是系统中唯一可以修改 current_stage 的入口
        """
        profile = self.get_profile(db, user_id)
        if not profile:
            logger.warning(f"No profile found for user {user_id}")
            return None

        profile.current_stage = BehavioralStage(new_stage)
        profile.stage_confidence = confidence
        profile.stage_stability = StageStability(stability)
        profile.stage_updated_at = datetime.utcnow()

        # Sync to JourneyState.journey_stage
        self._sync_journey_state(db, user_id, new_stage)

        # 更新交互模式
        bpt6_type = profile.bpt6_type or "mixed"
        profile.interaction_mode = self._determine_interaction_mode(new_stage, bpt6_type)

        # 更新友好名称
        profile.friendly_stage_name = BAPSScoringEngine.STAGE_FRIENDLY_NAMES.get(new_stage)
        profile.friendly_stage_desc = BAPSScoringEngine.STAGE_FRIENDLY_DESC.get(new_stage)

        profile.updated_at = datetime.utcnow()
        db.flush()
        return profile

    def update_risk_flags(
        self,
        db: Session,
        user_id: int,
        risk_flags: List[str],
    ) -> Optional[BehavioralProfile]:
        """更新风险标记"""
        profile = self.get_profile(db, user_id)
        if not profile:
            return None
        profile.risk_flags = risk_flags
        profile.updated_at = datetime.utcnow()
        db.flush()
        return profile

    # ====== 内部映射方法 ======

    def _determine_psychological_level(self, spi_result: SPIResult) -> PsychologicalLevel:
        """SPI score → 心理层级 L1-L5"""
        score = spi_result.spi_score
        mapping = self.spi_mapping.get("spi_to_psychological_level", {})

        # 按阈值从高到低判定
        for level in ["L5", "L4", "L3", "L2", "L1"]:
            if level in mapping and score >= mapping[level].get("min_spi", 0):
                return PsychologicalLevel(level)

        # 默认回退
        if score >= 70:
            return PsychologicalLevel.L5
        elif score >= 50:
            return PsychologicalLevel.L4
        elif score >= 30:
            return PsychologicalLevel.L3
        elif score >= 15:
            return PsychologicalLevel.L2
        else:
            return PsychologicalLevel.L1

    def _determine_interaction_mode(self, stage: str, bpt6_type: str) -> InteractionMode:
        """
        Stage × BPT6 type → 交互模式

        规则:
        - S0-S1 任何类型 → EMPATHY
        - S2-S3 + 行动型 → CHALLENGE
        - S2-S3 + 其他类型 → EMPATHY
        - S4-S6 → EXECUTION
        """
        if stage in ("S0", "S1"):
            return InteractionMode.EMPATHY

        if stage in ("S2", "S3"):
            if bpt6_type == "action":
                return InteractionMode.CHALLENGE
            return InteractionMode.EMPATHY

        if stage in ("S4", "S5", "S6"):
            return InteractionMode.EXECUTION

        return InteractionMode.EMPATHY

    def _identify_primary_domains(
        self,
        capacity_weak: Optional[List[str]] = None,
        bpt6_type: Optional[str] = None,
    ) -> List[str]:
        """
        识别用户主要需干预的行为领域

        基于 CAPACITY 弱项维度 + BPT6 类型亲和度
        """
        domains_score: Dict[str, int] = {}

        # 从 CAPACITY 弱项推导领域 (权重 2)
        if capacity_weak:
            for weak_dim in capacity_weak:
                mapped = CAPACITY_TO_DOMAIN.get(weak_dim, [])
                for domain in mapped:
                    domains_score[domain] = domains_score.get(domain, 0) + 2

        # 从 BPT6 类型推导领域亲和 (权重 1)
        if bpt6_type:
            affinity = BPT6_DOMAIN_AFFINITY.get(bpt6_type, [])
            for domain in affinity:
                domains_score[domain] = domains_score.get(domain, 0) + 1

        # 按分数降序排列，取前 3 个
        if not domains_score:
            return ["nutrition", "exercise", "sleep"]  # 默认三大基础领域

        sorted_domains = sorted(domains_score.items(), key=lambda x: -x[1])
        return [d[0] for d in sorted_domains[:3]]

    def get_profile_summary(self, db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取行为画像摘要（用于 API 返回）

        返回去诊断化的、面向前端友好的摘要
        """
        profile = self.get_profile(db, user_id)
        if not profile:
            return None

        return {
            "user_id": user_id,
            # 阶段信息 (去诊断化)
            "stage": {
                "current": profile.current_stage.value if profile.current_stage else None,
                "name": profile.friendly_stage_name,
                "description": profile.friendly_stage_desc,
                "confidence": profile.stage_confidence,
                "stability": profile.stage_stability.value if profile.stage_stability else None,
                "updated_at": profile.stage_updated_at.isoformat() if profile.stage_updated_at else None,
            },
            # 行为类型
            "behavior_type": {
                "primary": profile.bpt6_type,
                "scores": profile.bpt6_scores,
            },
            # 人格特征
            "personality": profile.big5_scores,
            # 改变潜力
            "capacity": {
                "total": profile.capacity_total,
                "weak": profile.capacity_weak,
                "strong": profile.capacity_strong,
            },
            # 成功可能性
            "spi": {
                "score": profile.spi_score,
                "level": profile.spi_level,
            },
            # 心理层级 & 交互模式
            "psychological_level": profile.psychological_level.value if profile.psychological_level else None,
            "interaction_mode": profile.interaction_mode.value if profile.interaction_mode else None,
            # 领域需求
            "primary_domains": profile.primary_domains,
            # 风险
            "risk_flags": profile.risk_flags,
            # 时间
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        }

    def get_coach_view(self, db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取教练视角的完整画像（含内部阶段编号、子分数等）

        仅教练/管理员可调用
        """
        profile = self.get_profile(db, user_id)
        if not profile:
            return None

        summary = self.get_profile_summary(db, user_id)
        # 教练额外信息
        summary["_coach_only"] = {
            "stage_code": profile.current_stage.value if profile.current_stage else None,
            "ttm7_stage_scores": profile.ttm7_stage_scores,
            "ttm7_sub_scores": profile.ttm7_sub_scores,
            "domain_details": profile.domain_details,
            "last_assessment_id": profile.last_assessment_id,
        }
        return summary
