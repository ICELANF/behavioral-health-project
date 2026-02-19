# -*- coding: utf-8 -*-
"""Catchup: program tables + missing views + seed data

Revision ID: 045
Revises: 044
Create Date: 2026-02-18

Summary:
  Formalizes tables/views that were created via manual SQL during the
  96/96 full-platform test pass. Uses IF NOT EXISTS / OR REPLACE guards
  so it's safe for both existing databases and fresh deployments.

  New tables:
    - program_templates (UUID PK, V004 program engine)
    - program_enrollments (UUID PK, FK → program_templates)
    - program_interactions (UUID PK, FK → program_enrollments)

  Missing tables from prior migrations (034, 044) that may not have applied:
    - reflection_journals (migration 034)
    - coach_review_queue (migration 044)
    - coach_review_logs columns: elapsed_seconds, reviewed_at

  Views (from migration 027 that may not have executed):
    - v_user_credit_summary
    - v_user_total_credits
    - v_companion_stats
    - v_program_enrollment_summary (new)

  Seed data:
    - glucose-14d program template
"""
from alembic import op
import sqlalchemy as sa

revision = "045"
down_revision = "044"
branch_labels = None
depends_on = None


def upgrade():
    # ════════════════════════════════════════════
    # 1. program_templates (V004 — never had migration)
    # ════════════════════════════════════════════
    op.execute("""
    CREATE TABLE IF NOT EXISTS program_templates (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        slug VARCHAR(100) UNIQUE NOT NULL,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        category VARCHAR(50) DEFAULT 'general',
        total_days INTEGER NOT NULL DEFAULT 14,
        pushes_per_day INTEGER DEFAULT 3,
        schedule_json JSONB,
        recommendation_rules JSONB,
        tags JSONB DEFAULT '[]'::jsonb,
        cover_image VARCHAR(500),
        is_active BOOLEAN DEFAULT true,
        is_public BOOLEAN DEFAULT true,
        tenant_id VARCHAR(50),
        created_by INTEGER,
        created_at TIMESTAMP NOT NULL DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_pt_slug ON program_templates(slug);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_pt_category ON program_templates(category);")

    # ════════════════════════════════════════════
    # 2. program_enrollments
    # ════════════════════════════════════════════
    op.execute("""
    CREATE TABLE IF NOT EXISTS program_enrollments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id INTEGER NOT NULL REFERENCES users(id),
        template_id UUID REFERENCES program_templates(id),
        start_date DATE NOT NULL DEFAULT CURRENT_DATE,
        current_day INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'active',
        push_preferences JSONB DEFAULT '{}'::jsonb,
        custom_schedule JSONB,
        coach_id INTEGER,
        behavior_profile JSONB,
        completed_at TIMESTAMP,
        created_at TIMESTAMP NOT NULL DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_pe_user ON program_enrollments(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_pe_template ON program_enrollments(template_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_pe_status ON program_enrollments(status);")

    # ════════════════════════════════════════════
    # 3. program_interactions
    # ════════════════════════════════════════════
    op.execute("""
    CREATE TABLE IF NOT EXISTS program_interactions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        enrollment_id UUID REFERENCES program_enrollments(id),
        day_number INTEGER NOT NULL,
        push_index INTEGER DEFAULT 0,
        push_content TEXT,
        user_reply TEXT,
        agent_response TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP NOT NULL DEFAULT now()
    );
    """)
    # Ensure columns needed by views exist (pre-existing tables may have different schema)
    op.execute("ALTER TABLE program_interactions ADD COLUMN IF NOT EXISTS user_reply TEXT;")
    op.execute("ALTER TABLE program_interactions ADD COLUMN IF NOT EXISTS agent_response TEXT;")
    op.execute("ALTER TABLE program_interactions ADD COLUMN IF NOT EXISTS push_index INTEGER DEFAULT 0;")
    op.execute("ALTER TABLE program_interactions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';")
    op.execute("CREATE INDEX IF NOT EXISTS idx_pi_enrollment ON program_interactions(enrollment_id, day_number);")

    # ════════════════════════════════════════════
    # 4. reflection_journals (migration 034 may not have applied)
    # ════════════════════════════════════════════
    op.execute("""
    CREATE TABLE IF NOT EXISTS reflection_journals (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        title VARCHAR(200),
        content TEXT NOT NULL,
        journal_type VARCHAR(30) DEFAULT 'freeform',
        reflection_depth FLOAT DEFAULT 0.0,
        depth_level VARCHAR(20) DEFAULT 'surface',
        agency_mode_at_time VARCHAR(20),
        tags JSONB DEFAULT '[]'::jsonb,
        prompt_used VARCHAR(200),
        created_at TIMESTAMP NOT NULL DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_rj_user ON reflection_journals(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rj_type ON reflection_journals(journal_type);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rj_created ON reflection_journals(created_at);")

    # ════════════════════════════════════════════
    # 5. coach_review_queue (migration 044 may not have applied)
    # ════════════════════════════════════════════
    op.execute("""
    CREATE TABLE IF NOT EXISTS coach_review_queue (
        id VARCHAR(50) PRIMARY KEY,
        coach_id INTEGER NOT NULL REFERENCES users(id),
        student_id INTEGER NOT NULL REFERENCES users(id),
        type VARCHAR(20) NOT NULL,
        priority VARCHAR(10) DEFAULT 'normal' NOT NULL,
        status VARCHAR(20) DEFAULT 'pending' NOT NULL,
        ai_summary TEXT,
        rx_fields_json JSONB,
        ai_draft TEXT,
        push_type VARCHAR(50),
        push_content TEXT,
        review_note TEXT,
        edited_content TEXT,
        edited_rx_json JSONB,
        reviewed_at TIMESTAMP,
        elapsed_seconds INTEGER,
        created_at TIMESTAMP NOT NULL DEFAULT now(),
        picked_at TIMESTAMP
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_review_coach_status ON coach_review_queue(coach_id, status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_review_priority ON coach_review_queue(priority, created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_review_student ON coach_review_queue(student_id, created_at);")

    # ════════════════════════════════════════════
    # 6. coach_review_logs — add missing columns
    # ════════════════════════════════════════════
    op.execute("ALTER TABLE coach_review_logs ADD COLUMN IF NOT EXISTS elapsed_seconds INTEGER;")
    op.execute("ALTER TABLE coach_review_logs ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP DEFAULT now();")

    # ════════════════════════════════════════════
    # 7. Views (from migration 027 that may not have executed)
    #    Drop first to handle column changes safely
    # ════════════════════════════════════════════
    op.execute("DROP VIEW IF EXISTS v_user_credit_summary CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_user_total_credits CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_companion_stats CASCADE;")

    op.execute("""
    CREATE OR REPLACE VIEW v_user_credit_summary AS
    SELECT uc.user_id, cm.module_type, cm.target_role,
      SUM(uc.credit_earned) AS credits, COUNT(*) AS modules_completed
    FROM user_credits uc JOIN course_modules cm ON uc.module_id = cm.id
    WHERE cm.is_active = true GROUP BY uc.user_id, cm.module_type, cm.target_role;
    """)

    op.execute("""
    CREATE OR REPLACE VIEW v_user_total_credits AS
    SELECT uc.user_id,
      SUM(uc.credit_earned) AS total_credits,
      SUM(CASE WHEN cm.module_type <> 'ELECTIVE' THEN uc.credit_earned ELSE 0 END) AS mandatory_credits,
      SUM(CASE WHEN cm.module_type = 'ELECTIVE' THEN uc.credit_earned ELSE 0 END) AS elective_credits,
      SUM(CASE WHEN cm.module_type = 'M1_BEHAVIOR' THEN uc.credit_earned ELSE 0 END) AS m1_credits,
      SUM(CASE WHEN cm.module_type = 'M2_LIFESTYLE' THEN uc.credit_earned ELSE 0 END) AS m2_credits,
      SUM(CASE WHEN cm.module_type = 'M3_MINDSET' THEN uc.credit_earned ELSE 0 END) AS m3_credits,
      SUM(CASE WHEN cm.module_type = 'M4_COACHING' THEN uc.credit_earned ELSE 0 END) AS m4_credits
    FROM user_credits uc JOIN course_modules cm ON uc.module_id = cm.id GROUP BY uc.user_id;
    """)

    op.execute("""
    CREATE OR REPLACE VIEW v_companion_stats AS
    SELECT cr.mentor_id, cr.mentor_role,
      COUNT(*) FILTER (WHERE cr.status = 'graduated') AS graduated_count,
      COUNT(*) FILTER (WHERE cr.status = 'active') AS active_count,
      COUNT(*) FILTER (WHERE cr.status = 'dropped') AS dropped_count,
      AVG(cr.quality_score) FILTER (WHERE cr.quality_score IS NOT NULL) AS avg_quality
    FROM companion_relations cr GROUP BY cr.mentor_id, cr.mentor_role;
    """)

    op.execute("DROP VIEW IF EXISTS v_program_enrollment_summary;")
    op.execute("""
    CREATE OR REPLACE VIEW v_program_enrollment_summary AS
    SELECT
        pe.id AS enrollment_id,
        pt.slug AS template_slug,
        pt.title AS template_title,
        pt.category,
        pt.total_days,
        pe.current_day,
        CASE WHEN pt.total_days > 0
             THEN ROUND((pe.current_day::numeric / pt.total_days) * 100, 1)
             ELSE 0 END AS progress_pct,
        pe.status,
        pe.user_id,
        pe.start_date,
        pe.coach_id,
        COALESCE((SELECT COUNT(*) FROM program_interactions pi
                  WHERE pi.enrollment_id = pe.id), 0) AS total_pushes,
        COALESCE((SELECT COUNT(*) FROM program_interactions pi
                  WHERE pi.enrollment_id = pe.id AND pi.user_reply IS NOT NULL), 0) AS answered_count,
        COALESCE((SELECT COUNT(*) FROM program_interactions pi
                  WHERE pi.enrollment_id = pe.id AND pi.user_reply LIKE '%photo%'), 0) AS photo_count,
        pe.updated_at AS last_interaction_at,
        pe.completed_at,
        pe.created_at
    FROM program_enrollments pe
    LEFT JOIN program_templates pt ON pe.template_id = pt.id;
    """)

    # ════════════════════════════════════════════
    # 7b. Recreate v_promotion_progress (depends on base views, may have been dropped by CASCADE)
    # ════════════════════════════════════════════
    op.execute("""
    CREATE OR REPLACE VIEW v_promotion_progress AS
    SELECT u.id AS user_id,
        u.role AS current_role,
        COALESCE(tc.total_credits, 0) AS total_credits,
        COALESCE(tc.mandatory_credits, 0) AS mandatory_credits,
        COALESCE(tc.m1_credits, 0) AS m1_credits,
        COALESCE(tc.m2_credits, 0) AS m2_credits,
        COALESCE(tc.m3_credits, 0) AS m3_credits,
        COALESCE(tc.m4_credits, 0) AS m4_credits,
        COALESCE(up.growth_points, 0) AS growth_points,
        COALESCE(up.contribution_points, 0) AS contribution_points,
        COALESCE(up.influence_points, 0) AS influence_points,
        COALESCE(cs.graduated_count, 0) AS companions_graduated,
        COALESCE(cs.active_count, 0) AS companions_active,
        COALESCE(cs.avg_quality, 0) AS companion_avg_quality
    FROM users u
    LEFT JOIN v_user_total_credits tc ON u.id = tc.user_id
    LEFT JOIN user_learning_stats up ON u.id = up.user_id
    LEFT JOIN v_companion_stats cs ON u.id = cs.mentor_id AND u.role = cs.mentor_role;
    """)

    # ════════════════════════════════════════════
    # 8. Seed data — glucose-14d program template
    # ════════════════════════════════════════════
    op.execute("""
    INSERT INTO program_templates (id, slug, title, description, category, total_days, pushes_per_day, schedule_json)
    VALUES (
        '00000000-0000-0000-0000-000000000001',
        'glucose-14d',
        '14天血糖管理方案',
        '基础代谢健康管理方案，涵盖饮食、运动、监测三大模块',
        'metabolic',
        14,
        3,
        '{}'::jsonb
    ) ON CONFLICT (slug) DO NOTHING;
    """)


def downgrade():
    op.execute("DROP VIEW IF EXISTS v_program_enrollment_summary;")
    op.execute("DROP VIEW IF EXISTS v_companion_stats;")
    op.execute("DROP VIEW IF EXISTS v_user_total_credits;")
    op.execute("DROP VIEW IF EXISTS v_user_credit_summary;")
    op.execute("DROP TABLE IF EXISTS program_interactions;")
    op.execute("DROP TABLE IF EXISTS program_enrollments;")
    op.execute("DROP TABLE IF EXISTS program_templates;")
    op.execute("DROP TABLE IF EXISTS reflection_journals;")
    op.execute("DROP TABLE IF EXISTS coach_review_queue;")
