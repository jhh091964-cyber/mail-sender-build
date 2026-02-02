# -*- mode: python ; coding: utf-8 -*-

import certifi

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (certifi.where(), 'certifi'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'requests',
        'paramiko',
        'certifi',
        'socks',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # ✅ Qt 瘦身：排除你通常用不到、但體積很大的模組
    # （只要你的程式沒有內嵌瀏覽器/影音/地圖/3D/藍牙/圖表，這些都可安全排除）
    excludes=[
        # WebEngine (非常大；若你沒用 QWebEngineView 就排除)
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineQuick',

        # Multimedia
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',

        # Location / Positioning
        'PySide6.QtPositioning',
        'PySide6.QtLocation',

        # 3D
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',

        # Bluetooth
        'PySide6.QtBluetooth',

        # Charts
        'PySide6.QtCharts',
    ],

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
    name='main',
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
    icon=None,
)