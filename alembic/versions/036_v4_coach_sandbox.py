"""
036 — 400分制考核 + 收益分配 + 沙箱测试引擎

基于契约注册表⑪Sheet和⑬Sheet:
1. coach_exam_records — 400分制教练考核 (⑪Sheet)
2. revenue_shares — 收益分配系统 (⑪Sheet)
3. sandbox_test_results — 沙箱自动化测试引擎 (⑬Sheet)
4. coach_supervision_records — 教练督导记录 (⑪Sheet)
5. coach_kpi_metrics — 教练KPI红绿灯仪表盘 (⑪Sheet)
6. peer_tracking — 四同道者追踪系统 (⑪Sheet)

Revision ID: 036
Revises: 035
"""
from alembic import op
import sqlalchemy as sa

revision = "036"
down_revision = "035"
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. coach_exam_records (400分制考核) ──────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS coach_exam_records (
        id                      SERIAL PRIMARY KEY,
        coach_id                INTEGER NOT NULL REFERENCES users(id),
        target_level            INTEGER NOT NULL,                           -- 目标教练等级(3-6)
        theory_score            FLOAT DEFAULT 0,                            -- 理论(满分150)
        theory_details          JSONB DEFAULT '{}',                         -- 理论考核明细
        skill_score             FLOAT DEFAULT 0,                            -- 技能(满分150)
        skill_details           JSONB DEFAULT '{}',                         -- 技能考核明细
        comprehensive_score     FLOAT DEFAULT 0,                            -- 综合(满分100)
        comprehensive_details   JSONB DEFAULT '{}',                         -- 综合考核明细
        total_score             FLOAT DEFAULT 0,                            -- 总分(满分400)
        status                  VARCHAR(20) DEFAULT 'in_progress',          -- in_progress/passed/failed/retake
        passed                  BOOLEAN DEFAULT false,                      -- 是否通过
        attempt_number          INTEGER DEFAULT 1,                          -- 考核次数
        examiner_id             INTEGER REFERENCES users(id),               -- 考官ID
        exam_date               DATE,                                       -- 考核日期
        notes                   TEXT,                                       -- 备注
        created_at              TIMESTAMP NOT NULL DEFAULT NOW(),           -- 创建时间
        updated_at              TIMESTAMP NOT NULL DEFAULT NOW()            -- 更新时间
    );
    COMMENT ON TABLE coach_exam_records IS '400分制教练考核记录';
    COMMENT ON COLUMN coach_exam_records.coach_id IS '教练用户ID';
    COMMENT ON COLUMN coach_exam_records.target_level IS '目标教练等级(3-6)';
    COMMENT ON COLUMN coach_exam_records.theory_score IS '理论得分(满分150)';
    COMMENT ON COLUMN coach_exam_records.theory_details IS '理论考核明细JSON';
    COMMENT ON COLUMN coach_exam_records.skill_score IS '技能得分(满分150)';
    COMMENT ON COLUMN coach_exam_records.skill_details IS '技能考核明细JSON';
    COMMENT ON COLUMN coach_exam_records.comprehensive_score IS '综合得分(满分100)';
    COMMENT ON COLUMN coach_exam_records.comprehensive_details IS '综合考核明细JSON';
    COMMENT ON COLUMN coach_exam_records.total_score IS '总分(满分400)';
    COMMENT ON COLUMN coach_exam_records.status IS '状态: in_progress/passed/failed/retake';
    COMMENT ON COLUMN coach_exam_records.passed IS '是否通过';
    COMMENT ON COLUMN coach_exam_records.attempt_number IS '考核次数';
    COMMENT ON COLUMN coach_exam_records.examiner_id IS '考官用户ID';
    COMMENT ON COLUMN coach_exam_records.exam_date IS '考核日期';
    COMMENT ON COLUMN coach_exam_records.notes IS '备注';
    CREATE INDEX IF NOT EXISTS idx_coach_exam_coach_level ON coach_exam_records(coach_id, target_level);
    """)

    # ── 2. revenue_shares (收益分配) ────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS revenue_shares (
        id                  SERIAL PRIMARY KEY,
        beneficiary_id      INTEGER NOT NULL REFERENCES users(id),          -- 受益人ID
        source_type         VARCHAR(30) NOT NULL,                           -- referral/collaboration/service/project/dividend
        source_id           INTEGER,                                        -- 关联实体ID
        amount              FLOAT NOT NULL,                                 -- 金额
        currency            VARCHAR(5) DEFAULT 'CNY',                       -- 货币
        status              VARCHAR(20) DEFAULT 'pending',                  -- pending/approved/paid/cancelled
        calculation         JSONB DEFAULT '{}',                             -- 计算明细
        approved_by         INTEGER REFERENCES users(id),                   -- 审批人ID
        paid_at             TIMESTAMP,                                      -- 支付时间
        period_start        DATE,                                           -- 结算起始日
        period_end          DATE,                                           -- 结算截止日
        created_at          TIMESTAMP NOT NULL DEFAULT NOW()                -- 创建时间
    );
    COMMENT ON TABLE revenue_shares IS '收益分配记录';
    COMMENT ON COLUMN revenue_shares.beneficiary_id IS '受益人用户ID';
    COMMENT ON COLUMN revenue_shares.source_type IS '收益来源: referral/collaboration/service/project/dividend';
    COMMENT ON COLUMN revenue_shares.source_id IS '关联实体ID';
    COMMENT ON COLUMN revenue_shares.amount IS '金额';
    COMMENT ON COLUMN revenue_shares.currency IS '货币类型';
    COMMENT ON COLUMN revenue_shares.status IS '状态: pending/approved/paid/cancelled';
    COMMENT ON COLUMN revenue_shares.calculation IS '计算明细JSON';
    COMMENT ON COLUMN revenue_shares.approved_by IS '审批人用户ID';
    COMMENT ON COLUMN revenue_shares.paid_at IS '支付时间';
    COMMENT ON COLUMN revenue_shares.period_start IS '结算起始日';
    COMMENT ON COLUMN revenue_shares.period_end IS '结算截止日';
    CREATE INDEX IF NOT EXISTS idx_revenue_beneficiary_status ON revenue_shares(beneficiary_id, status);
    """)

    # ── 3. sandbox_test_results (沙箱测试) ──────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS sandbox_test_results (
        id                  SERIAL PRIMARY KEY,
        agent_id            VARCHAR(32) NOT NULL,                           -- Agent标识
        test_suite          VARCHAR(50) NOT NULL,                           -- 测试套件
        test_case_id        VARCHAR(50) NOT NULL,                           -- 测试用例ID
        scenario            JSONB NOT NULL,                                 -- 测试场景
        expected_output     JSONB,                                          -- 期望输出
        actual_output       JSONB,                                          -- 实际输出
        passed              BOOLEAN NOT NULL,                               -- 是否通过
        score               FLOAT,                                          -- 得分(0.0-1.0)
        error_detail        TEXT,                                           -- 错误详情
        execution_ms        INTEGER,                                        -- 执行耗时(毫秒)
        run_id              VARCHAR(50) NOT NULL,                           -- 批次ID
        created_at          TIMESTAMP NOT NULL DEFAULT NOW()                -- 创建时间
    );
    COMMENT ON TABLE sandbox_test_results IS '沙箱自动化测试结果';
    COMMENT ON COLUMN sandbox_test_results.agent_id IS 'Agent标识符';
    COMMENT ON COLUMN sandbox_test_results.test_suite IS '测试套件: strategy_coverage/behavior_rational/personality_fit/safety_boundary';
    COMMENT ON COLUMN sandbox_test_results.test_case_id IS '测试用例ID';
    COMMENT ON COLUMN sandbox_test_results.scenario IS '测试场景JSON';
    COMMENT ON COLUMN sandbox_test_results.expected_output IS '期望输出JSON';
    COMMENT ON COLUMN sandbox_test_results.actual_output IS '实际输出JSON';
    COMMENT ON COLUMN sandbox_test_results.passed IS '是否通过';
    COMMENT ON COLUMN sandbox_test_results.score IS '得分(0.0-1.0)';
    COMMENT ON COLUMN sandbox_test_results.error_detail IS '错误详情';
    COMMENT ON COLUMN sandbox_test_results.execution_ms IS '执行耗时(毫秒)';
    COMMENT ON COLUMN sandbox_test_results.run_id IS '批次ID';
    CREATE INDEX IF NOT EXISTS idx_sandbox_agent_suite_run ON sandbox_test_results(agent_id, test_suite, run_id);
    """)

    # ── 4. coach_supervision_records (教练督导记录) ──────
    op.execute("""
    CREATE TABLE IF NOT EXISTS coach_supervision_records (
        id                  SERIAL PRIMARY KEY,
        supervisor_id       INTEGER NOT NULL REFERENCES users(id),          -- 督导人ID
        coach_id            INTEGER NOT NULL REFERENCES users(id),          -- 被督导教练ID
        session_type        VARCHAR(30) NOT NULL,                           -- individual/group/case_review/live_observation/emergency
        scheduled_at        TIMESTAMP,                                      -- 计划时间
        completed_at        TIMESTAMP,                                      -- 完成时间
        status              VARCHAR(20) DEFAULT 'scheduled',                -- scheduled/completed/cancelled/no_show
        template_id         VARCHAR(50),                                    -- 督导模板ID
        session_notes       TEXT,                                           -- 督导记录
        action_items        JSONB DEFAULT '[]',                             -- 行动项列表
        quality_rating      FLOAT,                                          -- 质量评分(1-5)
        compliance_met      BOOLEAN DEFAULT true,                           -- 是否达标
        created_at          TIMESTAMP NOT NULL DEFAULT NOW()                -- 创建时间
    );
    COMMENT ON TABLE coach_supervision_records IS '教练督导记录';
    COMMENT ON COLUMN coach_supervision_records.supervisor_id IS '督导人用户ID';
    COMMENT ON COLUMN coach_supervision_records.coach_id IS '被督导教练用户ID';
    COMMENT ON COLUMN coach_supervision_records.session_type IS '督导类型: individual/group/case_review/live_observation/emergency';
    COMMENT ON COLUMN coach_supervision_records.scheduled_at IS '计划时间';
    COMMENT ON COLUMN coach_supervision_records.completed_at IS '完成时间';
    COMMENT ON COLUMN coach_supervision_records.status IS '状态: scheduled/completed/cancelled/no_show';
    COMMENT ON COLUMN coach_supervision_records.template_id IS '督导模板ID';
    COMMENT ON COLUMN coach_supervision_records.session_notes IS '督导记录';
    COMMENT ON COLUMN coach_supervision_records.action_items IS '行动项列表JSON';
    COMMENT ON COLUMN coach_supervision_records.quality_rating IS '质量评分(1-5)';
    COMMENT ON COLUMN coach_supervision_records.compliance_met IS '是否达标';
    CREATE INDEX IF NOT EXISTS idx_supervision_coach ON coach_supervision_records(coach_id, status);
    CREATE INDEX IF NOT EXISTS idx_supervision_supervisor ON coach_supervision_records(supervisor_id, status);
    """)

    # ── 5. coach_kpi_metrics (教练KPI红绿灯) ───────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS coach_kpi_metrics (
        id                          SERIAL PRIMARY KEY,
        coach_id                    INTEGER NOT NULL REFERENCES users(id),  -- 教练用户ID
        period_type                 VARCHAR(10) NOT NULL,                   -- weekly/monthly/quarterly
        period_start                DATE NOT NULL,                          -- 周期起始日
        period_end                  DATE NOT NULL,                          -- 周期截止日
        active_client_count         INTEGER DEFAULT 0,                      -- 活跃客户数
        session_completion_rate     FLOAT DEFAULT 0.0,                      -- 会话完成率
        client_retention_rate       FLOAT DEFAULT 0.0,                      -- 客户留存率
        stage_advancement_rate      FLOAT DEFAULT 0.0,                      -- 阶段推进率
        assessment_coverage         FLOAT DEFAULT 0.0,                      -- 评估覆盖率
        intervention_adherence      FLOAT DEFAULT 0.0,                      -- 干预依从率
        client_satisfaction         FLOAT DEFAULT 0.0,                      -- 客户满意度
        safety_incident_count       INTEGER DEFAULT 0,                      -- 安全事件数
        supervision_compliance      FLOAT DEFAULT 0.0,                      -- 督导合规率
        knowledge_contribution      INTEGER DEFAULT 0,                      -- 知识贡献数
        overall_status              VARCHAR(10) DEFAULT 'green',            -- green/yellow/red
        alert_details               JSONB DEFAULT '{}',                     -- 告警详情
        auto_escalated              BOOLEAN DEFAULT false,                  -- 是否自动升级
        escalated_to                INTEGER REFERENCES users(id),           -- 升级对象
        created_at                  TIMESTAMP NOT NULL DEFAULT NOW(),       -- 创建时间
        updated_at                  TIMESTAMP NOT NULL DEFAULT NOW(),       -- 更新时间
        UNIQUE(coach_id, period_type, period_start)
    );
    COMMENT ON TABLE coach_kpi_metrics IS '教练KPI红绿灯仪表盘';
    COMMENT ON COLUMN coach_kpi_metrics.coach_id IS '教练用户ID';
    COMMENT ON COLUMN coach_kpi_metrics.period_type IS '周期类型: weekly/monthly/quarterly';
    COMMENT ON COLUMN coach_kpi_metrics.period_start IS '周期起始日';
    COMMENT ON COLUMN coach_kpi_metrics.period_end IS '周期截止日';
    COMMENT ON COLUMN coach_kpi_metrics.active_client_count IS '活跃客户数';
    COMMENT ON COLUMN coach_kpi_metrics.session_completion_rate IS '会话完成率';
    COMMENT ON COLUMN coach_kpi_metrics.client_retention_rate IS '客户留存率';
    COMMENT ON COLUMN coach_kpi_metrics.stage_advancement_rate IS '阶段推进率';
    COMMENT ON COLUMN coach_kpi_metrics.assessment_coverage IS '评估覆盖率';
    COMMENT ON COLUMN coach_kpi_metrics.intervention_adherence IS '干预依从率';
    COMMENT ON COLUMN coach_kpi_metrics.client_satisfaction IS '客户满意度';
    COMMENT ON COLUMN coach_kpi_metrics.safety_incident_count IS '安全事件数';
    COMMENT ON COLUMN coach_kpi_metrics.supervision_compliance IS '督导合规率';
    COMMENT ON COLUMN coach_kpi_metrics.knowledge_contribution IS '知识贡献数';
    COMMENT ON COLUMN coach_kpi_metrics.overall_status IS '综合状态: green/yellow/red';
    COMMENT ON COLUMN coach_kpi_metrics.alert_details IS '告警详情JSON';
    COMMENT ON COLUMN coach_kpi_metrics.auto_escalated IS '是否自动升级';
    COMMENT ON COLUMN coach_kpi_metrics.escalated_to IS '升级对象用户ID';
    CREATE INDEX IF NOT EXISTS idx_kpi_coach_period ON coach_kpi_metrics(coach_id, period_type, period_start);
    CREATE INDEX IF NOT EXISTS idx_kpi_overall_status ON coach_kpi_metrics(overall_status);
    """)

    # ── 6. peer_tracking (同道者追踪) ──────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS peer_tracking (
        id                      SERIAL PRIMARY KEY,
        coach_id                INTEGER NOT NULL REFERENCES users(id),      -- 教练用户ID
        peer_id                 INTEGER NOT NULL REFERENCES users(id),      -- 同道者用户ID
        coach_level             INTEGER NOT NULL,                           -- 教练当前level(3-6)
        relationship_type       VARCHAR(20) DEFAULT 'companion',            -- companion/mentee/protege
        status                  VARCHAR(20) DEFAULT 'active',               -- active/completed/dropped
        started_at              TIMESTAMP NOT NULL DEFAULT NOW(),           -- 开始时间
        completed_at            TIMESTAMP,                                  -- 完成时间
        quality_score           FLOAT,                                      -- 质量评分
        interaction_count       INTEGER DEFAULT 0,                          -- 互动次数
        last_interaction_at     TIMESTAMP,                                  -- 最后互动时间
        verified                BOOLEAN DEFAULT false,                      -- 是否已验证
        verified_by             INTEGER REFERENCES users(id),               -- 验证人ID
        notes                   TEXT,                                       -- 备注
        created_at              TIMESTAMP NOT NULL DEFAULT NOW(),           -- 创建时间
        updated_at              TIMESTAMP NOT NULL DEFAULT NOW(),           -- 更新时间
        UNIQUE(coach_id, peer_id, coach_level)
    );
    COMMENT ON TABLE peer_tracking IS '四同道者追踪记录';
    COMMENT ON COLUMN peer_tracking.coach_id IS '教练用户ID';
    COMMENT ON COLUMN peer_tracking.peer_id IS '同道者用户ID';
    COMMENT ON COLUMN peer_tracking.coach_level IS '教练当前等级(3-6)';
    COMMENT ON COLUMN peer_tracking.relationship_type IS '关系类型: companion/mentee/protege';
    COMMENT ON COLUMN peer_tracking.status IS '状态: active/completed/dropped';
    COMMENT ON COLUMN peer_tracking.started_at IS '开始时间';
    COMMENT ON COLUMN peer_tracking.completed_at IS '完成时间';
    COMMENT ON COLUMN peer_tracking.quality_score IS '质量评分';
    COMMENT ON COLUMN peer_tracking.interaction_count IS '互动次数';
    COMMENT ON COLUMN peer_tracking.last_interaction_at IS '最后互动时间';
    COMMENT ON COLUMN peer_tracking.verified IS '是否已验证';
    COMMENT ON COLUMN peer_tracking.verified_by IS '验证人用户ID';
    COMMENT ON COLUMN peer_tracking.notes IS '备注';
    CREATE INDEX IF NOT EXISTS idx_peer_coach_level ON peer_tracking(coach_id, coach_level, status);
    CREATE INDEX IF NOT EXISTS idx_peer_peer_id ON peer_tracking(peer_id, status);
    """)


def downgrade():
    # 按反序删除所有6张表和索引
    op.execute("DROP INDEX IF EXISTS idx_peer_peer_id;")
    op.execute("DROP INDEX IF EXISTS idx_peer_coach_level;")
    op.execute("DROP TABLE IF EXISTS peer_tracking;")

    op.execute("DROP INDEX IF EXISTS idx_kpi_overall_status;")
    op.execute("DROP INDEX IF EXISTS idx_kpi_coach_period;")
    op.execute("DROP TABLE IF EXISTS coach_kpi_metrics;")

    op.execute("DROP INDEX IF EXISTS idx_supervision_supervisor;")
    op.execute("DROP INDEX IF EXISTS idx_supervision_coach;")
    op.execute("DROP TABLE IF EXISTS coach_supervision_records;")

    op.execute("DROP INDEX IF EXISTS idx_sandbox_agent_suite_run;")
    op.execute("DROP TABLE IF EXISTS sandbox_test_results;")

    op.execute("DROP INDEX IF EXISTS idx_revenue_beneficiary_status;")
    op.execute("DROP TABLE IF EXISTS revenue_shares;")

    op.execute("DROP INDEX IF EXISTS idx_coach_exam_coach_level;")
    op.execute("DROP TABLE IF EXISTS coach_exam_records;")
