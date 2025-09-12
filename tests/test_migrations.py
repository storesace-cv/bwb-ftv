import sqlite3
import pytest

import data.migration as migration
from data.migration import apply_pending_migrations, get_pending_migrations


def test_apply_pending_migrations(tmp_path, monkeypatch):
    db = tmp_path / "db.sqlite"
    conn = sqlite3.connect(str(db))

    mig_dir = tmp_path / "data" / "migrations"
    mig_dir.mkdir(parents=True)
    (mig_dir / "001.sql").write_text("CREATE TABLE t1(id INTEGER);", encoding="utf-8")

    monkeypatch.setattr(migration, "MIGRATIONS_DIR", mig_dir)

    pending = get_pending_migrations(conn)
    assert [p.name for p in pending] == ["001.sql"]
    applied = apply_pending_migrations(conn)
    assert applied == ["001.sql"]

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='t1'"
    )
    assert cur.fetchone() is not None
    cur = conn.execute("SELECT filename FROM schema_version")
    assert cur.fetchone()[0] == "001.sql"


def test_datastore_migration_accept(monkeypatch, tmp_path):
    import data.datastore as ds_module

    db_dir = tmp_path / "databases"
    db_dir.mkdir()
    db_path = db_dir / "ftv.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE produtos (codigo TEXT)")
    conn.execute("CREATE TABLE fichas_tecnicas (produto_codigo TEXT)")
    conn.commit()
    conn.close()

    mig_dir = tmp_path / "data" / "migrations"
    mig_dir.mkdir(parents=True)
    (mig_dir / "001.sql").write_text("CREATE TABLE t2(id INTEGER);", encoding="utf-8")

    monkeypatch.setattr(ds_module, "base", tmp_path)
    monkeypatch.setattr(migration, "MIGRATIONS_DIR", mig_dir)

    class FakeDialog:
        def __init__(self, text, buttons, parent=None):
            self.text = text
            self.buttons = buttons

        def get_choice(self):
            return "Sim"

    class DummyApp:
        _inst = None

        def __init__(self, *args, **kwargs):
            DummyApp._inst = self

        @classmethod
        def instance(cls):
            return cls._inst

    import sys
    import types

    dummy_qtwidgets = types.SimpleNamespace(QApplication=DummyApp, QMessageBox=object)
    dummy_pyqt5 = types.SimpleNamespace(QtWidgets=dummy_qtwidgets)
    monkeypatch.setitem(sys.modules, "PyQt5", dummy_pyqt5)
    monkeypatch.setitem(sys.modules, "PyQt5.QtWidgets", dummy_qtwidgets)
    stub_startup = types.SimpleNamespace(StartupDialog=FakeDialog)
    monkeypatch.setitem(sys.modules, "ui.startup_dialog", stub_startup)

    ds = ds_module.DataStore()
    cur = ds.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='t2'"
    )
    assert cur.fetchone() is not None


def test_datastore_migration_decline(monkeypatch, tmp_path):
    import data.datastore as ds_module

    db_dir = tmp_path / "databases"
    db_dir.mkdir()
    db_path = db_dir / "ftv.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE produtos (codigo TEXT)")
    conn.execute("CREATE TABLE fichas_tecnicas (produto_codigo TEXT)")
    conn.commit()
    conn.close()

    mig_dir = tmp_path / "data" / "migrations"
    mig_dir.mkdir(parents=True)
    (mig_dir / "001.sql").write_text("CREATE TABLE t3(id INTEGER);", encoding="utf-8")

    monkeypatch.setattr(ds_module, "base", tmp_path)
    monkeypatch.setattr(migration, "MIGRATIONS_DIR", mig_dir)

    class FakeDialog:
        def __init__(self, text, buttons, parent=None):
            pass

        def get_choice(self):
            return "Não"

    class DummyApp:
        _inst = None

        def __init__(self, *args, **kwargs):
            DummyApp._inst = self

        @classmethod
        def instance(cls):
            return cls._inst

    import sys
    import types

    dummy_qtwidgets = types.SimpleNamespace(QApplication=DummyApp, QMessageBox=object)
    dummy_pyqt5 = types.SimpleNamespace(QtWidgets=dummy_qtwidgets)
    monkeypatch.setitem(sys.modules, "PyQt5", dummy_pyqt5)
    monkeypatch.setitem(sys.modules, "PyQt5.QtWidgets", dummy_qtwidgets)
    stub_startup = types.SimpleNamespace(StartupDialog=FakeDialog)
    monkeypatch.setitem(sys.modules, "ui.startup_dialog", stub_startup)

    with pytest.raises(RuntimeError):
        ds_module.DataStore()
