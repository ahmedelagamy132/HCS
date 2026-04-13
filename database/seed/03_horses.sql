-- ============================================================
-- HCS — Equine Intelligence System
-- seed/03_horses.sql  |  Horse registry + health records
-- ============================================================

-- ── Horses ───────────────────────────────────────────────────
INSERT INTO horses (id, horse_code, name, breed, gender, date_of_birth, color, weight_kg, height_cm, owner_id, stable_id, primary_vet_id, health_status, is_racing) VALUES
  ('h0000001-0000-0000-0000-000000000001','HRS-001','Desert Storm',   'Arabian',      'stallion','2020-03-14',  'Bay',          520, 155, 'c0000001-0000-0000-0000-000000000001', 's0000001-0000-0000-0000-000000000001', 'vet00001-0000-0000-0000-000000000001', 'excellent', TRUE),
  ('h0000001-0000-0000-0000-000000000002','HRS-002','Golden Wind',    'Arabian',      'mare',    '2022-05-02',  'Chestnut',     480, 150, 'c0000001-0000-0000-0000-000000000001', 's0000001-0000-0000-0000-000000000001', 'vet00001-0000-0000-0000-000000000001', 'excellent', FALSE),
  ('h0000001-0000-0000-0000-000000000003','HRS-003','Midnight Sun',   'Thoroughbred', 'gelding', '2018-07-22',  'Dark Bay',     540, 162, 'c0000001-0000-0000-0000-000000000002', 's0000001-0000-0000-0000-000000000002', 'vet00001-0000-0000-0000-000000000002', 'good',      TRUE),
  ('h0000001-0000-0000-0000-000000000004','HRS-004','Royal Thunder',  'Warmblood',    'stallion','2021-01-11',  'Grey',         610, 168, 'c0000001-0000-0000-0000-000000000004', 's0000001-0000-0000-0000-000000000003', 'vet00001-0000-0000-0000-000000000001', 'excellent', TRUE),
  ('h0000001-0000-0000-0000-000000000005','HRS-005','Sahara Prince',  'Arabian',      'stallion','2019-09-30',  'Grey',         505, 153, 'c0000001-0000-0000-0000-000000000007', 's0000001-0000-0000-0000-000000000008', 'vet00001-0000-0000-0000-000000000003', 'good',      TRUE),
  ('h0000001-0000-0000-0000-000000000006','HRS-006','Falcon Blaze',   'Quarter Horse','colt',    '2023-02-18',  'Sorrel',       410, 143, 'c0000001-0000-0000-0000-000000000005', 's0000001-0000-0000-0000-000000000006', 'vet00001-0000-0000-0000-000000000001', 'excellent', FALSE),
  ('h0000001-0000-0000-0000-000000000007','HRS-007','Silver Crescent', 'Arabian',     'mare',    '2016-06-07',  'Grey',         490, 151, 'c0000001-0000-0000-0000-000000000009', 's0000001-0000-0000-0000-000000000010', 'vet00001-0000-0000-0000-000000000004', 'fair',      FALSE),
  ('h0000001-0000-0000-0000-000000000008','HRS-008','Black Oasis',    'Thoroughbred', 'gelding', '2020-11-03',  'Black',        558, 160, 'c0000001-0000-0000-0000-000000000002', 's0000001-0000-0000-0000-000000000002', 'vet00001-0000-0000-0000-000000000002', 'critical',  TRUE),
  ('h0000001-0000-0000-0000-000000000009','HRS-009','Al Wathba Star', 'Arabian',      'filly',   '2022-04-20',  'Bay',          440, 147, 'c0000001-0000-0000-0000-000000000004', 's0000001-0000-0000-0000-000000000004', 'vet00001-0000-0000-0000-000000000002', 'excellent', FALSE),
  ('h0000001-0000-0000-0000-000000000010','HRS-010','Desert Eagle',   'Arabian',      'stallion','2017-08-15',  'Bay',          515, 154, 'c0000001-0000-0000-0000-000000000007', 's0000001-0000-0000-0000-000000000009', 'vet00001-0000-0000-0000-000000000003', 'good',      TRUE),
  ('h0000001-0000-0000-0000-000000000011','HRS-011','Thunder Peak',   'Warmblood',    'gelding', '2021-03-25',  'Brown',        600, 167, 'c0000001-0000-0000-0000-000000000008', 's0000001-0000-0000-0000-000000000008', 'vet00001-0000-0000-0000-000000000003', 'fair',      FALSE),
  ('h0000001-0000-0000-0000-000000000012','HRS-012','Reem Al Bawadi', 'Arabian',      'filly',   '2023-01-09',  'Chestnut',     420, 145, 'c0000001-0000-0000-0000-000000000001', 's0000001-0000-0000-0000-000000000001', 'vet00001-0000-0000-0000-000000000001', 'excellent', FALSE);

