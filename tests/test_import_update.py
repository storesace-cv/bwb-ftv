import shutil
import pytest
from openpyxl import Workbook, load_workbook

from data.datastore import DataStore
from services.products import ProductService, _update_from_excel, _import_single_excel
from utils.paths import get_project_root


@pytest.fixture
def ds():
    ds = DataStore(":memory:")
    conn = ds.conn
    conn.execute("DROP TABLE Produtos")
    conn.execute(
        "CREATE TABLE Produtos (Codigo TEXT PRIMARY KEY, Produto TEXT, "
        "TipoVenda INTEGER, Preco1G REAL, Preco2G REAL, Iva REAL)"
    )
    conn.execute("DROP TABLE FichasTecnicas")
    conn.execute(
        "CREATE TABLE FichasTecnicas ("
        "FamiliaSubfamilia TEXT, ProdutoCodigo TEXT, ProdutoNome TEXT, "
        "ComponenteCodigo TEXT, ComponenteNome TEXT, Qtd REAL, Unidade TEXT, "
        "Ppu REAL, Preco REAL, Peso REAL, Ordem INTEGER)"
    )
    return ds


@pytest.fixture
def imports_dir():
    base = get_project_root() / "imports"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    yield base
    shutil.rmtree(base, ignore_errors=True)


def _write_base_files(
    base_dir, products=None, code_header="Codigo", prices=None
):
    if products is None:
        products = [("P1", "Produto 1")]
    prod_wb = Workbook()
    ws = prod_wb.active
    ws.append(["Codigo", "Produto", "tipo_venda"])
    for code, name in products:
        ws.append([code, name, 1])
    prod_wb.save(base_dir / "Produtos_Base.xlsx")

    ft_wb = Workbook()
    ws = ft_wb.active
    ws.append(
        [
            "familia_subfamilia",
            "produto_codigo",
            "produto_nome",
            "componente_codigo",
            "componente_nome",
            "Qtd",
            "Unidade",
            "Ppu",
            "Preco",
            "Peso",
            "Ordem",
        ]
    )
    for code, _ in products:
        ws.append([None, code, None, None, None, None, None, None, None, None, None])
    ft_wb.save(base_dir / "FichasTecnicas_base.xlsx")

    if prices is None:
        prices = [1.0, None, None, None, None]
    prec_wb = Workbook()
    ws = prec_wb.active
    ws.append([code_header, "Preco1", "Preco2", "Preco3", "Preco4", "Preco5"])
    ws.append([products[0][0], *prices])
    prec_wb.save(base_dir / "PreçosTaxas_base.xlsx")


def test_import_from_excel_replaces_database(ds, imports_dir):
    ds.conn.execute("INSERT INTO Produtos (Codigo, Produto) VALUES ('OLD', 'Old')")
    ds.reload_ids()
    svc = ProductService(ds)
    _write_base_files(imports_dir, products=[("P1", "Produto 1"), ("P2", "Produto 2")])
    svc.import_from_excel()
    ds.reload_ids()

    assert ds.total() == 2
    assert ds.get_produto_info("OLD") == {}
    assert ds.get_produto_info("P1")["produto"] == "Produto 1"
    assert ds.get_produto_info("P2")["produto"] == "Produto 2"
    assert not (imports_dir / "Produtos_Base.xlsx").exists()
    rows = ds.conn.execute("SELECT Filename FROM Uploads").fetchall()
    names = {r[0] for r in rows}
    assert "Produtos_Base.xlsx" in names


