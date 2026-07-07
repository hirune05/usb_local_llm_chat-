# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for USB-portable build of the conversation app."""

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

hidden_imports = []
datas = []
binaries = []

# faster-whisper + ctranslate2 (native .dylib + weights loader)
for pkg in ("ctranslate2", "faster_whisper"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hidden_imports += h

# sounddevice (PortAudio) / soundfile (libsndfile) ship native libs alongside the wheel
for pkg in ("sounddevice", "soundfile"):
    binaries += collect_dynamic_libs(pkg)
    datas += collect_data_files(pkg)

# python-engineio picks its async driver at runtime, PyInstaller can't see the import
hidden_imports += [
    "engineio.async_drivers.threading",
    "sockets",  # imported for side effects in app.py
    "multiprocessing",  # ensure PyInstaller injects pyi_rth_multiprocessing runtime hook
]

# Bundled Flask template + static assets
datas += [
    ("index.html", "."),
    ("static", "static"),
]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
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
    [],
    exclude_binaries=True,
    name="conversation_app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="conversation_app",
)
