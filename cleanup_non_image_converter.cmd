@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Cleanup script for this repository.
rem It removes files/folders that do not belong to the Image Converter subset.
rem IMPORTANT: Run this script only from the repository root.

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul

if not exist "src\image_composite_converter.py" (
  echo [ERROR] This script must be started from the ImageConverter repository root.
  popd >nul
  exit /b 1
)

echo This script will permanently delete files that are not part of the Image Converter subset.
echo Repository: %CD%
echo.
set /p "CONFIRM=Type IMAGE-CONVERTER to continue: "
if /I not "%CONFIRM%"=="IMAGE-CONVERTER" (
  echo Aborted.
  popd >nul
  exit /b 0
)

call :delete_file_if_exists README.md
call :delete_file_if_exists documentation_tasks.md

call :delete_dir_if_exists .vscode

for %%F in (src\*) do (
  if /I not "%%~nxF"=="image_composite_converter.py" (
    call :delete_path "%%~fF"
  )
)

for %%F in (tests\*) do (
  if /I not "%%~nxF"=="test_image_composite_converter.py" if /I not "%%~nxF"=="detailtests" (
    call :delete_path "%%~fF"
  )
)

if exist "tests\detailtests" (
  for %%F in (tests\detailtests\*) do (
    if /I not "%%~nxF"=="test_semantic_quality_flags.py" (
      call :delete_path "%%~fF"
    )
  )
)

for %%F in (docs\*) do (
  if /I not "%%~nxF"=="image_converter_cli.md" ^
  if /I not "%%~nxF"=="image_converter_workflow.md" ^
  if /I not "%%~nxF"=="ac08_improvement_plan.md" ^
  if /I not "%%~nxF"=="ac08_artifact_analysis.md" ^
  if /I not "%%~nxF"=="open_tasks.md" (
    call :delete_path "%%~fF"
  )
)

echo.
echo Cleanup finished.
popd >nul
exit /b 0

:delete_file_if_exists
if exist "%~1" (
  echo Deleting file: %~1
  del /f /q "%~1"
)
exit /b 0

:delete_dir_if_exists
if exist "%~1\" (
  echo Deleting directory: %~1
  rmdir /s /q "%~1"
)
exit /b 0

:delete_path
if exist "%~1\" (
  echo Deleting directory: %~1
  rmdir /s /q "%~1"
) else if exist "%~1" (
  echo Deleting file: %~1
  del /f /q "%~1"
)
exit /b 0
