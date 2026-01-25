# -*- coding: utf-8 -*-
"""
master_agent.py - 中枢 Master Agent

行健行为教练多Agent系统的核心控制器，负责串联9步处理流程:
1. 用户输入 / 设备数据进入系统
2. 中枢 Master Agent 接收请求
3. 更新 User Master Profile（统一用户主画像）
4. Agent Router 判别问题类型与风险优先级
5. 调用 1–2 个专业 AGENT（代谢 / 睡眠 / 情绪 等）
6. Multi-Agent Coordinator 统一上下文并整合各 AGENT 结果
7. Intervention Planner 生成个性化行为干预路径（核心模块）
8. Response Synthesizer 统一教练风格并输出给用户
9. 写回 User Master Profile + 生成今日任务 / 追踪点
"""

import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum


# ============================================================================
# Core Data Schema v1.0 - 系统最高级别数据协议规范
# ============================================================================

SCHEMA_VERSION = "1.0"

# 系统级约束 - 唯一权威原则
SYSTEM_CONSTRAINTS = {
    "authority_principle": "UserMasterProfile是系统唯一权威用户主画像源",
    "communication_protocol": {
        "orchestrator_to_agent": "AgentTask",
        "agent_to_orchestrator": "AgentResult"
    },
    "write_back_channels": [
        "AgentResult.data_updates",
        "InterventionPlan.adjustment",
        "CoreDailyTask.feedback"
    ],
    "write_back_authority": "MasterOrchestrator"
}


# ============================================================================
# 数据结构定义
# ============================================================================

class RiskLevel(Enum):
    """风险等级"""
    CRITICAL = "critical"   # 危急 - 需要立即干预
    HIGH = "high"           # 高风险 - 优先处理
    MODERATE = "moderate"   # 中等 - 常规处理
    LOW = "low"             # 低风险 - 维护性干预


class InputType(Enum):
    """输入类型"""
    TEXT = "text"               # 文本输入
    VOICE = "voice"             # 语音输入
    DEVICE = "device"           # 设备数据同步
    FORM = "form"               # 表单/问卷
    ASSESSMENT = "assessment"   # 评估数据
    TASK_REPORT = "task_report" # 任务完成上报


class CoreInputType(Enum):
    """Core Data Schema v1.0 - 输入类型"""
    CHAT = "chat"
    WEARABLE_DATA = "wearable_data"
    MEDICAL_RECORD = "medical_record"
    QUESTIONNAIRE = "questionnaire"
    MANUAL_LOG = "manual_log"


class CoreSource(Enum):
    """Core Data Schema v1.0 - 输入来源"""
    APP = "app"
    DEVICE = "device"
    CLINICIAN = "clinician"
    SYSTEM = "system"


class CoreAgentType(Enum):
    """Core Data Schema v1.0 - Agent类型"""
    METABOLIC = "metabolic"
    SLEEP = "sleep"
    EMOTION = "emotion"
    MOTIVATION = "motivation"
    COACHING = "coaching"
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    TCM = "tcm"
    CRISIS = "crisis"


class CoreTaskType(Enum):
    """Core Data Schema v1.0 - 任务类型"""
    ANALYSIS = "analysis"
    ASSESSMENT_REQUEST = "assessment_request"
    PLANNING_SUPPORT = "planning_support"
    INTERPRETATION = "interpretation"


class CoreDailyTaskType(Enum):
    """Core Data Schema v1.0 - 每日任务类型"""
    MICRO_HABIT = "micro_habit"
    REFLECTION = "reflection"
    TRAINING = "training"
    MEASUREMENT = "measurement"


class CoreStrategyType(Enum):
    """Core Data Schema v1.0 - 干预策略类型"""
    COGNITIVE = "cognitive"
    BEHAVIORAL = "behavioral"
    EMOTIONAL_SUPPORT = "emotional_support"
    COMBINED = "combined"


class CoreModuleType(Enum):
    """Core Data Schema v1.0 - 干预模块类型"""
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    SLEEP = "sleep"
    EMOTION = "emotion"
    COGNITIVE = "cognitive"


class CoreBehaviorStage(Enum):
    """Core Data Schema v1.0 - 行为改变阶段(TTM)"""
    PRECONTEMPLATION = "precontemplation"
    CONTEMPLATION = "contemplation"
    PREPARATION = "preparation"
    ACTION = "action"
    MAINTENANCE = "maintenance"


class CoreResistanceLevel(Enum):
    """Core Data Schema v1.0 - 五层次心理准备度"""
    RESISTANCE = "resistance"
    AMBIVALENCE = "ambivalence"
    COMPROMISE = "compromise"
    ADAPTATION = "adaptation"
    INTEGRATION = "integration"


class CoreCultivationStage(Enum):
    """Core Data Schema v1.0 - 四阶段养成"""
    STARTUP = "startup"
    ADAPTATION = "adaptation"
    STABILITY = "stability"
    INTERNALIZATION = "internalization"


# ============================================================================
# Core Data Schema v1.0 - 六个核心结构体
# ============================================================================

