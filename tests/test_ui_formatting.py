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
        return None

    def list_tipos_artigos(self):
        return []

    def list_validade(self):
        return []

    def list_temperaturas(self):
        return []

    def list_active_allergens(self):
        return []

    def get_image_path(self, codigo: str) -> None:
        return None

    def save_product_image(self, codigo: str, src_path: str) -> None:
        pass

    def delete_product_image(self, codigo: str) -> None:
        pass

    def get_product_info(self, codigo):
        return Product(
            code=codigo,
            pvps=[1234.56, 2345.67, None, 0, 789.01],
            iva=None,
            ingredients=[],
        )

    def calculate_cost(self, product):
        return 1234.56


def test_format_pt_number_basic():
    assert format_pt_number(1234.56) == "1\u00A0234,56"
    assert format_pt_number(None) == "—"


def test_ftapp_formats_numbers(qapp):
    ft = FTApp(DummyService())
    expected_prices = [1234.56, 2345.67, None, 0, 789.01]
    expected_texts = [format_pt_number(p) for p in expected_prices]
    assert [lb.text() for lb in ft.lbPVPs] == expected_texts
    assert ft.edCustoTotal.text() == format_pt_number(1234.56)
    assert [lb.text() for lb in ft.lbFoodCosts] == [format_pt_number(None)] * 5
    ft.close()
