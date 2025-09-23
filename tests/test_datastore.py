import logging
import sqlite3
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


def test_datastore_creates_missing_db_without_prompt(tmp_path, caplog):
    db_path = tmp_path / "auto.db"
    ds = None
    with caplog.at_level(logging.INFO):
        ds = DataStore(db_path=db_path)
    try:
        assert db_path.exists()
        assert ds is not None and ds.conn is not None
        assert any(
            "A criar base vazia padrão." in record.message
            for record in caplog.records
        )
    finally:
        if ds is not None:
            ds.close()


def _make_filter_datastore():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Produtos")
    cur.execute("DELETE FROM FichasTecnicas")
    products = [
        ("P1", "Hambúrguer Clássico", 1, "Pratos Quentes", "Hambúrgueres"),
        ("P2", "Salada Fresca", 1, "Pratos Frios", "Saladas"),
        ("P3", "Sopa do Dia", 1, None, None),
    ]
    cur.executemany(
        (
            "INSERT INTO Produtos "
            "(Codigo, Produto, TipoVenda, Familia, SubFamilia) "
            "VALUES (?, ?, ?, ?, ?)"
        ),
        products,
    )
    fichas = [
        (
            "P1",
            "Hambúrguer Clássico",
            "Queijo Cheddar",
            "Pratos Quentes > Hambúrgueres",
        ),
        (
            "P1",
            "Hambúrguer Clássico",
            "Pão Brioche",
            "Pratos Quentes > Hambúrgueres",
        ),
        (
            "P2",
            "Salada Fresca",
            "Tomate Cherry",
            "Pratos Frios > Saladas",
        ),
        (
            "P2",
            "Salada Fresca",
            "Alface",
            "Pratos Frios > Saladas",
        ),
        ("P3", "Sopa do Dia", "Cenoura", "Sopas > Cremes"),
    ]
    cur.executemany(
        (
            "INSERT INTO FichasTecnicas "
            "(ProdutoCodigo, ProdutoNome, ComponenteNome, FamiliaSubfamilia) "
            "VALUES (?, ?, ?, ?)"
        ),
        fichas,
    )
    ds.conn.commit()
    ds.reload_ids()
    return ds


def test_datastore_upgrades_missing_columns(tmp_path):
    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        (
            "CREATE TABLE Produtos (\n"
            "    Codigo TEXT PRIMARY KEY,\n"
            "    Produto TEXT,\n"
            "    Familia TEXT,\n"
            "    SubFamilia TEXT,\n"
            "    AfetaStk TEXT,\n"
            "    Menu TEXT,\n"
            "    CodBarras TEXT,\n"
            "    TipoMercad TEXT,\n"
            "    TipoVenda TEXT,\n"
            "    TipoProducao TEXT,\n"
            "    TipoGener TEXT,\n"
            "    UnStockVMPG TEXT,\n"
            "    UnVendaVMV TEXT,\n"
            "    UnProduFtPV TEXT,\n"
            "    CodAuxiliar TEXT,\n"
            "    CodAuxiliar2 TEXT,\n"
            "    PCU DECIMAL(10,2),\n"
            "    PCM DECIMAL(10,2),\n"
            "    Descontinuado TEXT,\n"
            "    DispLojas TEXT\n"
            ")"
        )
    )
    conn.execute(
        (
            "CREATE TABLE FichasTecnicas (\n"
            "    FamiliaSubfamilia TEXT,\n"
            "    ProdutoCodigo TEXT,\n"
            "    ProdutoNome TEXT,\n"
            "    ComponenteCodigo TEXT,\n"
            "    ComponenteNome TEXT,\n"
            "    Qtd DECIMAL(10,2),\n"
            "    Unidade TEXT,\n"
            "    Ppu DECIMAL(10,2),\n"
            "    Peso DECIMAL(10,2)\n"
            ")"
        )
    )
    conn.commit()
    conn.close()

    ds = DataStore(db_path=db_path)
    cur = ds.conn.execute("PRAGMA table_info(Produtos)")
    cols = {r[1] for r in cur.fetchall()}
    assert {"UnInvVMMMPG", "TipoArtigo", "Validade", "Temperatura"} <= cols
    cur = ds.conn.execute("PRAGMA table_info(FichasTecnicas)")
    ft_cols = {r[1] for r in cur.fetchall()}
    assert {"Preco", "Ordem"} <= ft_cols
    ds.close()


def test_list_validades_rw():
    ds = _make_datastore()
    assert ds.list_validades() == [(1, "24h"), (2, "48h")]


