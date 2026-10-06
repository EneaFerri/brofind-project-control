@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_demo.ps1"
set "DEMO_EXIT_CODE=%ERRORLEVEL%"

if not "%DEMO_EXIT_CODE%"=="0" (
  echo.
  echo Arresto Cockpit non riuscito. Correggere l'errore mostrato prima di riprovare.
  if /I not "%BROFIND_NO_PAUSE%"=="1" pause
)

exit /b %DEMO_EXIT_CODE%
