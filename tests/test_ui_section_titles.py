import pytest
from tests._qt import require_real_qt_modules

require_real_qt_modules("PyQt5.QtWidgets", "PyQt5.QtGui")

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGroupBox, QLabel
from services.products import ProductService
from ui.ui_editor_fonte import FTApp
from ui import layout


class StubDataStore:
    def total(self):
        return 1

    def codigo_at(self, idx):
        return "P1"

    def list_tipos_artigos(self):
        return []

    def list_validade(self):
        return []

    def list_temperaturas(self):
        return []

    def list_active_allergens(self):
        return []

    def get_produto_info(self, codigo):
        return {
            "codigo": codigo,
            "produto": "Prod",
            "informacaoadicional": "Sem lactose",
        }

    def get_pvps(self, codigo):
        return {"pvps": [], "iva": None}

    def get_ingredientes(self, codigo):
        return []


@pytest.mark.parametrize("start_overlays", [True, False])
def test_section_titles_toggle_prefix(qapp, start_overlays):
    original = layout.DEV_OVERLAYS
    layout.DEV_OVERLAYS = start_overlays
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    headers = [
        h
        for h in ft.findChildren(QLabel)
        if h.objectName() == "sectionHeader" and h.property("devLabel") is not None
    ]
    assert headers
    for header in headers:
        expected = (
            header.property("devLabel")
            if start_overlays
            else header.property("userLabel")
        )
        assert header.text() == expected
    ft._toggle_overlays()
    for header in headers:
        expected = (
            header.property("userLabel")
            if start_overlays
            else header.property("devLabel")
        )
        assert header.text() == expected
    ft._toggle_overlays()
    for header in headers:
        expected = (
            header.property("devLabel")
            if start_overlays
            else header.property("userLabel")
        )
        assert header.text() == expected
    ft.close()
    layout.DEV_OVERLAYS = original


def test_section_titles_use_normal_weight(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    try:
        boxes = [
            b
            for b in ft.findChildren(QGroupBox)
            if b.property("devTitle") is not None
        ]
        assert boxes
        for box in boxes:
            font = box.font()
            assert font.weight() == QFont.Normal
            assert not font.bold()
    finally:
        ft.close()
