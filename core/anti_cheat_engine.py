"""
六种防刷策略引擎
契约来源: Sheet⑦ 积分契约 · 防刷策略矩阵 + Sheet⑩ P0 (2周)

六种策略:
  AS-01: 每日上限 — 同一积分行为每日获取上限, 次日重置
  AS-02: 质量加权 — 高质量贡献×2, 低质量×0.5
  AS-03: 时间衰减 — 同一行为重复执行积分递减曲线
  AS-04: 交叉验证 — 涉及他人的积分需对方确认
  AS-05: 成长轨校验 — 积分达标但成长轨未过→状态2 (已集成于双轨引擎)
  AS-06: 异常检测 — 短时间大量相同行为→标记审查

集成点:
  - IncentiveEngine.award_points() 前调用 pipeline
  - point_events.json / point_events_governance.json 配置驱动
  - Week1 Task2 anti_cheat_strategies 字段对接
  - Week2 Task A dual_track_engine AS-05 对接
"""

from __future__ import annotations
import json
import time
import math
from datetime import datetime, date, timedelta, timezone
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple, Protocol
from dataclasses import dataclass, field, asdict
from collections import defaultdict


# ══════════════════════════════════════════
# 0. 策略枚举与数据结构
# ══════════════════════════════════════════

class AntiCheatStrategy(str, Enum):
    AS_01_DAILY_CAP = "AS-01"
    AS_02_QUALITY_WEIGHT = "AS-02"
    AS_03_TIME_DECAY = "AS-03"
    AS_04_CROSS_VERIFY = "AS-04"
    AS_05_GROWTH_TRACK = "AS-05"
    AS_06_ANOMALY_DETECT = "AS-06"


class StrategyVerdict(str, Enum):
    ALLOW = "allow"           # 正常通过
    CAPPED = "capped"         # 每日上限已满 (AS-01)
    WEIGHTED = "weighted"     # 积分被质量加权 (AS-02)
    DECAYED = "decayed"       # 积分被时间衰减 (AS-03)
    PENDING = "pending"       # 等待交叉验证 (AS-04)
    BLOCKED = "blocked"       # 成长轨校验阻断 (AS-05)
    FLAGGED = "flagged"       # 异常标记审查 (AS-06)


@dataclass
class PointsAwardRequest:
    """积分发放请求"""
    user_id: int
    event_type: str              # e.g. "daily_checkin", "ethics_scenario_test"
    base_points: int             # 基础积分值
    points_category: str         # "growth" | "contribution" | "influence"
    behavior_id: str = ""        # 行为唯一 ID (用于去重/衰减追踪)
    quality_score: float = 1.0   # 质量评分 0.0~1.0 (AS-02)
    counterpart_user_id: int = 0 # 对方用户 (AS-04 交叉验证)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0      # Unix timestamp

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class StrategyResult:
    """单策略执行结果"""
    strategy: AntiCheatStrategy
    verdict: StrategyVerdict
    adjusted_points: int         # 调整后积分
    original_points: int         # 原始积分
    reason: str = ""             # 原因描述
    user_message: str = ""       # 用户可见消息
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """策略流水线最终结果"""
    final_points: int
    original_points: int
    awarded: bool                # 是否最终发放
    strategy_results: List[StrategyResult]
    verdict_summary: str         # 综合判定
    user_message: str            # 用户可见提示
    flagged_for_review: bool = False
    pending_confirmation: bool = False


# ══════════════════════════════════════════
# 1. AS-01 每日上限策略
# ══════════════════════════════════════════

