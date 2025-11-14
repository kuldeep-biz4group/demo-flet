@echo off
echo ========================================
echo Offline Report Generation System
echo Starting Application...
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo Starting backend server in background...
start /B uvicorn backend.main:app --host 127.0.0.1 --port 8000

echo Waiting for backend to initialize...
timeout /t 3 /nobreak > nul

echo Starting desktop application...
python frontend\main.py

pause
