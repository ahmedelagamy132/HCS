@echo off
SET PGPASSWORD=postgres
SET PSQL="C:\Program Files\PostgreSQL\18\bin\psql.exe"

%PSQL% -U postgres -d hcs_db -c "INSERT INTO horses (id, horse_code, name, breed, gender, date_of_birth, color, weight_kg, height_cm, owner_id, stable_id, primary_vet_id, health_status, is_racing, is_active) VALUES ('a0000001-0000-0000-0000-000000000001', 'HRS-ERS-01', 'Casino', 'Arabian', 'stallion', '2019-06-15', 'Bay', 520, 157, 'c0000013-0000-0000-0000-000000000013', 'e0000001-0000-0000-0000-000000000001', '1e700001-0000-0000-0000-000000000001', 'excellent', FALSE, TRUE) ON CONFLICT (id) DO UPDATE SET name='Casino', stable_id='e0000001-0000-0000-0000-000000000001';" > C:\Users\ahmed\Desktop\HCS\try2\horse_result.txt 2>&1

echo Done >> C:\Users\ahmed\Desktop\HCS\try2\horse_result.txt
