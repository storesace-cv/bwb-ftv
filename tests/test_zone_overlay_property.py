from PyQt5.QtWidgets import QLabel

import pytest

from ui import layout
from ui.utilities import LABEL_STYLE


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

    zone.apply_overlays(False)
    assert label.text() == "Nome"
    assert zone.styleSheet() == "background: transparent; border: none;"

    zone.apply_overlays(True)
    assert label.text() == "Overlay"
    assert "border:1px dashed red" in zone.styleSheet()

    zone.apply_overlays(False)
    assert label.text() == "Nome"
    assert zone.styleSheet() == "background: transparent; border: none;"


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
    zone = layout.Zone("B1")
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

    zone.apply_overlays(True)
    assert label.text() == "Overlay"
    assert "border:1px dashed red" in zone.styleSheet()

    zone.apply_overlays(False)
    assert label.text() == "Nome"
    assert zone.styleSheet() == "background: transparent; border: none;"


def test_zone_hides_overlays_when_globally_disabled(qapp):
    original = layout.DEV_OVERLAYS
    layout.DEV_OVERLAYS = False
    try:
        zone = layout.Zone("B1", show_overlays=True)
        assert zone.property("overlays") == "off"
        assert zone.styleSheet() == "background: transparent; border: none;"
    finally:
        layout.DEV_OVERLAYS = original
