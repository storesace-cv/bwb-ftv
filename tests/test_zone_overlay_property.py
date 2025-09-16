from PyQt5.QtCore import qInstallMessageHandler
from PyQt5.QtWidgets import QLabel

import pytest

from ui import layout
from ui.bwb_style_1 import ZONE_STYLES
from ui.utilities import LABEL_STYLE, OVERLAY_ON_STYLE


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
        f"{selector} {{ background:{background}; border:1px dashed blue; }}"
        if selector
        else f"background:{background}; border:1px dashed blue;"
    )


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
    assert label.styleSheet() == OVERLAY_ON_STYLE
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
    assert label.styleSheet() == OVERLAY_ON_STYLE
    assert "background-color" in value_widget.styleSheet()

    zone.apply_overlays(False)
    assert label.text() == "Nome"
    assert zone.styleSheet() == expected_off_style
    assert label.styleSheet() == expected_style
    assert "background-color" in value_widget.styleSheet()


def test_zone_add_row_uses_overlay_style_when_active(qapp, overlays_enabled):
    zone = layout.Zone("B1", show_overlays=True)
    value_widget = QLabel("valor", zone)
    label = zone.add_row("Nome", value_widget, overlay_text="Overlay")

    assert label.styleSheet() == OVERLAY_ON_STYLE
    assert label.text() == "Overlay"

    zone.apply_overlays(False)
    assert label.styleSheet() == LABEL_STYLE
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
