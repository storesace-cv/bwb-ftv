import data.backup as backup_module
from data import restore_backup


def test_restore_backup(tmp_path, monkeypatch):
    root = tmp_path
    databases_dir = root / "databases"
    backups_dir = databases_dir / "backups"
    backups_dir.mkdir(parents=True)

    backup = backups_dir / "ftv.20240101_000000.db"
    backup.write_text("backup content", encoding="utf-8")
    db_file = databases_dir / "ftv.db"
    db_file.write_text("old content", encoding="utf-8")

    monkeypatch.setattr(backup_module, "get_project_root", lambda: root)
    restored = restore_backup(backup)

    assert restored == db_file
    assert db_file.read_text(encoding="utf-8") == "backup content"
