import sqlite3
import shutil
from pathlib import Path
import pytest

import data.migration as migration
from data.migration import apply_pending_migrations, get_pending_migrations


def test_apply_pending_migrations(tmp_path, monkeypatch):
    db = tmp_path / "db.sqlite"
    conn = sqlite3.connect(str(db))

    conn.execute(
        "CREATE TABLE FichasTecnicas ("
        "FamiliaSubfamilia TEXT, ProdutoCodigo TEXT, ProdutoNome TEXT, "
        "ComponenteCodigo TEXT, ComponenteNome TEXT, Qtd REAL, Unidade TEXT, "
        "Ppu REAL, Preco REAL, Peso REAL)"
    )

    mig_dir = tmp_path / "data" / "migrations"
    mig_dir.mkdir(parents=True)
    (mig_dir / "001.sql").write_text("CREATE TABLE T1(Id INTEGER);", encoding="utf-8")

    monkeypatch.setattr(migration, "MIGRATIONS_DIR", mig_dir)

    pending = get_pending_migrations(conn)
    assert [p.name for p in pending] == ["001.sql"]
    applied = apply_pending_migrations(conn)
    assert applied == ["001.sql"]

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='T1'"
    )
    assert cur.fetchone() is not None
    cur = conn.execute("SELECT Filename FROM SchemaVersion")
    assert cur.fetchone()[0] == "001.sql"


def test_datastore_migration_accept(monkeypatch, tmp_path):
    import data.datastore as ds_module

    db_dir = tmp_path / "databases"
    db_dir.mkdir()
    db_path = db_dir / "ftv.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE Produtos ("
        "Codigo TEXT PRIMARY KEY,"
        "Produto TEXT,"
        "Familia TEXT,"
        "SubFamilia TEXT,"
        "AfetaStk TEXT,"
        "Menu TEXT,"
        "CodBarras TEXT,"
        "TipoMercad TEXT,"
        "TipoVenda TEXT,"
        "TipoProducao TEXT,"
        "TipoGener TEXT,"
        "UnStockVMPG TEXT,"
        "UnVendaVMV TEXT,"
        "UnInvVMMMPG TEXT,"
        "UnProduFtPV TEXT,"
        "CodAuxiliar TEXT,"
        "CodAuxiliar2 TEXT,"
        "PCU DECIMAL(10,2),"
        "PCM DECIMAL(10,2),"
        "Descontinuado TEXT,"
        "DispLojas TEXT"
        ")"
    )
    conn.execute(
        "CREATE TABLE FichasTecnicas ("
        "FamiliaSubfamilia TEXT, "
        "ProdutoCodigo TEXT, "
        "ProdutoNome TEXT, "
        "ComponenteCodigo TEXT, "
        "ComponenteNome TEXT, "
        "Qtd REAL, "
        "Unidade TEXT, "
        "Ppu REAL, "
        "Preco REAL, "
        "Peso REAL)"
    )
    conn.commit()
    conn.close()

    mig_dir = tmp_path / "data" / "migrations"
    mig_dir.mkdir(parents=True)
    (mig_dir / "001.sql").write_text("CREATE TABLE T2(Id INTEGER);", encoding="utf-8")

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
        "SELECT name FROM sqlite_master WHERE type='table' AND name='T2'"
    )
    assert cur.fetchone() is not None


def test_datastore_migration_decline(monkeypatch, tmp_path):
    import data.datastore as ds_module

    db_dir = tmp_path / "databases"
    db_dir.mkdir()
    db_path = db_dir / "ftv.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE Produtos ("
        "Codigo TEXT PRIMARY KEY,"
        "Produto TEXT,"
        "Familia TEXT,"
        "SubFamilia TEXT,"
        "AfetaStk TEXT,"
        "Menu TEXT,"
        "CodBarras TEXT,"
        "TipoMercad TEXT,"
        "TipoVenda TEXT,"
        "TipoProducao TEXT,"
        "TipoGener TEXT,"
        "UnStockVMPG TEXT,"
        "UnVendaVMV TEXT,"
        "UnInvVMMMPG TEXT,"
        "UnProduFtPV TEXT,"
        "CodAuxiliar TEXT,"
        "CodAuxiliar2 TEXT,"
        "PCU DECIMAL(10,2),"
        "PCM DECIMAL(10,2),"
        "Descontinuado TEXT,"
        "DispLojas TEXT"
        ")"
    )
    conn.execute(
        "CREATE TABLE FichasTecnicas ("
        "FamiliaSubfamilia TEXT, "
        "ProdutoCodigo TEXT, "
        "ProdutoNome TEXT, "
        "ComponenteCodigo TEXT, "
        "ComponenteNome TEXT, "
        "Qtd REAL, "
        "Unidade TEXT, "
        "Ppu REAL, "
        "Preco REAL, "
        "Peso REAL)"
    )
    conn.commit()
    conn.close()

    mig_dir = tmp_path / "data" / "migrations"
    mig_dir.mkdir(parents=True)
    (mig_dir / "001.sql").write_text("CREATE TABLE T3(Id INTEGER);", encoding="utf-8")

    monkeypatch.setattr(ds_module, "base", tmp_path)
    monkeypatch.setattr(migration, "MIGRATIONS_DIR", mig_dir)

    assert ds_module.DataStore.pending_migrations(db_path)
    ds_module.DataStore.apply_migrations(db_path)
    ds_module.DataStore(db_path=db_path)


def test_update_produtos_aux_cols_migration(tmp_path, monkeypatch):
    db = tmp_path / "db.sqlite"
    conn = sqlite3.connect(str(db))
    conn.execute(
        (
            "CREATE TABLE Produtos (\n"
            "    Codigo TEXT PRIMARY KEY,\n"
            "    Produto TEXT,\n"
            "    Familia TEXT,\n"
            "    SubFamilia TEXT,\n"
            "    AfetaStk TEXT,\n"
            "    Menu TEXT,\n"
            "    CodBarras TEXT,\n"
            "    TipoMercad TEXT,\n"
            "    TipoVenda TEXT,\n"
            "    TipoProducao TEXT,\n"
            "    TipoGener TEXT,\n"
            "    UnStockVMPG TEXT,\n"
            "    UnVendaVMV TEXT,\n"
            "    UnInvVMMMPG TEXT,\n"
            "    UnProduFtPV TEXT,\n"
            "    CodAuxiliar TEXT,\n"
            "    CodAuxiliar2 TEXT,\n"
            "    PCU DECIMAL(10,2),\n"
            "    PCM DECIMAL(10,2),\n"
            "    Descontinuado TEXT,\n"
            "    DispLojas TEXT\n"
            ")"
        )
    )
    conn.commit()

    mig_dir = tmp_path / "migrations"
    mig_dir.mkdir()
    src = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "migrations"
        / "update_produtos_aux_cols.sql"
    )
    shutil.copy(src, mig_dir / src.name)
    monkeypatch.setattr(migration, "MIGRATIONS_DIR", mig_dir)

    apply_pending_migrations(conn)
    cur = conn.execute("PRAGMA table_info(Produtos)")
    cols = {r[1] for r in cur.fetchall()}
    assert {"TipoArtigo", "Validade", "Temperatura"} <= cols
    conn.close()
