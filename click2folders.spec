# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(5000)

block_cipher = None

a = Analysis(
    ['click2folders.py'],
    pathex=['C:\\Users\\Usuario\\Desktop\\click2folder'],
    binaries=[],
    datas=[
        ('favicon.ico', '.'),
        ('Cansado4.jpg', '.'),
        ('Limites1.jpg', '.')
    ],
    hiddenimports=['PIL', 'win32com', 'win32com.client', 'win32com.client.makepy', 'win32com.client.gencache', 'win32com.client.dynamic', 'pythoncom', 'win32timezone', 'win32file'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='click2folders',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['favicon.ico'],
    version='version_info.txt',
    onefile=True  # Habilitar modo onefile para un solo .exe
)