@dataclass
class CoreUserInput:
    """Core Data Schema v1.0 - 结构体1: UserInput（统一输入对象）

    作用：系统所有外部输入的统一入口（对话/设备/医疗录入/问卷）
    """
    input_id: str
    user_id: str
    input_type: CoreInputType
    raw_content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: CoreSource = CoreSource.APP
    intent_hint: str = ""
    schema_version: str = SCHEMA_VERSION
    extensions: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoreUserInput':
        input_type = CoreInputType(data.get('input_type', 'chat'))
        source = CoreSource(data.get('source', 'app'))
        return cls(
            input_id=data.get('input_id', f"IN{uuid.uuid4().hex[:8]}"),
            user_id=data['user_id'],
            input_type=input_type,
            raw_content=data.get('raw_content', {}),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            source=source,
            intent_hint=data.get('intent_hint', ''),
            schema_version=data.get('schema_version', SCHEMA_VERSION),
            extensions=data.get('extensions', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_id": self.input_id,
            "user_id": self.user_id,
            "input_type": self.input_type.value,
            "raw_content": self.raw_content,
            "timestamp": self.timestamp,
            "source": self.source.value,
            "intent_hint": self.intent_hint,
            "schema_version": self.schema_version,
            "extensions": self.extensions
        }


@dataclass
class CoreAgentTask:
    """Core Data Schema v1.0 - 结构体3: AgentTask（中枢→AGENT标准指令对象）

    作用：Orchestrator调用专业AGENT的唯一通信协议
    """
    task_id: str
    user_id: str
    target_agent: CoreAgentType
    task_type: CoreTaskType
    focus_domain: str = ""
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    specific_questions: List[str] = field(default_factory=list)
    priority: str = "normal"  # high/normal/low
    schema_version: str = SCHEMA_VERSION
    extensions: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoreAgentTask':
        target_agent = CoreAgentType(data.get('target_agent', 'coaching'))
        task_type = CoreTaskType(data.get('task_type', 'analysis'))
        return cls(
            task_id=data.get('task_id', f"T{uuid.uuid4().hex[:8]}"),
            user_id=data['user_id'],
            target_agent=target_agent,
            task_type=task_type,
            focus_domain=data.get('focus_domain', ''),
            context_snapshot=data.get('context_snapshot', {}),
            specific_questions=data.get('specific_questions', []),
            priority=data.get('priority', 'normal'),
            schema_version=data.get('schema_version', SCHEMA_VERSION),
            extensions=data.get('extensions', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "target_agent": self.target_agent.value,
            "task_type": self.task_type.value,
            "focus_domain": self.focus_domain,
            "context_snapshot": self.context_snapshot,
            "specific_questions": self.specific_questions,
            "priority": self.priority,
            "schema_version": self.schema_version,
            "extensions": self.extensions
        }


@dataclass
class CoreAgentResult:
    """Core Data Schema v1.0 - 结构体4: AgentResult（AGENT→中枢回传对象）

    作用：所有AGENT分析结果的统一回传格式
    """
    task_id: str
    agent_id: str
    domain: str
    key_findings: List[str] = field(default_factory=list)
    behavior_pattern_tags: List[str] = field(default_factory=list)
    inner_need_tags: List[str] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=lambda: {"risk_level": "low", "confidence": 0.8})
    recommendations: List[str] = field(default_factory=list)
    data_updates: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
    extensions: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoreAgentResult':
        return cls(
            task_id=data.get('task_id', ''),
            agent_id=data.get('agent_id', ''),
            domain=data.get('domain', ''),
            key_findings=data.get('key_findings', []),
            behavior_pattern_tags=data.get('behavior_pattern_tags', []),
            inner_need_tags=data.get('inner_need_tags', []),
            risk_assessment=data.get('risk_assessment', {"risk_level": "low", "confidence": 0.8}),
            recommendations=data.get('recommendations', []),
            data_updates=data.get('data_updates', {}),
            schema_version=data.get('schema_version', SCHEMA_VERSION),
            extensions=data.get('extensions', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "domain": self.domain,
            "key_findings": self.key_findings,
            "behavior_pattern_tags": self.behavior_pattern_tags,
            "inner_need_tags": self.inner_need_tags,
            "risk_assessment": self.risk_assessment,
            "recommendations": self.recommendations,
            "data_updates": self.data_updates,
            "schema_version": self.schema_version,
            "extensions": self.extensions
        }


@dataclass
class CoreInterventionModule:
    """Core Data Schema v1.0 - 干预模块"""
    module_type: CoreModuleType
    intensity_level: str = "moderate"  # light/moderate/intensive
    duration: str = ""
    key_methods: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_type": self.module_type.value,
            "intensity_level": self.intensity_level,
            "duration": self.duration,
            "key_methods": self.key_methods
        }


@dataclass
class CoreInterventionPlan:
    """Core Data Schema v1.0 - 结构体5: InterventionPlan（干预路径对象）

    作用：从分析到行动的核心桥梁（行为处方）
    """
    plan_id: str
    user_id: str
    target_goals: List[str]
    current_stage: CoreCultivationStage
    strategy_type: CoreStrategyType = CoreStrategyType.COMBINED
    intervention_modules: List[CoreInterventionModule] = field(default_factory=list)
    adjustment_rules: List[str] = field(default_factory=list)
    expected_outcomes: List[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    extensions: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.plan_id:
            self.plan_id = f"IP{uuid.uuid4().hex[:8].upper()}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoreInterventionPlan':
        current_stage = CoreCultivationStage(data.get('current_stage', 'startup'))
        strategy_type = CoreStrategyType(data.get('strategy_type', 'combined'))

        modules = []
        for mod_data in data.get('intervention_modules', []):
            modules.append(CoreInterventionModule(
                module_type=CoreModuleType(mod_data.get('module_type', 'cognitive')),
                intensity_level=mod_data.get('intensity_level', 'moderate'),
                duration=mod_data.get('duration', ''),
                key_methods=mod_data.get('key_methods', [])
            ))

        return cls(
            plan_id=data.get('plan_id', f"IP{uuid.uuid4().hex[:8].upper()}"),
            user_id=data['user_id'],
            target_goals=data.get('target_goals', []),
            current_stage=current_stage,
            strategy_type=strategy_type,
            intervention_modules=modules,
            adjustment_rules=data.get('adjustment_rules', []),
            expected_outcomes=data.get('expected_outcomes', []),
            schema_version=data.get('schema_version', SCHEMA_VERSION),
            extensions=data.get('extensions', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "user_id": self.user_id,
            "target_goals": self.target_goals,
            "current_stage": self.current_stage.value,
            "strategy_type": self.strategy_type.value,
            "intervention_modules": [m.to_dict() for m in self.intervention_modules],
            "adjustment_rules": self.adjustment_rules,
            "expected_outcomes": self.expected_outcomes,
            "schema_version": self.schema_version,
            "extensions": self.extensions
        }


@dataclass
class CoreDailyTask:
    """Core Data Schema v1.0 - 结构体6: DailyTask（每日任务与陪伴执行对象）

    作用：系统真正产生行为改变的执行出口
    """
    task_id: str
    user_id: str
    task_type: CoreDailyTaskType
    description: str
    related_plan_id: str = ""
    scheduled_time: str = ""
    completion_status: str = "pending"  # pending/in_progress/completed/skipped
    user_feedback: str = ""
    adherence_score: float = 0.0
    schema_version: str = SCHEMA_VERSION
    extensions: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"DT{uuid.uuid4().hex[:8].upper()}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoreDailyTask':
        task_type = CoreDailyTaskType(data.get('task_type', 'micro_habit'))
        return cls(
            task_id=data.get('task_id', f"DT{uuid.uuid4().hex[:8].upper()}"),
            user_id=data['user_id'],
            task_type=task_type,
            description=data.get('description', ''),
            related_plan_id=data.get('related_plan_id', ''),
            scheduled_time=data.get('scheduled_time', ''),
            completion_status=data.get('completion_status', 'pending'),
            user_feedback=data.get('user_feedback', ''),
            adherence_score=data.get('adherence_score', 0.0),
            schema_version=data.get('schema_version', SCHEMA_VERSION),
            extensions=data.get('extensions', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "related_plan_id": self.related_plan_id,
            "task_type": self.task_type.value,
            "description": self.description,
            "scheduled_time": self.scheduled_time,
            "completion_status": self.completion_status,
            "user_feedback": self.user_feedback,
            "adherence_score": self.adherence_score,
            "schema_version": self.schema_version,
            "extensions": self.extensions
        }


@dataclass
class CoreUserMasterProfile:
    """Core Data Schema v1.0 - 结构体2: UserMasterProfile（用户主画像）

    作用：全系统唯一权威用户状态对象
    注意：任何模块不得直接修改原始字段，所有修改必须通过
          AgentResult.data_updates / InterventionPlan.adjustment / DailyTask.feedback
          由 Master Orchestrator 统一写回
    """
    user_id: str
    schema_version: str = SCHEMA_VERSION

    # 基础信息
    demographics: Dict[str, Any] = field(default_factory=lambda: {
        "age": None,
        "gender": None,
        "height": None,
        "weight": None
    })

    # 医疗档案
    medical_profile: Dict[str, Any] = field(default_factory=lambda: {
        "diagnoses": [],
        "medications": [],
        "lab_summary": {}
    })

    # 设备档案
    device_profile: Dict[str, Any] = field(default_factory=lambda: {
        "cgm_summary": {},
        "hrv_summary": {},
        "activity_summary": {}
    })

    # 行为档案
    behavior_profile: Dict[str, Any] = field(default_factory=lambda: {
        "current_stage": "precontemplation",
        "motivation_level": 5,
        "self_efficacy": 5,
        "resistance_level": "resistance",
        "dominant_behavior_patterns": []
    })

    # 内在需求档案
    inner_need_profile: Dict[str, Any] = field(default_factory=lambda: {
        "core_needs": [],
        "emotional_tendencies": []
    })

    # 风险档案
    risk_profile: Dict[str, Any] = field(default_factory=lambda: {
        "metabolic_risk_level": "low",
        "cardiovascular_risk_level": "low",
        "mental_stress_level": "low"
    })

    # 干预状态
    intervention_state: Dict[str, Any] = field(default_factory=lambda: {
        "active_plan_id": None,
        "adherence_score": 0,
        "last_adjustment_time": None
    })

    # 历史引用
    history_refs: Dict[str, Any] = field(default_factory=lambda: {
        "recent_assessments": [],
        "recent_tasks": []
    })

    extensions: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoreUserMasterProfile':
        return cls(
            user_id=data['user_id'],
            schema_version=data.get('schema_version', SCHEMA_VERSION),
            demographics=data.get('demographics', {}),
            medical_profile=data.get('medical_profile', {}),
            device_profile=data.get('device_profile', {}),
            behavior_profile=data.get('behavior_profile', {}),
            inner_need_profile=data.get('inner_need_profile', {}),
            risk_profile=data.get('risk_profile', {}),
            intervention_state=data.get('intervention_state', {}),
            history_refs=data.get('history_refs', {}),
            extensions=data.get('extensions', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "schema_version": self.schema_version,
            "demographics": self.demographics,
            "medical_profile": self.medical_profile,
            "device_profile": self.device_profile,
            "behavior_profile": self.behavior_profile,
            "inner_need_profile": self.inner_need_profile,
            "risk_profile": self.risk_profile,
            "intervention_state": self.intervention_state,
            "history_refs": self.history_refs,
            "extensions": self.extensions
        }

    def apply_data_updates(self, updates: Dict[str, Any]) -> None:
        """应用数据更新（由Orchestrator调用）"""
        for key, value in updates.items():
            if hasattr(self, key) and isinstance(getattr(self, key), dict):
                getattr(self, key).update(value)
            elif hasattr(self, key):
                setattr(self, key, value)


# ============================================================================
# Core Data Schema v1.0 - 数据流验证器
# ============================================================================

class CoreDataFlowValidator:
    """数据流验证器 - 确保遵循9步主执行链路"""

    PIPELINE_STEPS = [
        "UserInput进入系统",
        "Orchestrator解析输入，更新UserMasterProfile基础字段",
        "Router基于Profile+Intent生成1-2个AgentTask",
        "各AGENT返回AgentResult",
        "Multi-Agent Coordinator融合多个AgentResult",
        "Intervention Planner读取Profile+AgentResult生成InterventionPlan",
        "Planner生成DailyTask",
        "Response Synthesizer输出对话+任务",
        "执行反馈写回DailyTask和UserMasterProfile"
    ]

    ALLOWED_WRITE_CHANNELS = [
        "AgentResult.data_updates",
        "InterventionPlan.adjustment",
        "CoreDailyTask.feedback"
    ]

    @classmethod
    def validate_agent_communication(cls, sender: str, receiver: str, message_type: str) -> bool:
        """验证Agent通信是否符合协议"""
        valid_patterns = {
            ("Orchestrator", "Agent"): "AgentTask",
            ("Agent", "Orchestrator"): "AgentResult"
        }
        expected_type = valid_patterns.get((sender, receiver))
        return expected_type == message_type

    @classmethod
    def validate_profile_write(cls, writer: str, channel: str) -> bool:
        """验证画像写入是否通过合法渠道"""
        if writer != "MasterOrchestrator":
            return False
        return channel in cls.ALLOWED_WRITE_CHANNELS

    @classmethod
    def get_current_step(cls, step_index: int) -> str:
        """获取当前步骤描述"""
        if 0 <= step_index < len(cls.PIPELINE_STEPS):
            return cls.PIPELINE_STEPS[step_index]
        return "Unknown step"


# ============================================================================
# 数据格式兼容层 - 支持旧格式到 v2.0 的转换
# ============================================================================

class DataFormatConverter:
    """数据格式转换器 - 将旧格式数据转换为 v2.0 格式

    支持的旧格式字段映射:
    - physiological_state → biometrics
    - psychological_state → psych
    - computed_indicators → behavior + constitution
    - behavior_state → behavior
    - user_profile (旧) → v2.0 完整结构

    使用方式:
        converter = DataFormatConverter()
        new_data = converter.convert(old_data)
    """

    # 旧字段到新字段的映射
    FIELD_MAPPINGS = {
        # 顶层字段映射
        "physiological_state": "biometrics",
        "psychological_state": "psych",
        "behavior_state": "behavior",
        "computed_indicators": "_computed",  # 特殊处理
        "user_state": "_user_state",  # 特殊处理

        # physiological_state 子字段映射到 biometrics
        "hrv_sdnn": ("biometrics", "hrv", "sdnn"),
        "hrv_rmssd": ("biometrics", "hrv", "rmssd"),
        "resting_hr": ("biometrics", "hrv", "resting_hr"),
        "sleep_hours": ("biometrics", "sleep", "avg_duration"),
        "sleep_quality": ("biometrics", "sleep", "avg_quality"),
        "deep_sleep_percent": ("biometrics", "sleep", "deep_sleep_percent"),
        "fasting_glucose": ("biometrics", "glucose", "fasting"),
        "hba1c": ("biometrics", "glucose", "hba1c"),
        "time_in_range": ("biometrics", "glucose", "tir"),
        "glucose_cv": ("biometrics", "glucose", "cv"),
        "steps": ("biometrics", "activity", "avg_steps"),
        "active_minutes": ("biometrics", "activity", "active_minutes_weekly"),

        # psychological_state 子字段映射到 psych
        "anxiety_score": ("psych", "anxiety_level"),
        "depression_score": ("psych", "depression_level"),
        "stress_score": ("psych", "stress_score"),
        "stress_level": ("psych", "stress_level"),
        "motivation_score": ("psych", "motivation_score"),
        "self_efficacy": ("psych", "efficacy_score"),
        "efficacy_score": ("psych", "efficacy_score"),

        # computed_indicators 子字段映射
        "bmi": ("constitution", "bmi"),
        "bmi_category": ("constitution", "bmi_category"),
        "metabolic_age": ("constitution", "metabolic_age"),
        "visceral_fat": ("constitution", "visceral_fat"),
        "change_stage": ("behavior", "stage"),
        "readiness_level": ("behavior", "stage"),
        "spi": ("behavior", "spi_coefficient"),
        "spi_coefficient": ("behavior", "spi_coefficient"),

        # 其他常见旧字段
        "message": "content",
        "query": "content",
        "text": "content",
        "input": "content",
    }

    # 行为阶段映射 (TTM 旧名称 → 五层次模型)
    STAGE_MAPPINGS = {
        # TTM 阶段
        "precontemplation": "resistance",
        "contemplation": "ambivalence",
        "preparation": "compromise",
        "action": "adaptation",
        "maintenance": "integration",

        # 中文名称
        "前意向期": "resistance",
        "意向期": "ambivalence",
        "准备期": "compromise",
        "行动期": "adaptation",
        "维持期": "integration",

        # 保持五层次模型原有命名
        "resistance": "resistance",
        "ambivalence": "ambivalence",
        "compromise": "compromise",
        "adaptation": "adaptation",
        "integration": "integration",

        # 中文五层次
        "完全对抗": "resistance",
        "抗拒与反思": "ambivalence",
        "妥协与接受": "compromise",
        "顺应与调整": "adaptation",
        "全面臣服": "integration",
    }

    # 风险等级映射
    RISK_LEVEL_MAPPINGS = {
        "critical": "critical",
        "high": "high",
        "moderate": "moderate",
        "medium": "moderate",
        "low": "low",
        "none": "low",
        "危急": "critical",
        "高": "high",
        "中": "moderate",
        "低": "low",
    }

    @classmethod
    def convert(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """转换数据格式 (自动检测并转换)

        Args:
            data: 输入数据 (可能是旧格式或新格式)

        Returns:
            v2.0 格式的数据
        """
        if not data:
            return data

        # 检测是否为旧格式
        if cls._is_old_format(data):
            return cls._convert_from_old_format(data)

        # 已经是新格式，但可能有嵌套的旧格式字段
        return cls._normalize_fields(data)

    @classmethod
    def convert_user_input(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """转换用户输入数据"""
        result = data.copy()

        # 处理消息/内容字段
        for old_key in ["message", "query", "text", "input"]:
            if old_key in result and "content" not in result:
                result["content"] = result.pop(old_key)

        # 处理设备数据
        if "device_data" in result:
            result["device_data"] = cls.convert_device_data(result["device_data"])
        elif "physiological_state" in result:
            result["device_data"] = cls._convert_physiological_to_device(
                result.pop("physiological_state")
            )

        # 处理表单数据
        if "form_data" in result:
            result["form_data"] = cls.convert_profile_data(result["form_data"])
        elif "user_state" in result:
            result["form_data"] = cls.convert_profile_data(result.pop("user_state"))

        # 处理效能感评分
        for old_key in ["efficacy", "self_efficacy", "efficacy_score"]:
            if old_key in result and "efficacy_score" not in result:
                result["efficacy_score"] = float(result.pop(old_key))

        return result

    @classmethod
    def convert_profile_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """转换用户画像数据"""
        if not data:
            return data

        result = {}

        # 处理顶层旧字段
        if "physiological_state" in data:
            result["biometrics"] = cls._convert_physiological_state(
                data["physiological_state"]
            )

        if "psychological_state" in data:
            result["psych"] = cls._convert_psychological_state(
                data["psychological_state"]
            )

        if "behavior_state" in data:
            result["behavior"] = cls._convert_behavior_state(data["behavior_state"])

        if "computed_indicators" in data:
            computed = cls._convert_computed_indicators(data["computed_indicators"])
            for key, value in computed.items():
                if key in result:
                    result[key].update(value)
                else:
                    result[key] = value

        # 复制其他新格式字段
        new_format_fields = [
            "user_id", "basic", "medical", "biometrics", "psych", "behavior",
            "constitution", "preferences", "goals", "risk_flags", "history",
            "current_intervention", "today", "session_history",
            "demographics", "medical_profile", "device_profile",
            "behavior_profile", "inner_need_profile", "risk_profile",
            "intervention_state", "history_refs"
        ]

        for field in new_format_fields:
            if field in data and field not in result:
                result[field] = data[field]

        return result if result else data

    @classmethod
    def convert_device_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """转换设备数据"""
        if not data:
            return data

        result = data.copy()

        # 如果是旧的扁平格式，转换为嵌套格式
        if "hrv_sdnn" in data or "sleep_hours" in data or "fasting_glucose" in data:
            result = cls._convert_physiological_to_device(data)

        return result

    @classmethod
    def convert_stage(cls, stage: str) -> str:
        """转换行为阶段名称"""
        if not stage:
            return "resistance"
        return cls.STAGE_MAPPINGS.get(stage.lower(), stage)

    @classmethod
    def convert_risk_level(cls, level: str) -> str:
        """转换风险等级"""
        if not level:
            return "low"
        return cls.RISK_LEVEL_MAPPINGS.get(level.lower(), level)

    # ========== 内部方法 ==========

    @classmethod
    def _is_old_format(cls, data: Dict[str, Any]) -> bool:
        """检测是否为旧格式"""
        old_format_indicators = [
            "physiological_state",
            "psychological_state",
            "behavior_state",
            "computed_indicators",
            "user_state",
        ]
        return any(key in data for key in old_format_indicators)

    @classmethod
    def _convert_from_old_format(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """从旧格式转换"""
        return cls.convert_profile_data(data)

    @classmethod
    def _normalize_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """规范化字段（处理可能的嵌套旧格式）"""
        result = data.copy()

        # 规范化行为阶段
        if "behavior" in result and "stage" in result["behavior"]:
            result["behavior"]["stage"] = cls.convert_stage(
                result["behavior"]["stage"]
            )

        # 规范化风险等级
        for risk_field in ["risk_level", "metabolic_risk_level",
                          "cardiovascular_risk_level", "mental_stress_level"]:
            if risk_field in result:
                result[risk_field] = cls.convert_risk_level(result[risk_field])
            if "risk_profile" in result and risk_field in result["risk_profile"]:
                result["risk_profile"][risk_field] = cls.convert_risk_level(
                    result["risk_profile"][risk_field]
                )

        return result

    @classmethod
    def _convert_physiological_state(cls, old: Dict[str, Any]) -> Dict[str, Any]:
        """转换 physiological_state → biometrics"""
        if not old:
            return {}

        result = {
            "glucose": {},
            "hrv": {},
            "sleep": {},
            "activity": {}
        }

        # HRV 数据
        if "hrv_sdnn" in old:
            result["hrv"]["sdnn"] = old["hrv_sdnn"]
        if "hrv_rmssd" in old:
            result["hrv"]["rmssd"] = old["hrv_rmssd"]
        if "resting_hr" in old:
            result["hrv"]["resting_hr"] = old["resting_hr"]
        if "stress_index" in old:
            result["hrv"]["stress_index"] = old["stress_index"]

        # 睡眠数据
        if "sleep_hours" in old:
            result["sleep"]["avg_duration"] = old["sleep_hours"]
        if "sleep_quality" in old:
            result["sleep"]["avg_quality"] = old["sleep_quality"]
        if "deep_sleep_percent" in old:
            result["sleep"]["deep_sleep_percent"] = old["deep_sleep_percent"]
        if "sleep_efficiency" in old:
            result["sleep"]["sleep_efficiency"] = old["sleep_efficiency"]

        # 血糖数据
        if "fasting_glucose" in old:
            result["glucose"]["fasting"] = old["fasting_glucose"]
        if "hba1c" in old:
            result["glucose"]["hba1c"] = old["hba1c"]
        if "time_in_range" in old or "tir" in old:
            result["glucose"]["tir"] = old.get("time_in_range", old.get("tir"))
        if "glucose_cv" in old:
            result["glucose"]["cv"] = old["glucose_cv"]

        # 活动数据
        if "steps" in old:
            result["activity"]["avg_steps"] = old["steps"]
        if "active_minutes" in old:
            result["activity"]["active_minutes_weekly"] = old["active_minutes"]

        # 清理空字典
        return {k: v for k, v in result.items() if v}

    @classmethod
    def _convert_psychological_state(cls, old: Dict[str, Any]) -> Dict[str, Any]:
        """转换 psychological_state → psych"""
        if not old:
            return {}

        result = {}

        mappings = {
            "anxiety_score": "anxiety_level",
            "anxiety_level": "anxiety_level",
            "depression_score": "depression_level",
            "depression_level": "depression_level",
            "stress_score": "stress_score",
            "stress_level": "stress_level",
            "motivation_score": "motivation_score",
            "motivation": "motivation",
            "self_efficacy": "efficacy_score",
            "efficacy_score": "efficacy_score",
            "mood": "mood_trend",
            "mood_trend": "mood_trend",
            "social_support": "social_support",
        }

        for old_key, new_key in mappings.items():
            if old_key in old:
                result[new_key] = old[old_key]

        return result

    @classmethod
    def _convert_behavior_state(cls, old: Dict[str, Any]) -> Dict[str, Any]:
        """转换 behavior_state → behavior"""
        if not old:
            return {}

        result = {}

        # 阶段转换
        if "stage" in old:
            result["stage"] = cls.convert_stage(old["stage"])
        if "change_stage" in old:
            result["stage"] = cls.convert_stage(old["change_stage"])
        if "readiness_level" in old:
            result["stage"] = cls.convert_stage(old["readiness_level"])

        # SPI 系数
        if "spi" in old:
            result["spi_coefficient"] = old["spi"]
        if "spi_coefficient" in old:
            result["spi_coefficient"] = old["spi_coefficient"]

        # 其他字段
        direct_mappings = [
            "patterns", "adherence_score", "task_completion_rate",
            "streak_days", "cultivation_phase"
        ]
        for field in direct_mappings:
            if field in old:
                result[field] = old[field]

        return result

    @classmethod
    def _convert_computed_indicators(cls, old: Dict[str, Any]) -> Dict[str, Any]:
        """转换 computed_indicators → constitution + behavior"""
        if not old:
            return {}

        result = {
            "constitution": {},
            "behavior": {}
        }

        # 体质指标
        constitution_fields = ["bmi", "bmi_category", "metabolic_age",
                              "visceral_fat", "inflammation_risk"]
        for field in constitution_fields:
            if field in old:
                result["constitution"][field] = old[field]

        # 行为指标
        if "change_stage" in old:
            result["behavior"]["stage"] = cls.convert_stage(old["change_stage"])
        if "spi" in old:
            result["behavior"]["spi_coefficient"] = old["spi"]

        # 清理空字典
        return {k: v for k, v in result.items() if v}

    @classmethod
    def _convert_physiological_to_device(cls, old: Dict[str, Any]) -> Dict[str, Any]:
        """将旧的 physiological_state 转换为 DeviceData 格式"""
        if not old:
            return {}

        result = {}

        # CGM 数据
        cgm = {}
        if "current_glucose" in old:
            cgm["current_glucose"] = old["current_glucose"]
        if "glucose_trend" in old:
            cgm["trend"] = old["glucose_trend"]
        if "time_in_range" in old:
            cgm["time_in_range_percent"] = old["time_in_range"]
        if "avg_glucose" in old:
            cgm["avg_glucose_24h"] = old["avg_glucose"]
        if cgm:
            result["cgm"] = cgm

        # HRV 数据
        hrv = {}
        if "hrv_sdnn" in old:
            hrv["sdnn"] = old["hrv_sdnn"]
        if "hrv_rmssd" in old:
            hrv["rmssd"] = old["hrv_rmssd"]
        if "stress_index" in old:
            hrv["stress_index"] = old["stress_index"]
        if hrv:
            result["hrv"] = hrv

        # 睡眠数据
        sleep = {}
        if "sleep_hours" in old:
            sleep["duration_hours"] = old["sleep_hours"]
        if "sleep_quality" in old:
            sleep["quality_score"] = old["sleep_quality"]
        if "deep_sleep_percent" in old:
            sleep["deep_sleep_percent"] = old["deep_sleep_percent"]
        if sleep:
            result["sleep"] = sleep

        # 活动数据
        if "steps" in old:
            result["steps"] = old["steps"]
        if "active_minutes" in old:
            result["active_minutes"] = old["active_minutes"]

        return result


# ============================================================================
# Assessment Engine - 问卷评估系统 (Core Data Schema v1.0 扩展)
# ============================================================================

class QuestionnaireDomain(Enum):
    """问卷领域"""
    METABOLIC = "metabolic"
    EMOTION = "emotion"
    MOTIVATION = "motivation"
    STAGE = "stage"
    ADHERENCE = "adherence"
    SLEEP = "sleep"
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    STRESS = "stress"
    COGNITION = "cognition"
    SOCIAL_SUPPORT = "social_support"
    SELF_EFFICACY = "self_efficacy"
    BARRIER_IDENTIFICATION = "barrier_identification"


class QuestionType(Enum):
    """题目类型"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    SCALE = "scale"
    TEXT = "text"
    NUMERIC = "numeric"
    DATE = "date"
    MATRIX = "matrix"


class TriggerEvent(Enum):
    """问卷触发事件"""
    ONBOARDING = "onboarding"
    AGENT_REQUEST = "agent_request"
    PLANNER_REQUEST = "planner_request"
    FOLLOWUP_7DAY = "followup_7day"
    FOLLOWUP_14DAY = "followup_14day"
    FOLLOWUP_30DAY = "followup_30day"
    GLUCOSE_ABNORMAL = "glucose_abnormal"
    SLEEP_ABNORMAL = "sleep_abnormal"
    TASK_INCOMPLETE_3DAYS = "task_incomplete_3days"
    STAGE_CHANGE = "stage_change"
    RISK_ELEVATED = "risk_elevated"
    MANUAL = "manual"


class QuestionnaireStatus(Enum):
    """问卷状态"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class QuestionOption:
    """问题选项"""
    value: Any
    label: str
    score: float = 0.0


@dataclass
class Question:
    """问卷题目"""
    question_id: str
    text: str
    type: QuestionType
    options: List[QuestionOption] = field(default_factory=list)
    scale_min: int = 1
    scale_max: int = 5
    scale_labels: Dict[int, str] = field(default_factory=dict)
    required: bool = True
    scoring_weight: float = 1.0
    maps_to_field: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "text": self.text,
            "type": self.type.value,
            "options": [{"value": o.value, "label": o.label, "score": o.score} for o in self.options],
            "scale_min": self.scale_min,
            "scale_max": self.scale_max,
            "scale_labels": self.scale_labels,
            "required": self.required,
            "scoring_weight": self.scoring_weight,
            "maps_to_field": self.maps_to_field
        }


@dataclass
class QuestionBlock:
    """问卷题块"""
    block_id: str
    title: str
    questions: List[Question]
    description: str = ""
    domain: QuestionnaireDomain = QuestionnaireDomain.MOTIVATION
    required_for_stages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "title": self.title,
            "description": self.description,
            "domain": self.domain.value,
            "questions": [q.to_dict() for q in self.questions],
            "required_for_stages": self.required_for_stages
        }


@dataclass
class ScoringRule:
    """评分规则"""
    dimension: str
    calculation: str = "sum"  # sum/average/weighted_sum/max/custom
    question_ids: List[str] = field(default_factory=list)
    normalization_min: float = 0
    normalization_max: float = 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "calculation": self.calculation,
            "question_ids": self.question_ids,
            "normalization": {"min": self.normalization_min, "max": self.normalization_max}
        }


@dataclass
class InterpretationRange:
    """解读区间"""
    min_score: float
    max_score: float
    level: str
    label: str
    description: str
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class InterpretationRule:
    """解读规则"""
    dimension: str
    ranges: List[InterpretationRange] = field(default_factory=list)
    maps_to_profile_field: str = ""

    def interpret(self, score: float) -> Optional[InterpretationRange]:
        """根据得分返回解读"""
        for r in self.ranges:
            if r.min_score <= score <= r.max_score:
                return r
        return None


@dataclass
class QuestionnaireTemplate:
    """问卷模板定义 - Assessment Engine 结构体1"""
    template_id: str
    name: str
    domain: QuestionnaireDomain
    question_blocks: List[QuestionBlock]
    description: str = ""
    version: str = "1.0"
    target_stages: List[str] = field(default_factory=list)
    target_population: List[str] = field(default_factory=list)
    estimated_minutes: int = 10
    scoring_rules: List[ScoringRule] = field(default_factory=list)
    interpretation_rules: List[InterpretationRule] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    extensions: Dict[str, Any] = field(default_factory=dict)

    def get_all_questions(self) -> List[Question]:
        """获取所有题目"""
        questions = []
        for block in self.question_blocks:
            questions.extend(block.questions)
        return questions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "domain": self.domain.value,
            "description": self.description,
            "version": self.version,
            "target_stages": self.target_stages,
            "target_population": self.target_population,
            "estimated_minutes": self.estimated_minutes,
            "question_blocks": [b.to_dict() for b in self.question_blocks],
            "scoring_rules": [r.to_dict() for r in self.scoring_rules],
            "schema_version": self.schema_version,
            "extensions": self.extensions
        }


@dataclass
class QuestionAnswer:
    """问题答案"""
    question_id: str
    value: Any
    answered_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class QuestionnaireInstance:
    """问卷实例 - Assessment Engine 结构体2"""
    instance_id: str
    user_id: str
    template_id: str
    status: QuestionnaireStatus = QuestionnaireStatus.DRAFT
    trigger_source: TriggerEvent = TriggerEvent.MANUAL
    trigger_agent: str = ""
    answers: List[QuestionAnswer] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    time_spent_seconds: int = 0
    schema_version: str = SCHEMA_VERSION
    extensions: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.instance_id:
            self.instance_id = f"QI{uuid.uuid4().hex[:8].upper()}"

    def add_answer(self, question_id: str, value: Any) -> None:
        """添加答案"""
        self.answers.append(QuestionAnswer(question_id=question_id, value=value))

    def get_answer(self, question_id: str) -> Optional[Any]:
        """获取答案"""
        for a in self.answers:
            if a.question_id == question_id:
                return a.value
        return None

    def complete(self) -> None:
        """完成问卷"""
        self.status = QuestionnaireStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        if self.started_at:
            start = datetime.fromisoformat(self.started_at)
            self.time_spent_seconds = int((datetime.now() - start).total_seconds())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "status": self.status.value,
            "trigger_source": self.trigger_source.value,
            "trigger_agent": self.trigger_agent,
            "answers": [{"question_id": a.question_id, "value": a.value, "answered_at": a.answered_at} for a in self.answers],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "time_spent_seconds": self.time_spent_seconds,
            "schema_version": self.schema_version,
            "extensions": self.extensions
        }


@dataclass
class AssessmentResult:
    """评估结果 - Assessment Engine 结构体3 (进入中枢的关键对象)"""
    result_id: str
    user_id: str
    instance_id: str
    domain: QuestionnaireDomain
    template_id: str = ""
    assessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    core_scores: Dict[str, float] = field(default_factory=dict)
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    behavior_pattern_tags: List[str] = field(default_factory=list)
    inner_need_tags: List[str] = field(default_factory=list)
    identified_barriers: List[str] = field(default_factory=list)
    risk_level: str = "low"
    confidence_level: float = 0.8
    interpretation_summary: str = ""
    recommended_interventions: List[str] = field(default_factory=list)
    profile_updates: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
    extensions: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.result_id:
            self.result_id = f"AR{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "user_id": self.user_id,
            "instance_id": self.instance_id,
            "template_id": self.template_id,
            "domain": self.domain.value,
            "assessed_at": self.assessed_at,
            "core_scores": self.core_scores,
            "dimension_scores": self.dimension_scores,
            "behavior_pattern_tags": self.behavior_pattern_tags,
            "inner_need_tags": self.inner_need_tags,
            "identified_barriers": self.identified_barriers,
            "risk_level": self.risk_level,
            "confidence_level": self.confidence_level,
            "interpretation_summary": self.interpretation_summary,
            "recommended_interventions": self.recommended_interventions,
            "profile_updates": self.profile_updates,
            "schema_version": self.schema_version,
            "extensions": self.extensions
        }

    def to_agent_result(self) -> 'CoreAgentResult':
        """转换为CoreAgentResult格式，用于与AGENT系统集成"""
        return CoreAgentResult(
            task_id=self.instance_id,
            agent_id="AssessmentEngine",
            domain=self.domain.value,
            key_findings=[self.interpretation_summary] + self.identified_barriers,
            behavior_pattern_tags=self.behavior_pattern_tags,
            inner_need_tags=self.inner_need_tags,
            risk_assessment={"risk_level": self.risk_level, "confidence": self.confidence_level},
            recommendations=self.recommended_interventions,
            data_updates=self.profile_updates
        )


@dataclass
class QuestionnaireTriggerRule:
    """问卷触发规则 - Assessment Engine 结构体4"""
    rule_id: str
    trigger_event: TriggerEvent
    template_id: str
    name: str = ""
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    target_agent: str = ""
    priority: str = "normal"
    cooldown_hours: int = 24
    max_frequency_per_week: int = 3
    enabled: bool = True
    schema_version: str = SCHEMA_VERSION
    extensions: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.rule_id:
            self.rule_id = f"TR{uuid.uuid4().hex[:8].upper()}"

    def check_conditions(self, profile: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """检查触发条件是否满足"""
        if not self.enabled:
            return False

        for cond in self.conditions:
            field_path = cond.get("field", "")
            operator = cond.get("operator", "eq")
            expected = cond.get("value")

            # 获取实际值 (支持嵌套路径如 "behavior_profile.current_stage")
            actual = profile
            for part in field_path.split("."):
                if isinstance(actual, dict):
                    actual = actual.get(part)
                else:
                    actual = None
                    break

            # 比较
            if operator == "eq" and actual != expected:
                return False
            elif operator == "ne" and actual == expected:
                return False
            elif operator == "gt" and (actual is None or actual <= expected):
                return False
            elif operator == "lt" and (actual is None or actual >= expected):
                return False
            elif operator == "gte" and (actual is None or actual < expected):
                return False
            elif operator == "lte" and (actual is None or actual > expected):
                return False
            elif operator == "in" and actual not in expected:
                return False
            elif operator == "contains" and expected not in str(actual):
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "trigger_event": self.trigger_event.value,
            "template_id": self.template_id,
            "conditions": self.conditions,
            "target_agent": self.target_agent,
            "priority": self.priority,
            "cooldown_hours": self.cooldown_hours,
            "max_frequency_per_week": self.max_frequency_per_week,
            "enabled": self.enabled,
            "schema_version": self.schema_version,
            "extensions": self.extensions
        }


class AssessmentEngine:
    """问卷评估引擎 - Master Orchestrator 的一级核心子系统

    架构位置:
    Master Orchestrator
        ├── Agent Router
        ├── Multi-Agent Coordinator
        ├── Intervention Planner
        └── Assessment Engine（本模块）
                ├── Questionnaire Generator
                ├── Scoring Engine
                ├── Interpretation Engine
                └── Profile Writer
    """

    def __init__(self, templates_path: str = "data/questionnaire_templates"):
        self.templates_path = Path(templates_path)
        self.templates_path.mkdir(parents=True, exist_ok=True)
        self._templates: Dict[str, QuestionnaireTemplate] = {}
        self._trigger_rules: List[QuestionnaireTriggerRule] = []
        self._instances: Dict[str, QuestionnaireInstance] = {}
        self._results: Dict[str, AssessmentResult] = {}

    # ========== Questionnaire Generator ==========

    def generate_questionnaire(self,
                               template_id: str,
                               user_id: str,
                               trigger: TriggerEvent = TriggerEvent.MANUAL,
                               trigger_agent: str = "",
                               profile_snapshot: Optional[Dict[str, Any]] = None) -> QuestionnaireInstance:
        """生成问卷实例 - Questionnaire Generator 核心方法"""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        instance = QuestionnaireInstance(
            instance_id=f"QI{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            template_id=template_id,
            trigger_source=trigger,
            trigger_agent=trigger_agent,
            started_at=datetime.now().isoformat()
        )

        # 根据用户阶段过滤题块
        if profile_snapshot:
            current_stage = profile_snapshot.get("behavior_profile", {}).get("current_stage", "")
            # 可以在这里添加动态题块过滤逻辑

        self._instances[instance.instance_id] = instance
        return instance

    def generate_adaptive_questionnaire(self,
                                        goal: str,
                                        user_id: str,
                                        profile: Dict[str, Any],
                                        calling_agent: str = "") -> QuestionnaireInstance:
        """动态生成自适应问卷 - 根据目标+画像+阶段自动选择模板和题块"""
        # 确定最适合的模板
        best_template_id = self._select_best_template(goal, profile)

        if not best_template_id:
            # 如果没有匹配模板，使用默认行为评估
            best_template_id = "behavior_change_assessment"

        return self.generate_questionnaire(
            template_id=best_template_id,
            user_id=user_id,
            trigger=TriggerEvent.AGENT_REQUEST if calling_agent else TriggerEvent.MANUAL,
            trigger_agent=calling_agent,
            profile_snapshot=profile
        )

    def _select_best_template(self, goal: str, profile: Dict[str, Any]) -> Optional[str]:
        """选择最适合的模板"""
        goal_lower = goal.lower()
        current_stage = profile.get("behavior_profile", {}).get("current_stage", "")

        # 简单的关键词匹配逻辑
        for tid, template in self._templates.items():
            # 检查阶段匹配
            if template.target_stages and current_stage not in template.target_stages:
                continue

            # 检查目标关键词
            domain_keywords = {
                QuestionnaireDomain.MOTIVATION: ["动机", "motivation", "意愿"],
                QuestionnaireDomain.STAGE: ["阶段", "stage", "准备度"],
                QuestionnaireDomain.BARRIER_IDENTIFICATION: ["障碍", "barrier", "困难"],
                QuestionnaireDomain.SELF_EFFICACY: ["效能", "efficacy", "信心"],
                QuestionnaireDomain.ADHERENCE: ["依从", "adherence", "执行"],
                QuestionnaireDomain.NUTRITION: ["饮食", "nutrition", "营养"],
                QuestionnaireDomain.SLEEP: ["睡眠", "sleep"],
                QuestionnaireDomain.STRESS: ["压力", "stress", "焦虑"],
            }

            keywords = domain_keywords.get(template.domain, [])
            if any(kw in goal_lower for kw in keywords):
                return tid

        return None

    # ========== Scoring Engine ==========

    def score_questionnaire(self,
                           instance: QuestionnaireInstance,
                           template: QuestionnaireTemplate) -> Dict[str, float]:
        """评分引擎 - 根据 ScoringRules 计算各维度得分"""
        dimension_scores = {}

        for rule in template.scoring_rules:
            scores = []
            weights = []

            for q_id in rule.question_ids:
                answer = instance.get_answer(q_id)
                if answer is None:
                    continue

                # 找到对应问题获取分数
                question = self._find_question(template, q_id)
                if not question:
                    continue

                score = self._calculate_question_score(question, answer)
                scores.append(score)
                weights.append(question.scoring_weight)

            if not scores:
                continue

            # 根据计算方式计算维度得分
            if rule.calculation == "sum":
                raw_score = sum(scores)
            elif rule.calculation == "average":
                raw_score = sum(scores) / len(scores)
            elif rule.calculation == "weighted_sum":
                raw_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights) if weights else 0
            elif rule.calculation == "max":
                raw_score = max(scores)
            else:
                raw_score = sum(scores)

            # 归一化
            normalized = self._normalize_score(
                raw_score,
                rule.normalization_min,
                rule.normalization_max
            )
            dimension_scores[rule.dimension] = round(normalized, 2)

        return dimension_scores

    def _find_question(self, template: QuestionnaireTemplate, question_id: str) -> Optional[Question]:
        """查找问题"""
        for block in template.question_blocks:
            for q in block.questions:
                if q.question_id == question_id:
                    return q
        return None

    def _calculate_question_score(self, question: Question, answer: Any) -> float:
        """计算单题得分"""
        if question.type == QuestionType.SCALE:
            return float(answer) if isinstance(answer, (int, float)) else 0

        if question.type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]:
            for opt in question.options:
                if opt.value == answer:
                    return opt.score
            # 多选题
            if isinstance(answer, list):
                return sum(opt.score for opt in question.options if opt.value in answer)

        return 0

    def _normalize_score(self, raw: float, min_val: float, max_val: float) -> float:
        """归一化得分到 0-100"""
        if max_val == min_val:
            return 50
        return max(0, min(100, (raw - min_val) / (max_val - min_val) * 100))

    # ========== Interpretation Engine ==========

    def interpret_results(self,
                         dimension_scores: Dict[str, float],
                         template: QuestionnaireTemplate) -> Tuple[str, List[str], Dict[str, Any]]:
        """解读引擎 - 生成解读摘要、建议行动和画像更新"""
        summaries = []
        all_actions = []
        profile_updates = {}

        for rule in template.interpretation_rules:
            score = dimension_scores.get(rule.dimension)
            if score is None:
                continue

            interpretation = rule.interpret(score)
            if interpretation:
                summaries.append(f"{rule.dimension}: {interpretation.label} - {interpretation.description}")
                all_actions.extend(interpretation.recommended_actions)

                # 画像更新映射
                if rule.maps_to_profile_field:
                    profile_updates[rule.maps_to_profile_field] = interpretation.level

        summary = "; ".join(summaries) if summaries else "评估完成"
        return summary, all_actions, profile_updates

    # ========== Full Assessment Pipeline ==========

    def assess(self, instance: QuestionnaireInstance) -> AssessmentResult:
        """完整评估流程 - 评分 + 解读 + 生成结果"""
        template = self._templates.get(instance.template_id)
        if not template:
            raise ValueError(f"Template not found: {instance.template_id}")

        # 1. 评分
        dimension_scores = self.score_questionnaire(instance, template)

        # 2. 计算核心得分
        core_scores = {
            "motivation_score": dimension_scores.get("motivation", 50),
            "self_efficacy_score": dimension_scores.get("self_efficacy", 50),
            "resistance_level": 100 - dimension_scores.get("readiness", 50),
            "stage_score": dimension_scores.get("stage", 50),
            "adherence_score": dimension_scores.get("adherence", 50),
        }

        # 3. 解读
        summary, actions, profile_updates = self.interpret_results(dimension_scores, template)

        # 4. 识别行为模式标签
        behavior_tags = self._identify_behavior_patterns(dimension_scores)

        # 5. 识别内在需求标签
        need_tags = self._identify_inner_needs(dimension_scores, instance)

        # 6. 识别障碍
        barriers = self._identify_barriers(dimension_scores, instance)

        # 7. 确定风险等级
        risk_level = self._determine_risk_level(dimension_scores, core_scores)

        # 8. 构建结果
        result = AssessmentResult(
            result_id=f"AR{uuid.uuid4().hex[:8].upper()}",
            user_id=instance.user_id,
            instance_id=instance.instance_id,
            template_id=instance.template_id,
            domain=template.domain,
            core_scores=core_scores,
            dimension_scores=dimension_scores,
            behavior_pattern_tags=behavior_tags,
            inner_need_tags=need_tags,
            identified_barriers=barriers,
            risk_level=risk_level,
            confidence_level=self._calculate_confidence(instance, template),
            interpretation_summary=summary,
            recommended_interventions=actions,
            profile_updates=profile_updates
        )

        self._results[result.result_id] = result
        return result

    def _identify_behavior_patterns(self, scores: Dict[str, float]) -> List[str]:
        """识别行为模式标签"""
        tags = []
        if scores.get("motivation", 50) < 30:
            tags.append("low_motivation")
        elif scores.get("motivation", 50) > 70:
            tags.append("high_motivation")

        if scores.get("self_efficacy", 50) < 30:
            tags.append("low_self_efficacy")

        if scores.get("resistance", 50) > 70:
            tags.append("high_resistance")

        if scores.get("adherence", 50) < 40:
            tags.append("adherence_challenge")

        return tags

    def _identify_inner_needs(self, scores: Dict[str, float], instance: QuestionnaireInstance) -> List[str]:
        """识别内在需求标签"""
        needs = []
        if scores.get("social_support", 50) < 40:
            needs.append("need_social_support")
        if scores.get("autonomy", 50) > 70:
            needs.append("need_autonomy")
        if scores.get("competence", 50) < 40:
            needs.append("need_competence_building")
        return needs

    def _identify_barriers(self, scores: Dict[str, float], instance: QuestionnaireInstance) -> List[str]:
        """识别行为障碍"""
        barriers = []
        if scores.get("time_barrier", 0) > 60:
            barriers.append("time_constraint")
        if scores.get("knowledge_barrier", 0) > 60:
            barriers.append("knowledge_gap")
        if scores.get("environmental_barrier", 0) > 60:
            barriers.append("environmental_obstacle")
        if scores.get("emotional_barrier", 0) > 60:
            barriers.append("emotional_block")
        return barriers

    def _determine_risk_level(self, dimension_scores: Dict[str, float], core_scores: Dict[str, float]) -> str:
        """确定风险等级"""
        risk_indicators = 0

        if core_scores.get("motivation_score", 50) < 20:
            risk_indicators += 2
        if core_scores.get("self_efficacy_score", 50) < 20:
            risk_indicators += 2
        if core_scores.get("resistance_level", 50) > 80:
            risk_indicators += 1
        if dimension_scores.get("depression", 0) > 70:
            risk_indicators += 3
        if dimension_scores.get("anxiety", 0) > 70:
            risk_indicators += 2

        if risk_indicators >= 5:
            return "critical"
        elif risk_indicators >= 3:
            return "high"
        elif risk_indicators >= 1:
            return "moderate"
        return "low"

    def _calculate_confidence(self, instance: QuestionnaireInstance, template: QuestionnaireTemplate) -> float:
        """计算置信度"""
        total_questions = len(template.get_all_questions())
        answered = len(instance.answers)
        if total_questions == 0:
            return 0.5
        return min(1.0, answered / total_questions)

    # ========== Profile Writer ==========

    def write_to_profile(self, result: AssessmentResult, profile: Dict[str, Any]) -> Dict[str, Any]:
        """将评估结果写入用户画像 - 通过 profile_updates 渠道"""
        # 注意：实际写入应通过 Master Orchestrator 统一执行
        updates = result.profile_updates.copy()

        # 更新行为档案
        if "behavior_profile" not in updates:
            updates["behavior_profile"] = {}

        updates["behavior_profile"].update({
            "motivation_level": result.core_scores.get("motivation_score", 50) / 10,
            "self_efficacy": result.core_scores.get("self_efficacy_score", 50) / 10,
        })

        # 更新风险档案
        if "risk_profile" not in updates:
            updates["risk_profile"] = {}
        updates["risk_profile"]["mental_stress_level"] = result.risk_level

        # 添加到历史
        if "history_refs" not in updates:
            updates["history_refs"] = {}
        updates["history_refs"]["last_assessment_id"] = result.result_id
        updates["history_refs"]["last_assessment_at"] = result.assessed_at

        return updates

    # ========== Trigger Rules Management ==========

    def register_template(self, template: QuestionnaireTemplate) -> None:
        """注册问卷模板"""
        self._templates[template.template_id] = template

    def register_trigger_rule(self, rule: QuestionnaireTriggerRule) -> None:
        """注册触发规则"""
        self._trigger_rules.append(rule)

    def check_triggers(self,
                       event: TriggerEvent,
                       profile: Dict[str, Any],
                       context: Optional[Dict[str, Any]] = None) -> List[str]:
        """检查触发器，返回应触发的模板ID列表"""
        triggered_templates = []
        context = context or {}

        for rule in self._trigger_rules:
            if rule.trigger_event != event:
                continue
            if rule.check_conditions(profile, context):
                triggered_templates.append(rule.template_id)

        return triggered_templates

    # ========== Integration with AGENT System ==========

    def handle_agent_assessment_request(self,
                                        task: 'CoreAgentTask',
                                        profile: Dict[str, Any]) -> 'CoreAgentResult':
        """处理来自 AGENT 的评估请求

        当 AGENT 发送 task_type="assessment_request" 时调用
        """
        if task.task_type != CoreTaskType.ASSESSMENT_REQUEST:
            raise ValueError("Task type must be assessment_request")

        # 生成问卷
        goal = task.focus_domain or "general_assessment"
        instance = self.generate_adaptive_questionnaire(
            goal=goal,
            user_id=task.user_id,
            profile=profile,
            calling_agent=task.target_agent.value
        )

        # 如果有预填答案(从context中)
        if "prefilled_answers" in task.context_snapshot:
            for q_id, value in task.context_snapshot["prefilled_answers"].items():
                instance.add_answer(q_id, value)
            instance.complete()

            # 执行评估
            result = self.assess(instance)
            return result.to_agent_result()

        # 否则返回待填写的问卷实例
        return CoreAgentResult(
            task_id=task.task_id,
            agent_id="AssessmentEngine",
            domain=goal,
            key_findings=[f"问卷已生成: {instance.instance_id}"],
            recommendations=["请完成问卷后重新提交"],
            data_updates={"pending_questionnaire": instance.to_dict()}
        )


