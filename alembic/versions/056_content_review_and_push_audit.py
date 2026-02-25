"""Migration 056 — 铁律审核字段补全

1. content_items 新增 review_status 列 (pending/approved/rejected)
   铁律要求: AI生成内容必须审核后才能推送/发布

2. coach_push_queue (coach_schema) 新增 reviewer_id 列
   审批审计追踪: 记录实际审批人

幂等性: 全部使用 IF NOT EXISTS / 条件检查，可重复执行
"""
from alembic import op
import sqlalchemy as sa

revision = '056'
down_revision = '055'
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. content_items.review_status ──
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'content_items'
                  AND column_name = 'review_status'
            ) THEN
                ALTER TABLE content_items
                    ADD COLUMN review_status VARCHAR(20) NOT NULL DEFAULT 'pending';
                CREATE INDEX IF NOT EXISTS idx_ci_review_status
                    ON content_items (review_status);
                COMMENT ON COLUMN content_items.review_status IS '审核状态: pending/approved/rejected — 铁律字段';
            END IF;
        END $$;
    """)

    # ── 2. coach_schema.coach_push_queue.reviewer_id ──
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'coach_schema'
                  AND table_name = 'coach_push_queue'
                  AND column_name = 'reviewer_id'
            ) THEN
                ALTER TABLE coach_schema.coach_push_queue
                    ADD COLUMN reviewer_id INTEGER REFERENCES users(id);
                COMMENT ON COLUMN coach_schema.coach_push_queue.reviewer_id IS '审批人用户ID — 审计追踪';
            END IF;
        END $$;
    """)


def downgrade():
    op.execute("""
        ALTER TABLE coach_schema.coach_push_queue DROP COLUMN IF EXISTS reviewer_id;
        DROP INDEX IF EXISTS idx_ci_review_status;
        ALTER TABLE content_items DROP COLUMN IF EXISTS review_status;
    """)
