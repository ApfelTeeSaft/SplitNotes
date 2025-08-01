#!/bin/bash

# SplitNotes Cross-Platform Setup Script
# This script helps set up SplitNotes on different platforms

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Detect operating system
detect_os() {
    case "$OSTYPE" in
        darwin*)  OS="macos" ;;
        linux*)   OS="linux" ;;
        msys*|cygwin*|mingw*) OS="windows" ;;
        *)        OS="unknown" ;;
    esac
    
    print_info "Detected OS: $OS"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
check_python() {
    print_header "Checking Python Installation"
    
    PYTHON_CMD=""
    
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1)
        if [ "$PYTHON_VERSION" = "3" ]; then
            PYTHON_CMD="python"
        fi
    fi
    
    if [ -z "$PYTHON_CMD" ]; then
        print_error "Python 3 not found!"
        echo "Please install Python 3.6 or higher:"
        case $OS in
            "linux")
                echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-tk"
                echo "  Fedora/RHEL: sudo dnf install python3 python3-pip python3-tkinter"
                echo "  Arch: sudo pacman -S python python-pip python-tkinter"
                ;;
            "macos")
                echo "  Install from python.org or use Homebrew: brew install python-tk"
                ;;
            "windows")
                echo "  Download from python.org (make sure to check 'Add to PATH')"
                ;;
        esac
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    print_success "Python found: $PYTHON_CMD ($PYTHON_VERSION)"
    
    # Check if version is 3.6+
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 6 ]; then
        print_success "Python version is compatible"
    else
        print_error "Python 3.6+ required, found $PYTHON_VERSION"
        exit 1
    fi
}

# Check required modules
check_modules() {
    print_header "Checking Required Modules"
    
    MISSING_MODULES=""
    
    # Check tkinter
    if ! $PYTHON_CMD -c "import tkinter" 2>/dev/null; then
        MISSING_MODULES="$MISSING_MODULES tkinter"
        print_error "tkinter not available"
    else
        print_success "tkinter available"
    fi
    
    # Check other standard library modules
    for module in socket threading select os sys platform; do
        if ! $PYTHON_CMD -c "import $module" 2>/dev/null; then
            MISSING_MODULES="$MISSING_MODULES $module"
            print_error "$module not available"
        else
            print_success "$module available"
        fi
    done
    
    if [ -n "$MISSING_MODULES" ]; then
        print_error "Missing required modules:$MISSING_MODULES"
        
        case $OS in
            "linux")
                if [[ $MISSING_MODULES == *"tkinter"* ]]; then
                    echo "Install tkinter with:"
                    echo "  Ubuntu/Debian: sudo apt install python3-tk"
                    echo "  Fedora/RHEL: sudo dnf install python3-tkinter"
                    echo "  Arch: sudo pacman -S python-tkinter"
                fi
                ;;
            "macos"|"windows")
                echo "tkinter should be included with Python. Try reinstalling Python."
                ;;
        esac
        exit 1
    fi
}

# Create resources directory
setup_resources() {
    print_header "Setting Up Resources"
    
    if [ ! -d "resources" ]; then
        mkdir -p resources
        print_success "Created resources directory"
    fi
    
    # Create placeholder icon files if they don't exist
    for icon in green.png red.png settings_icon.png; do
        if [ ! -f "resources/$icon" ]; then
            touch "resources/$icon"
            print_warning "Created placeholder resources/$icon"
        else
            print_success "resources/$icon exists"
        fi
    done
    
    if [ -f "resources/green.png" ] && [ ! -s "resources/green.png" ]; then
        print_warning "Icon files are empty placeholders"
        print_info "Replace with actual PNG icons for proper functionality"
    fi
}