class DailyCapStrategy:
    """
    AS-01: 每日上限。
    同一积分行为设定每日获取上限, 次日零点重置。
    
    配置来源: point_events.json → daily_cap 字段
    用户感知: 「今日该项积分已达上限, 明天继续」
    """
    
    STRATEGY = AntiCheatStrategy.AS_01_DAILY_CAP
    
    # 默认上限 (从配置覆盖)
    DEFAULT_CAPS: Dict[str, int] = {
        "daily_checkin": 1,
        "behavior_attempt": 3,
        "path_contribution": 3,
        "content_publish": 3,
        "community_help": 10,
        "case_share": 2,
        "assessment_submit": 3,
        "micro_action_complete": 5,
        "challenge_checkin": 3,
        "reflection_create": 3,
        "contract_sign": 1,
        "companion_add": 3,
        "contribution_submit": 3,
        "food_recognize": 5,
        "peer_accept": 3,
        # 治理事件
        "ethics_scenario_test": 1,
        "competency_self_assessment": 1,
        "conflict_disclosure_update": 1,
        "alert_timely_response": 5,
        "student_message_reply": 10,
        "agent_feedback_reply": 5,
        "knowledge_shared": 3,
        "certificate_renewal_confirmed": 1,
        # Agent 生态
        "optimize_prompt": 5,  # 每Agent每月≤5, 简化为每日
        "feedback_positive": 17,  # 50积分/3分每次≈17次
    }
    
    def __init__(self, redis_client=None, config_overrides: Dict[str, int] = None):
        self.redis = redis_client
        self._caps = {**self.DEFAULT_CAPS}
        if config_overrides:
            self._caps.update(config_overrides)
        # 内存备份 (Redis不可用时)
        self._memory_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    async def evaluate(self, request: PointsAwardRequest) -> StrategyResult:
        """评估是否超出每日上限"""
        cap = self._caps.get(request.event_type, 0)
        
        # 无上限设定 → 直接通过
        if cap == 0:
            return StrategyResult(
                strategy=self.STRATEGY,
                verdict=StrategyVerdict.ALLOW,
                adjusted_points=request.base_points,
                original_points=request.base_points,
            )
        
        # 获取今日已计次数
        today_key = self._day_key(request.user_id, request.event_type)
        current_count = await self._get_count(today_key)
        
        if current_count >= cap:
            return StrategyResult(
                strategy=self.STRATEGY,
                verdict=StrategyVerdict.CAPPED,
                adjusted_points=0,
                original_points=request.base_points,
                reason=f"每日上限 {cap} 次已满 (已 {current_count} 次)",
                user_message=f"今日该项积分已达上限({cap}次),明天继续!",
                metadata={"daily_cap": cap, "current_count": current_count},
            )
        
        # 通过 → 计数器 +1
        await self._increment(today_key)
        
        return StrategyResult(
            strategy=self.STRATEGY,
            verdict=StrategyVerdict.ALLOW,
            adjusted_points=request.base_points,
            original_points=request.base_points,
            metadata={"daily_cap": cap, "current_count": current_count + 1},
        )
    
    def _day_key(self, user_id: int, event_type: str) -> str:
        today = date.today().isoformat()
        return f"anticheat:daily:{user_id}:{event_type}:{today}"
    
    async def _get_count(self, key: str) -> int:
        if self.redis:
            try:
                val = await self.redis.get(key)
                return int(val) if val else 0
            except Exception:
                pass
        # 内存回退
        return self._memory_counters.get(key, {}).get("count", 0)
    
    async def _increment(self, key: str) -> None:
        if self.redis:
            try:
                pipe = self.redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, 86400)  # TTL = 1 天
                await pipe.execute()
                return
            except Exception:
                pass
        self._memory_counters[key]["count"] = self._memory_counters.get(key, {}).get("count", 0) + 1


# ══════════════════════════════════════════
# 2. AS-02 质量加权策略
# ══════════════════════════════════════════

class QualityWeightStrategy:
    """
    AS-02: 质量加权。
    高质量贡献 ×2 倍积分, 低质量 ×0.5 倍。
    
    适用层级: L1-L5
    用户感知: 不展示倍率, 只展示最终积分
    
    质量评分来源:
      - content_publish → ContentReview.quality_score
      - case_share → CaseReview.quality_score
      - agent_feedback_reply → FeedbackService.quality_score
      - knowledge_shared → KnowledgeReview.quality_score
      - optimize_prompt → PromptVersion.improvement_score
    """
    
    STRATEGY = AntiCheatStrategy.AS_02_QUALITY_WEIGHT
    
    # 需要质量加权的事件列表
    QUALITY_EVENTS = {
        "content_publish", "case_share", "community_help",
        "agent_feedback_reply", "knowledge_shared", "optimize_prompt",
        "contribution_submit",
    }
    
    # 质量→倍率映射 (Sheet⑦: 高质量×2, 低质量×0.5)
    QUALITY_TIERS = [
        (0.8, 2.0, "high"),     # quality >= 0.8 → ×2
        (0.6, 1.0, "medium"),   # quality >= 0.6 → ×1 (标准)
        (0.3, 0.5, "low"),      # quality >= 0.3 → ×0.5
        (0.0, 0.0, "rejected"), # quality < 0.3 → ×0 (拒绝)
    ]
    
    async def evaluate(self, request: PointsAwardRequest) -> StrategyResult:
        """评估质量加权"""
        # 不在质量加权列表 → 直接通过
        if request.event_type not in self.QUALITY_EVENTS:
            return StrategyResult(
                strategy=self.STRATEGY,
                verdict=StrategyVerdict.ALLOW,
                adjusted_points=request.base_points,
                original_points=request.base_points,
            )
        
        # 确定倍率
        multiplier = 1.0
        tier_name = "standard"
        for threshold, mult, name in self.QUALITY_TIERS:
            if request.quality_score >= threshold:
                multiplier = mult
                tier_name = name
                break
        
        adjusted = int(request.base_points * multiplier)
        
        if multiplier == request.base_points and multiplier == 1.0:
            verdict = StrategyVerdict.ALLOW
        else:
            verdict = StrategyVerdict.WEIGHTED
        
        return StrategyResult(
            strategy=self.STRATEGY,
            verdict=verdict,
            adjusted_points=adjusted,
            original_points=request.base_points,
            reason=f"质量评级 {tier_name} (score={request.quality_score:.2f}), 倍率 ×{multiplier}",
            metadata={
                "quality_score": request.quality_score,
                "multiplier": multiplier,
                "tier": tier_name,
            },
        )


