"""
Migration 057 - VisionGuard 护眼行为数据层
续接 VisionExam Migration 056（采集表）
表: vision_behavior_logs / vision_behavior_goals / vision_parent_bindings

规约：CAST 铁律 / 枚举 UPPERCASE / UUID PK / server_default NOW()
"""

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


# ── 复用平台 Base（实际项目中从 app.models.base import Base）──────────────────
class Base(DeclarativeBase):
    pass


# ── 枚举定义（全大写，CAST 安全）────────────────────────────────────────────────
class InputSourceEnum(str, enum.Enum):
    MANUAL = "MANUAL"
    DEVICE_SYNC = "DEVICE_SYNC"
    PARENT_INPUT = "PARENT_INPUT"
    COACH_INPUT = "COACH_INPUT"


class RiskLevelEnum(str, enum.Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    ALERT = "ALERT"
    URGENT = "URGENT"


# ──────────────────────────────────────────────────────────────────────────────
# 表1: vision_behavior_logs  — 日常用眼行为流水表
# ──────────────────────────────────────────────────────────────────────────────
class VisionBehaviorLog(Base):
    __tablename__ = "vision_behavior_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="行为记录唯一标识",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联学员",
    )
    log_date = Column(
        Date,
        nullable=False,
        comment="记录日期（允许补录）",
    )

    # 五大行为维度
    outdoor_minutes = Column(Integer, nullable=True, comment="当日户外活动分钟数")
    screen_sessions = Column(Integer, nullable=True, comment="合规用眼次数（每次≤20min）")
    screen_total_minutes = Column(Integer, nullable=True, comment="当日总屏幕时间（分钟）")
    eye_exercise_done = Column(
        Boolean, server_default=text("false"), nullable=False, comment="眼保健操是否完成"
    )
    lutein_intake_mg = Column(Numeric(5, 1), nullable=True, comment="叶黄素摄入量（mg）")
    sleep_minutes = Column(Integer, nullable=True, comment="当日实际睡眠时长（分钟）")

    # 综合评分（Job 27 在 23:00 写入）
    behavior_score = Column(
        Numeric(4, 1),
        nullable=False,
        server_default=text("0"),
        comment="当日综合护眼行为评分（0-100）",
    )

    input_source = Column(
        Enum(InputSourceEnum, name="input_source_enum", create_type=True),
        nullable=False,
        server_default=text("'MANUAL'"),
        comment="数据来源",
    )
    created_at = Column(
        TIMESTAMPTZ,
        nullable=False,
        server_default=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "log_date", name="uq_vision_behavior_log_user_date"),
        {"comment": "VisionGuard 日常用眼行为流水 — Migration 057"},
    )


# ──────────────────────────────────────────────────────────────────────────────
# 表2: vision_behavior_goals  — 个人护眼目标配置（一人一条 UPSERT）
# ──────────────────────────────────────────────────────────────────────────────
class VisionBehaviorGoal(Base):
    __tablename__ = "vision_behavior_goals"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="一人一条，UPSERT 模式",
    )

    # 五大维度目标阈值（可由专家/教练覆盖）
    outdoor_target_min = Column(
        Integer, server_default=text("120"), nullable=False, comment="户外目标分钟/天"
    )
    screen_session_limit = Column(
        Integer, server_default=text("20"), nullable=False, comment="单次用眼上限（分钟）"
    )
    screen_daily_limit = Column(
        Integer, server_default=text("120"), nullable=False, comment="日屏幕时间上限（分钟）"
    )
    lutein_target_mg = Column(
        Numeric(4, 1), server_default=text("10"), nullable=False, comment="叶黄素日目标（mg）"
    )
    sleep_target_min = Column(
        Integer, server_default=text("540"), nullable=False, comment="睡眠目标（分钟，540=9h）"
    )

    risk_level_at_set = Column(
        Enum(RiskLevelEnum, name="risk_level_enum", create_type=False),
        nullable=True,
        comment="设定时的风险等级",
    )
    set_by_expert_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="行诊智伴专家定制时记录",
    )
    updated_at = Column(
        TIMESTAMPTZ,
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
        comment="最后更新时间",
    )

    __table_args__ = (
        {"comment": "VisionGuard 个人护眼目标配置 — Migration 057"},
    )


