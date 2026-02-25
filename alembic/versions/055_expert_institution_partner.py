"""Migration 055 — Expert独立AGENT + 机构合作 + 合伙人体系

契约对应: 行健平台生态架构升级实施方案 V1.0
前置: HEAD=054 (XZB Expert Agent)
新建表: 6张
ALTER表: 2张
新增枚举: INSTITUTION_ADMIN

幂等性: 全部使用 IF NOT EXISTS，可重复执行
asyncpg约定: 使用 CAST(:v AS type) 而非 ::type
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector

revision = '055'
down_revision = '054'
branch_labels = None
depends_on = None


def upgrade():
    # ──────────────────────────────────────────────────────
    # 1. UserRole 枚举扩展 — 新增 INSTITUTION_ADMIN
    # ──────────────────────────────────────────────────────
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumtypid = 'userrole'::regtype
                  AND enumlabel = 'INSTITUTION_ADMIN'
            ) THEN
                ALTER TYPE userrole ADD VALUE 'INSTITUTION_ADMIN';
            END IF;
        END
        $$;
    """)

    # ──────────────────────────────────────────────────────
    # 2. tenants 表 — 机构租户（新建，区别于 expert_tenants 个人租户）
    # ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_name     VARCHAR(200) NOT NULL,
            tenant_type     VARCHAR(30) NOT NULL DEFAULT 'personal',
            status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','active','suspended','terminated')),
            region          VARCHAR(100),
            institution_config JSONB DEFAULT '{}',
            partner_config  JSONB DEFAULT '{}',
            parent_tenant_id UUID REFERENCES tenants(id),
            max_users       INTEGER DEFAULT 500,
            domain_whitelist TEXT[] DEFAULT '{}',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_tenants_type
            ON tenants(tenant_type);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_tenants_parent
            ON tenants(parent_tenant_id)
            WHERE parent_tenant_id IS NOT NULL;
    """)

    # ──────────────────────────────────────────────────────
    # 2b. users 表扩展 — 添加 tenant_id (机构关联)
    # ──────────────────────────────────────────────────────
    op.execute("""
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_tenant
            ON users(tenant_id)
            WHERE tenant_id IS NOT NULL;
    """)

    # ──────────────────────────────────────────────────────
    # 3. expert_tenants 表扩展 — 服务模式 + 公开主页
    # ──────────────────────────────────────────────────────
    op.execute("""
        ALTER TABLE expert_tenants
            ADD COLUMN IF NOT EXISTS service_mode_public          BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS service_mode_clinical        BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS service_mode_coach_network   BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS expert_slug                  VARCHAR(100),
            ADD COLUMN IF NOT EXISTS public_bio                   TEXT,
            ADD COLUMN IF NOT EXISTS specialty_domains            TEXT[] DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS target_populations           JSONB DEFAULT '[]',
            ADD COLUMN IF NOT EXISTS excluded_populations         JSONB DEFAULT '[]',
            ADD COLUMN IF NOT EXISTS consultation_fee_config      JSONB DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS is_publicly_listed           BOOLEAN DEFAULT FALSE;
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_expert_tenants_slug
            ON expert_tenants(expert_slug)
            WHERE expert_slug IS NOT NULL;
    """)

    # ──────────────────────────────────────────────────────
    # 4. expert_public_profiles — Expert公开主页信息
    # ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS expert_public_profiles (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            expert_user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            display_name        VARCHAR(100) NOT NULL,
            title               VARCHAR(200),
            institution_name    VARCHAR(200),
            certifications      JSONB DEFAULT '[]',
            publication_count   INTEGER DEFAULT 0,
            cover_image_url     TEXT,
            intro_video_url     TEXT,
            available_hours     JSONB DEFAULT '{}',
            total_patients      INTEGER DEFAULT 0,
            rating              NUMERIC(3,2) DEFAULT 5.00,
            review_count        INTEGER DEFAULT 0,
            is_verified         BOOLEAN DEFAULT FALSE,
            seo_keywords        TEXT[] DEFAULT '{}',
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(expert_user_id)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_expert_profiles_verified
            ON expert_public_profiles(is_verified)
            WHERE is_verified = TRUE;
    """)

    # ──────────────────────────────────────────────────────
    # 5. expert_patient_bindings — Expert-患者绑定（MODE_B）
    # ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS expert_patient_bindings (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            expert_user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            patient_user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            binding_type        VARCHAR(20) NOT NULL DEFAULT 'clinical',
            status              VARCHAR(20) NOT NULL DEFAULT 'active'
                                CHECK (status IN ('pending','active','suspended','terminated')),
            initiated_by        VARCHAR(20) NOT NULL DEFAULT 'expert'
                                CHECK (initiated_by IN ('expert','patient','institution')),
            institution_id      UUID REFERENCES tenants(id),
            notes               TEXT,
            activated_at        TIMESTAMPTZ,
            terminated_at       TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(expert_user_id, patient_user_id)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_epb_expert
            ON expert_patient_bindings(expert_user_id, status);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_epb_patient
            ON expert_patient_bindings(patient_user_id, status);
    """)

    # ──────────────────────────────────────────────────────
    # 6. xzb_knowledge — 行诊智伴专家私有知识库
    # ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS xzb_knowledge (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            expert_id               INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            knowledge_type          VARCHAR(30) NOT NULL DEFAULT 'note'
                                    CHECK (knowledge_type IN
                                        ('note','rule','case','annotation','template','forbidden')),
            content                 TEXT NOT NULL,
            evidence_tier           VARCHAR(5) NOT NULL DEFAULT 'T3'
                                    CHECK (evidence_tier IN ('T1','T2','T3','T4')),
            vector_embedding        vector(768),
            source                  TEXT,
            tags                    TEXT[] DEFAULT '{}',
            applicable_conditions   JSONB DEFAULT '{}',
            confidence_override     FLOAT CHECK (confidence_override BETWEEN 0 AND 1),
            usage_count             INTEGER DEFAULT 0,
            expert_confirmed        BOOLEAN DEFAULT FALSE,
            expires_at              TIMESTAMPTZ,
            is_active               BOOLEAN DEFAULT TRUE,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_xzb_knowledge_expert_active
            ON xzb_knowledge(expert_id, is_active)
            WHERE is_active = TRUE;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_xzb_knowledge_vector
            ON xzb_knowledge
            USING ivfflat (vector_embedding vector_cosine_ops)
            WITH (lists = 50);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_xzb_knowledge_tags
            ON xzb_knowledge USING GIN (tags);
    """)

    # ──────────────────────────────────────────────────────
    # 7. xzb_rules — 诊疗规则（IF-THEN结构）
    # ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS xzb_rules (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            expert_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rule_name       VARCHAR(200),
            condition_json  JSONB NOT NULL,
            action_type     VARCHAR(30) NOT NULL
                            CHECK (action_type IN
                                ('respond','refer','prescribe','warn','defer','escalate')),
            action_content  TEXT NOT NULL,
            priority        INTEGER DEFAULT 50 CHECK (priority BETWEEN 1 AND 100),
            overrides_llm   BOOLEAN DEFAULT FALSE,
            domain_tags     TEXT[] DEFAULT '{}',
            is_active       BOOLEAN DEFAULT TRUE,
            usage_count     INTEGER DEFAULT 0,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_xzb_rules_expert_priority
            ON xzb_rules(expert_id, priority DESC)
            WHERE is_active = TRUE;
    """)

    # ──────────────────────────────────────────────────────
    # 8. partner_configs — 合伙人配置
    # ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS partner_configs (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            partner_user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tenant_id               UUID REFERENCES tenants(id),
            region                  VARCHAR(100),
            institution_quota       INTEGER DEFAULT 5,
            revenue_share_rate      NUMERIC(5,4) DEFAULT 0.15
                                    CHECK (revenue_share_rate BETWEEN 0 AND 1),
            commission_model        VARCHAR(30) DEFAULT 'subscription'
                                    CHECK (commission_model IN
                                        ('subscription','per_user','milestone','hybrid')),
            active_institutions     INTEGER DEFAULT 0,
            total_revenue           NUMERIC(12,2) DEFAULT 0,
            contract_start          DATE,
            contract_end            DATE,
            referral_code           VARCHAR(50) UNIQUE,
            status                  VARCHAR(20) DEFAULT 'active'
                                    CHECK (status IN ('pending','active','suspended','terminated')),
            approved_by             INTEGER REFERENCES users(id),
            approved_at             TIMESTAMPTZ,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(partner_user_id)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_partner_configs_status
            ON partner_configs(status)
            WHERE status = 'active';
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_partner_referral_code
            ON partner_configs(referral_code)
            WHERE referral_code IS NOT NULL;
    """)

    # ──────────────────────────────────────────────────────
    # 9. partner_revenue_logs — 合伙人收益明细
    # ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS partner_revenue_logs (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            partner_user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            institution_id      UUID REFERENCES tenants(id),
            event_type          VARCHAR(50) NOT NULL
                                CHECK (event_type IN (
                                    'institution_activation',
                                    'user_subscription',
                                    'milestone_bonus',
                                    'renewal',
                                    'referral_bonus'
                                )),
            base_amount         NUMERIC(10,2) NOT NULL CHECK (base_amount >= 0),
            share_rate          NUMERIC(5,4) NOT NULL,
            partner_amount      NUMERIC(10,2) NOT NULL CHECK (partner_amount >= 0),
            period_start        DATE,
            period_end          DATE,
            status              VARCHAR(20) DEFAULT 'pending'
                                CHECK (status IN ('pending','confirmed','paid','cancelled')),
            memo                TEXT,
            settled_at          TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_revenue_logs_partner
            ON partner_revenue_logs(partner_user_id, created_at DESC);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_revenue_logs_status
            ON partner_revenue_logs(status)
            WHERE status IN ('pending','confirmed');
    """)


def downgrade():
    # 按依赖倒序删除
    op.execute("DROP TABLE IF EXISTS partner_revenue_logs CASCADE;")
    op.execute("DROP TABLE IF EXISTS partner_configs CASCADE;")
    op.execute("DROP TABLE IF EXISTS xzb_rules CASCADE;")
    op.execute("DROP TABLE IF EXISTS xzb_knowledge CASCADE;")
    op.execute("DROP TABLE IF EXISTS expert_patient_bindings CASCADE;")
    op.execute("DROP TABLE IF EXISTS expert_public_profiles CASCADE;")
    op.execute("""
        ALTER TABLE expert_tenants
            DROP COLUMN IF EXISTS service_mode_public,
            DROP COLUMN IF EXISTS service_mode_clinical,
            DROP COLUMN IF EXISTS service_mode_coach_network,
            DROP COLUMN IF EXISTS expert_slug,
            DROP COLUMN IF EXISTS public_bio,
            DROP COLUMN IF EXISTS specialty_domains,
            DROP COLUMN IF EXISTS target_populations,
            DROP COLUMN IF EXISTS excluded_populations,
            DROP COLUMN IF EXISTS consultation_fee_config,
            DROP COLUMN IF EXISTS is_publicly_listed;
    """)
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS tenant_id;")
    op.execute("DROP TABLE IF EXISTS tenants CASCADE;")
    # 注意: PostgreSQL 不支持 DROP VALUE FROM ENUM，INSTITUTION_ADMIN 保留
