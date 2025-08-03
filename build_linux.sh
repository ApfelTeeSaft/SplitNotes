#!/bin/bash
# Linux Build Script for SplitNotes
# Requires PyInstaller: pip install pyinstaller

echo "Building SplitNotes for Linux..."
echo

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        ARCH_NAME="x64"
        ;;
    i386|i686)
        ARCH_NAME="x86"
        ;;
    aarch64|arm64)
        ARCH_NAME="arm64"
        ;;
    armv7l)
        ARCH_NAME="armv7"
        ;;
    *)
        ARCH_NAME="$ARCH"
        ;;
esac

echo "Detected architecture: $ARCH ($ARCH_NAME)"

# Check if we're on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Warning: This script is designed for Linux. Continuing anyway..."
fi

# Check Python version
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "Error: Python not found. Please install Python 3.6 or later."
        exit 1
    fi
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -Po '(?<=Python )[0-9]+\.[0-9]+')
if ! $PYTHON_CMD -c "import sys; sys.exit(0 if sys.version_info >= (3,6) else 1)"; then
    echo "Error: Python 3.6 or later is required. Found: $($PYTHON_CMD --version)"
    exit 1
fi

# Check if PyInstaller is installed
if ! $PYTHON_CMD -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    $PYTHON_CMD -m pip install pyinstaller --user
    if [ $? -ne 0 ]; then
        echo "Failed to install PyInstaller. Trying with sudo..."
        sudo $PYTHON_CMD -m pip install pyinstaller
        if [ $? -ne 0 ]; then
            echo "Failed to install PyInstaller. Please install manually:"
            echo "  pip3 install pyinstaller"
            exit 1
        fi
    fi
fi

# Check for required system packages
echo "Checking system dependencies..."
MISSING_DEPS=()

# Check for tkinter
if ! $PYTHON_CMD -c "import tkinter" 2>/dev/null; then
    MISSING_DEPS+=("python3-tk")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "Missing dependencies detected:"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "  - $dep"
    done
    echo
    echo "Install with your package manager:"
    echo "  Ubuntu/Debian: sudo apt install ${MISSING_DEPS[*]}"
    echo "  Fedora/RHEL:   sudo dnf install python3-tkinter"
    echo "  Arch:          sudo pacman -S tk"
    echo "  openSUSE:      sudo zypper install python3-tk"
    exit 1
fi

