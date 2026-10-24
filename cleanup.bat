@echo off
setlocal EnableExtensions

rem Repository cleanup for Windows. The default is deliberately a dry run.
rem Use --apply to remove disposable files from the working tree.
rem Use --purge-history to remove the same files from every Git commit.

cd /d "%~dp0"
set "MODE=dry-run"
if /I "%~1"=="--apply" set "MODE=apply"
if /I "%~1"=="--purge-history" set "MODE=history"
if /I "%~1"=="--help" goto :help
if not "%~2"=="" goto :usage_error
if "%~1"=="" goto :run
if /I "%~1"=="--dry-run" goto :run
if /I "%~1"=="--apply" goto :run
if /I "%~1"=="--purge-history" goto :run
goto :usage_error

:run
echo ImageConverter cleanup: %MODE%
echo.

if /I "%MODE%"=="history" goto :history

set "CLEANUP_ARGS="
if /I "%MODE%"=="apply" set "CLEANUP_ARGS=--apply"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m tools.cleanup_test_data %CLEANUP_ARGS%
) else (
  python -m tools.cleanup_test_data %CLEANUP_ARGS%
)
exit /b %ERRORLEVEL%

:history
where git-filter-repo >nul 2>nul
if errorlevel 1 (
  echo FEHLER: git-filter-repo wurde nicht gefunden.
  echo Installation: python -m pip install git-filter-repo
  exit /b 2
)
git diff --quiet && git diff --cached --quiet
if errorlevel 1 (
  echo FEHLER: Fuer die History-Bereinigung muss der Arbeitsbaum sauber sein.
  exit /b 3
)
echo WARNUNG: Alle Commit-IDs werden neu geschrieben. Andere Klone muessen danach
echo          neu geklont werden. Zum Veroeffentlichen ist ein Force-Push noetig.
echo.
git filter-repo --force --invert-paths ^
  --path .venv --path .venv-py314 --path venv ^
  --path .pytest_cache --path .mypy_cache --path .ruff_cache ^
  --path .coverage --path htmlcov ^
  --path imageCompositeConverter.local.log ^
  --path artifacts/pytest_test_image_composite_converter_2026-04-27.log ^
  --path-glob "**/__pycache__/**" --path-glob "**/*.pyc" ^
  --path-glob "**/*.pyo" --path-glob "**/*.tmp" --path-glob "**/*.prof"
if errorlevel 1 exit /b %ERRORLEVEL%
echo.
echo History bereinigt. Pruefen Sie das Ergebnis, bevor Sie mit
echo git push --force-with-lease --all und --tags veroeffentlichen.
exit /b 0

:help
echo Verwendung: cleanup.bat [--dry-run^|--apply^|--purge-history]
echo   --dry-run        Nur gefundene Dateien anzeigen ^(Standard^)
echo   --apply          Entbehrliche Dateien im Arbeitsbaum loeschen
echo   --purge-history  Dieselben Pfade mit git-filter-repo aus allen Commits entfernen
exit /b 0

:usage_error
echo Unbekannte Argumente. cleanup.bat --help zeigt die Verwendung.
exit /b 1
