from datetime import datetime

from data import create_backup
from utils.paths import get_project_root


def test_create_backup(tmp_path):
    root = get_project_root()
    databases_dir = root / "databases"
    databases_dir.mkdir(exist_ok=True)
    db_file = databases_dir / "test.db"
    db_file.write_text("dummy data", encoding="utf-8")

    backup_path = create_backup(db_file)

    assert backup_path.exists()
    assert backup_path.parent == databases_dir / "backups"
    assert backup_path.read_text(encoding="utf-8") == "dummy data"

    stem_part = backup_path.stem.split(".")[0]
    assert stem_part == db_file.stem

    timestamp_str = backup_path.stem.split(".")[-1]
    assert len(timestamp_str) == 15
    datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

    backup_path.unlink()
    db_file.unlink()
    backups_dir = databases_dir / "backups"
    if not any(backups_dir.iterdir()):
        backups_dir.rmdir()
    if not any(databases_dir.iterdir()):
        databases_dir.rmdir()
