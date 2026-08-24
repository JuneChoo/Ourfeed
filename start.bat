@echo off
cd /d "%~dp0"
python.exe ourfeed.py >> ourfeed.log 2>&1
