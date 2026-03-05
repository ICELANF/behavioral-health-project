# ── C4 权威源声明 ────────────────────────────────────────
# | 字段           | 权威源 (SOURCE OF TRUTH) | 缓存 (SNAPSHOT)    |
# |current_stage   | JourneyStageV4           | User.current_stage |
# |agency_mode     | JourneyStageV4           | User.agency_mode   |
# |agency_score    | JourneyStageV4           | User.agency_score  |
# |trust_score     | JourneyStageV4           | User.trust_score   |
# 写入规则: 先写权威源 → FieldSyncGuard 自动同步缓存
# ────────────────────────────────────────────────────────
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Float, Boolean,
    JSON, ForeignKey, Index, Enum as SQLEnum, text as sa_text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import uuid

# 🔥 新�：�� pgvector ��
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

Base = declarative_base()


# ============================================
# 枚举类型定义
# ============================================

class UserRole(str, enum.Enum):
    """
    用户角色 - v18统一角色层级

    行为健康晋级序列（从低到高）�
    L0: 观察� (observer)
    L1: 成长� (grower) - 原患�
    L2: 分享� (sharer)
    L3: 健康教练 (coach)
    L4: 促进� (promoter) / 督� (supervisor) - 平级平权
    L5: 大师 (master)
    L99: 管理� (admin)
    """
    # 行为健康晋级序列
    OBSERVER = "observer"        # L0 行为健康观察�
    GROWER = "grower"            # L1 成长者（原患者）
    SHARER = "sharer"            # L2 分享�
    COACH = "coach"              # L3 健康教练
    PROMOTER = "promoter"        # L4 行为健康促进�
    SUPERVISOR = "supervisor"    # L4 督�专家（与促进师平级�
    MASTER = "master"            # L5 行为健康促进大师

    # 系统角色
    ADMIN = "admin"              # L99 系统管理�
    INSTITUTION_ADMIN = "institution_admin"  # 机构管理员 (V5.3.0 Migration 055)
    SYSTEM = "system"            # 系统账号

    # 旧�色（向后兼容，映射到新角色�
    PATIENT = "patient"          # 已废� � 映射� grower


# ============================================
# 权威角色等级映射�1-indexed，全���定义�
# �有后�代码统一引用此表，不得自行定�
# 显示标�: L0-L5 = ROLE_LEVEL� - 1
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
    # 向后兼�
    UserRole.PATIENT: 2,       # 等同 grower
}

# 字�串版本（供 auth.py 等使用字符串 key 的模块引��
ROLE_LEVEL_STR = {r.value: lv for r, lv in ROLE_LEVEL.items()}

# 显示标�: L0 观察� ... L5 大师
ROLE_DISPLAY = {r: f"L{lv - 1}" for r, lv in ROLE_LEVEL.items() if lv < 90}


class AgencyMode(str, enum.Enum):
    """V4.0 主体性三态模� � agency_mode"""
    PASSIVE = "passive"            # ��: <0.3, Agent=照料�
    TRANSITIONAL = "transitional"  # 过渡: 0.3-0.6, Agent=同��
    ACTIVE = "active"              # 主动: >0.6, Agent=镜子/临在�


class JourneyStageV4(str, enum.Enum):
    """V4.0 成长者S0-S5阶�化执�结�"""
    S0_AUTHORIZATION = "s0_authorization"    # 授权进入
    S1_AWARENESS = "s1_awareness"            # 觉察与稳定期
    S2_TRIAL = "s2_trial"                    # 尝试与波动期
    S3_PATHWAY = "s3_pathway"                # 形成�径期
    S4_INTERNALIZATION = "s4_internalization" # 内化�
    S5_GRADUATION = "s5_graduation"          # �出期(毕业)


class RiskLevel(str, enum.Enum):
    """风险等级"""
    R0 = "R0"  # 正常
    R1 = "R1"  # 轻度
    R2 = "R2"  # ��
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
    PHYSIOLOGICAL = "physiological"  # 生理�
    PSYCHOLOGICAL = "psychological"  # 心理�
    BEHAVIORAL = "behavioral"        # 行为�
    ENVIRONMENTAL = "environmental"  # �境类


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
    用户�

    存储用户基本信息、�证��、用户画�
    """
    __tablename__ = "users"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    # FIX-17: 对�暴露的 UUID (防� ID 枚举)
    public_id = Column(PG_UUID(as_uuid=True), server_default=sa_text("gen_random_uuid()"), unique=True, index=True)

    # 基本信息
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True)

    # 认证信息
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # 角色与权�
    role = Column(SQLEnum(UserRole), default=UserRole.OBSERVER, nullable=False)

    # �人信�
    full_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)

    # 用户画像（JSON存储�
    profile = Column(JSON, nullable=True, default={})
    # 示例结构�
    # {
    #   "age": 45,
    #   "chronic_conditions": ["diabetes", "hypertension"],
    #   "medications": ["metformin"],
    #   "goals": ["weight_loss", "glucose_control"],
    #   "preferences": {"notification_time": "09:00"}
    # }

    # v3 扩展字�
    nickname = Column(String(64), nullable=True, default="")
    avatar_url = Column(String(256), nullable=True, default="")
    health_competency_level = Column(String(4), nullable=True, default="Lv0")
    # DEPRECATED: 使用 JourneyState.journey_stage � BehavioralProfile.current_stage
    current_stage = Column(String(4), nullable=True, default="S0")
    growth_level = Column(String(4), nullable=True, default="G0")

    # WeChat (physical columns exist in DB since migration 044)
    wx_openid = Column(String(100), unique=True, nullable=True, index=True)
    union_id = Column(String(100), unique=True, nullable=True, index=True)
    wx_miniprogram_openid = Column(String(100), unique=True, nullable=True)
    preferred_channel = Column(String(20), default="app", nullable=True)
    growth_points = Column(Integer, default=0, server_default="0")

    # V4.0 主体性 & 信任
    agency_mode = Column(String(20), default="passive")        # passive/transitional/active
    agency_score = Column(Float, default=0.0)                  # 0.0-1.0
    trust_score = Column(Float, default=0.0)                   # 0.0-1.0
    coach_intent = Column(Boolean, default=False)              # 教练意向标�
    conversion_type = Column(String(30), nullable=True)        # curiosity/time/coach_referred
    conversion_source = Column(String(30), nullable=True)      # self/community/institution/paid

    # 健康指标
    adherence_rate = Column(Float, default=0.0)  # 依从性百分比
    last_assessment_date = Column(DateTime, nullable=True)

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)
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
    评估记录�

    存储每�L2评估的完整结�
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

    # 用户画像�照（评估时的状�）
    user_profile_snapshot = Column(JSON, nullable=True)

    # 风险评估结果
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0-100
    primary_concern = Column(String(200), nullable=True)
    urgency = Column(String(20), nullable=True)  # immediate/high/moderate/low
    severity_distribution = Column(JSON, nullable=True)  # {"critical": 1, "high": 2, ...}
    reasoning = Column(Text, nullable=True)

    # �由决�
    primary_agent = Column(SQLEnum(AgentType), nullable=False)
    secondary_agents = Column(JSON, nullable=True)  # ["StressAgent", "SleepAgent"]
    priority = Column(Integer, nullable=False)  # 1-4
    response_time = Column(String(50), nullable=True)  # "立即", "1小时�"
    routing_reasoning = Column(Text, nullable=True)
    recommended_actions = Column(JSON, nullable=True)  # ["行动1", "行动2"]

    # 执�状�
    status = Column(String(20), default="pending")  # pending/processing/completed/failed

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # 元数�
    context = Column(JSON, nullable=True)  # 额�上下文信息

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
    Trigger记录�

    存储每�评估识�出的Trigger
    """
    __tablename__ = "trigger_records"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 外键
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False, index=True)

    # Trigger信息
    tag_id = Column(String(50), nullable=False, index=True)  # high_glucose
    name = Column(String(100), nullable=False)  # 高��
    category = Column(SQLEnum(TriggerCategory), nullable=False)
    severity = Column(SQLEnum(TriggerSeverity), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # 0.0-1.0

    # 元数�（使用trigger_metadata避免与SQLAlchemy的metadata冲突�
    trigger_metadata = Column("metadata", JSON, nullable=True)
    # 示例：{"max_glucose": 13.5, "threshold": 10.0, "detection_method": "signal"}

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

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
    干��录�

    存储针�评估结果的干�措施和执�情�
    """
    __tablename__ = "interventions"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 外键
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False, index=True)

    # 干�信�
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    intervention_type = Column(String(50), nullable=True)  # education/medication_review/counseling

    # 干�内�
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    actions = Column(JSON, nullable=True)  # 具体行动步�

    # 执�状�
    status = Column(String(20), default="pending")  # pending/sent/acknowledged/completed/skipped

    # 用户反�
    user_feedback = Column(Text, nullable=True)
    feedback_score = Column(Integer, nullable=True)  # 1-5
    completed = Column(Boolean, default=False)

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
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
    用户会话�

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

    # 客户�信息
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_info = Column(JSON, nullable=True)

    # 会话状�
    is_active = Column(Boolean, default=True, index=True)

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_activity_at = Column(DateTime, server_default=func.now(), nullable=False)

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
    健康数据�

    存储用户的连�健康监测数据
    """
    __tablename__ = "health_data"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 外键
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 数据类型
    data_type = Column(String(50), nullable=False, index=True)  # glucose/hrv/activity/sleep

    # 数据�
    value = Column(Float, nullable=True)
    values = Column(JSON, nullable=True)  # 用于存储数组或�杂数据

    # 单位和元数据
    unit = Column(String(20), nullable=True)  # mmol/L, ms, steps
    data_metadata = Column("metadata", JSON, nullable=True)

    # 来源
    source = Column(String(50), nullable=True)  # manual/device/api
    device_id = Column(String(100), nullable=True)

    # 时间�
    recorded_at = Column(DateTime, nullable=False, index=True)  # 数据记录时间
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

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
    AI聊天会话�

    存储用户与AI健康助手的�话会话
    """
    __tablename__ = "chat_sessions"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)

    # 外键
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 会话信息
    title = Column(String(200), nullable=True)  # 会话标�（�选）
    model = Column(String(50), default="qwen2.5:0.5b")  # 使用的模�

    # 会话状�
    is_active = Column(Boolean, default=True, index=True)
    message_count = Column(Integer, default=0)

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

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
    AI聊天消息�

    存储每条对话消息
    """
    __tablename__ = "chat_messages"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 外键
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)

    # 消息内�
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)

    # 元数�
    model = Column(String(50), nullable=True)  # 生成此消�的模�
    tokens_used = Column(Integer, nullable=True)  # token消�（�选）
    msg_metadata = Column("metadata", JSON, nullable=True)  # 其他元数�

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # 关系
    session = relationship("ChatSession", back_populates="messages")

    # 索引
    __table_args__ = (
        Index('idx_chat_message_session_created', 'session_id', 'created_at'),
    )

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}', content='{self.content[:30]}...')>"


# ============================================
# 设�数�模型
# ============================================

class DeviceType(str, enum.Enum):
    """设�类�"""
    CGM = "cgm"                  # 连续�糖监�
    GLUCOMETER = "glucometer"    # 指尖�糖仪
    SMARTWATCH = "smartwatch"    # 智能手表
    SMARTBAND = "smartband"      # 智能手环
    SCALE = "scale"              # 体重�
    BP_MONITOR = "bp_monitor"    # �压�


class DeviceStatus(str, enum.Enum):
    """设�状�"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    PAIRING = "pairing"


class UserDevice(Base):
    """
    用户设�绑定表

    记录用户绑定的健康��
    """
    __tablename__ = "user_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), unique=True, nullable=False, index=True)

    # 设�信�
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    manufacturer = Column(String(50), nullable=True)  # abbott/dexcom/huawei/xiaomi/apple
    model = Column(String(100), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    serial_number = Column(String(100), nullable=True)

    # 状�
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.CONNECTED)
    battery_level = Column(Integer, nullable=True)

    # 授权信息
    auth_token = Column(Text, nullable=True)
    auth_expires_at = Column(DateTime, nullable=True)

    # 同�信�
    last_sync_at = Column(DateTime, nullable=True)
    sync_cursor = Column(String(200), nullable=True)

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_user_device_user', 'user_id'),
        Index('idx_user_device_type', 'device_type'),
    )

    def __repr__(self):
        return f"<UserDevice(id={self.device_id}, type={self.device_type}, user={self.user_id})>"


class GlucoseReading(Base):
    """
    �糖数��

    存储 CGM 和手动录入的�糖数�
    """
    __tablename__ = "glucose_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=True, index=True)

    # �糖�
    value = Column(Float, nullable=False)  # mmol/L
    unit = Column(String(10), default="mmol/L")

    # CGM 趋势
    trend = Column(String(20), nullable=True)  # rising_fast/rising/stable/falling/falling_fast
    trend_rate = Column(Float, nullable=True)  # 变化� mmol/L/min

    # 来源和标�
    source = Column(String(20), default="manual")  # cgm/finger/manual
    meal_tag = Column(String(20), nullable=True)  # fasting/before_meal/after_meal/bedtime
    notes = Column(Text, nullable=True)

    # 时间
    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_glucose_user_time', 'user_id', 'recorded_at'),
        Index('idx_glucose_device_time', 'device_id', 'recorded_at'),
    )

    def __repr__(self):
        return f"<GlucoseReading(user={self.user_id}, value={self.value}, time={self.recorded_at})>"


class HeartRateReading(Base):
    """
    心率数据�
    """
    __tablename__ = "heart_rate_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=True)

    hr = Column(Integer, nullable=False)  # bpm
    activity_type = Column(String(20), nullable=True)  # rest/walk/run/sleep

    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_hr_user_time', 'user_id', 'recorded_at'),
    )


class HRVReading(Base):
    """
    HRV 数据�
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
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_hrv_user_time', 'user_id', 'recorded_at'),
    )


class SleepRecord(Base):
    """
    睡眠数据�
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

    # 睡眠阶� (分钟)
    awake_min = Column(Integer, default=0)
    light_min = Column(Integer, default=0)
    deep_min = Column(Integer, default=0)
    rem_min = Column(Integer, default=0)

    # 质量指标
    sleep_score = Column(Integer, nullable=True)  # 0-100
    efficiency = Column(Float, nullable=True)  # 百分�
    awakenings = Column(Integer, default=0)
    onset_latency_min = Column(Integer, nullable=True)

    # ��
    avg_spo2 = Column(Float, nullable=True)
    min_spo2 = Column(Float, nullable=True)

    # 详细数据 (JSON)
    stages_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_sleep_user_date', 'user_id', 'sleep_date'),
    )


class ActivityRecord(Base):
    """
    每日活动数据�
    """
    __tablename__ = "activity_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    activity_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD

    # 基�指标
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

    # 每小时数� (JSON)
    hourly_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_activity_user_date', 'user_id', 'activity_date'),
    )


class WorkoutRecord(Base):
    """
    运动记录�
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

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_workout_user_time', 'user_id', 'start_time'),
    )


class VitalSign(Base):
    """
    体征数据� (体重/��/体温/��)
    """
    __tablename__ = "vital_signs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=True)

    data_type = Column(String(20), nullable=False)  # weight/blood_pressure/temperature/spo2

    # 体重/体成�
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    body_fat_percent = Column(Float, nullable=True)
    muscle_mass_kg = Column(Float, nullable=True)
    water_percent = Column(Float, nullable=True)
    visceral_fat = Column(Integer, nullable=True)

    # ��
    systolic = Column(Integer, nullable=True)
    diastolic = Column(Integer, nullable=True)
    pulse = Column(Integer, nullable=True)

    # 体温
    temperature = Column(Float, nullable=True)

    # ��
    spo2 = Column(Float, nullable=True)

    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_vital_user_type_time', 'user_id', 'data_type', 'recorded_at'),
    )


class BehavioralStage(str, enum.Enum):
    """行为改变七阶�"""
    S0 = "S0"  # 无知无�
    S1 = "S1"  # 强烈抗拒
    S2 = "S2"  # �动承�
    S3 = "S3"  # 勉强接受
    S4 = "S4"  # 主动尝试
    S5 = "S5"  # 规律践�
    S6 = "S6"  # 内化为常


