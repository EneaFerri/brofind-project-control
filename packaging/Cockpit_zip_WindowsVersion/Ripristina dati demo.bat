@echo off
title Brofind Control Cockpit - Ripristino dati demo
cd /d "%~dp0"
if not exist "sistema\python\python.exe" (
  echo.
  echo   Estrai prima lo zip: tasto destro sul file .zip, "Estrai tutto...".
  echo.
  pause
  exit /b 1
)
"sistema\python\python.exe" "sistema\ripristina_demo.py"
echo.
pause
