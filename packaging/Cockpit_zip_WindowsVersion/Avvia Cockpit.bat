@echo off
title Brofind Control Cockpit - Demo
cd /d "%~dp0"
if not exist "sistema\python\python.exe" (
  echo.
  echo   ATTENZIONE: la cartella della demo non e' stata estratta dallo zip.
  echo.
  echo   1. Chiudi questa finestra.
  echo   2. Clic con il tasto destro sul file .zip e scegli "Estrai tutto...".
  echo   3. Apri la cartella estratta e fai doppio clic su "Avvia Cockpit".
  echo.
  pause
  exit /b 1
)
"sistema\python\python.exe" "sistema\avvio_demo.py"
if errorlevel 1 pause
