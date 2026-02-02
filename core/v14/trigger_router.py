"""
行为健康数字平台 - v14 Trigger 事件路由增强
Enhanced Trigger Event Routing for v14

[v14-NEW] 在v11 TriggerEngine基础上增加事件路由系统

原有功能（v11）：
- recognize_glucose_triggers(): 血糖触发识别

新增功能（v14）：
- emit_event(): 发射触发事件
- process_event(): 处理触发事件
- find_route(): 查找路由规则

使用方式：
    from core.v14.trigger_router import get_trigger_router
    
    router = get_trigger_router()
    router.emit_event(user_id=1001, event_type="TASK", event_name="task_fail", ...)
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
import time


class TriggerEventType(str, Enum):
    """触发事件类型"""
    CGM = "CGM"              # 血糖监测
    TASK = "TASK"            # 任务执行
    USAGE = "USAGE"          # 使用行为
    EMOTION = "EMOTION"      # 情绪信号
    RHYTHM = "RHYTHM"        # 节律信号


class TriggerLevel(str, Enum):
    """触发等级"""
    INFO = "info"           # 信息
    WARN = "warn"           # 警告
    RISK = "risk"           # 风险
    CRITICAL = "critical"   # 危急


class EngineAction(str, Enum):
    """引擎动作"""
    LOG = "log"              # 仅记录
    RUN = "run"              # 运行决策
    FREEZE = "freeze"        # 冻结Workflow
    DOWNGRADE = "downgrade"  # 降级干预
    ESCALATE = "escalate"    # 升级到人工


@dataclass
class TriggerEvent:
    """触发事件"""
    event_id: str
    user_id: int
    event_type: TriggerEventType
    event_name: str
    event_value: Dict[str, Any]
    level: TriggerLevel
    source: str
    occurred_at: datetime = field(default_factory=datetime.now)
    processed: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "event_type": self.event_type.value,
            "event_name": self.event_name,
            "event_value": self.event_value,
            "level": self.level.value,
            "source": self.source,
            "occurred_at": self.occurred_at.isoformat(),
            "processed": self.processed
        }


@dataclass
class TriggerRoute:
    """触发路由规则"""
    event_type: TriggerEventType
    event_name: str
    min_level: TriggerLevel
    engine_action: EngineAction
    workflow_hint: str
    priority: int = 0


# ============================================
# 默认路由规则
# ============================================

DEFAULT_ROUTES: List[TriggerRoute] = [
    # CGM触发器（生理优先级最高）
    TriggerRoute(TriggerEventType.CGM, "low_glucose", TriggerLevel.CRITICAL, 
                 EngineAction.FREEZE, "safety", 100),
    TriggerRoute(TriggerEventType.CGM, "high_glucose", TriggerLevel.RISK, 
                 EngineAction.RUN, "intervention", 90),
    TriggerRoute(TriggerEventType.CGM, "glucose_spike", TriggerLevel.WARN, 
                 EngineAction.RUN, "stabilize", 80),
    TriggerRoute(TriggerEventType.CGM, "dawn_risk", TriggerLevel.RISK, 
                 EngineAction.RUN, "prevention", 85),
    
    # 任务触发器
    TriggerRoute(TriggerEventType.TASK, "task_fail", TriggerLevel.INFO, 
                 EngineAction.LOG, "record", 10),
    TriggerRoute(TriggerEventType.TASK, "task_fail_3d", TriggerLevel.WARN, 
                 EngineAction.RUN, "downgrade", 50),
    TriggerRoute(TriggerEventType.TASK, "task_skip_chain", TriggerLevel.RISK, 
                 EngineAction.RUN, "resistance", 60),
    TriggerRoute(TriggerEventType.TASK, "task_complete", TriggerLevel.INFO, 
                 EngineAction.LOG, "positive", 5),
    
    # 使用触发器
    TriggerRoute(TriggerEventType.USAGE, "inactive_24h", TriggerLevel.INFO, 
                 EngineAction.LOG, "monitor", 15),
    TriggerRoute(TriggerEventType.USAGE, "inactive_48h", TriggerLevel.WARN, 
                 EngineAction.RUN, "recall", 30),
    TriggerRoute(TriggerEventType.USAGE, "inactive_7d", TriggerLevel.RISK, 
                 EngineAction.ESCALATE, "human", 70),
    TriggerRoute(TriggerEventType.USAGE, "rage_exit", TriggerLevel.CRITICAL, 
                 EngineAction.ESCALATE, "safety", 95),
    
    # 情绪触发器
    TriggerRoute(TriggerEventType.EMOTION, "negative_sentiment", TriggerLevel.WARN, 
                 EngineAction.RUN, "empathy", 40),
    TriggerRoute(TriggerEventType.EMOTION, "frustration", TriggerLevel.RISK, 
                 EngineAction.DOWNGRADE, "support", 65),
    TriggerRoute(TriggerEventType.EMOTION, "crisis_signal", TriggerLevel.CRITICAL, 
                 EngineAction.ESCALATE, "safety", 100),
    
    # 节律触发器
    TriggerRoute(TriggerEventType.RHYTHM, "rhythm_drift", TriggerLevel.INFO, 
                 EngineAction.LOG, "monitor", 20),
    TriggerRoute(TriggerEventType.RHYTHM, "rhythm_strain", TriggerLevel.WARN, 
                 EngineAction.DOWNGRADE, "reduce", 75),
    TriggerRoute(TriggerEventType.RHYTHM, "rhythm_collapse", TriggerLevel.CRITICAL, 
                 EngineAction.FREEZE, "protect", 100),
]


class TriggerRouter:
    """
    Trigger 事件路由器 [v14-NEW]
    
    接收各类触发事件，根据路由规则决定引擎动作
    """
    
    def __init__(self):
        self.routes = sorted(DEFAULT_ROUTES, key=lambda r: r.priority, reverse=True)
        self._event_queue: List[TriggerEvent] = []
        self._processed_events: List[Dict] = []
        self._event_counter = 0
        logger.info("[v14] Trigger 路由器初始化完成")
    
    def _generate_event_id(self, user_id: int) -> str:
        """生成事件ID"""
        self._event_counter += 1
        return f"evt_{user_id}_{int(time.time()*1000)}_{self._event_counter}"
    
    def emit_event(
        self,
        user_id: int,
        event_type: TriggerEventType,
        event_name: str,
        event_value: Dict[str, Any],
        level: TriggerLevel,
        source: str = "system"
    ) -> Optional[TriggerEvent]:
        """
        发射触发事件
        
        Args:
            user_id: 用户ID
            event_type: 事件类型
            event_name: 事件名称
            event_value: 事件数据
            level: 事件等级
            source: 来源
        
        Returns:
            TriggerEvent 或 None（如果功能未启用）
        """
        from core.v14.config import is_feature_enabled
        
        if not is_feature_enabled("ENABLE_TRIGGER_EVENT_ROUTING"):
            logger.debug("[v14] 事件路由未启用，事件被忽略")
            return None
        
        event = TriggerEvent(
            event_id=self._generate_event_id(user_id),
            user_id=user_id,
            event_type=event_type,
            event_name=event_name,
            event_value=event_value,
            level=level,
            source=source
        )
        
        self._event_queue.append(event)
        logger.info(f"[v14] 触发事件: {event_name} | 用户: {user_id} | "
                   f"等级: {level.value} | 来源: {source}")
        
        return event
    
    def find_route(self, event: TriggerEvent) -> Optional[TriggerRoute]:
        """查找匹配的路由规则"""
        level_order = [TriggerLevel.INFO, TriggerLevel.WARN, 
                       TriggerLevel.RISK, TriggerLevel.CRITICAL]
        
        for route in self.routes:
            if route.event_type != event.event_type:
                continue
            if route.event_name != event.event_name:
                continue
            # 检查等级
            if level_order.index(event.level) >= level_order.index(route.min_level):
                return route
        
        return None
    
    def process_event(self, event: TriggerEvent) -> Dict[str, Any]:
        """
        处理触发事件
        
        Returns:
            处理结果字典
        """
        route = self.find_route(event)
        
        if not route:
            logger.debug(f"[v14] 事件 {event.event_name} 无匹配路由，仅记录")
            return {
                "event": event.to_dict(),
                "action": EngineAction.LOG.value,
                "reason": "no_route_match"
            }
        
        logger.info(f"[v14] 事件路由: {event.event_name} -> {route.engine_action.value}")
        
        result = {
            "event": event.to_dict(),
            "action": route.engine_action.value,
            "workflow_hint": route.workflow_hint,
            "priority": route.priority
        }
        
        event.processed = True
        self._processed_events.append(result)
        
        # 触发相应动作
        self._execute_action(event, route)
        
        return result
    
    def _execute_action(self, event: TriggerEvent, route: TriggerRoute):
        """执行路由动作"""
        if route.engine_action == EngineAction.FREEZE:
            logger.warning(f"[v14] 用户 {event.user_id} Workflow被冻结: {event.event_name}")
            # TODO: 调用Workflow冻结接口
            
        elif route.engine_action == EngineAction.ESCALATE:
            logger.warning(f"[v14] 用户 {event.user_id} 升级到人工: {event.event_name}")
            # TODO: 调用人工升级接口
            
        elif route.engine_action == EngineAction.DOWNGRADE:
            logger.info(f"[v14] 用户 {event.user_id} 干预降级: {event.event_name}")
            # TODO: 调用干预降级接口
            
        elif route.engine_action == EngineAction.RUN:
            logger.info(f"[v14] 用户 {event.user_id} 运行决策引擎: {event.event_name}")
            # TODO: 调用决策引擎
    
    def process_pending_events(self) -> List[Dict]:
        """处理所有待处理事件"""
        results = []
        while self._event_queue:
            event = self._event_queue.pop(0)
            result = self.process_event(event)
            results.append(result)
        return results
    
    def get_event_stats(self) -> Dict[str, Any]:
        """获取事件统计"""
        return {
            "pending_count": len(self._event_queue),
            "processed_count": len(self._processed_events),
            "route_count": len(self.routes)
        }
    
    # ============================================
    # 便捷方法
    # ============================================
    
    def emit_cgm_low(self, user_id: int, value: float) -> Optional[TriggerEvent]:
        """发射低血糖事件"""
        return self.emit_event(
            user_id=user_id,
            event_type=TriggerEventType.CGM,
            event_name="low_glucose",
            event_value={"glucose": value, "threshold": 3.9},
            level=TriggerLevel.CRITICAL,
            source="cgm"
        )
    
    def emit_cgm_high(self, user_id: int, value: float) -> Optional[TriggerEvent]:
        """发射高血糖事件"""
        return self.emit_event(
            user_id=user_id,
            event_type=TriggerEventType.CGM,
            event_name="high_glucose",
            event_value={"glucose": value, "threshold": 10.0},
            level=TriggerLevel.RISK,
            source="cgm"
        )
    
    def emit_task_fail(self, user_id: int, task_id: str, 
                       consecutive_days: int = 0) -> Optional[TriggerEvent]:
        """发射任务失败事件"""
        from core.v14.config import is_feature_enabled
        
        if not is_feature_enabled("ENABLE_TRIGGER_TASK_EVENTS"):
            return None
        
        if consecutive_days >= 3:
            event_name = "task_fail_3d"
            level = TriggerLevel.WARN
        else:
            event_name = "task_fail"
            level = TriggerLevel.INFO
        
        return self.emit_event(
            user_id=user_id,
            event_type=TriggerEventType.TASK,
            event_name=event_name,
            event_value={"task_id": task_id, "consecutive_days": consecutive_days},
            level=level,
            source="task_service"
        )
    
    def emit_inactive(self, user_id: int, hours: int) -> Optional[TriggerEvent]:
        """发射不活跃事件"""
        from core.v14.config import is_feature_enabled
        
        if not is_feature_enabled("ENABLE_TRIGGER_USAGE_EVENTS"):
            return None
        
        if hours >= 168:  # 7天
            event_name = "inactive_7d"
            level = TriggerLevel.RISK
        elif hours >= 48:
            event_name = "inactive_48h"
            level = TriggerLevel.WARN
        else:
            event_name = "inactive_24h"
            level = TriggerLevel.INFO
        
        return self.emit_event(
            user_id=user_id,
            event_type=TriggerEventType.USAGE,
            event_name=event_name,
            event_value={"inactive_hours": hours},
            level=level,
            source="usage_tracker"
        )
    
    def emit_rhythm_signal(self, user_id: int, phase: str, 
                           confidence: float) -> Optional[TriggerEvent]:
        """发射节律信号事件"""
        from core.v14.config import is_feature_enabled
        
        if not is_feature_enabled("ENABLE_RHYTHM_MODEL"):
            return None
        
        phase_mapping = {
            "DRIFT": ("rhythm_drift", TriggerLevel.INFO),
            "STRAIN": ("rhythm_strain", TriggerLevel.WARN),
            "COLLAPSE_RISK": ("rhythm_collapse", TriggerLevel.CRITICAL)
        }
        
        if phase not in phase_mapping:
            return None
        
        event_name, level = phase_mapping[phase]
        
        return self.emit_event(
            user_id=user_id,
            event_type=TriggerEventType.RHYTHM,
            event_name=event_name,
            event_value={"phase": phase, "confidence": confidence},
            level=level,
            source="rhythm_engine"
        )


# ============================================
# 全局单例
# ============================================

_trigger_router: Optional[TriggerRouter] = None


def get_trigger_router() -> Optional[TriggerRouter]:
    """获取Trigger路由器单例"""
    global _trigger_router
    
    from core.v14.config import is_feature_enabled
    
    if not is_feature_enabled("ENABLE_TRIGGER_EVENT_ROUTING"):
        logger.debug("[v14] Trigger事件路由未启用")
        return None
    
    if _trigger_router is None:
        _trigger_router = TriggerRouter()
    
    return _trigger_router
