-- ============================================================
-- HCS — Equine Intelligence System
-- 14_fix_relationships.sql  |  Fix schema & data relationships
--
-- Fixes applied:
--   1. Add missing FK constraints on ai_analysis_id columns
--   2. Add trigger functions + triggers for clients.horse_count
--      and clients.stable_count (previously missing)
--   3. Move Youssef Galal's 4 horses from STB-001 (Al Nakheel,
--      Dubai) to STB-ERS (Egyptian Riding School, Cairo)
--   4. Add stable_assignment records for those 4 horses
--   5. Add subscription for Youssef (CLT-013)
--   6. Recalculate all clients.horse_count and clients.stable_count
--
-- Run AFTER: 13_youssef_setup.sql
-- ============================================================

BEGIN;

-- ── 1. FK constraints: ai_analysis_id → ai_analyses ─────────
-- Skip if already applied (idempotent via DO block)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_gait_ai_analysis'
    ) THEN
        ALTER TABLE gait_analyses
            ADD CONSTRAINT fk_gait_ai_analysis
            FOREIGN KEY (ai_analysis_id) REFERENCES ai_analyses(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_diet_ai_analysis'
    ) THEN
        ALTER TABLE diet_plans
            ADD CONSTRAINT fk_diet_ai_analysis
            FOREIGN KEY (ai_analysis_id) REFERENCES ai_analyses(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_behavior_ai_analysis'
    ) THEN
        ALTER TABLE behavior_records
            ADD CONSTRAINT fk_behavior_ai_analysis
            FOREIGN KEY (ai_analysis_id) REFERENCES ai_analyses(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_performance_ai_analysis'
    ) THEN
        ALTER TABLE performance_records
            ADD CONSTRAINT fk_performance_ai_analysis
            FOREIGN KEY (ai_analysis_id) REFERENCES ai_analyses(id) ON DELETE SET NULL;
    END IF;
END;
$$;

-- ── 2. Trigger function: clients.horse_count ─────────────────
CREATE OR REPLACE FUNCTION fn_refresh_client_horse_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.owner_id IS NOT NULL THEN
            UPDATE clients SET horse_count = (
                SELECT COUNT(*) FROM horses
                WHERE owner_id = OLD.owner_id AND is_active = TRUE
            ) WHERE id = OLD.owner_id;
        END IF;
        RETURN OLD;
    ELSE
        IF OLD.owner_id IS DISTINCT FROM NEW.owner_id AND OLD.owner_id IS NOT NULL THEN
            UPDATE clients SET horse_count = (
                SELECT COUNT(*) FROM horses
                WHERE owner_id = OLD.owner_id AND is_active = TRUE
            ) WHERE id = OLD.owner_id;
        END IF;
        IF NEW.owner_id IS NOT NULL THEN
            UPDATE clients SET horse_count = (
                SELECT COUNT(*) FROM horses
                WHERE owner_id = NEW.owner_id AND is_active = TRUE
            ) WHERE id = NEW.owner_id;
        END IF;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ── 2. Trigger function: clients.stable_count ────────────────
CREATE OR REPLACE FUNCTION fn_refresh_client_stable_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.owner_id IS NOT NULL THEN
            UPDATE clients SET stable_count = (
                SELECT COUNT(*) FROM stables WHERE owner_id = OLD.owner_id
            ) WHERE id = OLD.owner_id;
        END IF;
        RETURN OLD;
    ELSE
        IF OLD.owner_id IS DISTINCT FROM NEW.owner_id AND OLD.owner_id IS NOT NULL THEN
            UPDATE clients SET stable_count = (
                SELECT COUNT(*) FROM stables WHERE owner_id = OLD.owner_id
            ) WHERE id = OLD.owner_id;
        END IF;
        IF NEW.owner_id IS NOT NULL THEN
            UPDATE clients SET stable_count = (
                SELECT COUNT(*) FROM stables WHERE owner_id = NEW.owner_id
            ) WHERE id = NEW.owner_id;
        END IF;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ── 2. Triggers (idempotent) ─────────────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_horses_client_count'
    ) THEN
        CREATE TRIGGER trg_horses_client_count
            AFTER INSERT OR UPDATE OF owner_id, is_active OR DELETE ON horses
            FOR EACH ROW EXECUTE FUNCTION fn_refresh_client_horse_count();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_stables_client_count'
    ) THEN
        CREATE TRIGGER trg_stables_client_count
            AFTER INSERT OR UPDATE OF owner_id OR DELETE ON stables
            FOR EACH ROW EXECUTE FUNCTION fn_refresh_client_stable_count();
    END IF;
