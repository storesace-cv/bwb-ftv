import sqlite3

from data.repositories import IngredientesRepo


def test_listar_por_produto_orders_by_custom_column():
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
            "Peso" REAL,
            "ComponenteCodigo" TEXT,
            "Ordem" INTEGER,
            "FamiliaSubfamilia" TEXT
        )
        """
    )
    conn.executemany(
        (
            "INSERT INTO FichasTecnicas ("
            '"ProdutoCodigo", "ComponenteNome", "Qtd", "Unidade", '
            '"Ppu", "Preco", "Peso", "ComponenteCodigo", "Ordem", '
            '"FamiliaSubfamilia"'
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        [
            (
                "P1",
                "Bovino Picado",
                2.0,
                "kg",
                1.5,
                3.0,
                1.2,
                "B1",
                2,
                "Carnes > Bovino",
            ),
            (
                "P1",
                "Trigo",
                1.0,
                "kg",
                1.0,
                1.0,
                0.9,
                "A1",
                3,
                "Cereais > Trigo",
            ),
            (
                "P1",
                "Suíno",
                1.5,
                "kg",
                2.0,
                3.0,
                1.5,
                "C1",
                4,
                "Carnes > Suíno",
            ),
            (
                "P1",
                "Bovino Cubos",
                0.5,
                "kg",
                1.8,
                0.9,
                0.7,
                "D1",
                5,
                " Carnes   >   Bovino  ",
            ),
        ],
    )
    repo = IngredientesRepo(conn)
    rows = repo.listar_por_produto("P1")
    assert [r["ComponenteNome"] for r in rows] == [
        "Bovino Picado",
        "Bovino Cubos",
        "Suíno",
        "Trigo",
    ]
    assert [r["Familia"] for r in rows] == ["Carnes", "Carnes", "Carnes", "Cereais"]
    assert [r["Subfamilia"] for r in rows] == [
        "Bovino",
        "Bovino",
        "Suíno",
        "Trigo",
    ]
