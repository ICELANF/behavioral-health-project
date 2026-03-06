"""063 phone auth - sms verification codes table

Revision ID: 063_phone_auth
Revises: 061_add_concerns_to_behavioral_profiles
Create Date: 2026-03-06

说明：
- 新建 sms_verification_codes 表，存储手机验证码
- 为 users.phone 添加索引（已存在唯一约束，补充普通查询索引）
- password_hash 改为 nullable，支持手机号注册用户无密码
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '063'
down_revision = '061'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建验证码表
    op.create_table(
        'sms_verification_codes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('phone', sa.String(20), nullable=False, comment='手机号'),
        sa.Column('code', sa.String(10), nullable=False, comment='验证码'),
        sa.Column('purpose', sa.String(20), nullable=False, default='register',
                  comment='用途: register/login/bind'),
        sa.Column('is_used', sa.Boolean(), nullable=False, default=False),
        sa.Column('attempts', sa.Integer(), nullable=False, default=0,
                  comment='错误尝试次数'),
        sa.Column('expires_at', sa.DateTime(), nullable=False,
                  comment='过期时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('now()')),
    )

    # 2. 索引
    op.create_index('idx_sms_phone_purpose', 'sms_verification_codes',
                    ['phone', 'purpose'])
    op.create_index('idx_sms_expires_at', 'sms_verification_codes',
                    ['expires_at'])

    # 3. password_hash 改为 nullable（手机号注册用户无密码）
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=True)

    # 4. users.phone 补充查询索引（唯一约束已存在）
    op.create_index('idx_users_phone', 'users', ['phone'])


def downgrade():
    op.drop_index('idx_users_phone', table_name='users')
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=False)
    op.drop_index('idx_sms_expires_at', table_name='sms_verification_codes')
    op.drop_index('idx_sms_phone_purpose', table_name='sms_verification_codes')
    op.drop_table('sms_verification_codes')
