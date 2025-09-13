import sqlite3

from services.products import sync_table_schema


def test_sync_table_schema_handles_duplicate_headers():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE produtos (codigo TEXT)")
    headers = ["codigo", "Nome", "nome"]
    sync_table_schema(conn, "produtos", headers)
    cur = conn.execute("PRAGMA table_info(produtos)")
    cols = [row[1] for row in cur.fetchall()]
    assert cols == ["codigo", "nome"]
