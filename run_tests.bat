@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Windows test runner for local ImageConverter development.
rem It creates/uses .venv, installs dev dependencies, then runs a named profile.

cd /d "%~dp0"

set "MODE=completion"
set "INSTALL_DEPS=1"
set "REQUIRE_DRIFT_SUMMARY=0"
set "REQUIRE_REPORT_CONSISTENCY=0"
set "REPORTS_DIR=artifacts\converted_images\reports"
set "SUMMARY_PATH=artifacts\converted_images\reports\chain_phase_telemetry_summary.txt"

if /I "%~1"=="--help" goto :help
if /I "%~1"=="-h" goto :help

:parse
if "%~1"=="" goto :main
if /I "%~1"=="--no-install" (
  set "INSTALL_DEPS=0"
  shift
  goto :parse
)
if /I "%~1"=="--require-drift-summary" (
  set "REQUIRE_DRIFT_SUMMARY=1"
  shift
  goto :parse
)
if /I "%~1"=="--require-report-consistency" (
  set "REQUIRE_REPORT_CONSISTENCY=1"
  shift
  goto :parse
)
if /I "%~1"=="completion" (
  set "MODE=completion"
  shift
  goto :parse
)
if /I "%~1"=="core-green" (
  set "MODE=core-green"
  shift
  goto :parse
)
if /I "%~1"=="extended" (
  set "MODE=extended"
  shift
  goto :parse
)
if /I "%~1"=="research" (
  set "MODE=research"
  shift
  goto :parse
)
if /I "%~1"=="safe-baseline" (
  set "MODE=safe-baseline"
  shift
  goto :parse
)
if /I "%~1"=="heavy" (
  set "MODE=heavy"
  shift
  goto :parse
)
if /I "%~1"=="all" (
  set "MODE=all"
  shift
  goto :parse
)
goto :usage_error

:main
call :ensure_venv
if errorlevel 1 exit /b %ERRORLEVEL%

if "%INSTALL_DEPS%"=="1" (
  echo.
  echo ==^> install dev dependencies
  "%PYTHON_BIN%" -m ensurepip --upgrade
  if errorlevel 1 exit /b %ERRORLEVEL%
  "%PYTHON_BIN%" -m pip install --upgrade pip
  if errorlevel 1 exit /b %ERRORLEVEL%
  "%PYTHON_BIN%" -m pip install -r requirements-dev.txt
  if errorlevel 1 exit /b %ERRORLEVEL%
)

echo.
echo ImageConverter test profile: %MODE%
echo Python: %PYTHON_BIN%

if /I "%MODE%"=="completion" goto :completion
if /I "%MODE%"=="core-green" goto :profile
if /I "%MODE%"=="extended" goto :profile
if /I "%MODE%"=="research" goto :profile
if /I "%MODE%"=="safe-baseline" goto :safe_baseline
if /I "%MODE%"=="heavy" goto :heavy
if /I "%MODE%"=="all" goto :all_tests
goto :usage_error

:ensure_venv
if exist ".venv\Scripts\python.exe" (
  set "PYTHON_BIN=.venv\Scripts\python.exe"
  goto :check_version
)

echo ==^> create .venv
where py >nul 2>nul
if not errorlevel 1 (
  py -3.10 -m venv .venv >nul 2>nul
  if not errorlevel 1 goto :venv_created
)

where python >nul 2>nul
if errorlevel 1 (
  echo FEHLER: Weder py noch python wurde gefunden.
  echo Bitte Python 3.10 installieren oder eine .venv im Projekt anlegen.
  exit /b 2
)
python -m venv .venv
if errorlevel 1 exit /b %ERRORLEVEL%

:venv_created
if not exist ".venv\Scripts\python.exe" (
  echo FEHLER: .venv\Scripts\python.exe wurde nicht erzeugt.
  exit /b 2
)
set "PYTHON_BIN=.venv\Scripts\python.exe"

:check_version
"%PYTHON_BIN%" -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo FEHLER: Der Python-Interpreter in .venv kann nicht gestartet werden.
  echo        Pruefe die lokale Python-Installation oder erstelle .venv neu.
  exit /b 2
)
"%PYTHON_BIN%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
  echo WARNUNG: Dieses Repo ist auf Python 3.10 ausgelegt ^(.python-version^).
  echo          Der aktuelle .venv-Interpreter ist:
  "%PYTHON_BIN%" --version
)
exit /b 0

