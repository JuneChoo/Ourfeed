@echo off
wmic process where "commandline like '%%ourfeed.py%%'" call terminate
