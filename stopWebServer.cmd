@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m src.imageConverterGui --stop %*
) else (
    python -m src.imageConverterGui --stop %*
)
if errorlevel 1 pause
