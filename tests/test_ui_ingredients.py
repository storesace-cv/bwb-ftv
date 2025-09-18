import pytest
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QFrame
from services.products import ProductService
from ui import layout
from ui.layout import Zone
from ui.models import build_fichas_tecnicas_model
from ui.ui_editor_fonte import FTApp
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
        return {"pvps": [], "iva": None}

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


def test_ingredient_table_has_no_frame_or_padding(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        assert ft.tbIng.frameShape() == QFrame.NoFrame
        assert not ft.tbIng.showGrid()
        style = ft.tbIng.styleSheet()
        assert "QTableView {" in style
        assert "border: none" in style
        assert "QTableView::item" in style
        assert "margin: 0" in style
        assert "padding: 0" in style
    finally:
        ft.close()


def test_load_record_uses_componente_nome_when_only_key(qapp):
    original = layout.DEV_OVERLAYS
    layout.DEV_OVERLAYS = False
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
    layout.DEV_OVERLAYS = original


def test_toggle_overlay_updates_headers(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    ft._load_record(0)
    model = ft.tbIng.model()
    assert model.headerData(0, Qt.Horizontal) == "Ingredientes"
    ft._toggle_overlays()
    assert model.headerData(0, Qt.Horizontal) == "FichasTecnicas.ComponenteNome"
    ft._toggle_overlays()
    assert model.headerData(0, Qt.Horizontal) == "Ingredientes"
    ft.close()


def test_classification_overlay_tags_hidden(qapp):
    original = layout.DEV_OVERLAYS
    layout.DEV_OVERLAYS = False
    ft = None
    try:
        ds = StubDataStore()
        service = ProductService(ds)
        ft = FTApp(service)
        ft._load_record(0)
        ft._toggle_overlays()
        qapp.processEvents()

        target_tags = [
            "B1.C1.A.2",
            "B1.C1.A.2.A",
            "B1.C1.A.2.A.2.A",
            *[f"B1.C1.A.2.A.2.A.{idx}" for idx in range(1, 6)],
            *[f"B1.C1.A.2.B.{idx}" for idx in range(1, 4)],
        ]

        for tag in target_tags:
            zone = ft.findChild(Zone, tag)
            assert zone is not None, f"Zone {tag} not found"
            assert zone._style_lbl.isHidden()
            assert zone._style_lbl.text() == ""

        for tag in ("B1.C1.A.2.A.1.A.1", "B1.C1.A.2.A.1.A.2"):
            zone = ft.findChild(Zone, tag)
            assert zone is not None, f"Zone {tag} not found"
            assert zone._base_style_label == "bwb-etiqueta-normal"

        ft._toggle_overlays()
    finally:
        if ft is not None:
            ft.close()
        layout.DEV_OVERLAYS = original


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

    ratios = {0: 0.52, 1: 0.08, 2: 0.125, 3: 0.15, 4: 0.125}
    width = ft.tbIng.viewport().width()
    for col, ratio in ratios.items():
        expected = width * ratio
        actual = ft.tbIng.columnWidth(col)
        assert actual == pytest.approx(expected, abs=2)
    ft.close()


def test_alignment_roles(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    ft._load_record(0)
    model = ft.tbIng.model()
    aligns = [
        Qt.AlignLeft | Qt.AlignVCenter,
        Qt.AlignLeft | Qt.AlignVCenter,
        Qt.AlignLeft | Qt.AlignVCenter,
        Qt.AlignLeft | Qt.AlignVCenter,
        Qt.AlignLeft | Qt.AlignVCenter,
    ]
    for col, expected in enumerate(aligns):
        assert model.data(model.index(0, col), Qt.TextAlignmentRole) == expected
        assert (
            model.headerData(col, Qt.Horizontal, Qt.TextAlignmentRole)
            == Qt.AlignLeft | Qt.AlignVCenter
        )
    ft.close()


def test_model_returns_dash_for_empty_ingredient(qapp):
    model = build_fichas_tecnicas_model(
        [FichaTecnica("", 0, "", None, None, None)], overlays=False
    )
    assert model.data(model.index(0, 0)) == "—"
    assert model.data(model.index(0, 1)) == ""
