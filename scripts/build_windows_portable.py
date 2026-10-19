"""Crea lo zip portatile della demo per Windows: Python incluso, nessuna installazione sul PC di destinazione.

Uso (da macOS, Linux o Windows, richiede uv: https://docs.astral.sh/uv/):

    .venv/bin/python scripts/build_windows_portable.py

Risultato: dist/Brofind_Cockpit_Demo_v<versione>_Windows.zip. Struttura dello zip:

    Brofind Cockpit Demo/
      Avvia Cockpit.bat
      Ripristina dati demo.bat
      LEGGIMI - Come avviare.txt
      sistema/             applicazione, Python embeddable e dipendenze per win_amd64
"""

import hashlib
import re
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "Cockpit_zip_WindowsVersion"
CACHE = ROOT / "build" / "cache"
STAGING = ROOT / "build" / "windows_portable"
DIST = ROOT / "dist"
PACKAGE_NAME = "Brofind Cockpit Demo"

PYTHON_VERSION = "3.13.16"
PYTHON_TAG = "313"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
PYTHON_SHA256 = "97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297"

APP_DIRECTORIES = ["app", "templates", "static", "alembic", "demo"]
APP_FILES = ["alembic.ini", "pyproject.toml"]
USER_FILES = ["Avvia Cockpit.bat", "Ripristina dati demo.bat", "LEGGIMI - Come avviare.txt"]
SYSTEM_FILES = ["avvio_demo.py", "ripristina_demo.py"]

# Pacchetti che la demo non carica mai (verificato con la suite di test senza di essi): esclusi dallo zip.
DEMO_EXCLUDED_PACKAGES = {
    "psycopg": "driver PostgreSQL, la demo usa SQLite",
    "psycopg-binary": "driver PostgreSQL, la demo usa SQLite",
    "msoffcrypto-tool": "decifra file Office protetti da password (via oletools); import opzionale",
    "cryptography": "richiesto solo da msoffcrypto-tool",
    "cffi": "richiesto solo da cryptography",
    "pycparser": "richiesto solo da cffi",
    "greenlet": "serve a SQLAlchemy solo in modalità asyncio",
    "watchfiles": "ricaricamento automatico di uvicorn (--reload)",
    "websockets": "WebSocket di uvicorn, non usati",
}
# File per compilare o tipizzare le dipendenze, inutili a runtime.
DEV_ONLY_SUFFIXES = {".c", ".h", ".pyx", ".pxd", ".pyi"}
DEV_ONLY_DIRECTORIES = {"tests", "test", "__pycache__"}

# Stessa mappa di scripts/prepare_b1_demo_sources.py: fonti del caso B1 già pronte nella demo.
B1_SOURCES = {
    "Galileo": "DEMO-B1-001_control.xlsx",
    "Documenti": "DEMO-B1-001_contract.pdf",
    "Outlook": "DEMO-B1-001_payment_followup.eml",
}


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["project"]["version"]


def embeddable_python() -> Path:
    archive = CACHE / f"python-{PYTHON_VERSION}-embed-amd64.zip"
    if not archive.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"Scarico Python {PYTHON_VERSION} embeddable...")
        # curl (presente su macOS, Linux e Windows 10+) usa i certificati di sistema; urllib dipende
        # dall'installazione Python, che su macOS spesso non li ha.
        subprocess.run(["curl", "-sSfL", "-o", str(archive), PYTHON_URL], check=True)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != PYTHON_SHA256:
        archive.unlink()
        raise SystemExit(f"Checksum non valido per {archive.name}: {digest}")
    return archive


def install_python(system_dir: Path) -> Path:
    python_dir = system_dir / "python"
    with zipfile.ZipFile(embeddable_python()) as archive:
        archive.extractall(python_dir)
    # Percorsi di import: stdlib, site-packages e la cartella "sistema" che contiene il pacchetto app.
    (python_dir / f"python{PYTHON_TAG}._pth").write_text(
        f"python{PYTHON_TAG}.zip\r\n.\r\nLib\\site-packages\r\n..\r\nimport site\r\n", encoding="ascii"
    )
    return python_dir


def requirement_name(line: str) -> str | None:
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", line.split("#", 1)[0])
    return match.group(1).lower().replace("_", "-") if match else None


