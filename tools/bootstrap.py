"""Bootstrap script to set up the ReportBro Designer environment."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Iterable
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = PROJECT_ROOT / ".venv"
STATIC_DIR = PROJECT_ROOT / "app" / "static"
DESIGNER_DIR = STATIC_DIR / "reportbro-designer"
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates_store" / "templates"
SAMPLES_DIR = PROJECT_ROOT / "app" / "templates_store" / "samples"
RELEASE_VERSION = "3.11.3"
DESIGNER_PACKAGE_URL = (
    f"https://github.com/jobsta/reportbro-designer/releases/download/v{RELEASE_VERSION}/"
    f"reportbro-designer-{RELEASE_VERSION}.tgz"
)
DEPENDENCIES = [
    "reportbro-lib==3.11.3",
    "Flask>=3.0,<4",
    "pywebview>=4.4,<5",
    "Pillow>=10.4.0,<12",
    "XlsxWriter>=3.1.0",
    "qrcode>=7.4.0",
    "python-barcode>=0.15.1",
    "reportbro-fpdf2>=1.0.0",
]


def run_command(args: Iterable[str]) -> None:
    """Run a subprocess and stream stdout/stderr."""

    process = subprocess.run(args, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        output = (process.stdout or "") + (process.stderr or "")
        if "externally-managed-environment" in output:
            message = (
                "A instalação falhou devido a um ambiente gerido externamente. "
                "Execute sempre este script para criar e usar o ambiente virtual local (.venv)."
            )
            raise RuntimeError(message)
        raise RuntimeError(output)
    if process.stdout:
        print(process.stdout)
    if process.stderr:
        print(process.stderr, file=sys.stderr)


def create_directories() -> None:
    for directory in (STATIC_DIR, DESIGNER_DIR, TEMPLATES_DIR, SAMPLES_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def create_virtualenv() -> Path:
    if not VENV_DIR.exists():
        print("[bootstrap] A criar ambiente virtual em .venv...")
        import venv

        venv.EnvBuilder(with_pip=True, clear=False).create(VENV_DIR)
    else:
        print("[bootstrap] Ambiente virtual já existe.")
    python_executable = (
        VENV_DIR / "Scripts" / "python.exe" if os.name == "nt" else VENV_DIR / "bin" / "python"
    )
    if not python_executable.exists():
        raise RuntimeError("Executável Python do ambiente virtual não encontrado.")
    return python_executable


def install_dependencies(python_executable: Path) -> None:
    print("[bootstrap] A actualizar pip e dependências...")
    run_command([str(python_executable), "-m", "pip", "install", "--upgrade", "pip", "wheel"])
    run_command([str(python_executable), "-m", "pip", "install", *DEPENDENCIES])


def download_designer_assets() -> None:
    if any(DESIGNER_DIR.iterdir()):
        print("[bootstrap] Assets do ReportBro Designer já estão presentes.")
        return

    print("[bootstrap] A descarregar assets do ReportBro Designer...")
    with urlopen(DESIGNER_PACKAGE_URL) as response:
        data = response.read()

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / "reportbro-designer.tgz"
        archive_path.write_bytes(data)
        with tarfile.open(archive_path, mode="r:gz") as tar:
            members = [member for member in tar.getmembers() if member.name.startswith("package/dist/")]
            tar.extractall(path=tmpdir, members=members)
        dist_dir = Path(tmpdir) / "package" / "dist"
        if not dist_dir.exists():
            raise RuntimeError("Estrutura inesperada no pacote do ReportBro Designer.")
        if DESIGNER_DIR.exists():
            shutil.rmtree(DESIGNER_DIR)
        shutil.copytree(dist_dir, DESIGNER_DIR)
        license_src = Path(tmpdir) / "package" / "LICENSE"
        if license_src.exists():
            shutil.copy2(license_src, DESIGNER_DIR / "LICENSE")
    print("[bootstrap] Assets do ReportBro Designer prontos.")


def main() -> None:
    create_directories()
    python_executable = create_virtualenv()
    install_dependencies(python_executable)
    download_designer_assets()
    print("[bootstrap] Ambiente preparado. Para iniciar execute:")
    if os.name == "nt":
        print(r"  .venv\Scripts\python -m app.ui.launcher")
    else:
        print("  .venv/bin/python -m app.ui.launcher")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"Erro: {error}", file=sys.stderr)
        sys.exit(1)
