"""
数据库模型定义
Database Models for Behavioral Health Platform

定义核心数据表：
- User: 用户表
- Assessment: 评估记录表
- Trigger: 触发器记录表
- Intervention: 干预记录表
- Session: 会话表
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    JSON, ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


# ============================================
# 枚举类型定义
# ============================================

class UserRole(str, enum.Enum):
    """
    用户角色 - v18统一角色层级

    行为健康晋级序列（从低到高）：
    L0: 观察员 (observer)
    L1: 成长者 (grower) - 原患者
    L2: 分享者 (sharer)
    L3: 健康教练 (coach)
    L4: 促进师 (promoter) / 督导 (supervisor) - 平级平权
    L5: 大师 (master)
    L99: 管理员 (admin)
    """
    # 行为健康晋级序列
    OBSERVER = "observer"        # L0 行为健康观察员
    GROWER = "grower"            # L1 成长者（原患者）
    SHARER = "sharer"            # L2 分享者
    COACH = "coach"              # L3 健康教练
    PROMOTER = "promoter"        # L4 行为健康促进师
    SUPERVISOR = "supervisor"    # L4 督导专家（与促进师平级）
    MASTER = "master"            # L5 行为健康促进大师

    # 系统角色
    ADMIN = "admin"              # L99 系统管理员
    SYSTEM = "system"            # 系统账号

    # 旧角色（向后兼容，映射到新角色）
    PATIENT = "patient"          # 已废弃 → 映射到 grower


class RiskLevel(str, enum.Enum):
    """风险等级"""
    R0 = "R0"  # 正常
    R1 = "R1"  # 轻度
    R2 = "R2"  # 中度
    R3 = "R3"  # 高度
    R4 = "R4"  # 危机


class TriggerSeverity(str, enum.Enum):
    """Trigger严重程度"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class TriggerCategory(str, enum.Enum):
    """Trigger类别"""
    PHYSIOLOGICAL = "physiological"  # 生理类
    PSYCHOLOGICAL = "psychological"  # 心理类
    BEHAVIORAL = "behavioral"        # 行为类
    ENVIRONMENTAL = "environmental"  # 环境类


class AgentType(str, enum.Enum):
    """Agent类型"""
    CRISIS = "CrisisAgent"
    GLUCOSE = "GlucoseAgent"
    METABOLIC = "MetabolicAgent"
    SLEEP = "SleepAgent"
    STRESS = "StressAgent"
    MENTAL_HEALTH = "MentalHealthAgent"
    MOTIVATION = "MotivationAgent"
    NUTRITION = "NutritionAgent"
    EXERCISE = "ExerciseAgent"
    COACHING = "CoachingAgent"
    TCM = "TCMAgent"


# ============================================
# 数据模型定义
# ============================================

class User(Base):
    """
    用户表

    存储用户基本信息、认证凭据、用户画像
    """
    __tablename__ = "users"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True)

    # 认证信息
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # 角色与权限
    role = Column(SQLEnum(UserRole), default=UserRole.PATIENT, nullable=False)

    # 个人信息
    full_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)

    # 用户画像（JSON存储）
    profile = Column(JSON, nullable=True, default={})
    # 示例结构：
    # {
    #   "age": 45,
    #   "chronic_conditions": ["diabetes", "hypertension"],
    #   "medications": ["metformin"],
    #   "goals": ["weight_loss", "glucose_control"],
    #   "preferences": {"notification_time": "09:00"}
    # }

    # 健康指标
    adherence_rate = Column(Float, default=0.0)  # 依从性百分比
    last_assessment_date = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # 关系
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    behavioral_profile = relationship("BehavioralProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_role', 'role'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"


class Assessment(Base):
    """
    评估记录表

    存储每次L2评估的完整结果
    """
    __tablename__ = "assessments"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(String(50), unique=True, nullable=False, index=True)  # ASS-xxx格式

    # 外键
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 输入数据
    text_content = Column(Text, nullable=True)
    glucose_values = Column(JSON, nullable=True)  # [6.5, 11.2, 13.5]
    hrv_values = Column(JSON, nullable=True)      # [58, 62, 55]
    activity_data = Column(JSON, nullable=True)   # {"steps": 3000, "distance": 2.5}
    sleep_data = Column(JSON, nullable=True)      # {"duration": 6.5, "quality": 0.7}

    # 用户画像快照（评估时的状态）
    user_profile_snapshot = Column(JSON, nullable=True)

    # 风险评估结果
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0-100
    primary_concern = Column(String(200), nullable=True)
    urgency = Column(String(20), nullable=True)  # immediate/high/moderate/low
    severity_distribution = Column(JSON, nullable=True)  # {"critical": 1, "high": 2, ...}
    reasoning = Column(Text, nullable=True)

    # 路由决策
    primary_agent = Column(SQLEnum(AgentType), nullable=False)
    secondary_agents = Column(JSON, nullable=True)  # ["StressAgent", "SleepAgent"]
    priority = Column(Integer, nullable=False)  # 1-4
    response_time = Column(String(50), nullable=True)  # "立即", "1小时内"
    routing_reasoning = Column(Text, nullable=True)
    recommended_actions = Column(JSON, nullable=True)  # ["行动1", "行动2"]

    # 执行状态
    status = Column(String(20), default="pending")  # pending/processing/completed/failed

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # 元数据
    context = Column(JSON, nullable=True)  # 额外上下文信息

    # 关系
    user = relationship("User", back_populates="assessments")
    triggers = relationship("TriggerRecord", back_populates="assessment", cascade="all, delete-orphan")
    interventions = relationship("Intervention", back_populates="assessment", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_assessment_user_created', 'user_id', 'created_at'),
        Index('idx_assessment_risk_level', 'risk_level'),
        Index('idx_assessment_status', 'status'),
    )

    def __repr__(self):
        return f"<Assessment(id={self.assessment_id}, user_id={self.user_id}, risk={self.risk_level.value})>"


class TriggerRecord(Base):
    """
    Trigger记录表

    存储每次评估识别出的Trigger
    """
    __tablename__ = "trigger_records"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 外键
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False, index=True)

    # Trigger信息
    tag_id = Column(String(50), nullable=False, index=True)  # high_glucose
    name = Column(String(100), nullable=False)  # 高血糖
    category = Column(SQLEnum(TriggerCategory), nullable=False)
    severity = Column(SQLEnum(TriggerSeverity), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # 0.0-1.0

    # 元数据（使用trigger_metadata避免与SQLAlchemy的metadata冲突）
    trigger_metadata = Column("metadata", JSON, nullable=True)
    # 示例：{"max_glucose": 13.5, "threshold": 10.0, "detection_method": "signal"}

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    assessment = relationship("Assessment", back_populates="triggers")

    # 索引
    __table_args__ = (
        Index('idx_trigger_tag_severity', 'tag_id', 'severity'),
        Index('idx_trigger_category', 'category'),
    )

    def __repr__(self):
        return f"<TriggerRecord(id={self.id}, tag_id='{self.tag_id}', severity='{self.severity.value}')>"


class Intervention(Base):
    """
    干预记录表

    存储针对评估结果的干预措施和执行情况
    """
    __tablename__ = "interventions"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 外键
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False, index=True)

    # 干预信息
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    intervention_type = Column(String(50), nullable=True)  # education/medication_review/counseling

    # 干预内容
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    actions = Column(JSON, nullable=True)  # 具体行动步骤

    # 执行状态
    status = Column(String(20), default="pending")  # pending/sent/acknowledged/completed/skipped

    # 用户反馈
    user_feedback = Column(Text, nullable=True)
    feedback_score = Column(Integer, nullable=True)  # 1-5
    completed = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    assessment = relationship("Assessment", back_populates="interventions")

    # 索引
    __table_args__ = (
        Index('idx_intervention_status', 'status'),
        Index('idx_intervention_agent', 'agent_type'),
    )

    def __repr__(self):
        return f"<Intervention(id={self.id}, agent='{self.agent_type.value}', status='{self.status}')>"


