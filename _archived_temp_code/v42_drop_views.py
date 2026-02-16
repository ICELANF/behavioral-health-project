"""V4.2: 删除12个兼容view (public→coach_schema迁移完成)

Revision ID: v42_drop_compat_views
Revises: v41_week3_001  # ← 确认和你的实际head一致
Create Date: 2026-02-15

前置条件 (7760ecc已确认):
  - agent_feedbacks ORM已加schema: coach_schema
  - access_control.py已改为coach_schema.coach_messages
  - 全部12个ORM model都有schema='coach_schema'
  - 35P/0F/0S无回归
"""
from alembic import op

revision = 'v42_drop_compat_views'
down_revision = None  # ← 改为你的实际Alembic head
branch_labels = None
depends_on = None

VIEWS = [
    'agent_feedbacks',
    'agent_metrics_daily',
    'agent_prompt_versions',
    'agent_templates',
    'coach_exam_records',
    'coach_kpi_metrics',
    'coach_messages',
    'coach_push_queue',
    'coach_review_items',
    'coach_supervision_records',
    'decision_trace',
    'rx_prescriptions',
]


def upgrade() -> None:
    for view in VIEWS:
        op.execute(f'DROP VIEW IF EXISTS public.{view}')


def downgrade() -> None:
    # 重建兼容view (auto-updatable, 指向coach_schema)
    for view in VIEWS:
        op.execute(f'CREATE OR REPLACE VIEW public.{view} AS SELECT * FROM coach_schema.{view}')