class StageStability(str, enum.Enum):
    """阶�稳定�"""
    STABLE = "stable"
    SEMI_STABLE = "semi_stable"
    UNSTABLE = "unstable"


class InteractionMode(str, enum.Enum):
    """交互模式"""
    EMPATHY = "empathy"         # 共情模式 (S0-S1)
    CHALLENGE = "challenge"     # 挑战模式 (S2-S3 行动�)
    EXECUTION = "execution"     # 执�模� (S4-S6)


class PsychologicalLevel(str, enum.Enum):
    """心理层级 (SPI-based)"""
    L1 = "L1"  # �大量��
    L2 = "L2"  # ��度支�
    L3 = "L3"  # 基本就绪
    L4 = "L4"  # 高度就绪
    L5 = "L5"  # �驱型


# �� v3.1 新�枚� ������������������������������

class ChangeCauseCategory(str, enum.Enum):
    """改变动因类别 (24动因 × 6�)"""
    INTRINSIC = "intrinsic"
    EXTERNAL_EVENT = "external_event"
    EMOTIONAL = "emotional"
    COGNITIVE = "cognitive"
    CAPABILITY = "capability"
    SOCIAL = "social"


class HealthCompetencyLevel(str, enum.Enum):
    """健康能力等级 (Lv0-Lv5)"""
    LV0 = "Lv0"  # 完全无知�
    LV1 = "Lv1"  # �题�察�
    LV2 = "Lv2"  # 方法学习�
    LV3 = "Lv3"  # 情��配�
    LV4 = "Lv4"  # �我驱动�
    LV5 = "Lv5"  # 使命实践�


class GrowthLevel(str, enum.Enum):
    """成长等级 (G0-G5, � HealthCompetencyLevel 对应)"""
    G0 = "G0"
    G1 = "G1"
    G2 = "G2"
    G3 = "G3"
    G4 = "G4"
    G5 = "G5"


class SPILevel(str, enum.Enum):
    """SPI 成功�能�等�"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class ObstacleCategory(str, enum.Enum):
    """障�类� (10�)"""
    TIME = "time"
    ENERGY = "energy"
    KNOWLEDGE = "knowledge"
    SKILL = "skill"
    ENVIRONMENT = "environment"
    SOCIAL = "social"
    EMOTION = "emotion"
    FINANCIAL = "financial"
    HABIT = "habit"
    BELIEF = "belief"


class HBMDimension(str, enum.Enum):
    """HBM 健康信念模型维度"""
    SUSCEPTIBILITY = "susceptibility"
    SEVERITY = "severity"
    BENEFITS = "benefits"
    BARRIERS = "barriers"
    CUES = "cues"
    SELF_EFFICACY = "self_efficacy"


class AttributionType(str, enum.Enum):
    """归因类型"""
    BEHAVIORAL = "behavioral"
    GENETIC = "genetic"
    ENVIRONMENTAL = "environmental"
    FATALISTIC = "fatalistic"


class TimeOrientation(str, enum.Enum):
    """时间视�"""
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"


class SupportLayer(str, enum.Enum):
    """�持系统层�"""
    CORE = "core"
    INTIMATE = "intimate"
    DAILY = "daily"
    PROFESSIONAL = "professional"
    COMMUNITY = "community"


class MonitoringLevel(str, enum.Enum):
    """养成监控频率"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class BehavioralProfile(Base):
    """
    统一行为画像�

    系统��真相源：存储用户的�为改变阶���为类型、心理层级�
    领域�求等核心画像数据，由 BehavioralProfileService 写入�
    StageRuntimeBuilder 负责阶�更新�

    �有干预决策必须基于�画像�
    """
    __tablename__ = "behavioral_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    # ====== 阶�运行� (�� StageRuntimeBuilder ��) ======
    current_stage = Column(SQLEnum(BehavioralStage), nullable=False, default=BehavioralStage.S0)
    stage_confidence = Column(Float, default=0.0)  # 0.0-1.0
    stage_stability = Column(SQLEnum(StageStability), default=StageStability.UNSTABLE)
    stage_updated_at = Column(DateTime, nullable=True)

    # ====== BAPS 向量 ======
    # 大五人格 {E: 15, N: -8, C: 22, A: 10, O: 18}
    big5_scores = Column(JSON, nullable=True)
    # BPT-6 行为类型: "action" / "knowledge" / "emotion" / "relation" / "environment" / "mixed"
    bpt6_type = Column(String(30), nullable=True)
    bpt6_scores = Column(JSON, nullable=True)  # �维度原�分
    # CAPACITY 改变潜力
    capacity_total = Column(Integer, nullable=True)
    capacity_weak = Column(JSON, nullable=True)  # ["A2_资源", "T_时间"]
    capacity_strong = Column(JSON, nullable=True)  # ["M_动机", "C_信心"]
    # SPI 成功�能�
    spi_score = Column(Float, nullable=True)  # 0-100
    spi_level = Column(String(10), nullable=True)  # very_high/high/medium/low/very_low
    # TTM7 阶�评估原始数�
    ttm7_stage_scores = Column(JSON, nullable=True)  # {S0: 12, S1: 6, ...}
    ttm7_sub_scores = Column(JSON, nullable=True)  # {AW: 25, WI: 22, AC: 18}

    # ====== 领域�� ======
    # 主�需干��域: ["nutrition", "exercise", "sleep", "emotion", ...]
    primary_domains = Column(JSON, nullable=True)
    # 领域详情: {"nutrition": {"priority": 1, "stage_strategy": "preparation"}, ...}
    domain_details = Column(JSON, nullable=True)

    # ====== V4.0 主体� & 信任 ======
    agency_mode = Column(String(20), default="passive")   # passive/transitional/active
    agency_score = Column(Float, default=0.0)             # 0.0-1.0
    trust_score = Column(Float, default=0.0)              # 0.0-1.0

    # ====== 干�配� ======
    interaction_mode = Column(SQLEnum(InteractionMode), nullable=True)
    psychological_level = Column(SQLEnum(PsychologicalLevel), nullable=True)
    # 风险标�: ["dropout_risk", "relapse_risk"]
    risk_flags = Column(JSON, nullable=True)

    # ====== 用户关注点（填空题 + 语音情感） ======
    concerns = Column(JSON, nullable=True)  # {"worry":"...", "confusion":"...", "desire":"...", "aversion":"..."}
    voice_emotions = Column(JSON, nullable=True)  # {"worry":"anxious", "desire":"hopeful", ...}

    # ====== 去诊�化展� ======
    friendly_stage_name = Column(String(50), nullable=True)  # "探索�"
    friendly_stage_desc = Column(Text, nullable=True)  # 面向用户的阶段描�

    # ====== �近评估ID (用于��) ======
    last_assessment_id = Column(String(50), nullable=True)

    # ====== 时间� ======
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

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
    行为跃迁审�日志表

    记录每� TTM 阶�跃迁事件，用于审�追�和数�分析
    """
    __tablename__ = "behavior_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)

    # 跃迁信息
    from_stage = Column(String(10), nullable=False)
    to_stage = Column(String(10), nullable=False)
    narrative = Column(Text, nullable=True)
    source_ui = Column(String(20), nullable=True)

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_stages', 'from_stage', 'to_stage'),
    )

    def __repr__(self):
        return f"<BehaviorAuditLog(user={self.user_id}, {self.from_stage}->{self.to_stage})>"


class BehaviorHistory(Base):
    """
    行为评估全量历史�

    记录每� TTM 评估结果（无论是否发生跃迁）�
    用于趋势分析、信念变化曲线和叙事回溯�
    """
    __tablename__ = "behavior_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # 阶�
    from_stage = Column(String(10), nullable=False)
    to_stage = Column(String(10), nullable=False)
    is_transition = Column(Boolean, default=False, nullable=False)

    # �照指�
    belief_score = Column(Float, nullable=True)
    narrative_sent = Column(Text, nullable=True)

    __table_args__ = (
        Index('idx_bh_user_ts', 'user_id', 'timestamp'),
        Index('idx_bh_transition', 'is_transition'),
    )

    def __repr__(self):
        arrow = "�" if self.is_transition else "="
        return f"<BehaviorHistory(user={self.user_id}, {self.from_stage}{arrow}{self.to_stage}, belief={self.belief_score})>"


class BehaviorTrace(Base):
    """
    行为长期记忆�

    每� TTM 判定的完整快照，作为系统�"长期记忆"�
    供周报生� (analyze_weekly_trend) 和信念变化回�使用�
    """
    __tablename__ = "behavior_traces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # 阶�跃�
    from_stage = Column(String(10), nullable=False)
    to_stage = Column(String(10), nullable=False)
    is_transition = Column(Boolean, default=False, nullable=False)

    # 判定时刻的指标快�
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
        arrow = "�" if self.is_transition else "="
        return f"<BehaviorTrace(user={self.user_id}, {self.from_stage}{arrow}{self.to_stage}, belief={self.belief_score})>"


# ============================================
# �行动跟踪模型
# ============================================

class MicroActionTask(Base):
    """
    �行动任务�

    存储从干预�划生成的每日微行动任务
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

    # 状�
    status = Column(String(20), default="pending")  # pending/completed/skipped/expired
    scheduled_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    completed_at = Column(DateTime, nullable=True)

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)

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
    �行动完成日志�

    记录每�任务完�/跳过的�细信息
    """
    __tablename__ = "micro_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("micro_action_tasks.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 操作
    action = Column(String(20), nullable=False)  # completed/skipped/partial
    note = Column(Text, nullable=True)  # 用户备注
    mood_score = Column(Integer, nullable=True)  # 1-5 完成后心�

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # 关系
    task = relationship("MicroActionTask", back_populates="logs")

    __table_args__ = (
        Index('idx_micro_log_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<MicroActionLog(id={self.id}, task={self.task_id}, action={self.action})>"


# ============================================
# 提醒与教练消�模型
# ============================================

class Reminder(Base):
    """
    提醒�

    存储用户的定时提醒（�物�随访��为、评估等�
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

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_reminder_user_active', 'user_id', 'is_active'),
        Index('idx_reminder_next_fire', 'next_fire_at'),
    )

    def __repr__(self):
        return f"<Reminder(id={self.id}, user={self.user_id}, type={self.type}, title='{self.title[:30]}')>"