# ══════════════════════════════════════════
# 3. AS-03 时间衰减策略
# ══════════════════════════════════════════

class TimeDecayStrategy:
    """
    AS-03: 时间衰减。
    同一行为重复执行, 积分逐次递减。
    
    适用层级: L0-L2
    衰减曲线 (Sheet⑦):
      第1-5次:   ×1.0
      第6-10次:  ×0.8
      第11-20次: ×0.5
      第21次起:  ×0.2
    
    用户感知: 「尝试不同行为获得更多积分」
    """
    
    STRATEGY = AntiCheatStrategy.AS_03_TIME_DECAY
    
    # 需要时间衰减的事件
    DECAY_EVENTS = {
        "behavior_attempt", "community_help", "daily_checkin",
        "student_message_reply", "micro_action_complete",
        "challenge_checkin", "food_recognize",
    }
    
    # 衰减曲线 (累计次数→倍率)
    DECAY_CURVE = [
        (5, 1.0),    # 第1-5次: 无衰减
        (10, 0.8),   # 第6-10次: ×0.8
        (20, 0.5),   # 第11-20次: ×0.5
        (999999, 0.2),  # 第21次起: ×0.2
    ]
    
    # 衰减周期 (天) — 周期结束后计数器重置
    DECAY_PERIOD_DAYS = 7
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._memory_counters: Dict[str, int] = defaultdict(int)
    
    async def evaluate(self, request: PointsAwardRequest) -> StrategyResult:
        """评估时间衰减"""
        if request.event_type not in self.DECAY_EVENTS:
            return StrategyResult(
                strategy=self.STRATEGY,
                verdict=StrategyVerdict.ALLOW,
                adjusted_points=request.base_points,
                original_points=request.base_points,
            )
        
        # 获取周期内累计次数
        period_key = self._period_key(request.user_id, request.event_type)
        count = await self._get_period_count(period_key)
        
        # 计算衰减倍率
        multiplier = self._get_decay_multiplier(count)
        adjusted = max(1, int(request.base_points * multiplier))  # 最低 1 分
        
        # 递增计数器
        await self._increment(period_key)
        
        if multiplier < 1.0:
            return StrategyResult(
                strategy=self.STRATEGY,
                verdict=StrategyVerdict.DECAYED,
                adjusted_points=adjusted,
                original_points=request.base_points,
                reason=f"周期内第 {count + 1} 次, 衰减倍率 ×{multiplier}",
                user_message="尝试不同行为获得更多积分!",
                metadata={
                    "period_count": count + 1,
                    "multiplier": multiplier,
                    "period_days": self.DECAY_PERIOD_DAYS,
                },
            )
        
        return StrategyResult(
            strategy=self.STRATEGY,
            verdict=StrategyVerdict.ALLOW,
            adjusted_points=adjusted,
            original_points=request.base_points,
            metadata={"period_count": count + 1, "multiplier": multiplier},
        )
    
    def _get_decay_multiplier(self, count: int) -> float:
        """根据累计次数返回衰减倍率"""
        for threshold, mult in self.DECAY_CURVE:
            if count < threshold:
                return mult
        return 0.2
    
    def _period_key(self, user_id: int, event_type: str) -> str:
        # 按周计算周期 (ISO week)
        week = date.today().isocalendar()
        return f"anticheat:decay:{user_id}:{event_type}:{week.year}W{week.week:02d}"
    
    async def _get_period_count(self, key: str) -> int:
        if self.redis:
            try:
                val = await self.redis.get(key)
                return int(val) if val else 0
            except Exception:
                pass
        return self._memory_counters.get(key, 0)
    
    async def _increment(self, key: str) -> None:
        if self.redis:
            try:
                pipe = self.redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, self.DECAY_PERIOD_DAYS * 86400)
                await pipe.execute()
                return
            except Exception:
                pass
        self._memory_counters[key] = self._memory_counters.get(key, 0) + 1


