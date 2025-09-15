from PyQt5.QtWidgets import QLabel

from ui import layout


def test_zone_overlay_property_updates(qapp):
    zone = layout.Zone("B1", show_overlays=True)
    assert zone.property("overlays") == "on"
    zone.apply_overlays(False)
    assert zone.property("overlays") == "off"
    zone.apply_overlays(True)
    assert zone.property("overlays") == "on"


def test_zone_apply_overlays_restores_text_and_border(qapp):
    zone = layout.Zone("B1", show_overlays=False)
    value_widget = QLabel("value", zone)
    label = zone.add_row("Nome", value_widget, overlay_text="Overlay")

    zone.apply_overlays(False)
    assert label.text() == "Nome"
    assert zone.styleSheet() == ""

    zone.apply_overlays(True)
    assert label.text() == "Overlay"
    assert "border:1px dashed red" in zone.styleSheet()

    zone.apply_overlays(False)
    assert label.text() == "Nome"
    assert zone.styleSheet() == ""
