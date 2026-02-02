"""
行为健康数字平台 - 状态同步管理器
State Sync Manager - "一套输入，两套表述"

[v15-NEW] State Sync 服务

核心目标：
- 实现数据的"一套输入，两套表述"
- 面向 C 端：脱敏为"陪伴话术参数"
- 面向 B 端：升维为"风险诊断参数"

架构位置：
8003 质量审计服务 ←→ StateSyncManager ←→ 8000 主API

数据库表：user_state_sync
- 存储同一事件 ID 下，针对不同角色的分发视图内容
"""
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json
from loguru import logger

# 尝试导入数据库模块
try:
    from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Enum as SQLEnum
    from sqlalchemy.ext.declarative import declarative_base
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("[StateSync] SQLAlchemy 未安装，使用内存存储")


class ViewRole(str, Enum):
    """视图角色"""
    PATIENT = "patient"   # 患者端视图
    COACH = "coach"       # 教练端视图
    EXPERT = "expert"     # 专家端视图
    ADMIN = "admin"       # 管理端视图


class EventType(str, Enum):
    """事件类型"""
    TEXT_INPUT = "text_input"           # 文本输入
    DEVICE_DATA = "device_data"         # 设备数据
    TASK_COMPLETE = "task_complete"     # 任务完成
    TRIGGER_MATCH = "trigger_match"     # 触发匹配
    STAGE_CHANGE = "stage_change"       # 阶段变更
    RISK_ALERT = "risk_alert"           # 风险警报


class UiStyle(str, Enum):
    """UI风格"""
    WARM = "warm"               # 温暖陪伴
    ENCOURAGING = "encouraging"  # 鼓励支持
    NEUTRAL = "neutral"         # 中性客观
    ALERT = "alert"             # 警示提醒


# ============================================
# 数据模型
# ============================================

@dataclass
class ClientView:
    """C端视图 - 陪伴话术参数"""
    msg_type: str                    # 消息类型
    content: str                     # 脱敏内容
    ui_style: UiStyle = UiStyle.WARM # UI风格
    action_buttons: List[Dict] = field(default_factory=list)  # 操作按钮
    extra_data: Dict[str, Any] = field(default_factory=dict)  # 额外数据
    
    def to_dict(self) -> Dict:
        return {
            "msg_type": self.msg_type,
            "content": self.content,
            "ui_style": self.ui_style.value,
            "action_buttons": self.action_buttons,
            "extra_data": self.extra_data
        }


@dataclass
class CoachView:
    """B端视图 - 风险诊断参数"""
    risk_flag: str                   # 风险标记: GREEN, YELLOW, ORANGE, RED
    diagnosis: str                   # 诊断标签
    trigger_source: str              # 触发来源
    suggested_action: str            # 建议动作
    analysis_detail: Dict[str, Any] = field(default_factory=dict)  # 分析详情
    intervention_scripts: List[str] = field(default_factory=list)  # 干预话术
    
    def to_dict(self) -> Dict:
        return {
            "risk_flag": self.risk_flag,
            "diagnosis": self.diagnosis,
            "trigger_source": self.trigger_source,
            "suggested_action": self.suggested_action,
            "analysis_detail": self.analysis_detail,
            "intervention_scripts": self.intervention_scripts
        }


@dataclass
class ExpertView:
    """专家端视图 - 完整诊断参数"""
    raw_data: Dict[str, Any]         # 原始数据
    risk_assessment: Dict[str, Any]  # 风险评估
    ai_analysis: Dict[str, Any]      # AI分析结果
    audit_flags: List[str] = field(default_factory=list)  # 审计标记
    requires_review: bool = False    # 是否需要审核
    
    def to_dict(self) -> Dict:
        return {
            "raw_data": self.raw_data,
            "risk_assessment": self.risk_assessment,
            "ai_analysis": self.ai_analysis,
            "audit_flags": self.audit_flags,
            "requires_review": self.requires_review
        }


@dataclass
class StateSyncRecord:
    """状态同步记录"""
    event_id: str
    user_id: int
    event_type: EventType
    timestamp: datetime
    
    # 分发视图
    client_view: ClientView
    coach_view: CoachView
    expert_view: Optional[ExpertView] = None
    
    # 元信息
    trigger_id: Optional[str] = None
    action_id: Optional[str] = None
    processed: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "client_view": self.client_view.to_dict(),
            "coach_view": self.coach_view.to_dict(),
            "expert_view": self.expert_view.to_dict() if self.expert_view else None,
            "trigger_id": self.trigger_id,
            "action_id": self.action_id,
            "processed": self.processed
        }


# ============================================
# 话术模板库
# ============================================

