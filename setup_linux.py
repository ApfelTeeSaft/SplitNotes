"""
Linux build setup using cx_Freeze
Run: python setup_linux.py build
"""

import sys
import os
from cx_Freeze import setup, Executable

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

# Dependencies are automatically detected, but some modules need help
build_options = {
    'packages': ['tkinter', 'socket', 'threading', 'select', 'os', 'sys', 'platform'],
    'excludes': ['matplotlib', 'numpy', 'scipy', 'PIL', 'pygame', 'PyQt5', 'PyQt6'],
    'include_files': [
        ('resources/', 'resources/'),
    ],
    'optimize': 2,
    'build_exe': 'build/linux',
}

executables = [
    Executable(
        'main_window.py',
        base=None,  # Console application base for Linux
        target_name='splitnotes',
        copyright=f'Copyright (c) 2024 {config.APP_AUTHOR}',
    )
]

setup(
    name=config.APP_NAME.lower(),
    version=config.APP_VERSION,
    description=config.APP_DESCRIPTION,
    author=config.APP_AUTHOR,
    options={'build_exe': build_options},
    executables=executables
)

# Alternative setup for creating a proper Linux package structure
def create_linux_package():
    """Create a proper Linux application structure"""
    import shutil
    import stat
    
    app_dir = f"build/{config.APP_NAME.lower()}"
    
    # Create directory structure
    os.makedirs(f"{app_dir}/bin", exist_ok=True)
    os.makedirs(f"{app_dir}/share/{config.APP_NAME.lower()}", exist_ok=True)
    os.makedirs(f"{app_dir}/share/applications", exist_ok=True)
    os.makedirs(f"{app_dir}/share/pixmaps", exist_ok=True)
    
    # Copy executable
    if os.path.exists("build/linux/splitnotes"):
        shutil.copy2("build/linux/splitnotes", f"{app_dir}/bin/")
        
        # Make executable
        st = os.stat(f"{app_dir}/bin/splitnotes")
        os.chmod(f"{app_dir}/bin/splitnotes", st.st_mode | stat.S_IEXEC)
    
    # Copy resources
    if os.path.exists("resources"):
        shutil.copytree("resources", f"{app_dir}/share/{config.APP_NAME.lower()}/resources", dirs_exist_ok=True)
    
    # Create .desktop file for Linux desktop integration
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={config.APP_NAME}
Comment={config.APP_DESCRIPTION}
Exec={app_dir}/bin/splitnotes
Icon={config.APP_NAME.lower()}
Categories=Utility;
Terminal=false
StartupNotify=true
"""
    
    with open(f"{app_dir}/share/applications/{config.APP_NAME.lower()}.desktop", 'w') as f:
        f.write(desktop_content)
    
    # Create launch script
    launch_script = f"""#!/bin/bash
DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" &> /dev/null && pwd )"
cd "$DIR"
./bin/splitnotes "$@"
"""
    
    with open(f"{app_dir}/{config.APP_NAME.lower()}", 'w') as f:
        f.write(launch_script)
    
    # Make launch script executable
    st = os.stat(f"{app_dir}/{config.APP_NAME.lower()}")
    os.chmod(f"{app_dir}/{config.APP_NAME.lower()}", st.st_mode | stat.S_IEXEC)
    
    print(f"Linux package created in {app_dir}/")
    print(f"Run with: ./{app_dir}/{config.APP_NAME.lower()}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "package":
        create_linux_package()
    else:
        # Standard build process
        pass