# ============================================================================
# 原有数据结构定义 (保持兼容)
# ============================================================================

@dataclass
class CGMData:
    """连续血糖监测数据 (Continuous Glucose Monitoring)"""
    current_glucose: Optional[float] = None      # 当前血糖 mg/dL
    trend: str = "stable"                        # rising_fast/rising/stable/falling/falling_fast
    time_in_range_percent: Optional[float] = None  # 血糖在目标范围内时间百分比
    avg_glucose_24h: Optional[float] = None      # 24小时平均血糖
    high_events_24h: int = 0                     # 高血糖事件次数 (>180)
    low_events_24h: int = 0                      # 低血糖事件次数 (<70)
    gmi: Optional[float] = None                  # 血糖管理指标
    cv: Optional[float] = None                   # 血糖变异系数


@dataclass
class HRVData:
    """心率变异性数据"""
    sdnn: Optional[float] = None                 # ms, 正常范围 50-100
    rmssd: Optional[float] = None                # ms
    lf_hf_ratio: Optional[float] = None          # 低频/高频比值
    stress_index: Optional[float] = None         # 压力指数 0-100
    recovery_score: Optional[float] = None       # 恢复评分 0-100
    readiness_score: Optional[float] = None      # 准备度评分 0-100


@dataclass
class SleepData:
    """睡眠数据"""
    duration_hours: Optional[float] = None       # 睡眠时长
    quality_score: Optional[float] = None        # 质量评分 0-100
    deep_sleep_percent: Optional[float] = None   # 深度睡眠百分比
    rem_percent: Optional[float] = None          # REM 睡眠百分比
    light_sleep_percent: Optional[float] = None  # 浅睡眠百分比
    awakenings: int = 0                          # 夜间觉醒次数
    sleep_onset_latency_min: Optional[float] = None  # 入睡时间(分钟)
    sleep_efficiency: Optional[float] = None     # 睡眠效率 0-100
    bed_time: Optional[str] = None               # 就寝时间
    wake_time: Optional[str] = None              # 起床时间


@dataclass
class DeviceData:
    """穿戴设备综合数据"""
    cgm: Optional[CGMData] = None                # 连续血糖监测
    hrv: Optional[HRVData] = None                # 心率变异性
    sleep: Optional[SleepData] = None            # 睡眠数据
    steps: int = 0                               # 步数
    heart_rate: Dict[str, Any] = field(default_factory=dict)  # 心率
    calories_burned: int = 0                     # 消耗卡路里
    active_minutes: int = 0                      # 活动分钟数
    stress_level: Optional[float] = None         # 压力水平 0-100
    body_battery: Optional[float] = None         # 身体电量 0-100
    spo2: Optional[float] = None                 # 血氧饱和度

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceData':
        """从字典创建 DeviceData"""
        cgm_data = data.get('cgm')
        hrv_data = data.get('hrv')
        sleep_data = data.get('sleep')

        return cls(
            cgm=CGMData(**cgm_data) if cgm_data else None,
            hrv=HRVData(**hrv_data) if hrv_data else None,
            sleep=SleepData(**sleep_data) if sleep_data else None,
            steps=data.get('steps', 0),
            heart_rate=data.get('heart_rate', {}),
            calories_burned=data.get('calories_burned', 0),
            active_minutes=data.get('active_minutes', 0),
            stress_level=data.get('stress_level'),
            body_battery=data.get('body_battery'),
            spo2=data.get('spo2')
        )


@dataclass
class UserInput:
    """用户输入请求 - 标准格式"""
    user_id: str
    input_type: InputType = InputType.TEXT
    content: str = ""                            # 用户输入内容 (文本/语音转文字)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_data: Optional[DeviceData] = None
    form_data: Optional[Dict[str, Any]] = None   # 表单数据
    efficacy_score: float = 50.0                 # 效能感评分 0-100
    context: Dict[str, Any] = field(default_factory=dict)  # 附加上下文

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInput':
        """从字典创建 UserInput (支持 JSON 输入，自动兼容旧格式)"""
        # 使用兼容层转换旧格式
        converted = DataFormatConverter.convert_user_input(data)

        input_type_str = converted.get('input_type', 'text')
        input_type = InputType(input_type_str) if input_type_str in [e.value for e in InputType] else InputType.TEXT

        device_data = converted.get('device_data')

        # 处理 content 字段 (兼容 message/query/text/input)
        content = converted.get('content', '')
        if not content:
            for alt_key in ['message', 'query', 'text', 'input']:
                if alt_key in converted:
                    content = converted[alt_key]
                    break

        return cls(
            user_id=converted.get('user_id', data.get('user_id', '')),
            input_type=input_type,
            content=content,
            timestamp=converted.get('timestamp', datetime.now().isoformat()),
            session_id=converted.get('session_id', str(uuid.uuid4())),
            device_data=DeviceData.from_dict(device_data) if device_data else None,
            form_data=converted.get('form_data'),
            efficacy_score=converted.get('efficacy_score', 50.0),
            context=converted.get('context', {})
        )

    # 兼容旧接口
    @property
    def message(self) -> str:
        return self.content

    @property
    def request_type(self) -> InputType:
        return self.input_type


@dataclass
class RoutingDecision:
    """路由决策"""
    input_type: InputType
    risk_level: RiskLevel
    risk_score: float  # 0-100
    risk_factors: List[str]
    primary_agent: str
    secondary_agents: List[str]
    requires_intervention: bool
    routing_confidence: float
    reasoning: str


@dataclass
class HealthAlert:
    """健康告警"""
    alert_type: str              # sleep, glucose, hrv, stress, etc.
    severity: str                # info, warning, critical
    message: str
    recommendation: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None


@dataclass
class HealthTrend:
    """健康趋势"""
    metric: str                  # sleep_quality, glucose_tir, hrv_sdnn, etc.
    direction: str               # improving, stable, declining
    change_percent: float
    interpretation: str
    period_days: int = 7


@dataclass
class Insights:
    """数据洞察"""
    health_summary: str
    alerts: List[HealthAlert] = field(default_factory=list)
    trends: List[HealthTrend] = field(default_factory=list)
    correlations: List[str] = field(default_factory=list)  # 指标间关联发现
    recommendations_priority: List[str] = field(default_factory=list)


@dataclass
class AgentResponse:
    """专家Agent响应"""
    agent_id: str
    agent_name: str
    response_text: str
    confidence: float
    suggestions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommended_actions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CoordinatedResult:
    """协调整合后的结果"""
    primary_response: AgentResponse
    supplementary_responses: List[AgentResponse]
    unified_context: Dict[str, Any]
    consensus_points: List[str]
    conflict_resolutions: List[Dict[str, str]]


@dataclass
class InterventionPlan:
    """干预计划"""
    plan_id: str
    user_id: str
    created_at: str
    intervention_type: str
    intervention_strategy: str
    tasks: List[Dict[str, Any]]
    knowledge_points: List[Dict[str, Any]]
    videos: List[Dict[str, Any]]
    products: List[Dict[str, Any]]
    coach_script: str
    follow_up_points: List[str]
    expected_duration_days: int
    difficulty_level: int
    max_tasks_today: int


class ActionType(Enum):
    """行动类型"""
    BEHAVIOR = "behavior"       # 行为改变
    MONITOR = "monitor"         # 监测追踪
    EDUCATION = "education"     # 教育学习
    EXERCISE = "exercise"       # 运动锻炼
    NUTRITION = "nutrition"     # 营养饮食
    RELAXATION = "relaxation"   # 放松减压
    SOCIAL = "social"           # 社交支持
    MEDICAL = "medical"         # 医疗相关


@dataclass
class PlanAction:
    """计划行动项"""
    type: ActionType
    content: str
    timing: Optional[str] = None        # 执行时间 (如 "22:30")
    frequency: str = "daily"            # daily/weekly/once
    duration_minutes: Optional[int] = None
    resources: Dict[str, str] = field(default_factory=dict)  # 关联资源
    priority: int = 2                   # 1-3 (1最高)
    completed: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlanAction':
        """从字典创建"""
        action_type_str = data.get('type', 'behavior')
        action_type = ActionType.BEHAVIOR
        for at in ActionType:
            if at.value == action_type_str:
                action_type = at
                break
        return cls(
            type=action_type,
            content=data.get('content', ''),
            timing=data.get('timing'),
            frequency=data.get('frequency', 'daily'),
            duration_minutes=data.get('duration_minutes'),
            resources=data.get('resources', {}),
            priority=data.get('priority', 2),
            completed=data.get('completed', False)
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "type": self.type.value,
            "content": self.content
        }
        if self.timing:
            result["timing"] = self.timing
        if self.frequency != "daily":
            result["frequency"] = self.frequency
        if self.duration_minutes:
            result["duration_minutes"] = self.duration_minutes
        if self.resources:
            result["resources"] = self.resources
        if self.priority != 2:
            result["priority"] = self.priority
        if self.completed:
            result["completed"] = self.completed
        return result


@dataclass
class PlanEvaluation:
    """计划评估标准"""
    metrics: List[str] = field(default_factory=list)     # 评估指标
    targets: Dict[str, Any] = field(default_factory=dict)  # 目标值
    checkpoints: List[str] = field(default_factory=list)   # 检查点时间

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlanEvaluation':
        """从字典创建"""
        return cls(
            metrics=data.get('metrics', []),
            targets=data.get('targets', {}),
            checkpoints=data.get('checkpoints', [])
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "metrics": self.metrics,
            "targets": self.targets,
            "checkpoints": self.checkpoints
        }


