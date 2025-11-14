@echo off
cls
echo ============================================================
echo   Building Installer for Report Generator
echo ============================================================
echo.

call venv\Scripts\activate

echo [Step 1/5] Creating application icon...
python create_icon.py
if not exist app_icon.ico (
    echo   ⚠ No icon created, will use default
) else (
    echo   ✓ Icon ready
)
echo.

echo [Step 2/5] Building executable with PyInstaller...
echo   This may take 2-5 minutes...
echo.

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ReportGenerator.spec del ReportGenerator.spec

REM Install PyInstaller if needed
pip install pyinstaller >nul 2>&1

REM Build with icon if available
if exist app_icon.ico (
    pyinstaller --onefile --windowed --icon=app_icon.ico ^
        --name "ReportGenerator" ^
        --add-data "backend;backend" ^
        --hidden-import=flet ^
        --hidden-import=fastapi ^
        --hidden-import=uvicorn ^
        --hidden-import=pandas ^
        --hidden-import=openpyxl ^
        --hidden-import=reportlab ^
        --hidden-import=numpy ^
        --hidden-import=backend.core.config_loader ^
        --hidden-import=backend.core.data_processor ^
        --hidden-import=backend.core.delta_calculator ^
        --hidden-import=backend.core.risk_analyzer ^
        --hidden-import=backend.core.pdf_engine ^
        --hidden-import=backend.core.error_handler ^
        --collect-all=flet ^
        --collect-all=reportlab ^
        frontend\main.py
) else (
    pyinstaller --onefile --windowed ^
        --name "ReportGenerator" ^
        --add-data "backend;backend" ^
        --hidden-import=flet ^
        --hidden-import=fastapi ^
        --hidden-import=uvicorn ^
        --hidden-import=pandas ^
        --hidden-import=openpyxl ^
        --hidden-import=reportlab ^
        --hidden-import=numpy ^
        --hidden-import=backend.core.config_loader ^
        --hidden-import=backend.core.data_processor ^
        --hidden-import=backend.core.delta_calculator ^
        --hidden-import=backend.core.risk_analyzer ^
        --hidden-import=backend.core.pdf_engine ^
        --hidden-import=backend.core.error_handler ^
        --collect-all=flet ^
        --collect-all=reportlab ^
        frontend\main.py
)

if errorlevel 1 (
    echo   ✗ Build failed!
    pause
    exit /b 1
)

echo   ✓ Executable built successfully
echo.

echo [Step 3/5] Organizing files for installer...

REM Create package directory
if not exist "dist\ReportGenerator_Package" mkdir "dist\ReportGenerator_Package"

REM Copy executable
copy "dist\ReportGenerator.exe" "dist\ReportGenerator_Package\" >nul
echo   ✓ Copied executable

REM Copy backend config
if not exist "dist\ReportGenerator_Package\backend\config" mkdir "dist\ReportGenerator_Package\backend\config"
copy "backend\config\*.json" "dist\ReportGenerator_Package\backend\config\" >nul
echo   ✓ Copied configuration files

REM Copy sample data
if not exist "dist\ReportGenerator_Package\backend\sample_data" mkdir "dist\ReportGenerator_Package\backend\sample_data"
copy "backend\sample_data\*.csv" "dist\ReportGenerator_Package\backend\sample_data\" >nul
echo   ✓ Copied sample data

REM Create output folder
if not exist "dist\ReportGenerator_Package\generated_reports" mkdir "dist\ReportGenerator_Package\generated_reports"
echo   ✓ Created output folder

REM Copy README
echo Offline Report Generator > "dist\ReportGenerator_Package\README.txt"
echo. >> "dist\ReportGenerator_Package\README.txt"
echo HOW TO USE: >> "dist\ReportGenerator_Package\README.txt"
echo 1. Launch the application >> "dist\ReportGenerator_Package\README.txt"
echo 2. Select your CSV/Excel file >> "dist\ReportGenerator_Package\README.txt"
echo 3. Choose report type and variant >> "dist\ReportGenerator_Package\README.txt"
echo 4. Click Generate Reports >> "dist\ReportGenerator_Package\README.txt"
echo 5. Find PDFs in generated_reports folder >> "dist\ReportGenerator_Package\README.txt"
echo. >> "dist\ReportGenerator_Package\README.txt"
echo Sample data files are in backend\sample_data\ >> "dist\ReportGenerator_Package\README.txt"
echo   ✓ Created README

echo.

echo [Step 4/5] Checking for Inno Setup...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo   ✓ Inno Setup found
    echo.
    echo [Step 5/5] Building installer...
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_config.iss
    
    if errorlevel 1 (
        echo   ⚠ Installer build had issues
    ) else (
        echo   ✓ Installer created successfully!
        echo.
        echo ============================================================
        echo   INSTALLER BUILD COMPLETE!
        echo ============================================================
        echo.
        echo Installer location:
        echo   installer_output\ReportGenerator_Setup.exe
        echo.
        echo This is a professional Windows installer that:
        echo   ✓ Asks user where to install
        echo   ✓ Creates Start Menu shortcuts
        echo   ✓ Creates Desktop shortcut (optional)
        echo   ✓ Can be uninstalled properly
        echo.
        echo Share this file with users!
        echo.
        if exist "installer_output\ReportGenerator_Setup.exe" (
            explorer "installer_output"
        )
    )
) else (
    echo   ⚠ Inno Setup not found
    echo.
    echo   Executable is ready in: dist\ReportGenerator_Package\
    echo.
    echo   To create an installer:
    echo   1. Download Inno Setup from: https://jrsoftware.org/isdl.php
    echo   2. Install Inno Setup
    echo   3. Run this script again
    echo.
    echo   OR share the dist\ReportGenerator_Package folder as a ZIP file
    echo.
    explorer "dist\ReportGenerator_Package"
)

echo.
pause
