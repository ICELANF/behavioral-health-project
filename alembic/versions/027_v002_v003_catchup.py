"""catchup migration: formalize V002 credit system + V003 incentive tables into Alembic chain

Revision ID: 027
Revises: 026
Create Date: 2026-02-12

Summary:
  V002 credit/promotion tables (4) and V003 incentive tables (9) were originally
  created via raw SQL outside the Alembic chain. This migration formalizes them
  using IF NOT EXISTS guards so it's safe for existing databases while enabling
  fresh deployments via `alembic upgrade head`.

  V002 tables: course_modules, user_credits, companion_relations, promotion_applications
  V002 views:  v_user_credit_summary, v_user_total_credits, v_companion_stats, v_promotion_progress
  V003 tables: badges, user_badges, user_milestones, user_streaks,
               flip_card_records, nudge_records, user_memorials,
               point_transactions, user_points
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # V002 — Credit & Promotion System (4 tables + enums + views)
    # ================================================================

    # -- Enums (safe: DO/EXCEPTION) --
    op.execute("""
        DO $$ BEGIN
          CREATE TYPE course_module_type AS ENUM (
            'M1_BEHAVIOR','M2_LIFESTYLE','M3_MINDSET','M4_COACHING','ELECTIVE'
          );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
          CREATE TYPE elective_category AS ENUM (
            'clinical','nutrition','exercise','psychology','coaching_tech','humanities','scenario'
          );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
          CREATE TYPE intervention_tier AS ENUM ('T1_PRESCRIPTION','T2_HEALTH','T3_GROWTH');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
          CREATE TYPE assessment_type AS ENUM (
            'theory_exam','case_review','practice_demo','peer_review','expert_review','effectiveness'
          );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # -- course_modules --
    op.execute("""
        CREATE TABLE IF NOT EXISTS course_modules (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          code VARCHAR(32) UNIQUE NOT NULL,
          title VARCHAR(200) NOT NULL,
          description TEXT,
          module_type course_module_type NOT NULL,
          elective_cat elective_category,
          tier intervention_tier,
          target_role userrole NOT NULL,
          credit_value INTEGER NOT NULL DEFAULT 5,
          theory_ratio DECIMAL(3,2) DEFAULT 0.50,
          prereq_modules UUID[],
          content_ref VARCHAR(500),
          is_active BOOLEAN DEFAULT true,
          sort_order INTEGER DEFAULT 0,
          created_at TIMESTAMPTZ DEFAULT NOW(),
          updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_cm_type_role ON course_modules(module_type, target_role);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cm_tier ON course_modules(tier);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cm_active ON course_modules(is_active) WHERE is_active = true;")

    # -- user_credits --
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_credits (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id BIGINT NOT NULL REFERENCES users(id),
          module_id UUID NOT NULL REFERENCES course_modules(id),
          credit_earned INTEGER NOT NULL,
          score DECIMAL(5,2),
          completed_at TIMESTAMPTZ DEFAULT NOW(),
          evidence_type assessment_type,
          evidence_ref VARCHAR(500),
          reviewer_id BIGINT REFERENCES users(id),
          created_at TIMESTAMPTZ DEFAULT NOW(),
          UNIQUE(user_id, module_id)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_uc_user ON user_credits(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_uc_module ON user_credits(module_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_uc_completed ON user_credits(completed_at);")

    # -- companion_relations --
    op.execute("""
        CREATE TABLE IF NOT EXISTS companion_relations (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          mentor_id BIGINT NOT NULL REFERENCES users(id),
          mentee_id BIGINT NOT NULL REFERENCES users(id),
          mentor_role userrole NOT NULL,
          mentee_role userrole NOT NULL,
          status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','graduated','dropped')),
          started_at TIMESTAMPTZ DEFAULT NOW(),
          graduated_at TIMESTAMPTZ,
          quality_score DECIMAL(5,2),
          notes TEXT,
          UNIQUE(mentor_id, mentee_id)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_cr_mentor ON companion_relations(mentor_id, status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cr_mentee ON companion_relations(mentee_id);")

    # -- promotion_applications --
    op.execute("""
        CREATE TABLE IF NOT EXISTS promotion_applications (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id BIGINT NOT NULL REFERENCES users(id),
          from_role userrole NOT NULL,
          to_role userrole NOT NULL,
          status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','withdrawn')),
          credit_snapshot JSONB,
          point_snapshot JSONB,
          companion_snapshot JSONB,
          practice_snapshot JSONB,
          check_result JSONB,
          reviewer_id BIGINT REFERENCES users(id),
          review_comment TEXT,
          reviewed_at TIMESTAMPTZ,
          created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_pa_user ON promotion_applications(user_id, status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_pa_status ON promotion_applications(status);")

    # -- V002 Views --
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
          SUM(CASE WHEN cm.module_type != 'ELECTIVE' THEN uc.credit_earned ELSE 0 END) AS mandatory_credits,
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
    op.execute("""
        CREATE OR REPLACE VIEW v_promotion_progress AS
        SELECT u.id AS user_id, u.role AS current_role,
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

    # -- V002 Constraints (safe: DROP IF EXISTS + ADD) --
    op.execute("ALTER TABLE course_modules DROP CONSTRAINT IF EXISTS chk_elective_cat;")
    op.execute("""
        ALTER TABLE course_modules ADD CONSTRAINT chk_elective_cat CHECK (
          (module_type = 'ELECTIVE' AND elective_cat IS NOT NULL) OR
          (module_type != 'ELECTIVE' AND elective_cat IS NULL)
        );
    """)
    op.execute("ALTER TABLE companion_relations DROP CONSTRAINT IF EXISTS chk_no_self_mentor;")
    op.execute("ALTER TABLE companion_relations ADD CONSTRAINT chk_no_self_mentor CHECK (mentor_id != mentee_id);")
    op.execute("ALTER TABLE promotion_applications DROP CONSTRAINT IF EXISTS chk_valid_promotion;")
    op.execute("""
        ALTER TABLE promotion_applications ADD CONSTRAINT chk_valid_promotion CHECK (
          (from_role = 'OBSERVER' AND to_role = 'GROWER') OR
          (from_role = 'GROWER' AND to_role = 'SHARER') OR
          (from_role = 'SHARER' AND to_role = 'COACH') OR
          (from_role = 'COACH' AND to_role = 'PROMOTER') OR
          (from_role = 'PROMOTER' AND to_role = 'MASTER')
        );
    """)

    # -- V002 Trigger --
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_cm_updated_at ON course_modules;")
    op.execute("""
        CREATE TRIGGER trg_cm_updated_at
          BEFORE UPDATE ON course_modules
          FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    """)

    # ================================================================
    # V003 — Incentive System (9 tables + 3 enums)
    # ================================================================

    # -- Enums --
    op.execute("""
        DO $$ BEGIN
          CREATE TYPE badge_rarity AS ENUM ('common','uncommon','rare','epic','legendary');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
          CREATE TYPE milestone_key AS ENUM (
            'FIRST_LOGIN','DAY_3','DAY_7','DAY_14','DAY_21','DAY_30','DAY_60','DAY_90','DAY_180'
          );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
          CREATE TYPE nudge_channel AS ENUM ('in_app','push','wechat','sms');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # -- badges --
    op.execute("""
        CREATE TABLE IF NOT EXISTS badges (
          id VARCHAR(64) PRIMARY KEY,
          name VARCHAR(100) NOT NULL,
          description TEXT,
          category VARCHAR(32) NOT NULL,
          icon VARCHAR(16),
          rarity badge_rarity NOT NULL DEFAULT 'common',
          condition_json JSONB NOT NULL,
          visual_json JSONB,
          sort_order INTEGER DEFAULT 0,
          is_active BOOLEAN DEFAULT true,
          created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_badges_category ON badges(category);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_badges_rarity ON badges(rarity);")

    # -- user_badges --
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id BIGINT NOT NULL REFERENCES users(id),
          badge_id VARCHAR(64) NOT NULL REFERENCES badges(id),
          earned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          metadata JSONB,
          UNIQUE(user_id, badge_id)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_ub_user ON user_badges(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_ub_badge ON user_badges(badge_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_ub_earned ON user_badges(earned_at);")

    # -- user_milestones --
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_milestones (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id BIGINT NOT NULL REFERENCES users(id),
          milestone milestone_key NOT NULL,
          achieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          streak_days INTEGER,
          rewards_json JSONB NOT NULL,
          ritual_played BOOLEAN DEFAULT false,
          UNIQUE(user_id, milestone)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_um_user ON user_milestones(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_um_milestone ON user_milestones(milestone);")

    # -- user_streaks --
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_streaks (
          user_id BIGINT PRIMARY KEY REFERENCES users(id),
          current_streak INTEGER NOT NULL DEFAULT 0,
          longest_streak INTEGER NOT NULL DEFAULT 0,
          last_checkin_date DATE,
          grace_used_month INTEGER DEFAULT 0,
          recovery_count INTEGER DEFAULT 0,
          updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # -- flip_card_records --
    op.execute("""
        CREATE TABLE IF NOT EXISTS flip_card_records (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id BIGINT NOT NULL REFERENCES users(id),
          pool_id VARCHAR(64) NOT NULL,
          shown_items JSONB NOT NULL,
          chosen_item_id VARCHAR(64) NOT NULL,
          reward_json JSONB NOT NULL,
          created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_fcr_user ON flip_card_records(user_id);")

    # -- nudge_records --
    op.execute("""
        CREATE TABLE IF NOT EXISTS nudge_records (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id BIGINT NOT NULL REFERENCES users(id),
          milestone milestone_key,
          channel nudge_channel NOT NULL,
          title VARCHAR(200),
          message TEXT,
          sent_at TIMESTAMPTZ DEFAULT NOW(),
          opened_at TIMESTAMPTZ,
          acted_on BOOLEAN DEFAULT false
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_nr_user ON nudge_records(user_id, sent_at);")

    # -- user_memorials --
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_memorials (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id BIGINT NOT NULL REFERENCES users(id),
          type VARCHAR(64) NOT NULL,
          template VARCHAR(64),
          data_snapshot JSONB NOT NULL,
          asset_url VARCHAR(500),
          shared_count INTEGER DEFAULT 0,
          created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_umem_user ON user_memorials(user_id);")

    # -- point_transactions --
    op.execute("""
        CREATE TABLE IF NOT EXISTS point_transactions (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id BIGINT NOT NULL REFERENCES users(id),
          point_type VARCHAR(32) NOT NULL,
          amount INTEGER NOT NULL,
          action VARCHAR(64) NOT NULL,
          created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_ptx_user ON point_transactions(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_ptx_action ON point_transactions(action);")

    # -- user_points --
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_points (
          user_id BIGINT NOT NULL REFERENCES users(id),
          point_type VARCHAR(32) NOT NULL,
          total_points INTEGER NOT NULL DEFAULT 0,
          PRIMARY KEY (user_id, point_type)
        );
    """)

    # -- V003 streak view --
    op.execute("""
        CREATE OR REPLACE VIEW v_user_streak_status AS
        SELECT
          user_id,
          current_streak,
          longest_streak,
          last_checkin_date,
          CASE
            WHEN last_checkin_date = CURRENT_DATE THEN 'checked_in'
            WHEN last_checkin_date = CURRENT_DATE - 1 THEN 'pending'
            ELSE 'broken'
          END AS streak_status
        FROM user_streaks;
    """)

    # -- V003 streak function --
    op.execute("""
        CREATE OR REPLACE FUNCTION compute_streak_status(uid BIGINT)
        RETURNS TABLE(current_streak INT, longest_streak INT, status TEXT) AS $$
        SELECT
          s.current_streak,
          s.longest_streak,
          CASE
            WHEN s.last_checkin_date = CURRENT_DATE THEN 'checked_in'
            WHEN s.last_checkin_date = CURRENT_DATE - 1 THEN 'pending'
            ELSE 'broken'
          END
        FROM user_streaks s WHERE s.user_id = uid;
        $$ LANGUAGE sql STABLE;
    """)


def downgrade() -> None:
    # -- V003 function + view --
    op.execute("DROP FUNCTION IF EXISTS compute_streak_status(BIGINT);")
    op.execute("DROP VIEW IF EXISTS v_user_streak_status;")

    # -- V003 tables (reverse order) --
    for t in [
        "user_points", "point_transactions", "user_memorials",
        "nudge_records", "flip_card_records", "user_streaks",
        "user_milestones", "user_badges", "badges",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

    # -- V003 enums --
    op.execute("DROP TYPE IF EXISTS nudge_channel;")
    op.execute("DROP TYPE IF EXISTS milestone_key;")
    op.execute("DROP TYPE IF EXISTS badge_rarity;")

    # -- V002 views --
    op.execute("DROP VIEW IF EXISTS v_promotion_progress;")
    op.execute("DROP VIEW IF EXISTS v_companion_stats;")
    op.execute("DROP VIEW IF EXISTS v_user_total_credits;")
    op.execute("DROP VIEW IF EXISTS v_user_credit_summary;")

    # -- V002 trigger --
    op.execute("DROP TRIGGER IF EXISTS trg_cm_updated_at ON course_modules;")

    # -- V002 tables (reverse order) --
    for t in [
        "promotion_applications", "companion_relations",
        "user_credits", "course_modules",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

    # -- V002 enums --
    op.execute("DROP TYPE IF EXISTS assessment_type;")
    op.execute("DROP TYPE IF EXISTS intervention_tier;")
    op.execute("DROP TYPE IF EXISTS elective_category;")
    op.execute("DROP TYPE IF EXISTS course_module_type;")
