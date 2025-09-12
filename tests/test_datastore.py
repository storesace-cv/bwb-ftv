import logging
import json
import sqlite3
import pytest

from ftv.data.datastore import DataStore
from ftv.data.repositories import AuxiliaresRepo


def _make_datastore():
    ds = DataStore(db_path=":memory:")
    conn = ds.conn
    cur = conn.cursor()
    # tabelas auxiliares
    cur.execute(
        "CREATE TABLE validade (cod INTEGER PRIMARY KEY, descricao TEXT, ativo INTEGER)"
    )
    cur.executemany(
        "INSERT INTO validade (cod, descricao, ativo) VALUES (?, ?, 1)",
        [(1, "24h"), (2, "48h")],
    )
    cur.execute(
        "CREATE TABLE produto_auxiliar (produto_codigo TEXT PRIMARY KEY, "
        "tipo_artigo_id INTEGER, validade_id INTEGER, temperatura_id INTEGER)"
    )
    conn.commit()
    ds.aux = AuxiliaresRepo(conn)
    return ds


def test_list_validades_and_auxiliares_rw():
    ds = _make_datastore()
    assert ds.list_validades()[1:] == [(1, "24h"), (2, "48h")]
    assert ds.get_auxiliares_for("P1") == (None, None, None)
    assert ds.save_auxiliares_for("P1", 10, 1, 20)
    assert ds.get_auxiliares_for("P1") == (10, 1, 20)


def test_reload_ids_fallback_to_fichas_tecnicas(caplog):
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("CREATE TABLE fichas_tecnicas (produto_codigo TEXT)")
    cur.executemany(
        "INSERT INTO fichas_tecnicas (produto_codigo) VALUES (?)",
        [("F1",), ("F2",)],
    )
    ds.conn.commit()
    with caplog.at_level(logging.INFO):
        ds.reload_ids()
    assert ds.total() == 2
    assert ds._ids == ["F1", "F2"]
    assert any("fichas_tecnicas" in r.message for r in caplog.records)


def test_list_active_allergens_db():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("CREATE TABLE alergenios (id INTEGER, nome TEXT, ativo INTEGER)")
    cur.executemany(
        "INSERT INTO alergenios (id, nome, ativo) VALUES (?, ?, ?)",
        [(2, "A", 1), (1, "B", 1), (3, "C", 0)],
    )
    ds.conn.commit()
    assert ds.list_active_allergens() == [(1, "B"), (2, "A")]


def test_list_active_allergens_json(tmp_path, monkeypatch):
    import ftv.data.datastore as ds_module

    monkeypatch.setattr(ds_module, "base", tmp_path)
    (tmp_path / "allergens.json").write_text(
        json.dumps({"alergenios": ["A", "B"]}), encoding="utf-8"
    )
    ds = ds_module.DataStore(demo=True)
    assert ds.list_active_allergens() == [(1, "A"), (2, "B")]


def test_list_active_allergens_default(tmp_path, monkeypatch):
    import ftv.data.datastore as ds_module

    monkeypatch.setattr(ds_module, "base", tmp_path)
    ds = ds_module.DataStore(demo=True)
    items = ds.list_active_allergens()
    assert len(items) == 14
    assert items[0] == (1, "Glúten")


def test_context_manager_closes_connection():
    with DataStore(db_path=":memory:") as ds:
        conn = ds.conn
        conn.execute("CREATE TABLE x (id INTEGER)")
    # connection is closed after context
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


def test_datastore_connect_failure_raises(tmp_path):
    bad_path = tmp_path / "no" / "db" / "ftv.db"
    with pytest.raises(sqlite3.Error):
        DataStore(db_path=str(bad_path))


def test_get_produto_info_repo_error(caplog):
    class BadRepo:
        def get_info(self, _codigo):
            raise sqlite3.OperationalError("boom")

    ds = DataStore(db_path=":memory:")
    ds.produtos = BadRepo()
    with caplog.at_level(logging.ERROR):
        assert ds.get_produto_info("X") == {}
    assert any("boom" in r.message for r in caplog.records)
