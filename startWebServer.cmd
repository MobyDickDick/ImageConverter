@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m src.imageConverterGui %*
) else (
    python -m src.imageConverterGui %*
)
if errorlevel 1 pause
