-- ============================================================
-- HCS — Equine Intelligence System
-- 06_tables_iot.sql  |  IoT devices & sensor telemetry
-- ============================================================

-- ── IoT Devices (collars + cameras + gateways) ──────────────
CREATE TABLE devices (
    id              UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_code     VARCHAR(50)   UNIQUE NOT NULL,         -- e.g. COL-001, CAM-001
    device_type     device_type   NOT NULL,
    model_number    VARCHAR(100),
    firmware_version VARCHAR(20),
    serial_number   VARCHAR(100)  UNIQUE,
    status          device_status NOT NULL DEFAULT 'inactive',

    -- assignment
    stable_id       UUID          REFERENCES stables(id) ON DELETE SET NULL,
    horse_id        UUID          REFERENCES horses(id) ON DELETE SET NULL, -- collars only
    assigned_at     TIMESTAMPTZ,

    -- connectivity
    last_seen_at    TIMESTAMPTZ,
    battery_pct     SMALLINT      CONSTRAINT chk_battery CHECK (battery_pct BETWEEN 0 AND 100),
    signal_strength SMALLINT,                              -- dBm
    ip_address      INET,
    mac_address     MACADDR,

    -- location (for cameras)
    location_label  VARCHAR(100),                         -- "Stall 7 – North Wall"
    latitude        DECIMAL(9,6),
    longitude       DECIMAL(9,6),

    notes           TEXT,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ── Sensor Readings (TIME-SERIES — partitioned by month) ────
-- Each row = one reading burst from a collar device
-- Partitioned monthly to manage volume (expected: ~1440 rows/horse/day)
CREATE TABLE sensor_readings (
    id                  UUID        NOT NULL DEFAULT uuid_generate_v4(),
    device_id           UUID        NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    horse_id            UUID        NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Vital signs (HCS Collar biosensors)
    heart_rate_bpm      SMALLINT,                         -- typical equine: 28-44 BPM
    temperature_celsius DECIMAL(4,2),                     -- typical: 37.2–38.3°C
    respiratory_rate    SMALLINT,                         -- breaths/min: 8-16
    spo2_pct            SMALLINT,                         -- blood oxygen %

    -- Motion (6-axis IMU)
    accel_x             DECIMAL(6,4),
    accel_y             DECIMAL(6,4),
    accel_z             DECIMAL(6,4),
    gyro_x              DECIMAL(6,4),
    gyro_y              DECIMAL(6,4),
    gyro_z              DECIMAL(6,4),
    activity_level      SMALLINT,                         -- 0=rest,1=walk,2=trot,3=canter,4=gallop

    -- Derived / computed
    is_anomaly          BOOLEAN     NOT NULL DEFAULT FALSE,
    anomaly_flags       TEXT[]      NOT NULL DEFAULT '{}', -- ['high_temp','irregular_hr']
    quality_score       SMALLINT,                         -- 0-100 signal quality

    PRIMARY KEY (id, recorded_at)
) PARTITION BY RANGE (recorded_at);

-- Create initial monthly partitions (2025-01 through 2027-12)
DO $$
DECLARE
    y   INTEGER;
    m   INTEGER;
    s   DATE;
    e   DATE;
    tbl TEXT;
BEGIN
    FOR y IN 2025..2027 LOOP
        FOR m IN 1..12 LOOP
            s   := make_date(y, m, 1);
            e   := s + INTERVAL '1 month';
            tbl := format('sensor_readings_%s_%s', y, LPAD(m::TEXT, 2, '0'));
            EXECUTE format(
                'CREATE TABLE IF NOT EXISTS %I PARTITION OF sensor_readings FOR VALUES FROM (%L) TO (%L)',
                tbl, s, e
            );
        END LOOP;
    END LOOP;
END;
$$;

-- ── Camera Frames / CV Events ────────────────────────────────
-- One row per detected computer-vision event (not per frame — filtered)
CREATE TABLE cv_events (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id       UUID        NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    stable_id       UUID        NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    horse_id        UUID        REFERENCES horses(id) ON DELETE SET NULL,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type      VARCHAR(50) NOT NULL,  -- 'lameness','fall','abnormal_posture','distress','feeding'
    confidence      DECIMAL(5,2),          -- 0-100
    bounding_box    JSONB,                 -- {"x":0.1,"y":0.2,"w":0.3,"h":0.4}
    frame_url       TEXT,                 -- S3 / object storage URL
    metadata        JSONB       NOT NULL DEFAULT '{}',
    is_reviewed     BOOLEAN     NOT NULL DEFAULT FALSE,
    reviewed_by     UUID        REFERENCES admin_users(id) ON DELETE SET NULL,
    reviewed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Triggers ─────────────────────────────────────────────────
CREATE TRIGGER trg_devices_updated
    BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
