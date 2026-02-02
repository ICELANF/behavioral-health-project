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
    """用户角色"""
    PATIENT = "patient"      # 患者
    COACH = "coach"          # 健康教练
    ADMIN = "admin"          # 管理员
    SYSTEM = "system"        # 系统账号


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
        # 行为审计 + 历史 + 长期记忆
        "behavior_audit_logs",
        "behavior_history",
        "behavior_traces",
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
        "BehaviorAuditLog": BehaviorAuditLog,
        "BehaviorHistory": BehaviorHistory,
        "BehaviorTrace": BehaviorTrace,
    }
    return models.get(name)
