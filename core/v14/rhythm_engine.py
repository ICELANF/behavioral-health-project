"""
行为健康数字平台 - 节律引擎
Rhythm Engine for Behavioral Health

[v14-NEW] 全新模块

核心概念：
- 行为健康失败有"相位变化"：稳定期 → 漂移期 → 压力期 → 崩溃风险期
- 节律模型用于提前感知风险，而非事后纠正
- 核心原则：节律只能降低系统强度，不能提高（伦理约束）

使用方式：
    from core.v14.rhythm_engine import get_rhythm_engine, RhythmPhase
    
    rhythm = get_rhythm_engine()
    result = rhythm.detect_composite_rhythm(user_id, data)
    
    if result.phase == RhythmPhase.COLLAPSE_RISK:
        # 冻结当前干预，升级到人工
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import statistics


class RhythmPhase(str, Enum):
    """节律相位"""
    STABLE = "STABLE"              # 稳定期 - 正常执行
    DRIFT = "DRIFT"                # 漂移期 - 监控记录
    STRAIN = "STRAIN"              # 压力期 - 降级干预
    COLLAPSE_RISK = "COLLAPSE_RISK" # 崩溃风险期 - 冻结+升级


class RhythmDomain(str, Enum):
    """节律域"""
    CGM = "cgm"              # 血糖节律
    ACTIVITY = "activity"    # 活动节律
    SLEEP = "sleep"          # 睡眠节律
    TASK = "task"            # 任务执行节律
    EMOTION = "emotion"      # 情绪节律
    COMPOSITE = "composite"  # 综合节律


@dataclass
class RhythmSignal:
    """节律信号"""
    user_id: int
    domain: RhythmDomain
    phase: RhythmPhase
    confidence: float           # 置信度 0-1
    intensity_cap: float        # 干预强度上限 0-1
    evidence: Dict[str, Any]    # 证据数据
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "domain": self.domain.value,
            "phase": self.phase.value,
            "confidence": self.confidence,
            "intensity_cap": self.intensity_cap,
            "evidence": self.evidence,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class RhythmPolicy:
    """节律策略"""
    phase: RhythmPhase
    action: str                 # allow / monitor / downgrade / freeze
    intensity_cap: float        # 最大干预强度
    escalate_to_human: bool = False
    notify_coach: bool = False


# 默认节律策略（伦理约束：只能降级）
DEFAULT_RHYTHM_POLICIES: List[RhythmPolicy] = [
    RhythmPolicy(
        phase=RhythmPhase.STABLE,
        action="allow",
        intensity_cap=1.0,
        escalate_to_human=False
    ),
    RhythmPolicy(
        phase=RhythmPhase.DRIFT,
        action="monitor",
        intensity_cap=0.8,
        escalate_to_human=False,
        notify_coach=True
    ),
    RhythmPolicy(
        phase=RhythmPhase.STRAIN,
        action="downgrade",
        intensity_cap=0.5,
        escalate_to_human=False,
        notify_coach=True
    ),
    RhythmPolicy(
        phase=RhythmPhase.COLLAPSE_RISK,
        action="freeze",
        intensity_cap=0.0,
        escalate_to_human=True,
        notify_coach=True
    ),
]


class RhythmEngine:
    """
    节律引擎 [v14-NEW]
    
    检测用户行为节律的相位变化，提前感知崩溃风险
    """
    
    def __init__(self):
        self.policies = {p.phase: p for p in DEFAULT_RHYTHM_POLICIES}
        self._signal_history: Dict[int, List[RhythmSignal]] = {}  # user_id -> signals
        logger.info("[v14] 节律引擎初始化完成")
    
    # ============================================
    # 核心检测方法
    # ============================================
    
    def detect_cgm_rhythm(
        self,
        user_id: int,
        glucose_values: List[float],
        hours: int = 24
    ) -> RhythmSignal:
        """
        检测血糖节律
        
        基于血糖变异系数(CV)判断：
        - CV < 20%: STABLE
        - CV 20-30%: DRIFT
        - CV 30-40%: STRAIN
        - CV > 40%: COLLAPSE_RISK
        """
        if not glucose_values or len(glucose_values) < 3:
            return self._create_signal(user_id, RhythmDomain.CGM, RhythmPhase.STABLE, 
                                       0.5, {"reason": "数据不足"})
        
        mean_val = statistics.mean(glucose_values)
        std_val = statistics.stdev(glucose_values) if len(glucose_values) > 1 else 0
        cv = (std_val / mean_val) * 100 if mean_val > 0 else 0
        
        # 判断相位
        if cv < 20:
            phase = RhythmPhase.STABLE
            confidence = 0.9
        elif cv < 30:
            phase = RhythmPhase.DRIFT
            confidence = 0.75
        elif cv < 40:
            phase = RhythmPhase.STRAIN
            confidence = 0.8
        else:
            phase = RhythmPhase.COLLAPSE_RISK
            confidence = 0.85
        
        evidence = {
            "cv": round(cv, 2),
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "samples": len(glucose_values),
            "hours": hours
        }
        
        signal = self._create_signal(user_id, RhythmDomain.CGM, phase, confidence, evidence)
        self._record_signal(signal)
        
        return signal
    
    def detect_task_rhythm(
        self,
        user_id: int,
        task_results: List[bool],  # True=完成, False=未完成
        days: int = 7
    ) -> RhythmSignal:
        """
        检测任务执行节律
        
        基于任务完成率判断：
        - 完成率 > 80%: STABLE
        - 完成率 60-80%: DRIFT
        - 完成率 40-60%: STRAIN
        - 完成率 < 40%: COLLAPSE_RISK
        """
        if not task_results:
            return self._create_signal(user_id, RhythmDomain.TASK, RhythmPhase.STABLE,
                                       0.5, {"reason": "无任务数据"})
        
        completion_rate = sum(task_results) / len(task_results)
        
        # 检测连续失败
        consecutive_fails = 0
        for result in reversed(task_results):
            if not result:
                consecutive_fails += 1
            else:
                break
        
        # 判断相位
        if completion_rate > 0.8:
            phase = RhythmPhase.STABLE
            confidence = 0.9
        elif completion_rate > 0.6:
            phase = RhythmPhase.DRIFT
            confidence = 0.75
        elif completion_rate > 0.4:
            phase = RhythmPhase.STRAIN
            confidence = 0.8
        else:
            phase = RhythmPhase.COLLAPSE_RISK
            confidence = 0.85
        
        # 连续失败3天以上直接升级
        if consecutive_fails >= 3 and phase.value < RhythmPhase.STRAIN.value:
            phase = RhythmPhase.STRAIN
            confidence = 0.85
        
        evidence = {
            "completion_rate": round(completion_rate, 2),
            "total_tasks": len(task_results),
            "completed": sum(task_results),
            "consecutive_fails": consecutive_fails,
            "days": days
        }
        
        signal = self._create_signal(user_id, RhythmDomain.TASK, phase, confidence, evidence)
        self._record_signal(signal)
        
        return signal
    
    def detect_activity_rhythm(
        self,
        user_id: int,
        inactive_hours: int
    ) -> RhythmSignal:
        """
        检测活动节律（基于不活跃时长）
        
        - < 24h: STABLE
        - 24-48h: DRIFT
        - 48-72h: STRAIN
        - > 72h: COLLAPSE_RISK
        """
        if inactive_hours < 24:
            phase = RhythmPhase.STABLE
            confidence = 0.9
        elif inactive_hours < 48:
            phase = RhythmPhase.DRIFT
            confidence = 0.75
        elif inactive_hours < 72:
            phase = RhythmPhase.STRAIN
            confidence = 0.8
        else:
            phase = RhythmPhase.COLLAPSE_RISK
            confidence = 0.85
        
        evidence = {
            "inactive_hours": inactive_hours,
            "threshold_24h": inactive_hours >= 24,
            "threshold_48h": inactive_hours >= 48,
            "threshold_72h": inactive_hours >= 72
        }
        
        signal = self._create_signal(user_id, RhythmDomain.ACTIVITY, phase, confidence, evidence)
        self._record_signal(signal)
        
        return signal
    
    def detect_composite_rhythm(
        self,
        user_id: int,
        domain_signals: List[RhythmSignal]
    ) -> RhythmSignal:
        """
        检测综合节律（多域加权融合）
        
        取最差相位（保守策略），加权计算置信度
        """
        if not domain_signals:
            return self._create_signal(user_id, RhythmDomain.COMPOSITE, RhythmPhase.STABLE,
                                       0.5, {"reason": "无域信号"})
        
        # 相位优先级排序
        phase_order = [RhythmPhase.STABLE, RhythmPhase.DRIFT, 
                       RhythmPhase.STRAIN, RhythmPhase.COLLAPSE_RISK]
        
        # 取最差相位
        worst_phase = max(domain_signals, 
                         key=lambda s: phase_order.index(s.phase)).phase
        
        # 加权置信度
        total_confidence = sum(s.confidence for s in domain_signals)
        avg_confidence = total_confidence / len(domain_signals) if domain_signals else 0.5
        
        evidence = {
            "domain_count": len(domain_signals),
            "domains": [s.domain.value for s in domain_signals],
            "phases": [s.phase.value for s in domain_signals],
            "worst_domain": next((s.domain.value for s in domain_signals 
                                 if s.phase == worst_phase), None)
        }
        
        signal = self._create_signal(user_id, RhythmDomain.COMPOSITE, worst_phase,
                                     avg_confidence, evidence)
        self._record_signal(signal)
        
        return signal
    
    # ============================================
    # 策略应用
    # ============================================
    
    def get_policy(self, phase: RhythmPhase) -> RhythmPolicy:
        """获取相位对应的策略"""
        return self.policies.get(phase, self.policies[RhythmPhase.STABLE])
    
    def apply_policy(self, signal: RhythmSignal) -> Dict[str, Any]:
        """
        应用节律策略
        
        返回应该采取的行动
        """
        from core.v14.config import feature_flags
        
        policy = self.get_policy(signal.phase)
        
        result = {
            "phase": signal.phase.value,
            "action": policy.action,
            "intensity_cap": policy.intensity_cap,
            "escalate_to_human": policy.escalate_to_human,
            "notify_coach": policy.notify_coach,
            "confidence": signal.confidence,
            "evidence": signal.evidence
        }
        
        # 伦理约束检查
        if feature_flags.RHYTHM_ONLY_DOWNGRADE:
            result["constraint"] = "only_downgrade"
        
        # 崩溃风险时冻结
        if signal.phase == RhythmPhase.COLLAPSE_RISK and feature_flags.RHYTHM_FREEZE_ON_COLLAPSE:
            result["freeze"] = True
            logger.warning(f"[v14] 用户 {signal.user_id} 节律崩溃风险，已冻结干预")
        
        return result
    
    # ============================================
    # 辅助方法
    # ============================================
    
    def _create_signal(
        self,
        user_id: int,
        domain: RhythmDomain,
        phase: RhythmPhase,
        confidence: float,
        evidence: Dict[str, Any]
    ) -> RhythmSignal:
        """创建节律信号"""
        policy = self.get_policy(phase)
        return RhythmSignal(
            user_id=user_id,
            domain=domain,
            phase=phase,
            confidence=confidence,
            intensity_cap=policy.intensity_cap,
            evidence=evidence
        )
    
    def _record_signal(self, signal: RhythmSignal):
        """记录信号历史"""
        if signal.user_id not in self._signal_history:
            self._signal_history[signal.user_id] = []
        
        self._signal_history[signal.user_id].append(signal)
        
        # 只保留最近100条
        if len(self._signal_history[signal.user_id]) > 100:
            self._signal_history[signal.user_id] = \
                self._signal_history[signal.user_id][-100:]
        
        logger.info(f"[v14] 节律信号: user={signal.user_id} domain={signal.domain.value} "
                   f"phase={signal.phase.value} confidence={signal.confidence:.2f}")
    
    def get_user_history(self, user_id: int, limit: int = 20) -> List[RhythmSignal]:
        """获取用户节律历史"""
        signals = self._signal_history.get(user_id, [])
        return signals[-limit:]
    
    def get_current_phase(self, user_id: int) -> Optional[RhythmPhase]:
        """获取用户当前综合相位"""
        signals = self.get_user_history(user_id, limit=5)
        composite = [s for s in signals if s.domain == RhythmDomain.COMPOSITE]
        
        if composite:
            return composite[-1].phase
        return None


# ============================================
# 全局单例
# ============================================

_rhythm_engine: Optional[RhythmEngine] = None


def get_rhythm_engine() -> RhythmEngine:
    """获取节律引擎单例"""
    global _rhythm_engine
    
    from core.v14.config import is_feature_enabled
    
    if not is_feature_enabled("ENABLE_RHYTHM_MODEL"):
        logger.debug("[v14] 节律模型未启用")
        return None
    
    if _rhythm_engine is None:
        _rhythm_engine = RhythmEngine()
    
    return _rhythm_engine
