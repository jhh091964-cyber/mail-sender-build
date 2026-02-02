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

        # 專案內模組（如果你有加這些就保留）
        'sender_manager',
        'proxy_handler',
        'resend_provider',
        'template_manager',
        'ssh_tunnel',
        'variable_parser',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)