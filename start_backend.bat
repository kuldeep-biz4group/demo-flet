@echo off
echo ========================================
echo Offline Report Generation System
echo Starting Backend Server...
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo Starting FastAPI server on http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

pause
