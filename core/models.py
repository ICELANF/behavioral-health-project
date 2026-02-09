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
    JSON, ForeignKey, Index, Enum as SQLEnum, text as sa_text
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import uuid

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


# ============================================
# 权威角色等级映射（1-indexed，全局唯一定义）
# 所有后端代码统一引用此表，不得自行定义
# 显示标签: L0-L5 = ROLE_LEVEL值 - 1
# ============================================
ROLE_LEVEL = {
    UserRole.OBSERVER: 1,
    UserRole.GROWER: 2,
    UserRole.SHARER: 3,
    UserRole.COACH: 4,
    UserRole.PROMOTER: 5,
    UserRole.SUPERVISOR: 5,
    UserRole.MASTER: 6,
    UserRole.ADMIN: 99,
    UserRole.SYSTEM: 100,
    # 向后兼容
    UserRole.PATIENT: 2,       # 等同 grower
}

# 字符串版本（供 auth.py 等使用字符串 key 的模块引用）
ROLE_LEVEL_STR = {r.value: lv for r, lv in ROLE_LEVEL.items()}

# 显示标签: L0 观察员 ... L5 大师
ROLE_DISPLAY = {r: f"L{lv - 1}" for r, lv in ROLE_LEVEL.items() if lv < 90}


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
    role = Column(SQLEnum(UserRole), default=UserRole.OBSERVER, nullable=False)

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


