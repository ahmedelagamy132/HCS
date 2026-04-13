-- ============================================================
-- HCS — Equine Intelligence System
-- 07_tables_health.sql  |  Health records, alerts & clinical data
-- ============================================================

-- ── Horse Health Records (periodic assessments) ─────────────
CREATE TABLE horse_health_records (
    id                      UUID                 PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id                UUID                 NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    recorded_at             TIMESTAMPTZ          NOT NULL DEFAULT NOW(),
    record_type             health_record_type   NOT NULL DEFAULT 'routine',

    -- Vitals snapshot
    heart_rate_bpm          SMALLINT,
    temperature_celsius     DECIMAL(4,2),
    respiratory_rate        SMALLINT,
    weight_kg               DECIMAL(6,2),
    blood_pressure_systolic SMALLINT,
    blood_pressure_diastolic SMALLINT,
    spo2_pct                SMALLINT,
    capillary_refill_sec    DECIMAL(3,1),        -- normal ≤ 2s
    gut_sounds              VARCHAR(20),         -- 'normal','reduced','absent','hypermotile'
    mucous_membrane_color   VARCHAR(30),         -- 'pink','pale','yellow','blue'

    -- Computed score (0-100, higher = healthier)
    health_score            DECIMAL(5,2)
                            CONSTRAINT chk_score CHECK (health_score BETWEEN 0 AND 100),
    status                  horse_health_status,

    -- Findings
    body_condition_score    DECIMAL(3,1),        -- 1-9 Henneke scale
    lameness_grade          SMALLINT,            -- 0-5 AAEP scale
    pain_score              SMALLINT,            -- 0-10
    notes                   TEXT,
    findings                JSONB NOT NULL DEFAULT '{}',

    -- Attribution
    vet_id                  UUID REFERENCES veterinarians(id) ON DELETE SET NULL,
    recorded_by_admin       UUID REFERENCES admin_users(id)  ON DELETE SET NULL,
    triggered_by_alert      UUID,                -- FK set after health_alerts created
    metadata                JSONB NOT NULL DEFAULT '{}'
);

