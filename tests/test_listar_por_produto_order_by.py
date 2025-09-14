import sqlite3

from data.repositories import IngredientesRepo


def test_listar_por_produto_orders_by_custom_column():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        '''
        CREATE TABLE FichasTecnicas (
            "ProdutoCodigo" TEXT,
            "ComponenteNome" TEXT,
            "Qtd" REAL,
            "Unidade" TEXT,
            "Ppu" REAL,
            "Preco" REAL,
            "ComponenteCodigo" TEXT,
            "Ordem" INTEGER
        )
        '''
    )
    conn.executemany(
        'INSERT INTO FichasTecnicas ("ProdutoCodigo", "ComponenteNome", "Qtd", "Unidade", "Ppu", "Preco", "ComponenteCodigo", "Ordem") VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [
            ("P1", "B", 2.0, "kg", 1.5, 3.0, "B1", 2),
            ("P1", "A", 1.0, "kg", 1.0, 1.0, "A1", 1),
        ],
    )
    repo = IngredientesRepo(conn)
    rows = repo.listar_por_produto("P1")
    assert [r["ComponenteNome"] for r in rows] == ["A", "B"]