class AssessmentAssignment(Base):
    """
    评估任务�

    教练推�评估量表给学员，�员完成后自动生成�理处方�
    教练审核�改后推�给学员�

    状�流�: pending � completed � reviewed � pushed
    """
    __tablename__ = "assessment_assignments"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 选定量表
    scales = Column(JSON, nullable=False)  # ["ttm7", "big5", "bpt6", "capacity", "spi"]

    # 状�
    status = Column(String(20), default="pending", nullable=False)  # pending/completed/reviewed/pushed
    note = Column(Text, nullable=True)  # 教练备注

    # 管道输出
    pipeline_result = Column(JSON, nullable=True)  # 评估管道完整输出

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
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
    教练审核条目�

    评估管道�动生成的��/处方/建�拆解为单条�核条目�
    教练逐条审核（采�/��/拒绝）后推�给学员�
    """
    __tablename__ = "coach_review_items"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assessment_assignments.id"), nullable=False, index=True)

    # 条目分类
    category = Column(String(20), nullable=False)  # goal / prescription / suggestion
    domain = Column(String(30), nullable=False)  # nutrition / exercise / sleep / emotion / stress / cognitive / social

    # 内�
    original_content = Column(JSON, nullable=False)  # 系统生成的原始内�
    coach_content = Column(JSON, nullable=True)  # 教练�改后内�（null=采用原�）
    status = Column(String(20), default="pending", nullable=False)  # pending/approved/modified/rejected
    coach_note = Column(Text, nullable=True)  # 教练批注

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)

    # 关系
    assignment = relationship("AssessmentAssignment", back_populates="review_items")

    __table_args__ = (
        Index('idx_cri_assignment', 'assignment_id'),
        Index('idx_cri_category', 'category'),
        {"schema": "coach_schema"},
    )

    def __repr__(self):
        return f"<CoachReviewItem(id={self.id}, assignment={self.assignment_id}, category={self.category}, status={self.status})>"


class DeviceAlert(Base):
    """
    设���表

    当穿戴��数�达到预�阈值时创建�
    同时向教练和服务对象发��知�
    """
    __tablename__ = "device_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    coach_id = Column(Integer, nullable=True, index=True)

    # 预�信�
    alert_type = Column(String(50), nullable=False)  # glucose_danger_high, hr_warning_low, etc.
    severity = Column(String(20), nullable=False)  # warning / danger
    message = Column(String(500), nullable=False)
    data_value = Column(Float, nullable=False)  # 实际读数
    threshold_value = Column(Float, nullable=False)  # 阈�
    data_type = Column(String(30), nullable=False)  # glucose / heart_rate / exercise / sleep

    # 状�
    user_read = Column(Boolean, default=False)
    coach_read = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)

    # 去重
    dedup_key = Column(String(100), nullable=False, index=True)  # user_id:type:YYYY-MM-DD-HH

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_device_alert_user', 'user_id', 'created_at'),
        Index('idx_device_alert_coach', 'coach_id', 'coach_read'),
        Index('idx_device_alert_dedup', 'dedup_key'),
    )

    def __repr__(self):
        return f"<DeviceAlert(id={self.id}, user={self.user_id}, type={self.alert_type}, severity={self.severity})>"


class CoachMessage(Base):
    """
    教练消息�

    教练与�员之间的单向消�（教练→学员�
    """
    __tablename__ = "coach_messages"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 消息内�
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text/encouragement/reminder/advice

    # 状�
    is_read = Column(Boolean, default=False)

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_coach_msg_student_read', 'student_id', 'is_read'),
        Index('idx_coach_msg_coach_student', 'coach_id', 'student_id'),
        {"schema": "coach_schema"},
    )

    def __repr__(self):
        return f"<CoachMessage(id={self.id}, coach={self.coach_id}, student={self.student_id}, read={self.is_read})>"


# ============================================
# 挑战/打卡活动模型
# ============================================

class PushSourceType(str, enum.Enum):
    """推�来源类�"""
    CHALLENGE = "challenge"
    DEVICE_ALERT = "device_alert"
    MICRO_ACTION = "micro_action"
    AI_RECOMMENDATION = "ai_recommendation"
    SYSTEM = "system"


class PushPriority(str, enum.Enum):
    """推�优先级"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class PushQueueStatus(str, enum.Enum):
    """推�队列状�"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"
    EXPIRED = "expired"


class ChallengeStatus(str, enum.Enum):
    """挑战模板状�"""
    DRAFT = "draft"                    # 草�
    PENDING_REVIEW = "pending_review"  # 待双专��核
    REVIEW_PARTIAL = "review_partial"  # �位专家已审核
    PUBLISHED = "published"            # 已发�
    ARCHIVED = "archived"              # 已归�


class ChallengeTemplate(Base):
    """
    挑战模板�

    定义��挑战活动（�14天�糖打卡�21天�念�练）�
    包含基本信息、持�天数、�核状�等�

    创建权限: 教练(L3)及以�
    发布权限: �双专家�核通过
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
    config_key = Column(String(100), nullable=True, unique=True)  # glucose_14day � 关联configs/challenges/*.json
    daily_push_times = Column(JSON, nullable=True)  # ["9:00", "11:30", "17:30"]
    day_topics = Column(JSON, nullable=True)  # {0: "欢迎", 1: "主�1", ...}

    # 创建�
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 审核流程（双专��核�
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

    # 统�
    enrollment_count = Column(Integer, default=0)

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

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
    挑战每日推�内容表

    每天�有�条推�（� 9:00/11:30/17:30），
    每条包含管理内���为健康指��互动评估（�卷JSON）�
    """
    __tablename__ = "challenge_day_pushes"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenge_templates.id"), nullable=False, index=True)

    # 推�时�
    day_number = Column(Integer, nullable=False)  # 0-based day
    push_time = Column(String(20), nullable=False)  # "9:00" / "11:30" / "17:30" / "立即发�"
    sort_order = Column(Integer, default=0)

    # 属�
    is_core = Column(Boolean, default=True)
    tag = Column(String(20), default="core")  # core / optional / assessment / info

    # 内�
    management_content = Column(Text, nullable=True)  # 管理内�
    behavior_guidance = Column(Text, nullable=True)  # 行为健康指�

    # 互动评估（结构化JSON�
    # {"title": "...", "questions": [{"type": "rating/text/single_choice/multi_choice", "label": "...", ...}]}
    survey = Column(JSON, nullable=True)

    # 时间�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)

    # 关系
    challenge = relationship("ChallengeTemplate", back_populates="day_pushes")

    __table_args__ = (
        Index('idx_cdp_challenge_day', 'challenge_id', 'day_number'),
        Index('idx_cdp_day_time', 'day_number', 'push_time'),
    )

    def __repr__(self):
        return f"<ChallengeDayPush(id={self.id}, day={self.day_number}, time={self.push_time}, core={self.is_core})>"


class EnrollmentStatus(str, enum.Enum):
    """报名状�"""
    ENROLLED = "enrolled"      # 已报名，���
    ACTIVE = "active"          # 进�中
    COMPLETED = "completed"    # 已完�
    DROPPED = "dropped"        # �途��


class ChallengeEnrollment(Base):
    """
    挑战报名�

    记录用户参加的挑战，跟踪进度�
    """
    __tablename__ = "challenge_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("challenge_templates.id"), nullable=False, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 推荐的教�

    # 进度
    status = Column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ENROLLED, nullable=False)
    current_day = Column(Integer, default=0)  # 当前进�到�几天
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 统�
    completed_pushes = Column(Integer, default=0)  # 已完成推送数
    completed_surveys = Column(Integer, default=0)  # 已完成问卷数
    streak_days = Column(Integer, default=0)  # 连续打卡天数

    # 时间�
    enrolled_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)

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
    挑战�卷回答表

    记录用户对每条推送中互动评估的回答�
    """
    __tablename__ = "challenge_survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("challenge_enrollments.id"), nullable=False, index=True)
    push_id = Column(Integer, ForeignKey("challenge_day_pushes.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 回答内� (JSON)
    # {"q1": "answer", "q2": 8, "q3": ["option1", "option2"]}
    responses = Column(JSON, nullable=False)

    # 时间�
    submitted_at = Column(DateTime, server_default=func.now(), nullable=False)

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
    挑战推�日志表

    记录每条推�的发�和阅�状态�
    """
    __tablename__ = "challenge_push_logs"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("challenge_enrollments.id"), nullable=False, index=True)
    push_id = Column(Integer, ForeignKey("challenge_day_pushes.id"), nullable=False, index=True)

    # 状�
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
    教练推��批队列

    �� AI 触发的推送（挑战打卡、�����微行动等）统一进入此队列，
    教练审批后才投�给学员。教练可调整推�的时间、�率、内容�

    流转: pending � approved � sent  �  pending � rejected  �  pending � expired
    """
    __tablename__ = "coach_push_queue"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 来源
    source_type = Column(String(30), nullable=False)  # challenge | device_alert | micro_action | ai_recommendation | system
    source_id = Column(String(50), nullable=True)  # 来源记录 ID

    # 内�
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    content_extra = Column(JSON, nullable=True)  # 附加结构化数�

    # 时间
    suggested_time = Column(DateTime, nullable=True)  # AI 建�发�时�
    scheduled_time = Column(DateTime, nullable=True)  # 教练设定时间（null=立即投�）

    # 优先级与状�
    priority = Column(String(10), default="normal")  # high | normal | low
    status = Column(String(10), default="pending", nullable=False)  # pending | approved | rejected | sent | expired
    coach_note = Column(String(500), nullable=True)

    # 审核追踪
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审批人ID")
    reviewed_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_cpq_coach_status', 'coach_id', 'status'),
        Index('idx_cpq_student', 'student_id'),
        Index('idx_cpq_source', 'source_type'),
        Index('idx_cpq_scheduled', 'status', 'scheduled_time'),
        {"schema": "coach_schema"},
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
    meal_type       = Column(String(20), nullable=True)
    cooking_method  = Column(String(50), nullable=True)
    is_packaged     = Column(Boolean, default=False, nullable=False)
    created_at      = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<FoodAnalysis(id={self.id}, user={self.user_id}, food={self.food_name})>"


# ============================================
# 专�白标�户枚举
# ============================================

# ============================================
# 知识� RAG 枚举
# ============================================

class EvidenceTier(str, enum.Enum):
    """证据分层"""
    T1 = "T1"  # 临床指南
    T2 = "T2"  # RCT/系统综述
    T3 = "T3"  # 专�共�/意�
    T4 = "T4"  # �人经验分�

class ContentType(str, enum.Enum):
    """内�类�"""
    GUIDELINE = "guideline"                  # 临床指南
    CONSENSUS = "consensus"                  # 专�共�
    RCT = "rct"                              # 随机对照试验
    REVIEW = "review"                        # 综述/荟萃分析
    EXPERT_OPINION = "expert_opinion"        # 专�意�
    CASE_REPORT = "case_report"              # 病例报告
    EXPERIENCE_SHARING = "experience_sharing" # �人经验分�

class ReviewStatus(str, enum.Enum):
    """审核状�"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"

# 证据分层 � priority 映射
TIER_PRIORITY_MAP = {"T1": 9, "T2": 7, "T3": 5, "T4": 3}

class KnowledgeScope(str, enum.Enum):
    """知识库范�"""
    TENANT = "tenant"        # 专��有
    DOMAIN = "domain"        # 领域知识
    PLATFORM = "platform"    # 平台��

class DocumentStatus(str, enum.Enum):
    """文档状�"""
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


# ============================================
# 知识� RAG 模型
# ============================================

# ============================================
# 知识库模� (V3.1 核心�复版)
# ============================================

class KnowledgeDocument(Base):
    """
    知识库文档主�
    """
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    file_type = Column(String(50), default="md")
    file_hash = Column(String(128), unique=True, nullable=False, index=True)
    scope = Column(String(50), default="global", index=True)
    domain_id = Column(String(50), default="tcm", index=True)
    status = Column(String(20), default="ready")
    author = Column(String(100), nullable=True)
    source = Column(String(255), nullable=True)
    tenant_id = Column(String(64), nullable=True, index=True)
    description = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    file_size = Column(Integer, default=0)
    priority = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)

    # 内�治� (migration 012/013)
    raw_content = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    evidence_tier = Column(String(2), server_default="T3", nullable=False)
    content_type = Column(String(30), nullable=True)
    published_date = Column(DateTime, nullable=True)
    review_status = Column(String(20), nullable=True)
    reviewer_id = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    contributor_id = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeDomain(Base):
    """知识领域元数�"""
    __tablename__ = "knowledge_domains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(String(50), unique=True, nullable=False)
    label = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class KnowledgeChunk(Base):
    """
    知识库分片表 (带向量存�)
    """
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    heading = Column(String(255), nullable=True)
    doc_title = Column(String(300), nullable=True)
    doc_author = Column(String(100), nullable=True)
    doc_source = Column(String(255), nullable=True)
    domain_id = Column(String(50), nullable=True)
    tenant_id = Column(String(64), nullable=True, index=True)
    page_number = Column(Integer, nullable=True)

    scope = Column(String(50), default="global", index=True)

    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)

    # 旧列 768 维 (保留, 蓝绿迁移期间不删)
    if Vector is not None:
        embedding = Column(Vector(768), nullable=True)
    else:
        embedding = Column(JSON, nullable=True)

    # 新列 1024 维 (mxbai-embed-large, 蓝绿迁移目标列)
    embedding_1024 = Column(Text, nullable=True)

    chunk_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    document = relationship("KnowledgeDocument", back_populates="chunks")


class KnowledgeCitation(Base):
    """
    知识库引用��表

    记录每� LLM 回�中实际引用了哪些知识块�
    用于审�追�和统计文档使用�率�
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

    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_kcite_session', 'session_id'),
        Index('idx_kcite_doc', 'document_id'),
        Index('idx_kcite_chunk', 'chunk_id'),
    )

    def __repr__(self):
        return f"<KnowledgeCitation(id={self.id}, chunk={self.chunk_id}, score={self.relevance_score})>"


class KnowledgeContribution(Base):
    """
    知识共享贡献� � 专�将私有知识贡献到�域共享池的请求记录

    工作�: pending � approved/rejected
    approved �, document.scope � 'tenant' 改为 'domain', chunks 同�更�
    """
    __tablename__ = "knowledge_contributions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(64), nullable=False, index=True, comment="贡献者�户ID")
    contributor_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="贡献者用户ID")
    domain_id = Column(String(50), nullable=False, comment="�标�域")

    # 贡献说明
    reason = Column(Text, nullable=True, comment="贡献理由/说明")

    # 审核状�
    status = Column(String(20), nullable=False, server_default="pending", comment="pending/approved/rejected")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核者用户ID")
    review_comment = Column(Text, nullable=True, comment="审核意�")
    reviewed_at = Column(DateTime, nullable=True)

    # 审�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_kcontrib_status", "status"),
        Index("idx_kcontrib_tenant", "tenant_id", "status"),
        Index("idx_kcontrib_domain", "domain_id", "status"),
    )

    def __repr__(self):
        return f"<KnowledgeContribution(id={self.id}, doc={self.document_id}, status={self.status})>"


# ============================================
# 内�交互枚�
# ============================================

class ContentItemStatus(str, enum.Enum):
    """内�条�状�"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class CommentStatus(str, enum.Enum):
    """评�状�"""
    ACTIVE = "active"
    HIDDEN = "hidden"
    DELETED = "deleted"

# ============================================
# 学习系统枚举
# ============================================

class LearningStatus(str, enum.Enum):
    """学习进度状�"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class PointsCategory(str, enum.Enum):
    """�分类�"""
    GROWTH = "growth"
    CONTRIBUTION = "contribution"
    INFLUENCE = "influence"

# ============================================
# 考试系统枚举
# ============================================

class ExamStatus(str, enum.Enum):
    """考试状�"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ExamResultStatus(str, enum.Enum):
    """考试结果状�"""
    PASSED = "passed"
    FAILED = "failed"

class ExamQuestionType(str, enum.Enum):
    """考试题目类型（区�于问� QuestionType�"""
    SINGLE = "single"
    MULTIPLE = "multiple"
    TRUEFALSE = "truefalse"
    SHORT_ANSWER = "short_answer"

# ============================================
# 批量灌注枚举
# ============================================

class IngestionStatus(str, enum.Enum):
    """灌注任务状�"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# ============================================
# 内�交互模�
# ============================================

class ContentItem(Base):
    """统一内�条��"""
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
    review_status = Column(String(20), default="pending", nullable=False, index=True)  # pending/approved/rejected — 铁律: AI内容必须审核后才能发布

    # 统��数 (反范式，高效读取)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    collect_count = Column(Integer, default=0)

    # �否含测试
    has_quiz = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_ci_type_status', 'content_type', 'status'),
        Index('idx_ci_domain_level', 'domain', 'level'),
        Index('idx_ci_author', 'author_id'),
    )

    def __repr__(self):
        return f"<ContentItem(id={self.id}, type={self.content_type}, title='{self.title}')>"


class ContentLike(Base):
    """内�点赞表"""
    __tablename__ = "content_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_cl_user_content', 'user_id', 'content_id', unique=True),
    )


class ContentBookmark(Base):
    """内�收藏表"""
    __tablename__ = "content_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_cb_user_content', 'user_id', 'content_id', unique=True),
    )


class ContentComment(Base):
    """内�评论表"""
    __tablename__ = "content_comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("content_items.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("content_comments.id"), nullable=True)  # �引用回�
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 评分
    like_count = Column(Integer, default=0)
    status = Column(String(20), default="active", nullable=False)  # active/hidden/deleted

    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_cc_content_status', 'content_id', 'status'),
    )

    def __repr__(self):
        return f"<ContentComment(id={self.id}, user={self.user_id}, content={self.content_id})>"


# ============================================
# 学习持久化模�
# ============================================

class LearningProgress(Base):
    """学习进度�"""
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("content_items.id"), nullable=False, index=True)
    progress_percent = Column(Float, default=0.0)  # 0-100
    last_position = Column(String(50), nullable=True)  # 视�时间点或章节位�
    time_spent_seconds = Column(Integer, default=0)
    status = Column(String(20), default="not_started")  # not_started/in_progress/completed

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

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
    earned_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_ltl_user_date', 'user_id', 'earned_at'),
    )


class LearningPointsLog(Base):
    """学习�分日�"""
    __tablename__ = "learning_points_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # quiz/complete/share/comment/daily_login/streak
    source_id = Column(String(50), nullable=True)  # 关联的内�/考试ID
    points = Column(Integer, nullable=False)
    category = Column(String(20), nullable=False)  # growth/contribution/influence
    earned_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_lpl_user_cat', 'user_id', 'category'),
        Index('idx_lpl_user_date', 'user_id', 'earned_at'),
    )


class UserLearningStats(Base):
    """用户学习统�汇�(反范�)"""
    __tablename__ = "user_learning_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    # 时长
    total_minutes = Column(Integer, default=0)

    # ��
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

    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_uls_points', 'total_points'),
    )

    def __repr__(self):
        return f"<UserLearningStats(user={self.user_id}, pts={self.total_points}, min={self.total_minutes})>"


# ============================================
# 考试系统模型
# ============================================

class ExamDefinition(Base):
    """考试定义�"""
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

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_exam_status', 'status'),
        Index('idx_exam_level', 'level'),
    )

    def __repr__(self):
        return f"<ExamDefinition(exam_id={self.exam_id}, name='{self.exam_name}')>"


class QuestionBank(Base):
    """题库�"""
    __tablename__ = "question_bank"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String(50), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)  # 题目内�
    question_type = Column(String(20), nullable=False)  # single/multiple/truefalse/short_answer
    options = Column(JSON, nullable=True)  # [{"key": "A", "text": "..."}, ...]
    answer = Column(JSON, nullable=False)  # ["A"] or ["A","C"] or "true" or "�答内�"
    explanation = Column(Text, nullable=True)  # 解析
    domain = Column(String(50), nullable=True)
    difficulty = Column(String(20), default="medium")  # easy/medium/hard
    tags = Column(JSON, nullable=True)  # ["nutrition", "L2"]
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_qb_type', 'question_type'),
        Index('idx_qb_domain', 'domain'),
    )

    def __repr__(self):
        return f"<QuestionBank(q_id={self.question_id}, type={self.question_type})>"


class ExamResult(Base):
    """考试结果�"""
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exam_id = Column(String(50), nullable=False, index=True)
    attempt_number = Column(Integer, default=1)
    score = Column(Integer, nullable=False)
    status = Column(String(10), nullable=False)  # passed/failed
    answers = Column(JSON, nullable=True)  # {"q1": "A", "q2": ["B","C"], ...}
    duration_seconds = Column(Integer, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

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
    """用户活动日志�"""
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_type = Column(String(30), nullable=False, index=True)  # login/share/learn/comment/like/exam/assess
    detail = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

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
    """批量灌注任务�"""
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
    result_doc_ids = Column(JSON, nullable=True)  # 创建� KnowledgeDocument IDs

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_bij_status', 'status'),
        Index('idx_bij_user', 'user_id'),
    )

    def __repr__(self):
        return f"<BatchIngestionJob(id={self.id}, file={self.filename}, status={self.status})>"


class TenantStatus(str, enum.Enum):
    """租户状�"""
    pending_review = "pending_review"  # 专�自助注册待审核
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
    """客户状�"""
    active = "active"
    graduated = "graduated"
    paused = "paused"
    exited = "exited"


# ============================================
# 专�白标�户模型
# ============================================

