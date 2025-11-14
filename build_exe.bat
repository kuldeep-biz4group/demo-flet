@echo off
cls
echo ============================================================
echo   Building Report Generator Executable
echo ============================================================
echo.

call venv\Scripts\activate

echo [1/4] Installing PyInstaller...
pip install pyinstaller
echo.

echo [2/4] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ReportGenerator.spec del ReportGenerator.spec
echo   ✓ Cleaned
echo.

echo [3/4] Building executable with PyInstaller...
echo   This may take 2-5 minutes...
echo.

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

if errorlevel 1 (
    echo.
    echo ✗ Build failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo   ✓ Build successful!
echo.

echo [4/4] Creating distribution folder...

REM Create final distribution folder
if not exist "dist\ReportGenerator_Package" mkdir "dist\ReportGenerator_Package"

REM Copy executable
copy "dist\ReportGenerator.exe" "dist\ReportGenerator_Package\"
echo   ✓ Copied executable

REM Copy backend config
if not exist "dist\ReportGenerator_Package\backend\config" mkdir "dist\ReportGenerator_Package\backend\config"
copy "backend\config\*.json" "dist\ReportGenerator_Package\backend\config\"
echo   ✓ Copied configuration files

REM Copy sample data
if not exist "dist\ReportGenerator_Package\backend\sample_data" mkdir "dist\ReportGenerator_Package\backend\sample_data"
copy "backend\sample_data\*.csv" "dist\ReportGenerator_Package\backend\sample_data\"
echo   ✓ Copied sample data

REM Create output folder
if not exist "dist\ReportGenerator_Package\generated_reports" mkdir "dist\ReportGenerator_Package\generated_reports"
echo   ✓ Created output folder

REM Create README
echo Offline Report Generator > "dist\ReportGenerator_Package\README.txt"
echo. >> "dist\ReportGenerator_Package\README.txt"
echo HOW TO USE: >> "dist\ReportGenerator_Package\README.txt"
echo 1. Double-click ReportGenerator.exe >> "dist\ReportGenerator_Package\README.txt"
echo 2. Select your CSV/Excel file >> "dist\ReportGenerator_Package\README.txt"
echo 3. Choose report type and variant >> "dist\ReportGenerator_Package\README.txt"
echo 4. Click Generate Reports >> "dist\ReportGenerator_Package\README.txt"
echo 5. Find PDFs in generated_reports folder >> "dist\ReportGenerator_Package\README.txt"
echo. >> "dist\ReportGenerator_Package\README.txt"
echo SAMPLE DATA: >> "dist\ReportGenerator_Package\README.txt"
echo Test files are in backend\sample_data\ >> "dist\ReportGenerator_Package\README.txt"
echo   - progress_monitoring_sample.csv >> "dist\ReportGenerator_Package\README.txt"
echo   - screening_sample.csv >> "dist\ReportGenerator_Package\README.txt"
echo. >> "dist\ReportGenerator_Package\README.txt"
echo No Python installation required! >> "dist\ReportGenerator_Package\README.txt"
echo   ✓ Created README.txt

echo.
echo ============================================================
echo   BUILD COMPLETE!
echo ============================================================
echo.
echo Executable created at:
echo   dist\ReportGenerator_Package\ReportGenerator.exe
echo.
echo Package contents:
echo   - ReportGenerator.exe (main application)
echo   - backend\config\ (report configurations)
echo   - backend\sample_data\ (sample CSV files)
echo   - generated_reports\ (output folder)
echo   - README.txt (instructions)
echo.
echo To distribute:
echo   1. Copy the entire "ReportGenerator_Package" folder
echo   2. Share with users
echo   3. They just double-click ReportGenerator.exe
echo.
echo Opening folder...
explorer "dist\ReportGenerator_Package"
echo.

pause
