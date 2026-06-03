-- =============================================
-- OntologyReady MVP — 4 张核心表 DDL
-- PostgreSQL 16 + pgvector
-- =============================================

-- 扩展
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================================
-- 1. 本体类型定义（Object / Link / Action）
-- =============================================
CREATE TABLE ontology_types (
    api_name      VARCHAR(100) PRIMARY KEY,
    type          VARCHAR(20) NOT NULL CHECK (type IN ('OBJECT', 'LINK', 'ACTION')),
    display_name  VARCHAR(200) NOT NULL,
    description   TEXT NOT NULL,
    config        JSONB NOT NULL DEFAULT '{}',
    maturity      VARCHAR(20) DEFAULT 'DRAFT' CHECK (maturity IN ('DRAFT', 'ACTIVE', 'DEPRECATED')),
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_types_type ON ontology_types(type);
CREATE INDEX idx_types_config ON ontology_types USING GIN (config);
CREATE INDEX idx_types_maturity ON ontology_types(maturity);

-- =============================================
-- 2. 对象实例（混合存储模式）
-- =============================================
CREATE TABLE ontology_objects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_type     VARCHAR(100) NOT NULL REFERENCES ontology_types(api_name),
    external_id     VARCHAR(500),
    dataset_id      VARCHAR(100) NOT NULL DEFAULT 'default',
    display_name    TEXT GENERATED ALWAYS AS (properties ->> 'name') STORED,
    properties      JSONB NOT NULL DEFAULT '{}',
    embedding       VECTOR(384),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_objects_type ON ontology_objects(object_type);
CREATE INDEX idx_objects_eid ON ontology_objects(object_type, external_id);
CREATE INDEX idx_objects_props ON ontology_objects USING GIN (properties);
CREATE INDEX idx_objects_display ON ontology_objects(display_name);
CREATE INDEX idx_objects_dataset ON ontology_objects(dataset_id, object_type);

-- =============================================
-- 3. 关系链接（邻接表模型）
-- =============================================
CREATE TABLE ontology_links (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_type       VARCHAR(100) NOT NULL REFERENCES ontology_types(api_name),
    source_id       UUID NOT NULL REFERENCES ontology_objects(id) ON DELETE CASCADE,
    target_id       UUID NOT NULL REFERENCES ontology_objects(id) ON DELETE CASCADE,
    dataset_id      VARCHAR(100) NOT NULL DEFAULT 'default',
    properties      JSONB DEFAULT '{}',
    confidence      REAL DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_links_source ON ontology_links(source_id);
CREATE INDEX idx_links_target ON ontology_links(target_id);
CREATE INDEX idx_links_type ON ontology_links(link_type);
CREATE INDEX idx_links_props ON ontology_links USING GIN (properties);
CREATE INDEX idx_links_source_type ON ontology_links(source_id, link_type);
CREATE INDEX idx_links_target_type ON ontology_links(target_id, link_type);
CREATE INDEX idx_links_dataset ON ontology_links(dataset_id, link_type);

-- =============================================
-- 4. 动作审计日志（不可篡改）
-- =============================================
CREATE TABLE ontology_actions_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_type     VARCHAR(100) NOT NULL,
    parameters      JSONB NOT NULL,
    status          VARCHAR(20) NOT NULL CHECK (status IN ('SUCCESS', 'FAILED', 'PENDING')),
    error_message   TEXT,
    executed_by     VARCHAR(200) NOT NULL,
    before_snapshot JSONB,
    after_snapshot  JSONB,
    executed_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_actions_log_type ON ontology_actions_log(action_type);
CREATE INDEX idx_actions_log_time ON ontology_actions_log(executed_at);
CREATE INDEX idx_actions_log_executor ON ontology_actions_log(executed_by);
CREATE INDEX idx_actions_log_params ON ontology_actions_log USING GIN (parameters);
CREATE INDEX idx_actions_log_before ON ontology_actions_log USING GIN (before_snapshot);
CREATE INDEX idx_actions_log_after ON ontology_actions_log USING GIN (after_snapshot);
