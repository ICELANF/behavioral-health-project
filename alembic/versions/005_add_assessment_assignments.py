"""Add assessment_assignments and coach_review_items tables

Revision ID: 005
Revises: 004
Create Date: 2026-02-06

Adds tables for:
- assessment_assignments: 教练评估推送任务
- coach_review_items: 教练审核条目
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create assessment_assignments and coach_review_items tables."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # ---- assessment_assignments ----
    if "assessment_assignments" not in existing_tables:
        op.create_table(
            "assessment_assignments",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("coach_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("student_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("scales", sa.JSON, nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("note", sa.Text, nullable=True),
            sa.Column("pipeline_result", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("completed_at", sa.DateTime, nullable=True),
            sa.Column("reviewed_at", sa.DateTime, nullable=True),
            sa.Column("pushed_at", sa.DateTime, nullable=True),
        )
        op.create_index("idx_aa_coach_student", "assessment_assignments", ["coach_id", "student_id"])
        op.create_index("idx_aa_student_status", "assessment_assignments", ["student_id", "status"])
        op.create_index("idx_aa_status", "assessment_assignments", ["status"])

    # ---- coach_review_items ----
    if "coach_review_items" not in existing_tables:
        op.create_table(
            "coach_review_items",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("assignment_id", sa.Integer, sa.ForeignKey("assessment_assignments.id"), nullable=False, index=True),
            sa.Column("category", sa.String(20), nullable=False),
            sa.Column("domain", sa.String(30), nullable=False),
            sa.Column("original_content", sa.JSON, nullable=False),
            sa.Column("coach_content", sa.JSON, nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("coach_note", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=True),
        )
        op.create_index("idx_cri_assignment", "coach_review_items", ["assignment_id"])
        op.create_index("idx_cri_category", "coach_review_items", ["category"])


def downgrade() -> None:
    """Drop assessment_assignments and coach_review_items tables."""
    op.drop_table("coach_review_items")
    op.drop_table("assessment_assignments")
