a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (certifi.where(), 'certifi'),
    ],
    hiddenimports=[
        # Qt
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',

        # third-party
        'requests',
        'paramiko',
        'certifi',
        'socks',

        # 🔴 專案內模組（最重要）
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
