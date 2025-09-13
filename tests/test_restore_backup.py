from data import restore_backup


def test_restore_backup(tmp_path):
    backup = tmp_path / "backup.db"
    backup.write_text("backup content", encoding="utf-8")
    db_file = tmp_path / "db.db"
    db_file.write_text("old content", encoding="utf-8")

    restored = restore_backup(backup, db_file)

    assert restored == db_file
    assert db_file.read_text(encoding="utf-8") == "backup content"