def test_update_from_excel_updates_and_inserts(ds, imports_dir):
    ds.conn.executemany(
        "INSERT INTO Produtos (Codigo, Produto, TipoVenda) VALUES (?, ?, 1)",
        [("P1", "Produto 1"), ("P2", "Produto 2")],
    )
    ds.conn.executemany(
        "INSERT INTO FichasTecnicas (ProdutoCodigo) VALUES (?)",
        [("P1",), ("P2",)],
    )
    ds.reload_ids()
    svc = ProductService(ds)
    _write_base_files(
        imports_dir,
        products=[("P1", "Produto 1 updated"), ("P3", "Produto 3")],
    )
    svc.update_from_excel()
    ds.reload_ids()

    assert ds.total() == 3
    assert ds.get_produto_info("P1")["produto"] == "Produto 1 updated"
    assert ds.get_produto_info("P2")["produto"] == "Produto 2"
    assert ds.get_produto_info("P3")["produto"] == "Produto 3"
    assert not (imports_dir / "Produtos_Base.xlsx").exists()
    rows = ds.conn.execute("SELECT Filename FROM Uploads").fetchall()
    names = {r[0] for r in rows}
    assert "Produtos_Base.xlsx" in names


def test_import_from_excel_missing_file(ds, imports_dir):
    _write_base_files(imports_dir)
    (imports_dir / "PreçosTaxas_base.xlsx").unlink()
    svc = ProductService(ds)
    with pytest.raises(FileNotFoundError) as exc:
        svc.import_from_excel()
    assert "PreçosTaxas_base.xlsx" in str(exc.value)


def test_update_from_excel_missing_file(ds, imports_dir):
    _write_base_files(imports_dir)
    (imports_dir / "FichasTecnicas_base.xlsx").unlink()
    svc = ProductService(ds)
    with pytest.raises(FileNotFoundError) as exc:
        svc.update_from_excel()
    assert "FichasTecnicas_base.xlsx" in str(exc.value)


def test_import_stores_files_in_uploads(ds, imports_dir):
    svc = ProductService(ds)
    _write_base_files(imports_dir)
    svc.import_from_excel()
    rows = ds.conn.execute("SELECT Filename, length(Content) FROM Uploads").fetchall()
    assert len(rows) == 3
    expected = [
        "Produtos_Base.xlsx",
        "FichasTecnicas_base.xlsx",
        "PreçosTaxas_base.xlsx",
    ]
    names = {r[0] for r in rows}
    for name in expected:
        assert name in names
        assert not (imports_dir / name).exists()


def test_update_stores_files_in_uploads(ds, imports_dir):
    svc = ProductService(ds)
    _write_base_files(imports_dir)
    svc.update_from_excel()
    rows = ds.conn.execute("SELECT Filename, length(Content) FROM Uploads").fetchall()
    assert len(rows) == 3
    expected = [
        "Produtos_Base.xlsx",
        "FichasTecnicas_base.xlsx",
        "PreçosTaxas_base.xlsx",
    ]
    names = {r[0] for r in rows}
    for name in expected:
        assert name in names
        assert not (imports_dir / name).exists()


def test_import_from_excel_uses_produto_codigo(ds, imports_dir):
    _write_base_files(
        imports_dir, code_header="produto_codigo", prices=[2.5, None, None, None, None]
    )
    svc = ProductService(ds)
    svc.import_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvps"][0] == 2.5
    assert len(pvps["pvps"]) == 5


def test_update_from_excel_uses_produto_codigo(ds, imports_dir):
    ds.conn.execute(
        "INSERT INTO Produtos (Codigo, Produto, Preco1G) VALUES ('P1', 'X', 1.0)"
    )
    ds.reload_ids()
    _write_base_files(
        imports_dir, code_header="produto_codigo", prices=[3.0, None, None, None, None]
    )
    svc = ProductService(ds)
    svc.update_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvps"][0] == 3.0
    assert len(pvps["pvps"]) == 5


def test_import_from_excel_skips_rows_without_codigo(ds, imports_dir):
    products = [("P1", "Produto 1"), ("   ", "Sem Código"), (None, "Outro")]
    _write_base_files(imports_dir, products=products)
    prec_path = imports_dir / "PreçosTaxas_base.xlsx"
    wb = load_workbook(prec_path)
    ws = wb.active
    ws.append([" ", None, None, None, None, None])
    wb.save(prec_path)
    wb.close()

    svc = ProductService(ds)
    svc.import_from_excel()

    rows = ds.conn.execute(
        "SELECT Codigo FROM Produtos WHERE Codigo IS NULL OR Codigo = ''"
    ).fetchall()
    assert rows == []

    ft_rows = ds.conn.execute(
        "SELECT ProdutoCodigo FROM FichasTecnicas "
        "WHERE ProdutoCodigo IS NULL OR ProdutoCodigo = ''"
    ).fetchall()
    assert ft_rows == []


