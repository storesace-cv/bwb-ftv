from tests._qt import require_real_qt_modules

require_real_qt_modules("PyQt5.QtWidgets")

from services.products import ProductService
from ui.ui_editor_fonte import FTApp


class StubDataStore:
    def __init__(self):
        self.called = None

    def total(self):
        return 1

    def codigo_at(self, idx):
        return "P1"

    def list_tipos_artigos(self):
        return []

    def list_validade(self):
        return []

    def list_temperaturas(self):
        return [(1, "Quente"), (2, "Frio")]

    def list_active_allergens(self):
        return []

    def get_produto_info(self, codigo):
        return {
            "codigo": codigo,
            "produto": "Prod",
            "temperatura": 1,
            "informacaoadicional": "Servir morno",
        }

    def get_pvps(self, codigo):
        return {"pvps": [], "iva": None}

    def get_ingredientes(self, codigo):
        return []

    def set_temperatura(self, codigo, temperatura_cod):
        self.called = (codigo, temperatura_cod)
        return True

    def get_preparacao_html(self, codigo):
        return ""


def test_combo_updates_temperatura(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    assert ft.cbTemp.count() == 3
    assert ft.cbTemp.currentData() == 1
    ft.cbTemp.setCurrentIndex(2)
    qapp.processEvents()
    assert ds.called == ("P1", 2)
    ft.close()
