import pytest

# Skip when the PyQt5/libGL runtime is unavailable on the test machine.
pytest.importorskip("PyQt5", reason="PyQt5 requires libGL.so.1")

from PyQt5.QtCore import Qt, qInstallMessageHandler
from PyQt5.QtWidgets import QLabel, QLineEdit

from domain import Product
from ui import layout
from ui.bwb_style_1 import OVERLAY_ON_CLASS
from ui.ui_editor_fonte import FTApp, _configure_zone
from ui.utilities import (
    AlignmentVariant,
    CENTER_FIELD_STYLE,
    CENTER_LABEL_STYLE,
    LABEL_STYLE,
    apply_label_style,
    apply_overlay_label_style,
    make_readonly_lineedit,
)


BASE_STYLE_DECLARATIONS = (
    "background: rgba(245, 245, 245, 0.8);\n"
    "border: 1px solid rgba(0, 0, 0, 0.15);\n"
    "border-radius: 8px;\n"
    "padding: 6px;\n"
)

ALT_STYLE_DECLARATIONS = (
    "background: #f0f;\n"
    "border: 1px solid #000;\n"
    "border-radius: 4px;\n"
    "padding: 4px;\n"
)


def _base_stylesheet(zone: layout.Zone, declarations: str) -> str:
    return layout.compose_stylesheet(zone, declarations)


def _tag_stylesheet(tag: str, declarations: str) -> str:
    selector = f"#{layout._escape_object_name(tag)}" if tag else ""
    return f"{selector} {{ {declarations} }}" if selector else declarations


def _overlay_stylesheet(zone: layout.Zone) -> str:
    selector = (
        f"#{layout._escape_object_name(zone.objectName())}"
        if zone.objectName()
        else ""
    )
    background = layout.bg_for_level(zone._level)
    return (
        f"{selector} {{ background:{background}; border:2px dashed blue; }}"
        if selector
        else f"background:{background}; border:2px dashed blue;"
    )


def _widget_classes(widget: QLabel) -> list[str]:
    value = widget.property("class")
    if value is None:
        return []
    if isinstance(value, str):
        return [cls for cls in value.split() if cls]
    if isinstance(value, (list, tuple)):
        return [str(cls) for cls in value if str(cls)]
    return [str(value)]


def _compose_style_label(
    zone: layout.Zone,
    style_label: str | None,
) -> str:
    return " | ".join(
        segment
        for segment in (
            zone.zone_type,
            zone.widget_qt_class,
            zone.widget_type,
            style_label,
        )
        if segment
    )


def test_apply_label_style_center_variant_sets_alignment(qapp):
    label = QLabel("Centro")
    apply_label_style(label, alignment=AlignmentVariant.CENTER)

    assert label.styleSheet() == CENTER_LABEL_STYLE
    assert label.alignment() == Qt.AlignHCenter | Qt.AlignVCenter
    assert label.property("labelAlignmentVariant") == AlignmentVariant.CENTER.value


def test_apply_label_style_reuses_stored_alignment(qapp):
    label = QLabel("Centro")
    apply_label_style(label, alignment=AlignmentVariant.CENTER)

    apply_label_style(label)

    assert label.styleSheet() == CENTER_LABEL_STYLE
    assert label.alignment() == Qt.AlignHCenter | Qt.AlignVCenter


def test_apply_overlay_label_style_preserves_alignment_variant(qapp):
    label = QLabel("Centro")
    apply_label_style(label, alignment=AlignmentVariant.CENTER)

    apply_overlay_label_style(label)
    assert label.styleSheet() == ""

    apply_label_style(label)

    assert label.styleSheet() == CENTER_LABEL_STYLE
    assert label.alignment() == Qt.AlignHCenter | Qt.AlignVCenter


