-- ============================================================
-- Migration 053: 行诊智伴核心数据模型 (4张新表)
-- ============================================================

-- 专家画像表
CREATE TABLE xzb_expert_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    display_name    VARCHAR(100) NOT NULL,           -- 智伴对外展示名称
    specialty       VARCHAR(200),                    -- 专科方向
    license_no      VARCHAR(100),                    -- 执照编号
    license_verified BOOLEAN DEFAULT FALSE,
    tcm_weight      FLOAT DEFAULT 0.5,               -- 0.0纯西医 ~ 1.0纯中医
    style_profile   JSONB DEFAULT '{}',              -- 风格向量（词汇/情感/结构偏好）
    domain_tags     TEXT[] DEFAULT '{}',             -- 专科标签，与AgentRouter领域关联
    is_active       BOOLEAN DEFAULT TRUE,
    last_active_at  TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_xzb_expert_user ON xzb_expert_profiles(user_id);
CREATE INDEX idx_xzb_expert_domain ON xzb_expert_profiles USING GIN(domain_tags);

-- 智伴配置表
CREATE TABLE xzb_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id) ON DELETE CASCADE,
    companion_name  VARCHAR(100) NOT NULL,           -- 智伴名称（如"张医生的健康助手"）
    greeting        TEXT,                            -- 开场白模板
    comm_style      JSONB DEFAULT '{}',              -- 沟通风格参数
    boundary_stmt   TEXT,                            -- 边界声明（不替代就医）
    referral_rules  JSONB DEFAULT '[]',              -- 转介规则列表
    auto_rx_enabled BOOLEAN DEFAULT TRUE,            -- 是否允许自动触发处方
    dormant_mode    BOOLEAN DEFAULT FALSE,           -- 休眠模式（30日未登录自动触发）
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_xzb_config_expert ON xzb_configs(expert_id);

-- 专家知识条目表
CREATE TABLE xzb_knowledge (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id           UUID NOT NULL REFERENCES xzb_expert_profiles(id) ON DELETE CASCADE,
    type                VARCHAR(20) NOT NULL CHECK (type IN (
                            'note','rule','case','annotation','template','forbidden'
                        )),
    content             TEXT NOT NULL,               -- 加密存储（应用层加密）
    evidence_tier       VARCHAR(2) CHECK (evidence_tier IN ('T1','T2','T3','T4')),
    vector_embedding    VECTOR(768),                 -- text2vec-base-chinese
    source              TEXT,                        -- 文献DOI/自述/对话沉淀/文件导入
    tags                TEXT[] DEFAULT '{}',
    applicable_conditions JSONB DEFAULT '{}',        -- {disease, stage_s0_s5, contraindications}
    confidence_override FLOAT,                       -- 覆盖evidence_tier默认置信度
    usage_count         INT DEFAULT 0,
    expert_confirmed    BOOLEAN DEFAULT FALSE,       -- 对话沉淀需二次确认
    expires_at          TIMESTAMP,                   -- NULL=永久有效
    is_active           BOOLEAN DEFAULT TRUE,
    needs_review        BOOLEAN DEFAULT FALSE,       -- 超2年未更新标记
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_xzb_knowledge_expert ON xzb_knowledge(expert_id);
CREATE INDEX idx_xzb_knowledge_type ON xzb_knowledge(type);
CREATE INDEX idx_xzb_knowledge_tags ON xzb_knowledge USING GIN(tags);
CREATE INDEX idx_xzb_knowledge_vector ON xzb_knowledge 
    USING ivfflat (vector_embedding vector_cosine_ops) WITH (lists = 100);

-- 诊疗规则表（IF-THEN结构）
CREATE TABLE xzb_knowledge_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id) ON DELETE CASCADE,
    rule_name       VARCHAR(200),
    condition_json  JSONB NOT NULL,                  -- {trigger_keywords, device_data_thresholds, ttm_stage}
    action_type     VARCHAR(20) CHECK (action_type IN (
                        'respond','refer','prescribe','warn','defer'
                    )),
    action_content  TEXT NOT NULL,
    priority        INT DEFAULT 50,                  -- 越大越优先
    overrides_llm   BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_xzb_rules_expert ON xzb_knowledge_rules(expert_id);
