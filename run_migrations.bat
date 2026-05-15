@echo off
SET PGPASSWORD=postgres
SET PSQL="C:\Program Files\PostgreSQL\18\bin\psql.exe"

echo Running migration 12_owner_auth...
%PSQL% -U postgres -d hcs_db -f "C:\Users\ahmed\Desktop\HCS\try2\database\migrations\12_owner_auth.sql" > C:\Users\ahmed\Desktop\HCS\try2\migration_result.txt 2>&1

echo Running migration 13_youssef_setup...
%PSQL% -U postgres -d hcs_db -f "C:\Users\ahmed\Desktop\HCS\try2\database\migrations\13_youssef_setup.sql" >> C:\Users\ahmed\Desktop\HCS\try2\migration_result.txt 2>&1

echo Done. >> C:\Users\ahmed\Desktop\HCS\try2\migration_result.txt
