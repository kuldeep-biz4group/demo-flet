"""
Build executable for Offline Report Generation System
Using PyInstaller with --onefile --windowed format
"""
import os
import sys
import shutil
import subprocess

def clean_build():
    """Clean previous build artifacts"""
    print("[1/5] Cleaning previous builds...")
    
    folders_to_remove = ['build', 'dist']
    files_to_remove = ['ReportGenerator.spec']
    
    for folder in folders_to_remove:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"  ✓ Removed {folder}/")
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"  ✓ Removed {file}")
    
    print()

def install_pyinstaller():
    """Install PyInstaller if not present"""
    print("[2/5] Checking PyInstaller...")
    
    try:
        import PyInstaller
        print("  ✓ PyInstaller already installed")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("  ✓ PyInstaller installed")
    
    print()

def build_executable():
    """Build the executable using PyInstaller"""
    print("[3/5] Building executable...")
    print("  This may take 2-5 minutes...")
    print()
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=ReportGenerator",
        "--add-data=backend;backend",
        
        # Hidden imports for all dependencies
        "--hidden-import=flet",
        "--hidden-import=fastapi",
        "--hidden-import=uvicorn",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=reportlab",
        "--hidden-import=numpy",
        
        # Backend modules
        "--hidden-import=backend.core.config_loader",
        "--hidden-import=backend.core.data_processor",
        "--hidden-import=backend.core.delta_calculator",
        "--hidden-import=backend.core.risk_analyzer",
        "--hidden-import=backend.core.pdf_engine",
        "--hidden-import=backend.core.error_handler",
        
        # Collect all package data
        "--collect-all=flet",
        "--collect-all=reportlab",
        
        # Main script
        "frontend/main.py"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("  ✓ Build successful!")
        print()
        return True
    except subprocess.CalledProcessError as e:
        print("  ✗ Build failed!")
        print(f"  Error: {e}")
        if e.stderr:
            print(f"  Details: {e.stderr}")
        return False

def create_package():
    """Create distribution package with all required files"""
    print("[4/5] Creating distribution package...")
    
    # Create package directory
    package_dir = "dist/ReportGenerator_Package"
    os.makedirs(package_dir, exist_ok=True)
    
    # Copy executable
    exe_src = "dist/ReportGenerator.exe"
    exe_dst = os.path.join(package_dir, "ReportGenerator.exe")
    if os.path.exists(exe_src):
        shutil.copy2(exe_src, exe_dst)
        print(f"  ✓ Copied executable")
    else:
        print(f"  ✗ Executable not found at {exe_src}")
        return False
    
    # Copy backend config
    config_src = "backend/config"
    config_dst = os.path.join(package_dir, "backend/config")
    if os.path.exists(config_src):
        shutil.copytree(config_src, config_dst, dirs_exist_ok=True)
        print(f"  ✓ Copied configuration files")
    
    # Copy sample data
    sample_src = "backend/sample_data"
    sample_dst = os.path.join(package_dir, "backend/sample_data")
    if os.path.exists(sample_src):
        shutil.copytree(sample_src, sample_dst, dirs_exist_ok=True)
        print(f"  ✓ Copied sample data")
    
    # Create output folder
    reports_dir = os.path.join(package_dir, "generated_reports")
    os.makedirs(reports_dir, exist_ok=True)
    print(f"  ✓ Created output folder")
    
    # Create README
    readme_content = """Offline Report Generator

HOW TO USE:
1. Double-click ReportGenerator.exe
2. Select your CSV/Excel file
3. Choose report type and variant
4. Click "Generate Reports"
5. Find PDFs in generated_reports folder

SAMPLE DATA:
Test files are in backend/sample_data/:
- progress_monitoring_sample.csv
- screening_sample.csv

SYSTEM REQUIREMENTS:
- Windows 10 or later
- No Python installation required
- No internet connection required

GENERATED REPORTS:
All PDF reports are saved in the generated_reports folder.

TROUBLESHOOTING:
- If Windows Defender blocks: Right-click .exe → Properties → Unblock
- Run as Administrator if needed
- Check antivirus settings

Enjoy generating professional assessment reports!
"""
    
    readme_path = os.path.join(package_dir, "README.txt")
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    print(f"  ✓ Created README.txt")
    
    print()
    return True

def print_summary():
    """Print build summary"""
    print("[5/5] Build Summary")
    print()
    print("=" * 60)
    print("  BUILD COMPLETE!")
    print("=" * 60)
    print()
    
    package_dir = os.path.abspath("dist/ReportGenerator_Package")
    print(f"Executable location:")
    print(f"  {package_dir}")
    print()
    
    print("Package contents:")
    print("  ✓ ReportGenerator.exe (main application)")
    print("  ✓ backend/config/ (report configurations)")
    print("  ✓ backend/sample_data/ (sample CSV files)")
    print("  ✓ generated_reports/ (output folder)")
    print("  ✓ README.txt (user instructions)")
    print()
    
    # Get file size
    exe_path = os.path.join(package_dir, "ReportGenerator.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"Executable size: {size_mb:.1f} MB")
        print()
    
    print("To distribute:")
    print("  1. Copy the entire 'ReportGenerator_Package' folder")
    print("  2. Share with users (zip it for easy transfer)")
    print("  3. Users just double-click ReportGenerator.exe")
    print()
    
    print("To test:")
    print("  1. Go to dist/ReportGenerator_Package/")
    print("  2. Double-click ReportGenerator.exe")
    print("  3. Test with sample data files")
    print()
    
    print("=" * 60)
    print()

def main():
    """Main build process"""
    print("=" * 60)
    print("  Building Offline Report Generator Executable")
    print("=" * 60)
    print()
    
    # Step 1: Clean
    clean_build()
    
    # Step 2: Install PyInstaller
    install_pyinstaller()
    
    # Step 3: Build
    if not build_executable():
        print("✗ Build failed!")
        input("Press Enter to exit...")
        return False
    
    # Step 4: Create package
    if not create_package():
        print("✗ Package creation failed!")
        input("Press Enter to exit...")
        return False
    
    # Step 5: Summary
    print_summary()
    
    # Open folder
    try:
        package_dir = os.path.abspath("dist/ReportGenerator_Package")
        if sys.platform == "win32":
            os.startfile(package_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", package_dir])
        else:
            subprocess.Popen(["xdg-open", package_dir])
        print("Opening package folder...")
    except:
        pass
    
    print("✓ Build successful!")
    input("Press Enter to exit...")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)