# ══════════════════════════════════════════
# 4. AS-04 交叉验证策略
# ══════════════════════════════════════════

class CrossVerifyStrategy:
    """
    AS-04: 交叉验证。
    涉及他人的积分需对方确认后才计入。
    
    适用层级: L1-L5
    适用场景: 陪伴/带教/转介/告警处置/督导会议/知识共享
    
    用户感知: 「等待对方确认中」
    技术实现: 双方 confirm 才 write 积分
    """
    
    STRATEGY = AntiCheatStrategy.AS_04_CROSS_VERIFY
    
    # 需要交叉验证的事件
    CROSS_VERIFY_EVENTS = {
        "companion_session",          # 陪伴记录
        "mentee_graduation",          # 学员毕业
        "referral_correct",           # 转介
        "alert_timely_response",      # 告警处置
        "supervision_session_completed",  # 督导会议
        "knowledge_shared",           # 知识共享
        "peer_accept",                # 同伴匹配接受
    }
    
    def __init__(self, confirmation_store=None):
        self.store = confirmation_store
        self._memory_pending: Dict[str, Dict] = {}
    
    async def evaluate(self, request: PointsAwardRequest) -> StrategyResult:
        """评估是否需要交叉验证"""
        if request.event_type not in self.CROSS_VERIFY_EVENTS:
            return StrategyResult(
                strategy=self.STRATEGY,
                verdict=StrategyVerdict.ALLOW,
                adjusted_points=request.base_points,
                original_points=request.base_points,
            )
        
        if request.counterpart_user_id == 0:
            # 无对方用户 → 需要提供
            return StrategyResult(
                strategy=self.STRATEGY,
                verdict=StrategyVerdict.PENDING,
                adjusted_points=0,
                original_points=request.base_points,
                reason="需要对方用户 ID 进行交叉验证",
                user_message="请提供关联用户以完成验证",
            )
        
        # 检查对方是否已确认
        confirmed = await self._check_confirmation(
            request.user_id,
            request.counterpart_user_id,
            request.event_type,
            request.behavior_id,
        )
        
        if confirmed:
            return StrategyResult(
                strategy=self.STRATEGY,
                verdict=StrategyVerdict.ALLOW,
                adjusted_points=request.base_points,
                original_points=request.base_points,
                reason="对方已确认",
                metadata={"counterpart_confirmed": True},
            )
        
        # 创建待确认记录
        await self._create_pending(request)
        
        return StrategyResult(
            strategy=self.STRATEGY,
            verdict=StrategyVerdict.PENDING,
            adjusted_points=0,
            original_points=request.base_points,
            reason="等待对方确认",
            user_message="等待对方确认中,确认后积分将自动发放",
            metadata={
                "counterpart_user_id": request.counterpart_user_id,
                "pending": True,
            },
        )
    
    async def confirm(
        self,
        confirmer_user_id: int,
        original_user_id: int,
        event_type: str,
        behavior_id: str,
    ) -> bool:
        """对方确认 → 释放积分"""
        pending_key = self._pending_key(original_user_id, confirmer_user_id, event_type, behavior_id)
        
        if self.store:
            try:
                return await self.store.confirm(pending_key)
            except Exception:
                pass
        
        if pending_key in self._memory_pending:
            self._memory_pending[pending_key]["confirmed"] = True
            return True
        return False
    
    async def _check_confirmation(
        self, user_id: int, counterpart_id: int, event_type: str, behavior_id: str
    ) -> bool:
        key = self._pending_key(user_id, counterpart_id, event_type, behavior_id)
        if self.store:
            try:
                return await self.store.is_confirmed(key)
            except Exception:
                pass
        return self._memory_pending.get(key, {}).get("confirmed", False)
    
    async def _create_pending(self, request: PointsAwardRequest) -> None:
        key = self._pending_key(
            request.user_id, request.counterpart_user_id,
            request.event_type, request.behavior_id,
        )
        pending = {
            "user_id": request.user_id,
            "counterpart": request.counterpart_user_id,
            "event_type": request.event_type,
            "base_points": request.base_points,
            "confirmed": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.store:
            try:
                await self.store.create_pending(key, pending)
                return
            except Exception:
                pass
        self._memory_pending[key] = pending
    
    def _pending_key(self, uid: int, cid: int, event: str, bid: str) -> str:
        return f"xverify:{uid}:{cid}:{event}:{bid}"


# ══════════════════════════════════════════
# 5. AS-05 成长轨校验策略 (桥接 DualTrackEngine)
# ══════════════════════════════════════════

class GrowthTrackStrategy:
    """
    AS-05: 成长轨校验。
    积分再多, 成长轨不过 = 不晋级。
    
    本策略不阻断积分发放, 而是在积分达标时触发双轨状态2。
    实际校验逻辑在 dual_track_engine.DualTrackChecker 中。
    
    集成方式:
      积分变动 → IncentiveEngine → 检查是否触达晋级阈值
      → 如果触达 → 调用 PromotionOrchestrator.check_promotion_eligibility()
      → 由双轨引擎判定状态
    """
    
    STRATEGY = AntiCheatStrategy.AS_05_GROWTH_TRACK
    
    def __init__(self, promotion_orchestrator=None):
        self.orchestrator = promotion_orchestrator
    
    async def evaluate(self, request: PointsAwardRequest) -> StrategyResult:
        """
        AS-05 不阻断积分, 只在达标时触发双轨校验。
        总是返回 ALLOW (积分正常发放), 但附带晋级状态信息。
        """
        result = StrategyResult(
            strategy=self.STRATEGY,
            verdict=StrategyVerdict.ALLOW,
            adjusted_points=request.base_points,
            original_points=request.base_points,
        )
        
        # 如果有编排器, 异步触发校验 (不阻塞积分发放)
        if self.orchestrator:
            try:
                promo_status = await self.orchestrator.check_promotion_eligibility(
                    request.user_id,
                    request.metadata.get("current_level", "L0"),
                )
                result.metadata = {"promotion_state": promo_status.get("state_name")}
                
                # 如果达到状态2, 附加信息
                if promo_status.get("state") == 2:
                    result.reason = "积分已达标, 成长轨待验证 (状态2)"
                    result.user_message = promo_status.get("guidance_message", "")
            except Exception:
                pass
        
        return result


# ══════════════════════════════════════════
# 6. AS-06 异常检测策略
# ══════════════════════════════════════════

class AnomalyDetectStrategy:
    """
    AS-06: 异常检测。
    短时间大量相同行为 → 自动标记 + 人工审查队列。
    
    检测规则 (Sheet⑦):
      - 1小时内同一行为 > 20次 → 标记
      - 模式异常 (夜间3-5点大量操作) → 标记
      - 同 IP 多账户相同行为 → 标记
    
    用户感知: 不提示用户 (避免对抗)
    """
    
    STRATEGY = AntiCheatStrategy.AS_06_ANOMALY_DETECT
    
    # 阈值配置
    HOURLY_THRESHOLD = 20          # 1小时内同一行为超过此数 → 异常
    NIGHT_HOURS = (3, 5)           # 异常时段 (3:00-5:00)
    NIGHT_THRESHOLD = 10           # 夜间阈值更低
    BURST_WINDOW_SECONDS = 60      # 突发窗口 (60秒内)
    BURST_THRESHOLD = 8            # 突发阈值
    
    def __init__(self, redis_client=None, review_queue=None, audit_logger=None):
        self.redis = redis_client
        self.review_queue = review_queue
        self.audit = audit_logger
        self._memory_windows: Dict[str, List[float]] = defaultdict(list)
    
    async def evaluate(self, request: PointsAwardRequest) -> StrategyResult:
        """评估是否存在异常行为"""
        anomalies = []
        
        # 检测1: 小时级频率
        hourly_count = await self._get_hourly_count(request.user_id, request.event_type)
        current_hour = datetime.now(timezone.utc).hour
        
        threshold = self.NIGHT_THRESHOLD if self.NIGHT_HOURS[0] <= current_hour <= self.NIGHT_HOURS[1] else self.HOURLY_THRESHOLD
        
        if hourly_count >= threshold:
            anomalies.append({
                "type": "hourly_frequency",
                "count": hourly_count,
                "threshold": threshold,
                "is_night": self.NIGHT_HOURS[0] <= current_hour <= self.NIGHT_HOURS[1],
            })
        
        # 检测2: 突发请求 (60秒内)
        burst_count = await self._get_burst_count(
            request.user_id, request.event_type, request.timestamp
        )
        if burst_count >= self.BURST_THRESHOLD:
            anomalies.append({
                "type": "burst_activity",
                "count": burst_count,
                "window_seconds": self.BURST_WINDOW_SECONDS,
                "threshold": self.BURST_THRESHOLD,
            })
        
        # 记录时间戳
        await self._record_event(request.user_id, request.event_type, request.timestamp)
        
        if anomalies:
            # 标记进审查队列 (不阻断积分, 不提示用户)
            await self._submit_for_review(request, anomalies)
            
            return StrategyResult(
                strategy=self.STRATEGY,
                verdict=StrategyVerdict.FLAGGED,
                adjusted_points=request.base_points,  # 仍然发放 (人工审查后可回收)
                original_points=request.base_points,
                reason=f"异常检测触发: {len(anomalies)} 项异常",
                user_message="",  # ⚠️ 不提示用户 (避免对抗)
                metadata={"anomalies": anomalies, "review_submitted": True},
            )
        
        return StrategyResult(
            strategy=self.STRATEGY,
            verdict=StrategyVerdict.ALLOW,
            adjusted_points=request.base_points,
            original_points=request.base_points,
        )
    
    async def _get_hourly_count(self, user_id: int, event_type: str) -> int:
        key = self._hourly_key(user_id, event_type)
        if self.redis:
            try:
                val = await self.redis.get(key)
                return int(val) if val else 0
            except Exception:
                pass
        now = time.time()
        timestamps = self._memory_windows.get(f"h:{key}", [])
        return sum(1 for t in timestamps if now - t < 3600)
    
    async def _get_burst_count(
        self, user_id: int, event_type: str, current_ts: float
    ) -> int:
        key = f"burst:{user_id}:{event_type}"
        timestamps = self._memory_windows.get(key, [])
        return sum(1 for t in timestamps if current_ts - t < self.BURST_WINDOW_SECONDS)
    
    async def _record_event(
        self, user_id: int, event_type: str, timestamp: float
    ) -> None:
        hourly_key = self._hourly_key(user_id, event_type)
        burst_key = f"burst:{user_id}:{event_type}"
        
        if self.redis:
            try:
                pipe = self.redis.pipeline()
                pipe.incr(hourly_key)
                pipe.expire(hourly_key, 3600)
                await pipe.execute()
                return
            except Exception:
                pass
        
        self._memory_windows[f"h:{hourly_key}"].append(timestamp)
        self._memory_windows[burst_key].append(timestamp)
        
        # 清理旧数据
        now = time.time()
        self._memory_windows[f"h:{hourly_key}"] = [
            t for t in self._memory_windows[f"h:{hourly_key}"] if now - t < 3600
        ]
        self._memory_windows[burst_key] = [
            t for t in self._memory_windows[burst_key] if now - t < self.BURST_WINDOW_SECONDS * 2
        ]
    
    async def _submit_for_review(
        self, request: PointsAwardRequest, anomalies: List[dict]
    ) -> None:
        review_item = {
            "user_id": request.user_id,
            "event_type": request.event_type,
            "anomalies": anomalies,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "base_points": request.base_points,
            "metadata": request.metadata,
        }
        
        if self.review_queue:
            try:
                await self.review_queue.submit(review_item)
            except Exception:
                pass
        
        if self.audit:
            try:
                await self.audit.log(
                    user_id=request.user_id,
                    action="anomaly_flagged",
                    resource_type="points",
                    details=review_item,
                    sensitivity="medium",
                )
            except Exception:
                pass
    
    def _hourly_key(self, user_id: int, event_type: str) -> str:
        hour = datetime.now(timezone.utc).strftime("%Y%m%d%H")
        return f"anticheat:hourly:{user_id}:{event_type}:{hour}"


# ══════════════════════════════════════════
# 7. 策略流水线 (Pipeline)
# ══════════════════════════════════════════

class AntiCheatPipeline:
    """
    防刷策略流水线。
    
    执行顺序:
      AS-06 异常检测 (先标记, 不阻断)
      → AS-01 每日上限 (硬性阻断)
      → AS-04 交叉验证 (等待确认)
      → AS-03 时间衰减 (积分调整)
      → AS-02 质量加权 (积分调整)
      → AS-05 成长轨校验 (附加信息, 不阻断)
    
    调用方式:
      pipeline = AntiCheatPipeline.create_default(redis)
      result = await pipeline.process(request)
      if result.awarded:
          await incentive_engine.write_points(user_id, result.final_points)
    """
    
    def __init__(
        self,
        daily_cap: DailyCapStrategy,
        quality_weight: QualityWeightStrategy,
        time_decay: TimeDecayStrategy,
        cross_verify: CrossVerifyStrategy,
        growth_track: GrowthTrackStrategy,
        anomaly_detect: AnomalyDetectStrategy,
        enabled_strategies: Optional[List[AntiCheatStrategy]] = None,
    ):
        self.daily_cap = daily_cap
        self.quality_weight = quality_weight
        self.time_decay = time_decay
        self.cross_verify = cross_verify
        self.growth_track = growth_track
        self.anomaly_detect = anomaly_detect
        
        # 默认全部启用
        self.enabled = set(enabled_strategies or [s for s in AntiCheatStrategy])
    
    @classmethod
    def create_default(cls, redis_client=None, promotion_orchestrator=None) -> "AntiCheatPipeline":
        """工厂方法: 创建默认配置的流水线"""
        return cls(
            daily_cap=DailyCapStrategy(redis_client),
            quality_weight=QualityWeightStrategy(),
            time_decay=TimeDecayStrategy(redis_client),
            cross_verify=CrossVerifyStrategy(),
            growth_track=GrowthTrackStrategy(promotion_orchestrator),
            anomaly_detect=AnomalyDetectStrategy(redis_client),
        )
    
    async def process(self, request: PointsAwardRequest) -> PipelineResult:
        """
        执行策略流水线。
        
        短路规则:
          - AS-01 CAPPED → 直接返回 0 积分
          - AS-04 PENDING → 暂不发放, 等待确认
          - AS-06 FLAGGED → 仍发放 (人工审查后可回收)
          - AS-02/AS-03 → 积分倍率累积
        """
        results: List[StrategyResult] = []
        current_points = request.base_points
        flagged = False
        pending = False
        
        # ── Step 1: AS-06 异常检测 (先检测, 不阻断) ──
        if AntiCheatStrategy.AS_06_ANOMALY_DETECT in self.enabled:
            r = await self.anomaly_detect.evaluate(request)
            results.append(r)
            if r.verdict == StrategyVerdict.FLAGGED:
                flagged = True
        
        # ── Step 2: AS-01 每日上限 (硬性阻断) ──
        if AntiCheatStrategy.AS_01_DAILY_CAP in self.enabled:
            r = await self.daily_cap.evaluate(request)
            results.append(r)
            if r.verdict == StrategyVerdict.CAPPED:
                return PipelineResult(
                    final_points=0,
                    original_points=request.base_points,
                    awarded=False,
                    strategy_results=results,
                    verdict_summary="capped",
                    user_message=r.user_message,
                    flagged_for_review=flagged,
                )
        
        # ── Step 3: AS-04 交叉验证 (等待确认) ──
        if AntiCheatStrategy.AS_04_CROSS_VERIFY in self.enabled:
            r = await self.cross_verify.evaluate(request)
            results.append(r)
            if r.verdict == StrategyVerdict.PENDING:
                return PipelineResult(
                    final_points=0,
                    original_points=request.base_points,
                    awarded=False,
                    strategy_results=results,
                    verdict_summary="pending_confirmation",
                    user_message=r.user_message,
                    pending_confirmation=True,
                    flagged_for_review=flagged,
                )
        
        # ── Step 4: AS-03 时间衰减 (调整积分) ──
        if AntiCheatStrategy.AS_03_TIME_DECAY in self.enabled:
            r = await self.time_decay.evaluate(request)
            results.append(r)
            if r.verdict == StrategyVerdict.DECAYED:
                current_points = r.adjusted_points
        
        # ── Step 5: AS-02 质量加权 (在衰减后的基础上加权) ──
        if AntiCheatStrategy.AS_02_QUALITY_WEIGHT in self.enabled:
            # 用当前积分值重新构建请求
            weighted_req = PointsAwardRequest(
                user_id=request.user_id,
                event_type=request.event_type,
                base_points=current_points,
                points_category=request.points_category,
                quality_score=request.quality_score,
                metadata=request.metadata,
                timestamp=request.timestamp,
            )
            r = await self.quality_weight.evaluate(weighted_req)
            results.append(r)
            current_points = r.adjusted_points
        
        # ── Step 6: AS-05 成长轨校验 (附加信息) ──
        if AntiCheatStrategy.AS_05_GROWTH_TRACK in self.enabled:
            r = await self.growth_track.evaluate(request)
            results.append(r)
        
        # 综合判定
        verdict = "allowed"
        if flagged:
            verdict = "allowed_but_flagged"
        
        user_msg = ""
        for r in results:
            if r.user_message:
                user_msg = r.user_message
                break
        
        return PipelineResult(
            final_points=max(0, current_points),
            original_points=request.base_points,
            awarded=current_points > 0,
            strategy_results=results,
            verdict_summary=verdict,
            user_message=user_msg,
            flagged_for_review=flagged,
            pending_confirmation=pending,
        )
    
    async def process_cross_verify_confirmation(
        self,
        confirmer_user_id: int,
        original_user_id: int,
        event_type: str,
        behavior_id: str,
    ) -> bool:
        """处理交叉验证确认"""
        return await self.cross_verify.confirm(
            confirmer_user_id, original_user_id, event_type, behavior_id,
        )


# ══════════════════════════════════════════
# 8. 事件→策略映射注册表
# ══════════════════════════════════════════

EVENT_STRATEGY_MAP: Dict[str, List[str]] = {
    # Week1 Task2 治理事件映射 (from point_events_governance.json)
    "ethics_scenario_test":        ["AS-01", "AS-05"],
    "competency_self_assessment":  ["AS-01", "AS-05"],
    "ethics_declaration_signed":   ["AS-05"],
    "conflict_disclosure_update":  ["AS-01", "AS-05"],
    "alert_timely_response":       ["AS-01", "AS-04"],
    "student_message_reply":       ["AS-01", "AS-03", "AS-06"],
    "supervision_session_completed": ["AS-04", "AS-05"],
    "agent_feedback_reply":        ["AS-01", "AS-02"],
    "knowledge_shared":            ["AS-02", "AS-04"],
    "certificate_renewal_confirmed": ["AS-01", "AS-05"],
    # Agent 生态
    "create_agent":                ["AS-05"],
    "optimize_prompt":             ["AS-01", "AS-02"],
    "share_knowledge":             ["AS-02", "AS-04"],
    "template_published":          ["AS-05"],
    "template_installed":          [],  # 被动获得, 无防刷
    # 基础积分事件
    "daily_checkin":               ["AS-01", "AS-03"],
    "course_complete":             ["AS-01"],
    "assessment_complete":         ["AS-01"],
    "behavior_attempt":            ["AS-01", "AS-03"],
    "stage_transition":            ["AS-05"],
    "path_contribution":           ["AS-01", "AS-02"],
    "content_publish":             ["AS-01", "AS-02"],
    "community_help":              ["AS-01", "AS-02", "AS-03"],
    "case_share":                  ["AS-01", "AS-02"],
    "mentee_graduation":           ["AS-04"],
    "course_develop":              [],
    "invite_register":             [],
    "train_l1_peer":               ["AS-04"],
    "workshop_held":               [],
    "standard_participation":      [],
    # V4.0 行为联动
    "assessment_submit":           ["AS-01", "AS-06"],
    "micro_action_complete":       ["AS-01", "AS-03"],
    "challenge_checkin":           ["AS-01", "AS-03"],
    "challenge_complete":          ["AS-05"],
    "reflection_create":           ["AS-01"],
    "contract_sign":               ["AS-01"],
    "companion_add":               ["AS-01", "AS-04"],
    "contribution_submit":         ["AS-01", "AS-02"],
    "food_recognize":              ["AS-01", "AS-03"],
    "peer_accept":                 ["AS-01", "AS-04"],
    "feedback_positive":           ["AS-01"],
    "composition_created":         [],
}


def get_strategies_for_event(event_type: str) -> List[str]:
    """查询指定事件适用的防刷策略列表"""
    return EVENT_STRATEGY_MAP.get(event_type, [])
