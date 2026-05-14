-- ============================================================
-- HCS — Equine Intelligence System
-- 13_youssef_setup.sql  |  Youssef Galal + Egyptian Riding School
-- Run AFTER 12_owner_auth.sql
-- ============================================================

-- 1. Ensure password_hash column exists on clients
ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- 2. Ensure client_sessions table exists
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

-- 3. Upsert Youssef Galal client account (password: HCS@Owner2026)
INSERT INTO clients (id, client_code, full_name, email, phone, region, country, city, status, stable_count, horse_count, password_hash, created_at)
VALUES (
    'c0000013-0000-0000-0000-000000000013',
    'CLT-013',
    'Youssef Galal',
    'youssef.galal@equine.ae',
    '+971 50 847 1928',
    'Cairo',
    'Egypt',
    'Cairo',
    'active',
    1,
    1,
    crypt('HCS@Owner2026', gen_salt('bf',12)),
    NOW() - INTERVAL '28 months'
)
ON CONFLICT (id) DO UPDATE
    SET password_hash = crypt('HCS@Owner2026', gen_salt('bf',12)),
        full_name = 'Youssef Galal',
        status = 'active';

-- 4. Upsert Egyptian Riding School stable (owned by Youssef)
INSERT INTO stables (id, stable_code, name, city, region, country, capacity, occupied, status, owner_id, established_date, notes)
VALUES (
    'e0000001-0000-0000-0000-000000000001',
    'STB-ERS',
    'Egyptian Riding School',
    'Cairo',
    'Cairo',
    'Egypt',
    20,
    1,
    'active',
    'c0000013-0000-0000-0000-000000000013',
    '1985-01-01',
    'Since 1985 — Premier equestrian facility in Cairo.'
)
ON CONFLICT (id) DO UPDATE
    SET name = 'Egyptian Riding School',
        status = 'active';

-- 5. Upsert Casino horse (owned by Youssef, in Egyptian Riding School stable)
INSERT INTO horses (id, horse_code, name, breed, gender, date_of_birth, color, weight_kg, height_cm, owner_id, stable_id, primary_vet_id, health_status, is_racing, is_active)
VALUES (
    'a0000001-0000-0000-0000-000000000001',
    'HRS-ERS-01',
    'Casino',
    'Arabian',
    'stallion',
    '2019-06-15',
    'Bay',
    520,
    157,
    'c0000013-0000-0000-0000-000000000013',
    'e0000001-0000-0000-0000-000000000001',
    '1e700001-0000-0000-0000-000000000001',
    'excellent',
    FALSE,
    TRUE
)
ON CONFLICT (id) DO UPDATE
    SET name = 'Casino',
        stable_id = 'e0000001-0000-0000-0000-000000000001',
        owner_id  = 'c0000013-0000-0000-0000-000000000013'::uuid;

-- 6. Update Youssef's counts
UPDATE clients
SET stable_count = 1, horse_count = 1
WHERE id = 'c0000013-0000-0000-0000-000000000013';