# Create build directories
mkdir -p build dist

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/*
rm -rf dist/*

# Check if resources folder exists, create if not
if [ ! -d "resources" ]; then
    echo "Creating resources folder..."
    mkdir -p resources
    echo "Note: Add icon files to resources folder for better appearance:"
    echo "  - app_icon.png (Linux icon, 256x256px recommended)"
    echo "  - green.png (connection active)"
    echo "  - red.png (connection inactive)"
    echo "  - settings_icon.png (settings window)"
fi

# Build the application
echo "Building Linux executable..."

# Build with or without resources
if [ -d "resources" ] && [ "$(ls -A resources 2>/dev/null)" ]; then
    echo "Including resources folder in build..."
    $PYTHON_CMD -m PyInstaller \
        --onedir \
        --console \
else
    echo "Building without resources folder..."
    $PYTHON_CMD -m PyInstaller \
        --onedir \
        --console \
        --name "SplitNotes" \
        --hidden-import "tkinter" \
        --hidden-import "tkinter.ttk" \
        --hidden-import "tkinter.colorchooser" \
        --hidden-import "tkinter.filedialog" \
        --hidden-import "tkinter.messagebox" \
        --hidden-import "socket" \
        --hidden-import "threading" \
        --hidden-import "json" \
        --hidden-import "time" \
        --hidden-import "select" \
        --hidden-import "platform" \
        --distpath "dist/linux" \
        --workpath "build/linux" \
        --specpath "build" \
        main_window.py
fi
        --add-data "resources:resources" \
        --hidden-import "tkinter" \
        --hidden-import "tkinter.ttk" \
        --hidden-import "tkinter.colorchooser" \
        --hidden-import "tkinter.filedialog" \
        --hidden-import "tkinter.messagebox" \
        --hidden-import "socket" \
        --hidden-import "threading" \
        --hidden-import "json" \
        --hidden-import "time" \
        --hidden-import "select" \
        --hidden-import "platform" \
        --distpath "dist/linux" \
        --workpath "build/linux" \
        --specpath "build" \
        main_window.py
else
    echo "Building without resources folder..."
    $PYTHON_CMD -m PyInstaller \
        --onedir \
        --console \
        --name "SplitNotes" \
    --hidden-import "tkinter" \
    --hidden-import "tkinter.ttk" \
    --hidden-import "tkinter.colorchooser" \
    --hidden-import "tkinter.filedialog" \
    --hidden-import "tkinter.messagebox" \
    --hidden-import "socket" \
    --hidden-import "threading" \
    --hidden-import "json" \
    --hidden-import "time" \
    --hidden-import "select" \
    --hidden-import "platform" \
    --distpath "dist/linux" \
    --workpath "build/linux" \
    --specpath "build" \
    main_window.py

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

# Create proper directory structure
DIST_DIR="dist/linux/SplitNotes-linux-$ARCH_NAME"
mkdir -p "$DIST_DIR"

# Move the built application
mv "dist/linux/SplitNotes"/* "$DIST_DIR/"
rmdir "dist/linux/SplitNotes"

# Copy additional files
echo "Copying additional files..."
cp README.md "$DIST_DIR/" 2>/dev/null || true
cp LICENSE "$DIST_DIR/" 2>/dev/null || true

# Copy resources if they exist
if [ "$RESOURCES_EXIST" = true ]; then
    echo "Copying resource files to distribution..."
    cp -r resources "$DIST_DIR/" 2>/dev/null || true
else
    echo "No resource files to copy..."
    # Create empty resources directory for app to use
    mkdir -p "$DIST_DIR/resources"
fi

# Create launch script
cat > "$DIST_DIR/splitnotes.sh" << 'EOF'
#!/bin/bash
# SplitNotes Launch Script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Set library path for the executable
export LD_LIBRARY_PATH="$SCRIPT_DIR:$LD_LIBRARY_PATH"

# Launch SplitNotes
if [ -f "./SplitNotes" ]; then
    ./SplitNotes "$@"
else
    echo "Error: SplitNotes executable not found!"
    exit 1
fi
EOF

# Make scripts executable
chmod +x "$DIST_DIR/splitnotes.sh"
chmod +x "$DIST_DIR/SplitNotes"

# Create desktop entry
cat > "$DIST_DIR/SplitNotes.desktop" << EOF
[Desktop Entry]
Type=Application
Name=SplitNotes
Comment=LiveSplit notes synchronization tool
Exec=$DIST_DIR/splitnotes.sh
Icon=$DIST_DIR/resources/app_icon.png
Terminal=false
Categories=Utility;Game;
StartupWMClass=SplitNotes
EOF

# Create installation script
cat > "$DIST_DIR/install.sh" << 'EOF'
#!/bin/bash
# SplitNotes Installation Script

INSTALL_DIR="$HOME/.local/share/SplitNotes"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Installing SplitNotes..."

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# Copy files
cp -r * "$INSTALL_DIR/"

# Create symlink in bin directory
ln -sf "$INSTALL_DIR/splitnotes.sh" "$BIN_DIR/splitnotes"

# Install desktop entry
cp "$INSTALL_DIR/SplitNotes.desktop" "$DESKTOP_DIR/"
sed -i "s|$PWD|$INSTALL_DIR|g" "$DESKTOP_DIR/SplitNotes.desktop"

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR"
fi

echo "Installation completed!"
echo "SplitNotes installed to: $INSTALL_DIR"
echo "You can now run 'splitnotes' from terminal or find it in your applications menu."
EOF

chmod +x "$DIST_DIR/install.sh"

# Create AppImage (if appimagetool is available)
echo "Checking for AppImage creation tools..."
if command -v appimagetool &> /dev/null; then
    echo "Creating AppImage..."
    
    APPDIR="dist/SplitNotes.AppDir"
    mkdir -p "$APPDIR/usr/bin"
    mkdir -p "$APPDIR/usr/share/applications"
    mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
    
    # Copy files to AppDir
    cp -r "$DIST_DIR"/* "$APPDIR/usr/bin/"
    
    # Create AppRun
    cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin/:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin/:${LD_LIBRARY_PATH}"
cd "${HERE}/usr/bin"
exec ./SplitNotes "$@"
EOF
    chmod +x "$APPDIR/AppRun"
    
    # Copy desktop file and icon
    cp "$DIST_DIR/SplitNotes.desktop" "$APPDIR/"
    if [ -f "resources/app_icon.png" ]; then
        cp "resources/app_icon.png" "$APPDIR/splitnotes.png"
        cp "resources/app_icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/"
    fi
    
    # Update desktop file paths
    sed -i 's|Exec=.*|Exec=SplitNotes|g' "$APPDIR/SplitNotes.desktop"
    sed -i 's|Icon=.*|Icon=splitnotes|g' "$APPDIR/SplitNotes.desktop"
    
    # Create AppImage
    appimagetool "$APPDIR" "dist/SplitNotes-linux-$ARCH_NAME.AppImage"
    
    if [ $? -eq 0 ]; then
        echo "AppImage created successfully!"
        chmod +x "dist/SplitNotes-linux-$ARCH_NAME.AppImage"
    fi
fi

# Create tarball
echo "Creating tarball..."
cd dist/linux
tar -czf "../SplitNotes-linux-$ARCH_NAME.tar.gz" "SplitNotes-linux-$ARCH_NAME"
cd ../..

echo
echo "==============================================="
echo "Build completed successfully!"
echo
echo "Executable location: $DIST_DIR/SplitNotes"
echo "Launch script: $DIST_DIR/splitnotes.sh"
echo "Tarball: dist/SplitNotes-linux-$ARCH_NAME.tar.gz"
if [ -f "dist/SplitNotes-linux-$ARCH_NAME.AppImage" ]; then
    echo "AppImage: dist/SplitNotes-linux-$ARCH_NAME.AppImage"
fi
echo
echo "To install locally:"
echo "  cd '$DIST_DIR' && ./install.sh"
echo
echo "To distribute:"
echo "1. Copy the entire '$DIST_DIR' folder"
echo "2. Or use the tarball/AppImage"
echo
echo "Requirements for target systems:"
echo "- Linux with glibc 2.17+ (RHEL 7+, Ubuntu 14.04+)"
echo "- X11 display server"
echo "- No Python installation required"
echo "==============================================="
echo

# Optional: Open the dist folder
read -p "Open build folder? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "dist/linux"
    elif command -v nautilus &> /dev/null; then
        nautilus "dist/linux"
    else
        echo "Build folder: $(pwd)/dist/linux"
    fi
fi