def test_update_from_excel_skips_rows_without_codigo(ds, imports_dir):
    ds.conn.execute(
        "INSERT INTO Produtos (Codigo, Produto, TipoVenda) VALUES ('P1', 'Produto 1', 1)"
    )
    ds.conn.execute(
        "INSERT INTO FichasTecnicas (ProdutoCodigo, ProdutoNome) VALUES ('P1', 'Produto 1')"
    )
    ds.reload_ids()

    products = [("P1", "Produto 1 atualizado"), ("P2", "Produto 2"), ("", "Sem Código")]
    _write_base_files(imports_dir, products=products)
    prec_path = imports_dir / "PreçosTaxas_base.xlsx"
    wb = load_workbook(prec_path)
    ws = wb.active
    ws.append(["", None, None, None, None, None])
    wb.save(prec_path)
    wb.close()

    svc = ProductService(ds)
    svc.update_from_excel()
    ds.reload_ids()

    codigos = {
        row[0]
        for row in ds.conn.execute("SELECT Codigo FROM Produtos").fetchall()
        if row[0] is not None
    }
    assert "" not in codigos
    assert "P1" in codigos and "P2" in codigos

    preco_rows = ds.conn.execute(
        "SELECT Codigo FROM PrecosTaxas WHERE Codigo IS NULL OR Codigo = ''"
    ).fetchall()
    assert preco_rows == []

    ft_invalid = ds.conn.execute(
        "SELECT ProdutoCodigo FROM FichasTecnicas "
        "WHERE ProdutoCodigo IS NULL OR ProdutoCodigo = ''"
    ).fetchall()
    assert ft_invalid == []

