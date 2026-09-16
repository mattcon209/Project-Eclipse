@echo off
cd /d "%~dp0"
py run.py %*
if errorlevel 1 python run.py %*