-- ── Stable assignment history ─────────────────────────────────
INSERT INTO stable_assignments (horse_id, stable_id, assigned_at, removed_at, reason, assigned_by) VALUES
  ('h0000001-0000-0000-0000-000000000001','s0000001-0000-0000-0000-000000000001', NOW() - INTERVAL '3 years', NULL, 'Initial registration', 'a0000001-0000-0000-0000-000000000001'),
  ('h0000001-0000-0000-0000-000000000008','s0000001-0000-0000-0000-000000000003', NOW() - INTERVAL '18 months', NOW() - INTERVAL '6 months', 'Owner transfer', 'a0000001-0000-0000-0000-000000000001'),
  ('h0000001-0000-0000-0000-000000000008','s0000001-0000-0000-0000-000000000002', NOW() - INTERVAL '6 months', NULL, 'Moved to owner primary stable', 'a0000001-0000-0000-0000-000000000001');

-- ── Latest health records ─────────────────────────────────────
INSERT INTO horse_health_records (horse_id, recorded_at, record_type, heart_rate_bpm, temperature_celsius, respiratory_rate, weight_kg, health_score, status, vet_id, body_condition_score) VALUES
  ('h0000001-0000-0000-0000-000000000001', NOW() - INTERVAL '1 day',    'routine',       40, 37.8, 14, 520, 96.2, 'excellent', 'vet00001-0000-0000-0000-000000000001', 5.5),
  ('h0000001-0000-0000-0000-000000000002', NOW() - INTERVAL '2 days',   'routine',       38, 37.6, 13, 480, 94.8, 'excellent', 'vet00001-0000-0000-0000-000000000001', 5.0),
  ('h0000001-0000-0000-0000-000000000003', NOW() - INTERVAL '3 days',   'routine',       42, 37.9, 15, 540, 82.1, 'good',      'vet00001-0000-0000-0000-000000000002', 5.0),
  ('h0000001-0000-0000-0000-000000000004', NOW() - INTERVAL '1 day',    'routine',       36, 37.7, 12, 610, 97.5, 'excellent', 'vet00001-0000-0000-0000-000000000001', 6.0),
  ('h0000001-0000-0000-0000-000000000005', NOW() - INTERVAL '4 days',   'routine',       44, 38.0, 16, 505, 80.3, 'good',      'vet00001-0000-0000-0000-000000000003', 5.0),
  ('h0000001-0000-0000-0000-000000000006', NOW() - INTERVAL '1 day',    'routine',       36, 37.5, 12, 410, 98.0, 'excellent', 'vet00001-0000-0000-0000-000000000001', 5.5),
  ('h0000001-0000-0000-0000-000000000007', NOW() - INTERVAL '5 days',   'routine',       48, 38.4, 18, 490, 61.2, 'fair',      'vet00001-0000-0000-0000-000000000004', 4.0),
  ('h0000001-0000-0000-0000-000000000008', NOW() - INTERVAL '2 hours',  'ai_analysis',   68, 39.8, 28, 558, 22.4, 'critical',  'vet00001-0000-0000-0000-000000000002', 3.5),
  ('h0000001-0000-0000-0000-000000000009', NOW() - INTERVAL '2 days',   'routine',       37, 37.6, 13, 440, 95.1, 'excellent', 'vet00001-0000-0000-0000-000000000002', 5.5),
  ('h0000001-0000-0000-0000-000000000010', NOW() - INTERVAL '3 days',   'routine',       41, 37.9, 15, 515, 81.7, 'good',      'vet00001-0000-0000-0000-000000000003', 5.0),
  ('h0000001-0000-0000-0000-000000000011', NOW() - INTERVAL '6 days',   'routine',       46, 38.2, 17, 600, 63.5, 'fair',      'vet00001-0000-0000-0000-000000000003', 4.5),
  ('h0000001-0000-0000-0000-000000000012', NOW() - INTERVAL '1 day',    'routine',       35, 37.5, 12, 420, 97.2, 'excellent', 'vet00001-0000-0000-0000-000000000001', 5.5);