class ExpertTenant(Base):
    """
    每个入驻专� = ��租户
    ��专��应�套独立品牌�Agent配置、�户�
    """
    __tablename__ = "expert_tenants"

    id = Column(String(64), primary_key=True, comment="租户ID, � dr-chen-endo")
    expert_user_id = Column(
        Integer, ForeignKey("users.id"),
        nullable=False, index=True,
        comment="专�在平台的用户ID"
    )

    # 品牌配置
    brand_name = Column(String(128), nullable=False, comment="工作室名�")
    brand_tagline = Column(String(256), default="", comment="品牌标�")
    brand_avatar = Column(String(16), default="🏥", comment="Emoji头像")
    brand_logo_url = Column(String(512), default="", comment="Logo图片URL")
    brand_colors = Column(JSON, nullable=False, default=dict, comment='{"primary":"#hex","accent":"#hex","bg":"#hex"}')
    brand_theme_id = Column(String(32), default="default", comment="主�模板ID")
    custom_domain = Column(String(256), default="", comment="�定义域名")

    # 专�人�
    expert_title = Column(String(64), default="", comment="专�头�")
    expert_self_intro = Column(Text, default="", comment="专�自我介�")
    expert_specialties = Column(JSON, default=list, comment='["内分�","代谢管理"]')
    expert_credentials = Column(JSON, default=list, comment='["主任医师","博士生�师"]')

    # Agent 配置
    enabled_agents = Column(JSON, nullable=False, default=list, comment="�用的Agent ID列表")
    agent_persona_overrides = Column(JSON, default=dict, comment="Agent话术覆盖")

    # �由配� (Phase 2)
    routing_correlations = Column(JSON, nullable=False, server_default='{}', default=dict,
                                  comment='专�自定义关联网络 {"sleep":["glucose","stress"]}')
    routing_conflicts = Column(JSON, nullable=False, server_default='{}', default=dict,
                               comment='专�自定义冲突规则 {"sleep|exercise":"sleep"}')
    default_fallback_agent = Column(String(32), nullable=False, server_default='behavior_rx',
                                    default='behavior_rx', comment='默�回�Agent')

    # 业务配置
    enabled_paths = Column(JSON, default=list, comment="�用的学习�径ID")
    service_packages = Column(JSON, default=list, comment="服务包配�")
    questionnaire_overrides = Column(JSON, default=dict, comment="�卷�删题配�")
    welcome_message = Column(Text, default="", comment="客户首�进入的欢迎�")

    # 控制
    status = Column(SQLEnum(TenantStatus), default=TenantStatus.trial, nullable=False, index=True)
    tier = Column(SQLEnum(TenantTier), default=TenantTier.basic, nullable=False)
    max_clients = Column(Integer, default=50, comment="客户数上�")
    revenue_share_expert = Column(Float, default=0.80, comment="专�分成比�")
    trial_expires_at = Column(DateTime, nullable=True, comment="试用到期时间")

    # �助注册申请字�
    application_status = Column(String(20), nullable=True, index=True,
        comment="pending_review/approved/rejected/NULL(旧数�)")
    application_data = Column(JSON, default=dict,
        comment="申�表单原始数�")
    applied_at = Column(DateTime, nullable=True,
        comment="申�提交时�")

    # Migration 052: 审计治理扩展 (I-01/I-02)
    credential_type = Column(String(30), nullable=True, comment="physician_license / coach_certification / phd_supervision")
    role_confirmed = Column(Boolean, server_default=sa_text("false"), nullable=False)
    role_confirmed_by = Column(Integer, nullable=True)
    role_confirmed_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True, comment="正式激活时间")
    suspension_count = Column(Integer, server_default="0", nullable=False)
    workspace_ready = Column(Boolean, server_default=sa_text("false"), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

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
    """专�的客户 � 关联平台用户 + 租户归属"""
    __tablename__ = "tenant_clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), ForeignKey("expert_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="平台统一用户ID")

    source = Column(String(32), default="expert_referred", comment="来源")
    service_package = Column(String(64), default="trial", comment="�买的服务包ID")

    status = Column(SQLEnum(ClientStatus), default=ClientStatus.active, nullable=False, index=True)
    enrolled_at = Column(DateTime, server_default=func.now(), nullable=False)
    graduated_at = Column(DateTime, nullable=True)

    total_sessions = Column(Integer, default=0, comment="�计会话�数")
    last_active_at = Column(DateTime, nullable=True)
    notes = Column(Text, default="", comment="专��注")

    tenant = relationship("ExpertTenant", back_populates="clients")

    __table_args__ = (
        Index("idx_tc_tenant_status", "tenant_id", "status"),
    )

    def __repr__(self):
        return f"<TenantClient tenant={self.tenant_id} user={self.user_id}>"


class TenantAgentMapping(Base):
    """租户 x Agent 的�细配置"""
    __tablename__ = "tenant_agent_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), ForeignKey("expert_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(32), nullable=False, comment="Agent标识: sleep/glucose/stress/...")

    display_name = Column(String(64), default="", comment="�定义显示�")
    display_avatar = Column(String(16), default="", comment="�定义Emoji头像")
    greeting = Column(Text, default="", comment="�定义�场白")
    tone = Column(String(128), default="", comment="�气�格描述")
    bio = Column(String(256), default="", comment="Agent��")

    is_enabled = Column(Boolean, default=True, nullable=False)
    is_primary = Column(Boolean, default=False, comment="�否为主力Agent")
    sort_order = Column(Integer, default=0, comment="排序权重")

    # �由配� (Phase 2)
    custom_keywords = Column(JSON, nullable=False, server_default='[]', default=list,
                             comment='专�自定义�由关��')
    keyword_boost = Column(Float, nullable=False, server_default='1.5', default=1.5,
                           comment='专�关�词得分加权�数')

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    tenant = relationship("ExpertTenant", back_populates="agent_mappings")

    __table_args__ = (
        Index("idx_tam_tenant_enabled", "tenant_id", "is_enabled"),
    )

    def __repr__(self):
        return f"<TenantAgentMapping {self.tenant_id}:{self.agent_id}>"


class TenantAuditLog(Base):
    """租户操作审�日�"""
    __tablename__ = "tenant_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), ForeignKey("expert_tenants.id"), nullable=False, index=True)
    actor_id = Column(Integer, nullable=False, comment="操作者用户ID")
    action = Column(String(64), nullable=False, comment="操作类型")
    detail = Column(JSON, default=dict, comment="操作详情")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_audit_tenant_time", "tenant_id", "created_at"),
    )


# ============================================
# 通用�卷引擎模� (v22)
# ============================================

class SurveyStatus(str, enum.Enum):
    """�卷状�"""
    draft = "draft"
    published = "published"
    closed = "closed"
    archived = "archived"

class SurveyType(str, enum.Enum):
    """�卷类�"""
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
    """�卷主�"""
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="�卷标�")
    description = Column(Text, default="", comment="�卷�明")
    survey_type = Column(SQLEnum(SurveyType), default=SurveyType.general)
    status = Column(SQLEnum(SurveyStatus), default=SurveyStatus.draft)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String(64), ForeignKey("expert_tenants.id"), nullable=True)

    settings = Column(JSON, default=dict, comment="�卷�置 JSON")
    baps_mapping = Column(JSON, nullable=True, comment="BAPS回流映射")

    response_count = Column(Integer, default=0)
    avg_duration = Column(Integer, default=0, comment="平均�写�数")

    short_code = Column(String(8), unique=True, index=True, comment="�链码")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)
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
    """�卷�目�"""
    __tablename__ = "survey_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    question_type = Column(SQLEnum(QuestionType), nullable=False)
    sort_order = Column(Integer, default=0)

    title = Column(Text, nullable=False, comment="题干")
    description = Column(Text, default="", comment="题目说明")
    is_required = Column(Boolean, default=False)

    config = Column(JSON, default=dict, comment="题目配置 JSON")
    skip_logic = Column(JSON, nullable=True, comment="跳��辑 JSON")

    created_at = Column(DateTime, server_default=func.now())

    survey = relationship("Survey", back_populates="questions")
    answers = relationship("SurveyResponseAnswer", back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sq_survey", "survey_id", "sort_order"),
    )


class SurveyResponse(Base):
    """�卷回收表"""
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="匿名时为null")

    respondent_ip = Column(String(45), nullable=True)
    respondent_ua = Column(String(500), nullable=True)
    device_type = Column(String(20), default="unknown")

    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    duration_sec = Column(Integer, nullable=True, comment="�写�时�")

    is_complete = Column(Boolean, default=False)
    current_page = Column(Integer, default=0, comment="�点续�页码")

    baps_synced = Column(Boolean, default=False)
    baps_synced_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    survey = relationship("Survey", back_populates="responses")
    answers = relationship("SurveyResponseAnswer", back_populates="response", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sr_survey", "survey_id"),
        Index("idx_sr_user", "user_id"),
        Index("idx_sr_complete", "survey_id", "is_complete"),
    )


class SurveyResponseAnswer(Base):
    """�卷��答�"""
    __tablename__ = "survey_response_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    response_id = Column(Integer, ForeignKey("survey_responses.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("survey_questions.id", ondelete="CASCADE"), nullable=False)

    answer_value = Column(JSON, nullable=False, comment="答� JSON")
    score = Column(Float, nullable=True, comment="�动评�")

    created_at = Column(DateTime, server_default=func.now())

    response = relationship("SurveyResponse", back_populates="answers")
    question = relationship("SurveyQuestion", back_populates="answers")

    __table_args__ = (
        Index("idx_sra_response", "response_id"),
        Index("idx_sra_question", "question_id"),
        Index("idx_sra_unique", "response_id", "question_id", unique=True),
    )


class SurveyDistribution(Base):
    """�卷分发渠�"""
    __tablename__ = "survey_distributions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    channel = Column(SQLEnum(DistributionChannel), nullable=False)

    channel_config = Column(JSON, default=dict, comment="渠道配置 JSON")
    tracking_code = Column(String(20), unique=True, comment="渠道追踪�")

    click_count = Column(Integer, default=0)
    submit_count = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    survey = relationship("Survey", back_populates="distributions")


# ============================================
# V002 学分晋级体系模型
# ============================================

class CourseModuleType(str, enum.Enum):
    """课程模块类型"""
    M1_KNOWLEDGE = "M1"       # 知识学习
    M2_SKILL = "M2"           # �能��
    M3_PRACTICE = "M3"        # 实践应用
    M4_ASSESSMENT = "M4"      # 考核评估
    ELECTIVE = "ELECTIVE"     # 选修

class ElectiveCategory(str, enum.Enum):
    """选修课分�"""
    BEHAVIOR = "behavior"             # 行为科�
    NUTRITION = "nutrition"           # 营养�
    EXERCISE = "exercise"             # 运动科�
    PSYCHOLOGY = "psychology"         # 心理�
    TCM = "tcm"                       # �医养�
    COMMUNICATION = "communication"   # 沟�技�
    DATA_LITERACY = "data_literacy"   # 数据素养
    ETHICS = "ethics"                 # 伦理规范

class InterventionTier(str, enum.Enum):
    """干�层�"""
    T1 = "T1"  # 基�科普
    T2 = "T2"  # �证指�
    T3 = "T3"  # 专业干�
    T4 = "T4"  # 专�督�

class AssessmentEvidenceType(str, enum.Enum):
    """评估证据类型"""
    QUIZ = "quiz"               # 在线测验
    CASE_REPORT = "case_report" # 案例报告
    PEER_REVIEW = "peer_review" # 同伴评�
    SUPERVISOR = "supervisor"   # 督�评�
    EXAM = "exam"               # 正式考试

class CompanionStatus(str, enum.Enum):
    """同道者关系状态 (CR-28 完整生命周期)"""
    PENDING = "pending"       # 待确认
    ACTIVE = "active"         # 活跃中
    COOLING = "cooling"       # 冷却期(7天无互动)
    DORMANT = "dormant"       # 休眠(14天无互动)
    DISSOLVED = "dissolved"   # 已解除(30天休眠自动/手动)
    GRADUATED = "graduated"   # 已毕业
    DROPPED = "dropped"       # 已退出