def test_import_single_excel_accepts_canonical_headers(ds, tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(["Codigo", "Produto", "Preco1G", "Preco2G", "Iva"])
    ws.append(["P1", "Produto 1", 10.5, None, 23])
    ws.append(["P2", "Produto 2", 5.75, 7.25, None])
    path = tmp_path / "produtos.xlsx"
    wb.save(path)

    _import_single_excel(path, ds)

    rows = [
        tuple(row)
        for row in ds.conn.execute(
            "SELECT Codigo, Produto, Preco1G, Preco2G, Iva FROM Produtos ORDER BY Codigo"
        ).fetchall()
    ]

    assert rows == [
        ("P1", "Produto 1", 10.5, None, 23),
        ("P2", "Produto 2", 5.75, 7.25, None),
    ]


def test_import_from_excel_reads_all_prices(ds, imports_dir):
    _write_base_files(imports_dir, prices=[1, 2, 3, 4, 5])
    svc = ProductService(ds)
    svc.import_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvps"] == [1.0, 2.0, 3.0, 4.0, 5.0]


def test_update_from_excel_reads_all_prices(ds, imports_dir):
    ds.conn.execute(
        "INSERT INTO Produtos (Codigo, Produto, Preco1G) VALUES ('P1', 'X', 1.0)"
    )
    ds.reload_ids()
    _write_base_files(imports_dir, prices=[6, 7, 8, 9, 10])
    svc = ProductService(ds)
    svc.update_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvps"] == [6.0, 7.0, 8.0, 9.0, 10.0]


@pytest.mark.parametrize(
    "price,expected",
    [("1,5", 1.5), ("1 234,5", 1234.5)],
)
def test_import_from_excel_parses_formatted_numbers(ds, imports_dir, price, expected):
    _write_base_files(imports_dir, prices=[price] * 5)
    svc = ProductService(ds)
    svc.import_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvps"] == [expected] * 5


@pytest.mark.parametrize(
    "price,expected",
    [("1,5", 1.5), ("1 234,5", 1234.5)],
)
def test_update_from_excel_parses_formatted_numbers(ds, imports_dir, price, expected):
    ds.conn.execute(
        "INSERT INTO Produtos (Codigo, Produto, Preco1G) VALUES ('P1', 'X', 1.0)"
    )
    ds.reload_ids()
    _write_base_files(imports_dir, prices=[price] * 5)
    svc = ProductService(ds)
    svc.update_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvps"] == [expected] * 5


@pytest.mark.parametrize("func", ["import_from_excel", "update_from_excel"])
def test_preco_taxas_requires_codigo(ds, imports_dir, func):
    _write_base_files(imports_dir, code_header="wrong")
    svc = ProductService(ds)
    with pytest.raises(ValueError):
        getattr(svc, func)()


def test_import_reads_preco(ds, imports_dir):
    prod = Workbook()
    ws = prod.active
    ws.append(["codigo", "nome", "tipo_venda"])
    ws.append(["P1", "Produto 1", 1])
    prod.save(imports_dir / "Produtos_Base.xlsx")

    ft = Workbook()
    ws = ft.active
    ws.append(
        [
            "familia_subfamilia",
            "produto_codigo",
            "produto_nome",
            "componente_codigo",
            "componente_nome",
            "Qtd",
            "Unidade",
            "Ppu",
            "Preco",
            "Peso",
            "Ordem",
        ]
    )
    ws.append([None, "P1", None, None, "Ing", 2, "Kg", 3, "1 234,5", None, None])
    ft.save(imports_dir / "FichasTecnicas_base.xlsx")

    prec = Workbook()
    ws = prec.active
    ws.append(["codigo", "Preco1", "Preco2", "Preco3", "Preco4", "Preco5"])
    ws.append(["P1", 1, None, None, None, None])
    prec.save(imports_dir / "PreçosTaxas_base.xlsx")

    svc = ProductService(ds)
    svc.import_from_excel()
    ing = ds.get_ingredientes("P1")[0]
    assert ing["Preco"] == 1234.5


def test_update_reads_preco(ds, imports_dir):
    ds.conn.execute("INSERT INTO Produtos (Codigo, Produto) VALUES ('P1', 'Prod')")
    ds.conn.execute(
        "INSERT INTO FichasTecnicas "
        "(ProdutoCodigo, ComponenteNome, Qtd, Unidade, Ppu, Preco) "
        "VALUES ('P1', 'Ing', 1, 'Kg', 2, 5)"
    )
    ds.reload_ids()

    prod = Workbook()
    ws = prod.active
    ws.append(["codigo", "nome", "tipo_venda"])
    ws.append(["P1", "Prod", 1])
    prod.save(imports_dir / "Produtos_Base.xlsx")

    ft = Workbook()
    ws = ft.active
    ws.append(
        [
            "familia_subfamilia",
            "produto_codigo",
            "produto_nome",
            "componente_codigo",
            "componente_nome",
            "Qtd",
            "Unidade",
            "Ppu",
            "Preco",
            "Peso",
            "Ordem",
        ]
    )
    ws.append([None, "P1", None, None, "Ing", 3, "Kg", 2, 7, None, None])
    ft.save(imports_dir / "FichasTecnicas_base.xlsx")

    prec = Workbook()
    ws = prec.active
    ws.append(["codigo", "Preco1", "Preco2", "Preco3", "Preco4", "Preco5"])
    ws.append(["P1", 1, None, None, None, None])
    prec.save(imports_dir / "PreçosTaxas_base.xlsx")

    svc = ProductService(ds)
    svc.update_from_excel()
    ing = ds.get_ingredientes("P1")[0]
    assert ing["Preco"] == 7


def test_private_update_from_excel_parses_numbers(ds, tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(["Código", "Produto", "Preço1 G"])
    ws.append(["P1", "Produto 1", "1 234,5"])
    path = tmp_path / "update.xlsx"
    wb.save(path)

    _update_from_excel(path, ds)
    info = ds.get_produto_info("P1")
    assert info["produto"] == "Produto 1"
    assert info["preco1g"] == 1234.5
