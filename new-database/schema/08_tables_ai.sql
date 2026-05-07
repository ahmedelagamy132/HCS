-- ============================================================
-- HCS — Equine Intelligence System
-- 08_tables_ai.sql  |  AI models, analyses & training pipeline
-- ============================================================

-- ── AI Model Registry ────────────────────────────────────────
CREATE TABLE ai_models (
    id               UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    name             VARCHAR(100)    UNIQUE NOT NULL,
    slug             VARCHAR(100)    UNIQUE NOT NULL,
    description      TEXT,
    model_type       analysis_type   NOT NULL,
    version          VARCHAR(20)     NOT NULL DEFAULT '1.0.0',
    status           ai_model_status NOT NULL DEFAULT 'active',

    accuracy_score   DECIMAL(5,2)    CONSTRAINT chk_acc  CHECK (accuracy_score  BETWEEN 0 AND 100),
    precision_score  DECIMAL(5,2)    CONSTRAINT chk_prec CHECK (precision_score BETWEEN 0 AND 100),
    recall_score     DECIMAL(5,2)    CONSTRAINT chk_rec  CHECK (recall_score    BETWEEN 0 AND 100),
    f1_score         DECIMAL(5,2)    CONSTRAINT chk_f1   CHECK (f1_score        BETWEEN 0 AND 100),
    avg_response_ms  INTEGER,

    total_requests   BIGINT          NOT NULL DEFAULT 0,
    requests_today   INTEGER         NOT NULL DEFAULT 0,

    last_trained_at  TIMESTAMPTZ,
    deployed_at      TIMESTAMPTZ,
    training_dataset_size INTEGER,

    model_config     JSONB           NOT NULL DEFAULT '{}',
    input_schema     JSONB           NOT NULL DEFAULT '{}',
    output_schema    JSONB           NOT NULL DEFAULT '{}',

    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ── AI Analysis Runs ─────────────────────────────────────────
CREATE TABLE ai_analyses (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id            UUID            NOT NULL REFERENCES ai_models(id)  ON DELETE CASCADE,
    horse_id            UUID            REFERENCES horses(id)              ON DELETE SET NULL,
    stable_id           UUID            REFERENCES stables(id)             ON DELETE SET NULL,
    analysis_type       analysis_type   NOT NULL,
    status              analysis_status NOT NULL DEFAULT 'pending',

    input_data          JSONB           NOT NULL DEFAULT '{}',
    result              JSONB           NOT NULL DEFAULT '{}',
    confidence_score    DECIMAL(5,2),
    processing_ms       INTEGER,

    triggered_by        VARCHAR(50)     NOT NULL DEFAULT 'system',
    triggered_by_admin  UUID            REFERENCES admin_users(id) ON DELETE SET NULL,

    error_message       TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ── AI Training Jobs ─────────────────────────────────────────
CREATE TABLE ai_training_jobs (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id            UUID        NOT NULL REFERENCES ai_models(id) ON DELETE CASCADE,
    triggered_by        UUID        REFERENCES admin_users(id)        ON DELETE SET NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'queued',
    reason              TEXT,

    dataset_size        INTEGER,
    train_split_pct     DECIMAL(4,1) DEFAULT 80.0,
    val_split_pct       DECIMAL(4,1) DEFAULT 10.0,
    test_split_pct      DECIMAL(4,1) DEFAULT 10.0,

    config              JSONB        NOT NULL DEFAULT '{}',

    final_accuracy      DECIMAL(5,2),
    final_val_loss      DECIMAL(8,6),
    total_epochs        INTEGER,
    best_epoch          INTEGER,

    queued_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,

    error_message       TEXT,
    notes               TEXT
);

-- ── Triggers ─────────────────────────────────────────────────
CREATE TRIGGER trg_ai_models_updated
    BEFORE UPDATE ON ai_models
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TRIGGER trg_analysis_increment_requests
    AFTER INSERT OR UPDATE OF status ON ai_analyses
    FOR EACH ROW EXECUTE FUNCTION fn_increment_model_requests();