CREATE INDEX idx_xzb_rules_priority ON xzb_knowledge_rules(priority DESC);

-- ============================================================
-- Migration 054: 对话与处方数据模型 (3张新表)
-- ============================================================

-- 对话记录表
CREATE TABLE xzb_conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id),
    seeker_id       UUID NOT NULL REFERENCES users(id),
    session_ref     UUID REFERENCES chat_sessions(id),  -- 关联平台chat_sessions
    summary         TEXT,                            -- 对话摘要
    rx_triggered    BOOLEAN DEFAULT FALSE,           -- 是否触发了处方
    expert_intervened BOOLEAN DEFAULT FALSE,         -- 专家是否介入
    knowledge_mined BOOLEAN DEFAULT FALSE,           -- 是否挖掘出待确认知识
    ttm_stage_at_start VARCHAR(2),                   -- 对话开始时的TTM阶段
    created_at      TIMESTAMP DEFAULT NOW(),
    ended_at        TIMESTAMP
);
CREATE INDEX idx_xzb_conv_expert ON xzb_conversations(expert_id);
CREATE INDEX idx_xzb_conv_seeker ON xzb_conversations(seeker_id);

-- 处方片段表（注入RxComposer的格式）
CREATE TABLE xzb_rx_fragments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES xzb_conversations(id),
    expert_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id),
    seeker_id       UUID NOT NULL REFERENCES users(id),
    source          VARCHAR(50) DEFAULT 'xzb_expert',
    priority        INT DEFAULT 0,                   -- 最高优先级
    evidence_tier   VARCHAR(2),
    domain          VARCHAR(100),
    strategies      JSONB NOT NULL DEFAULT '[]',     -- List[RxStrategy]
    knowledge_refs  UUID[] DEFAULT '{}',             -- 引用的知识条目ID
    style_profile_id UUID,
    contraindications TEXT[] DEFAULT '{}',
    requires_coach_review BOOLEAN DEFAULT TRUE,      -- 铁律：始终为True
    rx_id           UUID,                            -- 关联生成的处方ID
    status          VARCHAR(20) DEFAULT 'draft' 
                    CHECK (status IN ('draft','submitted','approved','rejected')),
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_xzb_rxfrag_expert ON xzb_rx_fragments(expert_id);
CREATE INDEX idx_xzb_rxfrag_status ON xzb_rx_fragments(status);

-- 专家介入记录表
CREATE TABLE xzb_expert_interventions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES xzb_conversations(id),
    expert_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id),
    intervention_type VARCHAR(20) CHECK (intervention_type IN (
                        'takeover','async_reply','rx_trigger','knowledge_push'
                    )),
    content         TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- Migration 055: 扩展现有表字段
-- ============================================================

-- 扩展 users 表
ALTER TABLE users ADD COLUMN IF NOT EXISTS xzb_expert_id UUID 
    REFERENCES xzb_expert_profiles(id);

-- 扩展 agent_templates 表
ALTER TABLE agent_templates ADD COLUMN IF NOT EXISTS xzb_config_id UUID 
    REFERENCES xzb_configs(id);

-- 扩展 knowledge_documents 表（加 expert_id，NULL=公共知识）
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS expert_id UUID 
    REFERENCES xzb_expert_profiles(id);
CREATE INDEX IF NOT EXISTS idx_kd_expert ON knowledge_documents(expert_id);

-- ============================================================
-- Migration 056: 医道汇数据模型 (Phase 3)
-- ============================================================

CREATE TABLE xzb_med_circle (
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
);

CREATE TABLE xzb_med_circle_comments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id         UUID NOT NULL REFERENCES xzb_med_circle(id) ON DELETE CASCADE,
    author_id       UUID NOT NULL REFERENCES xzb_expert_profiles(id),
    content         TEXT NOT NULL,
    parent_id       UUID REFERENCES xzb_med_circle_comments(id),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE xzb_knowledge_sharing (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_id    UUID NOT NULL REFERENCES xzb_knowledge(id),
    owner_id        UUID NOT NULL REFERENCES xzb_expert_profiles(id),
    grantee_id      UUID REFERENCES xzb_expert_profiles(id),  -- NULL=全平台公开
    permission      VARCHAR(20) DEFAULT 'read' CHECK (permission IN ('read','adapt')),
    expires_at      TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);
