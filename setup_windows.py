"""
Windows build setup using cx_Freeze (preferred) or py2exe
Run: python setup_windows.py build
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
    'excludes': ['matplotlib', 'numpy', 'scipy', 'PIL', 'pygame'],
    'include_files': [
        ('resources/', 'resources/'),
    ],
    'optimize': 2,
}

# Base for Windows GUI application (no console window)
base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable(
        'main_window.py',
        base=base,
        target_name='SplitNotes.exe',
        icon=None,  # Add icon path here if you have one
        copyright=f'Copyright (c) 2024 {config.APP_AUTHOR}',
    )
]

setup(
    name=config.APP_NAME,
    version=config.APP_VERSION,
    description=config.APP_DESCRIPTION,
    author=config.APP_AUTHOR,
    options={'build_exe': build_options},
    executables=executables
)

# Alternative py2exe setup (uncomment if cx_Freeze is not available)
"""
from distutils.core import setup
import py2exe

setup(
    windows=[{
        'script': 'main_window.py',
        'dest_base': 'SplitNotes',
        'copyright': f'Copyright (c) 2024 {config.APP_AUTHOR}',
    }],
    options={
        'py2exe': {
            'bundle_files': 2,
            'compressed': True,
            'optimize': 2,
            'excludes': ['matplotlib', 'numpy', 'scipy', 'PIL', 'pygame'],
        }
    },
    zipfile=None,
    data_files=[
        ('resources', [
            'resources/green.png',
            'resources/red.png',
            'resources/settings_icon.png'
        ])
    ]
)
"""