# ──────────────────────────────────────────────────────────────────────────────
# 表3: vision_parent_bindings  — 家长-学员绑定关系
# ──────────────────────────────────────────────────────────────────────────────
class VisionParentBinding(Base):
    __tablename__ = "vision_parent_bindings"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    student_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学员账号",
    )
    parent_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="家长账号",
    )
    notify_risk_threshold = Column(
        Enum(RiskLevelEnum, name="risk_level_enum", create_type=False),
        server_default=text("'WATCH'"),
        nullable=False,
        comment="最低接收推送的风险等级",
    )
    can_input_behavior = Column(
        Boolean,
        server_default=text("true"),
        nullable=False,
        comment="家长是否可代录行为数据",
    )
    created_at = Column(
        TIMESTAMPTZ,
        nullable=False,
        server_default=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint(
            "student_user_id", "parent_user_id", name="uq_vision_parent_student"
        ),
        {"comment": "VisionGuard 家长-学员绑定 — Migration 057"},
    )


# ──────────────────────────────────────────────────────────────────────────────
# DDL 辅助：生成 SQL（可直接粘贴到 Alembic revision 或 psql）
# ──────────────────────────────────────────────────────────────────────────────
MIGRATION_057_UP_SQL = """
-- =====================================================================
-- Migration 057: VisionGuard 护眼行为数据层
-- 续接 Migration 056（vision_exam_records）
-- 执行前确认 risk_level_enum 已在 Migration 056 中创建
-- =====================================================================

-- 枚举：输入来源（新建）
DO $$ BEGIN
    CREATE TYPE input_source_enum AS ENUM (
        'MANUAL', 'DEVICE_SYNC', 'PARENT_INPUT', 'COACH_INPUT'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 表1: 日常行为流水
CREATE TABLE IF NOT EXISTS vision_behavior_logs (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date            DATE        NOT NULL,
    outdoor_minutes     INTEGER,
    screen_sessions     INTEGER,
    screen_total_minutes INTEGER,
    eye_exercise_done   BOOLEAN     NOT NULL DEFAULT false,
    lutein_intake_mg    NUMERIC(5,1),
    sleep_minutes       INTEGER,
    behavior_score      NUMERIC(4,1) NOT NULL DEFAULT 0,
    input_source        input_source_enum NOT NULL DEFAULT 'MANUAL',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_vision_behavior_log_user_date UNIQUE (user_id, log_date)
);
CREATE INDEX IF NOT EXISTS idx_vbl_user_date ON vision_behavior_logs (user_id, log_date DESC);
COMMENT ON TABLE vision_behavior_logs IS 'VisionGuard 日常用眼行为流水 — Migration 057';

-- 表2: 个人护眼目标配置
CREATE TABLE IF NOT EXISTS vision_behavior_goals (
    user_id             UUID        PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    outdoor_target_min  INTEGER     NOT NULL DEFAULT 120,
    screen_session_limit INTEGER    NOT NULL DEFAULT 20,
    screen_daily_limit  INTEGER     NOT NULL DEFAULT 120,
    lutein_target_mg    NUMERIC(4,1) NOT NULL DEFAULT 10,
    sleep_target_min    INTEGER     NOT NULL DEFAULT 540,
    risk_level_at_set   risk_level_enum,
    set_by_expert_id    UUID        REFERENCES users(id) ON DELETE SET NULL,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE vision_behavior_goals IS 'VisionGuard 个人护眼目标配置 — Migration 057';

-- 表3: 家长-学员绑定
CREATE TABLE IF NOT EXISTS vision_parent_bindings (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    student_user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_user_id      UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notify_risk_threshold risk_level_enum NOT NULL DEFAULT 'WATCH',
    can_input_behavior  BOOLEAN     NOT NULL DEFAULT true,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_vision_parent_student UNIQUE (student_user_id, parent_user_id)
);
CREATE INDEX IF NOT EXISTS idx_vpb_student ON vision_parent_bindings (student_user_id);
CREATE INDEX IF NOT EXISTS idx_vpb_parent  ON vision_parent_bindings (parent_user_id);
COMMENT ON TABLE vision_parent_bindings IS 'VisionGuard 家长-学员绑定 — Migration 057';
"""

MIGRATION_057_DOWN_SQL = """
DROP TABLE IF EXISTS vision_parent_bindings;
DROP TABLE IF EXISTS vision_behavior_goals;
DROP TABLE IF EXISTS vision_behavior_logs;
DROP TYPE  IF EXISTS input_source_enum;
"""
