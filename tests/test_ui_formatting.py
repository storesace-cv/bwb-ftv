from domain import Product
from ui.ui_editor_fonte import FTApp
from utils.formatting import format_pt_number


class DummyService:
    def __init__(self):
        self.ds = None
        self.conn = None

    def total(self):
        return 1

    def codigo_at(self, idx):
        return "T1"

    def list_tipos_artigos(self):
        return []

    def list_validade(self):
        return []

    def list_temperaturas(self):
        return []

    def list_active_allergens(self):
        return []

    def get_product_info(self, codigo):
        return Product(code=codigo, pvp=1234.56, iva=None, ingredients=[])

    def calculate_cost(self, product):
        return 1234.56


def test_format_pt_number_basic():
    assert format_pt_number(1234.56) == "1\u00A0234,56"
    assert format_pt_number(None) == "—"


def test_ftapp_formats_numbers(qapp):
    ft = FTApp(DummyService())
    assert ft.lbPVP.text() == "1\u00A0234,56"
    assert ft.edCustoTotal.text() == "1\u00A0234,56"
    ft.close()
