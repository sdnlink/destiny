-- 风水房屋档案（PostgreSQL DDL）
-- 租户隔离：行级 tenant_id；所有查询必须携带 tenant_id 过滤。
-- 合规：只存坐向测量事实与屋宅描述，owner_consent 为屋主知情同意标记。

CREATE TABLE IF NOT EXISTS fengshui_building_profiles (
    tenant_id      VARCHAR(64)  NOT NULL,
    building_id    VARCHAR(64)  NOT NULL,
    name           VARCHAR(128) NOT NULL,
    profile        JSONB        NOT NULL,
    owner_consent  BOOLEAN      NOT NULL DEFAULT FALSE,
    data_classification VARCHAR(32) NOT NULL DEFAULT 'residential',
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, building_id)
);

CREATE INDEX IF NOT EXISTS idx_fengshui_profiles_tenant
    ON fengshui_building_profiles (tenant_id, updated_at DESC);
