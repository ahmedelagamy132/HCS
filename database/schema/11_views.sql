-- ============================================================
-- HCS — Equine Intelligence System
-- 11_views.sql  |  Useful views for the dashboard & API
-- ============================================================

-- ── v_system_kpis — single row of headline numbers ──────────
CREATE OR REPLACE VIEW v_system_kpis AS
SELECT
    (SELECT COUNT(*)                    FROM clients       WHERE status = 'active')                       AS active_clients,
    (SELECT COUNT(*)                    FROM clients       WHERE status = 'pending')                      AS pending_clients,
    (SELECT COUNT(*)                    FROM stables       WHERE status NOT IN ('inactive'))               AS active_stables,
    (SELECT COUNT(*)                    FROM stables       WHERE status = 'full')                         AS full_stables,
    (SELECT COUNT(*)                    FROM stables       WHERE status = 'maintenance')                  AS maintenance_stables,
    (SELECT COUNT(*)                    FROM horses        WHERE is_active = TRUE)                        AS total_horses,
    (SELECT COUNT(*)                    FROM horses        WHERE health_status IN ('excellent','good') AND is_active = TRUE) AS healthy_horses,
    (SELECT COUNT(*)                    FROM horses        WHERE health_status = 'fair'     AND is_active = TRUE) AS fair_horses,
    (SELECT COUNT(*)                    FROM horses        WHERE health_status IN ('poor','critical') AND is_active = TRUE) AS critical_horses,
    (SELECT COUNT(*)                    FROM health_alerts WHERE status = 'active')                       AS active_alerts,
    (SELECT COUNT(*)                    FROM health_alerts WHERE status = 'active' AND severity = 'critical') AS critical_alerts,
    (SELECT COUNT(*)                    FROM ai_analyses   WHERE created_at >= CURRENT_DATE)              AS analyses_today,
    (SELECT COUNT(*)                    FROM devices       WHERE status = 'active')                       AS active_devices,
    (SELECT COUNT(*)                    FROM admin_users   WHERE is_active = TRUE)                        AS active_admins,
    (SELECT ROUND(AVG(accuracy_score),2) FROM ai_models   WHERE status = 'active')                       AS avg_model_accuracy,
    NOW()                                                                                                 AS computed_at;

-- ── v_stable_occupancy — live occupancy per stable ──────────
CREATE OR REPLACE VIEW v_stable_occupancy AS
SELECT
    s.id,
    s.stable_code,
    s.name,
    s.city,
    s.region,
    s.capacity,
    s.occupied,
    s.capacity - s.occupied                                          AS available_slots,
    CASE WHEN s.capacity > 0
         THEN ROUND(s.occupied::NUMERIC / s.capacity * 100, 1)
         ELSE 0
    END                                                              AS occupancy_pct,
    s.status,
    c.full_name                                                      AS owner_name,
    c.id                                                             AS owner_id,
    (SELECT COUNT(*) FROM devices d WHERE d.stable_id = s.id AND d.status = 'active')  AS active_devices,
    (SELECT COUNT(*) FROM health_alerts a
     WHERE a.stable_id = s.id AND a.status = 'active' AND a.severity = 'critical')     AS critical_alerts
FROM stables s
LEFT JOIN clients c ON c.id = s.owner_id;

-- ── v_horse_summary — enriched horse list for the dashboard ──
CREATE OR REPLACE VIEW v_horse_summary AS
SELECT
    h.id,
    h.horse_code,
    h.name,
    h.breed,
    h.gender,
    EXTRACT(YEAR FROM AGE(h.date_of_birth))::INTEGER                AS age_years,
    h.health_status,
    h.is_active,
    h.is_racing,
    -- owner
    c.id                                                            AS owner_id,
    c.full_name                                                     AS owner_name,
    c.client_code                                                   AS owner_code,
    -- stable
    s.id                                                            AS stable_id,
    s.name                                                          AS stable_name,
    s.stable_code,
    s.city                                                          AS stable_city,
    -- latest health record
    hr.recorded_at                                                  AS last_check_at,
    hr.health_score                                                 AS last_health_score,
    hr.heart_rate_bpm                                               AS last_heart_rate,
    hr.temperature_celsius                                          AS last_temperature,
    -- active alert count
    (SELECT COUNT(*) FROM health_alerts a
     WHERE a.horse_id = h.id AND a.status = 'active')              AS active_alerts,
    -- active diet plan
    (SELECT id FROM diet_plans dp
     WHERE dp.horse_id = h.id AND dp.status = 'active'
     ORDER BY dp.created_at DESC LIMIT 1)                          AS active_diet_plan_id,
    -- collar device
    (SELECT device_code FROM devices d
     WHERE d.horse_id = h.id AND d.device_type = 'collar' AND d.status = 'active'
     LIMIT 1)                                                       AS collar_code,
    h.created_at
FROM horses h
LEFT JOIN clients        c  ON c.id  = h.owner_id
LEFT JOIN stables        s  ON s.id  = h.stable_id
LEFT JOIN LATERAL (
    SELECT recorded_at, health_score, heart_rate_bpm, temperature_celsius
    FROM   horse_health_records
    WHERE  horse_id = h.id
    ORDER  BY recorded_at DESC
    LIMIT  1
) hr ON TRUE;

