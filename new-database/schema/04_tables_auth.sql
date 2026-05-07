-- ============================================================
-- HCS — Equine Intelligence System
-- 04_tables_auth.sql  |  Admin authentication & authorisation
-- ============================================================

-- ── Admin Users ─────────────────────────────────────────────
CREATE TABLE admin_users (
    id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_code     VARCHAR(20) UNIQUE NOT NULL,           -- ADM-001
    full_name      VARCHAR(255) NOT NULL,
    email          CITEXT      UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    role           admin_role  NOT NULL DEFAULT 'view_only',
    is_active      BOOLEAN     NOT NULL DEFAULT TRUE,
    avatar_url     TEXT,
    last_login_at  TIMESTAMPTZ,
    login_count    INTEGER     NOT NULL DEFAULT 0,
    failed_logins  INTEGER     NOT NULL DEFAULT 0,
    locked_until   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Admin Sessions ──────────────────────────────────────────
CREATE TABLE admin_sessions (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id     UUID        NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
    token_hash   VARCHAR(255) UNIQUE NOT NULL,            -- SHA-256 of bearer token
    ip_address   INET,
    user_agent   TEXT,
    is_valid     BOOLEAN     NOT NULL DEFAULT TRUE,
    expires_at   TIMESTAMPTZ NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at   TIMESTAMPTZ
);

-- ── Admin Permissions (per-resource, per-admin) ─────────────
CREATE TABLE admin_permissions (
    id         UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id   UUID        NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
    resource   VARCHAR(50) NOT NULL,   -- 'clients','stables','horses','ai_models','reports','settings'
    can_read   BOOLEAN     NOT NULL DEFAULT TRUE,
    can_create BOOLEAN     NOT NULL DEFAULT FALSE,
    can_update BOOLEAN     NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN     NOT NULL DEFAULT FALSE,
    can_export BOOLEAN     NOT NULL DEFAULT FALSE,
    granted_by UUID        REFERENCES admin_users(id) ON DELETE SET NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (admin_id, resource)
);

-- ── API Keys (for backend integrations) ─────────────────────
CREATE TABLE api_keys (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash    VARCHAR(255) UNIQUE NOT NULL,    -- stored hash; never plain text
    key_prefix  VARCHAR(12) NOT NULL,            -- shown in UI e.g. "hcs_k_Xa3Q..."
    name        VARCHAR(100) NOT NULL,           -- human label e.g. "IoT Gateway Dubai"
    scopes      TEXT[]      NOT NULL DEFAULT '{}',
    admin_id    UUID        REFERENCES admin_users(id) ON DELETE SET NULL,
    last_used_at TIMESTAMPTZ,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    expires_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Triggers ────────────────────────────────────────────────
CREATE TRIGGER trg_admin_users_updated
    BEFORE UPDATE ON admin_users
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
