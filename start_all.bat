@echo off
title Start IDS System — Fresh
echo ===================================================
echo   Internal Network Traffic Monitoring IDS
echo   Starting System FRESH (killing old processes)
echo ===================================================

:: ── Step 1: Kill existing instances ─────────────────────────────────────────
echo.
echo [0/3] Stopping any running instances...

:: Kill Python processes (backend API + monitor)
taskkill /F /FI "WINDOWTITLE eq IDS Backend API*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq IDS Network Monitor*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq IDS Dashboard*" >nul 2>&1

:: Also force-kill any lingering python / node on the IDS ports
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Old processes stopped.
timeout /t 2 /nobreak >nul

:: ── Step 2: Start services fresh ─────────────────────────────────────────────
echo.
echo [1/3] Starting Backend API...
start "IDS Backend API" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate.bat && python main.py"

timeout /t 2 /nobreak >nul

echo.
echo [2/3] Starting Network Monitor...
echo NOTE: Monitor requires Admin privileges for full packet capture.
start "IDS Network Monitor" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate.bat && python monitor.py"

timeout /t 2 /nobreak >nul

echo.
echo [3/3] Starting Frontend Dashboard...
start "IDS Dashboard" cmd /k "cd /d "%~dp0" && npm run dev"

:: ── Done ─────────────────────────────────────────────────────────────────────
echo.
echo ===================================================
echo  All services launched fresh!
echo  - API:       http://localhost:8000
echo  - Dashboard: http://localhost:5173
echo ===================================================
echo.
pause
