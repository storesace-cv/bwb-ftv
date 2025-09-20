import pytest

# Skip when PyQt5 or its libGL-backed QtCore/QtWidgets modules are unavailable.
pytest.importorskip("PyQt5", reason="PyQt5 requires libGL.so.1")
pytest.importorskip("PyQt5.QtCore", reason="PyQt5.QtCore requires libGL.so.1")
pytest.importorskip("PyQt5.QtWidgets", reason="PyQt5.QtWidgets requires libGL.so.1")

from PyQt5.QtCore import Qt, QPointF, QEvent, qInstallMessageHandler
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLabel, QLineEdit

from domain import Product
from ui import layout
from ui.tagging import zone_tag
from ui.ui_editor_fonte import FTApp, _configure_zone
from ui.utilities import (
    AlignmentVariant,
    FIELD_STYLE,
    CENTER_FIELD_STYLE,
    CENTER_LABEL_STYLE,
    OVERLAY_ON_CLASS,
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


def _block_prefix(key: str) -> str:
    """Return the top-level block identifier for ``key``."""

    tag = zone_tag(key)
    return tag.split(".", 1)[0]


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


def _expected_metadata_lines(
    zone: layout.Zone,
    *,
    zone_type: str | None = None,
    widget_type: str | None = None,
    widget_qt_class: str | None = None,
    base_style_label: str | None = None,
    style_dev_info: str | None = None,
) -> list[str]:
    snapshot = zone._metadata_snapshot

    def _resolve(attr: str, key: str, override: str | None) -> str | None:
        if override is not None:
            return override
        value = getattr(zone, attr)
        if value:
            return value
        return snapshot.get(key)

    lines = [f"tag: {zone.tag}"]

    resolved_zone_type = _resolve("_zone_type", "zone_type", zone_type)
    if resolved_zone_type:
        lines.append(f"zoneType: {resolved_zone_type}")

    resolved_widget_type = _resolve("_widget_type", "widget_type", widget_type)
    if resolved_widget_type:
        lines.append(f"widgetType: {resolved_widget_type}")

    resolved_widget_qt_class = _resolve(
        "_widget_qt_class", "widget_qt_class", widget_qt_class
    )
    if resolved_widget_qt_class:
        lines.append(f"widgetQtClass: {resolved_widget_qt_class}")

    resolved_base_style_label = _resolve(
        "_base_style_label", "base_style_label", base_style_label
    )
    if resolved_base_style_label:
        lines.append(f"baseStyleLabel: {resolved_base_style_label}")

    resolved_dev_info = _resolve(
        "_style_dev_info", "style_dev_info", style_dev_info
    )
    if resolved_dev_info:
        lines.append(f"style_dev_info: {resolved_dev_info}")

    return lines


def test_apply_label_style_center_variant_uses_center_alignment(qapp):
    label = QLabel("Centro")
    stylesheet = apply_label_style(label, alignment=AlignmentVariant.CENTER)

    assert stylesheet == CENTER_LABEL_STYLE
    assert label.styleSheet() == CENTER_LABEL_STYLE
    assert label.alignment() == Qt.AlignHCenter | Qt.AlignVCenter
    assert label.property("labelAlignmentVariant") == AlignmentVariant.CENTER.value


def test_apply_label_style_reuses_stored_alignment(qapp):
    label = QLabel("Centro")
    apply_label_style(label, alignment=AlignmentVariant.CENTER)

    stylesheet = apply_label_style(label)

    assert stylesheet == CENTER_LABEL_STYLE
    assert label.styleSheet() == CENTER_LABEL_STYLE
    assert label.alignment() == Qt.AlignHCenter | Qt.AlignVCenter


def test_apply_label_style_right_variant_uses_right_alignment(qapp):
    label = QLabel("Direita")
    stylesheet = apply_label_style(label, alignment=AlignmentVariant.RIGHT)

    assert stylesheet == LABEL_STYLE
    assert label.styleSheet() == LABEL_STYLE
    assert label.alignment() == Qt.AlignRight | Qt.AlignVCenter
    assert label.property("labelAlignmentVariant") == AlignmentVariant.RIGHT.value

    apply_label_style(label)

    assert label.alignment() == Qt.AlignRight | Qt.AlignVCenter


def test_apply_overlay_label_style_preserves_alignment_variant(qapp):
    label = QLabel("Centro")
    apply_label_style(label, alignment=AlignmentVariant.CENTER)

    apply_overlay_label_style(label)
    assert label.styleSheet() == ""

    apply_label_style(label)

    assert label.styleSheet() == CENTER_LABEL_STYLE
    assert label.alignment() == Qt.AlignHCenter | Qt.AlignVCenter


def test_make_readonly_lineedit_center_variant_uses_left_alignment(qapp):
    le = QLineEdit("0")
    make_readonly_lineedit(le, alignment=AlignmentVariant.CENTER)

    assert le.isReadOnly()
    assert le.styleSheet() == CENTER_FIELD_STYLE
    assert le.alignment() == Qt.AlignLeft | Qt.AlignVCenter
    assert le.property("lineEditAlignmentVariant") == AlignmentVariant.CENTER.value

    make_readonly_lineedit(le)

    assert le.styleSheet() == CENTER_FIELD_STYLE
    assert le.alignment() == Qt.AlignLeft | Qt.AlignVCenter


def test_make_readonly_lineedit_right_variant_uses_right_alignment(qapp):
    le = QLineEdit("0")
    make_readonly_lineedit(le, alignment=AlignmentVariant.RIGHT)

    assert le.isReadOnly()
    assert le.styleSheet() == FIELD_STYLE
    assert le.alignment() == Qt.AlignRight | Qt.AlignVCenter
    assert le.property("lineEditAlignmentVariant") == AlignmentVariant.RIGHT.value

    make_readonly_lineedit(le)

    assert le.alignment() == Qt.AlignRight | Qt.AlignVCenter


@pytest.fixture
def overlays_enabled():
    original = layout.DEV_OVERLAYS
    layout.DEV_OVERLAYS = True
    try:
        yield
    finally:
        layout.DEV_OVERLAYS = original


def test_zone_overlay_property_updates(qapp, overlays_enabled):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=True)
    assert zone.property("overlays") == "on"
    zone.apply_overlays(False)
    assert zone.property("overlays") == "off"
    zone.apply_overlays(True)
    assert zone.property("overlays") == "on"


