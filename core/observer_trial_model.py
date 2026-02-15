"""
观察员体验版使用记录模型
契约来源: Sheet③ A节 — 体验版评估(限1次) + AI体验对话(限3轮)
迁移编号: 037 (接续036安全加固迁移)
"""

# ========================
# Part A: SQLAlchemy Model
# ========================

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from app.models.base import Base


class ObserverTrialUsage(Base):
    """
    观察员体验版使用记录表。
    
    追踪两类体验使用:
    - trial_assessment: 体验版HF-20快筛 (每人限1次)
    - trial_chat_rounds: AI体验对话轮数 (每人限3轮)
    """
    __tablename__ = "observer_trial_usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    usage_type = Column(
        String(50), nullable=False,
        comment="使用类型: trial_assessment | trial_chat_rounds"
    )
    count = Column(Integer, nullable=False, default=0, comment="已使用次数")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    __table_args__ = (
        UniqueConstraint("user_id", "usage_type", name="uq_trial_user_type"),
        {"comment": "观察员体验版使用追踪 (Sheet③契约)"},
    )
    
    def __repr__(self):
        return (
            f"<ObserverTrialUsage user={self.user_id} "
            f"type={self.usage_type} count={self.count}>"
        )


# ========================
# Part B: Alembic Migration
# ========================
# 保存为: alembic/versions/037_observer_trial_usage.py

MIGRATION_TEMPLATE = '''
"""037: Observer trial usage tracking

契约来源: Sheet③ 访客与入口契约 · A节
- 体验版评估限1次
- AI体验对话限3轮

Revision ID: 037_observer_trial
Revises: 036_security_hardening
Create Date: 2026-02-15
"""

from alembic import op
import sqlalchemy as sa

revision = '037_observer_trial'
down_revision = '036_security_hardening'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'observer_trial_usage',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('usage_type', sa.String(50), nullable=False,
                  comment='trial_assessment | trial_chat_rounds'),
        sa.Column('count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'usage_type', name='uq_trial_user_type'),
        comment='观察员体验版使用追踪 (Sheet③契约)'
    )
    op.create_index('ix_trial_user_id', 'observer_trial_usage', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_trial_user_id', 'observer_trial_usage')
    op.drop_table('observer_trial_usage')
'''
