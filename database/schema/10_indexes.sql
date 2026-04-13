-- ============================================================
-- HCS — Equine Intelligence System
-- 10_indexes.sql  |  All performance indexes
-- ============================================================

-- ── AUTH ─────────────────────────────────────────────────────
CREATE INDEX idx_admin_users_email        ON admin_users(email);
CREATE INDEX idx_admin_users_role         ON admin_users(role);
CREATE INDEX idx_admin_users_active       ON admin_users(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_admin_sessions_admin     ON admin_sessions(admin_id);
CREATE INDEX idx_admin_sessions_token     ON admin_sessions(token_hash);
CREATE INDEX idx_admin_sessions_valid     ON admin_sessions(is_valid, expires_at) WHERE is_valid = TRUE;
CREATE INDEX idx_admin_perms_admin        ON admin_permissions(admin_id);
CREATE INDEX idx_api_keys_hash            ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active          ON api_keys(is_active) WHERE is_active = TRUE;

-- ── CLIENTS ──────────────────────────────────────────────────
CREATE INDEX idx_clients_status           ON clients(status);
CREATE INDEX idx_clients_region           ON clients(region);
CREATE INDEX idx_clients_country          ON clients(country);
CREATE INDEX idx_clients_created          ON clients(created_at DESC);
-- Full-text search on client name
CREATE INDEX idx_clients_name_fts         ON clients USING gin(to_tsvector('english', full_name));

-- ── STABLES ──────────────────────────────────────────────────
CREATE INDEX idx_stables_owner            ON stables(owner_id);
CREATE INDEX idx_stables_status           ON stables(status);
CREATE INDEX idx_stables_city             ON stables(city);
CREATE INDEX idx_stables_country          ON stables(country);
-- Geo index for proximity queries
CREATE INDEX idx_stables_geo              ON stables USING gist(point(longitude, latitude))
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- ── HORSES ───────────────────────────────────────────────────
CREATE INDEX idx_horses_owner             ON horses(owner_id);
CREATE INDEX idx_horses_stable            ON horses(stable_id);
CREATE INDEX idx_horses_health_status     ON horses(health_status);
CREATE INDEX idx_horses_breed             ON horses(breed);
CREATE INDEX idx_horses_active            ON horses(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_horses_critical          ON horses(health_status) WHERE health_status IN ('critical','poor');
CREATE INDEX idx_horses_name_fts          ON horses USING gin(to_tsvector('english', name));

-- ── STABLE ASSIGNMENTS ───────────────────────────────────────
CREATE INDEX idx_assignments_horse        ON stable_assignments(horse_id);
CREATE INDEX idx_assignments_stable       ON stable_assignments(stable_id);
CREATE INDEX idx_assignments_current      ON stable_assignments(horse_id) WHERE removed_at IS NULL;

-- ── SUBSCRIPTIONS ────────────────────────────────────────────
CREATE INDEX idx_subs_client              ON subscriptions(client_id);
CREATE INDEX idx_subs_status              ON subscriptions(status);
CREATE INDEX idx_subs_billing             ON subscriptions(next_billing_date) WHERE status = 'active';

-- ── DEVICES ──────────────────────────────────────────────────
CREATE INDEX idx_devices_stable           ON devices(stable_id);
CREATE INDEX idx_devices_horse            ON devices(horse_id);
CREATE INDEX idx_devices_type             ON devices(device_type);
CREATE INDEX idx_devices_status           ON devices(status);
CREATE INDEX idx_devices_active           ON devices(status) WHERE status = 'active';

-- ── SENSOR READINGS (on partitions) ─────────────────────────
-- These must be created on each partition; we create a template for automation
-- and also on the parent (PostgreSQL propagates to new partitions).
CREATE INDEX idx_sensor_horse             ON sensor_readings(horse_id, recorded_at DESC);
CREATE INDEX idx_sensor_device            ON sensor_readings(device_id, recorded_at DESC);
CREATE INDEX idx_sensor_anomaly           ON sensor_readings(recorded_at DESC) WHERE is_anomaly = TRUE;

-- ── CV EVENTS ────────────────────────────────────────────────
CREATE INDEX idx_cv_stable                ON cv_events(stable_id, detected_at DESC);
CREATE INDEX idx_cv_horse                 ON cv_events(horse_id, detected_at DESC);
CREATE INDEX idx_cv_type                  ON cv_events(event_type);
CREATE INDEX idx_cv_unreviewed            ON cv_events(detected_at DESC) WHERE is_reviewed = FALSE;

-- ── HEALTH RECORDS ───────────────────────────────────────────
CREATE INDEX idx_health_rec_horse         ON horse_health_records(horse_id, recorded_at DESC);
CREATE INDEX idx_health_rec_type          ON horse_health_records(record_type);
CREATE INDEX idx_health_rec_status        ON horse_health_records(status);

-- ── HEALTH ALERTS ────────────────────────────────────────────
CREATE INDEX idx_alerts_horse             ON health_alerts(horse_id);
CREATE INDEX idx_alerts_stable            ON health_alerts(stable_id);
CREATE INDEX idx_alerts_severity          ON health_alerts(severity);
CREATE INDEX idx_alerts_status            ON health_alerts(status);
CREATE INDEX idx_alerts_active            ON health_alerts(created_at DESC) WHERE status = 'active';
CREATE INDEX idx_alerts_critical_active   ON health_alerts(created_at DESC)
    WHERE status = 'active' AND severity = 'critical';

-- ── GAIT ANALYSES ────────────────────────────────────────────
CREATE INDEX idx_gait_horse               ON gait_analyses(horse_id, analyzed_at DESC);
CREATE INDEX idx_gait_lameness            ON gait_analyses(horse_id) WHERE lameness_detected = TRUE;

-- ── DIET PLANS ───────────────────────────────────────────────
CREATE INDEX idx_diet_horse               ON diet_plans(horse_id);
CREATE INDEX idx_diet_active              ON diet_plans(horse_id) WHERE status = 'active';

-- ── BEHAVIOR RECORDS ─────────────────────────────────────────
CREATE INDEX idx_behavior_horse           ON behavior_records(horse_id, observed_at DESC);

-- ── PERFORMANCE RECORDS ──────────────────────────────────────
CREATE INDEX idx_perf_horse               ON performance_records(horse_id, event_date DESC);
CREATE INDEX idx_perf_event_type          ON performance_records(event_type);

-- ── MEDICAL RECORDS ──────────────────────────────────────────
CREATE INDEX idx_medical_horse            ON medical_records(horse_id, recorded_at DESC);
CREATE INDEX idx_medical_type             ON medical_records(record_type);
CREATE INDEX idx_medical_due              ON medical_records(next_due_date) WHERE next_due_date IS NOT NULL;

-- ── AI MODELS ────────────────────────────────────────────────
CREATE INDEX idx_ai_models_status         ON ai_models(status);
CREATE INDEX idx_ai_models_type           ON ai_models(model_type);

-- ── AI ANALYSES ──────────────────────────────────────────────
CREATE INDEX idx_analyses_model           ON ai_analyses(model_id, created_at DESC);
CREATE INDEX idx_analyses_horse           ON ai_analyses(horse_id, created_at DESC);
CREATE INDEX idx_analyses_type            ON ai_analyses(analysis_type);
CREATE INDEX idx_analyses_status          ON ai_analyses(status);
CREATE INDEX idx_analyses_today           ON ai_analyses(created_at DESC)
    WHERE created_at >= CURRENT_DATE;
-- GIN index for querying result JSONB
CREATE INDEX idx_analyses_result_gin      ON ai_analyses USING gin(result);

-- ── TRAINING JOBS ────────────────────────────────────────────
CREATE INDEX idx_train_jobs_model         ON ai_training_jobs(model_id, queued_at DESC);
CREATE INDEX idx_train_jobs_status        ON ai_training_jobs(status);

-- ── DRIFT LOGS ───────────────────────────────────────────────
CREATE INDEX idx_drift_model              ON ai_model_drift_logs(model_id, measured_at DESC);
CREATE INDEX idx_drift_significant        ON ai_model_drift_logs(model_id) WHERE is_significant = TRUE;

-- ── ACTIVITY LOGS ────────────────────────────────────────────
CREATE INDEX idx_logs_actor               ON activity_logs(actor_type, actor_id, created_at DESC);
CREATE INDEX idx_logs_entity              ON activity_logs(entity_type, entity_id);
CREATE INDEX idx_logs_action              ON activity_logs(action);
CREATE INDEX idx_logs_recent              ON activity_logs(created_at DESC);

-- ── NOTIFICATIONS ────────────────────────────────────────────
CREATE INDEX idx_notifs_recipient         ON notifications(recipient_type, recipient_id, created_at DESC);
CREATE INDEX idx_notifs_unread            ON notifications(recipient_type, recipient_id)
    WHERE is_read = FALSE;

-- ── NOTIFICATION QUEUE ───────────────────────────────────────
CREATE INDEX idx_nq_pending               ON notification_queue(priority, created_at) WHERE status = 'pending';
CREATE INDEX idx_nq_status                ON notification_queue(status);

-- ── REPORTS ──────────────────────────────────────────────────
CREATE INDEX idx_reports_type             ON reports(report_type);
CREATE INDEX idx_reports_generated_by     ON reports(generated_by);
CREATE INDEX idx_reports_status           ON reports(status);
