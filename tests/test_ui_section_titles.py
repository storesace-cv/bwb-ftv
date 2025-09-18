import pytest
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGroupBox
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
        return {"codigo": codigo, "produto": "Prod"}

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
    boxes = [
        b for b in ft.findChildren(QGroupBox) if b.property("devTitle") is not None
    ]
    assert boxes
    for box in boxes:
        expected = (
            box.property("devTitle") if start_overlays else box.property("userTitle")
        )
        assert box.title() == expected
    ft._toggle_overlays()
    for box in boxes:
        expected = (
            box.property("userTitle") if start_overlays else box.property("devTitle")
        )
        assert box.title() == expected
    ft._toggle_overlays()
    for box in boxes:
        expected = (
            box.property("devTitle") if start_overlays else box.property("userTitle")
        )
        assert box.title() == expected
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
