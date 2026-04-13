-- ============================================================
-- HCS — Equine Intelligence System
-- 08_tables_ai.sql  |  AI models, analyses & training pipeline
-- ============================================================

-- ── AI Model Registry ────────────────────────────────────────
CREATE TABLE ai_models (
    id               UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    name             VARCHAR(100)    UNIQUE NOT NULL,        -- "Health Analyzer"
    slug             VARCHAR(100)    UNIQUE NOT NULL,        -- "health-analyzer"
    description      TEXT,
    model_type       analysis_type   NOT NULL,
    version          VARCHAR(20)     NOT NULL DEFAULT '1.0.0',
    status           ai_model_status NOT NULL DEFAULT 'active',

    -- Performance metrics (updated after each training run)
    accuracy_score   DECIMAL(5,2)    CONSTRAINT chk_acc  CHECK (accuracy_score  BETWEEN 0 AND 100),
    precision_score  DECIMAL(5,2)    CONSTRAINT chk_prec CHECK (precision_score BETWEEN 0 AND 100),
    recall_score     DECIMAL(5,2)    CONSTRAINT chk_rec  CHECK (recall_score    BETWEEN 0 AND 100),
    f1_score         DECIMAL(5,2)    CONSTRAINT chk_f1   CHECK (f1_score        BETWEEN 0 AND 100),
    avg_response_ms  INTEGER,

    -- Usage counters (refreshed by trigger)
    total_requests   BIGINT          NOT NULL DEFAULT 0,
    requests_today   INTEGER         NOT NULL DEFAULT 0,    -- reset each midnight via cron

    -- Lifecycle
    last_trained_at  TIMESTAMPTZ,
    deployed_at      TIMESTAMPTZ,
    training_dataset_size INTEGER,                          -- number of samples used

    -- Config
    model_config     JSONB           NOT NULL DEFAULT '{}', -- hyperparameters
    input_schema     JSONB           NOT NULL DEFAULT '{}', -- expected input fields
    output_schema    JSONB           NOT NULL DEFAULT '{}', -- output field definitions

    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ── AI Analysis Runs ─────────────────────────────────────────
-- Each row = one inference call to a model
CREATE TABLE ai_analyses (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id            UUID            NOT NULL REFERENCES ai_models(id)  ON DELETE CASCADE,
    horse_id            UUID            REFERENCES horses(id)              ON DELETE SET NULL,
    stable_id           UUID            REFERENCES stables(id)             ON DELETE SET NULL,
    analysis_type       analysis_type   NOT NULL,
    status              analysis_status NOT NULL DEFAULT 'pending',

    -- I/O
    input_data          JSONB           NOT NULL DEFAULT '{}',
    result              JSONB           NOT NULL DEFAULT '{}',
    confidence_score    DECIMAL(5,2),
    processing_ms       INTEGER,

    -- Trigger context
    triggered_by        VARCHAR(50)     NOT NULL DEFAULT 'system', -- 'system','manual','scheduled','alert'
    triggered_by_admin  UUID            REFERENCES admin_users(id) ON DELETE SET NULL,

    -- Linked sensor window (for context, not FK due to partitioning)
    sensor_window_start TIMESTAMPTZ,
    sensor_window_end   TIMESTAMPTZ,

    error_message       TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ── AI Training Jobs ─────────────────────────────────────────
CREATE TABLE ai_training_jobs (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id            UUID        NOT NULL REFERENCES ai_models(id) ON DELETE CASCADE,
    triggered_by        UUID        REFERENCES admin_users(id)        ON DELETE SET NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'queued', -- queued,running,completed,failed,cancelled
    reason              TEXT,                                  -- why retraining was initiated

    -- Dataset
    dataset_size        INTEGER,
    train_split_pct     DECIMAL(4,1) DEFAULT 80.0,
    val_split_pct       DECIMAL(4,1) DEFAULT 10.0,
    test_split_pct      DECIMAL(4,1) DEFAULT 10.0,

    -- Hyperparameters
    config              JSONB        NOT NULL DEFAULT '{}',

    -- Results
    final_accuracy      DECIMAL(5,2),
    final_val_loss      DECIMAL(8,6),
    total_epochs        INTEGER,
    best_epoch          INTEGER,

    -- Timing
    queued_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,

    error_message       TEXT,
    notes               TEXT
);

-- ── Per-epoch Training Metrics ───────────────────────────────
CREATE TABLE ai_training_epochs (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id              UUID        NOT NULL REFERENCES ai_training_jobs(id) ON DELETE CASCADE,
    epoch               INTEGER     NOT NULL,
    train_accuracy      DECIMAL(5,2),
    val_accuracy        DECIMAL(5,2),
    train_loss          DECIMAL(10,6),
    val_loss            DECIMAL(10,6),
    learning_rate       DECIMAL(12,10),
    duration_sec        DECIMAL(6,2),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (job_id, epoch)
);

-- ── Model Drift Monitoring ───────────────────────────────────
-- Tracks when live accuracy deviates from training accuracy
CREATE TABLE ai_model_drift_logs (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id            UUID        NOT NULL REFERENCES ai_models(id) ON DELETE CASCADE,
    measured_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sample_size         INTEGER,
    measured_accuracy   DECIMAL(5,2),
    baseline_accuracy   DECIMAL(5,2),
    drift_pct           DECIMAL(5,2),  -- positive = degraded
    is_significant      BOOLEAN     NOT NULL DEFAULT FALSE,
    alert_raised        BOOLEAN     NOT NULL DEFAULT FALSE
);

-- ── Triggers ─────────────────────────────────────────────────
CREATE TRIGGER trg_ai_models_updated
    BEFORE UPDATE ON ai_models
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- Increment total_requests on ai_models when analysis completes
CREATE TRIGGER trg_analysis_increment_requests
    AFTER INSERT OR UPDATE OF status ON ai_analyses
    FOR EACH ROW EXECUTE FUNCTION fn_increment_model_requests();