def test_make_readonly_lineedit_center_variant(qapp):
    le = QLineEdit("0")
    make_readonly_lineedit(le, alignment=AlignmentVariant.CENTER)

    assert le.isReadOnly()
    assert le.styleSheet() == CENTER_FIELD_STYLE
    assert le.alignment() == Qt.AlignHCenter | Qt.AlignVCenter
    assert le.property("lineEditAlignmentVariant") == AlignmentVariant.CENTER.value

    make_readonly_lineedit(le)

    assert le.styleSheet() == CENTER_FIELD_STYLE
    assert le.alignment() == Qt.AlignHCenter | Qt.AlignVCenter


@pytest.fixture
def overlays_enabled():
    original = layout.DEV_OVERLAYS
    layout.DEV_OVERLAYS = True
    try:
        yield
    finally:
        layout.DEV_OVERLAYS = original


def test_zone_overlay_property_updates(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=True)
    assert zone.property("overlays") == "on"
    zone.apply_overlays(False)
    assert zone.property("overlays") == "off"
    zone.apply_overlays(True)
    assert zone.property("overlays") == "on"


def test_zone_apply_overlays_restores_text_and_border(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=False)
    value_widget = QLabel("value", zone)
    label = zone.add_row("Nome", value_widget, overlay_text="Overlay")
    expected_off_style = zone.styleSheet()
    expected_on_style = _overlay_stylesheet(zone)
    normal_label_style = label.styleSheet()
    assert normal_label_style == LABEL_STYLE
    original_value_style = value_widget.styleSheet()
    font_signature = label.font().toString()
    sample_text = "Overlay"
    base_metrics = (
        label.fontMetrics().height(),
        label.fontMetrics().horizontalAdvance(sample_text),
    )
    base_alignment = label.alignment()

    zone.apply_overlays(False)
    assert label.text() == "Nome"
    assert zone.styleSheet() == expected_off_style
    assert label.styleSheet() == normal_label_style
    assert OVERLAY_ON_CLASS not in _widget_classes(label)
    assert value_widget.styleSheet() == original_value_style
    assert label.font().toString() == font_signature
    assert (
        label.fontMetrics().height(),
        label.fontMetrics().horizontalAdvance(sample_text),
    ) == base_metrics
    assert label.alignment() == base_alignment

    zone.apply_overlays(True)
    assert label.text() == "Overlay"
    assert zone.styleSheet() == expected_on_style
    assert label.styleSheet() == ""
    assert OVERLAY_ON_CLASS in _widget_classes(label)
    assert value_widget.styleSheet() == original_value_style
    assert label.font().toString() == font_signature
    assert (
        label.fontMetrics().height(),
        label.fontMetrics().horizontalAdvance(sample_text),
    ) == base_metrics
    assert label.alignment() == base_alignment

    zone.apply_overlays(False)
    assert label.text() == "Nome"
    assert zone.styleSheet() == expected_off_style
    assert label.styleSheet() == normal_label_style
    assert OVERLAY_ON_CLASS not in _widget_classes(label)
    assert value_widget.styleSheet() == original_value_style
    assert label.font().toString() == font_signature
    assert (
        label.fontMetrics().height(),
        label.fontMetrics().horizontalAdvance(sample_text),
    ) == base_metrics
    assert label.alignment() == base_alignment


def test_zone_apply_overlays_updates_label_tooltips(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=False)
    value_widget = QLabel("value", zone)
    label = zone.add_row("Nome", value_widget, overlay_text="Produtos.Nome")

    manual_label = QLabel("Manual", zone)
    manual_label.setProperty("userLabel", "Manual")
    manual_label.setProperty("devLabel", "Manual.Dev")
    zone.ly.addWidget(manual_label)
    zone._labels.append(manual_label)

    assert label.toolTip() == ""
    assert manual_label.toolTip() == ""

    zone.apply_overlays(True)

    assert label.toolTip() == "Nome — Produtos.Nome"
    assert manual_label.toolTip() == "Manual — Manual.Dev"
    assert manual_label.text() == "Manual.Dev"

    zone.apply_overlays(False)

    assert label.toolTip() == ""
    assert manual_label.toolTip() == ""
    assert manual_label.text() == "Manual"


