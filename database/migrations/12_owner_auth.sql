-- ============================================================
-- HCS — Equine Intelligence System
-- 12_owner_auth.sql  |  Add password to clients for owner portal auth
-- ============================================================

ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- Set default password 'HCS@Owner2026' for existing active clients
UPDATE clients SET password_hash = crypt('HCS@Owner2026', gen_salt('bf',12))
WHERE password_hash IS NULL AND status = 'active';

-- ── Client Sessions (mirrors admin_sessions) ─────────────────
CREATE TABLE IF NOT EXISTS client_sessions (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id    UUID        NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    token_hash   VARCHAR(255) UNIQUE NOT NULL,
    ip_address   INET,
    user_agent   TEXT,
    is_valid     BOOLEAN     NOT NULL DEFAULT TRUE,
    expires_at   TIMESTAMPTZ NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at   TIMESTAMPTZ
);

-- Insert Youssef Galal as a client (idempotent)
INSERT INTO clients (id, client_code, full_name, email, phone, region, country, city, status, stable_count, horse_count, password_hash, created_at)
VALUES (
    'c0000013-0000-0000-0000-000000000013',
    'CLT-013',
    'Youssef Galal',
    'youssef.galal@equine.ae',
    '+971 50 847 1928',
    'Dubai',
    'UAE',
    'Dubai',
    'active',
    2,
    4,
    crypt('HCS@Owner2026', gen_salt('bf',12)),
    NOW() - INTERVAL '28 months'
) ON CONFLICT (email) DO UPDATE SET password_hash = crypt('HCS@Owner2026', gen_salt('bf',12))
WHERE clients.password_hash IS NULL;

-- Insert Youssef's horses if they don't exist yet
-- They belong to Al-Rayyan Stable (STB-001, id: 50000001-0000-0000-0000-000000000001)

INSERT INTO horses (id, horse_code, name, breed, gender, date_of_birth, color, weight_kg, height_cm, owner_id, stable_id, primary_vet_id, health_status, is_racing)
VALUES
    ('00000001-0000-0000-0000-000000000101','HRS-101','Sahara King',  'Arabian',      'stallion','2020-08-12',  'Bay',      510, 156, 'c0000013-0000-0000-0000-000000000013', '50000001-0000-0000-0000-000000000001', '1e700001-0000-0000-0000-000000000001', 'excellent', FALSE),
    ('00000001-0000-0000-0000-000000000102','HRS-102','Layali',       'Arabian',      'mare',    '2022-03-05',  'Grey',     465, 149, 'c0000013-0000-0000-0000-000000000013', '50000001-0000-0000-0000-000000000001', '1e700001-0000-0000-0000-000000000001', 'excellent', FALSE),
    ('00000001-0000-0000-0000-000000000103','HRS-103','Thunder Wind', 'Thoroughbred', 'gelding', '2018-11-15',  'Chestnut', 545, 163, 'c0000013-0000-0000-0000-000000000013', '50000001-0000-0000-0000-000000000001', '1e700001-0000-0000-0000-000000000001', 'good',      TRUE),
    ('00000001-0000-0000-0000-000000000104','HRS-104','Al Buraq',     'Arabian',      'stallion','2021-05-28',  'Black',    525, 154, 'c0000013-0000-0000-0000-000000000013', '50000001-0000-0000-0000-000000000001', '1e700001-0000-0000-0000-000000000001', 'excellent', FALSE)
ON CONFLICT (horse_code) DO NOTHING;
