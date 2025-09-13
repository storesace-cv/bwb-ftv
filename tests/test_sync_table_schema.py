import sqlite3

from services.products import sync_table_schema


def test_sync_table_schema_handles_duplicate_headers():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Produtos (Codigo TEXT)")
    headers = ["Codigo", "Nome", "nome"]
    sync_table_schema(conn, "Produtos", headers)
    cur = conn.execute("PRAGMA table_info(Produtos)")
    cols = [row[1] for row in cur.fetchall()]
    assert cols == ["Codigo", "Nome"]