def test_zone_overlay_tag_label_preserves_inline_style(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=True)
    expected_style = "color:#c00; font-size:10px; background:none; border:none;"

    assert zone._tag_lbl.styleSheet() == expected_style

    zone.apply_overlays(False)
    assert zone._tag_lbl.styleSheet() == expected_style


def test_zone_overlay_resizes_label_width_for_overlay_text(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=False)
    overlay_text = "Legenda de desenvolvimento bastante longa"
    value_widget = QLabel("valor", zone)
    label = zone.add_row("ID", value_widget, overlay_text=overlay_text)

    user_metrics = label.fontMetrics().horizontalAdvance(label.text())
    user_width = label.minimumWidth()

    assert user_width >= user_metrics

    zone.apply_overlays(True)
    qapp.processEvents()

    overlay_metrics = label.fontMetrics().horizontalAdvance(overlay_text)
    overlay_width = label.minimumWidth()

    assert overlay_width >= overlay_metrics
    assert overlay_width > user_width

    zone.apply_overlays(False)
    qapp.processEvents()

    restored_width = label.minimumWidth()
    restored_metrics = label.fontMetrics().horizontalAdvance(label.text())

    assert restored_width >= restored_metrics
    assert restored_width < overlay_width


def test_zone_overlay_label_width_tracks_visible_text(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=False)
    value_widget = QLabel("value", zone)
    overlay_text = "Identificador extendido"
    label = zone.add_row("ID", value_widget, overlay_text=overlay_text)

    qapp.processEvents()
    initial_width = label.minimumWidth()
    user_text_width = label.fontMetrics().horizontalAdvance("ID")
    assert initial_width >= user_text_width

    zone.apply_overlays(True)
    qapp.processEvents()
    overlay_width = label.minimumWidth()
    overlay_text_width = label.fontMetrics().horizontalAdvance(overlay_text)
    assert overlay_width >= overlay_text_width
    assert overlay_width > initial_width

    zone.apply_overlays(False)
    qapp.processEvents()
    reverted_width = label.minimumWidth()
    assert reverted_width == initial_width


def test_zone_style_label_tooltip_tracks_dev_info(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=False)
    zone.set_zone_type("secao")
    zone.set_widget_type("campo")
    zone.set_widget_qt_class("QLineEdits")
    dev_info = "FichaTecnica.Dev"
    zone.set_style_dev_info(dev_info)

    zone.apply_overlays(True)

    expected_text = _compose_style_label(zone, None)
    expected_tooltip = layout.Zone._build_label_tooltip(expected_text, dev_info)

    assert zone._style_lbl.text() == expected_text
    assert zone._style_lbl.toolTip() == expected_tooltip

    zone.apply_overlays(False)

    assert zone._style_lbl.toolTip() == ""


def test_configure_zone_sets_dev_info_tooltip(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=True)

    _configure_zone(zone, zone_type="secao", widget_type="campo")

    expected_text = _compose_style_label(zone, None)
    expected_tooltip = layout.Zone._build_label_tooltip(
        expected_text, zone.objectName()
    )

    assert zone._style_lbl.text() == expected_text
    assert zone._style_lbl.toolTip() == expected_tooltip

    zone.apply_overlays(False)

    assert zone._style_lbl.toolTip() == ""


@pytest.mark.parametrize(
    ("style_label", "declarations"),
    [
        ("estilo-base", BASE_STYLE_DECLARATIONS),
        ("estilo-alt", ALT_STYLE_DECLARATIONS),
    ],
)
def test_zone_overlay_shows_style_label_when_base_stylesheet_set(
    qapp, overlays_enabled, style_label, declarations
):
    widget_type = "campo"
    zone = layout.Zone(
        "B1",
        show_overlays=False,
        widget_type=widget_type,
    )
    zone.set_base_stylesheet(_base_stylesheet(zone, declarations), label=style_label)

    assert zone._style_lbl.isHidden()

    zone.apply_overlays(True)

    assert not zone._style_lbl.isHidden()
    expected = _compose_style_label(zone, style_label)
    assert zone._style_lbl.text() == expected