class UserSession(Base):
    """
    用户会话表

    存储用户登录会话信息
    """
    __tablename__ = "user_sessions"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)

    # 外键
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 会话信息
    token = Column(String(500), nullable=True)  # JWT token
    refresh_token = Column(String(500), nullable=True)

    # 客户端信息
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_info = Column(JSON, nullable=True)

    # 会话状态
    is_active = Column(Boolean, default=True, index=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", back_populates="sessions")

    # 索引
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
    )

    def __repr__(self):
        return f"<UserSession(id={self.session_id}, user_id={self.user_id}, active={self.is_active})>"


class HealthData(Base):
    """
    健康数据表

    存储用户的连续健康监测数据
    """
    __tablename__ = "health_data"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 外键
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 数据类型
    data_type = Column(String(50), nullable=False, index=True)  # glucose/hrv/activity/sleep

    # 数据值
    value = Column(Float, nullable=True)
    values = Column(JSON, nullable=True)  # 用于存储数组或复杂数据

    # 单位和元数据
    unit = Column(String(20), nullable=True)  # mmol/L, ms, steps
    data_metadata = Column("metadata", JSON, nullable=True)

    # 来源
    source = Column(String(50), nullable=True)  # manual/device/api
    device_id = Column(String(100), nullable=True)

    # 时间戳
    recorded_at = Column(DateTime, nullable=False, index=True)  # 数据记录时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 索引
    __table_args__ = (
        Index('idx_health_data_user_type_recorded', 'user_id', 'data_type', 'recorded_at'),
        Index('idx_health_data_type', 'data_type'),
    )

    def __repr__(self):
        return f"<HealthData(id={self.id}, user_id={self.user_id}, type='{self.data_type}', value={self.value})>"


# ============================================
# 辅助函数
# ============================================

class ChatSession(Base):
    """
    AI聊天会话表

    存储用户与AI健康助手的对话会话
    """
    __tablename__ = "chat_sessions"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)

    # 外键
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 会话信息
    title = Column(String(200), nullable=True)  # 会话标题（可选）
    model = Column(String(50), default="qwen2.5:0.5b")  # 使用的模型

    # 会话状态
    is_active = Column(Boolean, default=True, index=True)
    message_count = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan",
                          order_by="ChatMessage.created_at")

    # 索引
    __table_args__ = (
        Index('idx_chat_session_user_active', 'user_id', 'is_active'),
        Index('idx_chat_session_updated', 'updated_at'),
    )

    def __repr__(self):
        return f"<ChatSession(id={self.session_id}, user_id={self.user_id}, messages={self.message_count})>"


class ChatMessage(Base):
    """
    AI聊天消息表

    存储每条对话消息
    """
    __tablename__ = "chat_messages"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 外键
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)

    # 消息内容
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)

    # 元数据
    model = Column(String(50), nullable=True)  # 生成此消息的模型
    tokens_used = Column(Integer, nullable=True)  # token消耗（可选）
    msg_metadata = Column("metadata", JSON, nullable=True)  # 其他元数据

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    session = relationship("ChatSession", back_populates="messages")

    # 索引
    __table_args__ = (
        Index('idx_chat_message_session_created', 'session_id', 'created_at'),
    )

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}', content='{self.content[:30]}...')>"


