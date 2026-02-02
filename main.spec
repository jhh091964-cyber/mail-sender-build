# -*- mode: python ; coding: utf-8 -*-

import os
import certifi

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[os.path.abspath(".")],
    binaries=[],
    datas=[
        # certifi CA bundle，避免 HTTPS 憑證錯誤
        (certifi.where(), "certifi"),
    ],
    hiddenimports=[
        # socks 讓 requests 支援 SOCKS
        "socks",

        # 專案內模組（避免打包漏掉）
        "sender_manager",
        "proxy_handler",
        "resend_provider",
        "template_manager",
        "ssh_tunnel",
        "variable_parser",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # ✅ Qt 瘦身（你沒用到下列功能就排除，可大幅降低體積/依賴）
    excludes=[
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtPositioning",
        "PySide6.QtLocation",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.Qt3DInput",
        "PySide6.QtBluetooth",
        "PySide6.QtCharts",
    ],

    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # 配合 COLLECT 做 onedir（最穩定）
    name="mail_sender",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                # 有裝 UPX 就會壓縮
    console=False,            # GUI 無黑窗
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="mail_sender",
)