def test_zone_overlay_shows_widget_type_when_other_metadata_missing(
    qapp, overlays_enabled
):
    widget_type = "campo"
    zone = layout.Zone("B1", show_overlays=False, widget_type=widget_type)

    assert zone._style_lbl.isHidden()

    zone.apply_overlays(True)

    assert not zone._style_lbl.isHidden()
    assert zone._style_lbl.text() == widget_type


def test_zone_overlay_hides_style_label_when_disabled(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=False)
    zone.set_base_stylesheet(_base_stylesheet(zone, BASE_STYLE_DECLARATIONS), label="base")

    zone.apply_overlays(True)
    assert not zone._style_lbl.isHidden()

    zone.apply_overlays(False)

    assert zone._style_lbl.isHidden()
    assert zone._style_lbl.text() == ""


@pytest.mark.parametrize("widget_type", [None, "campo"])
def test_zone_set_base_stylesheet_updates_style_label_when_overlay_active(
    qapp, overlays_enabled, widget_type
):
    zone = layout.Zone("B1", show_overlays=True, widget_type=widget_type)

    if widget_type is None:
        assert zone._style_lbl.isHidden()
    else:
        assert not zone._style_lbl.isHidden()
        assert zone._style_lbl.text() == widget_type

    style_label = "estilo-base"
    zone.set_base_stylesheet(
        _base_stylesheet(zone, BASE_STYLE_DECLARATIONS), label=style_label
    )

    assert not zone._style_lbl.isHidden()
    expected = _compose_style_label(zone, style_label)
    assert zone._style_lbl.text() == expected


@pytest.mark.parametrize("widget_type", [None, "campo"])
def test_zone_init_base_stylesheet_shows_style_label_when_overlays_active(
    qapp, overlays_enabled, widget_type
):
    style_label = "estilo-base"
    base_stylesheet = _tag_stylesheet("B1", BASE_STYLE_DECLARATIONS)
    zone = layout.Zone(
        "B1",
        show_overlays=True,
        base_stylesheet=base_stylesheet,
        base_style_label=style_label,
        widget_type=widget_type,
    )

    assert zone.property("overlays") == "on"
    assert zone.base_stylesheet == base_stylesheet
    assert zone.styleSheet() == _overlay_stylesheet(zone)
    assert not zone._style_lbl.isHidden()
    expected = _compose_style_label(zone, style_label)
    assert zone._style_lbl.text() == expected


def test_zone_style_label_without_widget_type_stays_on_theme(qapp, overlays_enabled):
    style_label = "estilo-base"
    zone = layout.Zone(
        "B1",
        show_overlays=True,
        base_stylesheet=_tag_stylesheet("B1", BASE_STYLE_DECLARATIONS),
        base_style_label=style_label,
    )

    expected = _compose_style_label(zone, style_label)
    assert zone._style_lbl.text() == expected


def test_zone_set_widget_type_updates_style_label(qapp, overlays_enabled):
    style_label = "estilo-base"
    zone = layout.Zone(
        "B1",
        show_overlays=True,
        base_stylesheet=_tag_stylesheet("B1", BASE_STYLE_DECLARATIONS),
        base_style_label=style_label,
    )

    zone.set_widget_type("campo")

    expected = _compose_style_label(zone, style_label)
    assert zone._style_lbl.text() == expected


def test_zone_style_label_includes_all_segments(qapp, overlays_enabled):
    zone = layout.Zone(
        "B1",
        show_overlays=True,
        base_stylesheet=_tag_stylesheet("B1", BASE_STYLE_DECLARATIONS),
        base_style_label="estilo-base",
        widget_type="campo",
    )

    zone.set_zone_type("secao-teste")
    zone.set_widget_qt_class("QLineEdits")

    expected = _compose_style_label(zone, "estilo-base")
    assert expected == "secao-teste | QLineEdits | campo | estilo-base"
    assert zone._style_lbl.text() == expected


