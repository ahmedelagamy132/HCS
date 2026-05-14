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

-- ── CLIENTS ──────────────────────────────────────────────────
CREATE INDEX idx_clients_status           ON clients(status);
CREATE INDEX idx_clients_region           ON clients(region);
CREATE INDEX idx_clients_country          ON clients(country);
CREATE INDEX idx_clients_created          ON clients(created_at DESC);
CREATE INDEX idx_clients_name_fts         ON clients USING gin(to_tsvector('english', full_name));

-- ── STABLES ──────────────────────────────────────────────────
CREATE INDEX idx_stables_owner            ON stables(owner_id);
CREATE INDEX idx_stables_status           ON stables(status);
CREATE INDEX idx_stables_city             ON stables(city);
CREATE INDEX idx_stables_country          ON stables(country);
CREATE INDEX idx_stables_geo              ON stables USING gist(point(longitude, latitude))
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- ── HORSES ───────────────────────────────────────────────────
CREATE INDEX idx_horses_owner             ON horses(owner_id);
CREATE INDEX idx_horses_stable            ON horses(stable_id);
CREATE INDEX idx_horses_health_status     ON horses(health_status);
CREATE INDEX idx_horses_breed             ON horses(breed);
CREATE INDEX idx_horses_active            ON horses(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_horses_name_fts          ON horses USING gin(to_tsvector('english', name));

-- ── STABLE ASSIGNMENTS ───────────────────────────────────────
CREATE INDEX idx_assignments_horse        ON stable_assignments(horse_id);
CREATE INDEX idx_assignments_stable       ON stable_assignments(stable_id);
CREATE INDEX idx_assignments_current      ON stable_assignments(horse_id) WHERE removed_at IS NULL;

-- ── SUBSCRIPTIONS ────────────────────────────────────────────
CREATE INDEX idx_subs_client              ON subscriptions(client_id);
CREATE INDEX idx_subs_status              ON subscriptions(status);
CREATE INDEX idx_subs_billing             ON subscriptions(next_billing_date) WHERE status = 'active';

-- ── AI MODELS ────────────────────────────────────────────────
CREATE INDEX idx_ai_models_status         ON ai_models(status);
CREATE INDEX idx_ai_models_type           ON ai_models(model_type);

-- ── AI ANALYSES ──────────────────────────────────────────────
CREATE INDEX idx_analyses_model           ON ai_analyses(model_id, created_at DESC);
CREATE INDEX idx_analyses_horse           ON ai_analyses(horse_id, created_at DESC);
CREATE INDEX idx_analyses_type            ON ai_analyses(analysis_type);
CREATE INDEX idx_analyses_status          ON ai_analyses(status);
CREATE INDEX idx_analyses_result_gin      ON ai_analyses USING gin(result);

-- ── TRAINING JOBS ────────────────────────────────────────────
CREATE INDEX idx_train_jobs_model         ON ai_training_jobs(model_id, queued_at DESC);
CREATE INDEX idx_train_jobs_status        ON ai_training_jobs(status);

-- ── ACTIVITY LOGS ────────────────────────────────────────────
CREATE INDEX idx_logs_actor               ON activity_logs(actor_type, actor_id, created_at DESC);
CREATE INDEX idx_logs_entity              ON activity_logs(entity_type, entity_id);
CREATE INDEX idx_logs_action              ON activity_logs(action);
CREATE INDEX idx_logs_recent              ON activity_logs(created_at DESC);

-- ── NOTIFICATIONS ────────────────────────────────────────────
CREATE INDEX idx_notifs_recipient         ON notifications(recipient_type, recipient_id, created_at DESC);
CREATE INDEX idx_notifs_unread            ON notifications(recipient_type, recipient_id)
    WHERE is_read = FALSE;
