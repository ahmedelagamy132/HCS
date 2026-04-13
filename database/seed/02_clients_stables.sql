-- ============================================================
-- HCS — Equine Intelligence System
-- seed/02_clients_stables.sql  |  Clients, vets & stables
-- ============================================================

-- ── Veterinarians ────────────────────────────────────────────
INSERT INTO veterinarians (id, full_name, license_number, specialty, email, phone, city, country) VALUES
  ('vet00001-0000-0000-0000-000000000001', 'Dr. Khalid Hassan Al-Breiki', 'UAE-EQ-0021', 'Equine Medicine',          'k.albreiki@equivet.ae',    '+971 50 811 2233', 'Dubai',     'UAE'),
  ('vet00001-0000-0000-0000-000000000002', 'Dr. Noura Al-Shamlan',        'UAE-EQ-0047', 'Equine Surgery',           'n.shamlan@equivet.ae',     '+971 55 922 3344', 'Abu Dhabi', 'UAE'),
  ('vet00001-0000-0000-0000-000000000003', 'Dr. Faris Al-Dabbagh',        'KSA-EQ-0115', 'Large Animal Internal Med','f.dabbagh@vetriyadh.sa',   '+966 55 111 2345', 'Riyadh',    'Saudi Arabia'),
  ('vet00001-0000-0000-0000-000000000004', 'Dr. Maryam Al-Kuwari',        'QAT-EQ-0009', 'Equine Sport Medicine',    'm.kuwari@qatarevet.qa',    '+974 55 234 5678', 'Doha',      'Qatar');

-- ── Clients ──────────────────────────────────────────────────
INSERT INTO clients (id, client_code, full_name, email, phone, region, country, city, status, stable_count, horse_count, created_at) VALUES
  ('c0000001-0000-0000-0000-000000000001','CLT-001','Khalid Al-Rashid',    'k.rashid@equinegulf.ae',    '+971 50 123 4567','Dubai',         'UAE',          'Dubai',         'active',   3, 12, NOW() - INTERVAL '37 months'),
  ('c0000001-0000-0000-0000-000000000002','CLT-002','Mohammed Al-Farsi',   'm.farsi@alfaris.ae',         '+971 55 234 5678','Abu Dhabi',     'UAE',          'Abu Dhabi',     'active',   2,  8, NOW() - INTERVAL '39 months'),
  ('c0000001-0000-0000-0000-000000000003','CLT-003','Sultan Al-Nuaimi',    'sultan@nuaimi-stables.com',  '+971 50 345 6789','Sharjah',       'UAE',          'Sharjah',       'active',   1,  5, NOW() - INTERVAL '34 months'),
  ('c0000001-0000-0000-0000-000000000004','CLT-004','Rashid Al-Maktoum',   'r.maktoum@horsecare.ae',     '+971 54 456 7890','Dubai',         'UAE',          'Dubai',         'active',   5, 28, NOW() - INTERVAL '41 months'),
  ('c0000001-0000-0000-0000-000000000005','CLT-005','Faisal Al-Qassimi',   'faisal@qassimi.ae',          '+971 56 567 8901','Ras Al Khaimah','UAE',          'Ras Al Khaimah','active',   2, 11, NOW() - INTERVAL '32 months'),
  ('c0000001-0000-0000-0000-000000000006','CLT-006','Hamdan Al-Mansouri',  'h.mansouri@equine.ae',       '+971 50 678 9012','Ajman',         'UAE',          'Ajman',         'inactive', 1,  4, NOW() - INTERVAL '38 months'),
  ('c0000001-0000-0000-0000-000000000007','CLT-007','Tariq Al-Zahrani',    'tariq@zahrani-stables.sa',   '+966 55 789 0123','Riyadh',        'Saudi Arabia', 'Riyadh',        'active',   4, 22, NOW() - INTERVAL '43 months'),
  ('c0000001-0000-0000-0000-000000000008','CLT-008','Abdullah Al-Otaibi',  'a.otaibi@horses.sa',         '+966 50 890 1234','Jeddah',        'Saudi Arabia', 'Jeddah',        'active',   2,  9, NOW() - INTERVAL '35 months'),
  ('c0000001-0000-0000-0000-000000000009','CLT-009','Nasser Al-Thani',     'n.thani@qataristables.qa',   '+974 33 901 2345','Doha',          'Qatar',        'Doha',          'active',   3, 15, NOW() - INTERVAL '40 months'),
  ('c0000001-0000-0000-0000-000000000010','CLT-010','Jasim Al-Buainain',   'jasim@buainain.bh',          '+973 36 012 3456','Manama',        'Bahrain',      'Manama',        'pending',  1,  6, NOW() - INTERVAL '33 months'),
  ('c0000001-0000-0000-0000-000000000011','CLT-011','Ali Al-Hosani',       'ali.hosani@equinecare.ae',   '+971 52 111 2222','Dubai',         'UAE',          'Dubai',         'active',   2, 10, NOW() - INTERVAL '31 months'),
  ('c0000001-0000-0000-0000-000000000012','CLT-012','Omar Al-Saffar',      'omar@saffar-stables.ae',     '+971 55 333 4444','Abu Dhabi',     'UAE',          'Abu Dhabi',     'inactive', 1,  3, NOW() - INTERVAL '36 months');