def test_zone_style_label_skips_missing_segments(qapp, overlays_enabled):
    style_label = "estilo-base"
    zone = layout.Zone(
        "B1",
        show_overlays=True,
        base_stylesheet=_tag_stylesheet("B1", BASE_STYLE_DECLARATIONS),
        base_style_label=style_label,
    )

    zone.set_zone_type("secao-teste")
    expected = _compose_style_label(zone, style_label)
    assert expected == "secao-teste | estilo-base"
    assert zone._style_lbl.text() == expected

    zone.set_zone_type(None)
    zone.set_widget_type("campo")
    expected = _compose_style_label(zone, style_label)
    assert expected == "campo | estilo-base"
    assert zone._style_lbl.text() == expected


def test_zone_split_propagates_metadata(qapp):
    zone = layout.Zone(
        "B1.C1",
        show_overlays=False,
        widget_type="campo",
        zone_type="secao-teste",
        widget_qt_class="QLineEdits",
    )

    left, right = zone.split_h((1, 1))

    for child in (left, right):
        assert child.zone_type == "secao-teste"
        assert child.widget_type == "campo"
        assert child.widget_qt_class == "QLineEdits"

def test_zone_add_row_has_no_debug_styles_by_default(qapp):
    zone = layout.Zone("B1")
    value_widget = QLabel("valor")
    label = zone.add_row("Nome", value_widget)

    row = label.parentWidget()
    assert "background-color" not in row.styleSheet()
    assert "border-radius" not in row.styleSheet()
    assert label.styleSheet() == LABEL_STYLE
    assert "background-color" not in value_widget.styleSheet()
    assert "border-radius" not in value_widget.styleSheet()


def test_zone_center_theme_keeps_label_alignment(qapp):
    default_zone = layout.Zone("B1", show_overlays=False)
    default_zone.set_base_stylesheet(
        _base_stylesheet(default_zone, BASE_STYLE_DECLARATIONS)
    )
    default_label = default_zone.add_row("Nome", QLabel("valor", default_zone))

    centre_zone = layout.Zone("B2", show_overlays=False)
    centre_zone.set_base_stylesheet(
        _base_stylesheet(centre_zone, ALT_STYLE_DECLARATIONS)
    )
    centre_label = centre_zone.add_row("Nome", QLabel("valor", centre_zone))

    assert default_label.styleSheet() == LABEL_STYLE
    assert centre_label.styleSheet() == LABEL_STYLE
    assert centre_label.styleSheet() == default_label.styleSheet()
    assert centre_label.alignment() == default_label.alignment()
    assert (
        centre_label.property("labelAlignmentVariant")
        == default_label.property("labelAlignmentVariant")
        == AlignmentVariant.DEFAULT.value
    )


def test_zone_add_row_allows_opt_in_debug_styles(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=False)
    value_widget = QLabel("valor")
    label = zone.add_row("Nome", value_widget, overlay_text="Overlay", debug_styles=True)

    row = label.parentWidget()
    assert "background-color" in row.styleSheet()
    assert "border-radius" in row.styleSheet()
    expected_style = (
        f"{LABEL_STYLE}\n"
        "QLabel { background-color: rgba(0, 0, 0, 0.03); border-radius: 4px; }"
    )
    assert label.styleSheet() == expected_style
    assert "background-color" in value_widget.styleSheet()
    assert "border-radius" in value_widget.styleSheet()
    expected_off_style = zone.styleSheet()
    expected_on_style = _overlay_stylesheet(zone)

    zone.apply_overlays(True)
    assert label.text() == "Overlay"
    assert zone.styleSheet() == expected_on_style
    assert label.styleSheet() == ""
    assert OVERLAY_ON_CLASS in _widget_classes(label)
    assert "background-color" in value_widget.styleSheet()

    zone.apply_overlays(False)
    assert label.text() == "Nome"
    assert zone.styleSheet() == expected_off_style
    assert label.styleSheet() == expected_style
    assert OVERLAY_ON_CLASS not in _widget_classes(label)
    assert "background-color" in value_widget.styleSheet()


