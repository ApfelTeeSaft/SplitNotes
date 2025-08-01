"""
macOS build setup using py2app
Run: python setup_mac.py py2app
"""

import sys
import os
from setuptools import setup

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

APP = ['main_window.py']
DATA_FILES = [
    ('resources', [
        'resources/green.png',
        'resources/red.png',
        'resources/settings_icon.png'
    ])
]

OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': config.APP_NAME,
        'CFBundleDisplayName': config.APP_NAME,
        'CFBundleGetInfoString': config.APP_DESCRIPTION,
        'CFBundleIdentifier': 'com.ApfelTeeSaft.splitnotes',
        'CFBundleVersion': config.APP_VERSION,
        'CFBundleShortVersionString': config.APP_VERSION,
        'NSHumanReadableCopyright': f'Copyright (c) 2024 {config.APP_AUTHOR}',
        'NSHighResolutionCapable': True,
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    },
    'packages': ['tkinter'],
    'excludes': ['matplotlib', 'numpy', 'scipy', 'PIL', 'pygame'],
    'resources': DATA_FILES,
    'optimize': 2,
}

setup(
    name=config.APP_NAME,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    author=config.APP_AUTHOR,
    version=config.APP_VERSION,
    description=config.APP_DESCRIPTION,
    license='MIT',
    url='https://github.com/ApfelTeeSaft/SplitNotes',
)