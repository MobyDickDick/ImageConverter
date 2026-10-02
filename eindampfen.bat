@echo off
setlocal EnableExtensions

rem Erstellt eine schlanke, jederzeit rueckgaengig zu machende Arbeitskopie.
rem Ohne Argument wird die Arbeitskopie eingedampft. --dry-run zeigt nur die Wirkung.

cd /d "%~dp0"

if "%~1"=="" goto :apply
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
echo   - neun repraesentative Kontroll-, Problem- und Grenzfallbilder
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
set "SPARSE_FILE=%TEMP%\ImageConverter-sparse-%RANDOM%-%RANDOM%.txt"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "$patterns = [System.Collections.Generic.List[string]]@('/*', '!/*/', '/src/', '/tests/', '/tools/', '/config/', '/stabilization/', '/.github/', '/.vscode/', '/artifacts/', '!/artifacts/*/', '/artifacts/images_to_convert/', '!/artifacts/images_to_convert/*.jpg', '!/artifacts/images_to_convert/*.JPG', '/artifacts/images_to_convert/nonconvertable/', '!/artifacts/images_to_convert/nonconvertable/*.jpg', '!/artifacts/images_to_convert/nonconvertable/*.JPG', '/artifacts/regression_baseline/', '/artifacts/evaluation/');" ^
  "$subset = Get-Content -LiteralPath 'config/compact_image_subset.txt' | Where-Object { $_ -and -not $_.StartsWith('#') };" ^
  "$subset | ForEach-Object { $patterns.Add('/artifacts/images_to_convert/' + $_) };" ^
  "Set-Content -LiteralPath $env:SPARSE_FILE -Value $patterns -Encoding ASCII"
if errorlevel 1 goto :sparse_pattern_failed

rem Die Porcelain-Schnittstelle setzt die Muster und aktualisiert den Arbeitsbaum
rem atomar. Das direkte Schreiben nach .git/info plus reapply war je nach
rem Git-Version wirkungslos, obwohl der Befehl Erfolg meldete.
git sparse-checkout set --no-cone --stdin < "%SPARSE_FILE%"
set "SPARSE_EXIT=%ERRORLEVEL%"
del /q "%SPARSE_FILE%" >nul 2>nul
if not "%SPARSE_EXIT%"=="0" exit /b %SPARSE_EXIT%

rem Nicht nur dem Exitcode vertrauen: Diese versionierten Beispieldateien muessen
rem nach einem wirksamen Sparse-Checkout physisch aus der Arbeitskopie fehlen.
if exist "docs\README.md" goto :sparse_failed
if exist "vendor\linux-py310\site-packages\PIL\AvifImagePlugin.py" goto :sparse_failed
if exist "artifacts\converted_images\commented_diff_images\AC0020_M_commented_diff.png" goto :sparse_failed
if exist "artifacts\images_to_convert\AC0010.jpg" goto :sparse_failed

echo.
echo Arbeitskopie wurde physisch eingedampft.
echo Hinweis: "git status" bleibt dabei absichtlich sauber; Sparse-Checkout ist
echo eine lokale Ansicht und keine Dateiaenderung. Starte schnelles Testprofil ...
call :run_quick_test
exit /b %ERRORLEVEL%

:sparse_pattern_failed
del /q "%SPARSE_FILE%" >nul 2>nul
echo FEHLER: Die Sparse-Checkout-Muster konnten nicht erzeugt werden.
exit /b 5

:sparse_failed
echo FEHLER: Git meldete Erfolg, aber ausgeschlossene Dateien sind weiterhin vorhanden.
echo Die Arbeitskopie wurde nicht nachweisbar eingedampft. Pruefe "git --version"
echo und "git sparse-checkout list". Es werden keine Tests gestartet.
exit /b 5

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
echo   --dry-run  Nur Wirkung anzeigen
echo   --apply    Sparse-Checkout aktivieren und Schnelltests ausfuehren ^(Standard^)
echo   --restore  Alle versionierten Dateien wieder einblenden
echo   --test     Nur das schnelle core-green-Testprofil ausfuehren
exit /b 0

:usage_error
echo Unbekannte Argumente. eindampfen.bat --help zeigt die Verwendung.
exit /b 1
