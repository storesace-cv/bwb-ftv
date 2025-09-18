from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLineEdit, QToolTip

from ui.layout import Zone
import ui.layout as layout
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
    ft.C7 = Zone(
        "B7.C1",
        show_overlays=False,
        theme_name="bwb-style-1",
        widget_type="caixa de seleção",
    )
    qtbot.addWidget(ft.C7)
    ft._build_allergens_grid()
    checkbox = ft._allergen_checkboxes[1]
    tooltip_text = checkbox.toolTip()
    assert tooltip_text
    ft.C7.show()
    qtbot.waitUntil(ft.C7.isVisible)
    qapp.clipboard().clear()
    qtbot.mouseClick(checkbox, Qt.RightButton, pos=checkbox.rect().center(), delay=10)
    qtbot.waitUntil(lambda: qapp.clipboard().text() == tooltip_text)


def test_overlay_tooltip_copies_from_global_filter(qapp, qtbot):
    original = layout.DEV_OVERLAYS
    layout.DEV_OVERLAYS = True
    try:
        zone = Zone(
            "B1.C1",
            show_overlays=True,
            theme_name="bwb-style-1",
            widget_type="legenda",
        )
        qtbot.addWidget(zone)
        dummy_field = QLineEdit()
        label = zone.add_row("Etiqueta", dummy_field)
        tooltip_text = "Texto visível nas overlays"
        label.setToolTip(tooltip_text)
        zone.show()
        qtbot.waitUntil(zone.isVisible)
        global_pos = label.mapToGlobal(label.rect().center())
        QToolTip.showText(global_pos, tooltip_text, label, label.rect(), 10000)
        qtbot.waitUntil(QToolTip.isVisible)
        assert QToolTip.text() == tooltip_text
        assert zone.property("overlays") == "on"
        qapp.clipboard().clear()
        local_pos = dummy_field.rect().center()
        global_click_pos = dummy_field.mapToGlobal(local_pos)
        assert QToolTip.isVisible()
        from ui import utilities

        assert utilities._overlay_context(dummy_field)
        filter_obj = utilities._GLOBAL_TOOLTIP_FILTER
        assert isinstance(filter_obj, utilities._TooltipCopyGlobalFilter)
        press = QMouseEvent(
            QEvent.MouseButtonPress,
            local_pos,
            global_click_pos,
            Qt.RightButton,
            Qt.RightButton,
            Qt.NoModifier,
        )
        filter_obj.eventFilter(dummy_field, press)
        qtbot.waitUntil(lambda: qapp.clipboard().text() == tooltip_text)
    finally:
        QToolTip.hideText()
        layout.DEV_OVERLAYS = original