-- ── Subscriptions ────────────────────────────────────────────
INSERT INTO subscriptions (client_id, plan, status, start_date, end_date, monthly_rate, currency, max_stables, max_horses, ai_analyses_per_month) VALUES
  ('c0000001-0000-0000-0000-000000000001', 'enterprise',   'active',  '2023-03-01', NULL,         9800, 'AED', 99,  999, 99999),
  ('c0000001-0000-0000-0000-000000000002', 'professional', 'active',  '2023-01-01', NULL,         3200, 'AED',  5,  100,  1000),
  ('c0000001-0000-0000-0000-000000000003', 'basic',        'active',  '2023-06-01', NULL,          890, 'AED',  1,   10,   100),
  ('c0000001-0000-0000-0000-000000000004', 'enterprise',   'active',  '2022-11-01', NULL,         9800, 'AED', 99,  999, 99999),
  ('c0000001-0000-0000-0000-000000000005', 'professional', 'active',  '2023-08-01', NULL,         3200, 'AED',  5,  100,  1000),
  ('c0000001-0000-0000-0000-000000000006', 'basic',        'cancelled','2023-02-01','2024-02-01',  890, 'AED',  1,   10,   100),
  ('c0000001-0000-0000-0000-000000000007', 'enterprise',   'active',  '2022-10-01', NULL,         9800, 'AED', 99,  999, 99999),
  ('c0000001-0000-0000-0000-000000000008', 'professional', 'active',  '2023-05-01', NULL,         3200, 'AED',  5,  100,  1000),
  ('c0000001-0000-0000-0000-000000000009', 'enterprise',   'active',  '2022-12-01', NULL,         9800, 'AED', 99,  999, 99999),
  ('c0000001-0000-0000-0000-000000000010', 'basic',        'trial',   '2026-03-01', '2026-05-01',    0, 'AED',  1,   10,   100),
  ('c0000001-0000-0000-0000-000000000011', 'professional', 'active',  '2023-09-01', NULL,         3200, 'AED',  5,  100,  1000),
  ('c0000001-0000-0000-0000-000000000012', 'basic',        'cancelled','2023-04-01','2025-04-01',  890, 'AED',  1,   10,   100);

-- ── Stables ──────────────────────────────────────────────────
INSERT INTO stables (id, stable_code, name, city, region, country, capacity, occupied, status, owner_id, primary_vet_id, established_date) VALUES
  ('s0000001-0000-0000-0000-000000000001','STB-001','Al Nakheel Equestrian Centre', 'Dubai',         'Dubai',         'UAE',          40, 32, 'active',      'c0000001-0000-0000-0000-000000000001', 'vet00001-0000-0000-0000-000000000001', '2018-06-01'),
  ('s0000001-0000-0000-0000-000000000002','STB-002','Desert Rose Stables',          'Abu Dhabi',     'Abu Dhabi',     'UAE',          30, 30, 'full',        'c0000001-0000-0000-0000-000000000002', 'vet00001-0000-0000-0000-000000000002', '2017-03-15'),
  ('s0000001-0000-0000-0000-000000000003','STB-003','Emirates Royal Stables',       'Dubai',         'Dubai',         'UAE',          80, 62, 'active',      'c0000001-0000-0000-0000-000000000004', 'vet00001-0000-0000-0000-000000000001', '2015-01-01'),
  ('s0000001-0000-0000-0000-000000000004','STB-004','Al Forsan International',      'Abu Dhabi',     'Abu Dhabi',     'UAE',          60, 45, 'active',      'c0000001-0000-0000-0000-000000000004', 'vet00001-0000-0000-0000-000000000002', '2016-09-01'),
  ('s0000001-0000-0000-0000-000000000005','STB-005','Sharjah Equestrian Club',      'Sharjah',       'Sharjah',       'UAE',          35, 28, 'active',      'c0000001-0000-0000-0000-000000000003', 'vet00001-0000-0000-0000-000000000002', '2019-04-01'),
  ('s0000001-0000-0000-0000-000000000006','STB-006','Al Qassimi Stables',           'Ras Al Khaimah','Ras Al Khaimah','UAE',          25, 18, 'active',      'c0000001-0000-0000-0000-000000000005', 'vet00001-0000-0000-0000-000000000001', '2020-02-01'),
  ('s0000001-0000-0000-0000-000000000007','STB-007','Golden Gate Ranch',            'Dubai',         'Dubai',         'UAE',          50,  0, 'maintenance', 'c0000001-0000-0000-0000-000000000006', NULL,                                  '2021-07-01'),
  ('s0000001-0000-0000-0000-000000000008','STB-008','Al Zahrani Royal Stables',     'Riyadh',        'Riyadh',        'Saudi Arabia', 70, 65, 'active',      'c0000001-0000-0000-0000-000000000007', 'vet00001-0000-0000-0000-000000000003', '2014-11-01'),
  ('s0000001-0000-0000-0000-000000000009','STB-009','Desert Wind Stables',          'Riyadh',        'Riyadh',        'Saudi Arabia', 40, 31, 'active',      'c0000001-0000-0000-0000-000000000007', 'vet00001-0000-0000-0000-000000000003', '2017-08-01'),
  ('s0000001-0000-0000-0000-000000000010','STB-010','Doha International Equine',    'Doha',          'Doha',          'Qatar',        55, 48, 'active',      'c0000001-0000-0000-0000-000000000009', 'vet00001-0000-0000-0000-000000000004', '2016-05-01');
