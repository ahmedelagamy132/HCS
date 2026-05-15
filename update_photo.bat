@echo off
SET PGPASSWORD=postgres
SET PSQL="C:\Program Files\PostgreSQL\18\bin\psql.exe"

%PSQL% -U postgres -d hcs_db -c "UPDATE clients SET photo_url = '/user/assets/youssef-galal.png' WHERE id = 'c0000013-0000-0000-0000-000000000013';" > C:\Users\ahmed\Desktop\HCS\try2\update_photo_result.txt 2>&1
