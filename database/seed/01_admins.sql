-- ============================================================
-- HCS — Equine Intelligence System
-- seed/01_admins.sql  |  Admin users + permissions
-- Passwords are bcrypt-hashed. Default password: HCS@Admin2026
-- ============================================================

INSERT INTO admin_users (id, admin_code, full_name, email, password_hash, role, is_active, last_login_at) VALUES
  ('a0000001-0000-0000-0000-000000000001', 'ADM-001', 'Ahmed Al-Mansouri',  'ahmed@hcs.ai',   crypt('HCS@Admin2026', gen_salt('bf',12)), 'super_admin', TRUE, NOW() - INTERVAL '2 hours'),
  ('a0000001-0000-0000-0000-000000000002', 'ADM-002', 'Sarah Al-Khouri',    'sarah@hcs.ai',   crypt('HCS@Admin2026', gen_salt('bf',12)), 'super_admin', TRUE, NOW() - INTERVAL '3 hours'),
  ('a0000001-0000-0000-0000-000000000003', 'ADM-003', 'Omar Bin Rashid',    'omar@hcs.ai',    crypt('HCS@Admin2026', gen_salt('bf',12)), 'super_admin', TRUE, NOW() - INTERVAL '1 day'),
  ('a0000001-0000-0000-0000-000000000004', 'ADM-004', 'Fatima Al-Zaabi',    'fatima@hcs.ai',  crypt('HCS@Admin2026', gen_salt('bf',12)), 'staff_admin', TRUE, NOW() - INTERVAL '1 hour'),
  ('a0000001-0000-0000-0000-000000000005', 'ADM-005', 'Hassan Al-Faris',    'hassan@hcs.ai',  crypt('HCS@Admin2026', gen_salt('bf',12)), 'staff_admin', TRUE, NOW() - INTERVAL '2 hours'),
  ('a0000001-0000-0000-0000-000000000006', 'ADM-006', 'Layla Al-Shamsi',    'layla@hcs.ai',   crypt('HCS@Admin2026', gen_salt('bf',12)), 'staff_admin', TRUE, NOW() - INTERVAL '2 days'),
  ('a0000001-0000-0000-0000-000000000007', 'ADM-007', 'Khalid Bin Nasser',  'khalid.n@hcs.ai',crypt('HCS@Admin2026', gen_salt('bf',12)), 'staff_admin', TRUE, NOW() - INTERVAL '4 hours'),
  ('a0000001-0000-0000-0000-000000000008', 'ADM-008', 'Mariam Al-Muhairi',  'mariam@hcs.ai',  crypt('HCS@Admin2026', gen_salt('bf',12)), 'staff_admin', FALSE, NOW() - INTERVAL '3 days'),
  ('a0000001-0000-0000-0000-000000000009', 'ADM-009', 'Yousef Al-Hamdan',   'yousef@hcs.ai',  crypt('HCS@Admin2026', gen_salt('bf',12)), 'view_only',   FALSE, NOW() - INTERVAL '7 days');

-- Super admins — full access to everything
INSERT INTO admin_permissions (admin_id, resource, can_read, can_create, can_update, can_delete, can_export, granted_by) VALUES
  ('a0000001-0000-0000-0000-000000000001', 'clients',    TRUE, TRUE, TRUE, TRUE, TRUE, 'a0000001-0000-0000-0000-000000000001'),
  ('a0000001-0000-0000-0000-000000000001', 'stables',    TRUE, TRUE, TRUE, TRUE, TRUE, 'a0000001-0000-0000-0000-000000000001'),
  ('a0000001-0000-0000-0000-000000000001', 'horses',     TRUE, TRUE, TRUE, TRUE, TRUE, 'a0000001-0000-0000-0000-000000000001'),
  ('a0000001-0000-0000-0000-000000000001', 'ai_models',  TRUE, TRUE, TRUE, TRUE, TRUE, 'a0000001-0000-0000-0000-000000000001'),
  ('a0000001-0000-0000-0000-000000000001', 'reports',    TRUE, TRUE, TRUE, TRUE, TRUE, 'a0000001-0000-0000-0000-000000000001'),
  ('a0000001-0000-0000-0000-000000000001', 'settings',   TRUE, TRUE, TRUE, TRUE, FALSE,'a0000001-0000-0000-0000-000000000001'),
  ('a0000001-0000-0000-0000-000000000001', 'admins',     TRUE, TRUE, TRUE, TRUE, FALSE,'a0000001-0000-0000-0000-000000000001');

-- Staff — Fatima: Clients + Stables
INSERT INTO admin_permissions (admin_id, resource, can_read, can_create, can_update, can_delete, can_export, granted_by) VALUES
  ('a0000001-0000-0000-0000-000000000004', 'clients', TRUE, TRUE, TRUE, FALSE, TRUE, 'a0000001-0000-0000-0000-000000000001'),
  ('a0000001-0000-0000-0000-000000000004', 'stables', TRUE, TRUE, TRUE, FALSE, TRUE, 'a0000001-0000-0000-0000-000000000001');

-- Staff — Hassan: Horses + Health
INSERT INTO admin_permissions (admin_id, resource, can_read, can_create, can_update, can_delete, can_export, granted_by) VALUES
  ('a0000001-0000-0000-0000-000000000005', 'horses',  TRUE, TRUE, TRUE, FALSE, TRUE, 'a0000001-0000-0000-0000-000000000001'),
  ('a0000001-0000-0000-0000-000000000005', 'health',  TRUE, TRUE, TRUE, FALSE, TRUE, 'a0000001-0000-0000-0000-000000000001');

-- Staff — Layla: Reports + Export
INSERT INTO admin_permissions (admin_id, resource, can_read, can_create, can_update, can_delete, can_export, granted_by) VALUES
  ('a0000001-0000-0000-0000-000000000006', 'reports', TRUE, TRUE, FALSE, FALSE, TRUE, 'a0000001-0000-0000-0000-000000000001'),
  ('a0000001-0000-0000-0000-000000000006', 'clients', TRUE, FALSE, FALSE, FALSE, TRUE, 'a0000001-0000-0000-0000-000000000001');

-- Staff — Khalid: Stables + Horses
INSERT INTO admin_permissions (admin_id, resource, can_read, can_create, can_update, can_delete, can_export, granted_by) VALUES
  ('a0000001-0000-0000-0000-000000000007', 'stables', TRUE, TRUE, TRUE, FALSE, TRUE, 'a0000001-0000-0000-0000-000000000001'),
  ('a0000001-0000-0000-0000-000000000007', 'horses',  TRUE, TRUE, TRUE, FALSE, TRUE, 'a0000001-0000-0000-0000-000000000001');
