# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Recolectar TODO mysql.connector incluyendo plugins y locales dinamicos
mc_datas, mc_binaries, mc_hiddenimports = collect_all('mysql.connector')

a = Analysis(
    ['agente_sync.pyw'],
    pathex=[],
    binaries=mc_binaries,
    datas=mc_datas,
    hiddenimports=mc_hiddenimports + [
        'mysql.connector.plugins',
        'mysql.connector.plugins.mysql_native_password',
        'mysql.connector.plugins.caching_sha2_password',
        'mysql.connector.locales',
        'mysql.connector.locales.eng',
        'mysql.connector.locales.eng.client_error',
        'pyodbc',
    ],
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
    name='agente_sync',
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
)