def test_reload_ids_repo_success(caplog):
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Produtos")
    cur.execute("DELETE FROM FichasTecnicas")
    cur.executemany(
        "INSERT INTO Produtos (Codigo, Produto, TipoVenda) VALUES (?, ?, ?)",
        [
            ("P1", "Produto 1", 1),  # válido (TipoVenda=1 e tem ficha)
            ("P2", "Produto 2", 2),  # TipoVenda != 1
            ("P3", "Produto 3", 1),  # sem ficha técnica
        ],
    )
    cur.executemany(
        "INSERT INTO FichasTecnicas (ProdutoCodigo) VALUES (?)",
        [("P1",), ("P2",)],
    )
    ds.conn.commit()
    with caplog.at_level(logging.INFO):
        count = ds.reload_ids()
    assert count == 1
    assert ds._ids == ["P1"]
    assert ds.get_produto_info("P1")["produto"] == "Produto 1"
    assert "P2" not in ds._ids and "P3" not in ds._ids
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


def test_reload_ids_filters_by_fcost_level():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Produtos")
    cur.execute("DELETE FROM FichasTecnicas")
    cur.execute("DELETE FROM PrecosTaxas")
    cur.execute("DELETE FROM FcostValues")
    cur.execute(
        "INSERT INTO FcostValues (Nivel, Nome, ValorMin, ValorMax, Comentario) "
        "VALUES (1, 'L1', 20, 30, '')"
    )
    cur.executemany(
        "INSERT INTO Produtos (Codigo, Produto, TipoVenda) VALUES (?, ?, 1)",
        [("P1", "Produto 1"), ("P2", "Produto 2")],
    )
    cur.executemany(
        "INSERT INTO FichasTecnicas (ProdutoCodigo, Preco) VALUES (?, ?)",
        [("P1", 10), ("P2", 10)],
    )
    cur.executemany(
        "INSERT INTO PrecosTaxas (Codigo, Loja, Preco1, Iva1) VALUES (?, ?, ?, ?)",
        [("P1", "1", 50, 23), ("P2", "1", 20, 23)],
    )
    ds.conn.commit()

    ds.set_fcost_level(1)
    assert ds._ids == ["P1"]


def test_set_search_filters_filters_by_produto():
    ds = _make_filter_datastore()
    try:
        ds.set_search_filters(
            produto="  salada ",
            ingrediente=None,
            familia=None,
            subfamilia=None,
        )
        assert ds._ids == ["P2"]
    finally:
        ds.close()


def test_set_search_filters_filters_by_ingrediente():
    ds = _make_filter_datastore()
    try:
        ds.set_search_filters(
            produto=None,
            ingrediente="QUEIJO",
            familia=None,
            subfamilia=None,
        )
        assert ds._ids == ["P1"]
    finally:
        ds.close()


def test_set_search_filters_combined():
    ds = _make_filter_datastore()
    try:
        ds.set_search_filters(
            produto="sopa",
            ingrediente="cenoura",
            familia=None,
            subfamilia=None,
        )
        assert ds._ids == ["P3"]
    finally:
        ds.close()


def test_set_search_filters_clears_with_empty_strings():
    ds = _make_filter_datastore()
    try:
        ds.set_search_filters(
            produto="salada",
            ingrediente="tomate",
            familia=["Pratos Frios"],
            subfamilia=("Saladas",),
        )
        assert ds._family_filter == ("Pratos Frios",)
        assert ds._subfamily_filter == ("Saladas",)
        assert ds._ids == ["P2"]
        ds.set_search_filters(
            produto="",
            ingrediente="  ",
            familia=[],
            subfamilia=(),
        )
        assert ds._family_filter is None
        assert ds._subfamily_filter is None
        assert ds._ids == ["P1", "P2", "P3"]
    finally:
        ds.close()


def test_set_search_filters_filters_by_familia():
    ds = _make_filter_datastore()
    try:
        ds.set_search_filters(
            produto=None,
            ingrediente=None,
            familia=[" pratos quentes "],
            subfamilia=None,
        )
        assert ds._family_filter == ("pratos quentes",)
        assert ds._ids == ["P1"]
    finally:
        ds.close()


def test_set_search_filters_filters_by_subfamilia():
    ds = _make_filter_datastore()
    try:
        ds.set_search_filters(
            produto=None,
            ingrediente=None,
            familia=None,
            subfamilia=[" saladas "],
        )
        assert ds._subfamily_filter == ("saladas",)
        assert ds._ids == ["P2"]
    finally:
        ds.close()


