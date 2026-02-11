"""fix ORM-DB drift: missing columns, nullable mismatches, varchar widths

Revision ID: 020
Revises: 019
Create Date: 2026-02-11

Summary:
  Part A – Add missing columns to DB (2 tables)
  Part B – Fix 15 nullable mismatches across 8 tables (align DB → ORM)
  Part C – Widen 8 real VARCHAR columns across 4 tables (DB→ORM)
           (7 enum-backed columns excluded: module_type, elective_cat,
            evidence_type, mentor_role, mentee_role, from_role, to_role)

Affected tables:
  knowledge_documents, knowledge_chunks, course_modules, user_credits,
  promotion_applications, comb_assessments, health_competency_assessments,
  obstacle_assessments, self_efficacy_assessments, support_assessments,
  user_change_cause_scores
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '020'
down_revision: Union[str, None] = '019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ──────────────────────────────────────────────────────────
    # Part A: Add missing columns to DB
    # ──────────────────────────────────────────────────────────

    # A1: knowledge_chunks — ORM has 'metadata' (JSON), DB lacks it
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE knowledge_chunks ADD COLUMN metadata JSON;
        EXCEPTION WHEN duplicate_column THEN NULL; END $$;
    """)

    # A2: knowledge_documents — 5 columns added manually via ALTER TABLE
    #     (idempotent with DO/EXCEPTION guard)
    for col_sql in [
        "ALTER TABLE knowledge_documents ADD COLUMN description TEXT",
        "ALTER TABLE knowledge_documents ADD COLUMN chunk_count INTEGER DEFAULT 0",
        "ALTER TABLE knowledge_documents ADD COLUMN file_size INTEGER DEFAULT 0",
        "ALTER TABLE knowledge_documents ADD COLUMN priority INTEGER DEFAULT 5",
        "ALTER TABLE knowledge_documents ADD COLUMN is_active BOOLEAN DEFAULT TRUE",
    ]:
        op.execute(f"""
            DO $$ BEGIN {col_sql}; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
        """)

    # ──────────────────────────────────────────────────────────
    # Part B: Fix nullable mismatches (align DB to ORM definitions)
    # ──────────────────────────────────────────────────────────

    # B1: SET NOT NULL where ORM declares nullable=False but DB is nullable
    #     Fill NULLs with safe defaults first to avoid constraint violation.

    # created_at columns (6 tables) — default to NOW()
    for table in [
        'comb_assessments',
        'health_competency_assessments',
        'obstacle_assessments',
        'self_efficacy_assessments',
        'support_assessments',
        'user_change_cause_scores',
    ]:
        op.execute(f"UPDATE {table} SET created_at = NOW() WHERE created_at IS NULL")
        op.alter_column(table, 'created_at', nullable=False)

    # knowledge_chunks.chunk_index — default to 0
    op.execute("UPDATE knowledge_chunks SET chunk_index = 0 WHERE chunk_index IS NULL")
    op.alter_column('knowledge_chunks', 'chunk_index', nullable=False)

    # knowledge_documents.file_hash — generate placeholder for NULLs
    op.execute("""
        UPDATE knowledge_documents
           SET file_hash = md5(title || '-' || id::text)
         WHERE file_hash IS NULL
    """)
    op.alter_column('knowledge_documents', 'file_hash', nullable=False)

    # B2: DROP NOT NULL where ORM declares nullable=True but DB is NOT NULL
    op.alter_column('course_modules', 'tier', nullable=True)
    op.alter_column('knowledge_chunks', 'scope', nullable=True)
    op.alter_column('knowledge_documents', 'scope', nullable=True)
    op.alter_column('promotion_applications', 'companion_snapshot', nullable=True)
    op.alter_column('promotion_applications', 'credit_snapshot', nullable=True)
    op.alter_column('promotion_applications', 'point_snapshot', nullable=True)
    op.alter_column('user_credits', 'completed_at', nullable=True)

    # ──────────────────────────────────────────────────────────
    # Part C: Widen real VARCHAR columns (skip PG enum columns)
    #         Only WIDEN — never shrink. Safe, zero data loss.
    #         None of these are referenced by views.
    # ──────────────────────────────────────────────────────────
    varchar_fixes = [
        # table, column, new_length  (DB current → ORM target)
        ('course_modules',          'content_ref',    500),   # 200 → 500
        ('knowledge_chunks',        'heading',        255),   # 200 → 255
        ('knowledge_chunks',        'doc_source',     255),   # 200 → 255
        ('knowledge_chunks',        'scope',          50),    # 20 → 50
        ('knowledge_documents',     'file_type',      50),    # 10 → 50
        ('knowledge_documents',     'scope',          50),    # 20 → 50
        ('knowledge_documents',     'source',         255),   # 200 → 255
        ('user_credits',            'evidence_ref',   500),   # 200 → 500
    ]
    for table, col, new_len in varchar_fixes:
        op.alter_column(table, col, type_=sa.String(new_len))


def downgrade() -> None:
    # ── Part C reverse: shrink varchar back ──
    varchar_reverse = [
        ('course_modules',          'content_ref',    200),
        ('knowledge_chunks',        'heading',        200),
        ('knowledge_chunks',        'doc_source',     200),
        ('knowledge_chunks',        'scope',          20),
        ('knowledge_documents',     'file_type',      10),
        ('knowledge_documents',     'scope',          20),
        ('knowledge_documents',     'source',         200),
        ('user_credits',            'evidence_ref',   200),
    ]
    for table, col, old_len in varchar_reverse:
        op.alter_column(table, col, type_=sa.String(old_len))

    # ── Part B reverse: restore original nullable ──
    op.alter_column('user_credits', 'completed_at', nullable=False)
    op.alter_column('promotion_applications', 'point_snapshot', nullable=False)
    op.alter_column('promotion_applications', 'credit_snapshot', nullable=False)
    op.alter_column('promotion_applications', 'companion_snapshot', nullable=False)
    op.alter_column('knowledge_documents', 'scope', nullable=False)
    op.alter_column('knowledge_chunks', 'scope', nullable=False)
    op.alter_column('course_modules', 'tier', nullable=False)

    op.alter_column('knowledge_documents', 'file_hash', nullable=True)
    op.alter_column('knowledge_chunks', 'chunk_index', nullable=True)
    for table in [
        'user_change_cause_scores', 'support_assessments',
        'self_efficacy_assessments', 'obstacle_assessments',
        'health_competency_assessments', 'comb_assessments',
    ]:
        op.alter_column(table, 'created_at', nullable=True)

    # ── Part A reverse: drop added columns ──
    op.drop_column('knowledge_documents', 'is_active')
    op.drop_column('knowledge_documents', 'priority')
    op.drop_column('knowledge_documents', 'file_size')
    op.drop_column('knowledge_documents', 'chunk_count')
    op.drop_column('knowledge_documents', 'description')
    op.drop_column('knowledge_chunks', 'metadata')
