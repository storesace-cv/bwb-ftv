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


def test_zone_add_row_has_no_debug_styles_by_default(qapp):
    zone = layout.Zone("B1")
    value_widget = QLabel("valor")
    label = zone.add_row("Nome", value_widget)

    row = label.parentWidget()
    assert "background-color" not in row.styleSheet()
    assert "border-radius" not in row.styleSheet()
    assert label.styleSheet() == ""
    assert "background-color" not in value_widget.styleSheet()
    assert "border-radius" not in value_widget.styleSheet()


def test_zone_add_row_allows_opt_in_debug_styles(qapp):
    zone = layout.Zone("B1")
    value_widget = QLabel("valor")
    label = zone.add_row("Nome", value_widget, overlay_text="Overlay", debug_styles=True)

    row = label.parentWidget()
    assert "background-color" in row.styleSheet()
    assert "border-radius" in row.styleSheet()
    assert "background-color" in label.styleSheet()
    assert "border-radius" in label.styleSheet()
    assert "background-color" in value_widget.styleSheet()
    assert "border-radius" in value_widget.styleSheet()

    zone.apply_overlays(True)
    assert label.text() == "Overlay"
    assert "border:1px dashed red" in zone.styleSheet()

    zone.apply_overlays(False)
    assert label.text() == "Nome"
    assert zone.styleSheet() == ""
