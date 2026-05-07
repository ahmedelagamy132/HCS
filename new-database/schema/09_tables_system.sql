-- ============================================================
-- HCS — Equine Intelligence System
-- 09_tables_system.sql  |  Activity logs, notifications & settings
-- ============================================================

-- ── Activity / Audit Log ─────────────────────────────────────
CREATE TABLE activity_logs (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_type   actor_type  NOT NULL,
    actor_id     UUID,
    actor_label  VARCHAR(255),
    action       VARCHAR(100) NOT NULL,
    entity_type  VARCHAR(50),
    entity_id    UUID,
    entity_label VARCHAR(255),
    description  TEXT,
    ip_address   INET,
    user_agent   TEXT,
    metadata     JSONB        NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Notifications ────────────────────────────────────────────
CREATE TABLE notifications (
    id              UUID              PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipient_type  VARCHAR(20)       NOT NULL,
    recipient_id    UUID              NOT NULL,
    type            notification_type NOT NULL DEFAULT 'info',
    title           VARCHAR(255)      NOT NULL,
    message         TEXT,
    is_read         BOOLEAN           NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    link            TEXT,
    related_entity_type VARCHAR(50),
    related_entity_id   UUID,
    metadata        JSONB             NOT NULL DEFAULT '{}',
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

-- ── System Settings (key-value store) ────────────────────────
CREATE TABLE system_settings (
    key           VARCHAR(100) PRIMARY KEY,
    value         TEXT,
    value_type    VARCHAR(20)  NOT NULL DEFAULT 'string',
    description   TEXT,
    is_public     BOOLEAN      NOT NULL DEFAULT FALSE,
    updated_by    UUID         REFERENCES admin_users(id) ON DELETE SET NULL,
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