# Install build dependencies
install_build_deps() {
    print_header "Installing Build Dependencies"
    
    PIP_CMD=""
    if command_exists pip3; then
        PIP_CMD="pip3"
    elif command_exists pip; then
        PIP_CMD="pip"
    else
        print_error "pip not found!"
        exit 1
    fi
    
    case $OS in
        "windows")
            print_info "Installing Windows build tools..."
            $PIP_CMD install cx_Freeze
            print_success "Windows build tools installed"
            ;;
        "macos")
            print_info "Installing macOS build tools..."
            $PIP_CMD install py2app
            print_success "macOS build tools installed"
            ;;
        "linux")
            print_info "Installing Linux build tools..."
            $PIP_CMD install cx_Freeze
            print_success "Linux build tools installed"
            ;;
    esac
}

# Test the application
test_app() {
    print_header "Testing Application"
    
    print_info "Testing module imports..."
    if $PYTHON_CMD -c "
import config
import ls_connection
import note_reader  
import setting_handler
print('All modules imported successfully')
" 2>/dev/null; then
        print_success "Module imports working"
    else
        print_error "Module import failed"
        exit 1
    fi
    
    print_info "Testing note parsing..."
    echo -e "Test note 1\n\nTest note 2" > test_notes.txt
    if $PYTHON_CMD -c "
import note_reader
notes = note_reader.get_notes('test_notes.txt', 'new_line')
print(f'Parsed {len(notes)} notes successfully')
" 2>/dev/null; then
        print_success "Note parsing working"
    else
        print_error "Note parsing failed"
    fi
    rm -f test_notes.txt
    
    print_success "Application tests passed"
}

# Build application
build_app() {
    print_header "Building Application"
    
    case $OS in
        "windows")
            print_info "Building Windows executable..."
            $PYTHON_CMD setup_windows.py build
            print_success "Windows build complete (check build/ directory)"
            ;;
        "macos")
            print_info "Building macOS application..."
            $PYTHON_CMD setup_mac.py py2app
            print_success "macOS build complete (check dist/ directory)"
            ;;
        "linux")
            print_info "Building Linux executable..."
            $PYTHON_CMD setup_linux.py build
            $PYTHON_CMD setup_linux.py package
            print_success "Linux build complete (check build/ directory)"
            ;;
    esac
}

# Run the application
run_app() {
    print_header "Running SplitNotes"
    
    print_info "Starting SplitNotes from source..."
    print_info "Press Ctrl+C to stop"
    $PYTHON_CMD main_window.py
}

# Show usage information
show_usage() {
    echo "SplitNotes Setup Script"
    echo "======================"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup      - Full setup (check deps, create resources, test)"
    echo "  check      - Check system requirements only"
    echo "  build      - Install build dependencies and build"
    echo "  run        - Run the application"
    echo "  test       - Test the application"
    echo "  clean      - Clean build artifacts"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup    # First time setup"
    echo "  $0 run      # Run the application"
    echo "  $0 build    # Build executable"
    echo ""
}

# Clean build artifacts
clean_build() {
    print_header "Cleaning Build Artifacts"
    
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    
    print_success "Build artifacts cleaned"
}

# Main setup function
main_setup() {
    print_header "SplitNotes Setup"
    
    detect_os
    check_python
    check_modules
    setup_resources
    test_app
    
    print_header "Setup Complete!"
    print_success "SplitNotes is ready to use"
    echo ""
    print_info "Next steps:"
    echo "  1. Replace placeholder icons in resources/ with actual PNG files"
    echo "  2. Install LiveSplit Server component"
    echo "  3. Run: $0 run"
    echo ""
    print_info "To build executable: $0 build"
}

# Parse command line arguments
case "${1:-setup}" in
    "setup")
        main_setup
        ;;
    "check")
        detect_os
        check_python
        check_modules
        ;;
    "build")
        detect_os
        check_python
        install_build_deps
        build_app
        ;;
    "run")
        detect_os
        check_python
        run_app
        ;;
    "test")
        detect_os
        check_python
        test_app
        ;;
    "clean")
        clean_build
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac