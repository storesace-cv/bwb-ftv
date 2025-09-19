import sqlite3

from data.repositories import IngredientesRepo


def test_listar_por_produto_includes_rows_with_trailing_spaces():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
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
        """
    )
    conn.executemany(
        (
            "INSERT INTO FichasTecnicas ("
            '"ProdutoCodigo", "ComponenteNome", "Qtd", "Unidade", '
            '"Ppu", "Preco", "ComponenteCodigo", "Ordem"'
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        [
            ("11480", "Base", 1.0, "kg", 1.0, 1.0, "B1", 1),
            ("11480   ", "Extra", 2.0, "kg", 2.0, 4.0, "E1", 2),
        ],
    )

    repo = IngredientesRepo(conn)
    rows = repo.listar_por_produto("11480")

    assert [row["ComponenteNome"] for row in rows] == ["Base", "Extra"]
