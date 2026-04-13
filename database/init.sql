-- ============================================================
-- HCS — Equine Intelligence System
-- init.sql  |  Master setup script — run this to create the full DB
--
-- Usage (psql):
--   createdb hcs_db
--   psql -d hcs_db -f database/init.sql
--
-- Or with connection string:
--   psql postgresql://user:pass@localhost:5432/hcs_db -f database/init.sql
-- ============================================================

\set ON_ERROR_STOP on
\set ECHO all

BEGIN;

-- ── 1. Extensions ────────────────────────────────────────────
\ir schema/01_extensions.sql

-- ── 2. Enum types ────────────────────────────────────────────
\ir schema/02_enums.sql

-- ── 3. Functions & trigger procedures ───────────────────────
\ir schema/03_functions.sql

-- ── 4. Auth tables ───────────────────────────────────────────
\ir schema/04_tables_auth.sql

-- ── 5. Core tables (clients, stables, horses) ───────────────
\ir schema/05_tables_core.sql

-- ── 6. IoT / device tables ───────────────────────────────────
\ir schema/06_tables_iot.sql

-- ── 7. Health tables (must come after AI models stub) ────────
-- ai_models table is referenced in health tables; we create a
-- temporary forward-reference stub and replace it in step 8.
-- health_alerts references ai_models (ON DELETE SET NULL) so
-- the FK is deferred — create health tables first, add FK later.
\ir schema/07_tables_health.sql

-- ── 8. AI tables ────────────────────────────────────────────
\ir schema/08_tables_ai.sql

-- ── Add deferred FK: health_alerts → ai_models ──────────────
ALTER TABLE health_alerts
    ADD CONSTRAINT fk_alerts_ai_model
    FOREIGN KEY (ai_model_id) REFERENCES ai_models(id) ON DELETE SET NULL;

-- ── Add deferred FK: horse_health_records → health_alerts ───
ALTER TABLE horse_health_records
    ADD CONSTRAINT fk_health_rec_alert
    FOREIGN KEY (triggered_by_alert) REFERENCES health_alerts(id) ON DELETE SET NULL;

-- ── 9. System tables ─────────────────────────────────────────
\ir schema/09_tables_system.sql

-- ── 10. Indexes ──────────────────────────────────────────────
\ir schema/10_indexes.sql

-- ── 11. Views ────────────────────────────────────────────────
\ir schema/11_views.sql

-- ── Seed data ────────────────────────────────────────────────
\ir seed/01_admins.sql
\ir seed/02_clients_stables.sql
\ir seed/03_horses.sql
\ir seed/04_ai_models.sql

COMMIT;

\echo ''
\echo '============================================================'
\echo ' HCS Database initialised successfully.'
\echo ' Run: SELECT * FROM v_system_kpis; to verify.'
\echo '============================================================'