@dataclass
class ActionPlan:
    """行动计划 - 阶段性干预方案

    格式示例:
    {
      "goal": "改善睡眠 + 稳定夜间血糖",
      "phase": "week_1",
      "actions": [
        { "type": "behavior", "content": "22:30 上床，睡前不进食" },
        { "type": "monitor", "content": "连续3晚查看夜间CGM" },
        { "type": "education", "content": "观看《睡眠与血糖》视频" }
      ],
      "evaluation": {
        "metrics": ["sleep_efficiency", "night_glucose"]
      }
    }
    """
    goal: str
    phase: str                                           # week_1, week_2, month_1, etc.
    actions: List[PlanAction] = field(default_factory=list)
    evaluation: Optional[PlanEvaluation] = None
    plan_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    status: str = "active"                               # active/paused/completed
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self):
        if not self.plan_id:
            self.plan_id = f"AP{uuid.uuid4().hex[:8].upper()}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionPlan':
        """从字典创建 ActionPlan"""
        actions = []
        for action_data in data.get('actions', []):
            actions.append(PlanAction.from_dict(action_data))

        evaluation = None
        if data.get('evaluation'):
            evaluation = PlanEvaluation.from_dict(data['evaluation'])

        return cls(
            goal=data.get('goal', ''),
            phase=data.get('phase', 'week_1'),
            actions=actions,
            evaluation=evaluation,
            plan_id=data.get('plan_id'),
            user_id=data.get('user_id'),
            created_at=data.get('created_at'),
            status=data.get('status', 'active'),
            tags=data.get('tags', []),
            notes=data.get('notes', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "phase": self.phase,
            "actions": [a.to_dict() for a in self.actions],
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "status": self.status,
            "tags": self.tags,
            "notes": self.notes
        }

    def get_actions_by_type(self, action_type: ActionType) -> List[PlanAction]:
        """按类型获取行动项"""
        return [a for a in self.actions if a.type == action_type]

    def get_pending_actions(self) -> List[PlanAction]:
        """获取未完成的行动项"""
        return [a for a in self.actions if not a.completed]

    def mark_action_completed(self, index: int) -> bool:
        """标记行动项完成"""
        if 0 <= index < len(self.actions):
            self.actions[index].completed = True
            return True
        return False

    def progress_percent(self) -> float:
        """计算完成进度百分比"""
        if not self.actions:
            return 0.0
        completed = sum(1 for a in self.actions if a.completed)
        return round(completed / len(self.actions) * 100, 1)

    def to_daily_tasks(self, session_id: str) -> List['DailyTask']:
        """转换为今日任务列表"""
        tasks = []
        for i, action in enumerate(self.get_pending_actions()[:3]):  # 最多3个
            task_type_mapping = {
                ActionType.BEHAVIOR: "sleep" if "睡" in action.content else "cognitive",
                ActionType.MONITOR: "cognitive",
                ActionType.EDUCATION: "cognitive",
                ActionType.EXERCISE: "exercise",
                ActionType.NUTRITION: "nutrition",
                ActionType.RELAXATION: "meditation",
                ActionType.SOCIAL: "social",
                ActionType.MEDICAL: "cognitive"
            }
            tasks.append(DailyTask(
                task_id=f"task_{session_id}_{i}",
                title=action.content[:30],
                description=action.content,
                task_type=task_type_mapping.get(action.type, "cognitive"),
                difficulty=action.priority,
                duration_minutes=action.duration_minutes or 15,
                scheduled_time=action.timing,
                priority=action.priority,
                resources=action.resources,
                tracking_points=[f"完成{action.type.value}任务"],
                completion_criteria=f"完成: {action.content}"
            ))
        return tasks


@dataclass
class SynthesizedResponse:
    """合成后的最终响应"""
    response_text: str
    coach_style: str  # supportive, motivational, educational, empathetic
    tone: str
    key_messages: List[str]
    action_items: List[str]
    follow_up_questions: List[str]


@dataclass
class DailyTask:
    """今日任务"""
    task_id: str
    title: str
    description: str
    task_type: str  # breathing, meditation, exercise, nutrition, sleep, social, cognitive
    difficulty: int  # 1-5
    duration_minutes: int
    scheduled_time: Optional[str] = None
    priority: int = 1
    resources: Dict[str, str] = field(default_factory=dict)  # knowledge_link, video_link, product_id
    tracking_points: List[str] = field(default_factory=list)
    completion_criteria: str = ""


@dataclass
class Reminder:
    """提醒"""
    time: str
    message: str


@dataclass
class Tracking:
    """追踪信息"""
    points: List[str] = field(default_factory=list)
    next_check_in: Optional[str] = None
    reminders: List[Reminder] = field(default_factory=list)


@dataclass
class ProfileUpdates:
    """画像更新摘要"""
    updated_fields: List[str] = field(default_factory=list)
    new_risk_flags: List[str] = field(default_factory=list)
    stage_change: bool = False
    efficacy_change: float = 0.0


@dataclass
class DailyBriefing:
    """每日简报 - 推送给用户的今日任务摘要

    格式示例:
    {
      "user_id": "U12345",
      "date": "2026-01-23",
      "tasks": [
        "今晚22:30前上床",
        "记录睡前进食情况",
        "查看夜间血糖趋势"
      ],
      "coach_message": "今晚我们先从规律作息开始，一小步就很好。"
    }
    """
    user_id: str
    date: str
    tasks: List[str]
    coach_message: str
    greeting: str = ""                                    # 问候语
    focus_area: str = ""                                  # 今日重点领域
    encouragement: str = ""                               # 鼓励语
    streak_days: int = 0                                  # 连续完成天数
    progress_summary: Optional[str] = None                # 进度摘要
    alerts: List[str] = field(default_factory=list)       # 需要注意的事项
    reminders: List[Dict[str, str]] = field(default_factory=list)  # 定时提醒
    resources: Dict[str, str] = field(default_factory=dict)  # 相关资源链接

    def __post_init__(self):
        if not self.greeting:
            hour = datetime.now().hour
            if hour < 6:
                self.greeting = "夜深了"
            elif hour < 12:
                self.greeting = "早上好"
            elif hour < 14:
                self.greeting = "中午好"
            elif hour < 18:
                self.greeting = "下午好"
            else:
                self.greeting = "晚上好"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailyBriefing':
        """从字典创建"""
        return cls(
            user_id=data.get('user_id', ''),
            date=data.get('date', datetime.now().strftime('%Y-%m-%d')),
            tasks=data.get('tasks', []),
            coach_message=data.get('coach_message', ''),
            greeting=data.get('greeting', ''),
            focus_area=data.get('focus_area', ''),
            encouragement=data.get('encouragement', ''),
            streak_days=data.get('streak_days', 0),
            progress_summary=data.get('progress_summary'),
            alerts=data.get('alerts', []),
            reminders=data.get('reminders', []),
            resources=data.get('resources', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 (简化版 - 用于推送)"""
        return {
            "user_id": self.user_id,
            "date": self.date,
            "tasks": self.tasks,
            "coach_message": self.coach_message
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """转换为完整字典"""
        result = {
            "user_id": self.user_id,
            "date": self.date,
            "greeting": self.greeting,
            "tasks": self.tasks,
            "coach_message": self.coach_message
        }
        if self.focus_area:
            result["focus_area"] = self.focus_area
        if self.encouragement:
            result["encouragement"] = self.encouragement
        if self.streak_days > 0:
            result["streak_days"] = self.streak_days
        if self.progress_summary:
            result["progress_summary"] = self.progress_summary
        if self.alerts:
            result["alerts"] = self.alerts
        if self.reminders:
            result["reminders"] = self.reminders
        if self.resources:
            result["resources"] = self.resources
        return result

    def format_message(self) -> str:
        """格式化为推送消息文本"""
        lines = [f"{self.greeting}！"]

        if self.streak_days > 0:
            lines.append(f"🔥 您已连续完成 {self.streak_days} 天")

        lines.append("")
        lines.append("📋 今日任务：")
        for i, task in enumerate(self.tasks, 1):
            lines.append(f"  {i}. {task}")

        lines.append("")
        lines.append(f"💬 {self.coach_message}")

        if self.encouragement:
            lines.append("")
            lines.append(f"✨ {self.encouragement}")

        return "\n".join(lines)

    @classmethod
    def from_action_plan(cls,
                         plan: 'ActionPlan',
                         profile: Dict[str, Any],
                         coach_style: str = "gentle") -> 'DailyBriefing':
        """从 ActionPlan 生成每日简报"""
        # 提取任务文本
        tasks = [action.content for action in plan.get_pending_actions()[:5]]

        # 生成教练消息
        coach_message = cls._generate_coach_message(plan, profile, coach_style)

        # 确定重点领域
        action_types = [a.type.value for a in plan.actions]
        if "sleep" in str(action_types) or "behavior" in action_types:
            focus_area = "睡眠改善"
        elif "nutrition" in action_types:
            focus_area = "营养管理"
        elif "exercise" in action_types:
            focus_area = "运动健身"
        else:
            focus_area = "健康管理"

        # 获取连续天数
        streak_days = profile.get("behavior", {}).get("streak_days", 0)

        # 生成鼓励语
        encouragement = cls._generate_encouragement(profile, streak_days)

        return cls(
            user_id=profile.get("user_id", ""),
            date=datetime.now().strftime('%Y-%m-%d'),
            tasks=tasks,
            coach_message=coach_message,
            focus_area=focus_area,
            streak_days=streak_days,
            encouragement=encouragement
        )

    @staticmethod
    def _generate_coach_message(plan: 'ActionPlan',
                                profile: Dict[str, Any],
                                coach_style: str) -> str:
        """生成教练消息"""
        stage = profile.get("behavior", {}).get("stage", "resistance")
        task_count = len(plan.get_pending_actions())

        # 根据行为阶段和教练风格生成消息
        messages = {
            "resistance": {
                "gentle": "今天我们只做一小步，不急，慢慢来。",
                "direct": "今天有几个小任务，试试看？",
                "motivational": "相信自己，每一小步都是进步！",
                "educational": "今天的任务会帮助您了解自己的身体。"
            },
            "ambivalence": {
                "gentle": "您已经开始思考改变了，这很棒。今天继续保持。",
                "direct": f"今天{task_count}个任务，您可以的。",
                "motivational": "改变正在发生，继续加油！",
                "educational": "今天的任务基于您的数据定制。"
            },
            "compromise": {
                "gentle": "今晚我们先从规律作息开始，一小步就很好。",
                "direct": f"今天重点：{plan.goal}",
                "motivational": "您已经走了很远，今天再进一步！",
                "educational": "今天的任务将巩固您的新习惯。"
            },
            "adaptation": {
                "gentle": "您做得很好，今天继续保持节奏。",
                "direct": "今天的任务您应该很熟悉了。",
                "motivational": "习惯正在形成，继续保持！",
                "educational": "今天可以尝试增加一点挑战。"
            },
            "integration": {
                "gentle": "健康已成为您生活的一部分。",
                "direct": "今天继续您的健康日常。",
                "motivational": "您已经是健康生活的榜样！",
                "educational": "今天可以分享您的经验给他人。"
            }
        }

        stage_messages = messages.get(stage, messages["compromise"])
        return stage_messages.get(coach_style, stage_messages["gentle"])

    @staticmethod
    def _generate_encouragement(profile: Dict[str, Any], streak_days: int) -> str:
        """生成鼓励语"""
        if streak_days >= 21:
            return "21天习惯已养成，继续保持！"
        elif streak_days >= 7:
            return f"连续{streak_days}天，您正在建立新习惯！"
        elif streak_days >= 3:
            return "坚持了几天，势头很好！"
        elif streak_days == 1:
            return "昨天完成得很好，今天继续！"
        else:
            efficacy = profile.get("psych", {}).get("efficacy_score", 50)
            if efficacy < 40:
                return "每一次尝试都是进步。"
            else:
                return "今天是新的开始。"


class AgentType(Enum):
    """专业 Agent 类型"""
    SLEEP = "SleepAgent"
    GLUCOSE = "GlucoseAgent"
    STRESS = "StressAgent"
    NUTRITION = "NutritionAgent"
    EXERCISE = "ExerciseAgent"
    MENTAL_HEALTH = "MentalHealthAgent"
    TCM_WELLNESS = "TCMWellnessAgent"
    CRISIS = "CrisisAgent"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentTaskFinding:
    """Agent 分析发现"""
    category: str
    observation: str
    severity: str = "info"  # info, warning, critical
    confidence: float = 0.8


@dataclass
class AgentTaskCorrelation:
    """Agent 发现的相关性"""
    factor_a: str
    factor_b: str
    relationship: str
    strength: str = "moderate"  # weak, moderate, strong


@dataclass
class AgentTaskRecommendation:
    """Agent 干预建议"""
    type: str  # behavioral, nutritional, medical, lifestyle, psychological
    action: str
    rationale: str
    priority: int = 3  # 1-5
    difficulty: int = 2  # 1-5
    duration_minutes: int = 10
    timing: Optional[str] = None
    resources: Dict[str, str] = field(default_factory=dict)


@dataclass
class AgentTaskAnalysis:
    """Agent 分析结果"""
    summary: str
    findings: List[AgentTaskFinding] = field(default_factory=list)
    correlations: List[AgentTaskCorrelation] = field(default_factory=list)


@dataclass
class AgentTaskFollowUp:
    """Agent 跟进建议"""
    suggested_questions: List[str] = field(default_factory=list)
    monitoring_points: List[str] = field(default_factory=list)
    escalation_needed: bool = False
    escalation_reason: Optional[str] = None


@dataclass
class AgentTask:
    """发送给专业 Agent 的任务请求"""
    task_id: str
    agent_type: AgentType
    question: str
    priority: str = "normal"  # critical, high, normal, low
    context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.metadata.get("created_at"):
            self.metadata["created_at"] = datetime.now().isoformat()
        if not self.metadata.get("requester"):
            self.metadata["requester"] = "MasterAgent"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentTask':
        """从字典创建 AgentTask"""
        agent_type_str = data.get('agent_type', 'MentalHealthAgent')
        # 查找匹配的 AgentType
        agent_type = AgentType.MENTAL_HEALTH
        for at in AgentType:
            if at.value == agent_type_str:
                agent_type = at
                break
        return cls(
            task_id=data.get('task_id', f"T{uuid.uuid4().hex[:8]}"),
            agent_type=agent_type,
            question=data.get('question', ''),
            priority=data.get('priority', 'normal'),
            context=data.get('context', {}),
            constraints=data.get('constraints', {}),
            metadata=data.get('metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type.value,
            "question": self.question,
            "priority": self.priority,
            "context": self.context,
            "constraints": self.constraints,
            "metadata": self.metadata
        }


@dataclass
class AgentAnalysisResult:
    """简化版 Agent 分析结果 - 用于快速通信和缓存

    格式示例:
    {
      "agent": "SleepAgent",
      "analysis": "用户存在睡眠碎片化 + 夜间高血糖",
      "risk_level": "medium",
      "suggestions": ["固定入睡时间", "睡前避免进食"],
      "tags": ["sleep", "glucose", "circadian"]
    }
    """
    agent: str                                          # Agent 标识
    analysis: str                                       # 分析摘要
    risk_level: str = "low"                             # low/medium/high/critical
    suggestions: List[str] = field(default_factory=list)  # 建议列表
    tags: List[str] = field(default_factory=list)       # 标签 (用于分类/检索)
    confidence: float = 0.8                             # 置信度 0-1
    timestamp: Optional[str] = None                     # 分析时间

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentAnalysisResult':
        """从字典创建"""
        return cls(
            agent=data.get('agent', 'UnknownAgent'),
            analysis=data.get('analysis', ''),
            risk_level=data.get('risk_level', 'low'),
            suggestions=data.get('suggestions', []),
            tags=data.get('tags', []),
            confidence=data.get('confidence', 0.8),
            timestamp=data.get('timestamp')
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent": self.agent,
            "analysis": self.analysis,
            "risk_level": self.risk_level,
            "suggestions": self.suggestions,
            "tags": self.tags,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_task_response(cls, response: 'AgentTaskResponse') -> 'AgentAnalysisResult':
        """从完整 AgentTaskResponse 转换为简化格式"""
        # 提取建议
        suggestions = [r.action for r in response.recommendations[:5]]

        # 提取标签 (从 findings 和 correlations)
        tags = set()
        if response.analysis:
            for finding in response.analysis.findings:
                tags.add(finding.category)
            for corr in response.analysis.correlations:
                tags.add(corr.factor_a.replace(" ", "_").lower())
                tags.add(corr.factor_b.replace(" ", "_").lower())

        # 确定风险等级
        risk_level = "low"
        if response.analysis:
            critical_count = sum(1 for f in response.analysis.findings if f.severity == "critical")
            warning_count = sum(1 for f in response.analysis.findings if f.severity == "warning")
            if critical_count > 0:
                risk_level = "high"
            elif warning_count >= 2:
                risk_level = "medium"
            elif warning_count == 1:
                risk_level = "low"

        return cls(
            agent=response.agent_type.value,
            analysis=response.analysis.summary if response.analysis else response.response_text[:200],
            risk_level=risk_level,
            suggestions=suggestions,
            tags=list(tags),
            confidence=response.metadata.get("confidence_score", 0.8),
            timestamp=response.metadata.get("completed_at")
        )


@dataclass
class AgentTaskResponse:
    """专业 Agent 返回的任务响应"""
    task_id: str
    agent_type: AgentType
    status: TaskStatus
    analysis: Optional[AgentTaskAnalysis] = None
    recommendations: List[AgentTaskRecommendation] = field(default_factory=list)
    response_text: str = ""
    coach_notes: str = ""  # 给 Master Agent 的内部备注
    follow_up: Optional[AgentTaskFollowUp] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.metadata.get("completed_at"):
            self.metadata["completed_at"] = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "analysis": {
                "summary": self.analysis.summary if self.analysis else "",
                "findings": [asdict(f) for f in (self.analysis.findings if self.analysis else [])],
                "correlations": [asdict(c) for c in (self.analysis.correlations if self.analysis else [])]
            } if self.analysis else None,
            "recommendations": [asdict(r) for r in self.recommendations],
            "response_text": self.response_text,
            "coach_notes": self.coach_notes,
            "follow_up": asdict(self.follow_up) if self.follow_up else None,
            "metadata": self.metadata
        }


@dataclass
class MasterAgentResponse:
    """Master Agent 最终响应 - 完整输出格式"""
    session_id: str
    user_id: str
    timestamp: str

    # 路由信息
    routing: RoutingDecision

    # 最终响应
    response: SynthesizedResponse

    # 数据洞察
    insights: Optional[Insights] = None

    # 干预计划 (如适用)
    intervention_plan: Optional[InterventionPlan] = None

    # 今日任务
    daily_tasks: List[DailyTask] = field(default_factory=list)

    # 追踪信息
    tracking: Optional[Tracking] = None

    # 画像更新摘要
    profile_updates: Optional[ProfileUpdates] = None

    # 处理元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为标准输出字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "routing": {
                "input_type": self.routing.input_type.value,
                "risk_level": self.routing.risk_level.value,
                "risk_score": self.routing.risk_score,
                "risk_factors": self.routing.risk_factors,
                "primary_agent": self.routing.primary_agent,
                "secondary_agents": self.routing.secondary_agents,
                "requires_intervention": self.routing.requires_intervention
            },
            "response": {
                "text": self.response.response_text,
                "coach_style": self.response.coach_style,
                "tone": self.response.tone,
                "key_messages": self.response.key_messages,
                "action_items": self.response.action_items,
                "follow_up_questions": self.response.follow_up_questions
            },
            "insights": asdict(self.insights) if self.insights else None,
            "intervention_plan": asdict(self.intervention_plan) if self.intervention_plan else None,
            "daily_tasks": [asdict(t) for t in self.daily_tasks],
            "tracking": asdict(self.tracking) if self.tracking else None,
            "profile_updates": asdict(self.profile_updates) if self.profile_updates else None,
            "metadata": self.metadata
        }


# ============================================================================
# User Master Profile 管理
# ============================================================================

class UserMasterProfile:
    """用户主画像管理器

    基于 user_state_schema.json 的完整用户画像，
    贯穿整个处理流程，支持读取、更新、写回。
    """

    def __init__(self, storage_path: str = "data/profiles"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        # 优先从缓存读取
        if user_id in self._cache:
            return self._cache[user_id]

        # 从文件读取
        profile_path = self.storage_path / f"{user_id}.json"
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
                self._cache[user_id] = profile
                return profile

        # 新用户，创建默认画像
        return self._create_default_profile(user_id)

    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户画像 (深度合并)"""
        profile = self.get_profile(user_id)
        self._deep_merge(profile, updates)
        profile["last_updated"] = datetime.now().isoformat()
        self._cache[user_id] = profile
        return profile

    def save_profile(self, user_id: str) -> bool:
        """持久化用户画像"""
        if user_id not in self._cache:
            return False

        profile_path = self.storage_path / f"{user_id}.json"
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(self._cache[user_id], f, ensure_ascii=False, indent=2)
        return True

    def _create_default_profile(self, user_id: str) -> Dict[str, Any]:
        """创建默认用户画像 (v2.0 结构)"""
        profile = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),

            # 基本信息
            "basic": {
                "age": None,
                "sex": None,
                "height_cm": None,
                "weight_kg": None
            },

            # 医疗信息
            "medical": {
                "diabetes": "none",
                "bp": None,
                "bp_category": None,
                "medications": [],
                "conditions": []
            },

            # 行为状态 (基于自研五层次模型)
            "behavior": {
                "stage": "resistance",           # 默认完全对抗
                "stage_chinese": "完全对抗",
                "spi_coefficient": 0.3,
                "patterns": [],
                "adherence_score": 0.0,
                "task_completion_rate": 0.0,
                "streak_days": 0,
                "cultivation_phase": "startup"   # 启动期
            },

            # 心理状态
            "psych": {
                "stress_level": "medium",
                "stress_score": 50,
                "motivation": "medium",
                "motivation_score": 50,
                "efficacy_score": 50,
                "anxiety_level": "normal",
                "depression_level": "normal",
                "mood_trend": "stable",
                "social_support": "moderate"
            },

            # 体质指标
            "constitution": {
                "bmi": None,
                "bmi_category": None,
                "visceral_fat": None,
                "inflammation_risk": None,
                "tcm_constitution": None
            },

            # 生物指标 (设备/检测)
            "biometrics": {
                "glucose": {
                    "fasting": None,
                    "hba1c": None,
                    "tir": None,
                    "trend": "stable"
                },
                "hrv": {
                    "sdnn": None,
                    "rmssd": None,
                    "trend": "stable"
                },
                "sleep": {
                    "avg_duration": None,
                    "avg_quality": None,
                    "trend": "stable"
                },
                "activity": {
                    "avg_steps": 0,
                    "active_minutes_weekly": 0,
                    "exercise_frequency": "none"
                }
            },

            # 用户偏好
            "preferences": {
                "focus": [],
                "coaching_style": "gentle",
                "max_tasks_per_day": 2,
                "language": "zh-CN"
            },

            # 健康目标
            "goals": {
                "primary": None,
                "secondary": []
            },

            # 风险标记
            "risk_flags": [],

            # 历史记录
            "history": {
                "total_sessions": 0,
                "first_session": None,
                "last_session": None,
                "total_tasks_assigned": 0,
                "total_tasks_completed": 0,
                "assessments_count": 0
            },

            # 当前干预
            "current_intervention": None,

            # 今日状态
            "today": {
                "tasks": [],
                "mood_log": [],
                "device_sync_time": None,
                "check_ins": 0
            },

            # 会话历史 (上下文)
            "session_history": []
        }

        self._cache[user_id] = profile
        return profile

    def set_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """直接设置用户画像 (用于初始化已知用户)"""
        profile = self._create_default_profile(user_id)
        self._deep_merge(profile, profile_data)
        profile["updated_at"] = datetime.now().isoformat()
        self._cache[user_id] = profile
        self.save_profile(user_id)
        return profile

    def _deep_merge(self, base: Dict, updates: Dict):
        """深度合并字典"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value


# ============================================================================
# 风险优先级评估器
# ============================================================================

class RiskPriorityAssessor:
    """风险优先级评估器

    基于用户画像和当前输入，评估风险等级和优先级。
    """

    # 高风险关键词
    EMERGENCY_KEYWORDS = [
        "自杀", "自残", "不想活", "死", "跳楼", "割腕", "结束生命",
        "伤害自己", "活着没意思", "想死", "轻生"
    ]

    HIGH_RISK_KEYWORDS = [
        "崩溃", "绝望", "恐慌", "无法呼吸", "心脏剧痛", "晕倒",
        "失控", "暴怒", "严重失眠", "连续几天没睡"
    ]

    # 生理指标风险阈值
    PHYSIOLOGICAL_THRESHOLDS = {
        "hrv_sdnn_critical": 30,    # SDNN < 30 危急
        "hrv_sdnn_high": 40,        # SDNN < 40 高风险
        "sleep_critical": 3,         # 睡眠 < 3小时 危急
        "sleep_high": 4,             # 睡眠 < 4小时 高风险
        "resting_hr_high": 100       # 静息心率 > 100 高风险
    }

    # CGM 血糖阈值
    CGM_THRESHOLDS = {
        "glucose_critical_high": 300,   # 血糖 > 300 危急
        "glucose_critical_low": 54,     # 血糖 < 54 危急
        "glucose_high": 250,            # 血糖 > 250 高风险
        "glucose_low": 70,              # 血糖 < 70 高风险
        "tir_low": 50,                  # 时间在范围内 < 50% 高风险
        "cv_high": 36                   # 血糖变异系数 > 36% 高风险
    }

    # 心理指标风险阈值
    PSYCHOLOGICAL_THRESHOLDS = {
        "anxiety_severe": 80,
        "depression_severe": 80,
        "stress_severe": 80
    }

    def assess(self,
               user_input: UserInput,
               profile: Dict[str, Any]) -> Tuple[RiskLevel, float, List[str]]:
        """
        评估风险等级

        Returns:
            (risk_level, risk_score, risk_factors)
        """
        risk_factors = []
        risk_score = 0.0

        # 1. 检查紧急关键词
        message_lower = user_input.message.lower()

        for keyword in self.EMERGENCY_KEYWORDS:
            if keyword in message_lower:
                risk_factors.append(f"紧急关键词: {keyword}")
                return RiskLevel.CRITICAL, 100.0, risk_factors

        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in message_lower:
                risk_factors.append(f"高风险关键词: {keyword}")
                risk_score += 30

        # 2. 检查设备数据 (优先使用实时设备数据，其次 profile.biometrics)
        device = user_input.device_data
        biometrics = profile.get("biometrics", {})

        # HRV 检查 (优先设备数据)
        hrv_sdnn = None
        if device and device.hrv:
            hrv_sdnn = device.hrv.sdnn
        else:
            hrv = biometrics.get("hrv", {})
            hrv_sdnn = hrv.get("sdnn")

        if hrv_sdnn is not None:
            if hrv_sdnn < self.PHYSIOLOGICAL_THRESHOLDS["hrv_sdnn_critical"]:
                risk_factors.append(f"HRV SDNN 危急: {hrv_sdnn}ms")
                risk_score += 40
            elif hrv_sdnn < self.PHYSIOLOGICAL_THRESHOLDS["hrv_sdnn_high"]:
                risk_factors.append(f"HRV SDNN 偏低: {hrv_sdnn}ms")
                risk_score += 20

        # 睡眠检查 (优先设备数据)
        sleep_duration = None
        if device and device.sleep:
            sleep_duration = device.sleep.duration_hours
        else:
            sleep = biometrics.get("sleep", {})
            sleep_duration = sleep.get("avg_duration")

        if sleep_duration is not None:
            if sleep_duration < self.PHYSIOLOGICAL_THRESHOLDS["sleep_critical"]:
                risk_factors.append(f"严重睡眠不足: {sleep_duration}小时")
                risk_score += 35
            elif sleep_duration < self.PHYSIOLOGICAL_THRESHOLDS["sleep_high"]:
                risk_factors.append(f"睡眠不足: {sleep_duration}小时")
                risk_score += 15

        # 静息心率检查
        resting_hr = None
        if device and device.heart_rate:
            resting_hr = device.heart_rate.get("resting")

        if resting_hr is not None and resting_hr > self.PHYSIOLOGICAL_THRESHOLDS["resting_hr_high"]:
            risk_factors.append(f"静息心率偏高: {resting_hr}bpm")
            risk_score += 15

        # 3. CGM 血糖检查
        if device and device.cgm:
            cgm = device.cgm
            # 当前血糖
            if cgm.current_glucose is not None:
                if cgm.current_glucose > self.CGM_THRESHOLDS["glucose_critical_high"]:
                    risk_factors.append(f"血糖危急过高: {cgm.current_glucose}mg/dL")
                    risk_score += 45
                elif cgm.current_glucose < self.CGM_THRESHOLDS["glucose_critical_low"]:
                    risk_factors.append(f"血糖危急过低: {cgm.current_glucose}mg/dL")
                    risk_score += 50  # 低血糖更危险
                elif cgm.current_glucose > self.CGM_THRESHOLDS["glucose_high"]:
                    risk_factors.append(f"血糖偏高: {cgm.current_glucose}mg/dL")
                    risk_score += 20
                elif cgm.current_glucose < self.CGM_THRESHOLDS["glucose_low"]:
                    risk_factors.append(f"血糖偏低: {cgm.current_glucose}mg/dL")
                    risk_score += 25

            # 时间在范围内
            if cgm.time_in_range_percent is not None:
                if cgm.time_in_range_percent < self.CGM_THRESHOLDS["tir_low"]:
                    risk_factors.append(f"血糖波动大: TIR {cgm.time_in_range_percent}%")
                    risk_score += 15

            # 低血糖事件
            if cgm.low_events_24h and cgm.low_events_24h >= 2:
                risk_factors.append(f"24小时内多次低血糖: {cgm.low_events_24h}次")
                risk_score += 20

        # 4. 检查心理指标 (v2.0 结构: profile.psych)
        psych = profile.get("psych", {})

        # 检查压力
        stress_score = psych.get("stress_score")
        stress_level = psych.get("stress_level")
        if stress_score is not None and stress_score >= self.PSYCHOLOGICAL_THRESHOLDS["stress_severe"]:
            risk_factors.append(f"压力评分严重: {stress_score}")
            risk_score += 25
        elif stress_level == "severe":
            risk_factors.append("压力水平严重")
            risk_score += 25
        elif stress_level == "high":
            risk_factors.append("压力水平偏高")
            risk_score += 15

        # 检查焦虑/抑郁 level
        if psych.get("anxiety_level") == "severe":
            risk_factors.append("焦虑水平严重")
            risk_score += 25
        elif psych.get("anxiety_level") == "moderate":
            risk_factors.append("焦虑水平中等")
            risk_score += 10

        if psych.get("depression_level") == "severe":
            risk_factors.append("抑郁水平严重")
            risk_score += 25
        elif psych.get("depression_level") == "moderate":
            risk_factors.append("抑郁水平中等")
            risk_score += 10

        # 5. 检查效能感
        efficacy = user_input.efficacy_score
        if efficacy < 20:
            risk_factors.append(f"效能感极低: {efficacy}")
            risk_score += 20
        elif efficacy < 40:
            risk_factors.append(f"效能感偏低: {efficacy}")
            risk_score += 10

        # 6. 检查已有风险标记 (v2.0 结构: profile.risk_flags)
        existing_flags = profile.get("risk_flags", [])
        for flag in existing_flags:
            if not flag.get("resolved", False):
                severity = flag.get("severity", "low")
                if severity in ["high", "critical"]:
                    risk_factors.append(f"历史高风险: {flag.get('flag')}")
                    risk_score += 15
                elif severity == "medium":
                    risk_factors.append(f"历史风险: {flag.get('flag')}")
                    risk_score += 8

        # 7. 确定风险等级
        risk_score = min(risk_score, 100)

        if risk_score >= 80:
            return RiskLevel.HIGH, risk_score, risk_factors
        elif risk_score >= 50:
            return RiskLevel.MODERATE, risk_score, risk_factors
        else:
            return RiskLevel.LOW, risk_score, risk_factors


# ============================================================================
# 数据洞察生成器
# ============================================================================

class InsightGenerator:
    """数据洞察生成器

    分析用户数据，生成健康洞察、告警和趋势。
    """

    def generate(self,
                 user_input: UserInput,
                 profile: Dict[str, Any],
                 risk_factors: List[str]) -> Insights:
        """生成数据洞察"""
        alerts = []
        trends = []
        correlations = []
        recommendations = []

        device = user_input.device_data

        # 生成告警
        alerts = self._generate_alerts(device, profile, risk_factors)

        # 生成趋势分析
        trends = self._generate_trends(device, profile)

        # 生成关联发现
        correlations = self._find_correlations(device, profile)

        # 生成健康摘要
        health_summary = self._generate_summary(alerts, trends, correlations)

        # 优先级建议
        recommendations = self._prioritize_recommendations(alerts, trends)

        return Insights(
            health_summary=health_summary,
            alerts=alerts,
            trends=trends,
            correlations=correlations,
            recommendations_priority=recommendations
        )

    def _generate_alerts(self,
                        device: Optional[DeviceData],
                        profile: Dict[str, Any],
                        risk_factors: List[str]) -> List[HealthAlert]:
        """生成健康告警"""
        alerts = []

        # 基于风险因素生成告警
        for factor in risk_factors:
            severity = "critical" if "危急" in factor else "warning" if "偏" in factor else "info"

            if "睡眠" in factor:
                alerts.append(HealthAlert(
                    alert_type="sleep",
                    severity=severity,
                    message=factor,
                    recommendation="建议调整作息，增加睡前放松"
                ))
            elif "HRV" in factor:
                alerts.append(HealthAlert(
                    alert_type="hrv",
                    severity=severity,
                    message=factor,
                    recommendation="注意休息，避免过度劳累"
                ))
            elif "血糖" in factor:
                alerts.append(HealthAlert(
                    alert_type="glucose",
                    severity=severity,
                    message=factor,
                    recommendation="请注意血糖管理，必要时咨询医生"
                ))
            elif "效能感" in factor:
                alerts.append(HealthAlert(
                    alert_type="efficacy",
                    severity=severity,
                    message=factor,
                    recommendation="从小任务开始，逐步建立信心"
                ))

        # 基于设备数据生成额外告警
        if device:
            if device.sleep and device.sleep.deep_sleep_percent:
                if device.sleep.deep_sleep_percent < 15:
                    alerts.append(HealthAlert(
                        alert_type="sleep",
                        severity="warning",
                        message=f"深度睡眠比例偏低: {device.sleep.deep_sleep_percent}%",
                        recommendation="尝试睡前避免屏幕，保持卧室黑暗凉爽",
                        metric_value=device.sleep.deep_sleep_percent,
                        threshold=15
                    ))

            if device.cgm and device.cgm.time_in_range_percent:
                if device.cgm.time_in_range_percent < 70:
                    alerts.append(HealthAlert(
                        alert_type="glucose",
                        severity="info" if device.cgm.time_in_range_percent >= 60 else "warning",
                        message=f"血糖时间在范围内: {device.cgm.time_in_range_percent}% (目标>70%)",
                        recommendation="配合睡眠和运动改善后观察变化",
                        metric_value=device.cgm.time_in_range_percent,
                        threshold=70
                    ))

        return alerts

    def _generate_trends(self,
                        device: Optional[DeviceData],
                        profile: Dict[str, Any]) -> List[HealthTrend]:
        """生成趋势分析"""
        trends = []

        # 从 profile 的历史数据分析趋势
        # (实际实现需要存储历史数据进行对比)

        if device:
            # 睡眠趋势示例
            if device.sleep and device.sleep.quality_score is not None:
                # 模拟趋势 (实际需要历史数据)
                trends.append(HealthTrend(
                    metric="sleep_quality",
                    direction="stable" if device.sleep.quality_score >= 70 else "declining",
                    change_percent=-10 if device.sleep.quality_score < 70 else 0,
                    interpretation="睡眠质量需要关注" if device.sleep.quality_score < 70 else "睡眠质量稳定",
                    period_days=7
                ))

            # HRV 趋势
            if device.hrv and device.hrv.sdnn is not None:
                direction = "declining" if device.hrv.sdnn < 45 else "stable" if device.hrv.sdnn < 60 else "improving"
                trends.append(HealthTrend(
                    metric="hrv_sdnn",
                    direction=direction,
                    change_percent=0,
                    interpretation=f"HRV {'偏低，需关注恢复' if direction == 'declining' else '正常范围内'}",
                    period_days=7
                ))

        return trends

    def _find_correlations(self,
                          device: Optional[DeviceData],
                          profile: Dict[str, Any]) -> List[str]:
        """发现指标间关联"""
        correlations = []

        if device:
            # 睡眠与血糖关联
            if device.sleep and device.cgm:
                if device.sleep.duration_hours and device.sleep.duration_hours < 6:
                    if device.cgm.time_in_range_percent and device.cgm.time_in_range_percent < 70:
                        correlations.append("睡眠不足可能影响血糖控制，两者存在关联")

            # HRV 与睡眠关联
            if device.hrv and device.sleep:
                if device.hrv.sdnn and device.hrv.sdnn < 45:
                    if device.sleep.quality_score and device.sleep.quality_score < 60:
                        correlations.append("HRV偏低与睡眠质量下降可能相互影响")

        return correlations

    def _generate_summary(self,
                         alerts: List[HealthAlert],
                         trends: List[HealthTrend],
                         correlations: List[str]) -> str:
        """生成健康摘要"""
        critical_count = sum(1 for a in alerts if a.severity == "critical")
        warning_count = sum(1 for a in alerts if a.severity == "warning")
        declining_count = sum(1 for t in trends if t.direction == "declining")

        if critical_count > 0:
            return f"检测到{critical_count}个需要立即关注的问题，请优先处理"
        elif warning_count > 0:
            if correlations:
                return f"发现{warning_count}个健康提醒，{correlations[0]}"
            return f"发现{warning_count}个健康提醒，建议关注并调整"
        elif declining_count > 0:
            return "部分指标呈下降趋势，建议积极干预"
        else:
            return "整体健康状况稳定，继续保持良好习惯"

    def _prioritize_recommendations(self,
                                   alerts: List[HealthAlert],
                                   trends: List[HealthTrend]) -> List[str]:
        """生成优先级建议"""
        recommendations = []

        # 按严重程度排序告警
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        warning_alerts = [a for a in alerts if a.severity == "warning"]

        for alert in critical_alerts[:2]:
            recommendations.append(alert.recommendation)

        for alert in warning_alerts[:2]:
            if alert.recommendation not in recommendations:
                recommendations.append(alert.recommendation)

        # 补充一般性建议
        if not recommendations:
            recommendations.append("保持当前健康习惯")

        return recommendations[:3]


# ============================================================================
# Pipeline 流程定义
# ============================================================================

class PipelineStep(Enum):
    """流程步骤枚举"""
    INPUT_HANDLER = "input_handler"
    PROFILE_MANAGER = "profile_manager"
    RISK_ANALYZER = "risk_analyzer"
    AGENT_ROUTER = "agent_router"
    MULTI_AGENT_COORDINATOR = "multi_agent_coordinator"
    INTERVENTION_PLANNER = "intervention_planner"
    RESPONSE_SYNTHESIZER = "response_synthesizer"
    TASK_GENERATOR = "task_generator"


@dataclass
class PipelineContext:
    """流程上下文 - 在各步骤间传递数据"""
    # 输入
    user_input: Optional[UserInput] = None
    raw_input: Optional[Dict[str, Any]] = None

    # Step 2: Profile
    profile: Optional[Dict[str, Any]] = None
    profile_updated: bool = False

    # Step 3: Risk Analysis
    risk_assessment: Optional[Dict[str, Any]] = None

    # Step 4: Routing
    routing_decision: Optional[RoutingDecision] = None

    # Step 5: Coordination
    agent_results: List[AgentAnalysisResult] = field(default_factory=list)
    coordinated_result: Optional[CoordinatedResult] = None

    # Step 6: Planning
    intervention_plan: Optional[InterventionPlan] = None
    action_plan: Optional[ActionPlan] = None

    # Step 7: Synthesis
    synthesized_response: Optional[SynthesizedResponse] = None

    # Step 8: Output
    daily_tasks: List[DailyTask] = field(default_factory=list)
    daily_briefing: Optional[DailyBriefing] = None
    profile_updates: Optional[ProfileUpdates] = None

    # 元数据
    current_step: Optional[PipelineStep] = None
    completed_steps: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def mark_step_complete(self, step: PipelineStep):
        """标记步骤完成"""
        self.completed_steps.append(step.value)
        self.current_step = step

    def add_error(self, step: PipelineStep, error: str):
        """添加错误"""
        self.errors.append({
            "step": step.value,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        duration_ms = 0
        if self.start_time and self.end_time:
            duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

        return {
            "completed_steps": self.completed_steps,
            "current_step": self.current_step.value if self.current_step else None,
            "errors_count": len(self.errors),
            "errors": self.errors,
            "duration_ms": duration_ms,
            "has_intervention": self.intervention_plan is not None,
            "tasks_generated": len(self.daily_tasks)
        }


@dataclass
class AgentRouteResult:
    """Agent 路由结果"""
    agents: List[Dict[str, Any]]      # [{"agent": "GlucoseAgent", "priority": 1}, ...]
    primary_agent: str
    secondary_agents: List[str]
    reasoning: str                     # 路由决策原因
    confidence: float = 0.8


class AgentRouter:
    """Agent 路由器

    根据用户画像、意图和风险等级，智能选择最合适的 Agent 组合。

    路由优先级规则:
    1. 危机状态 → CrisisAgent (强制)
    2. 风险等级 → 对应专业 Agent
    3. 意图关键词 → 匹配领域 Agent
    4. 用户偏好 → preferences.focus
    5. 设备数据 → 有数据的领域 Agent
    """

    # Agent 定义
    AGENTS = {
        "CrisisAgent": {
            "name": "危机干预",
            "domain": "crisis",
            "keywords": ["自杀", "自残", "不想活", "结束生命", "伤害自己"],
            "risk_trigger": "critical",
            "priority_base": 0
        },
        "SleepAgent": {
            "name": "睡眠专家",
            "domain": "sleep",
            "keywords": ["睡眠", "失眠", "睡不着", "早醒", "多梦", "熬夜", "作息", "起床"],
            "data_fields": ["sleep"],
            "priority_base": 2
        },
        "GlucoseAgent": {
            "name": "血糖管理",
            "domain": "glucose",
            "keywords": ["血糖", "糖尿病", "餐后", "空腹", "胰岛素", "低血糖", "高血糖"],
            "data_fields": ["cgm"],
            "priority_base": 1
        },
        "StressAgent": {
            "name": "压力管理",
            "domain": "stress",
            "keywords": ["压力", "焦虑", "紧张", "烦躁", "心慌", "喘不过气"],
            "data_fields": ["hrv"],
            "priority_base": 2
        },
        "NutritionAgent": {
            "name": "营养指导",
            "domain": "nutrition",
            "keywords": ["饮食", "吃", "营养", "减肥", "体重", "食物", "热量", "蛋白质"],
            "priority_base": 3
        },
        "ExerciseAgent": {
            "name": "运动指导",
            "domain": "exercise",
            "keywords": ["运动", "锻炼", "健身", "跑步", "散步", "活动量", "步数"],
            "data_fields": ["activity"],
            "priority_base": 3
        },
        "MentalHealthAgent": {
            "name": "心理咨询",
            "domain": "mental",
            "keywords": ["情绪", "抑郁", "心情", "难过", "开心", "烦", "累"],
            "priority_base": 2
        },
        "TCMWellnessAgent": {
            "name": "中医养生",
            "domain": "tcm",
            "keywords": ["中医", "体质", "养生", "调理", "穴位", "气血", "湿气"],
            "priority_base": 4
        }
    }

    # 领域关联 (A 领域问题可能需要 B 领域协同)
    DOMAIN_CORRELATIONS = {
        "sleep": ["glucose", "stress", "mental"],      # 睡眠 ↔ 血糖、压力、心理
        "glucose": ["sleep", "nutrition", "exercise"], # 血糖 ↔ 睡眠、营养、运动
        "stress": ["sleep", "mental", "exercise"],     # 压力 ↔ 睡眠、心理、运动
        "nutrition": ["glucose", "exercise"],          # 营养 ↔ 血糖、运动
        "exercise": ["glucose", "stress"],             # 运动 ↔ 血糖、压力
        "mental": ["stress", "sleep"]                  # 心理 ↔ 压力、睡眠
    }

    def route(self,
              profile: Dict[str, Any],
              intent: str,
              risk: Dict[str, Any],
              device_data: Optional[Dict[str, Any]] = None) -> AgentRouteResult:
        """
        执行 Agent 路由

        Args:
            profile: 用户画像
            intent: 用户意图/消息
            risk: 风险评估结果 {"level": "high", "score": 72, "factors": [...]}
            device_data: 设备数据 (可选)

        Returns:
            AgentRouteResult 路由结果
        """
        agents = []
        reasoning_parts = []

        # Step 1: 危机检测 (最高优先级)
        if self._is_crisis(intent, risk):
            agents.append({"agent": "CrisisAgent", "priority": 0, "reason": "危机关键词检测"})
            reasoning_parts.append("检测到危机信号")

        # Step 2: 基于意图关键词匹配
        intent_matches = self._match_by_intent(intent)
        for match in intent_matches:
            if not any(a["agent"] == match["agent"] for a in agents):
                agents.append(match)
                reasoning_parts.append(f"意图匹配: {match['agent']}")

        # Step 3: 基于设备数据
        if device_data:
            data_matches = self._match_by_data(device_data)
            for match in data_matches:
                if not any(a["agent"] == match["agent"] for a in agents):
                    agents.append(match)
                    reasoning_parts.append(f"设备数据: {match['agent']}")

        # Step 4: 基于用户偏好 (focus areas)
        focus_areas = profile.get("preferences", {}).get("focus", [])
        for area in focus_areas:
            focus_match = self._match_by_focus(area)
            if focus_match and not any(a["agent"] == focus_match["agent"] for a in agents):
                focus_match["priority"] += 1  # 偏好匹配优先级略低
                agents.append(focus_match)
                reasoning_parts.append(f"用户关注: {area}")

        # Step 5: 基于风险因素
        risk_factors = risk.get("factors", [])
        for factor in risk_factors:
            risk_match = self._match_by_risk_factor(factor)
            if risk_match and not any(a["agent"] == risk_match["agent"] for a in agents):
                agents.append(risk_match)
                reasoning_parts.append(f"风险因素: {factor[:20]}")

        # Step 6: 添加协同 Agent
        if agents:
            primary_domain = self._get_agent_domain(agents[0]["agent"])
            correlations = self.DOMAIN_CORRELATIONS.get(primary_domain, [])
            for corr_domain in correlations[:1]:  # 最多1个协同
                corr_agent = self._domain_to_agent(corr_domain)
                if corr_agent and not any(a["agent"] == corr_agent for a in agents):
                    agents.append({
                        "agent": corr_agent,
                        "priority": 5,
                        "reason": f"协同领域: {corr_domain}"
                    })

        # Step 7: 默认 Agent (如果没有匹配)
        if not agents:
            agents.append({
                "agent": "MentalHealthAgent",
                "priority": 3,
                "reason": "默认心理支持"
            })
            reasoning_parts.append("默认路由到心理咨询")

        # 按优先级排序
        agents.sort(key=lambda x: x["priority"])

        # 限制数量 (最多2个主要 Agent)
        agents = agents[:2]

        # 构建结果
        primary = agents[0]["agent"]
        secondary = [a["agent"] for a in agents[1:]]

        return AgentRouteResult(
            agents=agents,
            primary_agent=primary,
            secondary_agents=secondary,
            reasoning=" → ".join(reasoning_parts) if reasoning_parts else "默认路由",
            confidence=self._calculate_confidence(agents, intent)
        )

    def _is_crisis(self, intent: str, risk: Dict[str, Any]) -> bool:
        """检测是否为危机状态"""
        if risk.get("level") == "critical":
            return True

        crisis_keywords = self.AGENTS["CrisisAgent"]["keywords"]
        intent_lower = intent.lower()
        return any(kw in intent_lower for kw in crisis_keywords)

    def _match_by_intent(self, intent: str) -> List[Dict[str, Any]]:
        """基于意图关键词匹配"""
        matches = []
        intent_lower = intent.lower()

        for agent_id, agent_info in self.AGENTS.items():
            if agent_id == "CrisisAgent":
                continue  # 危机已单独处理

            keywords = agent_info.get("keywords", [])
            match_count = sum(1 for kw in keywords if kw in intent_lower)

            if match_count > 0:
                matches.append({
                    "agent": agent_id,
                    "priority": agent_info["priority_base"],
                    "match_score": match_count,
                    "reason": f"关键词匹配({match_count})"
                })

        # 按匹配数排序
        matches.sort(key=lambda x: (-x["match_score"], x["priority"]))
        return matches[:2]

    def _match_by_data(self, device_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于设备数据匹配"""
        matches = []

        for agent_id, agent_info in self.AGENTS.items():
            data_fields = agent_info.get("data_fields", [])
            for field in data_fields:
                if device_data.get(field):
                    matches.append({
                        "agent": agent_id,
                        "priority": agent_info["priority_base"],
                        "reason": f"设备数据: {field}"
                    })
                    break

        return matches

    def _match_by_focus(self, focus_area: str) -> Optional[Dict[str, Any]]:
        """基于用户关注领域匹配"""
        focus_mapping = {
            "sleep": "SleepAgent",
            "glucose": "GlucoseAgent",
            "stress": "StressAgent",
            "nutrition": "NutritionAgent",
            "exercise": "ExerciseAgent",
            "mood": "MentalHealthAgent",
            "energy": "StressAgent",
            "weight": "NutritionAgent"
        }

        agent_id = focus_mapping.get(focus_area)
        if agent_id and agent_id in self.AGENTS:
            return {
                "agent": agent_id,
                "priority": self.AGENTS[agent_id]["priority_base"],
                "reason": f"用户关注: {focus_area}"
            }
        return None

    def _match_by_risk_factor(self, factor: str) -> Optional[Dict[str, Any]]:
        """基于风险因素匹配"""
        factor_lower = factor.lower()

        factor_mapping = {
            "睡眠": "SleepAgent",
            "血糖": "GlucoseAgent",
            "hrv": "StressAgent",
            "压力": "StressAgent",
            "情绪": "MentalHealthAgent",
            "体重": "NutritionAgent"
        }

        for keyword, agent_id in factor_mapping.items():
            if keyword in factor_lower:
                return {
                    "agent": agent_id,
                    "priority": self.AGENTS[agent_id]["priority_base"] + 1,
                    "reason": f"风险因素: {keyword}"
                }
        return None

    def _get_agent_domain(self, agent_id: str) -> str:
        """获取 Agent 的领域"""
        return self.AGENTS.get(agent_id, {}).get("domain", "mental")

    def _domain_to_agent(self, domain: str) -> Optional[str]:
        """领域转 Agent ID"""
        for agent_id, info in self.AGENTS.items():
            if info.get("domain") == domain:
                return agent_id
        return None

    def _calculate_confidence(self, agents: List[Dict], intent: str) -> float:
        """计算路由置信度"""
        if not agents:
            return 0.5

        # 基础置信度
        confidence = 0.7

        # 有多个匹配提高置信度
        if len(agents) >= 2:
            confidence += 0.1

        # 关键词匹配数
        total_matches = sum(a.get("match_score", 0) for a in agents)
        if total_matches >= 3:
            confidence += 0.1
        elif total_matches >= 1:
            confidence += 0.05

        return min(confidence, 0.95)


@dataclass
class ConflictResolution:
    """冲突消解结果"""
    conflict_type: str           # contradiction, overlap, priority
    agents_involved: List[str]
    original_values: Dict[str, Any]
    resolved_value: Any
    resolution_method: str       # priority, average, expert_rule, consensus
    confidence: float = 0.8


@dataclass
class IntegratedAnalysis:
    """融合后的分析结果"""
    summary: str
    risk_level: str
    confidence: float
    findings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    conflicts_resolved: List[ConflictResolution]
    agent_weights: Dict[str, float]
    consensus_points: List[str]
    divergence_points: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "conflicts_resolved": [asdict(c) for c in self.conflicts_resolved],
            "agent_weights": self.agent_weights,
            "consensus_points": self.consensus_points,
            "divergence_points": self.divergence_points,
            "metadata": self.metadata
        }


