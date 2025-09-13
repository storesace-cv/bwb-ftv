import re
import shutil
import pytest
from openpyxl import Workbook

from data.datastore import DataStore
from services.products import ProductService
from utils.paths import get_project_root


@pytest.fixture
def ds():
    ds = DataStore(":memory:")
    conn = ds.conn
    conn.execute("DROP TABLE Produtos")
    conn.execute(
        "CREATE TABLE Produtos (Codigo TEXT PRIMARY KEY, Nome TEXT, "
        "preco1_g REAL, preco2_g REAL, Iva REAL)"
    )
    conn.execute("DROP TABLE FichasTecnicas")
    conn.execute(
        "CREATE TABLE FichasTecnicas (ProdutoCodigo TEXT, "
        "ComponenteNome TEXT, qtd REAL, unidade TEXT, "
        "ppu REAL, total REAL)"
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
    ws.append(["codigo", "nome"])
    for code, name in products:
        ws.append([code, name])
    prod_wb.save(base_dir / "Produtos_Base.xlsx")

    ft_wb = Workbook()
    ws = ft_wb.active
    ws.append(["produto_codigo"])
    ft_wb.save(base_dir / "FichasTecnicas_base.xlsx")

    prec_wb = Workbook()
    ws = prec_wb.active
    ws.append([code_header, price_header])
    ws.append([products[0][0], price])
    prec_wb.save(base_dir / "PreçosTaxas_base.xlsx")


def test_import_from_excel_replaces_database(ds, imports_dir):
    ds.conn.execute("INSERT INTO Produtos (Codigo, Nome) VALUES ('OLD', 'Old')")
    ds.reload_ids()
    svc = ProductService(ds)
    _write_base_files(imports_dir, products=[("P1", "Produto 1"), ("P2", "Produto 2")])
    svc.import_from_excel()
    ds.reload_ids()

    assert ds.total() == 2
    assert ds.get_produto_info("OLD") == {}
    assert ds.get_produto_info("P1")["Nome"] == "Produto 1"
    assert ds.get_produto_info("P2")["Nome"] == "Produto 2"
    assert not (imports_dir / "Produtos_Base.xlsx").exists()
    hist = {p.name for p in (imports_dir / "history").iterdir()}
    assert any(name.startswith("Produtos_Base.xlsx") for name in hist)


def test_update_from_excel_updates_and_inserts(ds, imports_dir):
    ds.conn.executemany(
        "INSERT INTO Produtos (Codigo, Nome) VALUES (?, ?)",
        [("P1", "Produto 1"), ("P2", "Produto 2")],
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
    assert ds.get_produto_info("P1")["Nome"] == "Produto 1 updated"
    assert ds.get_produto_info("P2")["Nome"] == "Produto 2"
    assert ds.get_produto_info("P3")["Nome"] == "Produto 3"
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
        "INSERT INTO Produtos (Codigo, Nome, preco1_g) VALUES ('P1', 'X', 1.0)"
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
        "INSERT INTO Produtos (Codigo, Nome, preco1_g) VALUES ('P1', 'X', 1.0)"
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


@pytest.mark.parametrize("func", ["import_from_excel", "update_from_excel"])
def test_preco_taxas_requires_codigo(ds, imports_dir, func):
    _write_base_files(imports_dir, code_header="wrong")
    svc = ProductService(ds)
    with pytest.raises(ValueError):
        getattr(svc, func)()


def test_import_maps_custo_to_total(ds, imports_dir):
    prod = Workbook()
    ws = prod.active
    ws.append(["codigo", "nome"])
    ws.append(["P1", "Produto 1"])
    prod.save(imports_dir / "Produtos_Base.xlsx")

    ft = Workbook()
    ws = ft.active
    ws.append(["produto_codigo", "componente_nome", "qtd", "unidade", "ppu", "custo"])
    ws.append(["P1", "Ing", 2, "Kg", 3, 6])
    ft.save(imports_dir / "FichasTecnicas_base.xlsx")

    prec = Workbook()
    ws = prec.active
    ws.append(["codigo", "preco1_g"])
    ws.append(["P1", 1])
    prec.save(imports_dir / "PreçosTaxas_base.xlsx")

    svc = ProductService(ds)
    svc.import_from_excel()
    ing = ds.get_ingredientes("P1")[0]
    assert ing["total"] == 6


def test_update_maps_custo_to_total(ds, imports_dir):
    ds.conn.execute("INSERT INTO Produtos (Codigo, Nome) VALUES ('P1', 'Prod')")
    ds.conn.execute(
        "INSERT INTO FichasTecnicas "
        "(ProdutoCodigo, ComponenteNome, qtd, unidade, ppu, total) "
        "VALUES ('P1', 'Ing', 1, 'Kg', 2, 5)"
    )
    ds.reload_ids()

    prod = Workbook()
    ws = prod.active
    ws.append(["codigo", "nome"])
    ws.append(["P1", "Prod"])
    prod.save(imports_dir / "Produtos_Base.xlsx")

    ft = Workbook()
    ws = ft.active
    ws.append(["produto_codigo", "componente_nome", "qtd", "unidade", "ppu", "custo"])
    ws.append(["P1", "Ing", 3, "Kg", 2, 7])
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
