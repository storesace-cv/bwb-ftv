from PyQt5.QtCore import Qt, qInstallMessageHandler
from PyQt5.QtWidgets import QLabel, QLineEdit

import pytest

from ui import layout
from ui.bwb_style_1 import OVERLAY_ON_CLASS, ZONE_STYLES
from ui.utilities import (
    AlignmentVariant,
    CENTER_FIELD_STYLE,
    CENTER_LABEL_STYLE,
    LABEL_STYLE,
    apply_label_style,
    apply_overlay_label_style,
    make_readonly_lineedit,
)


def _theme_stylesheet(zone: layout.Zone, theme_name: str) -> str:
    selector = (
        f"#{layout._escape_object_name(zone.objectName())}"
        if zone.objectName()
        else ""
    )
    declarations = ZONE_STYLES[theme_name]
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
    theme_name: str | None,
) -> str:
    return " | ".join(
        segment
        for segment in (
            zone.zone_type,
            zone.widget_qt_class,
            zone.widget_type,
            theme_name,
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


def test_zone_overlay_tag_label_preserves_inline_style(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=True)
    expected_style = "color:#c00; font-size:10px; background:none; border:none;"

    assert zone._tag_lbl.styleSheet() == expected_style

    zone.apply_overlays(False)
    assert zone._tag_lbl.styleSheet() == expected_style

    zone.apply_overlays(True)
    assert zone._tag_lbl.styleSheet() == expected_style


@pytest.mark.parametrize(
    ("theme_name", "declarations"),
    [
        ("bwb-style-1", None),
        ("bwb-style-1-center", None),
        ("bwb-style-1-extra", "background: #f0f; border: 1px solid #000;"),
    ],
)
def test_zone_overlay_shows_style_name_for_any_registered_theme(
    qapp, overlays_enabled, monkeypatch, theme_name, declarations
):
    if declarations is not None:
        monkeypatch.setitem(ZONE_STYLES, theme_name, declarations)

    widget_type = "campo"
    zone = layout.Zone(
        "B1",
        show_overlays=False,
        widget_type=widget_type,
    )
    zone.set_theme(theme_name)

    assert zone._style_lbl.isHidden()

    zone.apply_overlays(True)

    assert not zone._style_lbl.isHidden()
    expected = _compose_style_label(zone, theme_name)
    assert zone._style_lbl.text() == expected


def test_zone_overlay_hides_style_label_when_disabled(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=False)
    zone.set_theme("bwb-style-1")

    zone.apply_overlays(True)
    assert not zone._style_lbl.isHidden()

    zone.apply_overlays(False)

    assert zone._style_lbl.isHidden()
    assert zone._style_lbl.text() == ""


@pytest.mark.parametrize("widget_type", [None, "campo"])
@pytest.mark.parametrize("theme_name", ["bwb-style-1", "bwb-style-1-center"])
def test_zone_set_theme_updates_style_label_when_overlay_active(
    qapp, overlays_enabled, theme_name, widget_type
):
    zone = layout.Zone("B1", show_overlays=True, widget_type=widget_type)

    assert zone._style_lbl.isHidden()

    zone.set_theme(theme_name)

    assert not zone._style_lbl.isHidden()
    expected = _compose_style_label(zone, theme_name)
    assert zone._style_lbl.text() == expected


@pytest.mark.parametrize("widget_type", [None, "campo"])
@pytest.mark.parametrize("theme_name", ["bwb-style-1", "bwb-style-1-center"])
def test_zone_init_theme_shows_style_label_when_overlays_active(
    qapp, overlays_enabled, theme_name, widget_type
):
    zone = layout.Zone(
        "B1",
        show_overlays=True,
        theme_name=theme_name,
        widget_type=widget_type,
    )

    assert zone.property("overlays") == "on"
    assert zone.base_stylesheet == _theme_stylesheet(zone, theme_name)
    assert zone.styleSheet() == _overlay_stylesheet(zone)
    assert not zone._style_lbl.isHidden()
    expected = _compose_style_label(zone, theme_name)
    assert zone._style_lbl.text() == expected


def test_zone_style_label_without_widget_type_stays_on_theme(qapp, overlays_enabled):
    theme_name = "bwb-style-1"
    zone = layout.Zone("B1", show_overlays=True, theme_name=theme_name)

    expected = _compose_style_label(zone, theme_name)
    assert zone._style_lbl.text() == expected


def test_zone_set_widget_type_updates_style_label(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=True, theme_name="bwb-style-1")

    zone.set_widget_type("campo")

    expected = _compose_style_label(zone, "bwb-style-1")
    assert zone._style_lbl.text() == expected


def test_zone_style_label_includes_all_segments(qapp, overlays_enabled):
    zone = layout.Zone(
        "B1",
        show_overlays=True,
        theme_name="bwb-style-1",
        widget_type="campo",
    )

    zone.set_zone_type("secao-teste")
    zone.set_widget_qt_class("QLineEdits")

    expected = _compose_style_label(zone, "bwb-style-1")
    assert expected == "secao-teste | QLineEdits | campo | bwb-style-1"
    assert zone._style_lbl.text() == expected


def test_zone_style_label_skips_missing_segments(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=True, theme_name="bwb-style-1")

    zone.set_zone_type("secao-teste")
    expected = _compose_style_label(zone, "bwb-style-1")
    assert expected == "secao-teste | bwb-style-1"
    assert zone._style_lbl.text() == expected

    zone.set_zone_type(None)
    zone.set_widget_type("campo")
    expected = _compose_style_label(zone, "bwb-style-1")
    assert expected == "campo | bwb-style-1"
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
    default_zone.set_theme("bwb-style-1")
    default_label = default_zone.add_row("Nome", QLabel("valor", default_zone))

    centre_zone = layout.Zone("B2", show_overlays=False)
    centre_zone.set_theme("bwb-style-1-center")
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
    zone.set_theme("bwb-style-1")
    expected_theme_style = _theme_stylesheet(zone, "bwb-style-1")
    assert zone.styleSheet() == expected_theme_style

    expected_overlay_style = _overlay_stylesheet(zone)

    zone.apply_overlays(True)
    assert zone.styleSheet() == expected_overlay_style

    zone.apply_overlays(False)
    assert zone.styleSheet() == expected_theme_style


def test_zone_set_theme_while_overlay_active_keeps_overlay_style(
    qapp, overlays_enabled
):
    zone = layout.Zone("B1", show_overlays=True)
    expected_overlay_style = _overlay_stylesheet(zone)
    assert zone.styleSheet() == expected_overlay_style

    zone.set_theme("bwb-style-1")
    assert zone.styleSheet() == expected_overlay_style

    expected_theme_style = _theme_stylesheet(zone, "bwb-style-1")

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
