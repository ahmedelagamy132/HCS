-- ============================================================
-- HCS — Equine Intelligence System
-- 09_tables_system.sql  |  Activity logs, notifications & settings
-- ============================================================

-- ── Activity / Audit Log ─────────────────────────────────────
-- Immutable append-only audit trail for compliance
CREATE TABLE activity_logs (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_type   actor_type  NOT NULL,
    actor_id     UUID,                           -- admin_users.id or clients.id
    actor_label  VARCHAR(255),                   -- denormalised name for deleted actors
    action       VARCHAR(100) NOT NULL,          -- 'created','updated','deleted','login','logout','export'
    entity_type  VARCHAR(50),                    -- 'horse','stable','client','ai_model', etc.
    entity_id    UUID,
    entity_label VARCHAR(255),                   -- denormalised label
    description  TEXT,
    ip_address   INET,
    user_agent   TEXT,
    metadata     JSONB        NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Notifications ────────────────────────────────────────────
CREATE TABLE notifications (
    id              UUID              PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipient_type  VARCHAR(20)       NOT NULL,  -- 'admin','client'
    recipient_id    UUID              NOT NULL,
    type            notification_type NOT NULL DEFAULT 'info',
    title           VARCHAR(255)      NOT NULL,
    message         TEXT,
    is_read         BOOLEAN           NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    link            TEXT,                        -- deep-link in dashboard e.g. "/horses/HRS-008"
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
    value_type    VARCHAR(20)  NOT NULL DEFAULT 'string',  -- 'string','integer','boolean','json'
    description   TEXT,
    is_public     BOOLEAN      NOT NULL DEFAULT FALSE,     -- exposed to frontend?
    updated_by    UUID         REFERENCES admin_users(id)  ON DELETE SET NULL,
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Email / SMS Notification Queue ───────────────────────────
CREATE TABLE notification_queue (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel         VARCHAR(20) NOT NULL,  -- 'email','sms','push'
    recipient_email CITEXT,
    recipient_phone VARCHAR(50),
    recipient_name  VARCHAR(255),
    subject         VARCHAR(255),
    body            TEXT        NOT NULL,
    template_id     VARCHAR(100),
    template_vars   JSONB       NOT NULL DEFAULT '{}',
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending,sent,failed,cancelled
    attempts        SMALLINT    NOT NULL DEFAULT 0,
    last_attempted_at TIMESTAMPTZ,
    sent_at         TIMESTAMPTZ,
    error_message   TEXT,
    priority        SMALLINT    NOT NULL DEFAULT 5,         -- 1=highest,10=lowest
    related_alert_id UUID       REFERENCES health_alerts(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Reports ──────────────────────────────────────────────────
CREATE TABLE reports (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_type     VARCHAR(50) NOT NULL,  -- 'health_summary','stable_utilization','client_portfolio','ai_performance','financial','audit'
    title           VARCHAR(255) NOT NULL,
    generated_by    UUID        REFERENCES admin_users(id) ON DELETE SET NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending,generating,ready,failed
    parameters      JSONB       NOT NULL DEFAULT '{}',       -- date_range, filters, etc.
    file_url        TEXT,                                    -- S3 URL when ready
    file_format     VARCHAR(10),                             -- 'pdf','csv','xlsx'
    file_size_bytes INTEGER,
    generated_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Webhooks (for external integrations) ─────────────────────
CREATE TABLE webhooks (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL,
    url             TEXT        NOT NULL,
    secret_hash     VARCHAR(255),
    events          TEXT[]      NOT NULL DEFAULT '{}', -- ['alert.created','horse.health_changed']
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    last_triggered_at TIMESTAMPTZ,
    failure_count   SMALLINT    NOT NULL DEFAULT 0,
    created_by      UUID        REFERENCES admin_users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Webhook Delivery Logs ────────────────────────────────────
CREATE TABLE webhook_deliveries (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id      UUID        NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type      VARCHAR(100) NOT NULL,
    payload         JSONB       NOT NULL DEFAULT '{}',
    status_code     SMALLINT,
    response_body   TEXT,
    duration_ms     INTEGER,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    attempts        SMALLINT    NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Triggers ─────────────────────────────────────────────────
CREATE TRIGGER trg_webhooks_updated
    BEFORE UPDATE ON webhooks
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
