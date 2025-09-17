from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit

from ui.layout import Zone
from ui.ui_editor_fonte import FTApp


def test_zone_label_right_click_copies_tooltip(qapp, qtbot):
    zone = Zone(
        "B9.C1",
        show_overlays=False,
        theme_name="bwb-style-1",
        widget_type="legenda",
    )
    qtbot.addWidget(zone)
    dummy_field = QLineEdit()
    label = zone.add_row("Etiqueta", dummy_field)
    tooltip_text = "Informação de teste"
    label.setToolTip(tooltip_text)
    zone.show()
    qtbot.waitUntil(zone.isVisible)
    qapp.clipboard().clear()
    qtbot.mouseClick(label, Qt.RightButton, pos=label.rect().center(), delay=10)
    qtbot.waitUntil(lambda: qapp.clipboard().text() == tooltip_text)


class _DummyAllergenService:
    def list_active_allergens(self):
        return [(1, "Glúten")]

    def get_allergen_details(self, aid):  # pragma: no cover - defensive fallback
        if aid == 1:
            return {"Exemplos": ["Pão"], "Notas": "Evitar contaminações"}
        return {}


def test_checkbox_right_click_copies_tooltip(qapp, qtbot):
    ft = FTApp.__new__(FTApp)
    ft.service = _DummyAllergenService()
    ft._allergen_checkboxes = {}
    ft.C5 = Zone(
        "B5.C1",
        show_overlays=False,
        theme_name="bwb-style-1",
        widget_type="caixa de seleção",
    )
    qtbot.addWidget(ft.C5)
    ft._build_allergens_grid()
    checkbox = ft._allergen_checkboxes[1]
    tooltip_text = checkbox.toolTip()
    assert tooltip_text
    ft.C5.show()
    qtbot.waitUntil(ft.C5.isVisible)
    qapp.clipboard().clear()
    qtbot.mouseClick(checkbox, Qt.RightButton, pos=checkbox.rect().center(), delay=10)
    qtbot.waitUntil(lambda: qapp.clipboard().text() == tooltip_text)
