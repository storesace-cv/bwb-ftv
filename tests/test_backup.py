from datetime import datetime

import data.backup as backup_module
from data import create_backup


def test_create_backup(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_module, "get_project_root", lambda: tmp_path)
    databases_dir = tmp_path / "databases"
    databases_dir.mkdir()
    db_file = databases_dir / "ftv.db"
    db_file.write_text("dummy data", encoding="utf-8")

    backup_path = create_backup()

    assert backup_path.exists()
    assert backup_path.parent == databases_dir / "backups"
    assert backup_path.read_text(encoding="utf-8") == "dummy data"

    _, timestamp_str = backup_path.stem.split(".")
    assert len(timestamp_str) == 15
    datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
