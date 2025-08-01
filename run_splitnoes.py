#!/usr/bin/env python3
"""
Cross-platform launcher for SplitNotes
This file can be used as an alternative entry point
"""

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_requirements():
    """Check if all required modules are available"""
    required_modules = ['tkinter', 'socket', 'threading', 'select']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("Error: Missing required modules:")
        for module in missing_modules:
            print(f"  - {module}")
        
        print("\nInstallation help:")
        if 'tkinter' in missing_modules:
            print("  Ubuntu/Debian: sudo apt install python3-tk")
            print("  Fedora/RHEL: sudo dnf install python3-tkinter")
            print("  Arch: sudo pacman -S python-tkinter")
            print("  macOS: tkinter should be included with Python")
            print("  Windows: tkinter should be included with Python")
        
        return False
    
    return True

def main():
    """Main entry point"""
    print("SplitNotes - Cross-platform LiveSplit notes viewer")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check if main_window.py exists
    main_window_path = os.path.join(current_dir, 'main_window.py')
    if not os.path.exists(main_window_path):
        print("Error: main_window.py not found in current directory")
        sys.exit(1)
    
    # Check if resources directory exists
    resources_path = os.path.join(current_dir, 'resources')
    if not os.path.exists(resources_path):
        print("Warning: resources/ directory not found")
        print("Creating resources directory...")
        try:
            os.makedirs(resources_path)
            print("Please add icon files to resources/ directory:")
            print("  - green.png (connection active)")
            print("  - red.png (connection inactive)")  
            print("  - settings_icon.png (settings window)")
        except OSError as e:
            print(f"Could not create resources directory: {e}")
    
    print("Starting SplitNotes...")
    print("Platform:", sys.platform)
    
    try:
        # Import and run the main application
        import main_window
        # main_window.main() is called automatically when imported
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()