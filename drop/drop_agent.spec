# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for standalone drop_agent binary."""
import sys
from pathlib import Path

block_cipher = None
drop_dir = Path(SPECPATH)

a = Analysis(
    [str(drop_dir / "agent.py")],
    pathex=[str(drop_dir)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "collectors",
        "collectors.perf_collector",
        "collectors.pyspy_collector",
        "collectors.bpftrace_collector",
        "collectors.cp_worker",
        "storage_minio",
        "minio",
        "minio.helpers",
        "minio.credentials",
        "minio.credentials.providers",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "idna",
        "requests",
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
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="drop_agent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
