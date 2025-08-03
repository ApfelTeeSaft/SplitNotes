@echo off
REM Windows Build Script for SplitNotes
REM Requires PyInstaller: pip install pyinstaller

echo Building SplitNotes for Windows...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Error: PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller. Please install manually: pip install pyinstaller
        pause
        exit /b 1
    )
)

REM Create build directory
if not exist "build" mkdir build
if not exist "dist" mkdir dist

REM Clean previous builds
if exist "build\*" (
    echo Cleaning previous builds...
    rmdir /s /q build
    mkdir build
)
if exist "dist\*" (
    rmdir /s /q dist
    mkdir dist
)

REM Check if resources folder exists and has files
if not exist "resources" (
    echo Creating resources folder...
    mkdir resources
    echo Note: Add icon files to resources folder for better appearance:
    echo   - app_icon.ico (Windows icon)
    echo   - green.png (connection active)
    echo   - red.png (connection inactive)
    echo   - settings_icon.png (settings window)
    set RESOURCES_EXIST=false
) else (
    dir /b "resources\*" >nul 2>&1
    if errorlevel 1 (
        echo Resources folder is empty...
        set RESOURCES_EXIST=false
    ) else (
        echo Found resources folder with files...
        set RESOURCES_EXIST=true
    )
)

REM Build the application
echo Building executable...

REM Set icon parameter if icon exists
if exist "resources\app_icon.ico" (
    echo Found app icon, including in build...
    set ICON_PARAM=--icon="%CD%\resources\app_icon.ico"
) else (
    echo No app icon found, building without custom icon...
    set ICON_PARAM=
)

REM Build with or without resources depending on availability
if "%RESOURCES_EXIST%"=="true" (
    echo Including resources in build...
    pyinstaller ^
        --onedir ^
        --windowed ^
        --name "SplitNotes" ^
        %ICON_PARAM% ^
        --add-data "%CD%\resources;resources" ^
        --hidden-import "tkinter" ^
        --hidden-import "tkinter.ttk" ^
        --hidden-import "tkinter.colorchooser" ^
        --hidden-import "tkinter.filedialog" ^
        --hidden-import "tkinter.messagebox" ^
        --hidden-import "socket" ^
        --hidden-import "threading" ^
        --hidden-import "json" ^
        --hidden-import "time" ^
        --hidden-import "select" ^
        --hidden-import "platform" ^
        --distpath "dist/windows" ^
        --workpath "build/windows" ^
        --specpath "build" ^
        main_window.py
) else (
    echo Building without resources...
    pyinstaller ^
        --onedir ^
        --windowed ^
        --name "SplitNotes" ^
        %ICON_PARAM% ^
        --hidden-import "tkinter" ^
        --hidden-import "tkinter.ttk" ^
        --hidden-import "tkinter.colorchooser" ^
        --hidden-import "tkinter.filedialog" ^
        --hidden-import "tkinter.messagebox" ^
        --hidden-import "socket" ^
        --hidden-import "threading" ^
        --hidden-import "json" ^
        --hidden-import "time" ^
        --hidden-import "select" ^
        --hidden-import "platform" ^
        --distpath "dist/windows" ^
        --workpath "build/windows" ^
        --specpath "build" ^
        main_window.py
)

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

REM Copy additional files
echo Copying additional files...
if exist "README.md" copy "README.md" "dist\windows\SplitNotes\" 2>nul
if exist "LICENSE" copy "LICENSE" "dist\windows\SplitNotes\" 2>nul

REM Create resources directory in dist and copy files if they exist
if not exist "dist\windows\SplitNotes\resources" mkdir "dist\windows\SplitNotes\resources"
if "%RESOURCES_EXIST%"=="true" (
    echo Copying resource files to distribution...
    if exist "resources\*.png" copy "resources\*.png" "dist\windows\SplitNotes\resources\" 2>nul
    if exist "resources\*.ico" copy "resources\*.ico" "dist\windows\SplitNotes\resources\" 2>nul
    if exist "resources\*.cfg" copy "resources\*.cfg" "dist\windows\SplitNotes\resources\" 2>nul
) else (
    echo No resource files to copy...
)

REM Create batch file for easy launching
echo @echo off > "dist\windows\SplitNotes\SplitNotes.bat"
echo cd /d "%%~dp0" >> "dist\windows\SplitNotes\SplitNotes.bat"
echo start "" "SplitNotes.exe" >> "dist\windows\SplitNotes\SplitNotes.bat"

REM Create ZIP package
echo Creating ZIP package...
if exist "dist\SplitNotes-Windows.zip" del "dist\SplitNotes-Windows.zip"
powershell -command "Compress-Archive -Path 'dist\windows\SplitNotes\*' -DestinationPath 'dist\SplitNotes-Windows.zip'"

if errorlevel 1 (
    echo Warning: Failed to create ZIP package. Please create manually.
)

echo.
echo ===============================================
echo Build completed successfully!
echo.
echo Executable location: dist\windows\SplitNotes\SplitNotes.exe
echo ZIP package: dist\SplitNotes-Windows.zip
echo.
echo To distribute:
echo 1. Copy the entire 'dist\windows\SplitNotes' folder
echo 2. Or use the ZIP package
echo.
echo Requirements for target systems:
echo - Windows 7 or later
echo - No Python installation required
echo ===============================================
echo.

REM Optional: Open the dist folder
set /p OPEN="Open build folder? (y/n): "
if /i "%OPEN%"=="y" explorer "dist\windows\SplitNotes"

pause