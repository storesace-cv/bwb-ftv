import pytest
from openpyxl import Workbook

from data.datastore import DataStore
from services.products import ProductService


@pytest.fixture
def ds():
    ds = DataStore(":memory:")
    conn = ds.conn
    # Minimal schema for products
    conn.execute("CREATE TABLE produtos (codigo TEXT PRIMARY KEY, nome TEXT)")
    # Ingredients table (may be unused but keeps schema closer to real)
    conn.execute(
        "CREATE TABLE fichas_tecnicas (produto_codigo TEXT, "
        "componente_nome TEXT, qtd REAL, unidade TEXT, "
        "ppu REAL, custo REAL)"
    )
    return ds


def _write_import_excel(path):
    wb = Workbook()
    ws = wb.active
    ws.append(["codigo", "nome"])
    ws.append(["P1", "Produto 1"])
    ws.append(["P2", "Produto 2"])
    wb.save(path)


def _write_update_excel(path):
    wb = Workbook()
    ws = wb.active
    ws.append(["codigo", "nome"])
    ws.append(["P1", "Produto 1 updated"])
    ws.append(["P3", "Produto 3"])
    wb.save(path)


def test_import_from_excel_replaces_database(ds, tmp_path):
    # Prepopulate with stale data
    ds.conn.execute("INSERT INTO produtos (codigo, nome) VALUES ('OLD', 'Old')")
    ds.reload_ids()
    svc = ProductService(ds)
    excel_path = tmp_path / "import.xlsx"
    _write_import_excel(excel_path)

    svc.import_from_excel(str(excel_path))
    ds.reload_ids()

    assert ds.total() == 2
    assert ds.get_produto_info("OLD") == {}
    assert ds.get_produto_info("P1")["nome"] == "Produto 1"
    assert ds.get_produto_info("P2")["nome"] == "Produto 2"


def test_update_from_excel_updates_and_inserts(ds, tmp_path):
    ds.conn.executemany(
        "INSERT INTO produtos (codigo, nome) VALUES (?, ?)",
        [("P1", "Produto 1"), ("P2", "Produto 2")],
    )
    ds.reload_ids()
    svc = ProductService(ds)
    excel_path = tmp_path / "update.xlsx"
    _write_update_excel(excel_path)

    svc.update_from_excel(str(excel_path))
    ds.reload_ids()

    assert ds.total() == 3
    assert ds.get_produto_info("P1")["nome"] == "Produto 1 updated"
    assert ds.get_produto_info("P2")["nome"] == "Produto 2"
    assert ds.get_produto_info("P3")["nome"] == "Produto 3"


def test_import_from_excel_missing_file(ds):
    svc = ProductService(ds)
    with pytest.raises(FileNotFoundError):
        svc.import_from_excel("/no/such/file.xlsx")


def test_import_from_excel_invalid_format(ds, tmp_path):
    svc = ProductService(ds)
    fake = tmp_path / "fake.txt"
    fake.write_text("not excel")
    with pytest.raises(ValueError):
        svc.import_from_excel(str(fake))


def test_update_from_excel_missing_file(ds):
    svc = ProductService(ds)
    with pytest.raises(FileNotFoundError):
        svc.update_from_excel("/no/such/file.xlsx")


def test_update_from_excel_invalid_format(ds, tmp_path):
    svc = ProductService(ds)
    fake = tmp_path / "fake.txt"
    fake.write_text("not excel")
    with pytest.raises(ValueError):
        svc.update_from_excel(str(fake))
