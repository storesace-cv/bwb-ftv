import pytest
from services.products import ProductService
from ui.ui_editor_fonte import FTApp
from utils.formatting import format_pt_number


class StubDataStore:
    def total(self):
        return 1

    def codigo_at(self, idx):
        return "P1"

    def list_tipos_artigos(self):
        return []

    def list_validade(self):
        return []

    def list_temperaturas(self):
        return []

    def list_active_allergens(self):
        return []

    def get_produto_info(self, codigo):
        return {"codigo": codigo, "produto": "Prod"}

    def get_pvps(self, codigo):
        return {}

    def get_ingredientes(self, codigo):
        return [
            {
                "nome": "Sugar",
                "qtd": 1.5,
                "unidade": "kg",
                "ppu": 2.0,
                "total": 3.0,
                "codigo": "A1",
            },
            {
                "nome": "Salt",
                "qtd": 0.5,
                "unidade": "kg",
                "ppu": 1.5,
                "total": 0.75,
                "codigo": "A2",
            },
        ]


def test_load_record_populates_ingredients(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    ft._load_record(0)
    model = ft.tbIng.model()
    assert model.rowCount() == 2
    expected = ds.get_ingredientes("P1")
    for row, data in enumerate(expected):
        assert model.data(model.index(row, 0)) == data["nome"]
        assert model.data(model.index(row, 1)) == format_pt_number(data["qtd"])
        assert model.data(model.index(row, 2)) == data["unidade"]
        assert model.data(model.index(row, 3)) == format_pt_number(data["ppu"])
        assert model.data(model.index(row, 4)) == format_pt_number(data["total"])
    assert ft.tbIng.isColumnHidden(5)
    assert not ft.tbIng.verticalHeader().isVisible()
    ft.close()


class VarStubDataStore(StubDataStore):
    def __init__(self, n):
        self.n = n

    def get_ingredientes(self, codigo):
        return [
            {
                "nome": f"Ing{i}",
                "qtd": 1.0,
                "unidade": "kg",
                "ppu": 1.0,
                "total": 1.0,
                "codigo": f"C{i}",
            }
            for i in range(self.n)
        ]


@pytest.mark.parametrize("rows", [1, 8, 9])
def test_apply_ing_autofit_or_scroll(rows, qapp):
    ds = VarStubDataStore(rows)
    service = ProductService(ds)
    ft = FTApp(service)
    ft._load_record(0)
    ft.show()
    ft._apply_ing_autofit_or_scroll()
    qapp.processEvents()
    vh = ft.tbIng.verticalHeader()
    hh = ft.tbIng.horizontalHeader()
    frame = ft.tbIng.frameWidth()
    row_h = vh.defaultSectionSize()
    visible = min(rows, 8)
    expected_h = hh.height() + row_h * visible + frame * 2
    assert ft.tbIng.height() == expected_h
    assert ft.tbIng.verticalScrollBar().isVisible() == (rows >= 9)
    ft.close()
