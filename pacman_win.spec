# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# Get the current directory
current_dir = os.getcwd()

# Collect all necessary data files
datas = [
    ('data/maze.json', 'data'),
    ('src/fonts', 'src/fonts'),
    ('assets/sprites', 'assets/sprites')
]

# Add hidden imports
hiddenimports = [
    'pygame',
    'pygame._sdl2',
    'pygame._sdl2.controller',
    'pygame._sdl2.mixer',
    'json',
    'os',
    'sys',
    'math',
    'random',
    'heapq',
    'collections'
]

a = Analysis(
    ['src/main.py'],
    pathex=[current_dir],  # Use current directory
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'test', 'unittest', 'email', 'xml', 'pydoc', 'pdb'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Pacman',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/sprites/pacman.ico' if os.path.exists('assets/sprites/pacman.ico') else None,
)

# For folder distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PacmanGame',
)