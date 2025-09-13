import logging
import json
import sqlite3
import sys
import types
import pytest

from data.datastore import DataStore


def _make_datastore():
    ds = DataStore(db_path=":memory:")
    conn = ds.conn
    cur = conn.cursor()
    cur.execute("DELETE FROM Validade")
    cur.executemany(
        "INSERT INTO Validade (Cod, Descricao, Ativo) VALUES (?, ?, 1)",
        [(1, "24h"), (2, "48h")],
    )
    conn.commit()
    return ds


def test_list_validades_rw():
    ds = _make_datastore()
    assert ds.list_validades()[1:] == [(1, "24h"), (2, "48h")]


def test_reload_ids_repo_success(caplog):
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Produtos")
    cur.executemany(
        "INSERT INTO Produtos (Codigo) VALUES (?)",
        [("P1",), ("P2",)],
    )
    ds.conn.commit()
    with caplog.at_level(logging.INFO):
        count = ds.reload_ids()
    assert count == 2
    assert ds._ids == ["P1", "P2"]
    assert any("repositorio" in r.message for r in caplog.records)


def test_reload_ids_fallback_to_fichastecnicas(caplog):
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DROP TABLE Produtos")
    cur.execute("DELETE FROM FichasTecnicas")
    cur.executemany(
        "INSERT INTO FichasTecnicas (ProdutoCodigo) VALUES (?)",
        [("F1",), ("F2",)],
    )
    ds.conn.commit()
    with caplog.at_level(logging.INFO):
        ds.reload_ids()
    assert ds.total() == 2
    assert ds._ids == ["F1", "F2"]
    assert any("FichasTecnicas" in r.message for r in caplog.records)


def test_list_active_allergens_db():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Alergenios")
    cur.executemany(
        "INSERT INTO Alergenios (Id, Nome, Ativo) VALUES (?, ?, ?)",
        [(2, "A", 1), (1, "B", 1), (3, "C", 0)],
    )
    ds.conn.commit()
    assert ds.list_active_allergens() == [(1, "B"), (2, "A")]


def test_list_active_allergens_json(tmp_path, monkeypatch):
    import data.datastore as ds_module

    monkeypatch.setattr(ds_module, "base", tmp_path)
    (tmp_path / "allergens.json").write_text(
        json.dumps({"alergenios": ["A", "B"]}), encoding="utf-8"
    )
    ds = ds_module.DataStore(demo=True)
    assert ds.list_active_allergens() == [(1, "A"), (2, "B")]


def test_list_active_allergens_default(tmp_path, monkeypatch):
    import data.datastore as ds_module

    monkeypatch.setattr(ds_module, "base", tmp_path)
    ds = ds_module.DataStore(demo=True)
    items = ds.list_active_allergens()
    assert len(items) == 14
    assert items[0] == (1, "Glúten")


def test_context_manager_closes_connection():
    with DataStore(db_path=":memory:") as ds:
        conn = ds.conn
        conn.execute("CREATE TABLE X (Id INTEGER)")
    # connection is closed after context
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


def _stub_dialog(monkeypatch, choice):
    class DummyDialog:
        calls = 0

        def __init__(self, *a, **k):
            pass

        def get_choice(self):
            if DummyDialog.calls == 0:
                DummyDialog.calls += 1
                return choice
            DummyDialog.calls += 1
            return "Sim"

    dummy_module = types.SimpleNamespace(StartupDialog=DummyDialog)
    monkeypatch.setitem(sys.modules, "ui.startup_dialog", dummy_module)

    class DummyApp:
        _inst = None

        def __init__(self, *a, **k):
            DummyApp._inst = self

        @classmethod
        def instance(cls):
            return cls._inst

    qtwidgets = types.SimpleNamespace(QApplication=DummyApp)
    monkeypatch.setitem(sys.modules, "PyQt5", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "PyQt5.QtWidgets", qtwidgets)


def test_datastore_missing_path_errors(tmp_path, caplog, monkeypatch):
    _stub_dialog(monkeypatch, None)
    bad_path = tmp_path / "no" / "db" / "ftv.db"
    with caplog.at_level(logging.ERROR), pytest.raises(FileNotFoundError):
        DataStore(db_path=str(bad_path))
    assert any("FTV_DB_PATH" in r.message for r in caplog.records)


def test_datastore_creates_empty_db(tmp_path, monkeypatch):
    _stub_dialog(monkeypatch, "Base vazia")
    import data.datastore as ds_module

    monkeypatch.setattr(ds_module, "base", tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "databases").mkdir()
    (tmp_path / "data" / "schema.sql").write_text(
        "CREATE TABLE Produtos (Codigo TEXT PRIMARY KEY);"
        "CREATE TABLE FichasTecnicas (ProdutoCodigo TEXT);",
        encoding="utf-8",
    )

    ds = ds_module.DataStore()
    cur = ds.conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    names = {r[0] for r in cur.fetchall()}
    assert names >= {"Produtos", "FichasTecnicas"}


def test_datastore_missing_tables(tmp_path):
    db_file = tmp_path / "ftv.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE X (Id INTEGER)")
    conn.commit()
    conn.close()
    ds = DataStore(db_path=str(db_file))
    cur = ds.conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    names = {r[0] for r in cur.fetchall()}
    required = {
        "Produtos",
        "FichasTecnicas",
        "Alergenios",
        "TiposArtigos",
        "Validade",
        "Temperaturas",
    }
    assert required <= names


def test_datastore_missing_columns(tmp_path, caplog):
    db_file = tmp_path / "ftv.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE Produtos (Codigo TEXT)")
    conn.execute("CREATE TABLE FichasTecnicas (ProdutoCodigo TEXT)")
    conn.execute("CREATE TABLE TiposArtigos (Cod INTEGER)")
    conn.execute("CREATE TABLE Validade (Cod INTEGER)")
    conn.execute("CREATE TABLE Temperaturas (Cod INTEGER)")
    conn.execute("CREATE TABLE Alergenios (Id INTEGER, Nome TEXT)")
    conn.commit()
    conn.close()
    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError):
        DataStore(db_path=str(db_file))
    assert any("colunas" in r.message for r in caplog.records)


def test_get_produto_info_repo_error(caplog):
    class BadRepo:
        def get_info(self, _codigo):
            raise sqlite3.OperationalError("boom")

    ds = DataStore(db_path=":memory:")
    ds.produtos = BadRepo()
    with caplog.at_level(logging.ERROR):
        assert ds.get_produto_info("X") == {}
    assert any("boom" in r.message for r in caplog.records)
