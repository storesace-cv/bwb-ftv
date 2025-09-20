import pytest
from PyQt5.QtCore import QSize, Qt, QPoint
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget
from services.products import ProductService
from ui import layout
from ui.layout import Zone
from ui.utilities import AlignmentVariant
from ui.tagging import zone_tag
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


def test_ingredient_table_style_includes_bottom_border(qapp):
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
        assert "border-bottom: 1px solid #dfe3eb" in style
        assert "QTableView::item:last" in style
        assert "border-bottom: none" in style
    finally:
        ft.close()


def test_identification_zone_has_embossed_bottom_border(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        zone = ft.findChild(Zone, "B1.C1.A.1")
        assert zone is not None
        stylesheet = zone.base_stylesheet
        assert "border-bottom-width: 2px" in stylesheet
        assert "border-bottom-style: groove" in stylesheet
        assert "border-bottom: 2px groove #f7f9fc" in stylesheet
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
            "B1.C1.A.2.A.1",
            "B1.C1.A.2.A.2",
            "B1.C1.A.2.A.3",
            "B1.C1.A.2.A.1.A",
            "B1.C1.A.2.A.1.A.1",
            "B1.C1.A.2.A.1.A.2",
            "B1.C1.A.2.A.1.B",
            "B1.C1.A.2.A.1.B.1",
            "B1.C1.A.2.A.1.B.2",
            "B1.C1.A.2.B",
            "B1.C1.A.2.B.A",
            "B1.C1.A.2.B.B",
            "B1.C1.A.2.B.B.1",
        ]

        for tag in target_tags:
            zone = ft.findChild(Zone, tag)
            assert zone is not None, f"Zone {tag} not found"
            assert zone._style_lbl.isHidden()
            assert zone._style_lbl.text() == ""

        combos_container = ft.findChild(
            Zone, zone_tag("family_combos_container")
        )
        combos_wrapper = ft.findChild(Zone, zone_tag("family_combos_wrapper"))
        combos_section = ft.findChild(Zone, zone_tag("family_combos_section"))
        assert combos_container is not None
        assert combos_wrapper is not None
        assert combos_section is not None
        assert isinstance(combos_container.ly, QHBoxLayout)
        assert isinstance(combos_wrapper.ly, QHBoxLayout)
        assert isinstance(combos_section.ly, QHBoxLayout)
        assert combos_wrapper.parentWidget() is combos_container
        assert combos_section.parentWidget() is combos_wrapper
        column_widgets = []
        for i in range(combos_section.ly.count()):
            item = combos_section.ly.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget and widget is not combos_section._tag_container:
                column_widgets.append(widget)
        assert len(column_widgets) == 3

        combo_label_zones = [
            ft.findChild(Zone, zone_tag("family_combo_label_col_1")),
            ft.findChild(Zone, zone_tag("family_combo_label_col_2")),
            ft.findChild(Zone, zone_tag("family_combo_label_col_3")),
        ]
        combo_field_zones = [
            ft.findChild(Zone, zone_tag("family_combo_field_col_1")),
            ft.findChild(Zone, zone_tag("family_combo_field_col_2")),
            ft.findChild(Zone, zone_tag("family_combo_field_col_3")),
        ]
        assert all(zone is not None for zone in combo_label_zones)
        assert all(zone is not None for zone in combo_field_zones)
        for label_zone, field_zone in zip(combo_label_zones, combo_field_zones):
            label_parent = label_zone.parentWidget()
            field_parent = field_zone.parentWidget()
            assert isinstance(label_parent, QWidget)
            assert label_parent is field_parent
            assert label_parent.parentWidget() is combos_section
            parent_layout = label_parent.layout()
            assert isinstance(parent_layout, QVBoxLayout)
            assert parent_layout.indexOf(label_zone) != -1
            assert parent_layout.indexOf(field_zone) != -1
        for label_zone in combo_label_zones:
            assert label_zone.widget_type == "legenda"
            assert label_zone.widget_qt_class == "QLabels"
            assert label_zone.zone_type == "linha-legenda"
        for field_zone in combo_field_zones:
            assert field_zone.widget_type == "lista"
            assert field_zone.widget_qt_class == "QComboBoxes"
            assert field_zone.zone_type == "combo-lista"

        for tag in ("B1.C1.A.2.A.1.A.1", "B1.C1.A.2.A.1.A.2"):
            zone = ft.findChild(Zone, tag)
            assert zone is not None, f"Zone {tag} not found"
            margins = zone.ly.contentsMargins()
            assert margins.left() == 0
            assert margins.right() == 0
            assert zone._label_alignment is AlignmentVariant.RIGHT
            assert zone._base_style_label is None
            assert "linear-gradient" not in zone.base_stylesheet

        ft._toggle_overlays()
    finally:
        if ft is not None:
            ft.close()
        layout.DEV_OVERLAYS = original


def test_identification_and_family_label_columns_expand_with_long_text(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        ft.show()
        qapp.processEvents()

        ident_zone = ft.findChild(Zone, "B1.C1.A.1.A")
        family_zone = ft.findChild(Zone, "B1.C1.A.2.A.1.A")

        assert ident_zone is not None
        assert family_zone is not None

        initial_width = ident_zone.width()
        assert ident_zone.width() == family_zone.width()

        origin = QPoint(0, 0)
        ident_x = ident_zone.mapToGlobal(origin).x()
        family_x = family_zone.mapToGlobal(origin).x()

        assert ident_x == family_x

        long_text = (
            "Família / Categoria com descrição muitíssimo longa para validar largura"
        )
        assert family_zone._labels, "expected labels in family zone"
        family_zone._labels[0].setText(long_text)

        ft._refresh_family_label_column_widths()
        qapp.processEvents()

        assert ident_zone.width() == family_zone.width()
        assert ident_zone.width() > initial_width
    finally:
        ft.close()


def test_family_caption_zone_keeps_padding_gap(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        ft.show()
        qapp.processEvents()

        ft._refresh_family_label_column_widths()
        qapp.processEvents()

        caption_zone = ft.findChild(Zone, "B1.C1.A.1.A.1")
        assert caption_zone is not None
        assert caption_zone._labels, "expected caption label in zone"

        caption_label = caption_zone._labels[0]
        zone_width = caption_zone.geometry().width()
        label_width = caption_label.geometry().width()

        assert zone_width - label_width == 6
    finally:
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
