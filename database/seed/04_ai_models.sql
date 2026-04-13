-- ============================================================
-- HCS — Equine Intelligence System
-- seed/04_ai_models.sql  |  AI model registry + recent analyses
-- ============================================================

-- ── AI Models ────────────────────────────────────────────────
INSERT INTO ai_models (id, name, slug, description, model_type, version, status, accuracy_score, precision_score, recall_score, f1_score, avg_response_ms, total_requests, requests_today, last_trained_at, deployed_at, training_dataset_size, model_config) VALUES

  ('m0000001-0000-0000-0000-000000000001',
   'Health Analyzer', 'health-analyzer',
   'Real-time vital monitoring and health score computation using biometric sensor data from the HCS Collar. Integrates heart rate, temperature, respiratory rate, SpO2, and motion context to produce a composite health score every 3 seconds.',
   'health', '3.2.1', 'active',
   97.4, 96.8, 97.9, 97.3, 800,
   284750, 847,
   NOW()-INTERVAL '3 days', NOW()-INTERVAL '3 days', 2840000,
   '{"architecture":"LightGBM+LSTM","seq_len":180,"feature_count":14,"threshold_critical":30,"threshold_warning":60}'
  ),

  ('m0000001-0000-0000-0000-000000000002',
   'Gait Analysis', 'gait-analysis',
   'Computer vision model detecting lameness, stride irregularities, and performance metrics from stable-mounted cameras. Uses skeleton keypoint estimation trained on 50,000+ equine movement sequences.',
   'gait', '2.4.0', 'active',
   95.1, 94.3, 95.8, 95.0, 1400,
   98420, 312,
   NOW()-INTERVAL '5 days', NOW()-INTERVAL '5 days', 820000,
   '{"architecture":"HRNet+GRU","input_fps":30,"keypoints":17,"lameness_threshold_grade":1}'
  ),

  ('m0000001-0000-0000-0000-000000000003',
   'Behavior Predictor', 'behavior-predictor',
   'LSTM-based behavioral pattern recognition for stress, mood, and social dynamics. Analyzes movement patterns, feeding behavior, social interactions, and environmental factors to predict behavioral outcomes.',
   'behavior', '1.8.2', 'active',
   91.8, 90.5, 92.9, 91.7, 1100,
   54180, 204,
   NOW()-INTERVAL '16 days', NOW()-INTERVAL '16 days', 430000,
   '{"architecture":"BiLSTM","seq_len":720,"hidden_units":256,"dropout":0.3}'
  ),

  ('m0000001-0000-0000-0000-000000000004',
   'Diet Optimizer', 'diet-optimizer',
   'Nutritional recommendation engine adapting to health metrics, workload intensity, breed profiles, and seasonal factors. Generates day-by-day feeding plans with supplement protocols.',
   'diet', '2.1.3', 'active',
   94.6, 93.8, 95.3, 94.5, 600,
   41320, 178,
   NOW()-INTERVAL '8 days', NOW()-INTERVAL '8 days', 310000,
   '{"architecture":"XGBoost","n_estimators":500,"feature_importance_threshold":0.01}'
  ),

  ('m0000001-0000-0000-0000-000000000005',
   'Disease Detector', 'disease-detector',
   'Early-warning pathology detection trained on 2M+ equine medical records globally. Detects over 140 equine conditions including colic precursors, respiratory infections, metabolic disorders, and musculoskeletal issues.',
   'disease', '4.0.1', 'active',
   98.2, 97.9, 98.5, 98.2, 1900,
   187560, 306,
   NOW()-INTERVAL '2 days', NOW()-INTERVAL '2 days', 2100000,
   '{"architecture":"Transformer","n_heads":8,"n_layers":6,"condition_classes":140,"alert_threshold":0.65}'
  ),

  ('m0000001-0000-0000-0000-000000000006',
   'Performance Tracker', 'performance-tracker',
   'Athletic performance modeling for race predictions, training load optimization, and recovery analytics. Predicts peak performance windows and injury risk based on longitudinal performance data.',
   'performance', '1.2.0', 'training',
   88.3, 87.1, 89.2, 88.1, NULL,
   0, 0,
   NULL, NULL, NULL,
   '{"architecture":"CNN+LSTM","input_window_days":90,"forecast_horizon_days":14}'
  );

-- ── Active training job for Performance Tracker ──────────────
INSERT INTO ai_training_jobs (model_id, triggered_by, status, reason, dataset_size, train_split_pct, val_split_pct, test_split_pct, config, queued_at, started_at, total_epochs, best_epoch, final_accuracy) VALUES
  ('m0000001-0000-0000-0000-000000000006',
   'a0000001-0000-0000-0000-000000000001',
   'running',
   'Initial production training run — v1.2.0. Incorporating 18 months of race telemetry from Gulf region.',
   185000, 80.0, 10.0, 10.0,
   '{"lr":0.001,"batch_size":128,"epochs":1000,"optimizer":"AdamW","scheduler":"cosine_annealing"}',
   NOW()-INTERVAL '2 days', NOW()-INTERVAL '2 days',
   847, 721, 88.3
  );

-- ── Sample epochs for the training job ───────────────────────
DO $$
DECLARE
  job_id UUID;
