# PyInstaller spec — works on macOS and Windows.
# Build:  pyinstaller packaging/pdf_presenter.spec
from PyInstaller.utils.hooks import collect_submodules
import sys, os

block_cipher = None
ROOT = os.path.abspath(os.path.dirname(SPEC) + os.sep + os.pardir)

datas = []
# Bundle a logo file if the user dropped one next to the source.
for name in ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp"):
    p = os.path.join(ROOT, name)
    if os.path.isfile(p):
        datas.append((p, "."))

hiddenimports = collect_submodules("PySide6") + ["fitz"]

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

is_mac = sys.platform == "darwin"
is_win = sys.platform.startswith("win")

icon = None
for cand in ("logo.icns" if is_mac else "logo.ico", "logo.png"):
    p = os.path.join(ROOT, cand)
    if os.path.isfile(p):
        icon = p
        break

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="PDF Presenter",
    debug=False, bootloader_ignore_signals=False, strip=False,
    upx=False, console=False, icon=icon,
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, name="PDF Presenter",
)
if is_mac:
    app = BUNDLE(
        coll,
        name="PDF Presenter.app",
        icon=icon,
        bundle_identifier="app.pdfpresenter",
        info_plist={
            "CFBundleName": "PDF Presenter",
            "CFBundleDisplayName": "PDF Presenter",
            "CFBundleShortVersionString": "3.0",
            "NSHighResolutionCapable": True,
        },
    )