:completion
echo.
echo ==^> image-ID hardcoding ratchet
"%PYTHON_BIN%" tools\check_no_new_image_id_hardcoding.py
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo ==^> compileall
"%PYTHON_BIN%" -m compileall src tests
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo ==^> pytest
"%PYTHON_BIN%" -m pytest
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo ==^> ImageConverter CLI help
"%PYTHON_BIN%" -m src.imageCompositeConverter --help
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo ==^> report consistency gate
if exist "%REPORTS_DIR%\conversion_checkpoint.json" (
  "%PYTHON_BIN%" tools\check_report_consistency.py "%REPORTS_DIR%"
  if errorlevel 1 (
    if "%REQUIRE_REPORT_CONSISTENCY%"=="1" exit /b !ERRORLEVEL!
    echo WARN: advisory report consistency gate failed for %REPORTS_DIR%.
  )
) else (
  echo SKIP: conversion checkpoint is missing: %REPORTS_DIR%\conversion_checkpoint.json
)

echo.
echo ==^> chain telemetry drift gate
if exist "%SUMMARY_PATH%" (
  "%PYTHON_BIN%" tools\check_chain_telemetry_drift_gate.py "%SUMMARY_PATH%"
  if errorlevel 1 (
    if "%REQUIRE_DRIFT_SUMMARY%"=="1" exit /b !ERRORLEVEL!
    echo WARN: advisory drift gate failed for %SUMMARY_PATH%.
  )
) else (
  if "%REQUIRE_DRIFT_SUMMARY%"=="1" (
    echo FEHLER: required drift summary artifact is missing: %SUMMARY_PATH%
    exit /b 1
  )
  echo SKIP: drift summary artifact is missing: %SUMMARY_PATH%
)
exit /b 0

:profile
"%PYTHON_BIN%" tools\run_pytest_profile.py %MODE%
exit /b %ERRORLEVEL%

:safe_baseline
set "RUN_HEAVY_CONVERSION_TESTS=1"
"%PYTHON_BIN%" -m pytest ^
  tests/test_image_composite_converter.py ^
  tests/test_weak_family_pipeline.py ^
  --deselect tests/test_image_composite_converter.py::test_vendored_site_packages_dirs_discovers_repo_bundle ^
  --deselect tests/test_image_composite_converter.py::test_load_optional_module_recovers_after_failed_partial_package ^
  --deselect tests/test_image_composite_converter.py::test_update_successful_conversions_manifest_keeps_existing_line_without_fresh_metrics ^
  --deselect tests/test_image_composite_converter.py::test_convert_range_uses_existing_conversion_rows_as_template_donors ^
  --deselect tests/test_image_composite_converter.py::test_parse_description_manual_review_clears_default_label_for_unclassified_sia_symbol ^
  --deselect tests/test_image_composite_converter.py::test_update_successful_conversions_manifest_keeps_single_failed_entry
exit /b %ERRORLEVEL%

:heavy
set "RUN_HEAVY_CONVERSION_TESTS=1"
set "PYTEST_PER_TEST_TIMEOUT_SECONDS=60"
"%PYTHON_BIN%" -m pytest -q -rs tests/test_image_composite_converter.py
exit /b %ERRORLEVEL%

:all_tests
set "RUN_HEAVY_CONVERSION_TESTS=1"
set "PYTEST_PER_TEST_TIMEOUT_SECONDS=60"
"%PYTHON_BIN%" -m pytest -q -rs
exit /b %ERRORLEVEL%

:help
echo Verwendung: run_tests.bat [Optionen] [Profil]
echo.
echo Profile:
echo   completion     Lokales Abschlussprofil ^(Standard^): Ratchet, compileall, pytest, CLI-Smoke, advisory Gates
echo   core-green     Schnelles stabiles Kernprofil
echo   extended       Breitere Suite ohne blocking_conversion
echo   research       Nur research/blockierende/optionale Tests
echo   safe-baseline  Windows-Pendant zu tools/run_safe_test_baseline.sh
echo   heavy          Schwere image_composite_converter-Suite
echo   all            Alle pytest-Tests inklusive Heavy-Tests
echo.
echo Optionen:
echo   --no-install                    Vorhandene .venv verwenden, keine pip-Installation
echo   --require-drift-summary          Drift-Gate fatal machen, wenn Summary fehlt/fehlschlaegt
echo   --require-report-consistency     Report-Konsistenz-Gate fatal machen
echo   -h, --help                       Diese Hilfe anzeigen
echo.
echo Beispiele:
echo   run_tests.bat
echo   run_tests.bat core-green
echo   run_tests.bat all
echo   run_tests.bat --no-install extended
exit /b 0

:usage_error
echo Unbekannte Argumente. run_tests.bat --help zeigt die Verwendung.
exit /b 1
