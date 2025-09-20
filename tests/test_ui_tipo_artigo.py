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
        return [(1, "TipoA"), (2, "TipoB")]

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
            "tipoartigo": 1,
            "informacaoadicional": "Tipo padrão",
        }

    def get_pvps(self, codigo):
        return {"pvps": [], "iva": None}

    def get_ingredientes(self, codigo):
        return []

    def set_tipo_artigo(self, codigo, tipo_cod):
        self.called = (codigo, tipo_cod)
        return True

    def get_preparacao_html(self, codigo):
        return ""


def test_combo_updates_tipo_artigo(qapp):
    ds = StubDataStore()
    service = ProductService(ds)
    ft = FTApp(service)
    assert ft.cbTipos.count() == 3
    assert ft.cbTipos.currentData() == 1
    ft.cbTipos.setCurrentIndex(2)
    qapp.processEvents()
    assert ds.called == ("P1", 2)
    ft.close()