class FoodAnalysis(Base):
    """食物识别分析记录"""
    __tablename__ = "food_analyses"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    image_url     = Column(String(500), nullable=False)
    food_name     = Column(String(200), nullable=True)
    calories      = Column(Float, nullable=True)
    protein       = Column(Float, nullable=True)
    fat           = Column(Float, nullable=True)
    carbs         = Column(Float, nullable=True)
    fiber         = Column(Float, nullable=True)
    advice        = Column(Text, nullable=True)
    raw_response  = Column(Text, nullable=True)
    meal_type     = Column(String(20), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FoodAnalysis(id={self.id}, user={self.user_id}, food={self.food_name})>"


# ============================================
# 专家白标租户枚举
# ============================================

# ============================================
# 知识库 RAG 枚举
# ============================================

class EvidenceTier(str, enum.Enum):
    """证据分层"""
    T1 = "T1"  # 临床指南
    T2 = "T2"  # RCT/系统综述
    T3 = "T3"  # 专家共识/意见
    T4 = "T4"  # 个人经验分享

class ContentType(str, enum.Enum):
    """内容类型"""
    GUIDELINE = "guideline"                  # 临床指南
    CONSENSUS = "consensus"                  # 专家共识
    RCT = "rct"                              # 随机对照试验
    REVIEW = "review"                        # 综述/荟萃分析
    EXPERT_OPINION = "expert_opinion"        # 专家意见
    CASE_REPORT = "case_report"              # 病例报告
    EXPERIENCE_SHARING = "experience_sharing" # 个人经验分享

class ReviewStatus(str, enum.Enum):
    """审核状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"

# 证据分层 → priority 映射
TIER_PRIORITY_MAP = {"T1": 9, "T2": 7, "T3": 5, "T4": 3}

class KnowledgeScope(str, enum.Enum):
    """知识库范围"""
    TENANT = "tenant"        # 专家私有
    DOMAIN = "domain"        # 领域知识
    PLATFORM = "platform"    # 平台公共

class DocumentStatus(str, enum.Enum):
    """文档状态"""
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


# ============================================
# 知识库 RAG 模型
# ============================================

class KnowledgeDocument(Base):
    """
    知识库文档表

    存储已入库的文档元数据：标题、作者、来源、范围、状态。
    一个文档对应多个 KnowledgeChunk。
    """
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    author = Column(String(100), nullable=True)
    source = Column(String(200), nullable=True)
    domain_id = Column(String(50), nullable=True, index=True)  # nutrition/sleep/tcm/...
    scope = Column(String(20), nullable=False, default="platform")  # tenant/domain/platform
    tenant_id = Column(String(64), nullable=True, index=True)
    priority = Column(Integer, default=5)  # 1-10, 高=优先
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default="draft")  # draft/processing/ready/error
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(10), nullable=True)     # md/txt/pdf/docx
    file_hash = Column(String(128), nullable=True)    # SHA256 去重
    raw_content = Column(Text, nullable=True)  # 专家编写的原始 Markdown
    chunk_count = Column(Integer, default=0)

    # 内容治理字段
    evidence_tier = Column(String(2), default="T3", server_default="T3", nullable=False)  # T1/T2/T3/T4
    content_type = Column(String(30), nullable=True)  # guideline/consensus/rct/review/expert_opinion/case_report/experience_sharing
    published_date = Column(DateTime, nullable=True)  # 原始材料发布日期
    review_status = Column(String(20), nullable=True)  # pending/approved/rejected/not_required
    reviewer_id = Column(Integer, nullable=True)  # 审核人 User.id
    reviewed_at = Column(DateTime, nullable=True)  # 审核时间
    contributor_id = Column(Integer, nullable=True)  # 贡献者 User.id
    expires_at = Column(DateTime, nullable=True)  # 内容过期时间

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)  # 更新时间

    # 关系
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_kdoc_scope_domain', 'scope', 'domain_id'),
        Index('idx_kdoc_scope_tenant', 'scope', 'tenant_id'),
        Index('idx_kdoc_status', 'status'),
        Index('idx_kdoc_review_status', 'review_status'),
        Index('idx_kdoc_evidence_tier', 'evidence_tier'),
        Index('idx_kdoc_contributor', 'contributor_id'),
    )

    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, title='{self.title}', scope={self.scope})>"


class KnowledgeDomain(Base):
    """知识领域元数据"""
    __tablename__ = "knowledge_domains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(String(50), unique=True, nullable=False, index=True)
    label = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeChunk(Base):
    """
    知识库分块表

    文档切分后的文本块，每块含嵌入向量（JSON 存储，Python 层余弦相似度）。
    冗余 doc_title/doc_author/doc_source 加速检索时组装引用标签。
    """
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False, index=True)

    # 分块内容
    content = Column(Text, nullable=False)
    heading = Column(String(200), nullable=True)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, default=0)

    # 冗余字段 (加速检索)
    doc_title = Column(String(300), nullable=True)
    doc_author = Column(String(100), nullable=True)
    doc_source = Column(String(200), nullable=True)

    # 范围
    scope = Column(String(20), nullable=False, default="platform")
    domain_id = Column(String(50), nullable=True)
    tenant_id = Column(String(64), nullable=True)

    # 嵌入向量 (JSON 文本: [0.01, -0.02, ...])
    embedding = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    document = relationship("KnowledgeDocument", back_populates="chunks")

    __table_args__ = (
        Index('idx_kchunk_doc', 'document_id'),
        Index('idx_kchunk_scope_domain', 'scope', 'domain_id'),
        Index('idx_kchunk_scope_tenant', 'scope', 'tenant_id'),
    )

    def __repr__(self):
        return f"<KnowledgeChunk(id={self.id}, doc={self.document_id}, idx={self.chunk_index})>"


class KnowledgeCitation(Base):
    """
    知识库引用审计表

    记录每次 LLM 回复中实际引用了哪些知识块，
    用于审计追踪和统计文档使用频率。
    """
    __tablename__ = "knowledge_citations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=True)
    message_id = Column(String(100), nullable=True)
    agent_id = Column(String(50), nullable=True)
    tenant_id = Column(String(64), nullable=True)
    user_id = Column(String(50), nullable=True)

    chunk_id = Column(Integer, nullable=False)
    document_id = Column(Integer, nullable=False)
    query_text = Column(String(500), nullable=True)
    relevance_score = Column(Float, nullable=True)
    rank_position = Column(Integer, nullable=True)
    citation_text = Column(String(500), nullable=True)
    citation_label = Column(String(300), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_kcite_session', 'session_id'),
        Index('idx_kcite_doc', 'document_id'),
        Index('idx_kcite_chunk', 'chunk_id'),
    )

    def __repr__(self):
        return f"<KnowledgeCitation(id={self.id}, chunk={self.chunk_id}, score={self.relevance_score})>"


# ============================================
# 内容交互枚举
# ============================================

class ContentItemStatus(str, enum.Enum):
    """内容条目状态"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class CommentStatus(str, enum.Enum):
    """评论状态"""
    ACTIVE = "active"
    HIDDEN = "hidden"
    DELETED = "deleted"

# ============================================
# 学习系统枚举
# ============================================

class LearningStatus(str, enum.Enum):
    """学习进度状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class PointsCategory(str, enum.Enum):
    """积分类别"""
    GROWTH = "growth"
    CONTRIBUTION = "contribution"
    INFLUENCE = "influence"

# ============================================
# 考试系统枚举
# ============================================

class ExamStatus(str, enum.Enum):
    """考试状态"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ExamResultStatus(str, enum.Enum):
    """考试结果状态"""
    PASSED = "passed"
    FAILED = "failed"

class ExamQuestionType(str, enum.Enum):
    """考试题目类型（区别于问卷 QuestionType）"""
    SINGLE = "single"
    MULTIPLE = "multiple"
    TRUEFALSE = "truefalse"
    SHORT_ANSWER = "short_answer"

# ============================================
# 批量灌注枚举
# ============================================

class IngestionStatus(str, enum.Enum):
    """灌注任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# ============================================
# 内容交互模型
# ============================================

class ContentItem(Base):
    """统一内容条目表"""
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(30), nullable=False, index=True)  # article/video/course/card/case
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    media_url = Column(String(500), nullable=True)
    domain = Column(String(50), nullable=True, index=True)  # nutrition/exercise/sleep/emotion/...
    level = Column(String(10), nullable=True)  # L0-L5
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String(64), nullable=True, index=True)
    status = Column(String(20), default="draft", nullable=False, index=True)  # draft/published/archived

    # 统计计数 (反范式，高效读取)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    collect_count = Column(Integer, default=0)

    # 是否含测试
    has_quiz = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_ci_type_status', 'content_type', 'status'),
        Index('idx_ci_domain_level', 'domain', 'level'),
        Index('idx_ci_author', 'author_id'),
    )

    def __repr__(self):
        return f"<ContentItem(id={self.id}, type={self.content_type}, title='{self.title}')>"


class ContentLike(Base):
    """内容点赞表"""
    __tablename__ = "content_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_cl_user_content', 'user_id', 'content_id', unique=True),
    )


class ContentBookmark(Base):
    """内容收藏表"""
    __tablename__ = "content_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_cb_user_content', 'user_id', 'content_id', unique=True),
    )


class ContentComment(Base):
    """内容评论表"""
    __tablename__ = "content_comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("content_items.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("content_comments.id"), nullable=True)  # 自引用回复
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 评分
    like_count = Column(Integer, default=0)
    status = Column(String(20), default="active", nullable=False)  # active/hidden/deleted

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_cc_content_status', 'content_id', 'status'),
    )

    def __repr__(self):
        return f"<ContentComment(id={self.id}, user={self.user_id}, content={self.content_id})>"


# ============================================
# 学习持久化模型
# ============================================

class LearningProgress(Base):
    """学习进度表"""
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("content_items.id"), nullable=False, index=True)
    progress_percent = Column(Float, default=0.0)  # 0-100
    last_position = Column(String(50), nullable=True)  # 视频时间点或章节位置
    time_spent_seconds = Column(Integer, default=0)
    status = Column(String(20), default="not_started")  # not_started/in_progress/completed

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_lp_user_content', 'user_id', 'content_id', unique=True),
        Index('idx_lp_status', 'status'),
    )


class LearningTimeLog(Base):
    """学习时长日志"""
    __tablename__ = "learning_time_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content_id = Column(Integer, nullable=True)
    domain = Column(String(50), nullable=True)
    minutes = Column(Integer, nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_ltl_user_date', 'user_id', 'earned_at'),
    )


class LearningPointsLog(Base):
    """学习积分日志"""
    __tablename__ = "learning_points_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # quiz/complete/share/comment/daily_login/streak
    source_id = Column(String(50), nullable=True)  # 关联的内容/考试ID
    points = Column(Integer, nullable=False)
    category = Column(String(20), nullable=False)  # growth/contribution/influence
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_lpl_user_cat', 'user_id', 'category'),
        Index('idx_lpl_user_date', 'user_id', 'earned_at'),
    )


class UserLearningStats(Base):
    """用户学习统计汇总(反范式)"""
    __tablename__ = "user_learning_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    # 时长
    total_minutes = Column(Integer, default=0)

    # 积分
    total_points = Column(Integer, default=0)
    growth_points = Column(Integer, default=0)
    contribution_points = Column(Integer, default=0)
    influence_points = Column(Integer, default=0)

    # 打卡连续
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_learn_date = Column(String(10), nullable=True)  # YYYY-MM-DD

    # 考试
    quiz_total = Column(Integer, default=0)
    quiz_passed = Column(Integer, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_uls_points', 'total_points'),
    )

    def __repr__(self):
        return f"<UserLearningStats(user={self.user_id}, pts={self.total_points}, min={self.total_minutes})>"


# ============================================
# 考试系统模型
# ============================================

class ExamDefinition(Base):
    """考试定义表"""
    __tablename__ = "exam_definitions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(String(50), unique=True, nullable=False, index=True)  # 业务ID
    exam_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(String(10), nullable=True)  # L0-L5
    exam_type = Column(String(30), default="standard")  # standard/certification/practice
    passing_score = Column(Integer, default=60)
    duration_minutes = Column(Integer, default=60)
    max_attempts = Column(Integer, default=3)
    question_ids = Column(JSON, nullable=True)  # [q_id, q_id, ...]
    status = Column(String(20), default="draft", nullable=False)  # draft/published/archived
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_exam_status', 'status'),
        Index('idx_exam_level', 'level'),
    )

    def __repr__(self):
        return f"<ExamDefinition(exam_id={self.exam_id}, name='{self.exam_name}')>"


class QuestionBank(Base):
    """题库表"""
    __tablename__ = "question_bank"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String(50), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)  # 题目内容
    question_type = Column(String(20), nullable=False)  # single/multiple/truefalse/short_answer
    options = Column(JSON, nullable=True)  # [{"key": "A", "text": "..."}, ...]
    answer = Column(JSON, nullable=False)  # ["A"] or ["A","C"] or "true" or "简答内容"
    explanation = Column(Text, nullable=True)  # 解析
    domain = Column(String(50), nullable=True)
    difficulty = Column(String(20), default="medium")  # easy/medium/hard
    tags = Column(JSON, nullable=True)  # ["nutrition", "L2"]
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_qb_type', 'question_type'),
        Index('idx_qb_domain', 'domain'),
    )

    def __repr__(self):
        return f"<QuestionBank(q_id={self.question_id}, type={self.question_type})>"


class ExamResult(Base):
    """考试结果表"""
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exam_id = Column(String(50), nullable=False, index=True)
    attempt_number = Column(Integer, default=1)
    score = Column(Integer, nullable=False)
    status = Column(String(10), nullable=False)  # passed/failed
    answers = Column(JSON, nullable=True)  # {"q1": "A", "q2": ["B","C"], ...}
    duration_seconds = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_er_user_exam', 'user_id', 'exam_id'),
        Index('idx_er_status', 'status'),
    )

    def __repr__(self):
        return f"<ExamResult(user={self.user_id}, exam={self.exam_id}, score={self.score})>"


# ============================================
# 用户活动追踪模型
# ============================================

class UserActivityLog(Base):
    """用户活动日志表"""
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_type = Column(String(30), nullable=False, index=True)  # login/share/learn/comment/like/exam/assess
    detail = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_ual_user_type', 'user_id', 'activity_type'),
        Index('idx_ual_user_date', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<UserActivityLog(user={self.user_id}, type={self.activity_type})>"


# ============================================
# 批量知识灌注模型
# ============================================

class BatchIngestionJob(Base):
    """批量灌注任务表"""
    __tablename__ = "batch_ingestion_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(300), nullable=False)
    file_type = Column(String(20), nullable=False)  # zip/pdf/docx/md/txt/7z/rar
    status = Column(String(20), default="pending", nullable=False)  # pending/processing/completed/failed
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    result_doc_ids = Column(JSON, nullable=True)  # 创建的 KnowledgeDocument IDs

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_bij_status', 'status'),
        Index('idx_bij_user', 'user_id'),
    )

    def __repr__(self):
        return f"<BatchIngestionJob(id={self.id}, file={self.filename}, status={self.status})>"


class TenantStatus(str, enum.Enum):
    """租户状态"""
    trial = "trial"
    active = "active"
    suspended = "suspended"
    archived = "archived"

class TenantTier(str, enum.Enum):
    """合作等级"""
    basic = "basic_partner"
    premium = "premium_partner"
    strategic = "strategic_partner"

class ClientStatus(str, enum.Enum):
    """客户状态"""
    active = "active"
    graduated = "graduated"
    paused = "paused"
    exited = "exited"


# ============================================
# 专家白标租户模型
# ============================================

class ExpertTenant(Base):
    """
    每个入驻专家 = 一个租户
    一个专家对应一套独立品牌、Agent配置、客户群
    """
    __tablename__ = "expert_tenants"

    id = Column(String(64), primary_key=True, comment="租户ID, 如 dr-chen-endo")
    expert_user_id = Column(
        Integer, ForeignKey("users.id"),
        nullable=False, index=True,
        comment="专家在平台的用户ID"
    )

    # 品牌配置
    brand_name = Column(String(128), nullable=False, comment="工作室名称")
    brand_tagline = Column(String(256), default="", comment="品牌标语")
    brand_avatar = Column(String(16), default="🏥", comment="Emoji头像")
    brand_logo_url = Column(String(512), default="", comment="Logo图片URL")
    brand_colors = Column(JSON, nullable=False, default=dict, comment='{"primary":"#hex","accent":"#hex","bg":"#hex"}')
    brand_theme_id = Column(String(32), default="default", comment="主题模板ID")
    custom_domain = Column(String(256), default="", comment="自定义域名")

    # 专家人设
    expert_title = Column(String(64), default="", comment="专家头衔")
    expert_self_intro = Column(Text, default="", comment="专家自我介绍")
    expert_specialties = Column(JSON, default=list, comment='["内分泌","代谢管理"]')
    expert_credentials = Column(JSON, default=list, comment='["主任医师","博士生导师"]')

    # Agent 配置
    enabled_agents = Column(JSON, nullable=False, default=list, comment="启用的Agent ID列表")
    agent_persona_overrides = Column(JSON, default=dict, comment="Agent话术覆盖")

    # 业务配置
    enabled_paths = Column(JSON, default=list, comment="启用的学习路径ID")
    service_packages = Column(JSON, default=list, comment="服务包配置")
    questionnaire_overrides = Column(JSON, default=dict, comment="问卷增删题配置")
    welcome_message = Column(Text, default="", comment="客户首次进入的欢迎语")

    # 控制
    status = Column(SQLEnum(TenantStatus), default=TenantStatus.trial, nullable=False, index=True)
    tier = Column(SQLEnum(TenantTier), default=TenantTier.basic, nullable=False)
    max_clients = Column(Integer, default=50, comment="客户数上限")
    revenue_share_expert = Column(Float, default=0.80, comment="专家分成比例")
    trial_expires_at = Column(DateTime, nullable=True, comment="试用到期时间")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    clients = relationship("TenantClient", back_populates="tenant", lazy="dynamic")
    agent_mappings = relationship("TenantAgentMapping", back_populates="tenant", lazy="selectin")

    __table_args__ = (
        Index("idx_tenant_status", "status"),
        Index("idx_tenant_expert_user", "expert_user_id"),
    )

    def __repr__(self):
        return f"<ExpertTenant {self.id}: {self.brand_name}>"

    @property
    def is_active(self) -> bool:
        return self.status == TenantStatus.active


class TenantClient(Base):
    """专家的客户 — 关联平台用户 + 租户归属"""
    __tablename__ = "tenant_clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), ForeignKey("expert_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="平台统一用户ID")

    source = Column(String(32), default="expert_referred", comment="来源")
    service_package = Column(String(64), default="trial", comment="购买的服务包ID")

    status = Column(SQLEnum(ClientStatus), default=ClientStatus.active, nullable=False, index=True)
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    graduated_at = Column(DateTime, nullable=True)

    total_sessions = Column(Integer, default=0, comment="累计会话次数")
    last_active_at = Column(DateTime, nullable=True)
    notes = Column(Text, default="", comment="专家备注")

    tenant = relationship("ExpertTenant", back_populates="clients")

    __table_args__ = (
        Index("idx_tc_tenant_status", "tenant_id", "status"),
    )

    def __repr__(self):
        return f"<TenantClient tenant={self.tenant_id} user={self.user_id}>"


class TenantAgentMapping(Base):
    """租户 x Agent 的详细配置"""
    __tablename__ = "tenant_agent_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), ForeignKey("expert_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(32), nullable=False, comment="Agent标识: sleep/glucose/stress/...")

    display_name = Column(String(64), default="", comment="自定义显示名")
    display_avatar = Column(String(16), default="", comment="自定义Emoji头像")
    greeting = Column(Text, default="", comment="自定义开场白")
    tone = Column(String(128), default="", comment="语气风格描述")
    bio = Column(String(256), default="", comment="Agent简介")

    is_enabled = Column(Boolean, default=True, nullable=False)
    is_primary = Column(Boolean, default=False, comment="是否为主力Agent")
    sort_order = Column(Integer, default=0, comment="排序权重")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("ExpertTenant", back_populates="agent_mappings")

    __table_args__ = (
        Index("idx_tam_tenant_enabled", "tenant_id", "is_enabled"),
    )

    def __repr__(self):
        return f"<TenantAgentMapping {self.tenant_id}:{self.agent_id}>"


class TenantAuditLog(Base):
    """租户操作审计日志"""
    __tablename__ = "tenant_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), ForeignKey("expert_tenants.id"), nullable=False, index=True)
    actor_id = Column(Integer, nullable=False, comment="操作者用户ID")
    action = Column(String(64), nullable=False, comment="操作类型")
    detail = Column(JSON, default=dict, comment="操作详情")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_audit_tenant_time", "tenant_id", "created_at"),
    )


# ============================================
# 通用问卷引擎模型 (v22)
# ============================================

class SurveyStatus(str, enum.Enum):
    """问卷状态"""
    draft = "draft"
    published = "published"
    closed = "closed"
    archived = "archived"

class SurveyType(str, enum.Enum):
    """问卷类型"""
    general = "general"
    health = "health"
    satisfaction = "satisfaction"
    screening = "screening"
    feedback = "feedback"
    registration = "registration"

class QuestionType(str, enum.Enum):
    """题目类型"""
    single_choice = "single_choice"
    multiple_choice = "multiple_choice"
    text_short = "text_short"
    text_long = "text_long"
    rating = "rating"
    nps = "nps"
    slider = "slider"
    matrix_single = "matrix_single"
    matrix_multiple = "matrix_multiple"
    date = "date"
    file_upload = "file_upload"
    section_break = "section_break"
    description = "description"

class DistributionChannel(str, enum.Enum):
    """分发渠道"""
    link = "link"
    qrcode = "qrcode"
    wechat = "wechat"
    sms = "sms"
    email = "email"
    embed = "embed"
    coach = "coach"


class Survey(Base):
    """问卷主表"""
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="问卷标题")
    description = Column(Text, default="", comment="问卷说明")
    survey_type = Column(SQLEnum(SurveyType), default=SurveyType.general)
    status = Column(SQLEnum(SurveyStatus), default=SurveyStatus.draft)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String(64), ForeignKey("expert_tenants.id"), nullable=True)

    settings = Column(JSON, default=dict, comment="问卷设置 JSON")
    baps_mapping = Column(JSON, nullable=True, comment="BAPS回流映射")

    response_count = Column(Integer, default=0)
    avg_duration = Column(Integer, default=0, comment="平均填写秒数")

    short_code = Column(String(8), unique=True, index=True, comment="短链码")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # relationships
    questions = relationship("SurveyQuestion", back_populates="survey", cascade="all, delete-orphan", order_by="SurveyQuestion.sort_order")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")
    distributions = relationship("SurveyDistribution", back_populates="survey", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_surveys_status", "status"),
        Index("idx_surveys_created_by", "created_by"),
        Index("idx_surveys_tenant", "tenant_id"),
    )


class SurveyQuestion(Base):
    """问卷题目表"""
    __tablename__ = "survey_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    question_type = Column(SQLEnum(QuestionType), nullable=False)
    sort_order = Column(Integer, default=0)

    title = Column(Text, nullable=False, comment="题干")
    description = Column(Text, default="", comment="题目说明")
    is_required = Column(Boolean, default=False)

    config = Column(JSON, default=dict, comment="题目配置 JSON")
    skip_logic = Column(JSON, nullable=True, comment="跳题逻辑 JSON")

    created_at = Column(DateTime, default=datetime.utcnow)

    survey = relationship("Survey", back_populates="questions")
    answers = relationship("SurveyResponseAnswer", back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sq_survey", "survey_id", "sort_order"),
    )


class SurveyResponse(Base):
    """问卷回收表"""
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="匿名时为null")

    respondent_ip = Column(String(45), nullable=True)
    respondent_ua = Column(String(500), nullable=True)
    device_type = Column(String(20), default="unknown")

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_sec = Column(Integer, nullable=True, comment="填写耗时秒")

    is_complete = Column(Boolean, default=False)
    current_page = Column(Integer, default=0, comment="断点续填页码")

    baps_synced = Column(Boolean, default=False)
    baps_synced_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    survey = relationship("Survey", back_populates="responses")
    answers = relationship("SurveyResponseAnswer", back_populates="response", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sr_survey", "survey_id"),
        Index("idx_sr_user", "user_id"),
        Index("idx_sr_complete", "survey_id", "is_complete"),
    )


class SurveyResponseAnswer(Base):
    """问卷逐题答案"""
    __tablename__ = "survey_response_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    response_id = Column(Integer, ForeignKey("survey_responses.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("survey_questions.id", ondelete="CASCADE"), nullable=False)

    answer_value = Column(JSON, nullable=False, comment="答案 JSON")
    score = Column(Float, nullable=True, comment="自动评分")

    created_at = Column(DateTime, default=datetime.utcnow)

    response = relationship("SurveyResponse", back_populates="answers")
    question = relationship("SurveyQuestion", back_populates="answers")

    __table_args__ = (
        Index("idx_sra_response", "response_id"),
        Index("idx_sra_question", "question_id"),
        Index("idx_sra_unique", "response_id", "question_id", unique=True),
    )


class SurveyDistribution(Base):
    """问卷分发渠道"""
    __tablename__ = "survey_distributions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    channel = Column(SQLEnum(DistributionChannel), nullable=False)

    channel_config = Column(JSON, default=dict, comment="渠道配置 JSON")
    tracking_code = Column(String(20), unique=True, comment="渠道追踪码")

    click_count = Column(Integer, default=0)
    submit_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    survey = relationship("Survey", back_populates="distributions")


# ============================================
# V002 学分晋级体系模型
# ============================================

class CourseModuleType(str, enum.Enum):
    """课程模块类型"""
    M1_KNOWLEDGE = "M1"       # 知识学习
    M2_SKILL = "M2"           # 技能训练
    M3_PRACTICE = "M3"        # 实践应用
    M4_ASSESSMENT = "M4"      # 考核评估
    ELECTIVE = "ELECTIVE"     # 选修

class ElectiveCategory(str, enum.Enum):
    """选修课分类"""
    BEHAVIOR = "behavior"             # 行为科学
    NUTRITION = "nutrition"           # 营养学
    EXERCISE = "exercise"             # 运动科学
    PSYCHOLOGY = "psychology"         # 心理学
    TCM = "tcm"                       # 中医养生
    COMMUNICATION = "communication"   # 沟通技巧
    DATA_LITERACY = "data_literacy"   # 数据素养
    ETHICS = "ethics"                 # 伦理规范

class InterventionTier(str, enum.Enum):
    """干预层级"""
    T1 = "T1"  # 基础科普
    T2 = "T2"  # 循证指导
    T3 = "T3"  # 专业干预
    T4 = "T4"  # 专家督导

class AssessmentEvidenceType(str, enum.Enum):
    """评估证据类型"""
    QUIZ = "quiz"               # 在线测验
    CASE_REPORT = "case_report" # 案例报告
    PEER_REVIEW = "peer_review" # 同伴评审
    SUPERVISOR = "supervisor"   # 督导评估
    EXAM = "exam"               # 正式考试

class CompanionStatus(str, enum.Enum):
    """同道者关系状态"""
    ACTIVE = "active"
    GRADUATED = "graduated"
    DROPPED = "dropped"

class PromotionStatus(str, enum.Enum):
    """晋级申请状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CourseModule(Base):
    """课程模块 — V002学分体系核心表"""
    __tablename__ = "course_modules"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=sa_text("gen_random_uuid()"))
    code = Column(String(30), unique=True, nullable=False, comment="模块编码 OBS-M1-01")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    module_type = Column(String(20), nullable=False, comment="M1/M2/M3/M4/ELECTIVE")
    elective_cat = Column(String(30), nullable=True, comment="选修课分类")
    tier = Column(String(5), nullable=True, comment="T1-T4证据层级")
    target_role = Column(SQLEnum(UserRole, create_type=False), nullable=False,
                         comment="目标角色等级")

    credit_value = Column(Float, nullable=False, default=1.0, comment="学分值")
    theory_ratio = Column(String(10), nullable=True, comment="理论实践比例")
    prereq_modules = Column(JSON, nullable=True, default=list, comment="前置模块code列表")
    content_ref = Column(String(500), nullable=True, comment="内容引用")

    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    credits = relationship("UserCredit", back_populates="module", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_cm_role_type", "target_role", "module_type"),
        Index("idx_cm_code", "code", unique=True),
    )


