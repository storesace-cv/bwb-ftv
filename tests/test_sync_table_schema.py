import sqlite3

import pytest

from services.products import sync_table_schema


def test_sync_table_schema_handles_duplicate_headers():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Produtos (Codigo TEXT)")
    headers = ["Codigo", "Produto", "produto"]
    sync_table_schema(conn, "Produtos", headers)
    cur = conn.execute("PRAGMA table_info(Produtos)")
    cols = [row[1] for row in cur.fetchall()]
    assert cols == ["Codigo", "Produto"]


def test_sync_table_schema_preserves_composite_primary_key():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE Produtos (
            Codigo TEXT NOT NULL,
            Loja TEXT NOT NULL,
            Nome TEXT,
            PRIMARY KEY (Codigo, Loja)
        )
        """
    )
    headers = ["Codigo", "Loja"]

    sync_table_schema(conn, "Produtos", headers)

    rows = conn.execute("PRAGMA table_info(Produtos)").fetchall()
    pk_info = {row[1]: row[5] for row in rows}

    assert [row[1] for row in rows] == ["Codigo", "Loja"]
    assert pk_info["Codigo"] == 1
    assert pk_info["Loja"] == 2


def test_sync_table_schema_rejects_unknown_headers():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Produtos (Codigo TEXT)")

    with pytest.raises(ValueError):
        sync_table_schema(conn, "Produtos", ["Codigo", "Desconhecido"])
