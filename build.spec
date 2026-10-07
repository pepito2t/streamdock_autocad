# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("src", "src"), ("com.tmbk.streamdock.autocad.sdPlugin/presets", "presets")],
    hiddenimports=[
        "websocket",
        "win32com.client",
        "pythoncom",
        "pywintypes",
        "tkinter",
        "tkinter.ttk",
        "src.console.window",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="plugin",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