class MultiAgentCoordinator:
    """多 Agent 协调器

    职责:
    1. 并发调用多个 Agent
    2. 冲突检测与消解
    3. 结果加权融合
    4. 生成统一分析报告

    冲突类型:
    - contradiction: 观点矛盾 (如: A说增加运动, B说减少活动)
    - overlap: 建议重叠 (如: 多个Agent都建议改善睡眠)
    - priority: 优先级冲突 (如: 紧急vs长期建议)

    融合策略:
    - priority: 按Agent优先级选择
    - weighted_average: 加权平均
    - expert_rule: 专家规则
    - consensus: 共识优先
    """

    # Agent 权重 (基于专业领域可信度)
    AGENT_WEIGHTS = {
        "CrisisAgent": 1.0,       # 危机处理最高权重
        "GlucoseAgent": 0.9,      # 血糖管理高权重
        "SleepAgent": 0.85,
        "StressAgent": 0.85,
        "NutritionAgent": 0.8,
        "ExerciseAgent": 0.8,
        "MentalHealthAgent": 0.85,
        "TCMWellnessAgent": 0.75
    }

    # 领域优先级 (用于冲突消解)
    DOMAIN_PRIORITY = {
        "crisis": 0,      # 最高优先
        "medical": 1,
        "glucose": 2,
        "sleep": 3,
        "stress": 3,
        "mental": 4,
        "nutrition": 5,
        "exercise": 5,
        "tcm": 6
    }

    # 冲突消解规则
    CONFLICT_RULES = {
        # (domain_a, domain_b): winner
        ("glucose", "nutrition"): "glucose",    # 血糖管理优先于营养
        ("sleep", "exercise"): "sleep",         # 睡眠优先于运动
        ("stress", "exercise"): "stress",       # 压力管理优先于运动
        ("mental", "exercise"): "mental",       # 心理优先于运动
    }

    def coordinate(self, agent_results: List[AgentAnalysisResult]) -> IntegratedAnalysis:
        """
        协调多个 Agent 结果，执行冲突消解和加权融合

        Args:
            agent_results: Agent 分析结果列表

        Returns:
            IntegratedAnalysis 融合后的分析结果
        """
        if not agent_results:
            return self._empty_analysis()

        # Step 1: 分配权重
        agent_weights = self._assign_weights(agent_results)

        # Step 2: 检测冲突
        conflicts = self._detect_conflicts(agent_results)

        # Step 3: 消解冲突
        resolved_conflicts = self._resolve_conflicts(conflicts, agent_results, agent_weights)

        # Step 4: 融合 Findings
        integrated_findings = self._integrate_findings(agent_results, agent_weights, resolved_conflicts)

        # Step 5: 融合 Recommendations
        integrated_recommendations = self._integrate_recommendations(
            agent_results, agent_weights, resolved_conflicts
        )

        # Step 6: 确定综合风险等级
        risk_level = self._determine_risk_level(agent_results, agent_weights)

        # Step 7: 计算综合置信度
        confidence = self._calculate_confidence(agent_results, agent_weights, resolved_conflicts)

        # Step 8: 提取共识点和分歧点
        consensus, divergence = self._extract_consensus_divergence(agent_results)

        # Step 9: 生成摘要
        summary = self._generate_summary(
            agent_results, integrated_findings, risk_level, resolved_conflicts
        )

        return IntegratedAnalysis(
            summary=summary,
            risk_level=risk_level,
            confidence=confidence,
            findings=integrated_findings,
            recommendations=integrated_recommendations,
            conflicts_resolved=resolved_conflicts,
            agent_weights=agent_weights,
            consensus_points=consensus,
            divergence_points=divergence,
            metadata={
                "agents_count": len(agent_results),
                "conflicts_count": len(conflicts),
                "resolved_count": len(resolved_conflicts),
                "timestamp": datetime.now().isoformat()
            }
        )

    def _empty_analysis(self) -> IntegratedAnalysis:
        """返回空分析结果"""
        return IntegratedAnalysis(
            summary="暂无分析数据",
            risk_level="unknown",
            confidence=0.0,
            findings=[],
            recommendations=[],
            conflicts_resolved=[],
            agent_weights={},
            consensus_points=[],
            divergence_points=[]
        )

    def _assign_weights(self, results: List[AgentAnalysisResult]) -> Dict[str, float]:
        """分配 Agent 权重"""
        weights = {}
        for result in results:
            base_weight = self.AGENT_WEIGHTS.get(result.agent, 0.7)
            # 根据置信度调整权重
            adjusted_weight = base_weight * result.confidence
            weights[result.agent] = round(adjusted_weight, 3)
        return weights

    def _detect_conflicts(self, results: List[AgentAnalysisResult]) -> List[Dict[str, Any]]:
        """检测冲突"""
        conflicts = []

        # 比较每对 Agent 的建议
        for i, result_a in enumerate(results):
            for result_b in results[i+1:]:
                # 检测建议冲突
                suggestion_conflicts = self._find_suggestion_conflicts(result_a, result_b)
                conflicts.extend(suggestion_conflicts)

                # 检测风险评估冲突
                risk_conflict = self._find_risk_conflict(result_a, result_b)
                if risk_conflict:
                    conflicts.append(risk_conflict)

        return conflicts

    def _find_suggestion_conflicts(self,
                                   result_a: AgentAnalysisResult,
                                   result_b: AgentAnalysisResult) -> List[Dict[str, Any]]:
        """查找建议冲突"""
        conflicts = []

        # 矛盾关键词对
        contradiction_pairs = [
            (["增加", "多", "加强"], ["减少", "少", "降低"]),
            (["运动", "活动", "锻炼"], ["休息", "静养", "少动"]),
            (["早睡", "提前"], ["晚睡", "推迟"]),
            (["多吃", "补充"], ["少吃", "限制", "避免"])
        ]

        for sug_a in result_a.suggestions:
            for sug_b in result_b.suggestions:
                # 检查是否存在矛盾
                for pos_words, neg_words in contradiction_pairs:
                    a_has_pos = any(w in sug_a for w in pos_words)
                    a_has_neg = any(w in sug_a for w in neg_words)
                    b_has_pos = any(w in sug_b for w in pos_words)
                    b_has_neg = any(w in sug_b for w in neg_words)

                    if (a_has_pos and b_has_neg) or (a_has_neg and b_has_pos):
                        conflicts.append({
                            "type": "contradiction",
                            "agents": [result_a.agent, result_b.agent],
                            "values": {result_a.agent: sug_a, result_b.agent: sug_b},
                            "category": "suggestion"
                        })
                        break

        return conflicts

    def _find_risk_conflict(self,
                           result_a: AgentAnalysisResult,
                           result_b: AgentAnalysisResult) -> Optional[Dict[str, Any]]:
        """查找风险评估冲突"""
        risk_levels = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        level_a = risk_levels.get(result_a.risk_level, 2)
        level_b = risk_levels.get(result_b.risk_level, 2)

        # 风险等级相差2级以上视为冲突
        if abs(level_a - level_b) >= 2:
            return {
                "type": "priority",
                "agents": [result_a.agent, result_b.agent],
                "values": {
                    result_a.agent: result_a.risk_level,
                    result_b.agent: result_b.risk_level
                },
                "category": "risk_level"
            }

        return None

    def _resolve_conflicts(self,
                          conflicts: List[Dict[str, Any]],
                          results: List[AgentAnalysisResult],
                          weights: Dict[str, float]) -> List[ConflictResolution]:
        """消解冲突"""
        resolutions = []

        for conflict in conflicts:
            agents = conflict["agents"]
            values = conflict["values"]

            if conflict["type"] == "contradiction":
                # 矛盾消解: 按权重和领域优先级
                resolution = self._resolve_contradiction(agents, values, weights)

            elif conflict["type"] == "priority":
                # 优先级冲突: 取更高风险
                resolution = self._resolve_priority(agents, values)

            elif conflict["type"] == "overlap":
                # 重叠: 合并去重
                resolution = self._resolve_overlap(agents, values)

            else:
                # 默认: 按权重选择
                resolution = self._resolve_by_weight(agents, values, weights)

            resolutions.append(resolution)

        return resolutions

    def _resolve_contradiction(self,
                               agents: List[str],
                               values: Dict[str, Any],
                               weights: Dict[str, float]) -> ConflictResolution:
        """消解矛盾冲突"""
        # 获取领域
        domains = {}
        for agent in agents:
            for agent_id, info in AgentRouter.AGENTS.items():
                if agent_id == agent:
                    domains[agent] = info.get("domain", "unknown")

        # 检查是否有专家规则
        domain_pair = tuple(sorted([domains.get(a, "") for a in agents]))
        if domain_pair in self.CONFLICT_RULES:
            winner_domain = self.CONFLICT_RULES[domain_pair]
            winner_agent = next(
                (a for a in agents if domains.get(a) == winner_domain),
                agents[0]
            )
            return ConflictResolution(
                conflict_type="contradiction",
                agents_involved=agents,
                original_values=values,
                resolved_value=values[winner_agent],
                resolution_method="expert_rule",
                confidence=0.85
            )

        # 否则按权重选择
        winner = max(agents, key=lambda a: weights.get(a, 0.5))
        return ConflictResolution(
            conflict_type="contradiction",
            agents_involved=agents,
            original_values=values,
            resolved_value=values[winner],
            resolution_method="priority",
            confidence=weights.get(winner, 0.7)
        )

    def _resolve_priority(self,
                         agents: List[str],
                         values: Dict[str, Any]) -> ConflictResolution:
        """消解优先级冲突 (取更高风险)"""
        risk_levels = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        max_risk_agent = max(
            agents,
            key=lambda a: risk_levels.get(values.get(a, "low"), 1)
        )

        return ConflictResolution(
            conflict_type="priority",
            agents_involved=agents,
            original_values=values,
            resolved_value=values[max_risk_agent],
            resolution_method="max_risk",
            confidence=0.9
        )

    def _resolve_overlap(self,
                        agents: List[str],
                        values: Dict[str, Any]) -> ConflictResolution:
        """消解重叠 (合并)"""
        # 合并所有值
        merged = list(set(v for v in values.values() if v))

        return ConflictResolution(
            conflict_type="overlap",
            agents_involved=agents,
            original_values=values,
            resolved_value=merged,
            resolution_method="merge",
            confidence=0.95
        )

    def _resolve_by_weight(self,
                          agents: List[str],
                          values: Dict[str, Any],
                          weights: Dict[str, float]) -> ConflictResolution:
        """按权重消解"""
        winner = max(agents, key=lambda a: weights.get(a, 0.5))

        return ConflictResolution(
            conflict_type="unknown",
            agents_involved=agents,
            original_values=values,
            resolved_value=values[winner],
            resolution_method="weighted",
            confidence=weights.get(winner, 0.7)
        )

    def _integrate_findings(self,
                           results: List[AgentAnalysisResult],
                           weights: Dict[str, float],
                           resolved_conflicts: List[ConflictResolution]) -> List[Dict[str, Any]]:
        """融合 Findings"""
        all_findings = []
        seen = set()

        # 按权重排序
        sorted_results = sorted(results, key=lambda r: weights.get(r.agent, 0.5), reverse=True)

        for result in sorted_results:
            # 从 analysis 中提取 (如果有)
            analysis_text = result.analysis
            if analysis_text and analysis_text not in seen:
                seen.add(analysis_text)
                all_findings.append({
                    "source": result.agent,
                    "finding": analysis_text,
                    "severity": result.risk_level,
                    "weight": weights.get(result.agent, 0.7)
                })

        # 按权重和严重程度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_findings.sort(key=lambda f: (severity_order.get(f["severity"], 2), -f["weight"]))

        return all_findings[:10]  # 最多10条

    def _integrate_recommendations(self,
                                   results: List[AgentAnalysisResult],
                                   weights: Dict[str, float],
                                   resolved_conflicts: List[ConflictResolution]) -> List[Dict[str, Any]]:
        """融合 Recommendations"""
        all_recs = []
        seen_content = set()

        # 收集被冲突消解排除的建议
        excluded = set()
        for conflict in resolved_conflicts:
            if conflict.conflict_type == "contradiction":
                for agent, value in conflict.original_values.items():
                    if value != conflict.resolved_value:
                        excluded.add(value)

        # 按权重排序
        sorted_results = sorted(results, key=lambda r: weights.get(r.agent, 0.5), reverse=True)

        for result in sorted_results:
            for sug in result.suggestions:
                # 跳过被排除的建议
                if sug in excluded:
                    continue

                # 去重
                if sug in seen_content:
                    continue
                seen_content.add(sug)

                all_recs.append({
                    "source": result.agent,
                    "action": sug,
                    "priority": len(all_recs) + 1,
                    "weight": weights.get(result.agent, 0.7)
                })

        return all_recs[:8]  # 最多8条建议

    def _determine_risk_level(self,
                              results: List[AgentAnalysisResult],
                              weights: Dict[str, float]) -> str:
        """确定综合风险等级 (加权)"""
        risk_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        total_weight = 0
        weighted_score = 0

        for result in results:
            w = weights.get(result.agent, 0.7)
            score = risk_scores.get(result.risk_level, 2)
            weighted_score += w * score
            total_weight += w

        if total_weight == 0:
            return "medium"

        avg_score = weighted_score / total_weight

        if avg_score >= 3.5:
            return "critical"
        elif avg_score >= 2.5:
            return "high"
        elif avg_score >= 1.5:
            return "medium"
        else:
            return "low"

    def _calculate_confidence(self,
                              results: List[AgentAnalysisResult],
                              weights: Dict[str, float],
                              resolved_conflicts: List[ConflictResolution]) -> float:
        """计算综合置信度"""
        if not results:
            return 0.0

        # 基础: Agent 置信度加权平均
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.5

        weighted_conf = sum(
            r.confidence * weights.get(r.agent, 0.7)
            for r in results
        ) / total_weight

        # 冲突惩罚
        conflict_penalty = len(resolved_conflicts) * 0.05

        # Agent 数量奖励 (多 Agent 一致性更可信)
        agent_bonus = min(len(results) * 0.03, 0.1)

        final_conf = weighted_conf - conflict_penalty + agent_bonus

        return round(max(0.3, min(0.95, final_conf)), 2)

    def _extract_consensus_divergence(self,
                                      results: List[AgentAnalysisResult]) -> Tuple[List[str], List[str]]:
        """提取共识点和分歧点"""
        consensus = []
        divergence = []

        # 收集所有标签
        all_tags = {}
        for result in results:
            for tag in result.tags:
                if tag not in all_tags:
                    all_tags[tag] = []
                all_tags[tag].append(result.agent)

        # 分析共识和分歧
        for tag, agents in all_tags.items():
            if len(agents) >= 2:
                consensus.append(f"{tag} (多Agent一致)")
            elif len(agents) == 1 and len(results) > 1:
                divergence.append(f"{tag} (仅{agents[0]}关注)")

        return consensus[:5], divergence[:5]

    def _generate_summary(self,
                          results: List[AgentAnalysisResult],
                          findings: List[Dict[str, Any]],
                          risk_level: str,
                          conflicts: List[ConflictResolution]) -> str:
        """生成综合摘要"""
        parts = []

        # Agent 参与情况
        agent_names = [r.agent.replace("Agent", "") for r in results]
        parts.append(f"综合{'/'.join(agent_names)}分析")

        # 风险等级
        risk_desc = {
            "critical": "发现紧急情况需立即关注",
            "high": "存在较高健康风险",
            "medium": "有需要关注的健康问题",
            "low": "整体状况良好"
        }
        parts.append(risk_desc.get(risk_level, ""))

        # 主要发现
        if findings:
            parts.append(f"主要发现: {findings[0]['finding'][:50]}")

        # 冲突处理
        if conflicts:
            parts.append(f"已协调{len(conflicts)}处专业意见分歧")

        return "，".join(parts) + "。"