class PromotionStatus(str, enum.Enum):
    """晋级申�状�"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CourseModule(Base):
    """课程模块 � V002学分体系核心�"""
    __tablename__ = "course_modules"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=sa_text("gen_random_uuid()"))
    code = Column(String(32), unique=True, nullable=False, comment="模块编码 OBS-M1-01")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    module_type = Column(String(20), nullable=False, comment="M1/M2/M3/M4/ELECTIVE")
    elective_cat = Column(String(30), nullable=True, comment="选修课分�")
    tier = Column(String(15), nullable=True, comment="T1-T4证据层级")
    target_role = Column(SQLEnum(UserRole, create_type=False), nullable=False,
                         comment="�标�色等级")

    credit_value = Column(Float, nullable=False, default=1.0, comment="学分�")
    theory_ratio = Column(String(10), nullable=True, comment="理�实践比�")
    prereq_modules = Column(JSON, nullable=True, default=list, comment="前置模块code列表")
    content_ref = Column(String(500), nullable=True, comment="内�引�")

    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)

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
    completed_at = Column(DateTime, server_default=func.now())
    evidence_type = Column(String(30), nullable=True, comment="评估证据类型")
    evidence_ref = Column(String(500), nullable=True, comment="证据材料URL")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核�")
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    module = relationship("CourseModule", back_populates="credits")

    __table_args__ = (
        Index("idx_uc_user", "user_id"),
        Index("idx_uc_module", "module_id"),
        Index("idx_uc_user_module", "user_id", "module_id"),
    )


class CompanionRelation(Base):
    """同道者带教关�"""
    __tablename__ = "companion_relations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=sa_text("gen_random_uuid()"))
    mentor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mentee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    mentor_role = Column(String(20), nullable=False, comment="带教时�师角色")
    mentee_role = Column(String(20), nullable=False, comment="带教时�员角色")
    status = Column(String(20), default="active", comment="active/graduated/dropped")

    quality_score = Column(Float, nullable=True, comment="带教质量评分 1-5")
    started_at = Column(DateTime, server_default=func.now())
    graduated_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # CR-28: 互动追踪
    last_interaction_at = Column(DateTime, nullable=True, comment="最后互动时间")
    interaction_count = Column(Integer, nullable=True, server_default=sa_text("0"), comment="累计互动次数")
    avg_quality_score = Column(Float, nullable=True, comment="平均互动质量 0.0~1.0")

    # CR-28: 互惠性
    initiator_count_a = Column(Integer, nullable=True, server_default=sa_text("0"), comment="mentor方发起互动次数")
    initiator_count_b = Column(Integer, nullable=True, server_default=sa_text("0"), comment="mentee方发起互动次数")
    reciprocity_score = Column(Float, nullable=True, comment="互惠分 0.0~1.0")

    # CR-28: 生命周期
    state_changed_at = Column(DateTime, nullable=True, comment="状态变更时间")
    dissolved_at = Column(DateTime, nullable=True, comment="解除时间")
    dissolve_reason = Column(String(50), nullable=True, comment="解除原因")

    __table_args__ = (
        Index("idx_cr_mentor", "mentor_id"),
        Index("idx_cr_mentee", "mentee_id"),
        Index("idx_cr_status", "status"),
        Index("idx_cr_mentor_mentee", "mentor_id", "mentee_id", unique=True),
        Index("idx_cr_status_last_interaction", "status", "last_interaction_at"),
    )


class PromotionApplication(Base):
    """晋级申�"""
    __tablename__ = "promotion_applications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=sa_text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    from_role = Column(String(20), nullable=False)
    to_role = Column(String(20), nullable=False)
    status = Column(String(20), default="pending", comment="pending/approved/rejected")

    # 四维��
    credit_snapshot = Column(JSON, nullable=True)
    point_snapshot = Column(JSON, nullable=True)
    companion_snapshot = Column(JSON, nullable=True)
    practice_snapshot = Column(JSON, nullable=True)
    check_result = Column(JSON, nullable=True, comment="晋级校验详细结果")

    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_pa_user", "user_id"),
        Index("idx_pa_status", "status"),
        Index("idx_pa_user_status", "user_id", "status"),
    )


# �� v3.1 诊断评估持久化模� ��������������������������

class ChangeCause(Base):
    """24动因 × 6� � 改变动因字典"""
    __tablename__ = "change_causes"

    id = Column(String(4), primary_key=True)
    category = Column(String(20), nullable=False)
    name_zh = Column(String(50), nullable=False)
    name_en = Column(String(50), nullable=False)
    description = Column(Text)
    assessment_question = Column(Text, nullable=False)
    weight = Column(Float, default=1.0)


class UserChangeCauseScore(Base):
    """用户改变动因评分"""
    __tablename__ = "user_change_cause_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_id = Column(Integer, nullable=False)
    cause_id = Column(String(4), ForeignKey("change_causes.id"), nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)

    __table_args__ = (
        Index("ix_user_cause_ua", "user_id", "assessment_id"),
    )


class InterventionStrategy(Base):
    """阶� × 动因 � 干�策� ORM"""
    __tablename__ = "intervention_strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_code = Column(String(4), nullable=False, index=True)
    readiness_level = Column(String(4), index=True)
    stage_name = Column(String(20), nullable=False)
    cause_code = Column(String(4), nullable=False, index=True)
    cause_category = Column(String(30), nullable=False)
    cause_name = Column(String(30), nullable=False)
    strategy_type = Column(String(30), nullable=False)
    coach_script = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("stage_code", "cause_code", name="uq_stage_cause"),
        Index("ix_strat_rc", "readiness_level", "cause_code"),
    )


class HealthCompetencyAssessment(Base):
    """健康能力评估记录"""
    __tablename__ = "health_competency_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    level_scores = Column(JSON, nullable=False)
    current_level = Column(String(4), nullable=False)
    recommended_content_stage = Column(String(20))
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
                     


class COMBAssessment(Base):
    """COM-B 行为能力评估"""
    __tablename__ = "comb_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    dimension_scores = Column(JSON, nullable=False)
    bottleneck = Column(String(20))
    total_score = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
                      


class SelfEfficacyAssessment(Base):
    """�我效能评�"""
    __tablename__ = "self_efficacy_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    avg_score = Column(Float, nullable=False)
    level = Column(String(10), nullable=False)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
                        


class ObstacleAssessment(Base):
    """障�评�"""
    __tablename__ = "obstacle_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    category_scores = Column(JSON, nullable=False)
    top_obstacles = Column(JSON, nullable=False)
    rx_adjustments = Column(JSON)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
                        


class SupportAssessment(Base):
    """�持系统评�"""
    __tablename__ = "support_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    layer_scores = Column(JSON, nullable=False)
    total_score = Column(Float, nullable=False)
    support_level = Column(String(10), nullable=False)
    weakest_layer = Column(String(20))
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)


# ============================================
# V003 �励体� � 9 tables
# ============================================

class Badge(Base):
    """徽章定义"""
    __tablename__ = "badges"
    id = Column(String(64), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(32), nullable=False)
    icon = Column(String(16))
    rarity = Column(String(20), nullable=False, server_default="common")  # badge_rarity enum
    condition_json = Column(JSON, nullable=False)
    visual_json = Column(JSON)
    sort_order = Column(Integer, server_default=sa_text("0"))
    is_active = Column(Boolean, server_default=sa_text("true"))
    created_at = Column(DateTime(timezone=True), server_default=sa_text("now()"))
    __table_args__ = (
        Index("idx_badges_category", "category"),
        Index("idx_badges_rarity", "rarity"),
    )


class UserBadge(Base):
    """用户已获得徽�"""
    __tablename__ = "user_badges"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(String(64), ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime(timezone=True), nullable=False, server_default=sa_text("now()"))
    metadata_ = Column("metadata", JSON)
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id"),
        Index("idx_ub_user", "user_id"),
        Index("idx_ub_badge", "badge_id"),
        Index("idx_ub_earned", "earned_at"),
    )


class UserMilestone(Base):
    """用户里程�"""
    __tablename__ = "user_milestones"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    milestone = Column(String(20), nullable=False)  # milestone_key enum
    achieved_at = Column(DateTime(timezone=True), nullable=False, server_default=sa_text("now()"))
    streak_days = Column(Integer)
    rewards_json = Column(JSON, nullable=False)
    ritual_played = Column(Boolean, server_default=sa_text("false"))
    __table_args__ = (
        UniqueConstraint("user_id", "milestone"),
        Index("idx_um_user", "user_id"),
        Index("idx_um_milestone", "milestone"),
    )


class UserStreak(Base):
    """用户连续打卡记录"""
    __tablename__ = "user_streaks"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    current_streak = Column(Integer, nullable=False, server_default=sa_text("0"))
    longest_streak = Column(Integer, nullable=False, server_default=sa_text("0"))
    last_checkin_date = Column(Date)
    grace_used_month = Column(Integer, server_default=sa_text("0"))
    recovery_count = Column(Integer, server_default=sa_text("0"))
    updated_at = Column(DateTime(timezone=True), server_default=sa_text("now()"))


class FlipCardRecord(Base):
    """翻牌记录"""
    __tablename__ = "flip_card_records"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pool_id = Column(String(64), nullable=False)
    shown_items = Column(JSON, nullable=False)
    chosen_item_id = Column(String(64), nullable=False)
    reward_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=sa_text("now()"))
    __table_args__ = (
        Index("idx_fcr_user", "user_id"),
    )


class NudgeRecord(Base):
    """推�/提醒记录"""
    __tablename__ = "nudge_records"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    milestone = Column(String(20))  # milestone_key enum
    channel = Column(String(20), nullable=False)  # nudge_channel enum
    title = Column(String(200))
    message = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=sa_text("now()"))
    opened_at = Column(DateTime(timezone=True))
    acted_on = Column(Boolean, server_default=sa_text("false"))
    __table_args__ = (
        Index("idx_nr_user", "user_id", "sent_at"),
    )


class UserMemorial(Base):
    """用户�念卡/成就记录"""
    __tablename__ = "user_memorials"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(64), nullable=False)
    template = Column(String(64))
    data_snapshot = Column(JSON, nullable=False)
    asset_url = Column(String(500))
    shared_count = Column(Integer, server_default=sa_text("0"))
    created_at = Column(DateTime(timezone=True), server_default=sa_text("now()"))
    __table_args__ = (
        Index("idx_umem_user", "user_id"),
    )


class PointTransaction(Base):
    """�分流�"""
    __tablename__ = "point_transactions"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=sa_text("gen_random_uuid()"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    point_type = Column(String(32), nullable=False)
    amount = Column(Integer, nullable=False)
    action = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=sa_text("now()"))
    __table_args__ = (
        Index("idx_ptx_user", "user_id"),
        Index("idx_ptx_action", "action"),
    )


class UserPoint(Base):
    """用户�分汇� (复合PK: user_id + point_type)"""
    __tablename__ = "user_points"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    point_type = Column(String(32), primary_key=True)
    total_points = Column(Integer, nullable=False, server_default=sa_text("0"))


# ============================================
# m019 诊断管线补充 � 10 tables (migration 019 已建�)
# ============================================

class InterventionOutcome(Base):
    """干�效果追�记录"""
    __tablename__ = "intervention_outcomes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    outcome_type = Column(String(20), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    completion_rate = Column(Float)
    streak_days = Column(Integer, server_default=sa_text("0"))
    tasks_assigned = Column(Integer, server_default=sa_text("0"))
    tasks_completed = Column(Integer, server_default=sa_text("0"))
    tasks_skipped = Column(Integer, server_default=sa_text("0"))
    spi_before = Column(Float)
    spi_after = Column(Float)
    spi_delta = Column(Float)
    stage_before = Column(String(4))
    stage_after = Column(String(4))
    readiness_before = Column(String(4))
    readiness_after = Column(String(4))
    cultivation_stage = Column(String(20))
    user_mood = Column(Integer)
    user_difficulty = Column(Integer)
    user_notes = Column(Text)
    effectiveness_score = Column(Float)
    adjustment_action = Column(String(30))
    adjustment_detail = Column(JSON)
    created_at = Column(DateTime, server_default=sa_text("now()"))
    __table_args__ = (
        Index("ix_outcome_user_type", "user_id", "outcome_type"),
        Index("ix_outcome_user_period", "user_id", "period_start"),
    )


class StageTransitionLog(Base):
    """阶�转换历�"""
    __tablename__ = "stage_transition_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transition_type = Column(String(20), nullable=False)
    from_value = Column(String(10), nullable=False)
    to_value = Column(String(10), nullable=False)
    trigger = Column(String(50))
    evidence = Column(JSON)
    created_at = Column(DateTime, server_default=sa_text("now()"))
    __table_args__ = (
        Index("ix_stage_trans_user", "user_id", "transition_type"),
    )


class PointEvent(Base):
    """�分事件流� (三维��)"""
    __tablename__ = "point_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(30), nullable=False)
    dimension = Column(String(15), nullable=False)
    points = Column(Integer, nullable=False)
    source_type = Column(String(30))
    source_id = Column(String(50))
    description = Column(String(200))
    created_at = Column(DateTime, server_default=sa_text("now()"))
    __table_args__ = (
        Index("ix_point_user_dim", "user_id", "dimension"),
        Index("ix_point_user_date", "user_id", "created_at"),
    )


class UserPointBalance(Base):
    """用户�分余� (三维)"""
    __tablename__ = "user_point_balances"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    growth = Column(Integer, server_default=sa_text("0"))
    contribution = Column(Integer, server_default=sa_text("0"))
    influence = Column(Integer, server_default=sa_text("0"))
    total = Column(Integer, server_default=sa_text("0"))
    streak_days = Column(Integer, server_default=sa_text("0"))
    longest_streak = Column(Integer, server_default=sa_text("0"))
    last_checkin_date = Column(DateTime)
    tasks_completed_total = Column(Integer, server_default=sa_text("0"))
    assessments_completed = Column(Integer, server_default=sa_text("0"))
    updated_at = Column(DateTime, server_default=sa_text("now()"))


class IncentiveReward(Base):
    """�励�励定义"""
    __tablename__ = "incentive_rewards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reward_type = Column(String(30), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    icon = Column(String(10))
    unlock_dimension = Column(String(15))
    unlock_threshold = Column(Integer)
    unlock_growth_level = Column(String(4))
    rx_effect = Column(JSON)
    is_active = Column(Boolean, server_default=sa_text("true"))


class UserReward(Base):
    """用户已获得的奖励"""
    __tablename__ = "user_rewards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_id = Column(Integer, ForeignKey("incentive_rewards.id"), nullable=False)
    earned_at = Column(DateTime, server_default=sa_text("now()"))
    __table_args__ = (
        UniqueConstraint("user_id", "reward_id", name="uq_user_reward"),
    )


class AssessmentSession(Base):
    """渐进式评估会�"""
    __tablename__ = "assessment_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(15), nullable=False, server_default=sa_text("'in_progress'"))
    entry_type = Column(String(20), nullable=False, server_default=sa_text("'self'"))
    completed_batches = Column(JSON)
    pending_batches = Column(JSON)
    total_questions_answered = Column(Integer, server_default=sa_text("0"))
    total_questions = Column(Integer, server_default=sa_text("176"))
    partial_results = Column(JSON)
    started_at = Column(DateTime, server_default=sa_text("now()"))
    last_activity = Column(DateTime, server_default=sa_text("now()"))
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)
    __table_args__ = (
        Index("ix_assess_session_user", "user_id", "status"),
    )


class BatchAnswer(Base):
    """单批次答题�录"""
    __tablename__ = "batch_answers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    batch_id = Column(String(30), nullable=False)
    questionnaire = Column(String(10), nullable=False)
    answers = Column(JSON, nullable=False)
    scores = Column(JSON)
    duration_seconds = Column(Integer)
    created_at = Column(DateTime, server_default=sa_text("now()"))
    __table_args__ = (
        Index("ix_batch_session", "session_id", "batch_id"),
    )


class LLMCallLog(Base):
    """LLM 调用日志"""
    __tablename__ = "llm_call_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    session_id = Column(String(64))
    created_at = Column(DateTime, server_default=sa_text("now()"))
    intent = Column(String(32))
    complexity = Column(String(16))
    model_requested = Column(String(64))
    model_actual = Column(String(64))
    provider = Column(String(32))
    fell_back = Column(Boolean, server_default=sa_text("false"))
    input_tokens = Column(Integer, server_default=sa_text("0"))
    output_tokens = Column(Integer, server_default=sa_text("0"))
    cost_yuan = Column(Float, server_default=sa_text("0"))
    latency_ms = Column(Integer, server_default=sa_text("0"))
    finish_reason = Column(String(32))
    user_message_preview = Column(Text)
    assistant_message_preview = Column(Text)
    error_message = Column(Text)
    __table_args__ = (
        Index("ix_llm_logs_user_date", "user_id", "created_at"),
    )


class RAGQueryLog(Base):
    """RAG 查�日�"""
    __tablename__ = "rag_query_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    created_at = Column(DateTime, server_default=sa_text("now()"))
    query_text = Column(Text)
    query_type = Column(String(32))
    doc_type_filter = Column(String(32))
    top_k = Column(Integer, server_default=sa_text("5"))
    results_count = Column(Integer, server_default=sa_text("0"))
    top_score = Column(Float, server_default=sa_text("0"))
    avg_score = Column(Float, server_default=sa_text("0"))
    sources_json = Column(Text)
    total_latency_ms = Column(Integer, server_default=sa_text("0"))
    llm_call_log_id = Column(Integer)


# ============================================
# V005 安全日志 + 内�音�
# ============================================

class SafetyLog(Base):
    """安全事件日志"""
    __tablename__ = "safety_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String(30), nullable=False, index=True)
    # event_type: input_blocked / output_filtered / crisis_detected / daily_report
    severity = Column(String(15), nullable=False, default="low", index=True)
    # severity: low / medium / high / critical
    input_text = Column(Text, nullable=True)
    output_text = Column(Text, nullable=True)
    filter_details = Column(JSON, nullable=True)
    resolved = Column(Boolean, default=False, index=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)


class ContentAudio(Base):
    """内�音频附�"""
    __tablename__ = "content_audio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False, index=True)
    audio_url = Column(String(500), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    voice_type = Column(String(30), default="tts_female")
    # voice_type: tts_female / tts_male / human
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)


class AgentTemplate(Base):
    """Agent 模板 � � Agent 定义从代码搬到数��"""
    __tablename__ = "agent_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(32), unique=True, nullable=False, index=True)
    display_name = Column(String(64), nullable=False)
    agent_type = Column(String(20), server_default="specialist")
    # agent_type: specialist / integrative / dynamic_llm
    domain_enum = Column(String(32), nullable=True)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, server_default="[]")
    data_fields = Column(JSON, server_default="[]")
    correlations = Column(JSON, server_default="[]")
    priority = Column(Integer, server_default="5")
    base_weight = Column(Float, server_default="0.8")
    enable_llm = Column(Boolean, server_default=sa_text("true"))
    system_prompt = Column(Text, nullable=True)
    conflict_wins_over = Column(JSON, server_default="[]")
    is_preset = Column(Boolean, server_default=sa_text("false"))
    is_enabled = Column(Boolean, server_default=sa_text("true"), index=True)
    evidence_tier = Column(String(5), server_default="T3", nullable=False, comment="T1/T2/T3/T4 循证等级")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
    updated_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)

    __table_args__ = (
        Index('idx_at_type_enabled', 'agent_type', 'is_enabled'),
        {"schema": "coach_schema"},
    )


# ============================================
# Phase 4: 反��习��
# ============================================

class AgentFeedback(Base):
    """
    Agent 反��录 � 用户/教练� Agent 回�的评价

    persist 版本, 替代 agent_api.py 的内存存�
    """
    __tablename__ = "agent_feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(32), nullable=False, index=True, comment="Agent 标识")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    session_id = Column(String(100), nullable=True, comment="会话ID")

    # 反�内�
    feedback_type = Column(String(20), nullable=False, comment="accept/reject/modify/rate")
    rating = Column(Integer, nullable=True, comment="1-5 评分")
    comment = Column(Text, nullable=True, comment="文字反�")
    modifications = Column(JSON, nullable=True, comment="�改建�")

    # 上下文快�
    user_message = Column(Text, nullable=True, comment="用户原�消�")
    agent_response = Column(Text, nullable=True, comment="Agent 回�")
    agents_used = Column(JSON, nullable=True, comment="�活的 Agent 列表")
    confidence = Column(Float, nullable=True, comment="Agent �信度")
    processing_time_ms = Column(Integer, nullable=True)

    # 租户
    tenant_id = Column(String(64), nullable=True, index=True)

    # 审�
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_af_agent_time", "agent_id", "created_at"),
        Index("idx_af_user", "user_id", "created_at"),
        {"schema": "coach_schema"},
    )


class AgentMetricsDaily(Base):
    """
    Agent 日维度质量指� � 由定时任务聚�

    指标: 满意�(avg_rating), 采纳�(acceptance_rate), 平均耗时, 调用�
    """
    __tablename__ = "agent_metrics_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(32), nullable=False, comment="Agent 标识")
    metric_date = Column(Date, nullable=False, comment="指标日期")

    # 调用�
    total_calls = Column(Integer, default=0)
    llm_calls = Column(Integer, default=0)

    # 反�统�
    feedback_count = Column(Integer, default=0)
    accept_count = Column(Integer, default=0)
    reject_count = Column(Integer, default=0)
    modify_count = Column(Integer, default=0)
    rate_count = Column(Integer, default=0)
    total_rating = Column(Integer, default=0, comment="评分总和 (用于算均�)")

    # 性能指标
    avg_processing_ms = Column(Float, default=0)
    avg_confidence = Column(Float, default=0)

    # 计算字� (冗余存储, 便于查�)
    acceptance_rate = Column(Float, default=0, comment="采纳� = accept / feedback_count")
    avg_rating = Column(Float, default=0, comment="平均评分 = total_rating / rate_count")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_amd_agent_date", "agent_id", "metric_date", unique=True),
        {"schema": "coach_schema"},
    )


class AgentPromptVersion(Base):
    """
    Agent Prompt 版本记录 � 追踪 system_prompt 变更, �� A/B 测试

    每� AgentTemplate.system_prompt 变更时创建新版本
    """
    __tablename__ = "agent_prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(32), nullable=False, index=True)
    version = Column(Integer, nullable=False, comment="版本� (递�)")
    system_prompt = Column(Text, nullable=False, comment="该版�� system_prompt")
    change_reason = Column(Text, nullable=True, comment="变更原因")

    # A/B 测试
    is_active = Column(Boolean, server_default=sa_text("false"), comment="�否为当前�活版�")
    traffic_pct = Column(Integer, server_default="100", comment="流量百分� (0-100)")

    # 指标�� (变更时�录前一版本的指�)
    prev_avg_rating = Column(Float, nullable=True)
    prev_acceptance_rate = Column(Float, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_apv_agent_version", "agent_id", "version", unique=True),
        {"schema": "coach_schema"},
    )


# ============================================
# Phase 5: Agent 生�
# ============================================

class AgentMarketplaceListing(Base):
    """
    Agent 模板市场 � 专�发布的�复用 Agent 模板

    工作�: draft � submitted � approved/rejected � published
    其他专�可 install (克隆到自己的租户)
    """
    __tablename__ = "agent_marketplace_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("coach_schema.agent_templates.id"), nullable=False, comment="源模�")
    publisher_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="发布�")
    tenant_id = Column(String(64), nullable=False, comment="来源租户")

    # 展示信息
    title = Column(String(128), nullable=False, comment="市场标�")
    description = Column(Text, nullable=True, comment="详细描述")
    category = Column(String(50), nullable=True, comment="分类: health/nutrition/mental/etc")
    tags = Column(JSON, server_default="[]", comment="标�列�")
    cover_url = Column(String(500), nullable=True, comment="封面� URL")

    # 状�
    status = Column(String(20), nullable=False, server_default="draft",
                    comment="draft/submitted/approved/rejected/published/archived")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # 统�
    install_count = Column(Integer, server_default="0", comment="安��数")
    avg_rating = Column(Float, server_default="0", comment="平均评分")
    rating_count = Column(Integer, server_default="0", comment="评分人数")

    # 版本
    version = Column(String(20), server_default="1.0.0")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_aml_status", "status"),
        Index("idx_aml_category", "category", "status"),
        Index("idx_aml_publisher", "publisher_id"),
    )


class AgentComposition(Base):
    """
    Agent 组合编排 � 多个 Agent 协作的�定义流水线

    定义 Agent 调用顺序、条件触发�结果合并策�
    """
    __tablename__ = "agent_compositions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="组合名称")
    description = Column(Text, nullable=True)
    tenant_id = Column(String(64), nullable=True, comment="�属�户 (NULL=平台�)")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 编排定义 (JSON)
    # [{"agent_id": "glucose", "order": 1, "condition": "always"},
    #  {"agent_id": "nutrition", "order": 2, "condition": "if:glucose.risk_level>low"},
    #  {"agent_id": "exercise", "order": 3, "condition": "optional"}]
    pipeline = Column(JSON, nullable=False, server_default="[]", comment="编排流水线定�")

    # 合并策略
    merge_strategy = Column(String(30), server_default="weighted_average",
                            comment="weighted_average/priority_first/consensus")

    is_enabled = Column(Boolean, server_default=sa_text("true"))
    is_default = Column(Boolean, server_default=sa_text("false"), comment="�否为租户默�编�")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_ac_tenant", "tenant_id", "is_enabled"),
    )


class AgentGrowthPoints(Base):
    """
    Agent 成长�� � 与六级体系打�

    记录专��过 Agent 获得的成长积� (创建、优化�共�、�安�等)
    """
    __tablename__ = "agent_growth_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(String(32), nullable=True, comment="关联 Agent")

    # �分事�
    event_type = Column(String(50), nullable=False,
                        comment="create_agent/optimize_prompt/share_knowledge/template_installed/feedback_positive")
    points = Column(Integer, nullable=False, comment="�分�")
    description = Column(String(255), nullable=True, comment="事件描述")

    # 关联
    reference_id = Column(Integer, nullable=True, comment="关联实体ID (template_id/contribution_id/etc)")
    reference_type = Column(String(50), nullable=True, comment="关联实体类型")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_agp_user", "user_id", "created_at"),
        Index("idx_agp_event", "event_type"),
    )


# ============================================
# V007 Phase A: Policy Engine (6 tables)
# ============================================

class PolicyRule(Base):
    """策略规则定义 � V007 Policy OS"""
    __tablename__ = 'policy_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(100), nullable=False, unique=True)
    rule_type = Column(String(30), nullable=False)  # routing|safety|cost|conflict|stage
    condition_expr = Column(JSON, nullable=False)    # JSON-Logic expression
    action_type = Column(String(30), nullable=False)  # select_agent|block|escalate|cost_limit
    action_params = Column(JSON, nullable=False)
    priority = Column(Integer, server_default=sa_text("50"))
    tenant_id = Column(String(50), nullable=True)
    is_enabled = Column(Boolean, server_default=sa_text("true"))
    evidence_tier = Column(String(5), nullable=True)
    description = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"))
    updated_at = Column(DateTime, server_default=sa_text("now()"))

    priorities = relationship('RulePriority', foreign_keys='RulePriority.rule_id',
                              back_populates='rule', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_policy_rules_type', 'rule_type', 'is_enabled'),
        Index('idx_policy_rules_tenant', 'tenant_id', 'priority'),
    )


class RulePriority(Base):
    """规则优先级层级树"""
    __tablename__ = 'rule_priority'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('policy_rules.id', ondelete='CASCADE'), nullable=False)
    parent_rule_id = Column(Integer, ForeignKey('policy_rules.id'), nullable=True)
    level = Column(Integer, server_default=sa_text("0"))
    override_mode = Column(String(20), server_default="merge")
    effective_from = Column(DateTime, nullable=True)
    effective_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"))

    rule = relationship('PolicyRule', foreign_keys=[rule_id], back_populates='priorities')
    parent_rule = relationship('PolicyRule', foreign_keys=[parent_rule_id])


class AgentApplicabilityMatrix(Base):
    """Agent适用性矩�"""
    __tablename__ = 'agent_applicability_matrix'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False)
    stage_range = Column(String(20), nullable=False)   # 'S0-S2' | 'ALL'
    risk_level = Column(String(20), server_default="normal")
    intensity_level = Column(Integer, server_default=sa_text("3"))
    max_daily_calls = Column(Integer, server_default=sa_text("10"))
    cooldown_hours = Column(Integer, server_default=sa_text("0"))
    contraindications = Column(JSON, server_default="[]")
    tenant_id = Column(String(50), nullable=True)
    is_enabled = Column(Boolean, server_default=sa_text("true"))
    created_at = Column(DateTime, server_default=sa_text("now()"))
    updated_at = Column(DateTime, server_default=sa_text("now()"))

    def is_applicable(self, user_stage: str, user_risk: str) -> bool:
        if not self.is_enabled:
            return False
        if self.stage_range == 'ALL':
            stage_match = True
        else:
            parts = self.stage_range.split('-')
            s_start = int(parts[0].replace('S', ''))
            s_end = int(parts[1].replace('S', ''))
            user_s = int(user_stage.replace('S', ''))
            stage_match = s_start <= user_s <= s_end
        risk_order = {'low': 0, 'normal': 1, 'high': 2, 'critical': 3}
        risk_match = risk_order.get(user_risk, 1) >= risk_order.get(self.risk_level, 1)
        return stage_match and risk_match

    __table_args__ = (
        Index('idx_aam_agent', 'agent_id', 'is_enabled'),
        Index('idx_aam_stage', 'stage_range', 'risk_level'),
    )


class ConflictMatrix(Base):
    """冲突矩阵"""
    __tablename__ = 'conflict_matrix'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_a_id = Column(String(50), nullable=False)
    agent_b_id = Column(String(50), nullable=False)
    conflict_type = Column(String(30), nullable=False)       # exclusive|cooperative|conditional
    resolution_strategy = Column(String(30), nullable=False)  # 5 strategies
    winner_rule = Column(JSON, nullable=True)
    tenant_id = Column(String(50), nullable=True)
    is_enabled = Column(Boolean, server_default=sa_text("true"))
    created_at = Column(DateTime, server_default=sa_text("now()"))

    __table_args__ = (
        Index('idx_conflict_agents', 'agent_a_id', 'agent_b_id'),
    )


class DecisionTrace(Base):
    """决策追踪日志"""
    __tablename__ = 'decision_trace'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=sa_text("gen_random_uuid()"))
    event_id = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=False)
    tenant_id = Column(String(50), nullable=True)
    session_id = Column(String(100), nullable=True)
    triggered_agents = Column(JSON, nullable=False)
    policy_applied = Column(JSON, nullable=False)
    rule_weights = Column(JSON, nullable=False)
    conflict_resolution = Column(JSON, nullable=True)
    final_output = Column(String(50), nullable=False)
    secondary_agents = Column(JSON, nullable=True)
    llm_model = Column(String(50), nullable=True)
    token_cost = Column(Integer, server_default=sa_text("0"))
    latency_ms = Column(Integer, server_default=sa_text("0"))
    created_at = Column(DateTime, server_default=sa_text("now()"))

    __table_args__ = (
        Index('idx_trace_event', 'event_id'),
        {"schema": "coach_schema"},
    )


class CostBudgetLedger(Base):
    """成本预算台账"""
    __tablename__ = 'cost_budget_ledger'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False)
    user_id = Column(Integer, nullable=True)
    budget_type = Column(String(20), nullable=False)   # daily|monthly|total
    max_tokens = Column(Integer, nullable=False)
    used_tokens = Column(Integer, server_default=sa_text("0"))
    max_cost_cny = Column(Float, nullable=True)
    used_cost_cny = Column(Float, server_default=sa_text("0"))
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    overflow_action = Column(String(20), server_default="downgrade")
    is_active = Column(Boolean, server_default=sa_text("true"))
    created_at = Column(DateTime, server_default=sa_text("now()"))
    updated_at = Column(DateTime, server_default=sa_text("now()"))

    @property
    def remaining_tokens(self) -> int:
        return max(0, (self.max_tokens or 0) - (self.used_tokens or 0))

    @property
    def usage_ratio(self) -> float:
        if not self.max_tokens:
            return 1.0
        return (self.used_tokens or 0) / self.max_tokens

    __table_args__ = (
        Index('idx_budget_tenant', 'tenant_id', 'budget_type', 'is_active'),
    )


# ============================================
# V007 Phase B: Skill Graph (9 tables)
# ============================================

class ExpertDomain(Base):
    """Agent知识领域边界"""
    __tablename__ = 'expert_domain'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False, index=True)
    domain_name = Column(String(100), nullable=False)
    domain_type = Column(String(30), nullable=False)  # primary|secondary|supportive
    knowledge_scope = Column(JSON, nullable=True)
    authority_level = Column(Integer, server_default=sa_text("3"))
    tenant_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"))


class InterventionProtocol(Base):
    """结构化干预协�"""
    __tablename__ = 'intervention_protocol'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False, index=True)
    protocol_name = Column(String(100), nullable=False)
    trigger_condition = Column(JSON, nullable=False)
    response_template = Column(Text, nullable=True)
    intensity_range = Column(String(10), server_default="1-5")
    duration_days = Column(Integer, nullable=True)
    success_criteria = Column(JSON, nullable=True)
    escalation_protocol = Column(String(100), nullable=True)
    is_enabled = Column(Boolean, server_default=sa_text("true"))
    created_at = Column(DateTime, server_default=sa_text("now()"))


class RiskBoundary(Base):
    """风险边界与自动��"""
    __tablename__ = 'risk_boundary'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False, index=True)
    risk_type = Column(String(50), nullable=False)
    max_risk_level = Column(String(20), nullable=False)
    escalation_target = Column(String(50), nullable=False)
    auto_exit_condition = Column(JSON, nullable=True)
    alert_message = Column(Text, nullable=True)
    is_enabled = Column(Boolean, server_default=sa_text("true"))
    created_at = Column(DateTime, server_default=sa_text("now()"))


class StageApplicability(Base):
    """阶��用�"""
    __tablename__ = 'stage_applicability'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False)
    stage_code = Column(String(5), nullable=False)   # S0-S6
    effectiveness_score = Column(Float, server_default=sa_text("0.5"))
    recommended_intensity = Column(Integer, server_default=sa_text("3"))
    is_primary = Column(Boolean, server_default=sa_text("false"))
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"))

    __table_args__ = (
        Index('idx_stage_app_agent', 'agent_id', 'stage_code'),
        Index('idx_stage_app_primary', 'stage_code', 'is_primary'),
    )


class Contraindication(Base):
    """禁忌�"""
    __tablename__ = 'contraindications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False, index=True)
    condition_type = Column(String(30), nullable=False)  # medical|psychological|behavioral|stage
    condition_value = Column(String(200), nullable=False)
    severity = Column(String(20), server_default="warning")   # warning|block
    alternative_agent_id = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"))


class EvidenceTierBinding(Base):
    """证据等级绑定"""
    __tablename__ = 'evidence_tier_binding'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False, index=True)
    evidence_tier = Column(String(5), nullable=False)   # T1-T5
    source_documents = Column(JSON, nullable=True)
    last_reviewed_at = Column(DateTime, nullable=True)
    reviewer = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"))


class AgentSkillGraph(Base):
    """Agent�能图�"""
    __tablename__ = 'agent_skill_graph'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False, unique=True)
    skill_vector = Column(JSON, nullable=False)
    capability_fingerprint = Column(String(64), nullable=True)
    last_calibrated_at = Column(DateTime, nullable=True)
    calibration_source = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"))
    updated_at = Column(DateTime, server_default=sa_text("now()"))


class PolicyInterventionOutcome(Base):
    """V007干�效� (distinct from m019 intervention_outcomes)"""
    __tablename__ = 'policy_intervention_outcome'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    agent_id = Column(String(50), nullable=False)
    intervention_start = Column(DateTime, nullable=False)
    intervention_end = Column(DateTime, nullable=True)
    ies_score = Column(Float, nullable=True)
    stage_before = Column(String(5), nullable=True)
    stage_after = Column(String(5), nullable=True)
    adherence_index = Column(Float, nullable=True)
    risk_delta = Column(Float, nullable=True)
    token_cost_total = Column(Integer, server_default=sa_text("0"))
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"))

    __table_args__ = (
        Index('idx_policy_outcome_user', 'user_id', 'agent_id'),
    )


class PolicyStageTransitionLog(Base):
    """V007阶�跃迁日� (distinct from m019 stage_transition_logs)"""
    __tablename__ = 'policy_stage_transition_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    from_stage = Column(String(5), nullable=False)
    to_stage = Column(String(5), nullable=False)
    trigger_agent_id = Column(String(50), nullable=True)
    trigger_event = Column(String(100), nullable=True)
    confidence = Column(Float, server_default=sa_text("0.8"))
    created_at = Column(DateTime, server_default=sa_text("now()"))

    __table_args__ = (
        Index('idx_policy_stage_trans_user', 'user_id', 'created_at'),
    )


# ============================================
# V4.0 Foundation Models
# ============================================

class JourneyState(Base):
    """
    V4.0 用户旅程状�表

    追踪用户� S0-S5 阶�的生命周期，以�
    agency_mode 三�模型和 trust_score 信任评分�
    每用户唯�记录�
    """
    __tablename__ = "journey_states"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    # S0-S5 阶�
    journey_stage = Column(String(30), nullable=False, default="s0_authorization")

    # Agency mode 三�
    agency_mode = Column(String(20), nullable=False, default="passive")
    agency_score = Column(Float, nullable=False, default=0.0)
    agency_signals = Column(JSON, default={})
    coach_override_agency = Column(String(20), nullable=True)

    # Trust score
    trust_score = Column(Float, nullable=False, default=0.0)
    trust_signals = Column(JSON, default={})

    # Conversion tracking
    conversion_type = Column(String(30), nullable=True)    # curiosity/time/coach_referred
    conversion_source = Column(String(30), nullable=True)  # self/community/institution/paid

    # Lifecycle timestamps
    activated_at = Column(DateTime, nullable=True)   # Observer→Grower moment
    graduated_at = Column(DateTime, nullable=True)   # S5 graduation moment

    # Stage tracking (migration 033)
    stage_entered_at = Column(DateTime, server_default=func.now())
    stability_start_date = Column(Date, nullable=True)
    stability_days = Column(Integer, nullable=False, default=0)
    interruption_count = Column(Integer, nullable=False, default=0)
    last_interruption_at = Column(DateTime, nullable=True)
    stage_transition_count = Column(Integer, nullable=False, default=0)

    # Observer trial tracking
    observer_dialog_count = Column(Integer, nullable=False, default=0)
    observer_last_dialog_date = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_journey_stage', 'journey_stage'),
        Index('idx_journey_agency', 'agency_mode'),
    )

    def __repr__(self):
        return f"<JourneyState(user={self.user_id}, stage={self.journey_stage}, agency={self.agency_mode})>"


class TrustScoreLog(Base):
    """
    V4.0 信任评分信号日志

    记录每�信任评分�算的六信号细节�
    dialog_depth(25%), proactive_return_rate(20%),
    topic_openness(15%), emotion_expression(15%),
    autonomous_info_sharing(15%), curiosity_expression(10%)
    """
    __tablename__ = "trust_score_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    signal_name = Column(String(50), nullable=False)
    signal_value = Column(Float, nullable=False, default=0.0)
    weight = Column(Float, nullable=False, default=0.0)
    computed_score = Column(Float, nullable=False, default=0.0)
    source = Column(String(50), default="system")
    context = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_trust_log_user', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<TrustScoreLog(user={self.user_id}, signal={self.signal_name}, value={self.signal_value})>"


class AgencyScoreLog(Base):
    """
    V4.0 主体性评分信号日�

    记录每� agency_score 计算的六信号细节�
    S1 主动发起�(25%), S2 �主修改率(20%),
    S3 主动表达词�(20%), S4 觉察深度(15%),
    S5 教练依赖�(10%, 反向), S6 教练标注(10%)
    """
    __tablename__ = "agency_score_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    signal_name = Column(String(50), nullable=False)
    signal_value = Column(Float, nullable=False, default=0.0)
    weight = Column(Float, nullable=False, default=0.0)
    computed_score = Column(Float, nullable=False, default=0.0)
    source = Column(String(50), default="system")
    context = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_agency_log_user', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<AgencyScoreLog(user={self.user_id}, signal={self.signal_name}, value={self.signal_value})>"


# ============================================
# V4.0 Phase 2 � Stage Engine + Governance (migration 033)
# ============================================

class StageTransitionLogV4(Base):
    """V4.0 阶�跃迁日� � 复用 m019 stage_transition_logs 表结�"""
    __tablename__ = "stage_transition_logs"
    __table_args__ = {"schema": "coach_schema", "extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transition_type = Column(String(20), nullable=False, default="stage")
    from_value = Column(String(10), nullable=False)
    to_value = Column(String(10), nullable=False)
    trigger = Column(String(50), nullable=True)
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # �� 便捷�� (� Python �, 不产生�� SQL �) ��
    @property
    def from_stage(self):
        return self.from_value

    @property
    def to_stage(self):
        return self.to_value

    @property
    def reason(self):
        return self.trigger

    @property
    def triggered_by(self):
        ev = self.evidence or {}
        return ev.get("triggered_by", "system") if isinstance(ev, dict) else "system"

    @property
    def triggered_by_user_id(self):
        ev = self.evidence or {}
        return ev.get("triggered_by_user_id") if isinstance(ev, dict) else None


class ResponsibilityMetric(Base):
    """责任追踪指标记录"""
    __tablename__ = "responsibility_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    metric_code = Column(String(20), nullable=True)
    metric_value = Column(Float, nullable=True, default=0.0)
    threshold_value = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="healthy")
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    details = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)
    # ── CR-15: 治理健康度检查补充列 ──
    metric_type = Column(String(50), nullable=True, index=True)
    value = Column(Float, nullable=True)
    detail = Column(JSON, nullable=True)
    checked_at = Column(DateTime, nullable=True)


class AntiCheatEvent(Base):
    """防刷策略事件记录"""
    __tablename__ = "anti_cheat_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    strategy = Column(String(10), nullable=False)
    event_type = Column(String(50), nullable=False)
    details = Column(JSON, default={})
    action_taken = Column(String(50), nullable=True)
    resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class GovernanceViolation(Base):
    """治理违��录"""
    __tablename__ = "governance_violations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    violation_type = Column(String(30), nullable=False)
    severity = Column(String(20), nullable=False, default="light")
    description = Column(Text, nullable=True)
    point_penalty = Column(Integer, nullable=False, default=0)
    action_taken = Column(String(50), nullable=True)
    protection_until = Column(Date, nullable=True)
    recovery_path = Column(Text, nullable=True)
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_by = Column(Integer, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class DualTrackStatus(Base):
    """双轨晋级状�机"""
    __tablename__ = "dual_track_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_level = Column(Integer, nullable=False)
    points_track_passed = Column(Boolean, nullable=False, default=False)
    growth_track_passed = Column(Boolean, nullable=False, default=False)
    status = Column(String(30), nullable=False, default="normal_growth")
    gap_analysis = Column(JSON, default={})
    points_checked_at = Column(DateTime, nullable=True)
    growth_checked_at = Column(DateTime, nullable=True)
    ceremony_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow, nullable=False)


# ============================================
# Migration 035 � Contract Registry Sync
# ============================================

class IESScore(Base):
    """IES 干�效果评� (4分量��: 0.4×完成 + 0.2×活跃 + 0.25×进展 - 0.15×抗阻)"""
    __tablename__ = "ies_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_type = Column(String(50), nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    completion_rate = Column(Float, nullable=False, default=0.0)
    activity_rate = Column(Float, nullable=False, default=0.0)
    progression_delta = Column(Float, nullable=False, default=0.0)
    resistance_index = Column(Float, nullable=False, default=0.0)
    ies_score = Column(Float, nullable=False, default=0.0)
    interpretation = Column(String(30), nullable=False, default="no_change")
    details = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_ies_scores_user', 'user_id', 'period_end'),
        Index('idx_ies_scores_agent', 'agent_type', 'period_end'),
    )


class IESDecisionLog(Base):
    """IES 决策追踪日志 � Rx�动调整�录"""
    __tablename__ = "ies_decision_log"

    id = Column(Integer, primary_key=True, index=True)
    ies_score_id = Column(Integer, ForeignKey("ies_scores.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    decision_type = Column(String(30), nullable=False)
    old_value = Column(String(100), nullable=True)
    new_value = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    auto_applied = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_ies_decision_user', 'user_id', 'created_at'),
    )


class UserContract(Base):
    """用户契约生命周期 � 从��到大师的�约追踪"""
    __tablename__ = "user_contracts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_type = Column(String(30), nullable=False)  # observer/grower/sharer/coach/promoter/master
    role_at_signing = Column(String(20), nullable=False)
    level_at_signing = Column(Integer, nullable=False, default=0)
    content_snapshot = Column(JSON, default={})
    signed_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="active")  # active/expired/revoked/renewed
    renewed_from_id = Column(Integer, ForeignKey("user_contracts.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_user_contracts_user', 'user_id', 'status'),
        Index('idx_user_contracts_type', 'contract_type', 'status'),
    )


class EthicalDeclaration(Base):
    """伦理声明 � Coach 5� / Promoter 7� 签署记录"""
    __tablename__ = "ethical_declarations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    declaration_type = Column(String(30), nullable=False)  # coach_5clause / promoter_7clause
    clauses = Column(JSON, nullable=False, default=[])
    total_clauses = Column(Integer, nullable=False, default=0)
    accepted_all = Column(Boolean, nullable=False, default=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(300), nullable=True)
    signed_at = Column(DateTime, server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_ethical_decl_user', 'user_id', 'declaration_type'),
    )


# ============================================
# Migration 052 — 审计治理: 督导资质 + 角色变更日志
# ============================================

class SupervisorCredential(Base):
    """督导资质记录 — 资质授予/年审/吊销生命周期 (I-07)"""
    __tablename__ = "supervisor_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    credential_type = Column(String(30), nullable=False, comment="physician_license / coach_certification / phd_supervision")
    credential_number = Column(String(100), nullable=True, comment="证书编号")
    issuing_authority = Column(String(200), nullable=True, comment="颁发机构")
    issued_at = Column(DateTime, nullable=True, comment="颁发日期")
    expires_at = Column(DateTime, nullable=True, comment="到期日期")
    status = Column(String(20), server_default=sa_text("'active'"), nullable=False, comment="active/expired/revoked")
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="授予操作者")
    granted_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_review_at = Column(DateTime, nullable=True, comment="上次年审日期")
    next_review_at = Column(DateTime, nullable=True, comment="下次年审截止")
    revoked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(String(500), nullable=True)
    review_notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_supercred_user_status", "user_id", "status"),
        Index("idx_supercred_next_review", "next_review_at", "status"),
    )

    user = relationship("User", foreign_keys=[user_id], backref="credentials")


class RoleChangeLog(Base):
    """角色变更审计日志 (I-01)"""
    __tablename__ = "role_change_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    old_role = Column(String(30), nullable=False)
    new_role = Column(String(30), nullable=False)
    reason = Column(String(50), nullable=False, comment="application_approved / credential_granted / credential_revoked / manual")
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    detail = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_rcl_user_created", "user_id", "created_at"),
    )


# ============================================
# Migration 036 � 400分制考核 + 收益分配 + 沙�测�
# ============================================

class CoachExamRecord(Base):
    """400分制教练考核记录"""
    __tablename__ = "coach_exam_records"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_level = Column(Integer, nullable=False)
    theory_score = Column(Float, default=0)
    theory_details = Column(JSON, default={})
    skill_score = Column(Float, default=0)
    skill_details = Column(JSON, default={})
    comprehensive_score = Column(Float, default=0)
    comprehensive_details = Column(JSON, default={})
    total_score = Column(Float, default=0)
    status = Column(String(20), default="in_progress")
    passed = Column(Boolean, default=False)
    attempt_number = Column(Integer, default=1)
    examiner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    exam_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_coach_exam_coach_level', 'coach_id', 'target_level'),
        {"schema": "coach_schema"},
    )


class RevenueShare(Base):
    """收益分配记录"""
    __tablename__ = "revenue_shares"

    id = Column(Integer, primary_key=True, index=True)
    beneficiary_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_type = Column(String(30), nullable=False)
    source_id = Column(Integer, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(5), default="CNY")
    status = Column(String(20), default="pending")
    calculation = Column(JSON, default={})
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_revenue_beneficiary_status', 'beneficiary_id', 'status'),
    )


class SandboxTestResult(Base):
    """沙�自动化测试结果"""
    __tablename__ = "sandbox_test_results"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(32), nullable=False)
    test_suite = Column(String(50), nullable=False)
    test_case_id = Column(String(50), nullable=False)
    scenario = Column(JSON, nullable=False)
    expected_output = Column(JSON, nullable=True)
    actual_output = Column(JSON, nullable=True)
    passed = Column(Boolean, nullable=False)
    score = Column(Float, nullable=True)
    error_detail = Column(Text, nullable=True)
    execution_ms = Column(Integer, nullable=True)
    run_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_sandbox_agent_suite_run', 'agent_id', 'test_suite', 'run_id'),
    )


class CoachSupervisionRecord(Base):
    """教练督��录"""
    __tablename__ = "coach_supervision_records"

    id = Column(Integer, primary_key=True, index=True)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_type = Column(String(30), nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="scheduled")
    template_id = Column(String(50), nullable=True)
    session_notes = Column(Text, nullable=True)
    action_items = Column(JSON, default=[])
    quality_rating = Column(Float, nullable=True)
    compliance_met = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_supervision_coach', 'coach_id', 'status'),
        Index('idx_supervision_supervisor', 'supervisor_id', 'status'),
        {"schema": "coach_schema"},
    )


class CoachKpiMetric(Base):
    """教练KPI红绿��表盘"""
    __tablename__ = "coach_kpi_metrics"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    period_type = Column(String(10), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    active_client_count = Column(Integer, default=0)
    session_completion_rate = Column(Float, default=0.0)
    client_retention_rate = Column(Float, default=0.0)
    stage_advancement_rate = Column(Float, default=0.0)
    assessment_coverage = Column(Float, default=0.0)
    intervention_adherence = Column(Float, default=0.0)
    client_satisfaction = Column(Float, default=0.0)
    safety_incident_count = Column(Integer, default=0)
    supervision_compliance = Column(Float, default=0.0)
    knowledge_contribution = Column(Integer, default=0)
    overall_status = Column(String(10), default="green")
    alert_details = Column(JSON, default={})
    auto_escalated = Column(Boolean, default=False)
    escalated_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('coach_id', 'period_type', 'period_start', name='uq_kpi_coach_period'),
        Index('idx_kpi_coach_period', 'coach_id', 'period_type', 'period_start'),
        Index('idx_kpi_overall_status', 'overall_status'),
        {"schema": "coach_schema"},
    )


class PeerTracking(Base):
    """四同道�追�记录"""
    __tablename__ = "peer_tracking"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    peer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    coach_level = Column(Integer, nullable=False)
    relationship_type = Column(String(20), default="companion")
    status = Column(String(20), default="active")
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    quality_score = Column(Float, nullable=True)
    interaction_count = Column(Integer, default=0)
    last_interaction_at = Column(DateTime, nullable=True)
    verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('coach_id', 'peer_id', 'coach_level', name='uq_peer_coach_level'),
        Index('idx_peer_coach_level', 'coach_id', 'coach_level', 'status'),
        Index('idx_peer_peer_id', 'peer_id', 'status'),
    )


def get_table_names():
    """获取�有表�"""
    return [
        "users",
        "assessments",
        "trigger_records",
        "interventions",
        "user_sessions",
        "health_data",
        "chat_sessions",
        "chat_messages",
        # 设�数��
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
        # 行为审� + 历史 + 长期记忆
        "behavior_audit_logs",
        "behavior_history",
        "behavior_traces",
        # �行动跟踪
        "micro_action_tasks",
        "micro_action_logs",
        # 设���
        "device_alerts",
        # 提醒与教练消�
        "reminders",
        "coach_messages",
        # 评估任务与�核
        "assessment_assignments",
        "coach_review_items",
        # 挑战/打卡活动
        "challenge_templates",
        "challenge_day_pushes",
        "challenge_enrollments",
        "challenge_survey_responses",
        "challenge_push_logs",
        # 教练推��批队列
        "coach_push_queue",
        # 食物识别
        "food_analyses",
        # 知识� RAG
        "knowledge_documents",
        "knowledge_chunks",
        "knowledge_citations",
        # 专�白标�户
        "expert_tenants",
        "tenant_clients",
        "tenant_agent_mappings",
        "tenant_audit_logs",
        # 内�交�
        "content_items",
        "content_likes",
        "content_bookmarks",
        "content_comments",
        # 学习持久�
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
        # �卷引�
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
        # V003 �励体�
        "badges",
        "user_badges",
        "user_milestones",
        "user_streaks",
        "flip_card_records",
        "nudge_records",
        "user_memorials",
        # �分系�
        "point_transactions",
        "user_points",
        # m019 诊断管线补充
        "intervention_outcomes",
        "stage_transition_logs",
        "point_events",
        "user_point_balances",
        "incentive_rewards",
        "user_rewards",
        "assessment_sessions",
        "batch_answers",
        "llm_call_logs",
        "rag_query_logs",
        # V3.1 诊断评估
        "change_causes",
        "user_change_cause_scores",
        "intervention_strategies",
        "health_competency_assessments",
        "comb_assessments",
        "self_efficacy_assessments",
        "obstacle_assessments",
        "support_assessments",
        # V005 安全+音�
        "safety_logs",
        "content_audio",
        # V006 Agent 模板
        "agent_templates",
        # V007 Phase A: Policy Engine
        "policy_rules",
        "rule_priority",
        "agent_applicability_matrix",
        "conflict_matrix",
        "decision_trace",
        "cost_budget_ledger",
        # V007 Phase B: Skill Graph
        "expert_domain",
        "intervention_protocol",
        "risk_boundary",
        "stage_applicability",
        "contraindications",
        "evidence_tier_binding",
        "agent_skill_graph",
        "policy_intervention_outcome",
        "policy_stage_transition_log",
        # V4.0 Foundation
        "journey_states",
        "trust_score_logs",
        "agency_score_logs",
        # V4.0 Stage Engine + Governance (migration 033)
        "stage_transition_logs",
        "responsibility_metrics",
        "anti_cheat_events",
        "governance_violations",
        "dual_track_status",
        # Migration 035 � Contract Registry Sync
        "ies_scores",
        "ies_decision_log",
        "user_contracts",
        "ethical_declarations",
        # Migration 036 � 400分制考核 + 收益分配 + 沙�测�
        "coach_exam_records",
        "revenue_shares",
        "sandbox_test_results",
        "coach_supervision_records",
        "coach_kpi_metrics",
        "peer_tracking",
    ]


def get_model_by_name(name: str):
    """根据名称获取模型�"""
    models = {
        "User": User,
        "Assessment": Assessment,
        "TriggerRecord": TriggerRecord,
        "Intervention": Intervention,
        "UserSession": UserSession,
        "HealthData": HealthData,
        "ChatSession": ChatSession,
        "ChatMessage": ChatMessage,
        # 设�数�模型
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
        # �行动跟踪
        "MicroActionTask": MicroActionTask,
        "MicroActionLog": MicroActionLog,
        # 设���
        "DeviceAlert": DeviceAlert,
        # 提醒与教练消�
        "Reminder": Reminder,
        "CoachMessage": CoachMessage,
        # 评估任务与�核
        "AssessmentAssignment": AssessmentAssignment,
        "CoachReviewItem": CoachReviewItem,
        # 挑战/打卡活动
        "ChallengeTemplate": ChallengeTemplate,
        "ChallengeDayPush": ChallengeDayPush,
        "ChallengeEnrollment": ChallengeEnrollment,
        "ChallengeSurveyResponse": ChallengeSurveyResponse,
        "ChallengePushLog": ChallengePushLog,
        # 教练推��批队列
        "CoachPushQueue": CoachPushQueue,
        # 食物识别
        "FoodAnalysis": FoodAnalysis,
        # 知识� RAG
        "KnowledgeDocument": KnowledgeDocument,
        "KnowledgeChunk": KnowledgeChunk,
        "KnowledgeCitation": KnowledgeCitation,
        # 专�白标�户
        "ExpertTenant": ExpertTenant,
        "TenantClient": TenantClient,
        "TenantAgentMapping": TenantAgentMapping,
        "TenantAuditLog": TenantAuditLog,
        # 内�交�
        "ContentItem": ContentItem,
        "ContentLike": ContentLike,
        "ContentBookmark": ContentBookmark,
        "ContentComment": ContentComment,
        # 学习持久�
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
        # �卷引�
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
        # V3.1 诊断评估
        "ChangeCause": ChangeCause,
        "UserChangeCauseScore": UserChangeCauseScore,
        "InterventionStrategy": InterventionStrategy,
        "HealthCompetencyAssessment": HealthCompetencyAssessment,
        "COMBAssessment": COMBAssessment,
        "SelfEfficacyAssessment": SelfEfficacyAssessment,
        "ObstacleAssessment": ObstacleAssessment,
        "SupportAssessment": SupportAssessment,
        # V003 �励体�
        "Badge": Badge,
        "UserBadge": UserBadge,
        "UserMilestone": UserMilestone,
        "UserStreak": UserStreak,
        "FlipCardRecord": FlipCardRecord,
        "NudgeRecord": NudgeRecord,
        "UserMemorial": UserMemorial,
        "PointTransaction": PointTransaction,
        "UserPoint": UserPoint,
        # m019 诊断管线补充
        "InterventionOutcome": InterventionOutcome,
        "StageTransitionLog": StageTransitionLog,
        "PointEvent": PointEvent,
        "UserPointBalance": UserPointBalance,
        "IncentiveReward": IncentiveReward,
        "UserReward": UserReward,
        "AssessmentSession": AssessmentSession,
        "BatchAnswer": BatchAnswer,
        "LLMCallLog": LLMCallLog,
        "RAGQueryLog": RAGQueryLog,
        # V005 安全+音�
        "SafetyLog": SafetyLog,
        "ContentAudio": ContentAudio,
        # V006 Agent 模板
        "AgentTemplate": AgentTemplate,
        # Phase 3 知识共享
        "KnowledgeContribution": KnowledgeContribution,
        # Phase 4 反�闭�
        "AgentFeedback": AgentFeedback,
        "AgentMetricsDaily": AgentMetricsDaily,
        "AgentPromptVersion": AgentPromptVersion,
        # Phase 5 Agent 生�
        "AgentMarketplaceListing": AgentMarketplaceListing,
        "AgentComposition": AgentComposition,
        "AgentGrowthPoints": AgentGrowthPoints,
        # V007 Phase A: Policy Engine
        "PolicyRule": PolicyRule,
        "RulePriority": RulePriority,
        "AgentApplicabilityMatrix": AgentApplicabilityMatrix,
        "ConflictMatrix": ConflictMatrix,
        "DecisionTrace": DecisionTrace,
        "CostBudgetLedger": CostBudgetLedger,
        # V007 Phase B: Skill Graph
        "ExpertDomain": ExpertDomain,
        "InterventionProtocol": InterventionProtocol,
        "RiskBoundary": RiskBoundary,
        "StageApplicability": StageApplicability,
        "Contraindication": Contraindication,
        "EvidenceTierBinding": EvidenceTierBinding,
        "AgentSkillGraph": AgentSkillGraph,
        "PolicyInterventionOutcome": PolicyInterventionOutcome,
        "PolicyStageTransitionLog": PolicyStageTransitionLog,
        # V4.0 Foundation
        "JourneyState": JourneyState,
        "TrustScoreLog": TrustScoreLog,
        "AgencyScoreLog": AgencyScoreLog,
        # V4.0 Stage Engine + Governance
        "ResponsibilityMetric": ResponsibilityMetric,
        "AntiCheatEvent": AntiCheatEvent,
        "GovernanceViolation": GovernanceViolation,
        "DualTrackStatus": DualTrackStatus,
        # Migration 035 � Contract Registry Sync
        "IESScore": IESScore,
        "IESDecisionLog": IESDecisionLog,
        "UserContract": UserContract,
        "EthicalDeclaration": EthicalDeclaration,
        # Migration 036 � 400分制考核 + 收益分配 + 沙�测�
        "CoachExamRecord": CoachExamRecord,
        "RevenueShare": RevenueShare,
        "SandboxTestResult": SandboxTestResult,
        "CoachSupervisionRecord": CoachSupervisionRecord,
        "CoachKpiMetric": CoachKpiMetric,
        "PeerTracking": PeerTracking,
        # V5.0 Flywheel ORM (PATCH-1)
        "BehaviorPrescription": BehaviorPrescription,
        "DailyTask": DailyTask,
        "TaskCheckin": TaskCheckin,
        "ObserverQuotaLog": ObserverQuotaLog,
        "CoachReviewLog": CoachReviewLog,
        "UserContext": UserContext,
        "Notification": Notification,
    }
    return models.get(name)


# ═══════════════════════════════════════════════════
# V5.0 飞轮ORM模型 (PATCH-1, 修复CA-02)
# ═══════════════════════════════════════════════════

class BehaviorPrescription(Base):
    """行为处方 — 由rx_composer生成/教练审核激活"""
    __tablename__ = "behavior_prescriptions"

    id = Column(String(80), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    target_behavior = Column(String(200), nullable=False)
    frequency_dose = Column(String(100))
    time_place = Column(String(200))
    trigger_cue = Column(String(200))
    obstacle_plan = Column(Text)
    support_resource = Column(Text)

    domain = Column(String(30))
    difficulty_level = Column(String(20), server_default=sa_text("'easy'"))
    cultivation_stage = Column(String(30), server_default=sa_text("'startup'"))
    status = Column(String(20), server_default=sa_text("'draft'"), index=True)
    expires_at = Column(DateTime)
    approved_by_review = Column(String(80))

    created_at = Column(DateTime, server_default=sa_text("now()"))
    updated_at = Column(DateTime, server_default=sa_text("now()"))

    user = relationship("User", backref="behavior_prescriptions")


class DailyTask(Base):
    """每日任务 — 由scheduler_agent从处方生成"""
    __tablename__ = "daily_tasks"

    id = Column(String(80), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_date = Column(Date, nullable=False)
    order_num = Column(Integer, server_default=sa_text("0"))
    title = Column(String(200), nullable=False)
    tag = Column(String(20))
    tag_color = Column(String(10))
    time_hint = Column(String(100))
    input_mode = Column(String(20))
    quick_label = Column(String(20), server_default=sa_text("'打卡'"))
    source = Column(String(20), server_default=sa_text("'rx'"))
    agent_id = Column(String(50))
    rx_id = Column(String(80), ForeignKey("behavior_prescriptions.id"))
    done = Column(Boolean, server_default=sa_text("false"))
    done_time = Column(DateTime)
    created_at = Column(DateTime, server_default=sa_text("now()"))

    __table_args__ = (
        Index("idx_dt_user_date", "user_id", "task_date"),
    )

    user = relationship("User", backref="daily_tasks")
    prescription = relationship("BehaviorPrescription", backref="daily_tasks")


class TaskCheckin(Base):
    """任务打卡记录"""
    __tablename__ = "task_checkins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(80), ForeignKey("daily_tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    note = Column(Text)
    photo_url = Column(String(500))
    value = Column(Float)
    voice_url = Column(String(500))
    points_earned = Column(Integer, server_default=sa_text("0"))
    checked_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)

    __table_args__ = (
        Index("idx_checkin_user_date", "user_id", "checked_at"),
        Index("idx_checkin_task", "task_id"),
    )

    user = relationship("User", backref="task_checkins")
    task = relationship("DailyTask", backref="checkins")


class ObserverQuotaLog(Base):
    """Observer试用墙额度日志"""
    __tablename__ = "observer_quota_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quota_type = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)

    __table_args__ = (
        Index("idx_observer_quota_user_date", "user_id", "created_at"),
    )

    user = relationship("User", backref="observer_quota_logs")


class CoachReviewLog(Base):
    """教练审核日志"""
    __tablename__ = "coach_review_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_id = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    note = Column(Text)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)

    __table_args__ = (
        Index("idx_review_log_coach", "coach_id", "created_at"),
    )

    coach = relationship("User", backref="review_logs")


class UserContext(Base):
    """Agent跨Session用户记忆"""
    __tablename__ = "user_contexts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(30), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    source_agent = Column(String(50))
    confidence = Column(Float, server_default=sa_text("0.8"))
    extracted_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
    expires_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("user_id", "category", "key", name="uq_uctx_user_cat_key"),
        Index("idx_uctx_user_cat", "user_id", "category"),
    )

    user = relationship("User", backref="contexts")


class Notification(Base):
    """用户通知 — 主动触达"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200))
    body = Column(Text)
    type = Column(String(50))
    priority = Column(String(20), server_default=sa_text("'normal'"))
    is_read = Column(Boolean, server_default=sa_text("false"))
    created_at = Column(DateTime, server_default=sa_text("now()"))

    __table_args__ = (
        Index("idx_notif_user_unread", "user_id", "is_read", "created_at"),
    )

    user = relationship("User", backref="notifications")