BEGIN
  SELECT id INTO job_id FROM ai_training_jobs WHERE model_id = 'm0000001-0000-0000-0000-000000000006' LIMIT 1;
  INSERT INTO ai_training_epochs (job_id, epoch, train_accuracy, val_accuracy, train_loss, val_loss, learning_rate, duration_sec)
  SELECT job_id,
         gs.epoch,
         LEAST(60 + (gs.epoch / 1000.0) * 35 + random() * 2, 99.9),
         LEAST(55 + (gs.epoch / 1000.0) * 34 + random() * 2, 99.5),
         GREATEST(0.8 - (gs.epoch / 1000.0) * 0.75 + random() * 0.01, 0.001),
         GREATEST(0.9 - (gs.epoch / 1000.0) * 0.72 + random() * 0.01, 0.005),
         0.001 * (0.5 ^ (gs.epoch / 200)),
         18.5 + random() * 4
  FROM   generate_series(1, 847, 5) AS gs(epoch);
END;
$$;

-- ── Recent AI analyses (last 24h sample) ─────────────────────
INSERT INTO ai_analyses (model_id, horse_id, analysis_type, status, confidence_score, processing_ms, triggered_by, result) VALUES
  -- Health analyses
  ('m0000001-0000-0000-0000-000000000001','h0000001-0000-0000-0000-000000000001','health','completed',97.2,  780,'system','{"health_score":96.2,"status":"excellent","flags":[]}'),
  ('m0000001-0000-0000-0000-000000000001','h0000001-0000-0000-0000-000000000008','health','completed',96.2,  810,'system','{"health_score":22.4,"status":"critical","flags":["fever","tachycardia","dehydration"]}'),
  ('m0000001-0000-0000-0000-000000000001','h0000001-0000-0000-0000-000000000007','health','completed',91.7,  830,'system','{"health_score":61.2,"status":"fair","flags":["weight_loss","reduced_gut_sounds"]}'),
  -- Disease detection
  ('m0000001-0000-0000-0000-000000000005','h0000001-0000-0000-0000-000000000008','disease','completed',96.2, 1920,'system','{"conditions":[{"name":"febrile_illness","probability":0.962},{"name":"viral_infection","probability":0.741}],"alert_raised":true}'),
  -- Gait analyses
  ('m0000001-0000-0000-0000-000000000002','h0000001-0000-0000-0000-000000000007','gait',  'completed',84.1, 1380,'system','{"symmetry_score":71.0,"lameness_detected":true,"lameness_grade":1,"affected_limbs":["LF"]}'),
  ('m0000001-0000-0000-0000-000000000002','h0000001-0000-0000-0000-000000000001','gait',  'completed',95.8, 1350,'system','{"symmetry_score":97.2,"lameness_detected":false}'),
  -- Diet
  ('m0000001-0000-0000-0000-000000000004','h0000001-0000-0000-0000-000000000007','diet',  'completed',88.3,  590,'system','{"daily_calories":18500,"protein_pct":12,"fat_pct":4,"fiber_pct":38,"recommendation":"increase_forage_reduce_concentrate"}'),
  -- Behavior
  ('m0000001-0000-0000-0000-000000000003','h0000001-0000-0000-0000-000000000008','behavior','completed',87.4, 1080,'system','{"stress_level":9,"appetite_score":2,"activity_level":"distressed","notable_behaviors":["box_walking","refusing_feed","pawing"]}');

-- ── System settings ───────────────────────────────────────────
INSERT INTO system_settings (key, value, value_type, description, is_public) VALUES
  ('system_name',                   'HCS — Equine Intelligence System', 'string',  'Platform display name',                             TRUE),
  ('api_version',                   'v3.4.1',                           'string',  'Current API version',                               TRUE),
  ('data_center_region',            'UAE-Dubai',                        'string',  'Primary data center location',                      FALSE),
  ('backup_interval_hours',         '6',                                'integer', 'Database backup frequency in hours',                FALSE),
  ('session_timeout_minutes',       '120',                              'integer', 'Admin session timeout',                             FALSE),
  ('alert_email_enabled',           'true',                             'boolean', 'Send email notifications for alerts',               FALSE),
  ('alert_sms_enabled',             'true',                             'boolean', 'Send SMS for critical alerts',                      FALSE),
  ('ai_drift_alert_enabled',        'true',                             'boolean', 'Alert when model accuracy drifts below threshold',  FALSE),
  ('ai_drift_threshold_pct',        '5',                                'integer', 'Accuracy drift % that triggers retraining alert',   FALSE),
  ('ai_auto_retrain_threshold_pct', '10',                               'integer', 'Accuracy drop % that triggers automatic retraining',FALSE),
  ('sensor_reading_interval_sec',   '3',                                'integer', 'HCS Collar polling interval in seconds',            FALSE),
  ('health_score_critical_threshold','30',                              'integer', 'Health score below this triggers critical alert',   FALSE),
  ('health_score_warning_threshold', '60',                              'integer', 'Health score below this triggers warning alert',    FALSE),
  ('2fa_required_super_admin',      'true',                             'boolean', 'Require 2FA for super admin logins',                FALSE),
  ('audit_log_retention_days',      '365',                              'integer', 'Days to retain activity logs',                      FALSE),
  ('max_failed_login_attempts',     '5',                                'integer', 'Lock account after N failed logins',                FALSE);
