# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\DESCARGAS\\BACKUP 2\\MIS PROGRAMAS\\Click2folders\\click2folders.py'],
    pathex=[],
    binaries=[],
    datas=[('BAUL', 'BAUL'), ('D:\\DESCARGAS\\BACKUP 2\\MIS PROGRAMAS\\Click2folders\\favicon.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
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
    icon=['D:\\DESCARGAS\\BACKUP 2\\MIS PROGRAMAS\\Click2folders\\favicon.ico'],
    version='D:\\DESCARGAS\\BACKUP 2\\MIS PROGRAMAS\\Click2folders\\version_info.txt',
)