class UserCredit(Base):
    """用户学分记录"""
    __tablename__ = "user_credits"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=sa_text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(PG_UUID(as_uuid=True), ForeignKey("course_modules.id", ondelete="CASCADE"),
                       nullable=False)

    credit_earned = Column(Float, nullable=False, comment="获得学分")
    score = Column(Float, nullable=True, comment="成绩 0-100")
    completed_at = Column(DateTime, default=datetime.utcnow)
    evidence_type = Column(String(30), nullable=True, comment="评估证据类型")
    evidence_ref = Column(String(500), nullable=True, comment="证据材料URL")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    module = relationship("CourseModule", back_populates="credits")

    __table_args__ = (
        Index("idx_uc_user", "user_id"),
        Index("idx_uc_module", "module_id"),
        Index("idx_uc_user_module", "user_id", "module_id"),
    )


class CompanionRelation(Base):
    """同道者带教关系"""
    __tablename__ = "companion_relations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=sa_text("gen_random_uuid()"))
    mentor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mentee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    mentor_role = Column(String(20), nullable=False, comment="带教时导师角色")
    mentee_role = Column(String(20), nullable=False, comment="带教时学员角色")
    status = Column(String(20), default="active", comment="active/graduated/dropped")

    quality_score = Column(Float, nullable=True, comment="带教质量评分 1-5")
    started_at = Column(DateTime, default=datetime.utcnow)
    graduated_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_cr_mentor", "mentor_id"),
        Index("idx_cr_mentee", "mentee_id"),
        Index("idx_cr_status", "status"),
        Index("idx_cr_mentor_mentee", "mentor_id", "mentee_id", unique=True),
    )


