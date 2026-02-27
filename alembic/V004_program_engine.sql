-- ═══════════════════════════════════════════════════════════════
-- BHP平台 智能监测方案引擎 增量迁移
-- 版本: V004_program_engine
-- 日期: 2026-02-09
-- 前提: V003_milestone_incentive_system 已执行
-- 原则: 只新增，不修改已有表结构
-- ═══════════════════════════════════════════════════════════════

BEGIN;

-- ─────────────────────────────────────────
-- 1. 新增枚举类型
-- ─────────────────────────────────────────

DO $$ BEGIN
  CREATE TYPE program_category AS ENUM (
    'glucose', 'weight', 'sleep', 'metabolic', 'exercise', 'custom'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE enrollment_status AS ENUM (
    'active', 'paused', 'completed', 'dropped'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE push_slot AS ENUM (
    'morning', 'noon', 'evening', 'immediate', 'custom'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ─────────────────────────────────────────
-- 2. 方案模板定义表
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS program_templates (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  slug            VARCHAR(64) UNIQUE NOT NULL,     -- glucose-14d, weight-30d
  title           VARCHAR(200) NOT NULL,
  description     TEXT,
  category        program_category NOT NULL DEFAULT 'custom',
  total_days      INTEGER NOT NULL CHECK (total_days > 0 AND total_days <= 365),
  pushes_per_day  INTEGER NOT NULL DEFAULT 3 CHECK (pushes_per_day > 0 AND pushes_per_day <= 6),
  schedule_json   JSONB NOT NULL,                  -- 每天推送时间+内容+调查题
  recommendation_rules JSONB DEFAULT '{"rules":[]}',  -- 算法推荐规则
  tags            JSONB DEFAULT '[]',              -- 标签: ["CGM","血糖","入门"]
  cover_image     VARCHAR(500),                    -- 封面图URL
  is_active       BOOLEAN DEFAULT true,
  is_public       BOOLEAN DEFAULT true,            -- 公开/专家私有
  created_by      BIGINT REFERENCES users(id),
  tenant_id       VARCHAR REFERENCES expert_tenants(id),  -- NULL=平台级
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pt_slug ON program_templates(slug);
CREATE INDEX IF NOT EXISTS idx_pt_category ON program_templates(category);
CREATE INDEX IF NOT EXISTS idx_pt_active ON program_templates(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_pt_tenant ON program_templates(tenant_id);

-- ─────────────────────────────────────────
-- 3. 用户参与实例表
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS program_enrollments (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         BIGINT NOT NULL REFERENCES users(id),
  template_id     UUID NOT NULL REFERENCES program_templates(id),
  start_date      DATE NOT NULL DEFAULT CURRENT_DATE,
  current_day     INTEGER NOT NULL DEFAULT 0,      -- 0-indexed, 第0天=报名当天
  status          enrollment_status NOT NULL DEFAULT 'active',
  behavior_profile JSONB DEFAULT '{}',             -- 行为轨迹累计数据
  custom_schedule JSONB,                           -- 个人化覆盖, NULL=用模板默认
  push_preferences JSONB DEFAULT '{"morning":"09:00","noon":"11:30","evening":"17:30"}',
  coach_id        BIGINT REFERENCES users(id),     -- 分配的教练
  paused_at       TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ,
  dropped_at      TIMESTAMPTZ,
  drop_reason     TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
);

-- 同一用户同一模板同时只能有一个active/paused实例 (允许completed/dropped后重新加入)
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_enrollment
  ON program_enrollments (user_id, template_id)
  WHERE status IN ('active', 'paused');

CREATE INDEX IF NOT EXISTS idx_pe_user ON program_enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_pe_template ON program_enrollments(template_id);
CREATE INDEX IF NOT EXISTS idx_pe_status ON program_enrollments(status);
CREATE INDEX IF NOT EXISTS idx_pe_coach ON program_enrollments(coach_id);
CREATE INDEX IF NOT EXISTS idx_pe_active ON program_enrollments(status, start_date)
  WHERE status = 'active';

-- ─────────────────────────────────────────
-- 4. 每次交互记录表
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS program_interactions (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  enrollment_id   UUID NOT NULL REFERENCES program_enrollments(id) ON DELETE CASCADE,
  day_number      INTEGER NOT NULL CHECK (day_number >= 0),
  slot            push_slot NOT NULL,
  push_sent_at    TIMESTAMPTZ,                     -- 推送发出时间
  push_opened_at  TIMESTAMPTZ,                     -- 用户打开时间
  push_content    JSONB NOT NULL DEFAULT '{}',     -- 推送的完整内容快照
  survey_questions JSONB DEFAULT '[]',             -- 此次推送嵌入的调查题
  survey_answers  JSONB,                           -- 用户回答(NULL=未回答)
  answered_at     TIMESTAMPTZ,                     -- 回答时间
  photo_urls      JSONB DEFAULT '[]',              -- 打卡照片URLs
  device_data_snapshot JSONB,                      -- 设备数据快照(血糖/体重等)
  recommended_content JSONB DEFAULT '[]',          -- 算法推荐的学习资料
  user_feedback   JSONB,                           -- 用户对推荐的反馈
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  -- 同一enrollment的同一天同一时段只能有一条记录
  CONSTRAINT uq_interaction UNIQUE (enrollment_id, day_number, slot)
);

CREATE INDEX IF NOT EXISTS idx_pi_enrollment ON program_interactions(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_pi_day ON program_interactions(enrollment_id, day_number);
CREATE INDEX IF NOT EXISTS idx_pi_sent ON program_interactions(push_sent_at);
CREATE INDEX IF NOT EXISTS idx_pi_unanswered ON program_interactions(enrollment_id)
  WHERE survey_answers IS NULL AND survey_questions != '[]'::jsonb;

-- ─────────────────────────────────────────
-- 5. 视图: 方案参与概览
-- ─────────────────────────────────────────

CREATE OR REPLACE VIEW v_program_enrollment_summary AS
SELECT
  pe.id AS enrollment_id,
  pe.user_id,
  pe.template_id,
  pt.slug AS template_slug,
  pt.title AS template_title,
  pt.category,
  pt.total_days,
  pe.current_day,
  pe.status,
  pe.start_date,
  pe.coach_id,
  -- 进度百分比
  ROUND(pe.current_day::numeric / NULLIF(pt.total_days, 0) * 100, 1) AS progress_pct,
  -- 交互统计
  (SELECT COUNT(*) FROM program_interactions pi
   WHERE pi.enrollment_id = pe.id) AS total_pushes,
  (SELECT COUNT(*) FROM program_interactions pi
   WHERE pi.enrollment_id = pe.id AND pi.survey_answers IS NOT NULL) AS answered_count,
  (SELECT COUNT(*) FROM program_interactions pi
   WHERE pi.enrollment_id = pe.id AND pi.photo_urls != '[]'::jsonb) AS photo_count,
  -- 最近交互
  (SELECT MAX(pi.answered_at) FROM program_interactions pi
   WHERE pi.enrollment_id = pe.id) AS last_interaction_at,
  -- 行为特征
  pe.behavior_profile
FROM program_enrollments pe
JOIN program_templates pt ON pe.template_id = pt.id;

-- ─────────────────────────────────────────
-- 6. 视图: 今日待推送
-- ─────────────────────────────────────────

CREATE OR REPLACE VIEW v_program_today_pushes AS
SELECT
  pe.id AS enrollment_id,
  pe.user_id,
  pe.template_id,
  pt.slug AS template_slug,
  pe.current_day,
  pe.push_preferences,
  pt.schedule_json,
  pe.coach_id
FROM program_enrollments pe
JOIN program_templates pt ON pe.template_id = pt.id
WHERE pe.status = 'active'
  AND pe.current_day <= pt.total_days;

-- ─────────────────────────────────────────
-- 7. 函数: 推进用户方案天数
-- ─────────────────────────────────────────

CREATE OR REPLACE FUNCTION advance_program_day(p_enrollment_id UUID)
RETURNS TABLE(
  new_day INTEGER,
  is_completed BOOLEAN,
  milestone_day BOOLEAN
) AS $$
DECLARE
  v_enrollment RECORD;
  v_total_days INTEGER;
  v_new_day INTEGER;
  v_completed BOOLEAN := false;
  v_milestone BOOLEAN := false;
BEGIN
  -- 获取enrollment和template信息
  SELECT pe.*, pt.total_days INTO v_enrollment
  FROM program_enrollments pe
  JOIN program_templates pt ON pe.template_id = pt.id
  WHERE pe.id = p_enrollment_id
  FOR UPDATE OF pe;

  IF NOT FOUND OR v_enrollment.status != 'active' THEN
    new_day := COALESCE(v_enrollment.current_day, -1);
    is_completed := false;
    milestone_day := false;
    RETURN NEXT;
    RETURN;
  END IF;

  v_new_day := v_enrollment.current_day + 1;

  -- 检查是否完成
  IF v_new_day >= v_enrollment.total_days THEN
    v_completed := true;
    UPDATE program_enrollments SET
      current_day = v_new_day,
      status = 'completed',
      completed_at = NOW(),
      updated_at = NOW()
    WHERE id = p_enrollment_id;
  ELSE
    UPDATE program_enrollments SET
      current_day = v_new_day,
      updated_at = NOW()
    WHERE id = p_enrollment_id;
  END IF;

  -- 检查里程碑天(第7天、第14天)
  IF v_new_day IN (7, 14, 21, 30, 60, 90, 180) THEN
    v_milestone := true;
  END IF;

  new_day := v_new_day;
  is_completed := v_completed;
  milestone_day := v_milestone;
  RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- ─────────────────────────────────────────
-- 8. 函数: 计算交互完成率
-- ─────────────────────────────────────────

CREATE OR REPLACE FUNCTION calc_interaction_rate(
  p_enrollment_id UUID,
  p_window_days INTEGER DEFAULT 7
)
RETURNS TABLE(
  total_expected INTEGER,
  total_answered INTEGER,
  completion_rate NUMERIC,
  core_completion_rate NUMERIC
) AS $$
DECLARE
  v_enrollment RECORD;
  v_start_day INTEGER;
BEGIN
  SELECT * INTO v_enrollment
  FROM program_enrollments
  WHERE id = p_enrollment_id;

  v_start_day := GREATEST(0, v_enrollment.current_day - p_window_days);

  SELECT
    COUNT(*),
    COUNT(*) FILTER (WHERE survey_answers IS NOT NULL),
    ROUND(
      COUNT(*) FILTER (WHERE survey_answers IS NOT NULL)::numeric /
      NULLIF(COUNT(*), 0) * 100, 1
    ),
    ROUND(
      COUNT(*) FILTER (
        WHERE survey_answers IS NOT NULL
        AND (push_content->>'is_core')::boolean = true
      )::numeric /
      NULLIF(COUNT(*) FILTER (
        WHERE (push_content->>'is_core')::boolean = true
      ), 0) * 100, 1
    )
  INTO total_expected, total_answered, completion_rate, core_completion_rate
  FROM program_interactions
  WHERE enrollment_id = p_enrollment_id
    AND day_number BETWEEN v_start_day AND v_enrollment.current_day;

  RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- ─────────────────────────────────────────
-- 9. 触发器: 更新updated_at
-- ─────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_program_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_pt_updated ON program_templates;
CREATE TRIGGER trg_pt_updated BEFORE UPDATE ON program_templates
  FOR EACH ROW EXECUTE FUNCTION update_program_timestamp();

DROP TRIGGER IF EXISTS trg_pe_updated ON program_enrollments;
CREATE TRIGGER trg_pe_updated BEFORE UPDATE ON program_enrollments
  FOR EACH ROW EXECUTE FUNCTION update_program_timestamp();

COMMIT;