# ============================================
# P5B: 每日分析聚合
# ============================================

class AnalyticsDaily(Base):
    """Pre-computed daily analytics metrics."""
    __tablename__ = "analytics_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    dau = Column(Integer, server_default="0")
    new_users = Column(Integer, server_default="0")
    active_growers = Column(Integer, server_default="0")
    conversion_rate = Column(Float, server_default="0.0")
    retention_7d = Column(Float, server_default="0.0")
    avg_tasks_completed = Column(Float, server_default="0.0")
    avg_session_minutes = Column(Float, server_default="0.0")
    ai_response_avg_ms = Column(Float, server_default="0.0")
    total_events = Column(Integer, server_default="0")
    total_chat_messages = Column(Integer, server_default="0")
    created_at = Column(DateTime, server_default=sa_text("now()"))


# ============================================
# P5C: Feature Flags + A/B Test Events
# ============================================

class FeatureFlag(Base):
    """Feature flag / A/B experiment configuration."""
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, server_default=sa_text("false"))
    rollout_pct = Column(Integer, server_default="0")
    variants = Column(JSON, server_default=sa_text("'[]'::jsonb"))
    targeting_rules = Column(JSON, server_default=sa_text("'{}'::jsonb"))
    created_at = Column(DateTime, server_default=sa_text("now()"))
    updated_at = Column(DateTime, server_default=sa_text("now()"))


