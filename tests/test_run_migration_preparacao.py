import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL_SRC = ROOT / "data" / "migrations" / "preparacao.sql"


def run_script(tmp_path, create_db=True):
    mig_dir = tmp_path / "data" / "migrations"
    mig_dir.mkdir(parents=True)
    (mig_dir / "preparacao.sql").symlink_to(SQL_SRC)
    if create_db:
        db_dir = tmp_path / "databases"
        db_dir.mkdir()
        (db_dir / "ftv.db").touch()
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "run_migration_preparacao.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    return result


def test_run_migration_success(tmp_path):
    res = run_script(tmp_path, create_db=True)
    assert res.returncode == 0, res.stderr


def test_run_migration_missing_db(tmp_path):
    res = run_script(tmp_path, create_db=False)
    assert res.returncode == 2