class PipelineOrchestrator:
    """流程编排器

    清晰实现 9 步处理流程:

    [API / WebSocket / Device]
            │
            ▼
    1. Input Handler
            │
            ▼
    2. Profile Manager ──► 更新 user_master_profile
            │
            ▼
    3. Intent & Risk Analyzer
       ├─ 问题类型分类
       ├─ 行为阶段识别
       └─ 风险分级
            │
            ▼
    4. Agent Router
       ├─ 选择 1–2 个主 Agent
       └─ 可选协同 Agent
            │
            ▼
    5. Multi-Agent Coordinator
       ├─ 并发调用 Agents
       ├─ 冲突检测
       └─ 结果融合
            │
            ▼
    6. Intervention Planner
       ├─ 目标设定
       ├─ 阶段划分
       └─ 行为处方生成
            │
            ▼
    7. Response Synthesizer
       ├─ 对话输出
       ├─ 教练语气适配
       └─ 内容推荐
            │
            ▼
    8. Task Generator + Profile Writer
       ├─ 写回画像
       └─ 生成今日任务
    """

    def __init__(self, master_agent: 'MasterAgent'):
        self.master_agent = master_agent

    def execute(self, input_data: Dict[str, Any]) -> Tuple[MasterAgentResponse, PipelineContext]:
        """执行完整流程

        Args:
            input_data: 输入数据 (符合 master_io_schema.json)

        Returns:
            (MasterAgentResponse, PipelineContext) 元组
        """
        ctx = PipelineContext(raw_input=input_data, start_time=datetime.now())

        try:
            # Step 1: Input Handler
            ctx = self._step_input_handler(ctx)

            # Step 2: Profile Manager
            ctx = self._step_profile_manager(ctx)

            # Step 3: Intent & Risk Analyzer
            ctx = self._step_risk_analyzer(ctx)

            # Step 4: Agent Router
            ctx = self._step_agent_router(ctx)

            # Step 5: Multi-Agent Coordinator
            ctx = self._step_coordinator(ctx)

            # Step 6: Intervention Planner
            ctx = self._step_intervention_planner(ctx)

            # Step 7: Response Synthesizer
            ctx = self._step_response_synthesizer(ctx)

            # Step 8: Task Generator + Profile Writer
            ctx = self._step_task_generator(ctx)

            ctx.end_time = datetime.now()

            # 构建最终响应
            response = self._build_final_response(ctx)
            return response, ctx

        except Exception as e:
            ctx.add_error(ctx.current_step or PipelineStep.INPUT_HANDLER, str(e))
            ctx.end_time = datetime.now()
            # 返回错误响应
            response = self._build_error_response(ctx, str(e))
            return response, ctx

    def _step_input_handler(self, ctx: PipelineContext) -> PipelineContext:
        """Step 1: 输入处理"""
        ctx.current_step = PipelineStep.INPUT_HANDLER

        ctx.user_input = UserInput.from_dict(ctx.raw_input)

        ctx.mark_step_complete(PipelineStep.INPUT_HANDLER)
        return ctx

    def _step_profile_manager(self, ctx: PipelineContext) -> PipelineContext:
        """Step 2: 画像管理"""
        ctx.current_step = PipelineStep.PROFILE_MANAGER

        # 获取或创建 Profile
        ctx.profile = self.master_agent.profile_manager.get_profile(ctx.user_input.user_id)

        # 更新 Profile
        self.master_agent._update_profile_from_input(ctx.user_input, ctx.profile)
        ctx.profile_updated = True

        ctx.mark_step_complete(PipelineStep.PROFILE_MANAGER)
        return ctx

    def _step_risk_analyzer(self, ctx: PipelineContext) -> PipelineContext:
        """Step 3: 意图与风险分析"""
        ctx.current_step = PipelineStep.RISK_ANALYZER

        # 执行风险评估
        risk_result = self.master_agent.risk_assessor.assess(
            ctx.user_input, ctx.profile
        )

        ctx.risk_assessment = {
            "risk_level": risk_result.risk_level.value,
            "risk_score": risk_result.risk_score,
            "risk_factors": risk_result.risk_factors,
            "requires_intervention": risk_result.requires_intervention
        }

        ctx.mark_step_complete(PipelineStep.RISK_ANALYZER)
        return ctx

    def _step_agent_router(self, ctx: PipelineContext) -> PipelineContext:
        """Step 4: Agent 路由"""
        ctx.current_step = PipelineStep.AGENT_ROUTER

        ctx.routing_decision = self.master_agent._route_request(
            ctx.user_input, ctx.profile
        )

        ctx.mark_step_complete(PipelineStep.AGENT_ROUTER)
        return ctx

    def _step_coordinator(self, ctx: PipelineContext) -> PipelineContext:
        """Step 5: 多 Agent 协调"""
        ctx.current_step = PipelineStep.MULTI_AGENT_COORDINATOR

        # 构建设备数据
        recent_data = {}
        if ctx.user_input.device_data:
            if ctx.user_input.device_data.cgm:
                recent_data["cgm"] = asdict(ctx.user_input.device_data.cgm)
            if ctx.user_input.device_data.sleep:
                recent_data["sleep"] = asdict(ctx.user_input.device_data.sleep)
            if ctx.user_input.device_data.hrv:
                recent_data["hrv"] = asdict(ctx.user_input.device_data.hrv)

        # 收集 Agent 分析
        ctx.agent_results = self.master_agent.collect_multi_agent_analysis(
            ctx.profile, recent_data
        )

        # 协调结果
        ctx.coordinated_result = self.master_agent._coordinate_agents(
            ctx.user_input, ctx.profile, ctx.routing_decision
        )

        ctx.mark_step_complete(PipelineStep.MULTI_AGENT_COORDINATOR)
        return ctx

    def _step_intervention_planner(self, ctx: PipelineContext) -> PipelineContext:
        """Step 6: 干预规划"""
        ctx.current_step = PipelineStep.INTERVENTION_PLANNER

        # 生成干预计划
        if ctx.routing_decision.requires_intervention:
            ctx.intervention_plan = self.master_agent._generate_intervention_plan(
                ctx.user_input, ctx.profile, ctx.coordinated_result
            )

            # 生成行动计划
            if ctx.agent_results:
                focus_areas = ctx.profile.get("preferences", {}).get("focus", [])
                goal = f"改善{'和'.join(focus_areas[:2])}" if focus_areas else "健康管理"

                ctx.action_plan = self.master_agent.create_action_plan(
                    goal=goal,
                    analysis_results=ctx.agent_results,
                    profile=ctx.profile
                )

        ctx.mark_step_complete(PipelineStep.INTERVENTION_PLANNER)
        return ctx

    def _step_response_synthesizer(self, ctx: PipelineContext) -> PipelineContext:
        """Step 7: 响应合成"""
        ctx.current_step = PipelineStep.RESPONSE_SYNTHESIZER

        # 生成洞察
        insights = self.master_agent._generate_insights(ctx.user_input, ctx.profile)

        # 合成响应
        ctx.synthesized_response = self.master_agent._synthesize_response(
            ctx.user_input,
            ctx.profile,
            ctx.routing_decision,
            ctx.coordinated_result,
            ctx.intervention_plan,
            insights
        )

        ctx.mark_step_complete(PipelineStep.RESPONSE_SYNTHESIZER)
        return ctx

    def _step_task_generator(self, ctx: PipelineContext) -> PipelineContext:
        """Step 8: 任务生成与画像写回"""
        ctx.current_step = PipelineStep.TASK_GENERATOR

        # 生成任务和追踪
        ctx.daily_tasks, tracking = self.master_agent._generate_tasks_and_tracking(
            ctx.user_input, ctx.profile, ctx.intervention_plan
        )

        # 生成每日简报
        if ctx.action_plan:
            ctx.daily_briefing = DailyBriefing.from_action_plan(
                ctx.action_plan, ctx.profile,
                ctx.profile.get("preferences", {}).get("coaching_style", "gentle")
            )
        else:
            ctx.daily_briefing = self.master_agent.generate_daily_briefing(ctx.user_input.user_id)

        # 写回画像
        ctx.profile_updates = self.master_agent._finalize_and_save_profile(
            ctx.user_input.user_id,
            ctx.profile,
            ctx.synthesized_response,
            ctx.daily_tasks,
            tracking,
            ctx.routing_decision.risk_factors
        )

        ctx.mark_step_complete(PipelineStep.TASK_GENERATOR)
        return ctx

    def _build_final_response(self, ctx: PipelineContext) -> MasterAgentResponse:
        """构建最终响应"""
        insights = self.master_agent._generate_insights(ctx.user_input, ctx.profile)

        return MasterAgentResponse(
            session_id=ctx.user_input.session_id,
            user_id=ctx.user_input.user_id,
            timestamp=datetime.now().isoformat(),
            routing=ctx.routing_decision,
            response=ctx.synthesized_response,
            insights=insights,
            intervention_plan=ctx.intervention_plan,
            daily_tasks=ctx.daily_tasks,
            tracking=Tracking(
                points=ctx.profile.get("tracking_points", []),
                next_check_in=(datetime.now() + timedelta(hours=12)).isoformat()
            ),
            profile_updates=ctx.profile_updates,
            metadata={
                "pipeline_summary": ctx.get_execution_summary(),
                "action_plan_id": ctx.action_plan.plan_id if ctx.action_plan else None,
                "agents_consulted": [r.agent for r in ctx.agent_results]
            }
        )

    def _build_error_response(self, ctx: PipelineContext, error: str) -> MasterAgentResponse:
        """构建错误响应"""
        return MasterAgentResponse(
            session_id=ctx.user_input.session_id if ctx.user_input else "error",
            user_id=ctx.user_input.user_id if ctx.user_input else "unknown",
            timestamp=datetime.now().isoformat(),
            routing=RoutingDecision(
                input_type=InputType.TEXT,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                risk_factors=[],
                primary_agent="mental_health",
                secondary_agents=[],
                requires_intervention=False
            ),
            response=SynthesizedResponse(
                response_text="抱歉，处理您的请求时遇到了问题。请稍后重试。",
                coach_style="empathetic",
                tone="apologetic",
                key_messages=["系统暂时遇到问题"],
                action_items=[],
                follow_up_questions=[]
            ),
            metadata={
                "error": error,
                "pipeline_summary": ctx.get_execution_summary()
            }
        )


# ============================================================================
# Master Agent 主类
# ============================================================================

