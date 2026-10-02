@echo off
setlocal EnableExtensions

rem Erstellt eine schlanke, jederzeit rueckgaengig zu machende Arbeitskopie.
rem Ohne Argument wird ausschliesslich angezeigt, was passieren wuerde.

cd /d "%~dp0"

if "%~1"=="" goto :preview
if not "%~2"=="" goto :usage_error
if /I "%~1"=="--dry-run" goto :preview
if /I "%~1"=="--apply" goto :apply
if /I "%~1"=="--restore" goto :restore
if /I "%~1"=="--test" goto :quick_test
if /I "%~1"=="--help" goto :help
goto :usage_error

:require_git
where git >nul 2>nul
if errorlevel 1 (
  echo FEHLER: Git wurde nicht gefunden.
  exit /b 2
)
git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo FEHLER: Das Skript muss in einer Git-Arbeitskopie liegen.
  exit /b 2
)
exit /b 0

:require_clean
call :require_git
if errorlevel 1 exit /b %ERRORLEVEL%
for /f "delims=" %%I in ('git status --porcelain --untracked-files^=all') do (
  echo FEHLER: Die Arbeitskopie enthaelt Aenderungen oder neue Dateien.
  echo Bitte zuerst committen, verschieben oder entfernen. Es wurde nichts geaendert.
  exit /b 3
)
exit /b 0

:preview
call :require_git
if errorlevel 1 exit /b %ERRORLEVEL%
echo ImageConverter eindampfen ^(nur Vorschau^)
echo.
echo --apply aktiviert Git Sparse-Checkout. In der Arbeitskopie bleiben:
echo   - Programmcode: src, config, tools und stabilization
echo   - Tests und CI-Konfiguration: tests, .github und .vscode
echo   - notwendige Eingaben und Baselines unter artifacts
echo   - alle Dateien im Projektstamm
echo.
echo Ausgeblendet werden insbesondere vendor, historische docs sowie erzeugte
echo Konvertierungs- und Auswertungsartefakte. Die Dateien bleiben in Git und
echo koennen mit --restore vollstaendig wieder eingeblendet werden.
echo.
echo Nach --apply laeuft nur das schnelle, stabile Testprofil. Fuer eine reine
echo Wiederholung dieses Profils: eindampfen.bat --test
exit /b 0

:apply
call :require_clean
if errorlevel 1 exit /b %ERRORLEVEL%

echo Aktiviere schlanke Arbeitskopie ...
git sparse-checkout init --no-cone
if errorlevel 1 exit /b %ERRORLEVEL%

for /f "delims=" %%I in ('git rev-parse --git-path info/sparse-checkout') do set "SPARSE_FILE=%%I"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "$patterns = @('/*', '!/*/', '/src/', '/tests/', '/tools/', '/config/', '/stabilization/', '/.github/', '/.vscode/', '/artifacts/', '!/artifacts/*/', '/artifacts/images_to_convert/', '/artifacts/regression_baseline/', '/artifacts/evaluation/');" ^
  "Set-Content -LiteralPath $env:SPARSE_FILE -Value $patterns -Encoding ASCII"
if errorlevel 1 exit /b %ERRORLEVEL%

git sparse-checkout reapply
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo Arbeitskopie wurde eingedampft. Starte schnelles Testprofil ...
call :run_quick_test
exit /b %ERRORLEVEL%

:restore
call :require_clean
if errorlevel 1 exit /b %ERRORLEVEL%
git sparse-checkout disable
if errorlevel 1 exit /b %ERRORLEVEL%
echo Vollstaendige Arbeitskopie wiederhergestellt.
exit /b 0

:quick_test
call :require_git
if errorlevel 1 exit /b %ERRORLEVEL%
call :run_quick_test
exit /b %ERRORLEVEL%

:run_quick_test
where py >nul 2>nul
if not errorlevel 1 (
  py -3 tools\run_pytest_profile.py core-green
  exit /b %ERRORLEVEL%
)
where python >nul 2>nul
if errorlevel 1 (
  echo FEHLER: Weder py noch python wurde gefunden.
  exit /b 4
)
python tools\run_pytest_profile.py core-green
exit /b %ERRORLEVEL%

:help
echo Verwendung: eindampfen.bat [--dry-run^|--apply^|--restore^|--test]
echo   --dry-run  Nur Wirkung anzeigen ^(Standard^)
echo   --apply    Sparse-Checkout aktivieren und Schnelltests ausfuehren
echo   --restore  Alle versionierten Dateien wieder einblenden
echo   --test     Nur das schnelle core-green-Testprofil ausfuehren
exit /b 0

:usage_error
echo Unbekannte Argumente. eindampfen.bat --help zeigt die Verwendung.
exit /b 1
