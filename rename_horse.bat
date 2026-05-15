@echo off
SET PGPASSWORD=postgres
SET PSQL="C:\Program Files\PostgreSQL\18\bin\psql.exe"

%PSQL% -U postgres -d hcs_db -c "UPDATE horses SET name = 'Casine' WHERE id = 'a0000001-0000-0000-0000-000000000001';" > C:\Users\ahmed\Desktop\HCS\try2\rename_result.txt 2>&1
