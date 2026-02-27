"""create demo_requests table

Revision ID: 058
Revises: 057
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa

revision = "058"
down_revision = "057"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "demo_requests",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False, comment="联系人姓名"),
        sa.Column("organization", sa.String(200), nullable=True, comment="机构/公司名称"),
        sa.Column("title", sa.String(100), nullable=True, comment="职位"),
        sa.Column("phone", sa.String(20), nullable=False, comment="手机号"),
        sa.Column("email", sa.String(100), nullable=True, comment="邮箱"),
        sa.Column("solution", sa.String(30), nullable=True, comment="感兴趣方案"),
        sa.Column("message", sa.Text, nullable=True, comment="备注留言"),
        sa.Column("source_page", sa.String(30), nullable=True, comment="来源页面"),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False, comment="pending/contacted/closed"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
    )


def downgrade():
    op.drop_table("demo_requests")