COMPANION_TEMPLATES = {
    # 情绪相关
    "stress_detected": {
        "content": "感觉到你今天压力不小，要不要试试那个深呼吸？",
        "ui_style": UiStyle.WARM,
        "buttons": [
            {"text": "好的，开始", "action": "START_BREATHING"},
            {"text": "稍后再说", "action": "DISMISS"}
        ]
    },
    "emotional_eating": {
        "content": "有时候心情不好会想吃点东西，这很正常。不如我们先聊聊？",
        "ui_style": UiStyle.WARM,
        "buttons": [
            {"text": "聊一聊", "action": "START_CHAT"},
            {"text": "我没事", "action": "DISMISS"}
        ]
    },
    "low_motivation": {
        "content": "每个人都有不想动的时候，没关系的。今天就休息一下吧？",
        "ui_style": UiStyle.ENCOURAGING,
        "buttons": [
            {"text": "调整目标", "action": "ADJUST_GOAL"},
            {"text": "继续坚持", "action": "CONTINUE"}
        ]
    },
    
    # 健康数据相关
    "glucose_high": {
        "content": "血糖有点高哦，建议活动一下，比如散步15分钟？",
        "ui_style": UiStyle.NEUTRAL,
        "buttons": [
            {"text": "开始散步", "action": "START_WALKING"},
            {"text": "记录状态", "action": "LOG_STATE"}
        ]
    },
    "glucose_low": {
        "content": "血糖偏低了，请及时补充一些碳水化合物，比如几块糖果。",
        "ui_style": UiStyle.ALERT,
        "buttons": [
            {"text": "已处理", "action": "CONFIRM_HANDLED"},
            {"text": "需要帮助", "action": "REQUEST_HELP"}
        ]
    },
    "sleep_issue": {
        "content": "睡眠很重要呢，试试睡前放下手机，让身体自然放松？",
        "ui_style": UiStyle.WARM,
        "buttons": [
            {"text": "了解更多", "action": "LEARN_MORE"},
            {"text": "知道了", "action": "DISMISS"}
        ]
    },
    
    # 进度相关
    "task_completed": {
        "content": "太棒了！今天的任务完成了，继续保持！💪",
        "ui_style": UiStyle.ENCOURAGING,
        "buttons": [
            {"text": "查看进度", "action": "VIEW_PROGRESS"}
        ]
    },
    "streak_achieved": {
        "content": "已经连续坚持{days}天了，你真的很棒！",
        "ui_style": UiStyle.ENCOURAGING,
        "buttons": [
            {"text": "分享成就", "action": "SHARE"},
            {"text": "继续加油", "action": "DISMISS"}
        ]
    }
}


DIAGNOSIS_TEMPLATES = {
    "stress_detected": {
        "diagnosis": "Stress-induced Behavior Pattern (SIBP)",
        "suggested_action": "ADMINISTER_STRESS_RELIEF",
        "scripts": [
            "注意用户近期压力水平",
            "可以推送放松训练内容",
            "关注后续情绪变化"
        ]
    },
    "emotional_eating": {
        "diagnosis": "Stress-induced Compulsive Eating (SICE)",
        "suggested_action": "ADMINISTER_BAPS_SECTION_4",
        "scripts": [
            "用户存在情绪化进食倾向",
            "建议引导关注情绪而非食物",
            "可以推送正念饮食内容"
        ]
    },
    "low_motivation": {
        "diagnosis": "Motivation Decline Pattern (MDP)",
        "suggested_action": "ADJUST_INTERVENTION_INTENSITY",
        "scripts": [
            "用户动力下降，可能需要调整目标难度",
            "考虑增加社交支持元素",
            "评估是否存在其他阻碍因素"
        ]
    },
    "glucose_high": {
        "diagnosis": "Hyperglycemia Alert",
        "suggested_action": "RECOMMEND_PHYSICAL_ACTIVITY",
        "scripts": [
            "血糖数据偏高",
            "建议鼓励用户进行适量运动",
            "持续监测后续血糖变化"
        ]
    },
    "glucose_low": {
        "diagnosis": "Hypoglycemia Alert - URGENT",
        "suggested_action": "IMMEDIATE_CARB_INTAKE",
        "scripts": [
            "⚠️ 低血糖警报",
            "确保用户已及时补充碳水化合物",
            "如持续偏低需上报专家"
        ]
    }
}


# ============================================
# 状态同步管理器
# ============================================

