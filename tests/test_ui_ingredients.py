import pytest
from tests._qt import require_real_qt_modules

require_real_qt_modules("PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui")

from PyQt5.QtCore import QSize, Qt, QPoint
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QFrame, QSizePolicy, QHBoxLayout, QVBoxLayout, QLabel
from services.products import ProductService
from ui import layout
from ui.layout import Zone
from ui.utilities import AlignmentVariant
from ui.tagging import zone_tag
from ui.models import build_fichas_tecnicas_model
from ui.ui_editor_fonte import FTApp, ImagePreview
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
        return {
            "codigo": codigo,
            "produto": "Prod",
            "informacaoadicional": "Sem glúten",
        }

    def get_pvps(self, codigo):
        return {"pvps": [], "iva": None}

    def get_ingredientes(self, codigo):
        return [
            {
                "ComponenteNome": "Sugar",
                "Qtd": 1.5,
                "Unidade": "kg",
                "Ppu": 2.0,
                "Peso": 1.2,
                "Preco": 3.0,
                "ComponenteCodigo": "A1",
            },
            {
                "ComponenteNome": "Salt",
                "Qtd": 0.5,
                "Unidade": "kg",
                "Ppu": 1.5,
                "Peso": 0.4,
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
    assert ft.lbInformacaoAdicional.text() == "Sem glúten"
    assert model.rowCount() == 2
    expected = ds.get_ingredientes("P1")
    for row, data in enumerate(expected):
        assert model.data(model.index(row, 0)) == data["ComponenteNome"]
        assert model.data(model.index(row, 1)) == format_pt_number(data["Qtd"])
        assert model.data(model.index(row, 2)) == data["Unidade"]
        assert model.data(model.index(row, 3)) == format_pt_number(data["Ppu"])
        assert model.data(model.index(row, 4)) == format_pt_number(data["Preco"])
        assert model.data(model.index(row, 5)) == format_pt_number(data["Peso"])
        assert model.item(row, 0).textAlignment() == Qt.AlignLeft | Qt.AlignVCenter
        for col in range(1, 6):
            assert model.item(row, col).textAlignment() == Qt.AlignRight | Qt.AlignVCenter
    assert not ft.tbIng.isColumnHidden(0)
    assert model.columnCount() == 6
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
        zone = ft.findChild(Zone, "B1.C1.A.1.1")
        assert zone is not None
        stylesheet = zone.base_stylesheet
        assert "border-bottom-width: 2px" in stylesheet
        assert "border-bottom-style: groove" in stylesheet
        assert "border-bottom: 2px groove #f7f9fc" in stylesheet
        margins = zone.ly.contentsMargins()
        assert margins.top() == 8
        assert margins.bottom() == 8
    finally:
        ft.close()


def test_family_zone_has_vertical_spacing_and_border(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        zone = ft.findChild(Zone, "B1.C1.A.1.2")
        assert zone is not None
        margins = zone.ly.contentsMargins()
        assert margins.top() == 8
        assert margins.bottom() == 8
        stylesheet = zone.base_stylesheet
        assert "border-radius: 12px" in stylesheet
        assert "padding: 6px" in stylesheet
        assert "border-bottom-width: 2px" in stylesheet
        assert "border-bottom-style: groove" in stylesheet
        assert "border-bottom: 2px groove #f7f9fc" in stylesheet
    finally:
        ft.close()


def test_legend_labels_use_expanding_horizontal_policy(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        legend_tags = ["B1.C1.A.1.1.A.1", "B1.C1.A.1.1.C.1"]
        for tag in legend_tags:
            zone = ft.findChild(Zone, tag)
            assert zone is not None, f"Zone {tag} not found"
            assert (
                zone.sizePolicy().horizontalPolicy() == QSizePolicy.Expanding
            ), f"Zone {tag} should expand horizontally"
            assert zone._labels, f"Zone {tag} should register legend labels"
            for label in zone._labels:
                assert (
                    label.sizePolicy().horizontalPolicy() == QSizePolicy.Expanding
                ), f"Legend label in {tag} should expand horizontally"
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


def test_article_sheet_left_slots_expand_full_width(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        parent_zone = ft.findChild(Zone, "B1.C1.A")
        assert parent_zone is not None

        slot_tags = ["B1.C1.A.1", "B1.C1.A.2", "B1.C1.A.3", "B1.C1.A.4"]
        slots = []
        for tag in slot_tags:
            zone = ft.findChild(Zone, tag)
            assert zone is not None, f"Expected zone {tag} to exist"
            assert zone.parent() is parent_zone
            assert zone.sizePolicy().horizontalPolicy() == QSizePolicy.Expanding
            assert zone.sizePolicy().verticalPolicy() == QSizePolicy.Expanding
            slots.append(zone)

        # All slots should share the same layout container as siblings
        assert all(slot.parent() is parent_zone for slot in slots)

        # Slots originate from a split_v call with equal ratios (25% each)
        shared_parent = slots[0].parentWidget()
        layout = shared_parent.layout()
        assert isinstance(layout, QVBoxLayout)
        indices = [layout.indexOf(slot) for slot in slots]
        assert all(idx != -1 for idx in indices)
        stretches = [layout.stretch(idx) for idx in indices]
        assert all(stretch == 1 for stretch in stretches)
    finally:
        ft.close()


def test_additional_info_zone_stretch_matches_parent(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        parent_zone = ft.findChild(Zone, "B1.C1.A.2.A")
        assert parent_zone is not None, "Zone B1.C1.A.2.A should exist"

        child_zone = ft.findChild(Zone, "B1.C1.A.2.A.2")
        assert child_zone is not None, "Zone B1.C1.A.2.A.2 should exist"
        assert child_zone.parent() is parent_zone

        layout = parent_zone.layout()
        assert isinstance(layout, QVBoxLayout)

        index = layout.indexOf(child_zone)
        assert index != -1, "Child zone should be in the parent layout"
        assert (
            layout.stretch(index) == 1
        ), "Child zone stretch should match the parent section weight"
    finally:
        ft.close()


def test_pvps_zone_is_visible_without_legend_label(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        zone = ft.findChild(Zone, "B1.C1.A.3")
        assert zone is not None, "Expected zone B1.C1.A.3 to exist"
        assert not zone.isHidden(), "Zone B1.C1.A.3 should remain visible"

        labels = zone.findChildren(QLabel)
        assert all(
            label.text() != "PREÇOS DE VENDA" for label in labels
        ), "Zone B1.C1.A.3 should not contain the 'PREÇOS DE VENDA' legend"
    finally:
        ft.close()


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


def test_article_sheet_left_overlay_heights_reflect_stretch(qapp):
    original = layout.DEV_OVERLAYS
    layout.DEV_OVERLAYS = True
    ft = None
    try:
        ds = StubDataStore()
        service = ProductService(ds)
        ft = FTApp(service)
        qapp.processEvents()

        expected_percentages = {
            "B1.C1.A.1": "25%",
            "B1.C1.A.2": "15%",
            "B1.C1.A.3": "25%",
            "B1.C1.A.4": "35%",
        }

        for tag, percentage in expected_percentages.items():
            zone = ft.findChild(Zone, tag)
            assert zone is not None, f"Zone {tag} should exist"
            info = zone._style_dev_info
            assert info is not None, f"Zone {tag} should expose style dev info"
            assert (
                f"height: {percentage}" in info
            ), f"Zone {tag} should report height {percentage}, got {info!r}"
    finally:
        if ft is not None:
            ft.close()
        layout.DEV_OVERLAYS = original


def test_validate_tag_accepts_family_root(qapp):
    assert layout.validate_tag("B1.C1.A.2")
    zone = Zone("B1.C1.A.2")
    try:
        assert zone.objectName() == "B1.C1.A.2"
    finally:
        zone.deleteLater()


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

        target_keys = [
            "general_aux_identification_slot",
            "general_aux_family_slot",
            "family_labels_column",
            "family_values_column",
            "general_aux_additional_info_section",
            "general_aux_additional_info_field",
            "general_aux_prices_slot",
        ]
        pvps_keys = [
            "pvps_col_1",
            "pvps_col_2",
            "pvps_col_3",
            "pvps_col_4",
            "pvps_col_5",
        ]
        target_tags = [zone_tag(key) for key in (*target_keys, *pvps_keys)]

        for tag in target_tags:
            zone = ft.findChild(Zone, tag)
            assert zone is not None, f"Zone {tag} not found"
            assert zone._style_lbl.isHidden()
            assert zone._style_lbl.text() == ""

        for key in ("family_label_familia", "family_label_subfamilia"):
            tag = zone_tag(key)
            zone = ft.findChild(Zone, tag)
            assert zone is not None, f"Zone {tag} not found"
            margins = zone.ly.contentsMargins()
            assert margins.left() == 0
            assert margins.right() == 0
            assert zone._label_alignment is AlignmentVariant.RIGHT
            stylesheet = zone.base_stylesheet
            assert "border-radius: 12px" in stylesheet
            assert "padding: 6px" in stylesheet
            assert "linear-gradient" not in stylesheet

        ft._toggle_overlays()
    finally:
        if ft is not None:
            ft.close()
        layout.DEV_OVERLAYS = original


def test_general_aux_additional_slots_created(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        ft.show()
        qapp.processEvents()

        for tag in ("B1.A1.B", "B1.A1.C", "B1.A1.D"):
            zone = ft.findChild(Zone, tag)
            assert zone is None, f"Zone {tag} should have been removed"

        preview_zone = ft.findChild(Zone, "B1.A1.E")
        assert preview_zone is None, "Legacy preview zone B1.A1.E should be removed"

        right_zone = ft.findChild(Zone, "B1.C1.B")
        assert right_zone is not None, "Expected preview column B1.C1.B to exist"

        preview_widget = right_zone.findChild(ImagePreview)
        assert preview_widget is not None, "ImagePreview should reside in B1.C1.B"
        assert preview_widget is ft.image_preview
        assert right_zone.isAncestorOf(ft.image_preview)
    finally:
        ft.close()


def test_general_aux_reserved_slots_removed(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        removed_tags = ("B1.A1.2", "B1.A1.3", "B1.A1.4", "B1.A1.5")
        for tag in removed_tags:
            zone = ft.findChild(Zone, tag)
            assert zone is None, f"Zone {tag} should have been removed"

        prices_zone = ft.findChild(Zone, "B1.C1.A.3")
        assert prices_zone is not None, "Zone B1.C1.A.3 should exist"
        assert not prices_zone.isHidden(), "Zone B1.C1.A.3 should be visible"
        assert prices_zone.ly.count() > 0, "Zone B1.C1.A.3 should contain widgets"
    finally:
        ft.close()


def test_article_sheet_zones_use_two_to_one_ratio(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        ft.show()
        qapp.processEvents()

        root_zone = ft.findChild(Zone, "B1.C1")
        assert root_zone is not None, "Expected article sheet root zone B1.C1"

        left_zone = ft.findChild(Zone, "B1.C1.A")
        right_zone = ft.findChild(Zone, "B1.C1.B")
        assert left_zone is not None, "Expected article sheet left zone"
        assert right_zone is not None, "Expected article sheet right zone"

        container = left_zone.parentWidget()
        assert container is not None
        layout = container.layout()
        assert isinstance(layout, QHBoxLayout)

        left_index = layout.indexOf(left_zone)
        right_index = layout.indexOf(right_zone)
        assert left_index != -1 and right_index != -1
        assert layout.stretch(left_index) == 2
        assert layout.stretch(right_index) == 1

        for zone in (root_zone, left_zone, right_zone):
            margins = zone.ly.contentsMargins()
            assert margins.left() == 0
            assert margins.right() == 0
            assert margins.top() == 0
            assert margins.bottom() == 0
            policy = zone.sizePolicy()
            assert policy.horizontalPolicy() == QSizePolicy.Expanding
            assert policy.verticalPolicy() == QSizePolicy.Expanding

        assert right_zone.findChild(ImagePreview) is ft.image_preview
        assert left_zone.findChild(ImagePreview) is None
    finally:
        ft.close()


def test_identification_and_family_label_columns_expand_with_long_text(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        ft.show()
        qapp.processEvents()

        ident_zone = ft.findChild(Zone, "B1.C1.A.1.1.A")
        family_zone = ft.findChild(Zone, "B1.C1.A.1.1.C")

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

        caption_zone = ft.findChild(Zone, "B1.C1.A.1.1.A.1")
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
