@echo off
SET PGPASSWORD=postgres
SET PSQL="C:\Program Files\PostgreSQL\18\bin\psql.exe"

%PSQL% -U postgres -d hcs_db -c "DELETE FROM horses WHERE owner_id = 'c0000013-0000-0000-0000-000000000013' AND id != 'a0000001-0000-0000-0000-000000000001';" > C:\Users\ahmed\Desktop\HCS\try2\remove_result.txt 2>&1
