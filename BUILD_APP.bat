@echo off
cls
echo ============================================================
echo   Building Clarikey Analytics Executable
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install --upgrade pip
    pip install flet pillow
) else (
    call venv\Scripts\activate
)

:: Create assets directory if it doesn't exist
if not exist "assets\" (
    mkdir assets
)

:: Create icon if it doesn't exist
if not exist "assets\icon.ico" (
    echo Creating application icon...
    echo from PIL import Image, ImageDraw, ImageFont > create_icon.py
    echo import os >> create_icon.py
    echo img = Image.new('RGB', (256, 256), (0, 120, 215)) >> create_icon.py
    echo d = ImageDraw.Draw(img) >> create_icon.py
    echo try: font = ImageFont.truetype("arial.ttf", 120) >> create_icon.py
    echo except: font = ImageFont.load_default() >> create_icon.py
    echo d.text((30, 60), "CA", fill=(255, 255, 255), font=font) >> create_icon.py
    echo os.makedirs('assets', exist_ok=True) >> create_icon.py
    echo img.save('assets/icon.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]) >> create_icon.py
    
    python create_icon.py
    if exist "create_icon.py" del create_icon.py
)

:: Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

:: Build the executable
echo.
echo Building executable...
if exist "dist\" rmdir /s /q dist
if exist "build\" rmdir /s /q build

flet pack frontend/main.py --name "Clarikey Analytics" --icon assets/icon.ico

echo.
echo ============================================================
if exist "dist\Clarikey Analytics.exe" (
    echo ✅ Build successful!
    echo Executable: %CD%\dist\Clarikey Analytics.exe
) else (
    echo ❌ Build failed! Check the error messages above.
)
echo ============================================================

pause