# ============================================
# 设备数据模型
# ============================================

class DeviceType(str, enum.Enum):
    """设备类型"""
    CGM = "cgm"                  # 连续血糖监测
    GLUCOMETER = "glucometer"    # 指尖血糖仪
    SMARTWATCH = "smartwatch"    # 智能手表
    SMARTBAND = "smartband"      # 智能手环
    SCALE = "scale"              # 体重秤
    BP_MONITOR = "bp_monitor"    # 血压计


class DeviceStatus(str, enum.Enum):
    """设备状态"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    PAIRING = "pairing"


class UserDevice(Base):
    """
    用户设备绑定表

    记录用户绑定的健康设备
    """
    __tablename__ = "user_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), unique=True, nullable=False, index=True)

    # 设备信息
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    manufacturer = Column(String(50), nullable=True)  # abbott/dexcom/huawei/xiaomi/apple
    model = Column(String(100), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    serial_number = Column(String(100), nullable=True)

    # 状态
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.CONNECTED)
    battery_level = Column(Integer, nullable=True)

    # 授权信息
    auth_token = Column(Text, nullable=True)
    auth_expires_at = Column(DateTime, nullable=True)

    # 同步信息
    last_sync_at = Column(DateTime, nullable=True)
    sync_cursor = Column(String(200), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_user_device_user', 'user_id'),
        Index('idx_user_device_type', 'device_type'),
    )

    def __repr__(self):
        return f"<UserDevice(id={self.device_id}, type={self.device_type}, user={self.user_id})>"


class GlucoseReading(Base):
    """
    血糖数据表

    存储 CGM 和手动录入的血糖数据
    """
    __tablename__ = "glucose_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=True, index=True)

    # 血糖值
    value = Column(Float, nullable=False)  # mmol/L
    unit = Column(String(10), default="mmol/L")

    # CGM 趋势
    trend = Column(String(20), nullable=True)  # rising_fast/rising/stable/falling/falling_fast
    trend_rate = Column(Float, nullable=True)  # 变化率 mmol/L/min

    # 来源和标签
    source = Column(String(20), default="manual")  # cgm/finger/manual
    meal_tag = Column(String(20), nullable=True)  # fasting/before_meal/after_meal/bedtime
    notes = Column(Text, nullable=True)

    # 时间
    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_glucose_user_time', 'user_id', 'recorded_at'),
        Index('idx_glucose_device_time', 'device_id', 'recorded_at'),
    )

    def __repr__(self):
        return f"<GlucoseReading(user={self.user_id}, value={self.value}, time={self.recorded_at})>"


class HeartRateReading(Base):
    """
    心率数据表
    """
    __tablename__ = "heart_rate_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=True)

    hr = Column(Integer, nullable=False)  # bpm
    activity_type = Column(String(20), nullable=True)  # rest/walk/run/sleep

    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_hr_user_time', 'user_id', 'recorded_at'),
    )


class HRVReading(Base):
    """
    HRV 数据表
    """
    __tablename__ = "hrv_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=True)

    sdnn = Column(Float, nullable=True)  # ms
    rmssd = Column(Float, nullable=True)  # ms
    lf = Column(Float, nullable=True)
    hf = Column(Float, nullable=True)
    lf_hf_ratio = Column(Float, nullable=True)

    stress_score = Column(Float, nullable=True)  # 0-100
    recovery_score = Column(Float, nullable=True)  # 0-100

    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_hrv_user_time', 'user_id', 'recorded_at'),
    )


class SleepRecord(Base):
    """
    睡眠数据表
    """
    __tablename__ = "sleep_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=True)

    # 睡眠时间
    sleep_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    sleep_start = Column(DateTime, nullable=True)
    sleep_end = Column(DateTime, nullable=True)
    total_duration_min = Column(Integer, nullable=True)

    # 睡眠阶段 (分钟)
    awake_min = Column(Integer, default=0)
    light_min = Column(Integer, default=0)
    deep_min = Column(Integer, default=0)
    rem_min = Column(Integer, default=0)

    # 质量指标
    sleep_score = Column(Integer, nullable=True)  # 0-100
    efficiency = Column(Float, nullable=True)  # 百分比
    awakenings = Column(Integer, default=0)
    onset_latency_min = Column(Integer, nullable=True)

    # 血氧
    avg_spo2 = Column(Float, nullable=True)
    min_spo2 = Column(Float, nullable=True)

    # 详细数据 (JSON)
    stages_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_sleep_user_date', 'user_id', 'sleep_date'),
    )


class ActivityRecord(Base):
    """
    每日活动数据表
    """
    __tablename__ = "activity_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    activity_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD

    # 基础指标
    steps = Column(Integer, default=0)
    distance_m = Column(Integer, default=0)
    floors_climbed = Column(Integer, default=0)
    calories_total = Column(Integer, default=0)
    calories_active = Column(Integer, default=0)

    # 活动时间分布 (分钟)
    sedentary_min = Column(Integer, default=0)
    light_active_min = Column(Integer, default=0)
    moderate_active_min = Column(Integer, default=0)
    vigorous_active_min = Column(Integer, default=0)

    # 每小时数据 (JSON)
    hourly_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_activity_user_date', 'user_id', 'activity_date'),
    )


class WorkoutRecord(Base):
    """
    运动记录表
    """
    __tablename__ = "workout_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=True)

    workout_type = Column(String(50), nullable=False)  # walk/run/cycle/swim/yoga
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_min = Column(Integer, nullable=True)

    distance_m = Column(Integer, nullable=True)
    calories = Column(Integer, nullable=True)
    avg_hr = Column(Integer, nullable=True)
    max_hr = Column(Integer, nullable=True)
    avg_pace = Column(String(20), nullable=True)  # min/km

    notes = Column(Text, nullable=True)
    gps_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_workout_user_time', 'user_id', 'start_time'),
    )


class VitalSign(Base):
    """
    体征数据表 (体重/血压/体温/血氧)
    """
    __tablename__ = "vital_signs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=True)

    data_type = Column(String(20), nullable=False)  # weight/blood_pressure/temperature/spo2

    # 体重/体成分
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    body_fat_percent = Column(Float, nullable=True)
    muscle_mass_kg = Column(Float, nullable=True)
    water_percent = Column(Float, nullable=True)
    visceral_fat = Column(Integer, nullable=True)

    # 血压
    systolic = Column(Integer, nullable=True)
    diastolic = Column(Integer, nullable=True)
    pulse = Column(Integer, nullable=True)

    # 体温
    temperature = Column(Float, nullable=True)

    # 血氧
    spo2 = Column(Float, nullable=True)

    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_vital_user_type_time', 'user_id', 'data_type', 'recorded_at'),
    )


class BehavioralStage(str, enum.Enum):
    """行为改变七阶段"""
    S0 = "S0"  # 无知无觉
    S1 = "S1"  # 强烈抗拒
    S2 = "S2"  # 被动承受
    S3 = "S3"  # 勉强接受
    S4 = "S4"  # 主动尝试
    S5 = "S5"  # 规律践行
    S6 = "S6"  # 内化为常


class StageStability(str, enum.Enum):
    """阶段稳定性"""
    STABLE = "stable"
    SEMI_STABLE = "semi_stable"
    UNSTABLE = "unstable"


class InteractionMode(str, enum.Enum):
    """交互模式"""
    EMPATHY = "empathy"         # 共情模式 (S0-S1)
    CHALLENGE = "challenge"     # 挑战模式 (S2-S3 行动型)
    EXECUTION = "execution"     # 执行模式 (S4-S6)


class PsychologicalLevel(str, enum.Enum):
    """心理层级 (SPI-based)"""
    L1 = "L1"  # 需大量支持
    L2 = "L2"  # 需中度支持
    L3 = "L3"  # 基本就绪
    L4 = "L4"  # 高度就绪
    L5 = "L5"  # 自驱型


class BehavioralProfile(Base):
    """
    统一行为画像表

    系统唯一真相源：存储用户的行为改变阶段、行为类型、心理层级、
    领域需求等核心画像数据，由 BehavioralProfileService 写入，
    StageRuntimeBuilder 负责阶段更新。

    所有干预决策必须基于此画像。
    """
    __tablename__ = "behavioral_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    # ====== 阶段运行态 (只有 StageRuntimeBuilder 可写) ======
    current_stage = Column(SQLEnum(BehavioralStage), nullable=False, default=BehavioralStage.S0)
    stage_confidence = Column(Float, default=0.0)  # 0.0-1.0
    stage_stability = Column(SQLEnum(StageStability), default=StageStability.UNSTABLE)
    stage_updated_at = Column(DateTime, nullable=True)

    # ====== BAPS 向量 ======
    # 大五人格 {E: 15, N: -8, C: 22, A: 10, O: 18}
    big5_scores = Column(JSON, nullable=True)
    # BPT-6 行为类型: "action" / "knowledge" / "emotion" / "relation" / "environment" / "mixed"
    bpt6_type = Column(String(30), nullable=True)
    bpt6_scores = Column(JSON, nullable=True)  # 六维度原始分
    # CAPACITY 改变潜力
    capacity_total = Column(Integer, nullable=True)
    capacity_weak = Column(JSON, nullable=True)  # ["A2_资源", "T_时间"]
    capacity_strong = Column(JSON, nullable=True)  # ["M_动机", "C_信心"]
    # SPI 成功可能性
    spi_score = Column(Float, nullable=True)  # 0-100
    spi_level = Column(String(10), nullable=True)  # very_high/high/medium/low/very_low
    # TTM7 阶段评估原始数据
    ttm7_stage_scores = Column(JSON, nullable=True)  # {S0: 12, S1: 6, ...}
    ttm7_sub_scores = Column(JSON, nullable=True)  # {AW: 25, WI: 22, AC: 18}

    # ====== 领域需求 ======
    # 主要需干预领域: ["nutrition", "exercise", "sleep", "emotion", ...]
    primary_domains = Column(JSON, nullable=True)
    # 领域详情: {"nutrition": {"priority": 1, "stage_strategy": "preparation"}, ...}
    domain_details = Column(JSON, nullable=True)

    # ====== 干预配置 ======
    interaction_mode = Column(SQLEnum(InteractionMode), nullable=True)
    psychological_level = Column(SQLEnum(PsychologicalLevel), nullable=True)
    # 风险标记: ["dropout_risk", "relapse_risk"]
    risk_flags = Column(JSON, nullable=True)

    # ====== 去诊断化展示 ======
    friendly_stage_name = Column(String(50), nullable=True)  # "探索期"
    friendly_stage_desc = Column(Text, nullable=True)  # 面向用户的阶段描述

    # ====== 最近评估ID (用于溯源) ======
    last_assessment_id = Column(String(50), nullable=True)

    # ====== 时间戳 ======
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", back_populates="behavioral_profile")

    __table_args__ = (
        Index('idx_bp_user', 'user_id'),
        Index('idx_bp_stage', 'current_stage'),
        Index('idx_bp_updated', 'updated_at'),
    )

    def __repr__(self):
        return f"<BehavioralProfile(user={self.user_id}, stage={self.current_stage}, type={self.bpt6_type})>"


class BehaviorAuditLog(Base):
    """
    行为跃迁审计日志表

    记录每次 TTM 阶段跃迁事件，用于审计追踪和数据分析
    """
    __tablename__ = "behavior_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)

    # 跃迁信息
    from_stage = Column(String(10), nullable=False)
    to_stage = Column(String(10), nullable=False)
    narrative = Column(Text, nullable=True)
    source_ui = Column(String(20), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_stages', 'from_stage', 'to_stage'),
    )

    def __repr__(self):
        return f"<BehaviorAuditLog(user={self.user_id}, {self.from_stage}->{self.to_stage})>"


class BehaviorHistory(Base):
    """
    行为评估全量历史表

    记录每次 TTM 评估结果（无论是否发生跃迁），
    用于趋势分析、信念变化曲线和叙事回溯。
    """
    __tablename__ = "behavior_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 阶段
    from_stage = Column(String(10), nullable=False)
    to_stage = Column(String(10), nullable=False)
    is_transition = Column(Boolean, default=False, nullable=False)

    # 快照指标
    belief_score = Column(Float, nullable=True)
    narrative_sent = Column(Text, nullable=True)

    __table_args__ = (
        Index('idx_bh_user_ts', 'user_id', 'timestamp'),
        Index('idx_bh_transition', 'is_transition'),
    )

    def __repr__(self):
        arrow = "→" if self.is_transition else "="
        return f"<BehaviorHistory(user={self.user_id}, {self.from_stage}{arrow}{self.to_stage}, belief={self.belief_score})>"


class BehaviorTrace(Base):
    """
    行为长期记忆表

    每次 TTM 判定的完整快照，作为系统的"长期记忆"，
    供周报生成 (analyze_weekly_trend) 和信念变化回溯使用。
    """
    __tablename__ = "behavior_traces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 阶段跃迁
    from_stage = Column(String(10), nullable=False)
    to_stage = Column(String(10), nullable=False)
    is_transition = Column(Boolean, default=False, nullable=False)

    # 判定时刻的指标快照
    belief_score = Column(Float, nullable=True)
    action_count = Column(Integer, nullable=True)

    # 系统响应
    narrative_sent = Column(Text, nullable=True)
    source_ui = Column(String(20), nullable=True)

    __table_args__ = (
        Index('idx_bt_user_ts', 'user_id', 'timestamp'),
        Index('idx_bt_user_transition', 'user_id', 'is_transition'),
    )

    def __repr__(self):
        arrow = "→" if self.is_transition else "="
        return f"<BehaviorTrace(user={self.user_id}, {self.from_stage}{arrow}{self.to_stage}, belief={self.belief_score})>"


# ============================================
# 微行动跟踪模型
# ============================================

class MicroActionTask(Base):
    """
    微行动任务表

    存储从干预计划生成的每日微行动任务
    """
    __tablename__ = "micro_action_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 任务信息
    domain = Column(String(30), nullable=False)  # nutrition/exercise/sleep/emotion/stress/cognitive/social
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(20), default="easy")  # easy/moderate/challenging
    source = Column(String(30), default="intervention_plan")  # intervention_plan/coach/system
    source_id = Column(String(50), nullable=True)  # intervention_plan rx_id or coach user_id

    # 状态
    status = Column(String(20), default="pending")  # pending/completed/skipped/expired
    scheduled_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    completed_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    logs = relationship("MicroActionLog", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_micro_task_user_date', 'user_id', 'scheduled_date'),
        Index('idx_micro_task_status', 'status'),
        Index('idx_micro_task_domain', 'domain'),
    )

    def __repr__(self):
        return f"<MicroActionTask(id={self.id}, user={self.user_id}, title='{self.title[:30]}', status={self.status})>"


class MicroActionLog(Base):
    """
    微行动完成日志表

    记录每次任务完成/跳过的详细信息
    """
    __tablename__ = "micro_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("micro_action_tasks.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 操作
    action = Column(String(20), nullable=False)  # completed/skipped/partial
    note = Column(Text, nullable=True)  # 用户备注
    mood_score = Column(Integer, nullable=True)  # 1-5 完成后心情

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    task = relationship("MicroActionTask", back_populates="logs")

    __table_args__ = (
        Index('idx_micro_log_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<MicroActionLog(id={self.id}, task={self.task_id}, action={self.action})>"


# ============================================
# 提醒与教练消息模型
# ============================================

class Reminder(Base):
    """
    提醒表

    存储用户的定时提醒（药物、随访、行为、评估等）
    """
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 提醒信息
    type = Column(String(30), nullable=False)  # medication/visit/behavior/assessment
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    cron_expr = Column(String(50), nullable=True)  # "0 8 * * *" or null for one-time
    next_fire_at = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, default=True)

    # 来源
    source = Column(String(20), default="self")  # system/coach/self
    created_by = Column(Integer, nullable=True)  # coach user_id or null

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_reminder_user_active', 'user_id', 'is_active'),
        Index('idx_reminder_next_fire', 'next_fire_at'),
    )

    def __repr__(self):
        return f"<Reminder(id={self.id}, user={self.user_id}, type={self.type}, title='{self.title[:30]}')>"


class AssessmentAssignment(Base):
    """
    评估任务表

    教练推送评估量表给学员，学员完成后自动生成管理处方，
    教练审核修改后推送给学员。

    状态流转: pending → completed → reviewed → pushed
    """
    __tablename__ = "assessment_assignments"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 选定量表
    scales = Column(JSON, nullable=False)  # ["ttm7", "big5", "bpt6", "capacity", "spi"]

    # 状态
    status = Column(String(20), default="pending", nullable=False)  # pending/completed/reviewed/pushed
    note = Column(Text, nullable=True)  # 教练备注

    # 管道输出
    pipeline_result = Column(JSON, nullable=True)  # 评估管道完整输出

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    pushed_at = Column(DateTime, nullable=True)

    # 关系
    review_items = relationship("CoachReviewItem", back_populates="assignment", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_aa_coach_student', 'coach_id', 'student_id'),
        Index('idx_aa_student_status', 'student_id', 'status'),
        Index('idx_aa_status', 'status'),
    )

    def __repr__(self):
        return f"<AssessmentAssignment(id={self.id}, coach={self.coach_id}, student={self.student_id}, status={self.status})>"


class CoachReviewItem(Base):
    """
    教练审核条目表

    评估管道自动生成的目标/处方/建议拆解为单条审核条目，
    教练逐条审核（采纳/修改/拒绝）后推送给学员。
    """
    __tablename__ = "coach_review_items"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assessment_assignments.id"), nullable=False, index=True)

    # 条目分类
    category = Column(String(20), nullable=False)  # goal / prescription / suggestion
    domain = Column(String(30), nullable=False)  # nutrition / exercise / sleep / emotion / stress / cognitive / social

    # 内容
    original_content = Column(JSON, nullable=False)  # 系统生成的原始内容
    coach_content = Column(JSON, nullable=True)  # 教练修改后内容（null=采用原始）
    status = Column(String(20), default="pending", nullable=False)  # pending/approved/modified/rejected
    coach_note = Column(Text, nullable=True)  # 教练批注

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    assignment = relationship("AssessmentAssignment", back_populates="review_items")

    __table_args__ = (
        Index('idx_cri_assignment', 'assignment_id'),
        Index('idx_cri_category', 'category'),
    )

    def __repr__(self):
        return f"<CoachReviewItem(id={self.id}, assignment={self.assignment_id}, category={self.category}, status={self.status})>"


class DeviceAlert(Base):
    """
    设备预警表

    当穿戴设备数据达到预警阈值时创建，
    同时向教练和服务对象发送通知。
    """
    __tablename__ = "device_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    coach_id = Column(Integer, nullable=True, index=True)

    # 预警信息
    alert_type = Column(String(50), nullable=False)  # glucose_danger_high, hr_warning_low, etc.
    severity = Column(String(20), nullable=False)  # warning / danger
    message = Column(String(500), nullable=False)
    data_value = Column(Float, nullable=False)  # 实际读数
    threshold_value = Column(Float, nullable=False)  # 阈值
    data_type = Column(String(30), nullable=False)  # glucose / heart_rate / exercise / sleep

    # 状态
    user_read = Column(Boolean, default=False)
    coach_read = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)

    # 去重
    dedup_key = Column(String(100), nullable=False, index=True)  # user_id:type:YYYY-MM-DD-HH

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_device_alert_user', 'user_id', 'created_at'),
        Index('idx_device_alert_coach', 'coach_id', 'coach_read'),
        Index('idx_device_alert_dedup', 'dedup_key'),
    )

    def __repr__(self):
        return f"<DeviceAlert(id={self.id}, user={self.user_id}, type={self.alert_type}, severity={self.severity})>"


class CoachMessage(Base):
    """
    教练消息表

    教练与学员之间的单向消息（教练→学员）
    """
    __tablename__ = "coach_messages"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 消息内容
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text/encouragement/reminder/advice

    # 状态
    is_read = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_coach_msg_student_read', 'student_id', 'is_read'),
        Index('idx_coach_msg_coach_student', 'coach_id', 'student_id'),
    )

    def __repr__(self):
        return f"<CoachMessage(id={self.id}, coach={self.coach_id}, student={self.student_id}, read={self.is_read})>"


# ============================================
# 挑战/打卡活动模型
# ============================================

class PushSourceType(str, enum.Enum):
    """推送来源类型"""
    CHALLENGE = "challenge"
    DEVICE_ALERT = "device_alert"
    MICRO_ACTION = "micro_action"
    AI_RECOMMENDATION = "ai_recommendation"
    SYSTEM = "system"


class PushPriority(str, enum.Enum):
    """推送优先级"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class PushQueueStatus(str, enum.Enum):
    """推送队列状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"
    EXPIRED = "expired"


class ChallengeStatus(str, enum.Enum):
    """挑战模板状态"""
    DRAFT = "draft"                    # 草稿
    PENDING_REVIEW = "pending_review"  # 待双专家审核
    REVIEW_PARTIAL = "review_partial"  # 一位专家已审核
    PUBLISHED = "published"            # 已发布
    ARCHIVED = "archived"              # 已归档


class ChallengeTemplate(Base):
    """
    挑战模板表

    定义一个挑战活动（如14天血糖打卡、21天正念训练），
    包含基本信息、持续天数、审核状态等。

    创建权限: 教练(L3)及以上
    发布权限: 需双专家审核通过
    """
    __tablename__ = "challenge_templates"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # glucose_management / mindfulness / exercise / nutrition
    cover_image = Column(String(500), nullable=True)
    duration_days = Column(Integer, nullable=False)

    # 配置
    config_key = Column(String(100), nullable=True, unique=True)  # glucose_14day → 关联configs/challenges/*.json
    daily_push_times = Column(JSON, nullable=True)  # ["9:00", "11:30", "17:30"]
    day_topics = Column(JSON, nullable=True)  # {0: "欢迎", 1: "主题1", ...}

    # 创建者
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 审核流程（双专家审核）
    status = Column(SQLEnum(ChallengeStatus), default=ChallengeStatus.DRAFT, nullable=False)
    reviewer1_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer1_status = Column(String(20), nullable=True)  # approved / rejected
    reviewer1_note = Column(Text, nullable=True)
    reviewer1_at = Column(DateTime, nullable=True)
    reviewer2_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer2_status = Column(String(20), nullable=True)
    reviewer2_note = Column(Text, nullable=True)
    reviewer2_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)

    # 统计
    enrollment_count = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    day_pushes = relationship("ChallengeDayPush", back_populates="challenge", cascade="all, delete-orphan",
                              order_by="ChallengeDayPush.day_number, ChallengeDayPush.sort_order")
    enrollments = relationship("ChallengeEnrollment", back_populates="challenge", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_challenge_status', 'status'),
        Index('idx_challenge_category', 'category'),
        Index('idx_challenge_created_by', 'created_by'),
    )

    def __repr__(self):
        return f"<ChallengeTemplate(id={self.id}, title='{self.title}', status={self.status})>"


class ChallengeDayPush(Base):
    """
    挑战每日推送内容表

    每天可有多条推送（如 9:00/11:30/17:30），
    每条包含管理内容、行为健康指导、互动评估（问卷JSON）。
    """
    __tablename__ = "challenge_day_pushes"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenge_templates.id"), nullable=False, index=True)

    # 推送时间
    day_number = Column(Integer, nullable=False)  # 0-based day
    push_time = Column(String(20), nullable=False)  # "9:00" / "11:30" / "17:30" / "立即发送"
    sort_order = Column(Integer, default=0)

    # 属性
    is_core = Column(Boolean, default=True)
    tag = Column(String(20), default="core")  # core / optional / assessment / info

    # 内容
    management_content = Column(Text, nullable=True)  # 管理内容
    behavior_guidance = Column(Text, nullable=True)  # 行为健康指导

    # 互动评估（结构化JSON）
    # {"title": "...", "questions": [{"type": "rating/text/single_choice/multi_choice", "label": "...", ...}]}
    survey = Column(JSON, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    challenge = relationship("ChallengeTemplate", back_populates="day_pushes")

    __table_args__ = (
        Index('idx_cdp_challenge_day', 'challenge_id', 'day_number'),
        Index('idx_cdp_day_time', 'day_number', 'push_time'),
    )

    def __repr__(self):
        return f"<ChallengeDayPush(id={self.id}, day={self.day_number}, time={self.push_time}, core={self.is_core})>"


class EnrollmentStatus(str, enum.Enum):
    """报名状态"""
    ENROLLED = "enrolled"      # 已报名，未开始
    ACTIVE = "active"          # 进行中
    COMPLETED = "completed"    # 已完成
    DROPPED = "dropped"        # 中途退出


class ChallengeEnrollment(Base):
    """
    挑战报名表

    记录用户参加的挑战，跟踪进度。
    """
    __tablename__ = "challenge_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("challenge_templates.id"), nullable=False, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 推荐的教练

    # 进度
    status = Column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ENROLLED, nullable=False)
    current_day = Column(Integer, default=0)  # 当前进行到第几天
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 统计
    completed_pushes = Column(Integer, default=0)  # 已完成推送数
    completed_surveys = Column(Integer, default=0)  # 已完成问卷数
    streak_days = Column(Integer, default=0)  # 连续打卡天数

    # 时间戳
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    challenge = relationship("ChallengeTemplate", back_populates="enrollments")
    survey_responses = relationship("ChallengeSurveyResponse", back_populates="enrollment", cascade="all, delete-orphan")
    push_logs = relationship("ChallengePushLog", back_populates="enrollment", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_ce_user_challenge', 'user_id', 'challenge_id'),
        Index('idx_ce_status', 'status'),
        Index('idx_ce_coach', 'coach_id'),
    )

    def __repr__(self):
        return f"<ChallengeEnrollment(id={self.id}, user={self.user_id}, challenge={self.challenge_id}, day={self.current_day})>"


class ChallengeSurveyResponse(Base):
    """
    挑战问卷回答表

    记录用户对每条推送中互动评估的回答。
    """
    __tablename__ = "challenge_survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("challenge_enrollments.id"), nullable=False, index=True)
    push_id = Column(Integer, ForeignKey("challenge_day_pushes.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 回答内容 (JSON)
    # {"q1": "answer", "q2": 8, "q3": ["option1", "option2"]}
    responses = Column(JSON, nullable=False)

    # 时间戳
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    enrollment = relationship("ChallengeEnrollment", back_populates="survey_responses")

    __table_args__ = (
        Index('idx_csr_enrollment', 'enrollment_id'),
        Index('idx_csr_push', 'push_id'),
        Index('idx_csr_user', 'user_id', 'submitted_at'),
    )

    def __repr__(self):
        return f"<ChallengeSurveyResponse(id={self.id}, enrollment={self.enrollment_id}, push={self.push_id})>"


class ChallengePushLog(Base):
    """
    挑战推送日志表

    记录每条推送的发送和阅读状态。
    """
    __tablename__ = "challenge_push_logs"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("challenge_enrollments.id"), nullable=False, index=True)
    push_id = Column(Integer, ForeignKey("challenge_day_pushes.id"), nullable=False, index=True)

    # 状态
    status = Column(String(20), default="pending")  # pending / sent / read
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    # 关系
    enrollment = relationship("ChallengeEnrollment", back_populates="push_logs")

    __table_args__ = (
        Index('idx_cpl_enrollment', 'enrollment_id'),
        Index('idx_cpl_push', 'push_id'),
        Index('idx_cpl_status', 'status'),
    )

    def __repr__(self):
        return f"<ChallengePushLog(id={self.id}, enrollment={self.enrollment_id}, push={self.push_id}, status={self.status})>"


class CoachPushQueue(Base):
    """
    教练推送审批队列

    所有 AI 触发的推送（挑战打卡、设备预警、微行动等）统一进入此队列，
    教练审批后才投递给学员。教练可调整推送的时间、频率、内容。

    流转: pending → approved → sent  或  pending → rejected  或  pending → expired
    """
    __tablename__ = "coach_push_queue"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 来源
    source_type = Column(String(30), nullable=False)  # challenge | device_alert | micro_action | ai_recommendation | system
    source_id = Column(String(50), nullable=True)  # 来源记录 ID

    # 内容
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    content_extra = Column(JSON, nullable=True)  # 附加结构化数据

    # 时间
    suggested_time = Column(DateTime, nullable=True)  # AI 建议发送时间
    scheduled_time = Column(DateTime, nullable=True)  # 教练设定时间（null=立即投递）

    # 优先级与状态
    priority = Column(String(10), default="normal")  # high | normal | low
    status = Column(String(10), default="pending", nullable=False)  # pending | approved | rejected | sent | expired
    coach_note = Column(String(500), nullable=True)

    # 时间戳
    reviewed_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_cpq_coach_status', 'coach_id', 'status'),
        Index('idx_cpq_student', 'student_id'),
        Index('idx_cpq_source', 'source_type'),
        Index('idx_cpq_scheduled', 'status', 'scheduled_time'),
    )

    def __repr__(self):
        return f"<CoachPushQueue(id={self.id}, coach={self.coach_id}, student={self.student_id}, source={self.source_type}, status={self.status})>"


def get_table_names():
    """获取所有表名"""
    return [
        "users",
        "assessments",
        "trigger_records",
        "interventions",
        "user_sessions",
        "health_data",
        "chat_sessions",
        "chat_messages",
        # 设备数据表
        "user_devices",
        "glucose_readings",
        "heart_rate_readings",
        "hrv_readings",
        "sleep_records",
        "activity_records",
        "workout_records",
        "vital_signs",
        # 行为画像
        "behavioral_profiles",
        # 行为审计 + 历史 + 长期记忆
        "behavior_audit_logs",
        "behavior_history",
        "behavior_traces",
        # 微行动跟踪
        "micro_action_tasks",
        "micro_action_logs",
        # 设备预警
        "device_alerts",
        # 提醒与教练消息
        "reminders",
        "coach_messages",
        # 评估任务与审核
        "assessment_assignments",
        "coach_review_items",
        # 挑战/打卡活动
        "challenge_templates",
        "challenge_day_pushes",
        "challenge_enrollments",
        "challenge_survey_responses",
        "challenge_push_logs",
        # 教练推送审批队列
        "coach_push_queue",
    ]


def get_model_by_name(name: str):
    """根据名称获取模型类"""
    models = {
        "User": User,
        "Assessment": Assessment,
        "TriggerRecord": TriggerRecord,
        "Intervention": Intervention,
        "UserSession": UserSession,
        "HealthData": HealthData,
        "ChatSession": ChatSession,
        "ChatMessage": ChatMessage,
        # 设备数据模型
        "UserDevice": UserDevice,
        "GlucoseReading": GlucoseReading,
        "HeartRateReading": HeartRateReading,
        "HRVReading": HRVReading,
        "SleepRecord": SleepRecord,
        "ActivityRecord": ActivityRecord,
        "WorkoutRecord": WorkoutRecord,
        "VitalSign": VitalSign,
        "BehavioralProfile": BehavioralProfile,
        "BehaviorAuditLog": BehaviorAuditLog,
        "BehaviorHistory": BehaviorHistory,
        "BehaviorTrace": BehaviorTrace,
        # 微行动跟踪
        "MicroActionTask": MicroActionTask,
        "MicroActionLog": MicroActionLog,
        # 设备预警
        "DeviceAlert": DeviceAlert,
        # 提醒与教练消息
        "Reminder": Reminder,
        "CoachMessage": CoachMessage,
        # 评估任务与审核
        "AssessmentAssignment": AssessmentAssignment,
        "CoachReviewItem": CoachReviewItem,
        # 挑战/打卡活动
        "ChallengeTemplate": ChallengeTemplate,
        "ChallengeDayPush": ChallengeDayPush,
        "ChallengeEnrollment": ChallengeEnrollment,
        "ChallengeSurveyResponse": ChallengeSurveyResponse,
        "ChallengePushLog": ChallengePushLog,
        # 教练推送审批队列
        "CoachPushQueue": CoachPushQueue,
    }
    return models.get(name)
