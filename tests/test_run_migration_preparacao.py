import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_script(tmp_path, create_db=True):
    # Provide ftv_project via symlink so script can locate SQL and itself
    (tmp_path / "ftv_project").symlink_to(ROOT / "ftv_project")
    if create_db:
        db_dir = tmp_path / "databases"
        db_dir.mkdir()
        (db_dir / "ftv.db").touch()
    result = subprocess.run(
        [sys.executable, "ftv_project/ftv/tools/run_migration_preparacao.py"],
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
