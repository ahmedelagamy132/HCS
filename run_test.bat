@echo off
cd /d C:\Users\ahmed\Desktop\HCS\try2
python test_db2.py > C:\Users\ahmed\Desktop\HCS\try2\test_result.txt 2>&1
echo exit_code: %ERRORLEVEL% >> C:\Users\ahmed\Desktop\HCS\try2\test_result.txt
