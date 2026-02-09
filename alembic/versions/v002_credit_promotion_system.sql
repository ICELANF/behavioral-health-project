BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
  CREATE TYPE course_module_type AS ENUM ('M1_BEHAVIOR','M2_LIFESTYLE','M3_MINDSET','M4_COACHING','ELECTIVE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE elective_category AS ENUM ('clinical','nutrition','exercise','psychology','coaching_tech','humanities','scenario');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE intervention_tier AS ENUM ('T1_PRESCRIPTION','T2_HEALTH','T3_GROWTH');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE assessment_type AS ENUM ('theory_exam','case_review','practice_demo','peer_review','expert_review','effectiveness');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS course_modules (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code VARCHAR(32) UNIQUE NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  module_type course_module_type NOT NULL,
  elective_cat elective_category,
  tier intervention_tier NOT NULL,
  target_role userrole NOT NULL,
  credit_value INTEGER NOT NULL DEFAULT 5,
  theory_ratio DECIMAL(3,2) DEFAULT 0.50,
  prereq_modules UUID[],
  content_ref VARCHAR(200),
  is_active BOOLEAN DEFAULT true,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cm_type_role ON course_modules(module_type, target_role);
CREATE INDEX IF NOT EXISTS idx_cm_tier ON course_modules(tier);
CREATE INDEX IF NOT EXISTS idx_cm_active ON course_modules(is_active) WHERE is_active = true;

ALTER TABLE course_modules DROP CONSTRAINT IF EXISTS chk_elective_cat;
ALTER TABLE course_modules ADD CONSTRAINT chk_elective_cat CHECK (
  (module_type = 'ELECTIVE' AND elective_cat IS NOT NULL) OR
  (module_type != 'ELECTIVE' AND elective_cat IS NULL)
);

CREATE TABLE IF NOT EXISTS user_credits (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id BIGINT NOT NULL REFERENCES users(id),
  module_id UUID NOT NULL REFERENCES course_modules(id),
  credit_earned INTEGER NOT NULL,
  score DECIMAL(5,2),
  completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  evidence_type assessment_type,
  evidence_ref VARCHAR(200),
  reviewer_id BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, module_id)
);

CREATE INDEX IF NOT EXISTS idx_uc_user ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_uc_module ON user_credits(module_id);
CREATE INDEX IF NOT EXISTS idx_uc_completed ON user_credits(completed_at);

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

CREATE INDEX IF NOT EXISTS idx_cr_mentor ON companion_relations(mentor_id, status);
CREATE INDEX IF NOT EXISTS idx_cr_mentee ON companion_relations(mentee_id);

ALTER TABLE companion_relations DROP CONSTRAINT IF EXISTS chk_no_self_mentor;
ALTER TABLE companion_relations ADD CONSTRAINT chk_no_self_mentor CHECK (mentor_id != mentee_id);

CREATE TABLE IF NOT EXISTS promotion_applications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id BIGINT NOT NULL REFERENCES users(id),
  from_role userrole NOT NULL,
  to_role userrole NOT NULL,
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','withdrawn')),
  credit_snapshot JSONB NOT NULL,
  point_snapshot JSONB NOT NULL,
  companion_snapshot JSONB NOT NULL,
  practice_snapshot JSONB,
  check_result JSONB,
  reviewer_id BIGINT REFERENCES users(id),
  review_comment TEXT,
  reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pa_user ON promotion_applications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_pa_status ON promotion_applications(status);

ALTER TABLE promotion_applications DROP CONSTRAINT IF EXISTS chk_valid_promotion;
ALTER TABLE promotion_applications ADD CONSTRAINT chk_valid_promotion CHECK (
  (from_role = 'OBSERVER' AND to_role = 'GROWER') OR
  (from_role = 'GROWER' AND to_role = 'SHARER') OR
  (from_role = 'SHARER' AND to_role = 'COACH') OR
  (from_role = 'COACH' AND to_role = 'PROMOTER') OR
  (from_role = 'PROMOTER' AND to_role = 'MASTER')
);

CREATE OR REPLACE VIEW v_user_credit_summary AS
SELECT uc.user_id, cm.module_type, cm.target_role,
  SUM(uc.credit_earned) AS credits, COUNT(*) AS modules_completed
FROM user_credits uc JOIN course_modules cm ON uc.module_id = cm.id
WHERE cm.is_active = true GROUP BY uc.user_id, cm.module_type, cm.target_role;

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

CREATE OR REPLACE VIEW v_companion_stats AS
SELECT cr.mentor_id, cr.mentor_role,
  COUNT(*) FILTER (WHERE cr.status = 'graduated') AS graduated_count,
  COUNT(*) FILTER (WHERE cr.status = 'active') AS active_count,
  COUNT(*) FILTER (WHERE cr.status = 'dropped') AS dropped_count,
  AVG(cr.quality_score) FILTER (WHERE cr.quality_score IS NOT NULL) AS avg_quality
FROM companion_relations cr GROUP BY cr.mentor_id, cr.mentor_role;

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

CREATE OR REPLACE TRIGGER trg_cm_updated_at
  BEFORE UPDATE ON course_modules
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

ALTER TABLE users ALTER COLUMN role SET DEFAULT 'OBSERVER';

COMMIT;