def test_zone_apply_overlays_restores_text_and_border(qapp, overlays_enabled):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=False)
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
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=False)
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


def test_zone_right_alignment_persists_through_overlays(qapp, overlays_enabled):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=False)
    value_widget = QLabel("value", zone)
    label = zone.add_row("Nome", value_widget, overlay_text="Overlay")

    zone.set_label_alignment(AlignmentVariant.RIGHT)

    assert label.property("labelAlignmentVariant") == AlignmentVariant.RIGHT.value
    assert label.alignment() == Qt.AlignRight | Qt.AlignVCenter

    zone.apply_overlays(True)

    assert label.alignment() == Qt.AlignRight | Qt.AlignVCenter
    assert label.property("labelAlignmentVariant") == AlignmentVariant.RIGHT.value

    zone.apply_overlays(False)

    assert label.alignment() == Qt.AlignRight | Qt.AlignVCenter
    assert label.property("labelAlignmentVariant") == AlignmentVariant.RIGHT.value


def test_zone_overlay_tag_label_preserves_inline_style(qapp, overlays_enabled):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=True)
    expected_style = "color:#c00; font-size:10px; background:none; border:none;"

    assert zone._tag_lbl.styleSheet() == expected_style

    zone.apply_overlays(False)
    assert zone._tag_lbl.styleSheet() == expected_style


def test_zone_overlay_resizes_label_width_for_overlay_text(qapp, overlays_enabled):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=False)
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
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=False)
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


def test_apply_metadata_default_base_stylesheet_is_borderless(qapp):
    zone = layout.Zone(zone_tag("family_root"), show_overlays=False)

    zone.apply_metadata()

    assert zone.property("overlays") == "off"
    assert zone.styleSheet() == zone.base_stylesheet
    assert "border:" not in zone.base_stylesheet
    assert "border-radius" in zone.base_stylesheet