def install_dependencies(python_dir: Path) -> None:
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("uv non trovato: installarlo da https://docs.astral.sh/uv/ e rilanciare.")
    site_packages = python_dir / "Lib" / "site-packages"
    # Le dipendenze dirette escluse vanno tolte dal requirements: --excludes di uv vale solo per le transitive.
    requirements = STAGING / "requirements-demo.txt"
    requirements.write_text(
        "".join(
            line
            for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines(keepends=True)
            if requirement_name(line) not in DEMO_EXCLUDED_PACKAGES
        ),
        encoding="utf-8",
    )
    excludes = STAGING / "excludes.txt"
    excludes.write_text("\n".join(DEMO_EXCLUDED_PACKAGES) + "\n", encoding="ascii")
    print("Installo le dipendenze per Windows x64...")
    subprocess.run(
        [
            uv,
            "pip",
            "install",
            "--quiet",
            "--python-platform",
            "x86_64-pc-windows-msvc",
            "--python-version",
            PYTHON_VERSION.rsplit(".", 1)[0],
            "--target",
            str(site_packages),
            "--excludes",
            excludes.name,  # relativo: uv divide sugli spazi il percorso di --excludes
            "-r",
            requirements.name,
        ],
        check=True,
        cwd=excludes.parent,
    )
    excludes.unlink()
    requirements.unlink()
    # Eseguibili da console delle dipendenze: non servono e non sono pensati per questa cartella.
    shutil.rmtree(site_packages / "bin", ignore_errors=True)
    for path in sorted(site_packages.rglob("*"), reverse=True):
        if path.is_dir() and path.name in DEV_ONLY_DIRECTORIES:
            shutil.rmtree(path)
        elif path.is_file() and path.suffix in DEV_ONLY_SUFFIXES:
            path.unlink()


def copy_application(system_dir: Path) -> None:
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
    for name in APP_DIRECTORIES:
        shutil.copytree(ROOT / name, system_dir / name, ignore=ignore)
    for name in APP_FILES:
        shutil.copy2(ROOT / name, system_dir / name)
    for name in SYSTEM_FILES:
        shutil.copy2(PACKAGING / name, system_dir / name)

    (system_dir / "data" / "demo").mkdir(parents=True)
    sources = system_dir / "data_sources" / "DEMO-B1-001"
    for folder, name in B1_SOURCES.items():
        (sources / folder).mkdir(parents=True)
        shutil.copy2(ROOT / "demo" / "b1" / "assets" / name, sources / folder / name)


def copy_user_files(package_dir: Path) -> None:
    # File aperti da cmd.exe e Blocco note: fine riga CRLF indipendentemente dal checkout.
    for name in USER_FILES:
        text = (PACKAGING / name).read_text(encoding="utf-8").replace("\r\n", "\n")
        target = package_dir / name
        if name.endswith(".txt"):
            target.write_text(text.replace("\n", "\r\n"), encoding="utf-8-sig", newline="")
        else:
            target.write_text(text.replace("\n", "\r\n"), encoding="ascii", newline="")


def write_zip(package_dir: Path, version: str) -> Path:
    DIST.mkdir(exist_ok=True)
    zip_path = DIST / f"Brofind_Cockpit_Demo_v{version}_Windows.zip"
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(package_dir.rglob("*")):
            archive.write(path, path.relative_to(package_dir.parent).as_posix())
    return zip_path


def main() -> int:
    version = project_version()
    shutil.rmtree(STAGING, ignore_errors=True)
    package_dir = STAGING / PACKAGE_NAME
    system_dir = package_dir / "sistema"
    system_dir.mkdir(parents=True)

    python_dir = install_python(system_dir)
    install_dependencies(python_dir)
    copy_application(system_dir)
    copy_user_files(package_dir)
    zip_path = write_zip(package_dir, version)

    longest = max(len(path.relative_to(STAGING).as_posix()) for path in package_dir.rglob("*"))
    size_mb = zip_path.stat().st_size / 1_000_000
    print(f"Creato: {zip_path} ({size_mb:.0f} MB)")
    print(f"Percorso interno più lungo: {longest} caratteri (limite Windows: 260 incluso il percorso di estrazione)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