class StateSyncManager:
    """
    状态同步管理器
    
    核心职责：
    1. 将原始事件数据转换为不同角色的视图
    2. 管理视图的存储和检索
    3. 支持分角色数据分发
    """
    
    def __init__(self):
        self._records: Dict[str, StateSyncRecord] = {}  # event_id -> record
        self._user_events: Dict[int, List[str]] = {}    # user_id -> [event_ids]
        logger.info("[StateSync] 状态同步管理器初始化")
    
    def process_event(
        self,
        user_id: int,
        event_type: EventType,
        raw_data: Dict[str, Any],
        trigger_id: Optional[str] = None,
        action_id: Optional[str] = None
    ) -> StateSyncRecord:
        """
        处理事件并生成分角色视图
        
        Args:
            user_id: 用户ID
            event_type: 事件类型
            raw_data: 原始数据
            trigger_id: 触发规则ID
            action_id: 动作包ID
        
        Returns:
            StateSyncRecord: 同步记录
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # 分析原始数据，确定模板类型
        template_key = self._determine_template_key(event_type, raw_data)
        
        # 生成 C 端视图（脱敏陪伴话术）
        client_view = self._build_client_view(template_key, raw_data)
        
        # 生成 B 端视图（风险诊断参数）
        coach_view = self._build_coach_view(template_key, raw_data)
        
        # 生成专家端视图（完整数据）
        expert_view = self._build_expert_view(raw_data, template_key)
        
        # 创建记录
        record = StateSyncRecord(
            event_id=event_id,
            user_id=user_id,
            event_type=event_type,
            timestamp=timestamp,
            client_view=client_view,
            coach_view=coach_view,
            expert_view=expert_view,
            trigger_id=trigger_id,
            action_id=action_id,
            processed=True
        )
        
        # 存储
        self._records[event_id] = record
        if user_id not in self._user_events:
            self._user_events[user_id] = []
        self._user_events[user_id].append(event_id)
        
        logger.info(f"[StateSync] 事件处理完成: event={event_id} user={user_id} type={event_type.value}")
        
        return record
    
    def _determine_template_key(self, event_type: EventType, raw_data: Dict) -> str:
        """确定使用的模板类型"""
        # 基于关键词匹配
        text = raw_data.get('text', '') or raw_data.get('snippet', {}).get('text', '')
        
        # 情绪化进食
        if any(kw in text for kw in ['零食', '吃东西', '停不下来', '暴食']):
            return 'emotional_eating'
        
        # 压力检测
        if any(kw in text for kw in ['压力', '焦虑', '紧张', '累']):
            return 'stress_detected'
        
        # 动力不足
        if any(kw in text for kw in ['没动力', '不想', '放弃', '难']):
            return 'low_motivation'
        
        # 睡眠问题
        if any(kw in text for kw in ['失眠', '睡不着', '熬夜']):
            return 'sleep_issue'
        
        # 血糖数据
        if event_type == EventType.DEVICE_DATA:
            cgm_value = raw_data.get('cgm_value', 0)
            if cgm_value > 10.0:
                return 'glucose_high'
            elif cgm_value < 3.9:
                return 'glucose_low'
        
        # 任务完成
        if event_type == EventType.TASK_COMPLETE:
            return 'task_completed'
        
        # 默认
        return 'stress_detected'
    
    def _build_client_view(self, template_key: str, raw_data: Dict) -> ClientView:
        """构建 C 端视图"""
        template = COMPANION_TEMPLATES.get(template_key, COMPANION_TEMPLATES['stress_detected'])
        
        content = template['content']
        # 替换模板变量
        if '{days}' in content:
            content = content.format(days=raw_data.get('streak_days', 7))
        
        return ClientView(
            msg_type=f"companion_{template_key}",
            content=content,
            ui_style=template.get('ui_style', UiStyle.WARM),
            action_buttons=template.get('buttons', []),
            extra_data={}
        )
    
    def _build_coach_view(self, template_key: str, raw_data: Dict) -> CoachView:
        """构建 B 端视图"""
        template = DIAGNOSIS_TEMPLATES.get(template_key, {
            "diagnosis": "General Observation",
            "suggested_action": "MONITOR",
            "scripts": ["继续观察用户状态"]
        })
        
        # 确定风险标记
        risk_flag = self._determine_risk_flag(template_key, raw_data)
        
        return CoachView(
            risk_flag=risk_flag,
            diagnosis=template['diagnosis'],
            trigger_source=raw_data.get('text', raw_data.get('snippet', {}).get('text', '')),
            suggested_action=template['suggested_action'],
            analysis_detail={
                "template_key": template_key,
                "raw_keywords": self._extract_keywords(raw_data)
            },
            intervention_scripts=template.get('scripts', [])
        )
    
    def _build_expert_view(self, raw_data: Dict, template_key: str) -> ExpertView:
        """构建专家端视图"""
        # 确定是否需要审核
        requires_review = template_key in ['glucose_low', 'emotional_eating']
        
        # 审计标记
        audit_flags = []
        if 'glucose' in template_key:
            audit_flags.append("HEALTH_DATA")
        if template_key in ['emotional_eating', 'stress_detected', 'low_motivation']:
            audit_flags.append("PSYCHOLOGICAL")
        
        return ExpertView(
            raw_data=raw_data,
            risk_assessment={
                "template_key": template_key,
                "severity": "high" if 'low' in template_key else "moderate"
            },
            ai_analysis={
                "keywords": self._extract_keywords(raw_data),
                "sentiment": raw_data.get('sentiment', 'neutral')
            },
            audit_flags=audit_flags,
            requires_review=requires_review
        )
    
    def _determine_risk_flag(self, template_key: str, raw_data: Dict) -> str:
        """确定风险标记"""
        if template_key == 'glucose_low':
            return "RED"
        elif template_key in ['emotional_eating', 'glucose_high']:
            return "ORANGE"
        elif template_key in ['stress_detected', 'low_motivation']:
            return "YELLOW"
        else:
            return "GREEN"
    
    def _extract_keywords(self, raw_data: Dict) -> List[str]:
        """提取关键词"""
        text = raw_data.get('text', '') or raw_data.get('snippet', {}).get('text', '')
        keywords = []
        
        # 简单的关键词提取
        trigger_words = ['压力', '焦虑', '零食', '失眠', '没动力', '放弃', '累', '吃']
        for word in trigger_words:
            if word in text:
                keywords.append(word)
        
        return keywords
    
    def get_view(
        self,
        event_id: str,
        role: ViewRole
    ) -> Optional[Dict]:
        """
        获取指定角色的视图
        
        Args:
            event_id: 事件ID
            role: 角色
        
        Returns:
            对应角色的视图数据
        """
        record = self._records.get(event_id)
        if not record:
            return None
        
        if role == ViewRole.PATIENT:
            return record.client_view.to_dict()
        elif role == ViewRole.COACH:
            return record.coach_view.to_dict()
        elif role == ViewRole.EXPERT:
            return record.expert_view.to_dict() if record.expert_view else None
        elif role == ViewRole.ADMIN:
            return record.to_dict()  # 管理员看全部
        
        return None
    
    def get_user_events(
        self,
        user_id: int,
        role: ViewRole,
        limit: int = 10
    ) -> List[Dict]:
        """获取用户的事件列表"""
        event_ids = self._user_events.get(user_id, [])
        
        results = []
        for event_id in event_ids[-limit:]:
            view = self.get_view(event_id, role)
            if view:
                results.append({
                    "event_id": event_id,
                    "view": view
                })
        
        return results
    
    def get_pending_reviews(self) -> List[Dict]:
        """获取待审核事件"""
        pending = []
        for record in self._records.values():
            if record.expert_view and record.expert_view.requires_review:
                pending.append(record.to_dict())
        return pending


# ============================================
# 数据库表定义 (SQLAlchemy)
# ============================================

if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
    
    class UserStateSyncTable(Base):
        """user_state_sync 表"""
        __tablename__ = 'user_state_sync'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        event_id = Column(String(36), unique=True, nullable=False, index=True)
        user_id = Column(Integer, nullable=False, index=True)
        event_type = Column(String(50), nullable=False)
        timestamp = Column(DateTime, nullable=False)
        
        # 分角色视图（JSON存储）
        client_view = Column(JSON, nullable=False)
        coach_view = Column(JSON, nullable=False)
        expert_view = Column(JSON, nullable=True)
        
        # 关联信息
        trigger_id = Column(String(50), nullable=True)
        action_id = Column(String(50), nullable=True)
        
        # 状态
        processed = Column(Integer, default=1)
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ============================================
# 创建表的 SQL（备用）
# ============================================

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_state_sync (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(36) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- 分角色视图（JSONB存储）
    client_view JSONB NOT NULL,
    coach_view JSONB NOT NULL,
    expert_view JSONB,
    
    -- 关联信息
    trigger_id VARCHAR(50),
    action_id VARCHAR(50),
    
    -- 状态
    processed INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_user_state_sync_user_id ON user_state_sync(user_id);
CREATE INDEX IF NOT EXISTS idx_user_state_sync_event_type ON user_state_sync(event_type);
CREATE INDEX IF NOT EXISTS idx_user_state_sync_timestamp ON user_state_sync(timestamp);
"""


# ============================================
# 全局单例
# ============================================

_state_sync_manager: Optional[StateSyncManager] = None


def get_state_sync_manager() -> StateSyncManager:
    """获取状态同步管理器"""
    global _state_sync_manager
    if _state_sync_manager is None:
        _state_sync_manager = StateSyncManager()
    return _state_sync_manager
