from tests._qt import require_real_qt_modules

require_real_qt_modules("PyQt5.QtWidgets", "PyQt5.QtCore")

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit, QToolTip

import ui.layout as layout
from ui.layout import Zone
from ui.tagging import zone_tag
from ui.ui_editor_fonte import FTApp


def test_zone_label_right_click_keeps_clipboard(qapp, qtbot):
    zone = Zone(
        zone_tag("general_root"),
        show_overlays=False,
        theme_name="bwb-style-1",
        widget_type="etiqueta-c",
    )
    qtbot.addWidget(zone)
    dummy_field = QLineEdit()
    label = zone.add_row("Etiqueta-c", dummy_field)
    tooltip_text = "Informação de teste"
    label.setToolTip(tooltip_text)
    zone.show()
    qtbot.waitUntil(zone.isVisible)
    before = qapp.clipboard().text()
    qtbot.mouseClick(label, Qt.RightButton, pos=label.rect().center(), delay=10)
    qtbot.wait(50)
    assert qapp.clipboard().text() == before
    assert label.toolTip() == tooltip_text


class _DummyAllergenService:
    def list_active_allergens(self):
        return [(1, "Glúten")]

    def get_allergen_details(self, aid):  # pragma: no cover - defensive fallback
        if aid == 1:
            return {"Exemplos": ["Pão"], "Notas": "Evitar contaminações"}
        return {}


def test_checkbox_right_click_keeps_clipboard(qapp, qtbot):
    ft = FTApp.__new__(FTApp)
    ft.service = _DummyAllergenService()
    ft._allergen_checkboxes = {}
    ft.B7_C1 = Zone(
        zone_tag("allergens_root"),
        show_overlays=False,
        theme_name="bwb-style-1",
        widget_type="caixa de seleção",
    )
    ft.C7 = ft.B7_C1
    qtbot.addWidget(ft.B7_C1)
    ft._build_allergens_grid()
    checkbox = ft._allergen_checkboxes[1]
    tooltip_text = checkbox.toolTip()
    ft.B7_C1.show()
    qtbot.waitUntil(ft.B7_C1.isVisible)
    before = qapp.clipboard().text()
    qtbot.mouseClick(checkbox, Qt.RightButton, pos=checkbox.rect().center(), delay=10)
    qtbot.wait(50)
    assert qapp.clipboard().text() == before
    assert checkbox.toolTip() == tooltip_text


def test_overlay_tooltip_text_is_not_modified(qapp, qtbot):
    original = layout.DEV_OVERLAYS
    layout.DEV_OVERLAYS = True
    try:
        zone = Zone(
            zone_tag("general_root"),
            show_overlays=True,
            theme_name="bwb-style-1",
            widget_type="etiqueta-c",
        )
        qtbot.addWidget(zone)
        dummy_field = QLineEdit()
        label = zone.add_row("Etiqueta-c", dummy_field)
        tooltip_text = "Texto visível nas overlays"
        label.setToolTip(tooltip_text)
        zone.show()
        qtbot.waitUntil(zone.isVisible)
        global_pos = label.mapToGlobal(label.rect().center())
        QToolTip.showText(global_pos, tooltip_text, label, label.rect(), 1000)
        qtbot.waitUntil(QToolTip.isVisible)
        before = qapp.clipboard().text()
        qtbot.mouseClick(label, Qt.RightButton, pos=label.rect().center(), delay=10)
        qtbot.wait(50)
        assert qapp.clipboard().text() == before
        assert QToolTip.text() in ("", tooltip_text)
    finally:
        QToolTip.hideText()
        layout.DEV_OVERLAYS = original
