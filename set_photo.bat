@echo off
SET PGPASSWORD=postgres
SET PSQL="C:\Program Files\PostgreSQL\18\bin\psql.exe"

%PSQL% -U postgres -d hcs_db -c "ALTER TABLE clients ADD COLUMN IF NOT EXISTS photo_url TEXT;" > C:\Users\ahmed\Desktop\HCS\try2\photo_result.txt 2>&1

%PSQL% -U postgres -d hcs_db -c "UPDATE clients SET photo_url = '/user/assets/egyptian-riding-school.png' WHERE id = 'c0000013-0000-0000-0000-000000000013';" >> C:\Users\ahmed\Desktop\HCS\try2\photo_result.txt 2>&1
