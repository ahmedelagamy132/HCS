-- ============================================================
-- HCS — Equine Intelligence System
-- 05_tables_core.sql  |  Core business entities
-- ============================================================

-- ── Clients (horse owners / stable managers) ────────────────
CREATE TABLE clients (
    id              UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_code     VARCHAR(20)  UNIQUE NOT NULL,          -- CLT-001
    full_name       VARCHAR(255) NOT NULL,
    email           CITEXT       UNIQUE NOT NULL,
    phone           VARCHAR(50),
    region          VARCHAR(100),
    country         VARCHAR(100) NOT NULL DEFAULT 'UAE',
    city            VARCHAR(100),
    address         TEXT,
    status          client_status NOT NULL DEFAULT 'pending',
    notes           TEXT,
    -- denormalised counts (kept fresh by triggers)
    stable_count    INTEGER      NOT NULL DEFAULT 0,
    horse_count     INTEGER      NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Veterinarians ────────────────────────────────────────────
CREATE TABLE veterinarians (
    id              UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name       VARCHAR(255) NOT NULL,
    license_number  VARCHAR(100) UNIQUE,
    specialty       VARCHAR(100),                          -- 'equine', 'large animal', etc.
    clinic_name     VARCHAR(255),
    email           CITEXT,
    phone           VARCHAR(50),
    city            VARCHAR(100),
    country         VARCHAR(100),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    notes           TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Stables ──────────────────────────────────────────────────
CREATE TABLE stables (
    id              UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_code     VARCHAR(20)  UNIQUE NOT NULL,          -- STB-001
    name            VARCHAR(255) NOT NULL,
    address         TEXT,
    city            VARCHAR(100),
    region          VARCHAR(100),
    country         VARCHAR(100) NOT NULL DEFAULT 'UAE',
    latitude        DECIMAL(9,6),
    longitude       DECIMAL(9,6),
    capacity        INTEGER      NOT NULL DEFAULT 0
                    CONSTRAINT chk_capacity_positive CHECK (capacity >= 0),
    occupied        INTEGER      NOT NULL DEFAULT 0        -- refreshed by trigger
                    CONSTRAINT chk_occupied_non_negative CHECK (occupied >= 0),
    status          stable_status NOT NULL DEFAULT 'active',
    owner_id        UUID         REFERENCES clients(id) ON DELETE SET NULL,
    primary_vet_id  UUID         REFERENCES veterinarians(id) ON DELETE SET NULL,
    facilities      JSONB        NOT NULL DEFAULT '[]',    -- ["arena","wash_bay","tack_room"]
    notes           TEXT,
    established_date DATE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_occupied_lte_capacity CHECK (occupied <= capacity + 5)  -- small buffer
);

-- ── Horses ───────────────────────────────────────────────────
CREATE TABLE horses (
    id               UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_code       VARCHAR(20)  UNIQUE NOT NULL,         -- HRS-001
    name             VARCHAR(255) NOT NULL,
    breed            VARCHAR(100),
    gender           horse_gender,
    date_of_birth    DATE,
    color            VARCHAR(100),
    markings         TEXT,                                 -- distinguishing marks
    weight_kg        DECIMAL(6,2),
    height_cm        DECIMAL(5,2),
    passport_number  VARCHAR(100) UNIQUE,
    chip_number      VARCHAR(100) UNIQUE,
    owner_id         UUID         REFERENCES clients(id) ON DELETE SET NULL,
    stable_id        UUID         REFERENCES stables(id) ON DELETE SET NULL,
    primary_vet_id   UUID         REFERENCES veterinarians(id) ON DELETE SET NULL,
    health_status    horse_health_status NOT NULL DEFAULT 'good',
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    is_racing        BOOLEAN      NOT NULL DEFAULT FALSE,
    notes            TEXT,
    photo_url        TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Stable Assignments (horse-movement history) ──────────────
CREATE TABLE stable_assignments (
    id              UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id        UUID         NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    stable_id       UUID         NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    assigned_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    removed_at      TIMESTAMPTZ,
    reason          TEXT,
    assigned_by     UUID         REFERENCES admin_users(id) ON DELETE SET NULL,
    CONSTRAINT chk_assignment_dates CHECK (removed_at IS NULL OR removed_at > assigned_at)
);

-- ── Subscriptions ────────────────────────────────────────────
CREATE TABLE subscriptions (
    id                      UUID              PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id               UUID              NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    plan                    subscription_plan NOT NULL DEFAULT 'basic',
    status                  subscription_status NOT NULL DEFAULT 'trial',
    start_date              DATE              NOT NULL,
    end_date                DATE,
    monthly_rate            DECIMAL(10,2),
    currency                CHAR(3)           NOT NULL DEFAULT 'AED',
    max_stables             INTEGER           NOT NULL DEFAULT 1,
    max_horses              INTEGER           NOT NULL DEFAULT 10,
    ai_analyses_per_month   INTEGER           NOT NULL DEFAULT 100,
    -- billing
    next_billing_date       DATE,
    last_payment_at         TIMESTAMPTZ,
    last_payment_amount     DECIMAL(10,2),
    created_at              TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

-- ── Triggers ─────────────────────────────────────────────────

-- updated_at
CREATE TRIGGER trg_clients_updated
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_stables_updated
    BEFORE UPDATE ON stables
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_horses_updated
    BEFORE UPDATE ON horses
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_vets_updated
    BEFORE UPDATE ON veterinarians
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_subscriptions_updated
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- Refresh stable occupied count whenever a horse row changes
CREATE TRIGGER trg_horse_stable_occupancy
    AFTER INSERT OR UPDATE OF stable_id, is_active OR DELETE ON horses
    FOR EACH ROW EXECUTE FUNCTION fn_refresh_stable_occupied();
