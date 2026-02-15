"""V4.1 Week2: 教练层Schema分离 — 12表迁移到coach_schema

Revision ID: v41_week2_001
Revises: (填入当前最新revision)
Create Date: 2026-02-15

迁移策略 (3阶段):
  Phase A: 创建coach_schema + 迁移12张表
  Phase B: 在public中创建兼容view（旧代码无感）
  Phase C: 更新ORM的schema配置

完全可逆: downgrade会把表移回public并删除schema
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '038'
down_revision = '037'
branch_labels = None
depends_on = None

# ── 迁移目标 ──
COACH_TABLES = [
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

SCHEMA = 'coach_schema'


def upgrade() -> None:
    # ══════════════════════════════════════════
    # Phase A: 创建Schema + 迁移表
    # ══════════════════════════════════════════

    # 1. 创建 coach_schema
    op.execute(f'CREATE SCHEMA IF NOT EXISTS {SCHEMA}')

    # 2. 逐表迁移
    for table in COACH_TABLES:
        # 检查表是否存在（防止重复执行）
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = '{table}'
                ) THEN
                    ALTER TABLE public.{table} SET SCHEMA {SCHEMA};
                END IF;
            END $$;
        """)

    # ══════════════════════════════════════════
    # Phase B: 创建兼容View（过渡期）
    # ══════════════════════════════════════════
    # 旧代码通过 public.xxx 访问 → view透明转发到 coach_schema.xxx
    # ORM迁移完成后删除这些view

    for table in COACH_TABLES:
        # PostgreSQL simple views (SELECT * FROM single_table) are
        # auto-updatable — INSERT/UPDATE/DELETE work without rules/triggers.
        op.execute(f"""
            CREATE OR REPLACE VIEW public.{table} AS
            SELECT * FROM {SCHEMA}.{table};
        """)

    # ══════════════════════════════════════════
    # Phase C: 权限设置
    # ══════════════════════════════════════════
    # 给应用用户授权访问 coach_schema
    op.execute(f"""
        DO $$
        DECLARE
            app_user TEXT;
        BEGIN
            -- 获取当前连接用户（即应用用户）
            app_user := current_user;
            EXECUTE format('GRANT USAGE ON SCHEMA %I TO %I', '{SCHEMA}', app_user);
            EXECUTE format('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO %I', '{SCHEMA}', app_user);
            EXECUTE format('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I TO %I', '{SCHEMA}', app_user);
            EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON TABLES TO %I', '{SCHEMA}', app_user);
        END $$;
    """)


def downgrade() -> None:
    """完全回滚: 删除view → 移回public → 删除schema"""

    for table in COACH_TABLES:
        # 1. 删除兼容view
        op.execute(f'DROP VIEW IF EXISTS public.{table}')

        # 2. 把表移回public
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = '{SCHEMA}' AND table_name = '{table}'
                ) THEN
                    ALTER TABLE {SCHEMA}.{table} SET SCHEMA public;
                END IF;
            END $$;
        """)

    # 4. 删除schema
    op.execute(f'DROP SCHEMA IF EXISTS {SCHEMA}')