class PromotionApplication(Base):
    """晋级申请"""
    __tablename__ = "promotion_applications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=sa_text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    from_role = Column(String(20), nullable=False)
    to_role = Column(String(20), nullable=False)
    status = Column(String(20), default="pending", comment="pending/approved/rejected")

    # 四维快照
    credit_snapshot = Column(JSON, nullable=True)
    point_snapshot = Column(JSON, nullable=True)
    companion_snapshot = Column(JSON, nullable=True)
    practice_snapshot = Column(JSON, nullable=True)
    check_result = Column(JSON, nullable=True, comment="晋级校验详细结果")

    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_pa_user", "user_id"),
        Index("idx_pa_status", "status"),
        Index("idx_pa_user_status", "user_id", "status"),
    )


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
        # 食物识别
        "food_analyses",
        # 知识库 RAG
        "knowledge_documents",
        "knowledge_chunks",
        "knowledge_citations",
        # 专家白标租户
        "expert_tenants",
        "tenant_clients",
        "tenant_agent_mappings",
        "tenant_audit_logs",
        # 内容交互
        "content_items",
        "content_likes",
        "content_bookmarks",
        "content_comments",
        # 学习持久化
        "learning_progress",
        "learning_time_logs",
        "learning_points_logs",
        "user_learning_stats",
        # 考试系统
        "exam_definitions",
        "question_bank",
        "exam_results",
        # 用户活动追踪
        "user_activity_logs",
        # 批量灌注
        "batch_ingestion_jobs",
        # 问卷引擎
        "surveys",
        "survey_questions",
        "survey_responses",
        "survey_response_answers",
        "survey_distributions",
        # V002 学分晋级体系
        "course_modules",
        "user_credits",
        "companion_relations",
        "promotion_applications",
        # V003 激励体系
        "badges",
        "user_badges",
        "user_milestones",
        "user_streaks",
        "flip_card_records",
        "nudge_records",
        "user_memorials",
        # 积分系统
        "point_transactions",
        "user_points",
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
        # 食物识别
        "FoodAnalysis": FoodAnalysis,
        # 知识库 RAG
        "KnowledgeDocument": KnowledgeDocument,
        "KnowledgeChunk": KnowledgeChunk,
        "KnowledgeCitation": KnowledgeCitation,
        # 专家白标租户
        "ExpertTenant": ExpertTenant,
        "TenantClient": TenantClient,
        "TenantAgentMapping": TenantAgentMapping,
        "TenantAuditLog": TenantAuditLog,
        # 内容交互
        "ContentItem": ContentItem,
        "ContentLike": ContentLike,
        "ContentBookmark": ContentBookmark,
        "ContentComment": ContentComment,
        # 学习持久化
        "LearningProgress": LearningProgress,
        "LearningTimeLog": LearningTimeLog,
        "LearningPointsLog": LearningPointsLog,
        "UserLearningStats": UserLearningStats,
        # 考试系统
        "ExamDefinition": ExamDefinition,
        "QuestionBank": QuestionBank,
        "ExamResult": ExamResult,
        # 用户活动
        "UserActivityLog": UserActivityLog,
        # 批量灌注
        "BatchIngestionJob": BatchIngestionJob,
        # 问卷引擎
        "Survey": Survey,
        "SurveyQuestion": SurveyQuestion,
        "SurveyResponse": SurveyResponse,
        "SurveyResponseAnswer": SurveyResponseAnswer,
        "SurveyDistribution": SurveyDistribution,
        # V002 学分晋级
        "CourseModule": CourseModule,
        "UserCredit": UserCredit,
        "CompanionRelation": CompanionRelation,
        "PromotionApplication": PromotionApplication,
    }
    return models.get(name)
