import re
import shutil
import pytest
from openpyxl import Workbook

from data.datastore import DataStore
from services.products import ProductService, _update_from_excel
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
        "Ppu REAL, Preco REAL, Peso REAL)"
    )
    return ds


@pytest.fixture
def imports_dir():
    base = get_project_root() / "imports"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    (base / "history").mkdir(exist_ok=True)
    yield base
    shutil.rmtree(base, ignore_errors=True)


def _write_base_files(
    base_dir, products=None, code_header="codigo", price_header="preco1_g", price=1.0
):
    if products is None:
        products = [("P1", "Produto 1")]
    prod_wb = Workbook()
    ws = prod_wb.active
    ws.append(["codigo", "nome", "tipo_venda"])
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
            "qtd",
            "unidade",
            "ppu",
            "preco",
            "peso",
        ]
    )
    for code, _ in products:
        ws.append([None, code, None, None, None, None, None, None, None, None])
    ft_wb.save(base_dir / "FichasTecnicas_base.xlsx")

    prec_wb = Workbook()
    ws = prec_wb.active
    ws.append([code_header, price_header])
    ws.append([products[0][0], price])
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
    hist = {p.name for p in (imports_dir / "history").iterdir()}
    assert any(name.startswith("Produtos_Base.xlsx") for name in hist)


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


def test_import_moves_files_to_history_with_timestamp(ds, imports_dir):
    svc = ProductService(ds)
    _write_base_files(imports_dir)
    svc.import_from_excel()
    hist_files = list((imports_dir / "history").iterdir())
    assert len(hist_files) == 3
    expected = [
        "Produtos_Base.xlsx",
        "FichasTecnicas_base.xlsx",
        "PreçosTaxas_base.xlsx",
    ]
    for name in expected:
        assert not (imports_dir / name).exists()
        match = [p for p in hist_files if p.name.startswith(f"{name}.")]
        assert match
        assert re.fullmatch(rf"{re.escape(name)}\.\d{{14}}", match[0].name)


def test_update_moves_files_to_history_with_timestamp(ds, imports_dir):
    svc = ProductService(ds)
    _write_base_files(imports_dir)
    svc.update_from_excel()
    hist_files = list((imports_dir / "history").iterdir())
    assert len(hist_files) == 3
    expected = [
        "Produtos_Base.xlsx",
        "FichasTecnicas_base.xlsx",
        "PreçosTaxas_base.xlsx",
    ]
    for name in expected:
        assert not (imports_dir / name).exists()
        match = [p for p in hist_files if p.name.startswith(f"{name}.")]
        assert match
        assert re.fullmatch(rf"{re.escape(name)}\.\d{{14}}", match[0].name)


def test_import_from_excel_uses_produto_codigo(ds, imports_dir):
    _write_base_files(imports_dir, code_header="produto_codigo", price=2.5)
    svc = ProductService(ds)
    svc.import_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvp1"] == 2.5


def test_update_from_excel_uses_produto_codigo(ds, imports_dir):
    ds.conn.execute(
        "INSERT INTO Produtos (Codigo, Produto, Preco1G) VALUES ('P1', 'X', 1.0)"
    )
    ds.reload_ids()
    _write_base_files(imports_dir, code_header="produto_codigo", price=3.0)
    svc = ProductService(ds)
    svc.update_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvp1"] == 3.0


def test_import_from_excel_handles_alt_headers(ds, imports_dir):
    _write_base_files(
        imports_dir,
        code_header="Código do Produto",
        price_header="Preço1 G",
        price=2.0,
    )
    svc = ProductService(ds)
    svc.import_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvp1"] == 2.0


def test_update_from_excel_handles_alt_headers(ds, imports_dir):
    ds.conn.execute(
        "INSERT INTO Produtos (Codigo, Produto, Preco1G) VALUES ('P1', 'X', 1.0)"
    )
    ds.reload_ids()
    _write_base_files(
        imports_dir,
        code_header="Código do Produto",
        price_header="Preço1 G",
        price=4.0,
    )
    svc = ProductService(ds)
    svc.update_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvp1"] == 4.0


@pytest.mark.parametrize(
    "price,expected",
    [("1,5", 1.5), ("1 234,5", 1234.5)],
)
def test_import_from_excel_parses_formatted_numbers(ds, imports_dir, price, expected):
    _write_base_files(imports_dir, price=price)
    svc = ProductService(ds)
    svc.import_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvp1"] == expected


@pytest.mark.parametrize(
    "price,expected",
    [("1,5", 1.5), ("1 234,5", 1234.5)],
)
def test_update_from_excel_parses_formatted_numbers(ds, imports_dir, price, expected):
    ds.conn.execute(
        "INSERT INTO Produtos (Codigo, Produto, Preco1G) VALUES ('P1', 'X', 1.0)"
    )
    ds.reload_ids()
    _write_base_files(imports_dir, price=price)
    svc = ProductService(ds)
    svc.update_from_excel()
    pvps = ds.get_pvps("P1")
    assert pvps["pvp1"] == expected


@pytest.mark.parametrize("func", ["import_from_excel", "update_from_excel"])
def test_preco_taxas_requires_codigo(ds, imports_dir, func):
    _write_base_files(imports_dir, code_header="wrong")
    svc = ProductService(ds)
    with pytest.raises(ValueError):
        getattr(svc, func)()


def test_import_maps_custo_to_total(ds, imports_dir):
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
            "qtd",
            "unidade",
            "ppu",
            "custo",
            "peso",
        ]
    )
    ws.append([None, "P1", None, None, "Ing", 2, "Kg", 3, "1 234,5", None])
    ft.save(imports_dir / "FichasTecnicas_base.xlsx")

    prec = Workbook()
    ws = prec.active
    ws.append(["codigo", "preco1_g"])
    ws.append(["P1", 1])
    prec.save(imports_dir / "PreçosTaxas_base.xlsx")

    svc = ProductService(ds)
    svc.import_from_excel()
    ing = ds.get_ingredientes("P1")[0]
    assert ing["total"] == 1234.5


def test_update_maps_custo_to_total(ds, imports_dir):
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
            "qtd",
            "unidade",
            "ppu",
            "custo",
            "peso",
        ]
    )
    ws.append([None, "P1", None, None, "Ing", 3, "Kg", 2, 7, None])
    ft.save(imports_dir / "FichasTecnicas_base.xlsx")

    prec = Workbook()
    ws = prec.active
    ws.append(["codigo", "preco1_g"])
    ws.append(["P1", 1])
    prec.save(imports_dir / "PreçosTaxas_base.xlsx")

    svc = ProductService(ds)
    svc.update_from_excel()
    ing = ds.get_ingredientes("P1")[0]
    assert ing["total"] == 7


def test_private_update_from_excel_parses_numbers(ds, tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(["Código", "Nome", "Preço1 G"])
    ws.append(["P1", "Produto 1", "1 234,5"])
    path = tmp_path / "update.xlsx"
    wb.save(path)

    _update_from_excel(path, ds)
    info = ds.get_produto_info("P1")
    assert info["produto"] == "Produto 1"
    assert info["preco1g"] == 1234.5
