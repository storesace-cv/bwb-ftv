import pytest
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QResizeEvent
from services.products import ProductService
from ui.ui_editor_fonte import FTApp, FichasTecnicasModel
from domain import FichaTecnica
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
        return {"pvp": None, "iva": None}

    def get_ingredientes(self, codigo):
        return [
            {
                "ComponenteNome": "Sugar",
                "Qtd": 1.5,
                "Unidade": "kg",
                "Ppu": 2.0,
                "Preco": 3.0,
                "ComponenteCodigo": "A1",
            },
            {
                "ComponenteNome": "Salt",
                "Qtd": 0.5,
                "Unidade": "kg",
                "Ppu": 1.5,
                "Preco": 0.75,
                "ComponenteCodigo": "A2",
            },
        ]


class NameOnlyStubDataStore(StubDataStore):
    def get_ingredientes(self, codigo):
        return [
            {"ComponenteNome": "Sugar"},
            {"ComponenteNome": "Salt"},
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
        assert model.data(model.index(row, 0)) == data["ComponenteNome"]
        assert model.data(model.index(row, 1)) == format_pt_number(data["Qtd"])
        assert model.data(model.index(row, 2)) == data["Unidade"]
        assert model.data(model.index(row, 3)) == format_pt_number(data["Ppu"])
        assert model.data(model.index(row, 4)) == format_pt_number(data["Preco"])
    assert not ft.tbIng.isColumnHidden(0)
    assert model.columnCount() == 5
    assert not ft.tbIng.verticalHeader().isVisible()
    ft.close()


def test_load_record_uses_componente_nome_when_only_key(qapp):
    ds = NameOnlyStubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    ft._load_record(0)
    model = ft.tbIng.model()
    assert model.rowCount() == 2
    assert model.headerData(0, Qt.Horizontal) == "Ingredientes"
    assert model.data(model.index(0, 0)) == "Sugar"
    assert model.data(model.index(1, 0)) == "Salt"
    ft.close()


class VarStubDataStore(StubDataStore):
    def __init__(self, n):
        self.n = n

    def get_ingredientes(self, codigo):
        return [
            {
                "ComponenteNome": f"Ing{i}",
                "Qtd": 1.0,
                "Unidade": "kg",
                "Ppu": 1.0,
                "Preco": 1.0,
                "ComponenteCodigo": f"C{i}",
            }
            for i in range(self.n)
        ]


@pytest.mark.parametrize("rows", [1, 5, 6])
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
    visible = min(rows, 5)
    expected_h = (
        hh.height()
        + row_h * visible
        + frame * 2
        + ft.tbIng.horizontalScrollBar().height()
    )
    assert ft.tbIng.height() == expected_h
    assert ft.tbIng.verticalScrollBar().isVisible() == (rows >= 6)
    ft.close()


def test_apply_ingredient_widths_after_resize(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    ft._load_record(0)
    ft.show()
    qapp.processEvents()

    new_width = 1600
    old_size = ft.size()
    ev = QResizeEvent(QSize(new_width, old_size.height()), old_size)
    ft.resize(new_width, old_size.height())
    ft.resizeEvent(ev)
    ft._apply_ingredient_widths()
    qapp.processEvents()

    ratios = {0: 0.4444, 1: 0.1389, 2: 0.0833, 3: 0.1667, 4: 0.1667}
    width = ft.tbIng.viewport().width()
    for col, ratio in ratios.items():
        expected = width * ratio
        actual = ft.tbIng.columnWidth(col)
        assert actual == pytest.approx(expected, abs=2)
    ft.close()


def test_model_returns_dash_for_empty_ingredient(qapp):
    model = FichasTecnicasModel([FichaTecnica("", 0, "", None, None, None)])
    assert model.data(model.index(0, 0)) == "—"
    assert model.data(model.index(0, 1)) is None