def test_apply_bwb_etiqueta_c_normal_aligns_without_theming(qapp):
    zone = layout.Zone(zone_tag("allergens_root"), show_overlays=False)
    other_zone = layout.Zone(zone_tag("allergens_secondary"), show_overlays=False)

    original_stylesheet = zone.base_stylesheet

    layout.apply_bwb_etiqueta_c_normal(zone)

    margins = zone.ly.contentsMargins()
    assert margins.left() == 0
    assert margins.right() == 0
    assert margins.top() == 0
    assert margins.bottom() == 0
    assert zone._label_alignment is AlignmentVariant.CENTER

    updated_stylesheet = zone.base_stylesheet
    assert zone.styleSheet() == updated_stylesheet
    assert "margin: 0" in updated_stylesheet
    assert "padding: 0" in updated_stylesheet
    assert "padding: 6" not in updated_stylesheet
    assert "margin: 6" not in updated_stylesheet
    for declaration in ("background: transparent", "border: none"):
        assert declaration in updated_stylesheet
    assert "linear-gradient" not in zone.base_stylesheet

    value_widget = QLabel("valor", zone)
    label = zone.add_row("Etiqueta-c", value_widget)

    assert label.alignment() == Qt.AlignHCenter | Qt.AlignVCenter
    assert label.property("labelAlignmentVariant") == AlignmentVariant.CENTER.value

    assert other_zone.base_stylesheet == other_zone.styleSheet()


def test_apply_metadata_invokes_etiqueta_c_defaults(qapp):
    zone = layout.Zone(zone_tag("etiqueta_c_auto"), show_overlays=False)

    zone.apply_metadata(widget_type="etiqueta-c")

    margins = zone.ly.contentsMargins()
    assert margins.left() == 0
    assert margins.right() == 0
    assert margins.top() == 0
    assert margins.bottom() == 0
    assert zone._label_alignment is AlignmentVariant.CENTER

    stylesheet = zone.base_stylesheet
    assert zone.styleSheet() == stylesheet
    assert "margin: 0" in stylesheet
    assert "padding: 0" in stylesheet
    assert "padding: 6" not in stylesheet
    assert "margin: 6" not in stylesheet

    value_widget = QLabel("valor", zone)
    label = zone.add_row("Etiqueta-c", value_widget)

    assert label.alignment() == Qt.AlignHCenter | Qt.AlignVCenter
    assert label.property("labelAlignmentVariant") == AlignmentVariant.CENTER.value


def test_zone_style_label_tooltip_tracks_dev_info(qapp, overlays_enabled):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=False)
    zone.set_zone_type("secao")
    zone.set_widget_type("campo")
    zone.set_widget_qt_class("QLineEdits")
    dev_info = "FichaTecnica.Dev"
    zone.set_style_dev_info(dev_info)

    zone.apply_overlays(True)

    expected_lines = _expected_metadata_lines(zone, style_dev_info=dev_info)

    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == expected_lines
    assert expected_lines[-1] == f"style_dev_info: {dev_info}"

    zone.apply_overlays(False)

    assert zone._style_lbl.isHidden()
    assert zone._style_lbl.toolTip() == ""


def test_configure_zone_sets_dev_info_tooltip(qapp, overlays_enabled):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=True)

    _configure_zone(zone, zone_type="secao", widget_type="campo")

    zone.apply_overlays(True)

    expected_lines = _expected_metadata_lines(
        zone, style_dev_info=zone.objectName()
    )

    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == expected_lines

    zone.apply_overlays(False)

    assert zone._style_lbl.isHidden()
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
        _block_prefix("general_root"),
        show_overlays=False,
        widget_type=widget_type,
    )
    zone.set_zone_stylesheet(_base_stylesheet(zone, declarations), label=style_label)

    assert zone._style_lbl.isHidden()

    zone.apply_overlays(True)

    expected_lines = _expected_metadata_lines(
        zone, base_style_label=style_label, widget_type=widget_type
    )
    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == expected_lines


def test_zone_overlay_shows_widget_type_when_other_metadata_missing(
    qapp, overlays_enabled
):
    widget_type = "campo"
    zone = layout.Zone(
        _block_prefix("general_root"), show_overlays=False, widget_type=widget_type
    )

    assert zone._style_lbl.isHidden()

    zone.apply_overlays(True)

    expected_lines = _expected_metadata_lines(zone, widget_type=widget_type)
    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == expected_lines


def test_zone_overlay_hides_style_label_when_disabled(qapp, overlays_enabled):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=False)
    zone.set_zone_stylesheet(
        _base_stylesheet(zone, BASE_STYLE_DECLARATIONS), label="base"
    )

    zone.apply_overlays(True)
    assert zone._style_lbl.isHidden()

    zone.apply_overlays(False)

    assert zone._style_lbl.isHidden()
    assert zone._style_lbl.text() == ""


