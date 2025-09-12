import logging

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
