-- ============================================================
-- HCS â€” Equine Intelligence System
-- init.sql  |  Master setup script â€” run this to create the full DB
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

-- â”€â”€ 1. Extensions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
\ir schema/01_extensions.sql

-- â”€â”€ 2. Enum types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
\ir schema/02_enums.sql

-- â”€â”€ 3. Functions & trigger procedures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
\ir schema/03_functions.sql

-- â”€â”€ 4. Auth tables â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
\ir schema/04_tables_auth.sql

-- â”€â”€ 5. Core tables (clients, stables, horses) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
\ir schema/05_tables_core.sql

-- â”€â”€ 6. IoT / device tables â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
\ir schema/06_tables_iot.sql

-- â”€â”€ 7. Health tables (must come after AI models stub) â”€â”€â”€â”€â”€â”€â”€â”€
-- ai_models table is referenced in health tables; we create a
-- temporary forward-reference stub and replace it in step 8.
-- health_alerts references ai_models (ON DELETE SET NULL) so
-- the FK is deferred â€” create health tables first, add FK later.
\ir schema/07_tables_health.sql

-- â”€â”€ 8. AI tables â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
\ir schema/08_tables_ai.sql

-- â”€â”€ 9. System tables â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
\ir schema/09_tables_system.sql

-- â”€â”€ 10. Indexes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
\ir schema/10_indexes.sql

-- â”€â”€ 11. Views â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
\ir schema/11_views.sql

-- â”€â”€ Seed data â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