-- ── Health Alerts ─────────────────────────────────────────────
INSERT INTO health_alerts (horse_id, stable_id, severity, title, description, status, detected_by, confidence_score, created_at) VALUES
  ('h0000001-0000-0000-0000-000000000008','s0000001-0000-0000-0000-000000000002','critical',
   'Critical: Fever + Elevated Heart Rate — Black Oasis',
   'Temperature 39.8°C (threshold: 38.5°C) combined with heart rate 68 BPM (resting threshold: 48 BPM). Disease Detector confidence 96.2%. Vet notification dispatched.',
   'active','ai_model', 96.2, NOW() - INTERVAL '2 hours'),

  ('h0000001-0000-0000-0000-000000000007','s0000001-0000-0000-0000-000000000010','critical',
   'Critical: Significant Weight Loss — Silver Crescent',
   'Weight declined 8.2% over 14 days (490kg → 449kg). Combined with reduced gut sounds. Immediate dietary and GI review required.',
   'active','ai_model', 91.7, NOW() - INTERVAL '18 hours'),

  (NULL,'s0000001-0000-0000-0000-000000000002','warning',
   'Desert Rose Stables at Full Capacity',
   'Stable has reached maximum capacity (30/30). New intake requests are being queued. Consider expanding or redirecting.',
   'active','system', NULL, NOW() - INTERVAL '3 days'),

  ('h0000001-0000-0000-0000-000000000007',NULL,'warning',
   'Gait Irregularity Detected — Silver Crescent',
   'Gait symmetry score dropped to 71/100 over past 7 days. Possible early-stage left fore lameness. Grade 1 on AAEP scale.',
   'acknowledged','ai_model', 84.1, NOW() - INTERVAL '5 days'),

  ('h0000001-0000-0000-0000-000000000011',NULL,'warning',
   'Diet Compliance Alert — Thunder Peak',
   'AI Diet Optimizer flagged 3 consecutive days of feed refusal (>40%). Weight trending down. Plan review recommended.',
   'active','ai_model', 88.3, NOW() - INTERVAL '2 days');

-- ── Medical Records ───────────────────────────────────────────
INSERT INTO medical_records (horse_id, vet_id, recorded_at, record_type, description, medication, dosage, next_due_date) VALUES
  ('h0000001-0000-0000-0000-000000000001','vet00001-0000-0000-0000-000000000001', NOW()-INTERVAL '30 days', 'vaccination',  'Annual influenza + tetanus booster',                  'Equip + ProteqFlu', '2ml IM',  (CURRENT_DATE + INTERVAL '335 days')::DATE),
  ('h0000001-0000-0000-0000-000000000001','vet00001-0000-0000-0000-000000000001', NOW()-INTERVAL '45 days', 'deworming',    'Ivermectin deworming cycle',                          'Eqvalan',           '6ml oral', (CURRENT_DATE + INTERVAL '40 days')::DATE),
  ('h0000001-0000-0000-0000-000000000008','vet00001-0000-0000-0000-000000000002', NOW()-INTERVAL '3 days',  'emergency',    'Presenting with high fever and tachycardia. IV fluids administered. Awaiting blood panel.', 'Phenylbutazone + IV Fluids', '4.4mg/kg', NULL),
  ('h0000001-0000-0000-0000-000000000007','vet00001-0000-0000-0000-000000000004', NOW()-INTERVAL '7 days',  'medication',   'Prescribed omeprazole for suspected gastric ulcers',  'GastroGard',        '4mg/kg oral daily', (CURRENT_DATE + INTERVAL '21 days')::DATE),
  ('h0000001-0000-0000-0000-000000000004','vet00001-0000-0000-0000-000000000001', NOW()-INTERVAL '60 days', 'dental',       'Routine dental float, hooks removed, wolf teeth extracted', NULL,             NULL,       (CURRENT_DATE + INTERVAL '305 days')::DATE);
