"""
Package QGIS Plugin into a standard .zip distribution.
Archaeologists can install this directly via:
QGIS -> Plugins -> Manage and Install Plugins -> Install from ZIP.
"""

from pathlib import Path
import zipfile

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SRC = REPO_ROOT / "qgis_plugin"
DIST_DIR = REPO_ROOT / "dist"


def build_qgis_zip() -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DIST_DIR / "pre600bce_apm_qgis_plugin.zip"

    files_to_zip = [
        "__init__.py",
        "metadata.txt",
        "apm_plugin.py",
        "apm_dockwidget.py",
        "icon.png",
    ]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files_to_zip:
            p = PLUGIN_SRC / f
            if p.exists():
                # Store inside top-level folder 'pre600bce_apm' per QGIS standard
                arcname = f"pre600bce_apm/{f}"
                zf.write(p, arcname=arcname)
                print(f"  + Added: {arcname}")

    print(f"\n[OK] Built QGIS Plugin Package: {zip_path} ({zip_path.stat().st_size} bytes)")
    return zip_path


build_qgis_plugin_zip = build_qgis_zip


if __name__ == "__main__":
    build_qgis_zip()