@pytest.mark.parametrize("widget_type", [None, "campo"])
def test_zone_set_base_stylesheet_updates_style_label_when_overlay_active(
    qapp, overlays_enabled, widget_type
):
    zone = layout.Zone(
        _block_prefix("general_root"),
        show_overlays=True,
        widget_type=widget_type,
    )

    initial_expected = _expected_metadata_lines(zone)
    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == initial_expected

    style_label = "estilo-base"
    zone.set_zone_stylesheet(
        _base_stylesheet(zone, BASE_STYLE_DECLARATIONS), label=style_label
    )

    updated_expected = _expected_metadata_lines(
        zone, base_style_label=style_label
    )
    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == updated_expected


@pytest.mark.parametrize("widget_type", [None, "campo"])
def test_zone_init_base_stylesheet_shows_style_label_when_overlays_active(
    qapp, overlays_enabled, widget_type
):
    style_label = "estilo-base"
    base_stylesheet = _tag_stylesheet(
        _block_prefix("general_root"), BASE_STYLE_DECLARATIONS
    )
    zone = layout.Zone(
        _block_prefix("general_root"),
        show_overlays=True,
        base_stylesheet=base_stylesheet,
        base_style_label=style_label,
        widget_type=widget_type,
    )

    assert zone.property("overlays") == "on"
    assert zone.base_stylesheet == base_stylesheet
    assert zone.styleSheet() == _overlay_stylesheet(zone)
    expected_lines = _expected_metadata_lines(
        zone, base_style_label=style_label
    )
    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == expected_lines


def test_zone_style_label_without_widget_type_stays_on_theme(qapp, overlays_enabled):
    style_label = "estilo-base"
    zone = layout.Zone(
        _block_prefix("general_root"),
        show_overlays=True,
        base_stylesheet=_tag_stylesheet(
            _block_prefix("general_root"), BASE_STYLE_DECLARATIONS
        ),
        base_style_label=style_label,
    )

    expected_lines = _expected_metadata_lines(
        zone, base_style_label=style_label
    )
    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == expected_lines


def test_zone_set_widget_type_updates_style_label(qapp, overlays_enabled):
    style_label = "estilo-base"
    zone = layout.Zone(
        _block_prefix("general_root"),
        show_overlays=True,
        base_stylesheet=_tag_stylesheet(
            _block_prefix("general_root"), BASE_STYLE_DECLARATIONS
        ),
        base_style_label=style_label,
    )

    zone.set_widget_type("campo")

    expected_lines = _expected_metadata_lines(
        zone, base_style_label=style_label, widget_type="campo"
    )
    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == expected_lines


def test_zone_style_label_includes_all_segments(qapp, overlays_enabled):
    zone = layout.Zone(
        _block_prefix("general_root"),
        show_overlays=True,
        base_stylesheet=_tag_stylesheet(
            _block_prefix("general_root"), BASE_STYLE_DECLARATIONS
        ),
        base_style_label="estilo-base",
        widget_type="campo",
    )

    zone.set_zone_type("secao-teste")
    zone.set_widget_qt_class("QLineEdits")

    expected_lines = _expected_metadata_lines(zone)
    assert expected_lines == [
        f"tag: {zone.tag}",
        "zoneType: secao-teste",
        "widgetType: campo",
        "widgetQtClass: QLineEdits",
        "baseStyleLabel: estilo-base",
    ]
    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == expected_lines


def test_zone_style_label_skips_missing_segments(qapp, overlays_enabled):
    style_label = "estilo-base"
    zone = layout.Zone(
        _block_prefix("general_root"),
        show_overlays=True,
        base_stylesheet=_tag_stylesheet(
            _block_prefix("general_root"), BASE_STYLE_DECLARATIONS
        ),
        base_style_label=style_label,
    )

    zone.set_zone_type("secao-teste")
    expected_with_zone_type = _expected_metadata_lines(
        zone, base_style_label=style_label
    )
    assert expected_with_zone_type == [
        f"tag: {zone.tag}",
        "zoneType: secao-teste",
        "baseStyleLabel: estilo-base",
    ]
    assert zone._style_lbl.isHidden()
    assert zone._metadata_tooltip_text.splitlines() == expected_with_zone_type

    zone.set_zone_type(None)
    zone.set_widget_type("campo")
    expected_with_widget_type = _expected_metadata_lines(
        zone, base_style_label=style_label, widget_type="campo"
    )
    assert expected_with_widget_type == [
        f"tag: {zone.tag}",
        "widgetType: campo",
        "baseStyleLabel: estilo-base",
    ]
    assert zone._metadata_tooltip_text.splitlines() == expected_with_widget_type


