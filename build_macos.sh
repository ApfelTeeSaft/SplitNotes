#!/bin/bash
# macOS Build Script for SplitNotes
# Requires PyInstaller: pip install pyinstaller

echo "Building SplitNotes for macOS..."
echo

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script is for macOS only."
    exit 1
fi

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "Failed to install PyInstaller. Please install manually: pip3 install pyinstaller"
        exit 1
    fi
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
    echo "  - app_icon.icns (macOS icon)"
    echo "  - green.png (connection active)"
    echo "  - red.png (connection inactive)"
    echo "  - settings_icon.png (settings window)"
fi

# Build the application
echo "Building macOS app bundle..."

# Set icon parameter if icon exists
if [ -f "resources/app_icon.icns" ]; then
    echo "Found app icon, including in build..."
    ICON_PARAM="--icon=resources/app_icon.icns"
else
    echo "No app icon found, building without custom icon..."
    ICON_PARAM=""
fi

# Build with or without resources
if [ -d "resources" ] && [ "$(ls -A resources 2>/dev/null)" ]; then
    echo "Including resources folder in build..."
    python3 -m PyInstaller \
        --onedir \
        --windowed \
        --name "SplitNotes" \
else
    echo "Building without resources folder..."
    python3 -m PyInstaller \
        --onedir \
        --windowed \
        --name "SplitNotes" \
        $ICON_PARAM \
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
        --distpath "dist/macos" \
        --workpath "build/macos" \
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
        --distpath "dist/macos" \
        --workpath "build/macos" \
        --specpath "build" \
        main_window.py
else
    echo "Building without resources folder..."
    python3 -m PyInstaller \
        --onedir \
        --windowed \
        --name "SplitNotes" \
        $ICON_PARAM \
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
    --distpath "dist/macos" \
    --workpath "build/macos" \
    --specpath "build" \
    main_window.py

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

# Copy additional files to the app bundle
echo "Copying additional files..."
APP_DIR="dist/macos/SplitNotes.app"
CONTENTS_DIR="$APP_DIR/Contents"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

# Create proper app bundle structure
mkdir -p "$RESOURCES_DIR"

# Copy resources if they exist
if [ "$RESOURCES_EXIST" = true ]; then
    echo "Copying resource files to app bundle..."
    cp -r resources/* "$RESOURCES_DIR/" 2>/dev/null || true
else
    echo "No resource files to copy..."
    # Create empty resources directory for app to use
    mkdir -p "$RESOURCES_DIR"
fi

# Copy documentation
cp README.md "$RESOURCES_DIR/" 2>/dev/null || true
cp LICENSE "$RESOURCES_DIR/" 2>/dev/null || true

# Create Info.plist if it doesn't exist
INFO_PLIST="$CONTENTS_DIR/Info.plist"
if [ ! -f "$INFO_PLIST" ]; then
    cat > "$INFO_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>SplitNotes</string>
    <key>CFBundleDisplayName</key>
    <string>SplitNotes</string>
    <key>CFBundleIdentifier</key>
    <string>com.apfelteesaft.splitnotes</string>
    <key>CFBundleVersion</key>
    <string>1.1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.1.0</string>
    <key>CFBundleExecutable</key>
    <string>SplitNotes</string>
    <key>CFBundleIconFile</key>
    <string>app_icon.icns</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsLocalNetworking</key>
        <true/>
    </dict>
</dict>
</plist>
EOF
fi

# Set correct permissions
chmod +x "$APP_DIR/Contents/MacOS/SplitNotes"

# Code signing (optional, requires Apple Developer account)
echo "Checking for code signing..."
if command -v codesign >/dev/null 2>&1; then
    echo "Note: For distribution, you may want to code sign the app:"
    echo "  codesign --force --sign 'Developer ID Application: Your Name' '$APP_DIR'"
    echo "  Use --deep flag for embedded frameworks"
fi

# Create DMG (requires create-dmg tool)
echo "Creating DMG package..."
if command -v create-dmg >/dev/null 2>&1; then
    # Use icon if available, otherwise skip
    if [ -f "resources/app_icon.icns" ]; then
        VOLICON_PARAM="--volicon resources/app_icon.icns"
    else
        VOLICON_PARAM=""
    fi
    
    create-dmg \
        --volname "SplitNotes" \
        $VOLICON_PARAM \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "SplitNotes.app" 175 120 \
        --hide-extension "SplitNotes.app" \
        --app-drop-link 425 120 \
        "dist/SplitNotes-macOS.dmg" \
        "dist/macos/"
    
    if [ $? -eq 0 ]; then
        echo "DMG created successfully!"
    else
        echo "DMG creation failed. Creating ZIP instead..."
        cd dist/macos
        zip -r "../SplitNotes-macOS.zip" "SplitNotes.app"
        cd ../..
    fi
else
    echo "create-dmg not found. Creating ZIP package..."
    cd dist/macos
    zip -r "../SplitNotes-macOS.zip" "SplitNotes.app"
    cd ../..
fi

echo
echo "==============================================="
echo "Build completed successfully!"
echo
echo "App bundle location: dist/macos/SplitNotes.app"
if [ -f "dist/SplitNotes-macOS.dmg" ]; then
    echo "DMG package: dist/SplitNotes-macOS.dmg"
fi
if [ -f "dist/SplitNotes-macOS.zip" ]; then
    echo "ZIP package: dist/SplitNotes-macOS.zip"
fi
echo
echo "To distribute:"
echo "1. Copy the SplitNotes.app bundle"
echo "2. Or use the DMG/ZIP package"
echo
echo "Requirements for target systems:"
echo "- macOS 10.13 (High Sierra) or later"
echo "- No Python installation required"
echo
echo "Note: For distribution outside the App Store,"
echo "you may need to code sign and notarize the app."
echo "==============================================="
echo

# Optional: Open the dist folder
read -p "Open build folder? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "dist/macos"
fi