def test_set_search_filters_fallbacks_to_ficha_familia():
    ds = _make_filter_datastore()
    try:
        ds.set_search_filters(
            produto=None,
            ingrediente=None,
            familia=(" sopas ",),
            subfamilia=(" cremes ",),
        )
        assert ds._family_filter == ("sopas",)
        assert ds._subfamily_filter == ("cremes",)
        assert ds._ids == ["P3"]
    finally:
        ds.close()


def test_set_search_filters_preserves_family_on_partial_update():
    ds = _make_filter_datastore()
    try:
        ds.set_search_filters(familia=[" Sopas  "], subfamilia=[" Cremes "])
        assert ds._ids == ["P3"]
        assert ds._family_filter == ("Sopas",)
        assert ds._subfamily_filter == ("Cremes",)

        ds.set_search_filters(produto="sopa")

        assert ds._family_filter == ("Sopas",)
        assert ds._subfamily_filter == ("Cremes",)
        assert ds._ids == ["P3"]

        ds.set_search_filters(produto="  ", ingrediente="")

        assert ds._product_filter is None
        assert ds._ingredient_filter is None
        assert ds._family_filter == ("Sopas",)
        assert ds._subfamily_filter == ("Cremes",)
        assert ds._ids == ["P3"]
    finally:
        ds.close()


def test_set_search_filters_normalizes_iterables():
    ds = _make_filter_datastore()
    try:
        ds.set_search_filters(
            familia=[" Pratos Quentes ", "pratos quentes", ""],
            subfamilia=(" hambúrgueres ", "HAMBÚRGUERES"),
        )
        assert ds._family_filter == ("Pratos Quentes",)
        assert ds._subfamily_filter == ("hambúrgueres",)
        assert ds._ids == ["P1"]
    finally:
        ds.close()


def test_set_search_filters_accepts_multiple_families_and_subfamilias():
    ds = _make_filter_datastore()
    try:
        ds.set_search_filters(
            familia=("Pratos Quentes", " sopas "),
            subfamilia=(" hambúrgueres ", "CREMES"),
        )
        assert ds._family_filter == ("Pratos Quentes", "sopas")
        assert ds._subfamily_filter == ("hambúrgueres", "CREMES")
        assert ds._ids == ["P1", "P3"]
    finally:
        ds.close()


def test_list_families_with_subfamilies_uses_canonical_names():
    ds = _make_filter_datastore()
    try:
        mapping = ds.list_families_with_subfamilies()
        assert mapping == {
            "Pratos Frios": ("Saladas",),
            "Pratos Quentes": ("Hambúrgueres",),
            "Sopas": ("Cremes",),
        }
    finally:
        ds.close()


def test_list_active_allergens_db():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Alergenios")
    cur.executemany(
        "INSERT INTO Alergenios (Id, Nome, NomeIngles) VALUES (?, ?, ?)",
        [(2, "A", "A"), (1, "B", "B"), (3, "", "C")],
    )
    ds.conn.commit()
    assert ds.list_active_allergens() == [(1, "B"), (2, "A")]


def test_list_active_allergens_empty():
    ds = DataStore(db_path=":memory:")
    ds.conn.execute("DELETE FROM Alergenios")
    ds.conn.commit()
    assert ds.list_active_allergens() == []


def test_product_allergens_are_isolated_between_products():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Produtos")
    cur.execute("DELETE FROM ProdutoAlergenio")
    cur.execute("DELETE FROM Alergenios")
    cur.executemany(
        "INSERT INTO Produtos (Codigo, Produto, TipoVenda) VALUES (?, ?, 1)",
        [("P1", "Produto 1"), ("P2", "Produto 2")],
    )
    cur.executemany(
        "INSERT INTO Alergenios (Id, Nome, NomeIngles) VALUES (?, ?, ?)",
        [(1, "A", "A"), (2, "B", "B"), (3, "C", "C")],
    )
    ds.conn.commit()

    assert ds.get_product_allergens("P1") == []
    assert ds.get_product_allergens("P2") == []

    assert ds.set_product_allergens("P1", [1, 2])
    assert ds.set_product_allergens("P2", [3])

    assert ds.get_product_allergens("P1") == [1, 2]
    assert ds.get_product_allergens("P2") == [3]

    assert ds.set_product_allergens("P1", [])
    assert ds.get_product_allergens("P1") == []
    assert ds.get_product_allergens("P2") == [3]


def test_context_manager_closes_connection():
    with DataStore(db_path=":memory:") as ds:
        conn = ds.conn
        conn.execute("CREATE TABLE X (Id INTEGER)")
    # connection is closed after context
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