def test_zone_metadata_click_filter_triggers_tooltip(
    qapp, overlays_enabled, monkeypatch
):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=False)
    zone.set_zone_type("secao")
    zone.set_widget_type("campo")

    zone.apply_overlays(True)

    calls = []

    def fake_show_text(pos, text, widget=None):
        calls.append((pos, text, widget))

    monkeypatch.setattr(layout.QToolTip, "showText", fake_show_text)

    event = QMouseEvent(
        QEvent.MouseButtonPress,
        QPointF(1.0, 1.0),
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )

    qapp.sendEvent(zone, event)

    assert calls
    _, text, widget = calls[-1]
    assert text == zone._metadata_tooltip_text
    assert widget is zone


def test_zone_split_propagates_metadata(qapp):
    zone = layout.Zone(
        zone_tag("general_root"),
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
    zone = layout.Zone(_block_prefix("general_root"))
    value_widget = QLabel("valor")
    label = zone.add_row("Nome", value_widget)

    row = label.parentWidget()
    assert "background-color" not in row.styleSheet()
    assert "border-radius" not in row.styleSheet()
    assert label.styleSheet() == LABEL_STYLE
    assert "background-color" not in value_widget.styleSheet()
    assert "border-radius" not in value_widget.styleSheet()


def test_zone_center_theme_keeps_label_alignment(qapp):
    default_zone = layout.Zone(
        _block_prefix("general_root"), show_overlays=False
    )
    default_zone.set_zone_stylesheet(
        _base_stylesheet(default_zone, BASE_STYLE_DECLARATIONS)
    )
    default_label = default_zone.add_row("Nome", QLabel("valor", default_zone))

    centre_zone = layout.Zone(_block_prefix("family_root"), show_overlays=False)
    centre_zone.set_zone_stylesheet(
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
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=False)
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


def test_zone_label_minimum_width_is_preserved(qapp):
    zone = layout.Zone("B1")
    value_widget = QLabel("valor", zone)
    min_width = 120

    label = zone.add_row("Nome", value_widget, label_minw=min_width)
    zone.sync_label_widths()
    qapp.processEvents()

    assert label.property("labelMinimumWidth") == min_width
    assert label.width() >= min_width


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
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=True)
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
        zone = layout.Zone(_block_prefix("general_root"), show_overlays=True)
        assert zone.property("overlays") == "off"
        expected_off_style = zone.styleSheet()
        assert zone.styleSheet() == expected_off_style
    finally:
        layout.DEV_OVERLAYS = original


def test_zone_theme_stylesheet_restored_after_overlay_toggle(qapp, overlays_enabled):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=False)
    expected_theme_style = _base_stylesheet(zone, BASE_STYLE_DECLARATIONS)
    zone.set_zone_stylesheet(expected_theme_style)
    assert zone.styleSheet() == expected_theme_style

    expected_overlay_style = _overlay_stylesheet(zone)

    zone.apply_overlays(True)
    assert zone.styleSheet() == expected_overlay_style

    zone.apply_overlays(False)
    assert zone.styleSheet() == expected_theme_style


def test_zone_set_base_stylesheet_while_overlay_active_keeps_overlay_style(
    qapp, overlays_enabled
):
    zone = layout.Zone(_block_prefix("general_root"), show_overlays=True)
    expected_overlay_style = _overlay_stylesheet(zone)
    assert zone.styleSheet() == expected_overlay_style

    zone.set_zone_stylesheet(_base_stylesheet(zone, BASE_STYLE_DECLARATIONS))
    assert zone.styleSheet() == expected_overlay_style

    expected_theme_style = _base_stylesheet(zone, BASE_STYLE_DECLARATIONS)

    zone.apply_overlays(False)
    assert zone.styleSheet() == expected_theme_style

    zone.apply_overlays(True)
    assert zone.styleSheet() == expected_overlay_style


def test_zone_apply_overlays_with_dotted_tag_has_no_stylesheet_warning(
    qapp, overlays_enabled
):
    zone = layout.Zone(zone_tag("general_root"), show_overlays=False)
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
