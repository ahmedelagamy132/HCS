-- ============================================================
-- HCS — Equine Intelligence System
-- 02_enums.sql  |  Custom ENUM types
-- ============================================================

-- ── CLIENT ──────────────────────────────────────────────────
CREATE TYPE client_status AS ENUM (
    'active',       -- fully onboarded, subscription running
    'inactive',     -- manually deactivated
    'pending',      -- registered, awaiting onboarding review
    'suspended'     -- payment overdue / policy violation
);

-- ── STABLE ──────────────────────────────────────────────────
CREATE TYPE stable_status AS ENUM (
    'active',       -- operational, accepting horses
    'full',         -- at or over capacity
    'maintenance',  -- temporary closure for repairs
    'inactive'      -- permanently closed or decommissioned
);

-- ── HORSE ───────────────────────────────────────────────────
CREATE TYPE horse_gender AS ENUM (
    'stallion',     -- intact male ≥ 4 years
    'mare',         -- female ≥ 4 years
    'gelding',      -- castrated male
    'colt',         -- male < 4 years
    'filly'         -- female < 4 years
);

CREATE TYPE horse_health_status AS ENUM (
    'excellent',    -- all vitals optimal, no concerns
    'good',         -- minor deviations, no intervention needed
    'fair',         -- moderate concern, monitoring required
    'poor',         -- significant concern, vet review recommended
    'critical'      -- immediate veterinary intervention required
);

-- ── DEVICE / IOT ────────────────────────────────────────────
CREATE TYPE device_type AS ENUM (
    'collar',       -- HCS neck-worn biosensor collar
    'camera',       -- stable-mounted computer vision camera
    'gateway'       -- local IoT hub/gateway device
);

CREATE TYPE device_status AS ENUM (
    'active',
    'inactive',
    'charging',
    'low_battery',
    'offline',
    'maintenance',
    'retired'
);

-- ── ADMIN ───────────────────────────────────────────────────
CREATE TYPE admin_role AS ENUM (
    'super_admin',  -- full system access
    'staff_admin',  -- scoped resource access
    'view_only'     -- read-only across all resources
);

-- ── AI ──────────────────────────────────────────────────────
CREATE TYPE ai_model_status AS ENUM (
    'active',       -- deployed and serving
    'training',     -- currently being retrained
    'staging',      -- trained but not yet promoted to prod
    'offline',      -- disabled or paused
    'deprecated'    -- superseded by newer version
);

CREATE TYPE analysis_type AS ENUM (
    'health',
    'gait',
    'behavior',
    'diet',
    'disease',
    'performance'
);

CREATE TYPE analysis_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed'
);

-- ── HEALTH ──────────────────────────────────────────────────
CREATE TYPE alert_severity AS ENUM (
    'critical',     -- immediate action required
    'warning',      -- attention needed within hours
    'info'          -- informational, no immediate action
);

CREATE TYPE alert_status AS ENUM (
    'active',
    'acknowledged',
    'resolved',
    'dismissed'
);

CREATE TYPE health_record_type AS ENUM (
    'routine',          -- scheduled check
    'emergency',        -- urgent intervention
    'ai_analysis',      -- triggered by an AI model
    'sensor_anomaly',   -- triggered by live sensor reading
    'vet_visit',        -- on-site veterinarian visit
    'post_event'        -- after race/competition
);

-- ── SUBSCRIPTION ────────────────────────────────────────────
CREATE TYPE subscription_plan AS ENUM (
    'basic',        -- 1 stable, 10 horses, 100 AI analyses/month
    'professional', -- 5 stables, 100 horses, 1000 AI analyses/month
    'enterprise'    -- unlimited
);

CREATE TYPE subscription_status AS ENUM (
    'trial',
    'active',
    'past_due',
    'cancelled',
    'expired'
);

-- ── GENERAL ─────────────────────────────────────────────────
CREATE TYPE actor_type AS ENUM (
    'admin',
    'client',
    'system',
    'ai',
    'api'
);

CREATE TYPE notification_type AS ENUM (
    'alert',
    'info',
    'warning',
    'success',
    'system'
);
