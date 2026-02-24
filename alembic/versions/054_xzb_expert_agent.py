"""054 行智诊疗专家个人AGENT (10新表 + 3 ALTER)

合并原 XZB Migration 053-056 → 054 (避免与 VisionGuard 053 冲突)

新建表:
  - xzb_expert_profiles     专家画像
  - xzb_configs             智伴配置
  - xzb_knowledge           专家知识条目 (含pgvector 768维)
  - xzb_knowledge_rules     诊疗规则 (IF-THEN)
  - xzb_conversations       对话记录
  - xzb_rx_fragments        处方片段 (注入RxComposer)
  - xzb_expert_interventions 专家介入记录
  - xzb_med_circle          医道汇帖子
  - xzb_med_circle_comments 医道汇评论
  - xzb_knowledge_sharing   知识共享权限

ALTER TABLE:
  - users + xzb_expert_id
  - agent_templates + xzb_config_id
  - knowledge_documents + expert_id

Revision ID: 054
Revises: 053
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '054'
down_revision = '053'
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. xzb_expert_profiles ──────────────────────────────
    # user_id 为 INTEGER (平台 users.id 是 INTEGER, 非 UUID)
    op.execute("""
    CREATE TABLE IF NOT EXISTS xzb_expert_profiles (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        display_name    VARCHAR(100) NOT NULL,
        specialty       VARCHAR(200),
        license_no      VARCHAR(100),
        license_verified BOOLEAN DEFAULT FALSE,
        tcm_weight      FLOAT DEFAULT 0.5,
        style_profile   JSONB DEFAULT '{}',
        domain_tags     TEXT[] DEFAULT '{}',
        is_active       BOOLEAN DEFAULT TRUE,
        last_active_at  TIMESTAMP,
        created_at      TIMESTAMP DEFAULT NOW(),
        updated_at      TIMESTAMP DEFAULT NOW()
    )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_xzb_expert_user ON xzb_expert_profiles(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_xzb_expert_domain ON xzb_expert_profiles USING GIN(domain_tags)")

    # ── 2. xzb_configs ──────────────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS xzb_configs (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        expert_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id) ON DELETE CASCADE,
        companion_name  VARCHAR(100) NOT NULL,
        greeting        TEXT,
        comm_style      JSONB DEFAULT '{}',
        boundary_stmt   TEXT,
        referral_rules  JSONB DEFAULT '[]',
        auto_rx_enabled BOOLEAN DEFAULT TRUE,
        dormant_mode    BOOLEAN DEFAULT FALSE,
        created_at      TIMESTAMP DEFAULT NOW(),
        updated_at      TIMESTAMP DEFAULT NOW()
    )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_xzb_config_expert ON xzb_configs(expert_id)")

    # ── 3. xzb_knowledge (含pgvector 768维) ─────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS xzb_knowledge (
        id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        expert_id           UUID NOT NULL REFERENCES xzb_expert_profiles(id) ON DELETE CASCADE,
        type                VARCHAR(20) NOT NULL CHECK (type IN (
                                'note','rule','case','annotation','template','forbidden'
                            )),
        content             TEXT NOT NULL,
        evidence_tier       VARCHAR(2) CHECK (evidence_tier IN ('T1','T2','T3','T4')),
        vector_embedding    VECTOR(768),
        source              TEXT,
        tags                TEXT[] DEFAULT '{}',
        applicable_conditions JSONB DEFAULT '{}',
        confidence_override FLOAT,
        usage_count         INT DEFAULT 0,
        expert_confirmed    BOOLEAN DEFAULT FALSE,
        expires_at          TIMESTAMP,
        is_active           BOOLEAN DEFAULT TRUE,
        needs_review        BOOLEAN DEFAULT FALSE,
        source_conversation_id UUID,
        created_at          TIMESTAMP DEFAULT NOW(),
        updated_at          TIMESTAMP DEFAULT NOW()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_xzb_knowledge_expert ON xzb_knowledge(expert_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_xzb_knowledge_type ON xzb_knowledge(type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_xzb_knowledge_tags ON xzb_knowledge USING GIN(tags)")
    # ivfflat 向量索引 (需要pgvector扩展已启用; 空表时ivfflat可能报错, 使用hnsw替代)
    op.execute("""
    DO $$ BEGIN
        CREATE INDEX IF NOT EXISTS idx_xzb_knowledge_vector ON xzb_knowledge
            USING hnsw (vector_embedding vector_cosine_ops);
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Vector index creation skipped: %', SQLERRM;
    END $$
    """)

    # ── 4. xzb_knowledge_rules ──────────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS xzb_knowledge_rules (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        expert_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id) ON DELETE CASCADE,
        rule_name       VARCHAR(200),
        condition_json  JSONB NOT NULL,
        action_type     VARCHAR(20) CHECK (action_type IN (
                            'respond','refer','prescribe','warn','defer'
                        )),
        action_content  TEXT NOT NULL,
        priority        INT DEFAULT 50,
        overrides_llm   BOOLEAN DEFAULT FALSE,
        is_active       BOOLEAN DEFAULT TRUE,
        created_at      TIMESTAMP DEFAULT NOW(),
        updated_at      TIMESTAMP DEFAULT NOW()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_xzb_rules_expert ON xzb_knowledge_rules(expert_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_xzb_rules_priority ON xzb_knowledge_rules(priority DESC)")

    # ── 5. xzb_conversations ────────────────────────────────
    # seeker_id/session_ref 为 INTEGER (平台 users.id / chat_sessions.id 是 INTEGER)
    op.execute("""
    CREATE TABLE IF NOT EXISTS xzb_conversations (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        expert_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id),
        seeker_id       INTEGER NOT NULL REFERENCES users(id),
        session_ref     INTEGER REFERENCES chat_sessions(id),
        summary         TEXT,
        messages_json   JSONB DEFAULT '[]',
        rx_triggered    BOOLEAN DEFAULT FALSE,
        expert_intervened BOOLEAN DEFAULT FALSE,
        knowledge_mined BOOLEAN DEFAULT FALSE,
        ttm_stage_at_start VARCHAR(2),
        created_at      TIMESTAMP DEFAULT NOW(),
        ended_at        TIMESTAMP
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_xzb_conv_expert ON xzb_conversations(expert_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_xzb_conv_seeker ON xzb_conversations(seeker_id)")

    # ── 6. xzb_rx_fragments ─────────────────────────────────
    # seeker_id 为 INTEGER (平台 users.id 是 INTEGER)
    op.execute("""
    CREATE TABLE IF NOT EXISTS xzb_rx_fragments (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id UUID REFERENCES xzb_conversations(id),
        expert_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id),
        seeker_id       INTEGER NOT NULL REFERENCES users(id),
        source          VARCHAR(50) DEFAULT 'xzb_expert',
        priority        INT DEFAULT 0,
        evidence_tier   VARCHAR(2),
        domain          VARCHAR(100),
        strategies      JSONB NOT NULL DEFAULT '[]',
        knowledge_refs  UUID[] DEFAULT '{}',
        style_profile_id UUID,
        contraindications TEXT[] DEFAULT '{}',
        requires_coach_review BOOLEAN DEFAULT TRUE,
        rx_id           UUID,
        status          VARCHAR(20) DEFAULT 'draft'
                        CHECK (status IN ('draft','submitted','approved','rejected')),
        created_at      TIMESTAMP DEFAULT NOW()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_xzb_rxfrag_expert ON xzb_rx_fragments(expert_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_xzb_rxfrag_status ON xzb_rx_fragments(status)")

    # ── 7. xzb_expert_interventions ─────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS xzb_expert_interventions (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id UUID NOT NULL REFERENCES xzb_conversations(id),
        expert_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id),
        intervention_type VARCHAR(20) CHECK (intervention_type IN (
                            'takeover','async_reply','rx_trigger','knowledge_push'
                        )),
        content         TEXT,
        created_at      TIMESTAMP DEFAULT NOW()
    )
    """)

    # ── 8. xzb_med_circle (医道汇) ─────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS xzb_med_circle (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        author_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id),
        title           VARCHAR(500),
        content         TEXT NOT NULL,
        post_type       VARCHAR(20) CHECK (post_type IN (
                            'case','literature','discussion','guideline','tip'
                        )),
        tags            TEXT[] DEFAULT '{}',
        view_count      INT DEFAULT 0,
        like_count      INT DEFAULT 0,
        is_published    BOOLEAN DEFAULT FALSE,
        created_at      TIMESTAMP DEFAULT NOW(),
        updated_at      TIMESTAMP DEFAULT NOW()
    )
    """)

    # ── 9. xzb_med_circle_comments ──────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS xzb_med_circle_comments (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        post_id         UUID NOT NULL REFERENCES xzb_med_circle(id) ON DELETE CASCADE,
        author_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id),
        content         TEXT NOT NULL,
        parent_id       UUID REFERENCES xzb_med_circle_comments(id),
        created_at      TIMESTAMP DEFAULT NOW()
    )
    """)

    # ── 10. xzb_knowledge_sharing ───────────────────────────
    op.execute("""
    CREATE TABLE IF NOT EXISTS xzb_knowledge_sharing (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        knowledge_id    UUID NOT NULL REFERENCES xzb_knowledge(id),
        owner_id        UUID NOT NULL REFERENCES xzb_expert_profiles(id),
        grantee_id      UUID REFERENCES xzb_expert_profiles(id),
        permission      VARCHAR(20) DEFAULT 'read' CHECK (permission IN ('read','adapt')),
        expires_at      TIMESTAMP,
        created_at      TIMESTAMP DEFAULT NOW()
    )
    """)

    # ── ALTER TABLE: 扩展现有表 ─────────────────────────────
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS xzb_expert_id UUID REFERENCES xzb_expert_profiles(id)")
    # agent_templates 在 coach_schema (防御: 表不存在时静默跳过)
    op.execute("""
    DO $$ BEGIN
        ALTER TABLE coach_schema.agent_templates ADD COLUMN IF NOT EXISTS xzb_config_id UUID REFERENCES xzb_configs(id);
    EXCEPTION WHEN undefined_table THEN NULL;
    END $$
    """)
    op.execute("ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS expert_id UUID REFERENCES xzb_expert_profiles(id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_kd_expert ON knowledge_documents(expert_id)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_kd_expert")
    op.execute("ALTER TABLE knowledge_documents DROP COLUMN IF EXISTS expert_id")
    op.execute("""
    DO $$ BEGIN
        ALTER TABLE coach_schema.agent_templates DROP COLUMN IF EXISTS xzb_config_id;
    EXCEPTION WHEN undefined_table THEN NULL;
    END $$
    """)
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS xzb_expert_id")
    op.execute("DROP TABLE IF EXISTS xzb_knowledge_sharing CASCADE")
    op.execute("DROP TABLE IF EXISTS xzb_med_circle_comments CASCADE")
    op.execute("DROP TABLE IF EXISTS xzb_med_circle CASCADE")
    op.execute("DROP TABLE IF EXISTS xzb_expert_interventions CASCADE")
    op.execute("DROP TABLE IF EXISTS xzb_rx_fragments CASCADE")
    op.execute("DROP TABLE IF EXISTS xzb_conversations CASCADE")
    op.execute("DROP TABLE IF EXISTS xzb_knowledge_rules CASCADE")
    op.execute("DROP TABLE IF EXISTS xzb_knowledge CASCADE")
    op.execute("DROP TABLE IF EXISTS xzb_configs CASCADE")
    op.execute("DROP TABLE IF EXISTS xzb_expert_profiles CASCADE")