-- ── Health Alerts ─────────────────────────────────────────────
CREATE TABLE health_alerts (
    id               UUID           PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id         UUID           REFERENCES horses(id)   ON DELETE CASCADE,
    stable_id        UUID           REFERENCES stables(id)  ON DELETE CASCADE,
    severity         alert_severity NOT NULL DEFAULT 'warning',
    title            VARCHAR(255)   NOT NULL,
    description      TEXT,
    status           alert_status   NOT NULL DEFAULT 'active',

    -- Source
    detected_by      VARCHAR(50)    NOT NULL DEFAULT 'system', -- 'ai_model','sensor','vet','admin'
    ai_model_id      UUID           REFERENCES ai_models(id) ON DELETE SET NULL,
    sensor_reading_id UUID,                    -- reference to sensor_readings.id (no FK — partitioned)
    cv_event_id      UUID           REFERENCES cv_events(id) ON DELETE SET NULL,
    confidence_score DECIMAL(5,2),

    -- Resolution workflow
    acknowledged_by  UUID           REFERENCES admin_users(id) ON DELETE SET NULL,
    acknowledged_at  TIMESTAMPTZ,
    resolved_by      UUID           REFERENCES admin_users(id) ON DELETE SET NULL,
    resolved_at      TIMESTAMPTZ,
    resolution_notes TEXT,

    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- ── Gait Analysis Results (from Computer Vision) ─────────────
CREATE TABLE gait_analyses (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id            UUID        NOT NULL REFERENCES horses(id)   ON DELETE CASCADE,
    ai_analysis_id      UUID        REFERENCES ai_analyses(id)       ON DELETE SET NULL,
    cv_event_id         UUID        REFERENCES cv_events(id)         ON DELETE SET NULL,
    analyzed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Gait metrics
    stride_length_cm    DECIMAL(6,2),
    stride_frequency_hz DECIMAL(4,2),
    stance_duration_ms  DECIMAL(6,1),
    swing_duration_ms   DECIMAL(6,1),
    symmetry_score      DECIMAL(5,2)  -- 0-100, 100=perfect symmetry
                        CONSTRAINT chk_symmetry CHECK (symmetry_score BETWEEN 0 AND 100),

    -- Lameness
    lameness_detected   BOOLEAN     NOT NULL DEFAULT FALSE,
    lameness_grade      SMALLINT    CONSTRAINT chk_lameness_grade CHECK (lameness_grade BETWEEN 0 AND 5),
    affected_limbs      TEXT[],     -- ['LF','RH'] (LF=left front, RH=right hind, etc.)

    -- Media
    video_url           TEXT,
    thumbnail_url       TEXT,

    raw_keypoints       JSONB NOT NULL DEFAULT '{}',  -- skeleton keypoint coordinates
    notes               TEXT
);

-- ── Diet Plans (AI-generated nutrition plans) ────────────────
CREATE TABLE diet_plans (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id         UUID        NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    ai_analysis_id   UUID        REFERENCES ai_analyses(id)    ON DELETE SET NULL,
    created_by_admin UUID        REFERENCES admin_users(id)    ON DELETE SET NULL,

    -- Macronutrients
    daily_calories   DECIMAL(8,2),            -- kcal/day
    protein_pct      DECIMAL(4,2),
    fat_pct          DECIMAL(4,2),
    fiber_pct        DECIMAL(4,2),
    water_liters     DECIMAL(5,2),

    -- Detailed schedule (array of feeding events per day)
    feed_schedule    JSONB NOT NULL DEFAULT '[]',
    -- [{"time":"07:00","type":"hay","amount_kg":2.5},{"time":"12:00","type":"grain","amount_kg":1.2}]

    supplements      JSONB NOT NULL DEFAULT '[]',
    -- [{"name":"Vitamin E","dose_mg":1000,"frequency":"daily"}]

    restrictions     JSONB NOT NULL DEFAULT '[]',
    -- [{"item":"alfalfa","reason":"high_protein"}]

    valid_from       DATE,
    valid_until      DATE,
    status           VARCHAR(20) NOT NULL DEFAULT 'active',
    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Behavior Records ─────────────────────────────────────────
CREATE TABLE behavior_records (
    id                UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id          UUID        NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    ai_analysis_id    UUID        REFERENCES ai_analyses(id)    ON DELETE SET NULL,
    observed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Scores 1-10
    stress_level      SMALLINT    CONSTRAINT chk_stress  CHECK (stress_level  BETWEEN 1 AND 10),
    appetite_score    SMALLINT    CONSTRAINT chk_appetite CHECK (appetite_score BETWEEN 1 AND 10),
    social_score      SMALLINT    CONSTRAINT chk_social   CHECK (social_score  BETWEEN 1 AND 10),
    alertness_score   SMALLINT    CONSTRAINT chk_alert    CHECK (alertness_score BETWEEN 1 AND 10),

    -- Activity
    activity_level    VARCHAR(30),  -- 'resting','grazing','walking','playing','distressed'
    rest_hours        DECIMAL(4,2),
    movement_distance_m DECIMAL(8,2),

    notable_behaviors JSONB NOT NULL DEFAULT '[]',
    -- ["weaving","cribbing","pawing","head_tossing"]

    predictions       JSONB NOT NULL DEFAULT '{}',
    -- {"next_24h_stress_risk":0.23,"feed_refusal_risk":0.08}

    notes             TEXT
);

-- ── Performance Records ───────────────────────────────────────
CREATE TABLE performance_records (
    id                    UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id              UUID        NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    ai_analysis_id        UUID        REFERENCES ai_analyses(id)    ON DELETE SET NULL,

    event_type            VARCHAR(50),  -- 'race','training_session','endurance','dressage','show_jumping'
    event_name            VARCHAR(255),
    event_date            DATE,
    venue                 VARCHAR(255),

    -- Performance
    distance_m            INTEGER,
    time_seconds          DECIMAL(8,3),
    speed_ms              DECIMAL(6,3),
    placement             SMALLINT,
    total_competitors     SMALLINT,

    -- Biometrics during event
    heart_rate_max        SMALLINT,
    heart_rate_avg        SMALLINT,
    heart_rate_recovery   SMALLINT,   -- BPM at 1 min post-event
    recovery_time_min     SMALLINT,
    temperature_peak      DECIMAL(4,2),

    -- AI score
    performance_score     DECIMAL(5,2)  -- 0-100
                          CONSTRAINT chk_perf_score CHECK (performance_score BETWEEN 0 AND 100),
    predicted_score       DECIMAL(5,2), -- AI pre-event prediction

    notes                 TEXT,
    raw_telemetry         JSONB NOT NULL DEFAULT '{}',
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Vaccination & Medical History ────────────────────────────
CREATE TABLE medical_records (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id        UUID        NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    vet_id          UUID        REFERENCES veterinarians(id)   ON DELETE SET NULL,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    record_type     VARCHAR(50) NOT NULL, -- 'vaccination','deworming','dental','surgery','medication','injury'
    description     TEXT        NOT NULL,
    medication      VARCHAR(255),
    dosage          VARCHAR(100),
    next_due_date   DATE,
    attachments     TEXT[],               -- URLs to documents / lab results
    notes           TEXT,
    created_by      UUID        REFERENCES admin_users(id) ON DELETE SET NULL
);

-- ── Triggers ─────────────────────────────────────────────────
CREATE TRIGGER trg_health_alerts_updated
    BEFORE UPDATE ON health_alerts
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_diet_plans_updated
    BEFORE UPDATE ON diet_plans
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- Sync horse.health_status when a new health record is saved
CREATE TRIGGER trg_sync_horse_health
    AFTER INSERT ON horse_health_records
    FOR EACH ROW EXECUTE FUNCTION fn_sync_horse_health_status();