END;
$$;

-- ── 3. Move Youssef's 4 horses to Egyptian Riding School ─────
-- Migration 12 incorrectly placed these at STB-001 (Al Nakheel,
-- Dubai, owned by Khalid CLT-001). Youssef is in Cairo and owns
-- STB-ERS (Egyptian Riding School). All his horses belong there.
UPDATE horses
SET stable_id = 'e0000001-0000-0000-0000-000000000001'  -- STB-ERS
WHERE id IN (
    '00000001-0000-0000-0000-000000000101',  -- HRS-101 Sahara King
    '00000001-0000-0000-0000-000000000102',  -- HRS-102 Layali
    '00000001-0000-0000-0000-000000000103',  -- HRS-103 Thunder Wind
    '00000001-0000-0000-0000-000000000104'   -- HRS-104 Al Buraq
)
AND stable_id = '50000001-0000-0000-0000-000000000001'; -- only if still at STB-001

-- ── 4. Stable assignment history for Youssef's 4 horses ──────
-- They were initially registered at STB-001 (migration 12),
-- then moved to STB-ERS (this migration). Record both legs.
INSERT INTO stable_assignments (horse_id, stable_id, assigned_at, removed_at, reason, assigned_by)
SELECT
    h.id,
    '50000001-0000-0000-0000-000000000001',  -- STB-001
    NOW() - INTERVAL '28 months',            -- approximately when migration 12 ran
    NOW(),
    'Initial registration (incorrect stable — corrected by migration 14)',
    'f0000001-0000-0000-0000-000000000001'   -- ADM-001 Ahmed
FROM horses h
WHERE h.id IN (
    '00000001-0000-0000-0000-000000000101',
    '00000001-0000-0000-0000-000000000102',
    '00000001-0000-0000-0000-000000000103',
    '00000001-0000-0000-0000-000000000104'
)
AND NOT EXISTS (
    SELECT 1 FROM stable_assignments sa
    WHERE sa.horse_id = h.id
      AND sa.stable_id = '50000001-0000-0000-0000-000000000001'
);

INSERT INTO stable_assignments (horse_id, stable_id, assigned_at, removed_at, reason, assigned_by)
SELECT
    id,
    'e0000001-0000-0000-0000-000000000001',  -- STB-ERS
    NOW(),
    NULL,
    'Moved to owner''s stable (Egyptian Riding School, Cairo)',
    'f0000001-0000-0000-0000-000000000001'   -- ADM-001 Ahmed
FROM horses
WHERE id IN (
    '00000001-0000-0000-0000-000000000101',
    '00000001-0000-0000-0000-000000000102',
    '00000001-0000-0000-0000-000000000103',
    '00000001-0000-0000-0000-000000000104'
)
AND NOT EXISTS (
    SELECT 1 FROM stable_assignments sa
    WHERE sa.horse_id = horses.id
      AND sa.stable_id = 'e0000001-0000-0000-0000-000000000001'
      AND sa.removed_at IS NULL
);

-- ── 5. Subscription for Youssef (CLT-013) ───────────────────
INSERT INTO subscriptions (client_id, plan, status, start_date, monthly_rate, currency, max_stables, max_horses, ai_analyses_per_month)
VALUES (
    'c0000013-0000-0000-0000-000000000013',
    'basic',
    'active',
    (CURRENT_DATE - INTERVAL '28 months')::DATE,
    890, 'AED', 1, 10, 100
)
ON CONFLICT DO NOTHING;

-- ── 6. Recalculate all client counts ────────────────────────
-- This corrects counts for ALL clients after all data fixes above.
UPDATE clients SET
    horse_count  = (
        SELECT COUNT(*) FROM horses
        WHERE owner_id = clients.id AND is_active = TRUE
    ),
    stable_count = (
        SELECT COUNT(*) FROM stables
        WHERE owner_id = clients.id
    );

COMMIT;

\echo ''
\echo '============================================================'
\echo ' Migration 14 applied: relationships fixed.'
\echo ' Run the verification queries below to confirm:'
\echo ''
\echo ' SELECT client_code,'
\echo '        horse_count  AS stored_horses,'
\echo '        (SELECT COUNT(*) FROM horses WHERE owner_id=clients.id AND is_active=TRUE) AS actual_horses,'
\echo '        stable_count AS stored_stables,'
\echo '        (SELECT COUNT(*) FROM stables WHERE owner_id=clients.id) AS actual_stables'
\echo ' FROM clients ORDER BY client_code;'
\echo '============================================================'
