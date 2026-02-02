"""
行为健康数字平台 - 行为引擎
Behavior Engine with Hot-Reload Capability

[v15-NEW] 逻辑引擎模块

核心功能：
1. 从JSON配置文件加载行为规则
2. 支持热重载（不重启服务更新规则）
3. 规则匹配与动作分发
4. 条件表达式安全执行

替代所有 if user.stage == 'xxx' 的硬编码
"""
import json
import os
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from loguru import logger
import threading
import time

from services.logic_engine.schema.rules_definition import (
    BehaviorLibrary,
    TriggerRule,
    ActionPackage,
    RiskLevel,
    RuleValidator
)


class ConditionEvaluator:
    """
    条件表达式安全执行器
    
    支持的变量命名空间：
    - user: 用户状态
    - snippet: 当前文本片段
    - data: 设备数据
    - context: 上下文信息
    """
    
    # 安全的内置函数白名单
    SAFE_BUILTINS = {
        'any': any,
        'all': all,
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'min': min,
        'max': max,
        'abs': abs,
        'sum': sum,
        'True': True,
        'False': False,
        'None': None,
    }
    
    @classmethod
    def evaluate(
        cls,
        condition: str,
        user: Dict[str, Any] = None,
        snippet: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> bool:
        """
        安全执行条件表达式
        
        Args:
            condition: 条件表达式
            user: 用户状态
            snippet: 文本片段
            data: 设备数据
            context: 上下文
        
        Returns:
            bool: 条件是否满足
        """
        # 构建安全的执行环境
        safe_globals = {"__builtins__": cls.SAFE_BUILTINS}
        safe_locals = {
            'user': DotDict(user or {}),
            'snippet': DotDict(snippet or {}),
            'data': DotDict(data or {}),
            'context': DotDict(context or {}),
            're': SafeRe(),  # 安全的正则
            'kw': snippet.get('text', '') if snippet else '',  # 快捷访问文本
        }
        
        try:
            result = eval(condition, safe_globals, safe_locals)
            return bool(result)
        except Exception as e:
            logger.warning(f"[BehaviorEngine] 条件执行失败: {condition} - {e}")
            return False


class DotDict(dict):
    """支持点号访问的字典"""
    
    def __getattr__(self, key):
        try:
            value = self[key]
            if isinstance(value, dict):
                return DotDict(value)
            return value
        except KeyError:
            return None
    
    def __setattr__(self, key, value):
        self[key] = value


class SafeRe:
    """安全的正则表达式封装"""
    
    @staticmethod
    def match(pattern: str, text: str) -> bool:
        try:
            return bool(re.match(pattern, text or ''))
        except:
            return False
    
    @staticmethod
    def search(pattern: str, text: str) -> bool:
        try:
            return bool(re.search(pattern, text or ''))
        except:
            return False


class TriggerCooldown:
    """触发冷却管理"""
    
    def __init__(self):
        self._cooldowns: Dict[str, Dict[str, datetime]] = {}  # user_id -> {trigger_id: last_time}
        self._daily_counts: Dict[str, Dict[str, int]] = {}  # user_id -> {trigger_id: count}
        self._last_reset: datetime = datetime.now()
    
    def can_trigger(self, user_id: str, trigger: TriggerRule) -> bool:
        """检查是否可以触发"""
        self._maybe_reset_daily()
        
        user_cooldowns = self._cooldowns.get(user_id, {})
        user_counts = self._daily_counts.get(user_id, {})
        
        # 检查冷却时间
        if trigger.id in user_cooldowns:
            last_time = user_cooldowns[trigger.id]
            cooldown_end = last_time + timedelta(minutes=trigger.cooldown_minutes)
            if datetime.now() < cooldown_end:
                return False
        
        # 检查每日次数
        if trigger.id in user_counts:
            if user_counts[trigger.id] >= trigger.max_daily_triggers:
                return False
        
        return True
    
    def record_trigger(self, user_id: str, trigger_id: str):
        """记录触发"""
        if user_id not in self._cooldowns:
            self._cooldowns[user_id] = {}
        if user_id not in self._daily_counts:
            self._daily_counts[user_id] = {}
        
        self._cooldowns[user_id][trigger_id] = datetime.now()
        self._daily_counts[user_id][trigger_id] = self._daily_counts[user_id].get(trigger_id, 0) + 1
    
    def _maybe_reset_daily(self):
        """每日重置计数"""
        now = datetime.now()
        if now.date() != self._last_reset.date():
            self._daily_counts = {}
            self._last_reset = now


class BehaviorEngine:
    """
    行为引擎
    
    核心职责：
    1. 加载和管理行为母库
    2. 匹配触发规则
    3. 返回对应的动作包
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化行为引擎
        
        Args:
            config_path: 配置文件路径，默认为 configs/behavior/behavior_rules.json
        """
        if config_path is None:
            # 默认路径
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "configs" / "behavior" / "behavior_rules.json"
        
        self.config_path = Path(config_path)
        self.library: Optional[BehaviorLibrary] = None
        self._config_hash: str = ""
        self._cooldown = TriggerCooldown()
        self._lock = threading.Lock()
        
        # 初始加载
        self.reload()
        
        logger.info(f"[BehaviorEngine] 初始化完成: {self.config_path}")
    
    def reload(self) -> bool:
        """
        重新加载配置
        
        Returns:
            bool: 是否成功加载
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                raw_data = f.read()
                
            # 检查是否有变化
            new_hash = hashlib.md5(raw_data.encode()).hexdigest()
            if new_hash == self._config_hash:
                return True  # 无变化
            
            # 解析配置
            config_dict = json.loads(raw_data)
            
            with self._lock:
                self.library = BehaviorLibrary(**config_dict)
                self._config_hash = new_hash
            
            # 验证配置
            valid, errors = RuleValidator.validate_library(self.library)
            if not valid:
                for error in errors:
                    logger.warning(f"[BehaviorEngine] 配置警告: {error}")
            
            logger.info(f"[BehaviorEngine] 配置加载成功: "
                       f"stages={len(self.library.stages)} "
                       f"triggers={len(self.library.triggers)} "
                       f"actions={len(self.library.action_packages)}")
            
            return True
            
        except Exception as e:
            logger.error(f"[BehaviorEngine] 配置加载失败: {e}")
            return False
    
    def evaluate_state(
        self,
        user_id: str,
        user_context: Dict[str, Any],
        new_snippet: Dict[str, Any] = None,
        device_data: Dict[str, Any] = None
    ) -> Optional[Tuple[TriggerRule, ActionPackage]]:
        """
        评估状态并返回匹配的动作
        
        这是核心方法，替代所有 if user.stage == 'xxx' 的硬编码
        
        Args:
            user_id: 用户ID
            user_context: 用户上下文（包含stage, bpt_type等）
            new_snippet: 新的文本片段
            device_data: 设备数据
        
        Returns:
            Optional[Tuple[TriggerRule, ActionPackage]]: 匹配的规则和动作包
        """
        if not self.library:
            return None
        
        user_stage = user_context.get('stage', 'S0')
        
        # 按优先级排序触发规则
        sorted_triggers = sorted(
            self.library.triggers,
            key=lambda t: (
                {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}.get(t.priority.value, 2),
                {'L4': 0, 'L3': 1, 'L2': 2, 'L1': 3}.get(t.risk_level.value, 2)
            )
        )
        
        for trigger in sorted_triggers:
            # 检查是否启用
            if not trigger.enabled:
                continue
            
            # 检查阶段适用性
            if trigger.applicable_stages:
                if user_stage not in trigger.applicable_stages:
                    continue
            
            # 检查冷却
            if not self._cooldown.can_trigger(user_id, trigger):
                continue
            
            # 执行条件匹配
            matched = ConditionEvaluator.evaluate(
                trigger.condition,
                user=user_context,
                snippet=new_snippet,
                data=device_data
            )
            
            if matched:
                # 获取对应的动作包
                action = self.library.get_action_by_id(trigger.action_ref)
                if action and action.enabled:
                    # 记录触发
                    self._cooldown.record_trigger(user_id, trigger.id)
                    
                    logger.info(f"[BehaviorEngine] 规则匹配: "
                               f"user={user_id} trigger={trigger.id} "
                               f"action={action.action_id}")
                    
                    return trigger, action
        
        return None
    
    def get_action_by_trigger(self, trigger_id: str) -> Optional[ActionPackage]:
        """根据触发ID获取动作包"""
        if not self.library:
            return None
        
        trigger = self.library.get_trigger_by_id(trigger_id)
        if trigger:
            return self.library.get_action_by_id(trigger.action_ref)
        return None
    
    def get_action_by_id(self, action_id: str) -> Optional[ActionPackage]:
        """根据动作ID获取动作包"""
        if not self.library:
            return None
        return self.library.get_action_by_id(action_id)
    
    def get_stage_info(self, stage_id: str) -> Optional[Dict]:
        """获取阶段信息"""
        if not self.library:
            return None
        stage = self.library.stages.get(stage_id)
        if stage:
            return stage.dict()
        return None
    
    def get_applicable_triggers(self, stage_id: str) -> List[TriggerRule]:
        """获取适用于某阶段的所有触发规则"""
        if not self.library:
            return []
        return self.library.get_triggers_for_stage(stage_id)
    
    def list_all_actions(self) -> List[Dict]:
        """列出所有动作包"""
        if not self.library:
            return []
        return [action.dict() for action in self.library.action_packages.values()]
    
    def list_all_triggers(self) -> List[Dict]:
        """列出所有触发规则"""
        if not self.library:
            return []
        return [trigger.dict() for trigger in self.library.triggers]
    
    def validate_condition(self, condition: str) -> Tuple[bool, Optional[str]]:
        """验证条件表达式"""
        return RuleValidator.validate_condition(condition)


class LogicLoader:
    """
    母库加载器（兼容旧接口）
    
    提供简化的API访问BehaviorEngine
    """
    
    def __init__(self, file_path: str = None):
        self.engine = BehaviorEngine(file_path)
    
    @property
    def db(self) -> Optional[BehaviorLibrary]:
        return self.engine.library
    
    def get_action_by_trigger(self, trigger_id: str) -> Optional[Dict]:
        action = self.engine.get_action_by_trigger(trigger_id)
        return action.dict() if action else None
    
    def reload(self) -> bool:
        return self.engine.reload()


# ============================================
# 热重载监控器（可选）
# ============================================

class ConfigWatcher:
    """
    配置文件监控器
    
    自动检测配置变化并重新加载
    """
    
    def __init__(self, engine: BehaviorEngine, interval: int = 30):
        self.engine = engine
        self.interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """启动监控"""
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info(f"[ConfigWatcher] 启动配置监控，间隔 {self.interval}s")
    
    def stop(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _watch_loop(self):
        while self._running:
            time.sleep(self.interval)
            self.engine.reload()


# ============================================
# 全局单例
# ============================================

_behavior_engine: Optional[BehaviorEngine] = None
_config_watcher: Optional[ConfigWatcher] = None


def get_behavior_engine() -> BehaviorEngine:
    """获取行为引擎单例"""
    global _behavior_engine
    if _behavior_engine is None:
        _behavior_engine = BehaviorEngine()
    return _behavior_engine


def start_config_watcher(interval: int = 30):
    """启动配置监控"""
    global _config_watcher
    if _config_watcher is None:
        _config_watcher = ConfigWatcher(get_behavior_engine(), interval)
        _config_watcher.start()


def stop_config_watcher():
    """停止配置监控"""
    global _config_watcher
    if _config_watcher:
        _config_watcher.stop()
        _config_watcher = None
