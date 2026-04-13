-- ============================================================
-- HCS — Equine Intelligence System
-- 01_extensions.sql  |  PostgreSQL extensions
-- ============================================================

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cryptographic functions (password hashing)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Case-insensitive text (for email lookups)
CREATE EXTENSION IF NOT EXISTS "citext";

-- Time-series helpers
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Full-text search helper
CREATE EXTENSION IF NOT EXISTS "unaccent";
