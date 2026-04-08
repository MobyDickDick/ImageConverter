@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "REPO_ROOT=%~dp0.."
set "SOURCE=%REPO_ROOT%\src\imageCompositeConverter.py"
set "TARGET_MODULE=%REPO_ROOT%\src\iCCModules\imageCompositeConverterRemaining.py"
set "LOG_DIR=%REPO_ROOT%\artifacts\reports"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%I"
set "LOG_JSON=%LOG_DIR%\function_extraction_rounds_%TS%.json"
set "LOG_TXT=%LOG_DIR%\function_extraction_rounds_%TS%.log"

set "VERIFY_CMD=python -m py_compile src/imageCompositeConverter.py src/iCCModules/imageCompositeConverterRemaining.py"

echo Starte Auslagerung verbleibender Funktionen aus %SOURCE%
echo Zielmodul: %TARGET_MODULE%
echo Log (JSON): %LOG_JSON%
echo Log (Text): %LOG_TXT%

python "%~dp0extract_remaining_functions_batch.py" ^
  --source "%SOURCE%" ^
  --target-module "%TARGET_MODULE%" ^
  --exclude main ^
  --verify-cmd "%VERIFY_CMD%" ^
  --log-json "%LOG_JSON%" ^
  --log-text "%LOG_TXT%" ^
  --workdir "%REPO_ROOT%"

if errorlevel 1 (
  echo.
  echo Auslagerung abgeschlossen mit Fehlern. Details siehe Logs.
  exit /b 1
)

echo.
echo Auslagerung erfolgreich abgeschlossen. Details siehe Logs.
exit /b 0