def test_datastore_missing_path_errors(tmp_path, caplog):
    bad_path = tmp_path / "no" / "db" / "ftv.db"
    with caplog.at_level(logging.ERROR), pytest.raises(FileNotFoundError):
        DataStore(db_path=str(bad_path), prompt=lambda *_: None)
    assert any("FTV_DB_PATH" in r.message for r in caplog.records)


def test_datastore_creates_empty_db(tmp_path, monkeypatch):
    def prompt(*_):
        return "Base vazia"
    import data.datastore as ds_module

    monkeypatch.setattr(ds_module, "base", tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "databases").mkdir()
    (tmp_path / "data" / "schema.sql").write_text(
        (
            "CREATE TABLE Produtos (\n"
            "    Codigo TEXT PRIMARY KEY,\n"
            "    Produto TEXT,\n"
            "    Familia TEXT,\n"
            "    SubFamilia TEXT,\n"
            "    AfetaStk TEXT,\n"
            "    Menu TEXT,\n"
            "    CodBarras TEXT,\n"
            "    TipoMercad TEXT,\n"
            "    TipoVenda TEXT,\n"
            "    TipoProducao TEXT,\n"
            "    TipoGener TEXT,\n"
            "    UnStockVMPG TEXT,\n"
            "    UnVendaVMV TEXT,\n"
            "    UnInvVMMMPG TEXT,\n"
            "    UnProduFtPV TEXT,\n"
            "    CodAuxiliar TEXT,\n"
            "    CodAuxiliar2 TEXT,\n"
            "    PCU DECIMAL(10,2),\n"
            "    PCM DECIMAL(10,2),\n"
            "    Descontinuado TEXT,\n"
            "    DispLojas TEXT\n"
            ");\n"
            "CREATE TABLE FichasTecnicas (\n"
            "    FamiliaSubfamilia TEXT,\n"
            "    ProdutoCodigo TEXT,\n"
            "    ProdutoNome TEXT,\n"
            "    ComponenteCodigo TEXT,\n"
            "    ComponenteNome TEXT,\n"
            "    Qtd REAL,\n"
            "    Unidade TEXT,\n"
            "    Ppu REAL,\n"
            "    Preco REAL,\n"
            "    Peso REAL\n"
            ");\n"
        ),
        encoding="utf-8",
    )

    ds = ds_module.DataStore(prompt=prompt)
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
        "PrecosTaxas",
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
    conn.execute(
        "CREATE TABLE FichasTecnicas ("
        "FamiliaSubfamilia TEXT, ProdutoCodigo TEXT, ProdutoNome TEXT, "
        "ComponenteCodigo TEXT, ComponenteNome TEXT, Qtd REAL, Unidade TEXT, "
        "Ppu REAL, Preco REAL, Peso REAL)"
    )
    conn.execute("CREATE TABLE TiposArtigos (Cod INTEGER)")
    conn.execute("CREATE TABLE Validade (Cod INTEGER)")
    conn.execute("CREATE TABLE Temperaturas (Cod INTEGER)")
    conn.execute("CREATE TABLE Alergenios (Id INTEGER, Nome TEXT)")
    conn.commit()
    conn.close()
    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError):
        DataStore(db_path=str(db_file))
    assert any("colunas" in r.message and r.exc_info is None for r in caplog.records)


def test_get_produto_info_repo_error(caplog):
    class BadRepo:
        def get_info(self, _codigo):
            raise sqlite3.OperationalError("boom")

    ds = DataStore(db_path=":memory:")
    ds.produtos = BadRepo()
    with caplog.at_level(logging.ERROR):
        assert ds.get_produto_info("X") == {}
    assert any("boom" in r.message for r in caplog.records)


@pytest.mark.parametrize(
    "raw,expected",
    [("1234.56", 1234.56), ("1 234,56", 1234.56)],
)
def test_get_pvps_parses_decimal_formats(raw, expected):
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DROP TABLE PrecosTaxas")
    cur.execute(
        (
            "CREATE TABLE PrecosTaxas ("
            "Codigo TEXT, Loja TEXT, Preco1 TEXT, Preco2 TEXT, "
            "Preco3 TEXT, Preco4 TEXT, Preco5 TEXT, Iva1 TEXT, Iva2 TEXT)"
        )
    )
    cur.execute(
        (
            "INSERT INTO PrecosTaxas ("
            "Codigo, Loja, Preco1, Preco2, Preco3, Preco4, Preco5, Iva1, Iva2"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        ("P1", "L1", raw, raw, raw, raw, raw, raw, "999"),
    )
    ds.conn.commit()
    pvps = ds.get_pvps("P1")
    assert pvps["pvps"] == [expected] * 5
    assert pvps["iva"] == expected