class _OverlayDummyService:
    def __init__(self):
        self.ds = None
        self.conn = None

    def total(self):
        return 1

    def codigo_at(self, idx):
        return None

    def list_tipos_artigos(self):
        return []

    def list_validade(self):
        return []

    def list_temperaturas(self):
        return []

    def list_active_allergens(self):
        return []

    def get_image_path(self, codigo: str) -> None:
        return None

    def save_product_image(self, codigo: str, src_path: str) -> None:
        pass

    def delete_product_image(self, codigo: str) -> None:
        pass

    def get_product_info(self, codigo):
        return Product(
            code=codigo,
            pvps=[123, 246, None, 0, 615],
            iva=23,
            ingredients=[],
        )

    def calculate_cost(self, product):
        return 100


def test_food_cost_overlay_label_tooltip(qapp, overlays_enabled):
    ft = FTApp(_OverlayDummyService())
    try:
        labels = [
            lbl
            for lbl in ft.C3.findChildren(QLabel)
            if lbl.property("userLabel") == "Food Cost #1"
        ]
        assert len(labels) == 1
        food_cost_label = labels[0]
        assert food_cost_label.text() == "FoodCost.Nivel1"
        assert food_cost_label.toolTip() == "Food Cost #1 — FoodCost.Nivel1"
    finally:
        ft.close()


def test_zone_add_row_uses_overlay_style_when_active(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=True)
    value_widget = QLabel("valor", zone)
    label = zone.add_row("Nome", value_widget, overlay_text="Overlay")

    assert label.styleSheet() == ""
    assert OVERLAY_ON_CLASS in _widget_classes(label)
    assert label.text() == "Overlay"

    zone.apply_overlays(False)
    assert label.styleSheet() == LABEL_STYLE
    assert OVERLAY_ON_CLASS not in _widget_classes(label)
    assert label.text() == "Nome"


def test_zone_hides_overlays_when_globally_disabled(qapp):
    original = layout.DEV_OVERLAYS
    layout.DEV_OVERLAYS = False
    try:
        zone = layout.Zone("B1", show_overlays=True)
        assert zone.property("overlays") == "off"
        expected_off_style = zone.styleSheet()
        assert zone.styleSheet() == expected_off_style
    finally:
        layout.DEV_OVERLAYS = original


def test_zone_theme_stylesheet_restored_after_overlay_toggle(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=False)
    expected_theme_style = _base_stylesheet(zone, BASE_STYLE_DECLARATIONS)
    zone.set_base_stylesheet(expected_theme_style)
    assert zone.styleSheet() == expected_theme_style

    expected_overlay_style = _overlay_stylesheet(zone)

    zone.apply_overlays(True)
    assert zone.styleSheet() == expected_overlay_style

    zone.apply_overlays(False)
    assert zone.styleSheet() == expected_theme_style


def test_zone_set_base_stylesheet_while_overlay_active_keeps_overlay_style(
    qapp, overlays_enabled
):
    zone = layout.Zone("B1", show_overlays=True)
    expected_overlay_style = _overlay_stylesheet(zone)
    assert zone.styleSheet() == expected_overlay_style

    zone.set_base_stylesheet(_base_stylesheet(zone, BASE_STYLE_DECLARATIONS))
    assert zone.styleSheet() == expected_overlay_style

    expected_theme_style = _base_stylesheet(zone, BASE_STYLE_DECLARATIONS)

    zone.apply_overlays(False)
    assert zone.styleSheet() == expected_theme_style

    zone.apply_overlays(True)
    assert zone.styleSheet() == expected_overlay_style


def test_zone_apply_overlays_with_dotted_tag_has_no_stylesheet_warning(
    qapp, overlays_enabled
):
    zone = layout.Zone("B1.C1", show_overlays=False)
    captured_messages: list[str] = []

    def handler(msg_type, context, message):
        captured_messages.append(str(message))

    previous_handler = qInstallMessageHandler(handler)
    try:
        zone.apply_overlays(True)
    finally:
        qInstallMessageHandler(previous_handler)

    assert not any(
        "Could not parse stylesheet" in message for message in captured_messages
    )
