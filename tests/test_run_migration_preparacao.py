import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / "databases"
DB_FILE = DB_DIR / "ftv.db"


def run_script(tmp_path, create_db=True):
    DB_DIR.mkdir(exist_ok=True)
    if create_db:
        DB_FILE.touch()
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "run_migration_preparacao.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    if DB_FILE.exists():
        DB_FILE.unlink()
    if DB_DIR.exists() and not any(DB_DIR.iterdir()):
        DB_DIR.rmdir()
    return result


def test_run_migration_success(tmp_path):
    res = run_script(tmp_path, create_db=True)
    assert res.returncode == 0, res.stderr


def test_run_migration_missing_db(tmp_path):
    res = run_script(tmp_path, create_db=False)
    assert res.returncode == 2
