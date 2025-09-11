import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ftv_project.ftv.data.datastore import DataStore
from ftv_project.ftv.data.repositories import AuxiliaresRepo


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
        "CREATE TABLE produto_auxiliar (produto_codigo TEXT PRIMARY KEY, tipo_artigo_id INTEGER, validade_id INTEGER, temperatura_id INTEGER)"
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
