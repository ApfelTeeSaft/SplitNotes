@echo off
setlocal enabledelayedexpansion

REM SplitNotes Windows Setup Script
REM ================================

echo.
echo SplitNotes Windows Setup
echo ========================
echo.

REM Parse command line argument
set "COMMAND=%~1"
if "%COMMAND%"=="" set "COMMAND=setup"

REM Jump to appropriate section
if /i "%COMMAND%"=="setup" goto :main_setup
if /i "%COMMAND%"=="check" goto :check_system
if /i "%COMMAND%"=="build" goto :build_app
if /i "%COMMAND%"=="run" goto :run_app
if /i "%COMMAND%"=="test" goto :test_app
if /i "%COMMAND%"=="clean" goto :clean_build
if /i "%COMMAND%"=="help" goto :show_help
if /i "%COMMAND%"=="-h" goto :show_help
if /i "%COMMAND%"=="--help" goto :show_help

echo Error: Unknown command "%COMMAND%"
goto :show_help

:main_setup
echo [INFO] Starting full setup...
call :check_system
if errorlevel 1 exit /b 1
call :setup_resources
call :test_app
if errorlevel 1 exit /b 1
echo.
echo [SUCCESS] Setup complete!
echo.
echo Next steps:
echo   1. Replace placeholder icons in resources\ with actual PNG files
echo   2. Install LiveSplit Server component
echo   3. Run: setup.bat run
echo.
echo To build executable: setup.bat build
goto :end

:check_system
echo [INFO] Checking system requirements...

REM Check for Python
set "PYTHON_CMD="
python --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
    set "PYTHON_CMD=python"
) else (
    python3 --version >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set "PYTHON_VERSION=%%i"
        set "PYTHON_CMD=python3"
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python not found!
    echo Please install Python 3.6+ from python.org
    echo Make sure to check "Add Python to PATH" during installation
    exit /b 1
)

echo [SUCCESS] Python found: %PYTHON_CMD% ^(%PYTHON_VERSION%^)

REM Check Python version (basic check for 3.x)
echo %PYTHON_VERSION% | findstr /r "^3\." >nul
if errorlevel 1 (
    echo [ERROR] Python 3.6+ required, found %PYTHON_VERSION%
    exit /b 1
)

REM Check required modules
echo [INFO] Checking required modules...

%PYTHON_CMD% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] tkinter not available
    echo tkinter should be included with Python. Try reinstalling Python.
    exit /b 1
) else (
    echo [SUCCESS] tkinter available
)

for %%m in (socket threading select os sys platform) do (
    %PYTHON_CMD% -c "import %%m" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] %%m not available
        exit /b 1
    ) else (
        echo [SUCCESS] %%m available
    )
)

goto :eof

:setup_resources
echo [INFO] Setting up resources directory...

if not exist "resources" (
    mkdir resources
    echo [SUCCESS] Created resources directory
)

REM Create placeholder files if they don't exist
for %%f in (green.png red.png settings_icon.png) do (
    if not exist "resources\%%f" (
        echo. > "resources\%%f"
        echo [WARNING] Created placeholder resources\%%f
    ) else (
        echo [SUCCESS] resources\%%f exists
    )
)

echo [WARNING] Icon files are placeholders
echo [INFO] Replace with actual PNG icons for proper functionality

goto :eof

:test_app
echo [INFO] Testing application...

echo [INFO] Testing module imports...
%PYTHON_CMD% -c "import config; import ls_connection; import note_reader; import setting_handler; print('All modules imported successfully')" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Module import failed
    exit /b 1
) else (
    echo [SUCCESS] Module imports working
)

echo [INFO] Testing note parsing...
echo Test note 1> test_notes.txt
echo.>> test_notes.txt
echo Test note 2>> test_notes.txt

%PYTHON_CMD% -c "import note_reader; notes = note_reader.get_notes('test_notes.txt', 'new_line'); print(f'Parsed {len(notes)} notes successfully')" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Note parsing failed
    del test_notes.txt >nul 2>&1
    exit /b 1
) else (
    echo [SUCCESS] Note parsing working
)

del test_notes.txt >nul 2>&1
echo [SUCCESS] Application tests passed

goto :eof

:build_app
echo [INFO] Building Windows executable...

call :check_system
if errorlevel 1 exit /b 1

echo [INFO] Installing build dependencies...
%PYTHON_CMD% -m pip install cx_Freeze
if errorlevel 1 (
    echo [ERROR] Failed to install cx_Freeze
    exit /b 1
)

echo [INFO] Building executable...
%PYTHON_CMD% setup_windows.py build
if errorlevel 1 (
    echo [ERROR] Build failed
    exit /b 1
)

echo [SUCCESS] Windows build complete!
echo Check the build\ directory for your executable

goto :end

:run_app
echo [INFO] Running SplitNotes from source...
call :check_system
if errorlevel 1 exit /b 1

echo [INFO] Starting SplitNotes... (Press Ctrl+C to stop)
%PYTHON_CMD% main_window.py

goto :end

:clean_build
echo [INFO] Cleaning build artifacts...

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.egg-info" rmdir /s /q "*.egg-info"

for /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)

del /s /q "*.pyc" >nul 2>&1
del /s /q "*.pyo" >nul 2>&1

echo [SUCCESS] Build artifacts cleaned

goto :end

:show_help
echo SplitNotes Windows Setup Script
echo ================================
echo.
echo Usage: setup.bat [command]
echo.
echo Commands:
echo   setup      - Full setup ^(check deps, create resources, test^)
echo   check      - Check system requirements only
echo   build      - Install build dependencies and build
echo   run        - Run the application
echo   test       - Test the application
echo   clean      - Clean build artifacts
echo   help       - Show this help message
echo.
echo Examples:
echo   setup.bat setup    # First time setup
echo   setup.bat run      # Run the application
echo   setup.bat build    # Build executable
echo.

goto :end

:end
echo.
pause