-- ── v_client_summary — client portal overview ───────────────
CREATE OR REPLACE VIEW v_client_summary AS
SELECT
    c.id,
    c.client_code,
    c.full_name,
    c.email,
    c.phone,
    c.region,
    c.country,
    c.status,
    c.stable_count,
    c.horse_count,
    -- subscription
    sub.plan                                                        AS subscription_plan,
    sub.status                                                      AS subscription_status,
    sub.end_date                                                    AS subscription_end,
    -- health snapshot
    (SELECT COUNT(*) FROM horses h
     WHERE h.owner_id = c.id AND h.health_status IN ('critical','poor') AND h.is_active = TRUE) AS horses_critical,
    (SELECT COUNT(*) FROM health_alerts ha
     JOIN horses h ON h.id = ha.horse_id
     WHERE h.owner_id = c.id AND ha.status = 'active' AND ha.severity = 'critical')            AS critical_alerts,
    c.created_at
FROM clients c
LEFT JOIN LATERAL (
    SELECT plan, status, end_date
    FROM   subscriptions
    WHERE  client_id = c.id
    ORDER  BY created_at DESC
    LIMIT  1
) sub ON TRUE;

-- ── v_ai_model_performance — model health dashboard ──────────
CREATE OR REPLACE VIEW v_ai_model_performance AS
SELECT
    m.id,
    m.name,
    m.slug,
    m.model_type,
    m.version,
    m.status,
    m.accuracy_score,
    m.f1_score,
    m.avg_response_ms,
    m.total_requests,
    m.requests_today,
    m.last_trained_at,
    m.deployed_at,
    -- today's analysis count
    (SELECT COUNT(*) FROM ai_analyses a
     WHERE a.model_id = m.id AND a.created_at >= CURRENT_DATE AND a.status = 'completed') AS analyses_today,
    -- average confidence today
    (SELECT ROUND(AVG(a.confidence_score),2) FROM ai_analyses a
     WHERE a.model_id = m.id AND a.created_at >= CURRENT_DATE AND a.status = 'completed') AS avg_confidence_today,
    -- active training job
    (SELECT status FROM ai_training_jobs j
     WHERE j.model_id = m.id AND j.status IN ('queued','running')
     ORDER BY j.queued_at DESC LIMIT 1)                            AS training_status,
    -- latest drift measurement
    dl.drift_pct                                                   AS latest_drift_pct,
    dl.is_significant                                              AS drift_significant
FROM ai_models m
LEFT JOIN LATERAL (
    SELECT drift_pct, is_significant
    FROM   ai_model_drift_logs
    WHERE  model_id = m.id
    ORDER  BY measured_at DESC
    LIMIT  1
) dl ON TRUE;

-- ── v_recent_activity — last 50 activity log entries ─────────
CREATE OR REPLACE VIEW v_recent_activity AS
SELECT
    al.id,
    al.actor_type,
    al.actor_label,
    al.action,
    al.entity_type,
    al.entity_label,
    al.description,
    al.created_at
FROM activity_logs al
ORDER BY al.created_at DESC
LIMIT 50;

-- ── v_active_alerts_full — enriched alert feed ───────────────
CREATE OR REPLACE VIEW v_active_alerts_full AS
SELECT
    ha.id,
    ha.severity,
    ha.title,
    ha.description,
    ha.status,
    ha.detected_by,
    ha.confidence_score,
    ha.created_at,
    -- horse
    h.name                  AS horse_name,
    h.horse_code,
    h.breed                 AS horse_breed,
    -- stable
    s.name                  AS stable_name,
    s.stable_code,
    s.city                  AS stable_city,
    -- owner
    c.full_name             AS owner_name,
    c.email                 AS owner_email,
    -- AI model
    m.name                  AS model_name
FROM health_alerts ha
LEFT JOIN horses    h ON h.id = ha.horse_id
LEFT JOIN stables   s ON s.id = COALESCE(ha.stable_id, h.stable_id)
LEFT JOIN clients   c ON c.id = h.owner_id
LEFT JOIN ai_models m ON m.id = ha.ai_model_id
WHERE ha.status = 'active'
ORDER BY
    CASE ha.severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END,
    ha.created_at DESC;

-- ── v_device_health — IoT fleet status ───────────────────────
CREATE OR REPLACE VIEW v_device_health AS
SELECT
    d.id,
    d.device_code,
    d.device_type,
    d.status,
    d.battery_pct,
    d.last_seen_at,
    EXTRACT(EPOCH FROM (NOW() - d.last_seen_at)) / 60  AS minutes_since_seen,
    d.signal_strength,
    d.firmware_version,
    s.name      AS stable_name,
    s.stable_code,
    h.name      AS horse_name,
    h.horse_code
FROM devices d
LEFT JOIN stables s ON s.id = d.stable_id
LEFT JOIN horses  h ON h.id = d.horse_id;