class MasterAgent:
    """中枢 Master Agent

    行健行为教练多Agent系统的核心控制器，
    串联9步处理流程，协调所有模块。
    """

    # 专家Agent映射
    EXPERT_AGENTS = {
        "mental_health": {"name": "心理咨询师", "priority": 1},
        "nutrition": {"name": "营养师", "priority": 2},
        "sports_rehab": {"name": "运动康复师", "priority": 3},
        "tcm_wellness": {"name": "中医养生师", "priority": 4},
        "sleep": {"name": "睡眠专家", "priority": 1},
        "metabolism": {"name": "代谢专家", "priority": 2},
        "emotion": {"name": "情绪管理师", "priority": 1}
    }

    # 输入类型到主要专家的映射
    INPUT_EXPERT_MAPPING = {
        InputType.TEXT: None,           # 根据内容路由
        InputType.VOICE: None,          # 根据内容路由
        InputType.DEVICE: "metabolism", # 设备数据优先代谢专家
        InputType.FORM: "mental_health", # 表单/问卷优先心理专家
        InputType.ASSESSMENT: "mental_health",
        InputType.TASK_REPORT: "mental_health"
    }

    def __init__(self,
                 config_path: str = "config.yaml",
                 profile_storage: str = "data/profiles"):
        """
        初始化 Master Agent

        Args:
            config_path: 配置文件路径
            profile_storage: 用户画像存储路径
        """
        self.config_path = config_path

        # 初始化子模块
        self.profile_manager = UserMasterProfile(profile_storage)
        self.risk_assessor = RiskPriorityAssessor()
        self.insight_generator = InsightGenerator()
        self.agent_router = AgentRouter()
        self.multi_agent_coordinator = MultiAgentCoordinator()

        # 延迟加载的模块 (避免循环导入)
        self._orchestrator = None
        self._pipeline = None

        print("[Master Agent] 初始化完成 (含 AgentRouter + MultiAgentCoordinator)")

    @property
    def orchestrator(self):
        """延迟加载 Agent 协调器"""
        if self._orchestrator is None:
            try:
                from agents.orchestrator import AgentOrchestrator
                self._orchestrator = AgentOrchestrator(self.config_path)
            except Exception as e:
                print(f"[Master Agent] 协调器加载失败: {e}")
        return self._orchestrator

    @property
    def pipeline(self):
        """延迟加载五层架构流程引擎"""
        if self._pipeline is None:
            try:
                from core.pipeline import OctopusPipeline
                self._pipeline = OctopusPipeline()
            except Exception as e:
                print(f"[Master Agent] Pipeline加载失败: {e}")
        return self._pipeline

    def process(self, user_input: UserInput) -> MasterAgentResponse:
        """
        处理用户请求 - 9步完整流程

        Args:
            user_input: 用户输入请求

        Returns:
            MasterAgentResponse: 完整的响应对象
        """
        start_time = datetime.now()

        # ================================================================
        # Step 1-2: 接收请求
        # ================================================================
        print(f"\n[Master Agent] 收到请求: user={user_input.user_id}, type={user_input.input_type.value}")

        # ================================================================
        # Step 3: 更新 User Master Profile
        # ================================================================
        profile = self._update_profile_from_input(user_input)

        # ================================================================
        # Step 4: Agent Router - 判别问题类型与风险优先级
        # ================================================================
        routing = self._route_request(user_input, profile)
        print(f"[Master Agent] 路由决策: risk={routing.risk_level.value}, "
              f"primary={routing.primary_agent}, secondary={routing.secondary_agents}")

        # ================================================================
        # Step 4.5: 生成数据洞察
        # ================================================================
        insights = self.insight_generator.generate(user_input, profile, routing.risk_factors)

        # ================================================================
        # Step 5-6: 调用专业 Agent + Multi-Agent Coordinator
        # ================================================================
        coordinated_result = self._coordinate_agents(user_input, profile, routing)

        # ================================================================
        # Step 7: Intervention Planner - 生成个性化行为干预路径
        # ================================================================
        intervention_plan = None
        if routing.requires_intervention:
            intervention_plan = self._generate_intervention_plan(user_input, profile, coordinated_result)

        # ================================================================
        # Step 8: Response Synthesizer - 统一教练风格输出
        # ================================================================
        synthesized = self._synthesize_response(
            user_input, profile, routing, coordinated_result, intervention_plan, insights
        )

        # ================================================================
        # Step 9: 写回 Profile + 生成今日任务
        # ================================================================
        daily_tasks, tracking = self._generate_tasks_and_tracking(
            user_input, profile, intervention_plan
        )

        # 更新并保存 Profile
        profile_updates = self._finalize_profile(
            user_input.user_id, profile, synthesized, daily_tasks, tracking, routing.risk_factors
        )

        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # 构建最终响应
        return MasterAgentResponse(
            session_id=user_input.session_id,
            user_id=user_input.user_id,
            timestamp=datetime.now().isoformat(),
            routing=routing,
            response=synthesized,
            insights=insights,
            intervention_plan=intervention_plan,
            daily_tasks=daily_tasks,
            tracking=tracking,
            profile_updates=profile_updates,
            metadata={
                "processing_time_ms": processing_time,
                "agents_consulted": [routing.primary_agent] + routing.secondary_agents,
                "model_version": "xingjian-coach-v1.0"
            }
        )

    # ========================================================================
    # Step 3: Profile 更新
    # ========================================================================

    def _update_profile_from_input(self, user_input: UserInput) -> Dict[str, Any]:
        """从用户输入更新画像 (v2.0 结构)"""
        profile = self.profile_manager.get_profile(user_input.user_id)

        updates = {
            "updated_at": user_input.timestamp,
            "psych": {
                "efficacy_score": user_input.efficacy_score
            }
        }

        # 设备数据更新
        if user_input.device_data:
            device = user_input.device_data

            # 更新今日设备同步时间
            updates["today"] = {
                "device_sync_time": user_input.timestamp
            }

            # 更新生物指标
            biometrics_updates = {}

            # CGM 血糖数据
            if device.cgm:
                biometrics_updates["glucose"] = {
                    "fasting": device.cgm.current_glucose if device.cgm.trend == "stable" else None,
                    "tir": device.cgm.time_in_range_percent,
                    "avg_7d": device.cgm.avg_glucose_24h,
                    "trend": "improving" if device.cgm.trend in ["falling", "falling_fast"] else
                             "worsening" if device.cgm.trend in ["rising", "rising_fast"] else "stable"
                }

            # HRV 数据
            if device.hrv:
                biometrics_updates["hrv"] = {
                    "sdnn": device.hrv.sdnn,
                    "rmssd": device.hrv.rmssd,
                    "trend": "declining" if device.hrv.sdnn and device.hrv.sdnn < 45 else "stable"
                }

            # 睡眠数据
            if device.sleep:
                biometrics_updates["sleep"] = {
                    "avg_duration": device.sleep.duration_hours,
                    "avg_quality": device.sleep.quality_score,
                    "deep_sleep_percent": device.sleep.deep_sleep_percent,
                    "trend": "declining" if device.sleep.quality_score and device.sleep.quality_score < 60 else "stable"
                }

            # 活动数据
            if device.steps > 0:
                biometrics_updates["activity"] = {
                    "avg_steps": device.steps,
                    "active_minutes_weekly": device.active_minutes * 7 if device.active_minutes else 0
                }

            if biometrics_updates:
                updates["biometrics"] = biometrics_updates

        # 表单/评估数据更新
        if user_input.form_data:
            form = user_input.form_data

            # 更新心理状态
            if "psych" in form:
                updates["psych"] = {**updates.get("psych", {}), **form["psych"]}

            # 更新行为状态
            if "behavior" in form:
                updates["behavior"] = form["behavior"]

            # 更新体质
            if "constitution" in form:
                updates["constitution"] = form["constitution"]

            # 更新偏好
            if "preferences" in form:
                updates["preferences"] = form["preferences"]

            # 更新历史
            history = profile.get("history", {})
            history["assessments_count"] = history.get("assessments_count", 0) + 1
            updates["history"] = history

        # 任务完成上报
        if user_input.input_type == InputType.TASK_REPORT and user_input.form_data:
            history = profile.get("history", {})
            history["total_tasks_completed"] = history.get("total_tasks_completed", 0) + 1

            # 更新依从性评分
            if history.get("total_tasks_assigned", 0) > 0:
                adherence = history["total_tasks_completed"] / history["total_tasks_assigned"]
                updates["behavior"] = updates.get("behavior", {})
                updates["behavior"]["adherence_score"] = round(adherence, 2)
                updates["behavior"]["task_completion_rate"] = round(adherence, 2)

            updates["history"] = history

        # 记录会话历史
        session_entry = {
            "session_id": user_input.session_id,
            "timestamp": user_input.timestamp,
            "input_type": user_input.input_type.value,
            "message_preview": user_input.content[:100] if user_input.content else ""
        }

        session_history = profile.get("session_history", [])
        session_history.append(session_entry)
        updates["session_history"] = session_history[-50:]

        # 更新 history.last_session
        updates["history"] = updates.get("history", {})
        updates["history"]["last_session"] = user_input.timestamp
        updates["history"]["total_sessions"] = profile.get("history", {}).get("total_sessions", 0) + 1

        return self.profile_manager.update_profile(user_input.user_id, updates)

    # ========================================================================
    # Step 4: 路由决策
    # ========================================================================

    def _route_request(self, user_input: UserInput, profile: Dict[str, Any]) -> RoutingDecision:
        """路由请求到合适的专家"""

        # 评估风险
        risk_level, risk_score, risk_factors = self.risk_assessor.assess(user_input, profile)

        # 获取用户偏好
        preferences = profile.get("preferences", {})
        focus_areas = preferences.get("focus", [])

        # 确定主要专家
        mapped_agent = self.INPUT_EXPERT_MAPPING.get(user_input.input_type)
        if mapped_agent:
            primary_agent = mapped_agent
        else:
            # 基于消息内容路由
            primary_agent = self._route_by_content(user_input.content, profile)

        # 基于用户关注领域调整路由
        focus_expert_mapping = {
            "sleep": "mental_health",
            "glucose": "metabolism",
            "weight": "nutrition",
            "stress": "mental_health",
            "exercise": "sports_rehab",
            "nutrition": "nutrition",
            "mood": "mental_health",
            "energy": "tcm_wellness"
        }

        # 如果消息中包含用户关注的领域，优先路由到相关专家
        for focus in focus_areas:
            if focus in user_input.content.lower():
                primary_agent = focus_expert_mapping.get(focus, primary_agent)
                break

        # 设备数据中有血糖数据时，考虑代谢专家
        if user_input.device_data and user_input.device_data.cgm:
            if "血糖" in user_input.content or user_input.input_type == InputType.DEVICE:
                primary_agent = "metabolism"
            # 如果用户关注 glucose，强化代谢专家路由
            if "glucose" in focus_areas:
                primary_agent = "metabolism"

        # 紧急情况强制路由到心理专家
        if risk_level == RiskLevel.CRITICAL:
            primary_agent = "mental_health"

        # 确定辅助专家
        secondary_agents = self._determine_secondary_agents(
            primary_agent, user_input.content, profile
        )

        # 是否需要干预计划
        requires_intervention = (
            risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH] or
            user_input.input_type == InputType.ASSESSMENT or
            user_input.device_data is not None  # 有设备数据时生成干预计划
        )

        return RoutingDecision(
            input_type=user_input.input_type,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            requires_intervention=requires_intervention,
            routing_confidence=0.8 if risk_factors else 0.9,
            reasoning=f"风险等级: {risk_level.value}, 主要专家: {primary_agent}"
        )

    def _route_by_content(self, message: str, profile: Dict[str, Any]) -> str:
        """基于消息内容路由"""
        message_lower = message.lower()

        # 关键词匹配
        keyword_mapping = {
            "mental_health": ["焦虑", "抑郁", "压力", "情绪", "心理", "睡不着", "失眠", "紧张", "担心"],
            "nutrition": ["饮食", "吃", "营养", "减肥", "体重", "食物", "消化"],
            "metabolism": ["血糖", "糖尿病", "代谢", "胰岛素", "空腹", "餐后"],
            "sports_rehab": ["运动", "锻炼", "疼痛", "受伤", "肌肉", "关节", "康复"],
            "tcm_wellness": ["中医", "体质", "养生", "穴位", "调理", "气血"]
        }

        scores = {agent: 0 for agent in keyword_mapping}

        for agent, keywords in keyword_mapping.items():
            for keyword in keywords:
                if keyword in message_lower:
                    scores[agent] += 1

        # 返回得分最高的专家，默认心理咨询师
        max_agent = max(scores, key=scores.get)
        return max_agent if scores[max_agent] > 0 else "mental_health"

    def _determine_secondary_agents(self,
                                    primary: str,
                                    message: str,
                                    profile: Dict[str, Any]) -> List[str]:
        """确定辅助专家"""
        secondary = []

        # 跨领域触发
        cross_domain_triggers = {
            ("mental_health", "nutrition"): ["情绪化进食", "压力进食", "暴食"],
            ("mental_health", "sports_rehab"): ["运动焦虑", "运动恐惧"],
            ("nutrition", "tcm_wellness"): ["食疗", "药膳", "体质调理"],
            ("sports_rehab", "tcm_wellness"): ["穴位按摩", "运动恢复"]
        }

        message_lower = message.lower()

        for (agent1, agent2), triggers in cross_domain_triggers.items():
            for trigger in triggers:
                if trigger in message_lower:
                    if primary == agent1 and agent2 not in secondary:
                        secondary.append(agent2)
                    elif primary == agent2 and agent1 not in secondary:
                        secondary.append(agent1)

        # 基于 Profile 中的风险因素添加 (v2.0: risk_flags 在根级别)
        risk_flags = profile.get("risk_flags", [])
        for flag in risk_flags:
            flag_type = flag.get("flag", "")
            if "睡眠" in flag_type and "mental_health" not in secondary and primary != "mental_health":
                secondary.append("mental_health")
            if "营养" in flag_type and "nutrition" not in secondary and primary != "nutrition":
                secondary.append("nutrition")

        # 最多2个辅助专家
        return secondary[:2]

    # ========================================================================
    # Step 5-6: Agent 协调
    # ========================================================================

    def _coordinate_agents(self,
                          user_input: UserInput,
                          profile: Dict[str, Any],
                          routing: RoutingDecision) -> CoordinatedResult:
        """协调专家 Agent"""

        primary_response = None
        supplementary_responses = []

        # 使用 orchestrator 处理 (如果可用)
        if self.orchestrator:
            try:
                result = self.orchestrator.process_query(user_input.message)
                primary_response = AgentResponse(
                    agent_id=result.primary_expert_id,
                    agent_name=result.primary_expert,
                    response_text=result.final_response,
                    confidence=result.routing_confidence,
                    suggestions=[],
                    warnings=[],
                    recommended_actions=[]
                )

                # 添加咨询过的专家响应
                for expert_name in result.consulted_experts:
                    supplementary_responses.append(AgentResponse(
                        agent_id=expert_name.lower().replace(" ", "_"),
                        agent_name=expert_name,
                        response_text="(补充意见已整合)",
                        confidence=0.7,
                        suggestions=[],
                        warnings=[],
                        recommended_actions=[]
                    ))
            except Exception as e:
                print(f"[Master Agent] Orchestrator 调用失败: {e}")

        # 降级: 构建默认响应
        if primary_response is None:
            primary_response = self._build_default_response(routing, profile)

        # 构建统一上下文
        unified_context = {
            "user_id": user_input.user_id,
            "session_id": user_input.session_id,
            "risk_level": routing.risk_level.value,
            "primary_agent": routing.primary_agent,
            "profile_summary": self._summarize_profile(profile),
            "input_type": routing.input_type.value
        }

        return CoordinatedResult(
            primary_response=primary_response,
            supplementary_responses=supplementary_responses,
            unified_context=unified_context,
            consensus_points=[],
            conflict_resolutions=[]
        )

    def _build_default_response(self, routing: RoutingDecision, profile: Dict[str, Any]) -> AgentResponse:
        """构建默认响应 (降级方案)"""
        agent_info = self.EXPERT_AGENTS.get(routing.primary_agent, {"name": "行健行为教练"})

        # 基于风险等级构建响应
        if routing.risk_level == RiskLevel.CRITICAL:
            response_text = (
                "我注意到您现在可能正在经历一些困难。您的感受是真实的，值得被关注。"
                "如果您有伤害自己的想法，请立即拨打心理援助热线：400-161-9995 或 北京 010-82951332。"
                "我在这里陪伴您，请告诉我更多您的感受。"
            )
        elif routing.risk_level == RiskLevel.HIGH:
            response_text = (
                f"您好，我是{agent_info['name']}。根据您的情况，我建议我们一起来关注一下您目前的状态。"
                "请放心，我们会一步一步来，不会给您太大压力。"
            )
        else:
            response_text = (
                f"您好，我是{agent_info['name']}。很高兴为您服务。"
                "请告诉我您想聊些什么，或者有什么我可以帮助您的。"
            )

        return AgentResponse(
            agent_id=routing.primary_agent,
            agent_name=agent_info["name"],
            response_text=response_text,
            confidence=0.6,
            suggestions=[],
            warnings=routing.risk_factors,
            recommended_actions=[]
        )

    def _summarize_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """生成 Profile 摘要 (v2.0 结构)"""
        return {
            "efficacy_score": profile.get("psych", {}).get("efficacy_score", 50),
            "behavior_stage": profile.get("behavior", {}).get("stage", "unknown"),
            "spi_coefficient": profile.get("behavior", {}).get("spi_coefficient", 0.5),
            "risk_flags_count": len(profile.get("risk_flags", [])),
            "total_sessions": profile.get("history", {}).get("total_sessions", 0),
            "task_completion_rate": profile.get("behavior", {}).get("task_completion_rate", 0)
        }

    # ========================================================================
    # Agent Task 调度系统
    # ========================================================================

    def create_agent_task(self,
                          agent_type: AgentType,
                          question: str,
                          profile: Dict[str, Any],
                          recent_data: Optional[Dict[str, Any]] = None,
                          user_message: Optional[str] = None,
                          priority: str = "normal") -> AgentTask:
        """创建 Agent 任务

        Args:
            agent_type: 目标 Agent 类型
            question: 发送给 Agent 的问题/指令
            profile: 用户画像
            recent_data: 近期相关数据
            user_message: 用户原始消息
            priority: 任务优先级

        Returns:
            AgentTask 对象
        """
        # 提取精简版 Profile 供 Agent 使用
        profile_summary = {
            "user_id": profile.get("user_id"),
            "age": profile.get("basic", {}).get("age"),
            "sex": profile.get("basic", {}).get("sex"),
            "diabetes": profile.get("medical", {}).get("diabetes"),
            "behavior_stage": profile.get("behavior", {}).get("stage"),
            "spi_coefficient": profile.get("behavior", {}).get("spi_coefficient"),
            "stress_level": profile.get("psych", {}).get("stress_level"),
            "motivation": profile.get("psych", {}).get("motivation"),
            "efficacy_score": profile.get("psych", {}).get("efficacy_score"),
            "focus_areas": profile.get("preferences", {}).get("focus", []),
            "coaching_style": profile.get("preferences", {}).get("coaching_style"),
            "active_risk_flags": [
                f.get("flag") for f in profile.get("risk_flags", [])
                if not f.get("resolved", False)
            ]
        }

        # 构建上下文
        context = {
            "profile": profile_summary,
            "recent_data": recent_data or {},
            "user_message": user_message or ""
        }

        # 默认约束
        constraints = {
            "max_response_length": 500,
            "response_style": "concise",
            "timeout_ms": 30000
        }

        return AgentTask(
            task_id=f"T{uuid.uuid4().hex[:8].upper()}",
            agent_type=agent_type,
            question=question,
            priority=priority,
            context=context,
            constraints=constraints
        )

    def execute_agent_task(self, task: AgentTask) -> AgentTaskResponse:
        """执行 Agent 任务

        Args:
            task: AgentTask 对象

        Returns:
            AgentTaskResponse 对象
        """
        start_time = datetime.now()
        print(f"[Master Agent] 执行任务 {task.task_id} -> {task.agent_type.value}")

        try:
            # 映射 AgentType 到内部专家 ID
            agent_mapping = {
                AgentType.SLEEP: "mental_health",
                AgentType.GLUCOSE: "metabolism",
                AgentType.STRESS: "mental_health",
                AgentType.NUTRITION: "nutrition",
                AgentType.EXERCISE: "sports_rehab",
                AgentType.MENTAL_HEALTH: "mental_health",
                AgentType.TCM_WELLNESS: "tcm_wellness",
                AgentType.CRISIS: "mental_health"
            }

            internal_agent_id = agent_mapping.get(task.agent_type, "mental_health")

            # 尝试使用 orchestrator
            if self.orchestrator:
                try:
                    result = self.orchestrator.process_query(task.question)

                    # 构建响应
                    response = AgentTaskResponse(
                        task_id=task.task_id,
                        agent_type=task.agent_type,
                        status=TaskStatus.COMPLETED,
                        analysis=AgentTaskAnalysis(
                            summary=result.final_response[:200] if result.final_response else "",
                            findings=[],
                            correlations=[]
                        ),
                        recommendations=[],
                        response_text=result.final_response,
                        coach_notes=f"由 {result.primary_expert} 处理",
                        follow_up=AgentTaskFollowUp(),
                        metadata={
                            "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                            "model_used": "orchestrator",
                            "confidence_score": result.routing_confidence,
                            "completed_at": datetime.now().isoformat()
                        }
                    )
                    return response

                except Exception as e:
                    print(f"[Master Agent] Orchestrator 调用失败: {e}")

            # 降级方案: 根据任务类型构建默认响应
            response = self._build_default_task_response(task, start_time)
            return response

        except Exception as e:
            print(f"[Master Agent] 任务执行失败: {e}")
            return AgentTaskResponse(
                task_id=task.task_id,
                agent_type=task.agent_type,
                status=TaskStatus.FAILED,
                response_text="抱歉，处理您的请求时遇到了问题。",
                metadata={
                    "error": str(e),
                    "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "completed_at": datetime.now().isoformat()
                }
            )

    def _build_default_task_response(self, task: AgentTask, start_time: datetime) -> AgentTaskResponse:
        """构建默认任务响应 (当 orchestrator 不可用时)"""

        profile = task.context.get("profile", {})
        recent_data = task.context.get("recent_data", {})
        user_message = task.context.get("user_message", "")

        # 根据 Agent 类型构建分析和建议
        analysis, recommendations, response_text = self._generate_task_analysis(
            task.agent_type, profile, recent_data, task.question
        )

        return AgentTaskResponse(
            task_id=task.task_id,
            agent_type=task.agent_type,
            status=TaskStatus.COMPLETED,
            analysis=analysis,
            recommendations=recommendations,
            response_text=response_text,
            coach_notes=f"基于规则引擎生成 ({task.agent_type.value})",
            follow_up=AgentTaskFollowUp(
                suggested_questions=["您今天感觉怎么样？", "还有其他想聊的吗？"],
                monitoring_points=["完成情况", "主观感受"],
                escalation_needed=False
            ),
            metadata={
                "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "model_used": "rule_engine",
                "confidence_score": 0.7,
                "completed_at": datetime.now().isoformat()
            }
        )

    def _generate_task_analysis(self,
                                agent_type: AgentType,
                                profile: Dict[str, Any],
                                recent_data: Dict[str, Any],
                                question: str) -> Tuple[AgentTaskAnalysis, List[AgentTaskRecommendation], str]:
        """根据 Agent 类型生成分析和建议"""

        findings = []
        correlations = []
        recommendations = []
        summary = ""
        response_text = ""

        # 睡眠 Agent
        if agent_type == AgentType.SLEEP:
            sleep_data = recent_data.get("sleep", {})
            cgm_data = recent_data.get("cgm", {})

            hours = sleep_data.get("last_night_hours", 0)
            quality = sleep_data.get("quality_score", 0)
            deep_pct = sleep_data.get("deep_sleep_percent", 0)

            if hours < 6:
                findings.append(AgentTaskFinding(
                    category="sleep_duration",
                    observation=f"睡眠时长{hours}小时，低于建议的7小时",
                    severity="warning",
                    confidence=0.95
                ))

            if quality < 60:
                findings.append(AgentTaskFinding(
                    category="sleep_quality",
                    observation=f"睡眠质量评分{quality}，低于良好标准60分",
                    severity="warning",
                    confidence=0.9
                ))

            if deep_pct < 15:
                findings.append(AgentTaskFinding(
                    category="deep_sleep",
                    observation=f"深度睡眠比例{deep_pct}%，低于正常范围20-25%",
                    severity="warning",
                    confidence=0.85
                ))

            # 睡眠与血糖关联
            tir = cgm_data.get("tir_percent", 0)
            if hours < 6 and tir < 70:
                correlations.append(AgentTaskCorrelation(
                    factor_a="睡眠不足",
                    factor_b="血糖控制",
                    relationship="睡眠不足导致胰岛素敏感性下降，影响血糖控制",
                    strength="strong"
                ))

            summary = f"睡眠时长{hours}小时，质量评分{quality}，深度睡眠{deep_pct}%"
            response_text = "根据您的睡眠数据，我建议从改善睡眠习惯入手。今晚试试睡前呼吸练习？"

            recommendations.append(AgentTaskRecommendation(
                type="behavioral",
                action="睡前进行4-7-8呼吸练习",
                rationale="降低交感神经活性，改善入睡质量",
                priority=1,
                difficulty=1,
                duration_minutes=5,
                timing="22:30",
                resources={"knowledge_link": "/knowledge/sleep/breathing-478"}
            ))

        # 血糖 Agent
        elif agent_type == AgentType.GLUCOSE:
            cgm = recent_data.get("cgm", {})
            glucose = cgm.get("current_glucose", 0)
            tir = cgm.get("tir_percent", 0)
            trend = cgm.get("trend", "stable")

            if glucose > 180:
                findings.append(AgentTaskFinding(
                    category="glucose_high",
                    observation=f"当前血糖{glucose}mg/dL，高于目标180mg/dL",
                    severity="warning",
                    confidence=0.95
                ))

            if tir < 70:
                findings.append(AgentTaskFinding(
                    category="tir_low",
                    observation=f"TIR {tir}%，低于目标70%",
                    severity="warning",
                    confidence=0.9
                ))

            summary = f"当前血糖{glucose}mg/dL，TIR {tir}%，趋势{trend}"
            response_text = "我注意到您的血糖有些波动，让我们一起关注一下饮食和活动的调整。"

            recommendations.append(AgentTaskRecommendation(
                type="nutritional",
                action="餐后15分钟进行10分钟轻度活动",
                rationale="帮助降低餐后血糖峰值",
                priority=1,
                difficulty=1,
                duration_minutes=10,
                timing="餐后"
            ))

        # 压力 Agent
        elif agent_type == AgentType.STRESS:
            hrv = recent_data.get("hrv", {})
            sdnn = hrv.get("sdnn", 0)
            stress_idx = hrv.get("stress_index", 0)

            if sdnn < 50:
                findings.append(AgentTaskFinding(
                    category="hrv_low",
                    observation=f"HRV SDNN {sdnn}ms，低于正常范围50-100ms",
                    severity="warning",
                    confidence=0.85
                ))

            if stress_idx > 60:
                findings.append(AgentTaskFinding(
                    category="stress_high",
                    observation=f"压力指数{stress_idx}，处于较高水平",
                    severity="warning",
                    confidence=0.9
                ))

            summary = f"HRV SDNN {sdnn}ms，压力指数{stress_idx}"
            response_text = "从数据来看，您的压力水平偏高。让我们试试一些放松技巧？"

            recommendations.append(AgentTaskRecommendation(
                type="psychological",
                action="进行5分钟正念呼吸练习",
                rationale="激活副交感神经，降低压力反应",
                priority=1,
                difficulty=1,
                duration_minutes=5,
                timing="任意",
                resources={"video_link": "/videos/mindful-breathing-5min"}
            ))

        # 默认处理
        else:
            summary = "已收到您的问题"
            response_text = "感谢您的分享，让我来为您提供一些建议。"

            recommendations.append(AgentTaskRecommendation(
                type="lifestyle",
                action="今天完成一个小目标",
                rationale="建立正向反馈循环",
                priority=2,
                difficulty=1,
                duration_minutes=10
            ))

        analysis = AgentTaskAnalysis(
            summary=summary,
            findings=findings,
            correlations=correlations
        )

        return analysis, recommendations, response_text

    def process_agent_task_json(self, task_json: Dict[str, Any]) -> Dict[str, Any]:
        """处理 JSON 格式的 Agent 任务请求

        Args:
            task_json: 符合 agent_task_schema.json 的任务请求

        Returns:
            符合 agent_task_schema.json 的任务响应
        """
        task = AgentTask.from_dict(task_json)
        response = self.execute_agent_task(task)
        return response.to_dict()

    def get_quick_analysis(self,
                           agent_type: AgentType,
                           profile: Dict[str, Any],
                           recent_data: Dict[str, Any]) -> AgentAnalysisResult:
        """获取快速分析结果 (简化格式)

        Args:
            agent_type: Agent 类型
            profile: 用户画像
            recent_data: 近期数据

        Returns:
            AgentAnalysisResult 简化分析结果
        """
        # 创建并执行任务
        task = self.create_agent_task(
            agent_type=agent_type,
            question=f"分析用户{agent_type.value.replace('Agent', '')}相关状况",
            profile=profile,
            recent_data=recent_data,
            priority="normal"
        )
        response = self.execute_agent_task(task)

        # 转换为简化格式
        return AgentAnalysisResult.from_task_response(response)

    def collect_multi_agent_analysis(self,
                                     profile: Dict[str, Any],
                                     recent_data: Dict[str, Any],
                                     agent_types: Optional[List[AgentType]] = None) -> List[AgentAnalysisResult]:
        """收集多个 Agent 的分析结果

        Args:
            profile: 用户画像
            recent_data: 近期数据
            agent_types: 要咨询的 Agent 类型列表 (默认根据数据自动选择)

        Returns:
            AgentAnalysisResult 列表
        """
        results = []

        # 自动选择 Agent (基于可用数据)
        if agent_types is None:
            agent_types = []
            if recent_data.get("sleep"):
                agent_types.append(AgentType.SLEEP)
            if recent_data.get("cgm"):
                agent_types.append(AgentType.GLUCOSE)
            if recent_data.get("hrv"):
                agent_types.append(AgentType.STRESS)
            if not agent_types:
                agent_types = [AgentType.MENTAL_HEALTH]

        # 收集各 Agent 分析
        for agent_type in agent_types:
            try:
                result = self.get_quick_analysis(agent_type, profile, recent_data)
                results.append(result)
            except Exception as e:
                print(f"[Master Agent] {agent_type.value} 分析失败: {e}")

        return results

    def aggregate_analysis_results(self,
                                   results: List[AgentAnalysisResult]) -> Dict[str, Any]:
        """聚合多个 Agent 分析结果

        Args:
            results: AgentAnalysisResult 列表

        Returns:
            聚合后的分析摘要
        """
        if not results:
            return {"status": "no_results", "summary": "暂无分析结果"}

        # 收集所有建议和标签
        all_suggestions = []
        all_tags = set()
        analyses = []

        # 确定最高风险等级
        risk_priority = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        max_risk = "low"
        max_risk_priority = 1

        for result in results:
            analyses.append({
                "agent": result.agent,
                "summary": result.analysis
            })
            all_suggestions.extend(result.suggestions)
            all_tags.update(result.tags)

            current_priority = risk_priority.get(result.risk_level, 1)
            if current_priority > max_risk_priority:
                max_risk_priority = current_priority
                max_risk = result.risk_level

        # 去重建议 (保持顺序)
        seen = set()
        unique_suggestions = []
        for s in all_suggestions:
            if s not in seen:
                seen.add(s)
                unique_suggestions.append(s)

        return {
            "status": "completed",
            "agents_consulted": [r.agent for r in results],
            "overall_risk_level": max_risk,
            "analyses": analyses,
            "combined_suggestions": unique_suggestions[:10],  # 最多10条
            "tags": list(all_tags),
            "timestamp": datetime.now().isoformat()
        }

    def parse_agent_analysis_json(self, analysis_json: Dict[str, Any]) -> AgentAnalysisResult:
        """解析 JSON 格式的简化分析结果

        Args:
            analysis_json: 简化格式的分析 JSON

        Returns:
            AgentAnalysisResult 对象
        """
        return AgentAnalysisResult.from_dict(analysis_json)

    # ========================================================================
    # Action Plan 管理
    # ========================================================================

    def create_action_plan(self,
                           goal: str,
                           analysis_results: List[AgentAnalysisResult],
                           profile: Dict[str, Any],
                           phase: str = "week_1") -> ActionPlan:
        """基于分析结果创建行动计划

        Args:
            goal: 干预目标
            analysis_results: Agent 分析结果列表
            profile: 用户画像
            phase: 计划阶段

        Returns:
            ActionPlan 对象
        """
        actions = []
        tags = set()

        # 从分析结果中提取建议并转换为行动项
        for result in analysis_results:
            tags.update(result.tags)

            for i, suggestion in enumerate(result.suggestions[:3]):  # 每个 Agent 最多3条
                # 判断行动类型
                action_type = self._infer_action_type(suggestion)

                actions.append(PlanAction(
                    type=action_type,
                    content=suggestion,
                    priority=1 if i == 0 else 2,  # 第一条优先级最高
                    frequency="daily"
                ))

        # 根据用户行为阶段调整行动数量
        behavior_stage = profile.get("behavior", {}).get("stage", "resistance")
        max_actions = self._get_max_actions_for_stage(behavior_stage)
        actions = actions[:max_actions]

        # 添加默认监测行动
        if not any(a.type == ActionType.MONITOR for a in actions):
            actions.append(PlanAction(
                type=ActionType.MONITOR,
                content="记录今日完成情况和主观感受",
                priority=3,
                frequency="daily"
            ))

        # 确定评估指标
        evaluation = PlanEvaluation(
            metrics=list(tags)[:5],  # 最多5个指标
            targets={},
            checkpoints=["week_1_end", "week_2_end"]
        )

        return ActionPlan(
            goal=goal,
            phase=phase,
            actions=actions,
            evaluation=evaluation,
            user_id=profile.get("user_id"),
            tags=list(tags),
            notes=f"基于 {len(analysis_results)} 个Agent分析结果生成"
        )

    def _infer_action_type(self, suggestion: str) -> ActionType:
        """推断建议的行动类型"""
        suggestion_lower = suggestion.lower()

        type_keywords = {
            ActionType.MONITOR: ["监测", "记录", "查看", "追踪", "观察", "cgm", "测量"],
            ActionType.EDUCATION: ["学习", "了解", "观看", "阅读", "视频", "知识"],
            ActionType.EXERCISE: ["运动", "锻炼", "步行", "散步", "跑步", "健身"],
            ActionType.NUTRITION: ["饮食", "进食", "吃", "营养", "食物", "餐"],
            ActionType.RELAXATION: ["放松", "呼吸", "冥想", "正念", "休息"],
            ActionType.SOCIAL: ["社交", "朋友", "家人", "陪伴", "沟通"],
            ActionType.MEDICAL: ["就医", "复诊", "检查", "药物", "医生"]
        }

        for action_type, keywords in type_keywords.items():
            if any(kw in suggestion_lower for kw in keywords):
                return action_type

        return ActionType.BEHAVIOR  # 默认为行为改变

    def _get_max_actions_for_stage(self, stage: str) -> int:
        """根据行为阶段确定最大行动数"""
        stage_limits = {
            "resistance": 2,      # 完全对抗: 最少
            "ambivalence": 3,     # 抗拒与反思
            "compromise": 4,      # 妥协与接受
            "adaptation": 5,      # 顺应与调整
            "integration": 6      # 全面臣服: 最多
        }
        return stage_limits.get(stage, 3)

    def generate_phased_plan(self,
                             goal: str,
                             profile: Dict[str, Any],
                             recent_data: Dict[str, Any],
                             total_weeks: int = 4) -> List[ActionPlan]:
        """生成多阶段行动计划

        Args:
            goal: 干预目标
            profile: 用户画像
            recent_data: 近期数据
            total_weeks: 总周数

        Returns:
            ActionPlan 列表 (每周一个)
        """
        plans = []

        # 获取分析结果
        analysis_results = self.collect_multi_agent_analysis(profile, recent_data)

        # 根据四阶段养成方案生成计划
        # 启动期(1-2周) -> 适应期(3-8周) -> 稳定期(2-4月) -> 内化期(4月+)

        for week in range(1, total_weeks + 1):
            phase = f"week_{week}"

            # 确定当前养成阶段
            if week <= 2:
                cultivation_phase = "startup"      # 启动期
                focus = "建立打卡习惯"
            elif week <= 4:
                cultivation_phase = "adaptation"   # 适应期
                focus = "巩固行为、应对障碍"
            else:
                cultivation_phase = "stability"    # 稳定期
                focus = "减少外部依赖"

            # 创建该周计划
            plan = self.create_action_plan(
                goal=f"{goal} - {focus}",
                analysis_results=analysis_results,
                profile=profile,
                phase=phase
            )

            # 根据阶段调整行动难度
            self._adjust_plan_for_phase(plan, cultivation_phase, week)

            plans.append(plan)

        return plans

    def _adjust_plan_for_phase(self, plan: ActionPlan, cultivation_phase: str, week: int):
        """根据养成阶段调整计划"""
        if cultivation_phase == "startup":
            # 启动期: 降低难度，增加监测
            for action in plan.actions:
                action.priority = min(action.priority, 2)
            # 确保有教育类行动
            if not any(a.type == ActionType.EDUCATION for a in plan.actions):
                plan.actions.append(PlanAction(
                    type=ActionType.EDUCATION,
                    content="了解今日任务的意义和好处",
                    priority=3
                ))

        elif cultivation_phase == "adaptation":
            # 适应期: 逐步增加挑战
            if week > 2:
                # 可以增加行动难度或数量
                pass

        elif cultivation_phase == "stability":
            # 稳定期: 减少提醒，增加自主性
            # 移除部分监测行动
            plan.actions = [a for a in plan.actions
                          if a.type != ActionType.MONITOR or a.priority <= 2]

    def parse_action_plan_json(self, plan_json: Dict[str, Any]) -> ActionPlan:
        """解析 JSON 格式的行动计划

        Args:
            plan_json: 行动计划 JSON

        Returns:
            ActionPlan 对象
        """
        return ActionPlan.from_dict(plan_json)

    def update_action_plan_progress(self,
                                    plan: ActionPlan,
                                    completed_indices: List[int]) -> ActionPlan:
        """更新行动计划进度

        Args:
            plan: ActionPlan 对象
            completed_indices: 已完成行动项的索引列表

        Returns:
            更新后的 ActionPlan
        """
        for idx in completed_indices:
            plan.mark_action_completed(idx)

        # 检查是否全部完成
        if plan.progress_percent() >= 100:
            plan.status = "completed"

        return plan

    # ========================================================================
    # Daily Briefing 每日简报
    # ========================================================================

    def generate_daily_briefing(self,
                                user_id: str,
                                plan: Optional[ActionPlan] = None) -> DailyBriefing:
        """生成每日简报

        Args:
            user_id: 用户ID
            plan: 当前行动计划 (可选，如无则基于 Profile 生成)

        Returns:
            DailyBriefing 对象
        """
        profile = self.profile_manager.get_profile(user_id)

        # 确定教练风格
        coach_style = profile.get("preferences", {}).get("coaching_style", "gentle")

        if plan:
            # 从 ActionPlan 生成
            return DailyBriefing.from_action_plan(plan, profile, coach_style)

        # 无计划时，基于 Profile 和今日任务生成
        today_tasks = profile.get("today", {}).get("tasks", [])
        task_texts = [t.get("title", "") for t in today_tasks if t.get("status") == "pending"]

        if not task_texts:
            # 生成默认任务
            task_texts = self._generate_default_daily_tasks(profile)

        # 生成教练消息
        coach_message = self._generate_daily_coach_message(profile, coach_style)

        return DailyBriefing(
            user_id=user_id,
            date=datetime.now().strftime('%Y-%m-%d'),
            tasks=task_texts[:5],  # 最多5个任务
            coach_message=coach_message,
            streak_days=profile.get("behavior", {}).get("streak_days", 0),
            encouragement=DailyBriefing._generate_encouragement(
                profile,
                profile.get("behavior", {}).get("streak_days", 0)
            )
        )

    def _generate_default_daily_tasks(self, profile: Dict[str, Any]) -> List[str]:
        """生成默认每日任务"""
        tasks = []
        focus_areas = profile.get("preferences", {}).get("focus", [])

        # 基于关注领域生成任务
        task_templates = {
            "sleep": ["保持规律作息时间", "睡前30分钟放下手机"],
            "glucose": ["记录今日饮食", "餐后散步10分钟"],
            "weight": ["称量并记录体重", "控制今日热量摄入"],
            "stress": ["进行5分钟深呼吸", "记录今日心情"],
            "exercise": ["完成今日运动目标", "记录运动时长"],
            "nutrition": ["保证蔬菜摄入", "减少加工食品"],
            "mood": ["记录今日情绪", "做一件让自己开心的事"],
            "energy": ["保证午休时间", "避免咖啡因过量"]
        }

        for area in focus_areas[:2]:  # 最多2个领域
            if area in task_templates:
                tasks.extend(task_templates[area][:2])

        # 如果没有任务，添加通用任务
        if not tasks:
            tasks = ["记录今日感受", "完成一个小目标"]

        return tasks[:3]  # 最多3个任务

    def _generate_daily_coach_message(self,
                                      profile: Dict[str, Any],
                                      coach_style: str) -> str:
        """生成每日教练消息"""
        stage = profile.get("behavior", {}).get("stage", "resistance")
        streak = profile.get("behavior", {}).get("streak_days", 0)

        # 根据连续天数调整消息
        if streak >= 7:
            prefix = "一周了！"
        elif streak >= 3:
            prefix = "坚持得不错，"
        else:
            prefix = ""

        # 根据阶段和风格生成消息
        base_messages = {
            "gentle": f"{prefix}今天继续保持，一小步就很好。",
            "direct": f"{prefix}今天的任务已准备好，开始吧。",
            "motivational": f"{prefix}新的一天，新的机会！",
            "educational": f"{prefix}今天的任务会帮助您更健康。"
        }

        return base_messages.get(coach_style, base_messages["gentle"])

    def parse_daily_briefing_json(self, briefing_json: Dict[str, Any]) -> DailyBriefing:
        """解析 JSON 格式的每日简报

        Args:
            briefing_json: 每日简报 JSON

        Returns:
            DailyBriefing 对象
        """
        return DailyBriefing.from_dict(briefing_json)

    def get_daily_push_content(self, user_id: str) -> Dict[str, Any]:
        """获取用于推送的每日内容

        Args:
            user_id: 用户ID

        Returns:
            简化的推送内容字典
        """
        briefing = self.generate_daily_briefing(user_id)
        return briefing.to_dict()

    def get_daily_push_message(self, user_id: str) -> str:
        """获取格式化的推送消息文本

        Args:
            user_id: 用户ID

        Returns:
            格式化的消息文本
        """
        briefing = self.generate_daily_briefing(user_id)
        return briefing.format_message()

    # ========================================================================
    # Step 7: 干预规划
    # ========================================================================

    def _generate_intervention_plan(self,
                                   user_input: UserInput,
                                   profile: Dict[str, Any],
                                   coordinated: CoordinatedResult) -> Optional[InterventionPlan]:
        """生成干预计划"""

        # 尝试使用 Pipeline
        if self.pipeline:
            try:
                # 构建 pipeline 输入
                pipeline_result = self.pipeline.process_user_state(
                    user_id=user_input.user_id,
                    efficacy_score=user_input.efficacy_score
                )

                if pipeline_result:
                    return InterventionPlan(
                        plan_id=str(uuid.uuid4()),
                        user_id=user_input.user_id,
                        created_at=datetime.now().isoformat(),
                        intervention_type=pipeline_result.get("intervention_type", "standard"),
                        intervention_strategy=pipeline_result.get("strategy", "supportive"),
                        tasks=pipeline_result.get("tasks", []),
                        knowledge_points=pipeline_result.get("knowledge", []),
                        videos=pipeline_result.get("videos", []),
                        products=pipeline_result.get("products", []),
                        coach_script=pipeline_result.get("coach_script", ""),
                        follow_up_points=pipeline_result.get("follow_up", []),
                        expected_duration_days=pipeline_result.get("duration_days", 7),
                        difficulty_level=pipeline_result.get("difficulty", 2),
                        max_tasks_today=pipeline_result.get("max_tasks", 2)
                    )
            except Exception as e:
                print(f"[Master Agent] Pipeline 调用失败: {e}")

        # 降级: 基于效能感生成简单计划
        efficacy = user_input.efficacy_score

        if efficacy < 20:
            max_tasks = 1
            difficulty = 1
            strategy = "minimal_viable"
        elif efficacy < 50:
            max_tasks = 2
            difficulty = 2
            strategy = "gradual_build"
        else:
            max_tasks = 3
            difficulty = 3
            strategy = "habit_strengthening"

        return InterventionPlan(
            plan_id=str(uuid.uuid4()),
            user_id=user_input.user_id,
            created_at=datetime.now().isoformat(),
            intervention_type="behavioral",
            intervention_strategy=strategy,
            tasks=[],
            knowledge_points=[],
            videos=[],
            products=[],
            coach_script="",
            follow_up_points=["明天同一时间签到", "记录今日心情变化"],
            expected_duration_days=7,
            difficulty_level=difficulty,
            max_tasks_today=max_tasks
        )

    # ========================================================================
    # Step 8: 响应合成
    # ========================================================================

    def _synthesize_response(self,
                            user_input: UserInput,
                            profile: Dict[str, Any],
                            routing: RoutingDecision,
                            coordinated: CoordinatedResult,
                            intervention: Optional[InterventionPlan],
                            insights: Optional[Insights] = None) -> SynthesizedResponse:
        """合成最终响应 - 统一教练风格"""

        # 确定教练风格
        coach_style = self._determine_coach_style(routing, profile)

        # 获取主要响应
        main_text = coordinated.primary_response.response_text

        # 如果有洞察，增强响应内容
        if insights and insights.correlations:
            # 在响应中添加关联发现
            correlation_text = f"\n\n{insights.correlations[0]}"
            if correlation_text not in main_text:
                main_text = main_text + correlation_text

        # 构建关键消息
        key_messages = []
        if routing.risk_level == RiskLevel.CRITICAL:
            key_messages.append("您的安全是最重要的")
            key_messages.append("专业支持随时可用")
        elif routing.risk_factors:
            key_messages.append("我们注意到一些需要关注的地方")

        # 从洞察中提取关键消息
        if insights and insights.recommendations_priority:
            for rec in insights.recommendations_priority[:2]:
                if rec not in key_messages:
                    key_messages.append(rec)

        # 构建行动项
        action_items = []
        if intervention and intervention.tasks:
            for task in intervention.tasks[:3]:
                action_items.append(task.get("title", "完成今日任务"))
        elif insights and insights.recommendations_priority:
            action_items = insights.recommendations_priority[:2]
        else:
            if routing.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                action_items.append("如需要请联系专业支持")
            action_items.append("保持与我们的联系")

        # 构建跟进问题
        follow_up_questions = self._generate_follow_up_questions(routing, profile)

        # 确定语气
        tone = "empathetic" if routing.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH] else "supportive"

        return SynthesizedResponse(
            response_text=main_text,
            coach_style=coach_style,
            tone=tone,
            key_messages=key_messages,
            action_items=action_items,
            follow_up_questions=follow_up_questions
        )

    def _determine_coach_style(self, routing: RoutingDecision, profile: Dict[str, Any]) -> str:
        """确定教练风格

        优先级:
        1. 危机状态强制使用共情风格
        2. 高风险状态使用温和支持风格
        3. 用户偏好设置 (preferences.coaching_style)
        4. 基于行为阶段推断
        """

        # 危机状态强制使用共情风格
        if routing.risk_level == RiskLevel.CRITICAL:
            return "empathetic"  # 共情支持
        elif routing.risk_level == RiskLevel.HIGH:
            return "supportive"  # 温和支持

        # 用户偏好设置优先
        user_preference = profile.get("preferences", {}).get("coaching_style")
        if user_preference in ["gentle", "direct", "motivational", "educational"]:
            # 映射用户偏好到系统风格
            style_mapping = {
                "gentle": "supportive",
                "direct": "educational",
                "motivational": "motivational",
                "educational": "educational"
            }
            return style_mapping.get(user_preference, "supportive")

        # 基于行为阶段推断 (自研五层次心理准备度模型)
        # resistance(完全对抗) -> ambivalence(抗拒与反思) -> compromise(妥协与接受)
        # -> adaptation(顺应与调整) -> integration(全面臣服)
        behavior_stage = profile.get("behavior", {}).get("stage", "")

        if behavior_stage in ["resistance", "ambivalence"]:
            # 早期阶段: 需要温和引导，激发动机
            return "motivational"
        elif behavior_stage in ["compromise", "adaptation"]:
            # 中期阶段: 可以给予更多教育指导
            return "educational"
        elif behavior_stage == "integration":
            # 后期阶段: 支持性维持
            return "supportive"
        else:
            return "supportive"  # 默认支持

    def _generate_follow_up_questions(self, routing: RoutingDecision, profile: Dict[str, Any]) -> List[str]:
        """生成跟进问题"""
        questions = []

        if routing.risk_level == RiskLevel.CRITICAL:
            questions.append("您现在安全吗？")
            questions.append("身边有可以陪伴您的人吗？")
        elif routing.risk_level == RiskLevel.HIGH:
            questions.append("这种情况持续多久了？")
            questions.append("有什么让您感觉好一些的事情吗？")
        else:
            questions.append("您今天感觉怎么样？")
            questions.append("有什么我可以帮助您的吗？")

        return questions[:2]

    # ========================================================================
    # Step 9: 任务生成与持久化
    # ========================================================================

    def _generate_tasks_and_tracking(self,
                                    user_input: UserInput,
                                    profile: Dict[str, Any],
                                    intervention: Optional[InterventionPlan]) -> Tuple[List[DailyTask], Tracking]:
        """生成今日任务和追踪信息"""

        daily_tasks = []

        # 基于干预计划生成任务
        if intervention and intervention.tasks:
            for i, task_data in enumerate(intervention.tasks[:intervention.max_tasks_today]):
                task = DailyTask(
                    task_id=f"task_{user_input.session_id}_{i}",
                    title=task_data.get("title", f"任务 {i+1}"),
                    description=task_data.get("description", ""),
                    task_type=task_data.get("type", "general"),
                    difficulty=task_data.get("difficulty", 2),
                    duration_minutes=task_data.get("duration", 10),
                    scheduled_time=task_data.get("scheduled_time"),
                    priority=i + 1,
                    resources={
                        "knowledge_link": task_data.get("knowledge_link", ""),
                        "video_link": task_data.get("video_link", ""),
                        "product_id": task_data.get("product_id", "")
                    },
                    tracking_points=task_data.get("tracking_points", []),
                    completion_criteria=task_data.get("criteria", "完成即可")
                )
                daily_tasks.append(task)
        else:
            # 默认任务 (基于效能感)
            efficacy = user_input.efficacy_score

            if efficacy < 20:
                daily_tasks.append(DailyTask(
                    task_id=f"task_{user_input.session_id}_0",
                    title="今日微任务：深呼吸3次",
                    description="找一个安静的地方，慢慢吸气4秒，屏住2秒，呼气6秒。重复3次。",
                    task_type="breathing",
                    difficulty=1,
                    duration_minutes=2,
                    scheduled_time="22:30",
                    priority=1,
                    resources={"knowledge_link": "/knowledge/breathing/basic"},
                    tracking_points=["完成时间", "感受变化"],
                    completion_criteria="完成3次深呼吸"
                ))
            elif efficacy < 50:
                daily_tasks.append(DailyTask(
                    task_id=f"task_{user_input.session_id}_0",
                    title="今日任务：5分钟正念呼吸",
                    description="使用App引导的5分钟正念呼吸练习",
                    task_type="meditation",
                    difficulty=2,
                    duration_minutes=5,
                    scheduled_time="22:00",
                    priority=1,
                    resources={"video_link": "/videos/mindfulness-5min"},
                    tracking_points=["完成时间", "专注程度", "感受变化"],
                    completion_criteria="完成5分钟练习"
                ))
            else:
                daily_tasks.append(DailyTask(
                    task_id=f"task_{user_input.session_id}_0",
                    title="今日任务：15分钟轻度运动",
                    description="选择散步、拉伸或瑜伽，保持15分钟轻度活动",
                    task_type="exercise",
                    difficulty=3,
                    duration_minutes=15,
                    scheduled_time="18:00",
                    priority=1,
                    resources={"video_link": "/videos/light-exercise-15min"},
                    tracking_points=["完成时间", "运动类型", "运动后心情"],
                    completion_criteria="完成15分钟活动"
                ))

        # 生成追踪点
        tracking_points = [
            f"今日任务完成情况 ({len(daily_tasks)}项)",
            "睡眠质量记录",
            "心情变化记录"
        ]

        if intervention and intervention.follow_up_points:
            tracking_points.extend(intervention.follow_up_points[:2])

        # 计算下次签到时间 (明早8点)
        tomorrow = datetime.now() + timedelta(days=1)
        next_check_in = tomorrow.replace(hour=8, minute=0, second=0).isoformat()

        # 生成提醒
        reminders = []
        for task in daily_tasks:
            if task.scheduled_time:
                # 提前30分钟提醒
                reminders.append(Reminder(
                    time=task.scheduled_time,
                    message=f"该开始「{task.title}」啦～"
                ))

        tracking = Tracking(
            points=tracking_points,
            next_check_in=next_check_in,
            reminders=reminders
        )

        return daily_tasks, tracking

    def _finalize_profile(self,
                         user_id: str,
                         profile: Dict[str, Any],
                         response: SynthesizedResponse,
                         tasks: List[DailyTask],
                         tracking: Tracking,
                         risk_factors: List[str]) -> ProfileUpdates:
        """最终化并保存 Profile，返回更新摘要"""

        updated_fields = []
        new_risk_flags = []

        # 更新今日任务 (v2.0: today.tasks)
        today = profile.get("today", {})
        today["tasks"] = [
            {"task_id": t.task_id, "title": t.title, "status": "pending"}
            for t in tasks
        ]
        profile["today"] = today
        updated_fields.append("today.tasks")

        # 更新追踪点
        profile["tracking_points"] = tracking.points
        updated_fields.append("tracking_points")

        # 更新历史统计 (v2.0: history)
        history = profile.get("history", {})
        old_assigned = history.get("total_tasks_assigned", 0)
        history["total_tasks_assigned"] = old_assigned + len(tasks)
        history["total_sessions"] = history.get("total_sessions", 0) + 1
        history["last_session"] = datetime.now().isoformat()
        profile["history"] = history
        updated_fields.append("history")

        # 提取新的风险标记
        for factor in risk_factors:
            if "危急" in factor or "严重" in factor or "偏低" in factor or "偏高" in factor:
                new_risk_flags.append(factor)

        # 更新风险标记 (v2.0: risk_flags 在根级别)
        existing_flags = profile.get("risk_flags", [])
        for flag in new_risk_flags:
            flag_obj = {
                "flag": flag,
                "severity": "critical" if "危急" in flag else ("high" if "严重" in flag else "medium"),
                "detected_at": datetime.now().isoformat(),
                "resolved": False
            }
            # 检查是否已存在相同的未解决标记
            if not any(f.get("flag") == flag and not f.get("resolved") for f in existing_flags):
                existing_flags.append(flag_obj)
        profile["risk_flags"] = existing_flags[-20:]  # 保留最近20个
        updated_fields.append("risk_flags")

        self.profile_manager.update_profile(user_id, {
            "today": profile["today"],
            "tracking_points": profile["tracking_points"],
            "history": profile["history"],
            "risk_flags": profile["risk_flags"]
        })

        # 持久化
        self.profile_manager.save_profile(user_id)
        print(f"[Master Agent] Profile 已保存: {user_id}")

        return ProfileUpdates(
            updated_fields=updated_fields,
            new_risk_flags=new_risk_flags,
            stage_change=False,
            efficacy_change=0.0
        )

    # ========================================================================
    # 便捷接口
    # ========================================================================

    def chat(self, user_id: str, message: str, efficacy_score: float = 50.0) -> str:
        """简化的对话接口"""
        user_input = UserInput(
            user_id=user_id,
            input_type=InputType.TEXT,
            content=message,
            efficacy_score=efficacy_score
        )

        response = self.process(user_input)
        return response.response.response_text

    def process_json(self, input_json: Dict[str, Any]) -> Dict[str, Any]:
        """处理 JSON 格式的输入，返回 JSON 格式的输出"""
        user_input = UserInput.from_dict(input_json)
        response = self.process(user_input)
        return response.to_dict()

    def process_with_pipeline(self, input_json: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """使用 PipelineOrchestrator 处理请求 (带完整追踪)

        Args:
            input_json: 输入 JSON

        Returns:
            (response_dict, pipeline_summary) 元组
        """
        orchestrator = PipelineOrchestrator(self)
        response, ctx = orchestrator.execute(input_json)
        return response.to_dict(), ctx.get_execution_summary()

    def get_pipeline_orchestrator(self) -> PipelineOrchestrator:
        """获取 PipelineOrchestrator 实例"""
        return PipelineOrchestrator(self)

    def route_agents(self,
                     profile: Dict[str, Any],
                     intent: str,
                     risk: Dict[str, Any],
                     device_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Agent 路由 - 选择最合适的 Agent 组合

        Args:
            profile: 用户画像
            intent: 用户意图/消息
            risk: 风险评估 {"level": "high", "score": 72, "factors": [...]}
            device_data: 设备数据 (可选)

        Returns:
            Agent 列表 [{"agent": "GlucoseAgent", "priority": 1}, ...]

        示例:
            >>> agents = master_agent.route_agents(profile, "血糖高睡不好", risk)
            >>> [{"agent": "GlucoseAgent", "priority": 1},
            ...  {"agent": "SleepAgent", "priority": 2}]
        """
        result = self.agent_router.route(profile, intent, risk, device_data)
        return result.agents

    def route_agents_detailed(self,
                              profile: Dict[str, Any],
                              intent: str,
                              risk: Dict[str, Any],
                              device_data: Optional[Dict[str, Any]] = None) -> AgentRouteResult:
        """
        Agent 路由 (详细版) - 返回完整路由结果

        Returns:
            AgentRouteResult 包含 agents, primary_agent, secondary_agents, reasoning, confidence
        """
        return self.agent_router.route(profile, intent, risk, device_data)

    def coordinate(self, agent_results: List[AgentAnalysisResult]) -> IntegratedAnalysis:
        """
        协调多个 Agent 结果 - 冲突消解 + 权重融合

        Args:
            agent_results: Agent 分析结果列表

        Returns:
            IntegratedAnalysis 融合后的分析结果

        示例:
            >>> results = [
            ...     AgentAnalysisResult(agent="GlucoseAgent", analysis="血糖偏高", ...),
            ...     AgentAnalysisResult(agent="SleepAgent", analysis="睡眠不足", ...)
            ... ]
            >>> integrated = master_agent.coordinate(results)
            >>> integrated.summary
            '综合Glucose/Sleep分析，存在较高健康风险...'
        """
        return self.multi_agent_coordinator.coordinate(agent_results)

    def coordinate_from_json(self, agent_results_json: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        协调 JSON 格式的 Agent 结果

        Args:
            agent_results_json: Agent 分析结果 JSON 列表

        Returns:
            融合后的分析结果字典
        """
        results = [AgentAnalysisResult.from_dict(r) for r in agent_results_json]
        integrated = self.coordinate(results)
        return integrated.to_dict()

    def sync_device_data(self, user_id: str, device_data: DeviceData) -> MasterAgentResponse:
        """同步设备数据"""
        user_input = UserInput(
            user_id=user_id,
            input_type=InputType.DEVICE,
            device_data=device_data
        )
        return self.process(user_input)

    def submit_assessment(self, user_id: str, assessment_data: Dict[str, Any]) -> MasterAgentResponse:
        """提交评估数据"""
        user_input = UserInput(
            user_id=user_id,
            input_type=InputType.ASSESSMENT,
            form_data=assessment_data
        )
        return self.process(user_input)

    def report_task_completion(self, user_id: str, task_id: str, completion_data: Dict[str, Any]) -> MasterAgentResponse:
        """上报任务完成"""
        user_input = UserInput(
            user_id=user_id,
            input_type=InputType.TASK_REPORT,
            form_data={"task_id": task_id, **completion_data}
        )
        return self.process(user_input)


# ============================================================================
# 测试入口
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("行健行为教练 - Master Agent 测试")
    print("=" * 60)

    # 初始化
    master = MasterAgent()

    # 测试1: 简单文本对话
    print("\n" + "=" * 60)
    print("测试1: 简单文本对话")
    print("=" * 60)

    response = master.chat(
        user_id="test_user_001",
        message="我最近总是失眠，已经连续三天睡不好了",
        efficacy_score=35
    )
    print(f"响应: {response[:200]}...")

    # 测试2: 完整 JSON 输入 (带设备数据)
    print("\n" + "=" * 60)
    print("测试2: JSON 输入 (带 CGM 和睡眠数据)")
    print("=" * 60)

    json_input = {
        "user_id": "U12345",
        "input_type": "text",
        "content": "最近晚上总是睡不好，血糖也高",
        "timestamp": datetime.now().isoformat(),
        "efficacy_score": 45,
        "device_data": {
            "cgm": {
                "current_glucose": 145,
                "trend": "stable",
                "time_in_range_percent": 68,
                "avg_glucose_24h": 138,
                "high_events_24h": 3,
                "low_events_24h": 0
            },
            "hrv": {
                "sdnn": 42,
                "rmssd": 28,
                "stress_index": 65,
                "recovery_score": 55
            },
            "steps": 5321,
            "sleep": {
                "duration_hours": 5.5,
                "quality_score": 58,
                "deep_sleep_percent": 12,
                "awakenings": 4
            }
        },
        "context": {
            "source": "app",
            "platform": "ios"
        }
    }

    result = master.process_json(json_input)

    print(f"\n路由决策:")
    print(f"  - 风险等级: {result['routing']['risk_level']}")
    print(f"  - 风险分数: {result['routing']['risk_score']}")
    print(f"  - 风险因素: {result['routing']['risk_factors']}")
    print(f"  - 主要专家: {result['routing']['primary_agent']}")

    print(f"\n数据洞察:")
    if result.get('insights'):
        print(f"  - 健康摘要: {result['insights']['health_summary']}")
        print(f"  - 告警数量: {len(result['insights']['alerts'])}")
        for alert in result['insights']['alerts'][:2]:
            print(f"    * [{alert['severity']}] {alert['message']}")
        if result['insights']['correlations']:
            print(f"  - 关联发现: {result['insights']['correlations'][0]}")

    print(f"\n响应内容:")
    print(f"  {result['response']['text'][:300]}...")

    print(f"\n今日任务:")
    for task in result['daily_tasks']:
        print(f"  - [{task['task_type']}] {task['title']} ({task['duration_minutes']}分钟)")

    print(f"\n追踪信息:")
    if result.get('tracking'):
        print(f"  - 追踪点: {result['tracking']['points']}")
        print(f"  - 下次签到: {result['tracking']['next_check_in']}")

    print(f"\n处理耗时: {result['metadata']['processing_time_ms']:.2f}ms")

    # 测试3: 高风险场景
    print("\n" + "=" * 60)
    print("测试3: 高风险场景")
    print("=" * 60)

    response = master.chat(
        user_id="test_user_003",
        message="我感觉活着没什么意思",
        efficacy_score=15
    )
    print(f"响应: {response[:300]}...")
