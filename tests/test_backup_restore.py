from datetime import datetime
from pathlib import Path
import sqlite3

import ui.dialogs as dialogs
import data.backup as backup_module


class DummyDatastore:
    def __init__(self, db_path: str | Path):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    def reload_ids(self):
        pass


def test_backup_and_restore(tmp_path, monkeypatch):
    root = tmp_path
    databases_dir = root / "databases"
    databases_dir.mkdir()
    db_file = databases_dir / "ftv.db"

    ds = DummyDatastore(db_file)
    ds.conn.execute("CREATE TABLE data (value TEXT)")
    ds.conn.execute("INSERT INTO data VALUES ('original')")
    ds.conn.commit()

    monkeypatch.setattr(dialogs, "get_project_root", lambda: root)
    monkeypatch.setattr(backup_module, "get_project_root", lambda: root)
    monkeypatch.setattr(dialogs.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(dialogs.QMessageBox, "warning", lambda *a, **k: None)

    dialogs.backup_database(None, ds)

    backups_dir = databases_dir / "backups"
    backups = list(backups_dir.glob("*.db"))
    assert len(backups) == 1
    backup = backups[0]
    assert backup.parent == backups_dir
    _, timestamp = backup.stem.split(".")
    assert len(timestamp) == 15
    datetime.strptime(timestamp, "%Y%m%d_%H%M%S")

    ds.conn.execute("UPDATE data SET value='modified'")
    ds.conn.commit()
    monkeypatch.setattr(
        dialogs.QFileDialog, "getOpenFileName", lambda *a, **k: (str(backup), "")
    )

    dialogs.restore_database(None, ds)

    restored_value = ds.conn.execute("SELECT value FROM data").fetchone()[0]
    assert restored_value == "original"
