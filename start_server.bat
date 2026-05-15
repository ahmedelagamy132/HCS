@echo off
cd /d C:\Users\ahmed\Desktop\HCS\try2
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