class AbTestEvent(Base):
    """A/B test conversion event tracking."""
    __tablename__ = "ab_test_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    experiment_key = Column(String(100), nullable=False, index=True)
    variant = Column(String(50), nullable=False)
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSON, server_default=sa_text("'{}'::jsonb"))
    created_at = Column(DateTime, server_default=sa_text("now()"))


# ── Register external ORM models with Base.metadata ──────────
# Models defined in other files need to be imported so that
# Base.metadata.create_all() can create their tables (critical for CI).

def register_external_models():
    """Import all ORM models defined outside this file to ensure Base.metadata is complete."""
# ============================================
# Prompt 模板管理
# ============================================

class PromptTemplate(Base):
    """Prompt 模板 — 管理 AI 对话中使用的 Prompt 模板"""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    category = Column(String(30), nullable=False, index=True)
    content = Column(Text, nullable=False)
    variables = Column(JSON, server_default="[]")
    ttm_stage = Column(String(30), nullable=True, index=True)
    trigger_domain = Column(String(30), nullable=True, index=True)
    is_active = Column(Boolean, server_default=sa_text("true"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
    updated_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)


class DemoRequest(Base):
    """预约演示/商务咨询请求 — Landing Page 表单提交"""
    __tablename__ = "demo_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="联系人姓名")
    organization = Column(String(200), nullable=True, comment="机构/公司名称")
    title = Column(String(100), nullable=True, comment="职位")
    phone = Column(String(20), nullable=False, comment="手机号")
    email = Column(String(100), nullable=True, comment="邮箱")
    solution = Column(String(30), nullable=True, comment="感兴趣方案: hospital/insurance/government/rwe")
    message = Column(Text, nullable=True, comment="备注留言")
    source_page = Column(String(30), nullable=True, comment="来源页面")
    status = Column(String(20), server_default=sa_text("'pending'"), nullable=False, comment="pending/contacted/closed")
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)


    import importlib
    for mod in [
        'core.reflection_service',       # ReflectionJournal
        'core.script_library_service',   # ScriptTemplate
        'behavior_rx.core.rx_models',    # RxPrescription, RxStrategyTemplate, AgentHandoffLog
        'core.vision_service',           # VisionExamRecord, VisionBehaviorLog, VisionBehaviorGoal, VisionGuardianBinding, VisionProfile
        'core.xzb.xzb_models',          # XZB: XZBExpertProfile, XZBConfig, XZBKnowledge, XZBKnowledgeRule, XZBConversation, XZBRxFragment, XZBExpertIntervention, XZBMedCircle, XZBMedCircleComment, XZBKnowledgeSharing
    ]:
        try:
            importlib.import_module(mod)
        except ImportError:
            pass
