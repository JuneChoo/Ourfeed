@echo off
cd /d "%~dp0"
set OURFEED_CORS_ORIGIN=https://ourfeed.vercel.app
python.exe ourfeed.py >> ourfeed.log 2>&1
