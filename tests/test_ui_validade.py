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
        return [(1, "24h"), (2, "48h")]

    def list_temperaturas(self):
        return []

    def list_active_allergens(self):
        return []

    def get_produto_info(self, codigo):
        return {
            "codigo": codigo,
            "produto": "Prod",
            "validade": 1,
            "informacaoadicional": "Duração curta",
        }

    def get_pvps(self, codigo):
        return {"pvps": [], "iva": None}

    def get_ingredientes(self, codigo):
        return []

    def set_validade(self, codigo, validade_cod):
        self.called = (codigo, validade_cod)
        return True

    def get_preparacao_html(self, codigo):
        return ""


def test_combo_updates_validade(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    assert ft.cbValidade.count() == 3
    assert ft.cbValidade.currentData() == 1
    ft.cbValidade.setCurrentIndex(2)
    qapp.processEvents()
    assert ds.called == ("P1", 2)
    ft.close()
