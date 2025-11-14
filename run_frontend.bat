@echo off
echo ========================================
echo Starting Frontend GUI
echo ========================================
echo.

REM Clear Python cache
echo Clearing Python cache...
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found
    echo Please create one with: python -m venv venv
)

echo.
echo Starting GUI application...
echo.
python frontend\main.py

pause
