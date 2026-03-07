"""064 add personality_archetype and motivation_type to behavioral_profiles

Revision ID: 064_add_personality_motivation
Revises: 063_phone_auth
Create Date: 2026-03-08

说明：
- behavioral_profiles 新增 personality_archetype (P1-P5) 缓存列
- behavioral_profiles 新增 motivation_type (M1-M5) 缓存列
- 两列均为 nullable VARCHAR(10)，由 generate_profile() 自动填充
"""

from alembic import op
import sqlalchemy as sa

revision = "064_add_personality_motivation"
down_revision = "063_phone_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "behavioral_profiles",
        sa.Column("personality_archetype", sa.String(10), nullable=True, comment="P1-P5 人格原型缓存"),
    )
    op.add_column(
        "behavioral_profiles",
        sa.Column("motivation_type", sa.String(10), nullable=True, comment="M1-M5 动机类型缓存"),
    )


def downgrade() -> None:
    op.drop_column("behavioral_profiles", "motivation_type")
    op.drop_column("behavioral_profiles", "personality_archetype")
