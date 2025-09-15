import logging

from domain import Product
from services.products import calculate_food_cost
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
            pvps=[123, 246, None, 0, 615],
            iva=23,
            ingredients=[],
        )

    def calculate_cost(self, product):
        return 100


def test_format_pt_number_basic():
    assert format_pt_number(1234.56) == "1\u00A0234,56"
    assert format_pt_number(None) == "—"


def test_ftapp_formats_numbers(qapp):
    ft = FTApp(DummyService())
    expected_texts = [
        format_pt_number(123),
        format_pt_number(246),
        "--N/A--",
        "--N/A--",
        format_pt_number(615),
    ]
    assert [lb.text() for lb in ft.lbPVPs] == expected_texts
    assert ft.edCustoTotal.text() == format_pt_number(100)
    expected_fc_texts = [
        format_pt_number(100),
        format_pt_number(50),
        "--N/A--",
        "--N/A--",
        format_pt_number(20),
    ]
    assert [lb.text() for lb in ft.lbFoodCosts] == expected_fc_texts
    ft.close()


def test_ftapp_food_cost_missing_iva(qapp, caplog):
    class NoIVAService(DummyService):
        def get_product_info(self, codigo):
            return Product(
                code=codigo,
                pvps=[123, 246, 615, 1000, 2000],
                iva=None,
                ingredients=[],
            )

    with caplog.at_level(logging.WARNING):
        ft = FTApp(NoIVAService())
    assert [lb.text() for lb in ft.lbFoodCosts] == ["--"] * 5
    assert any("missing Iva1" in rec.message for rec in caplog.records)
    ft.close()


def test_ftapp_food_costs_large_total(qapp):
    class HighTotalService(DummyService):
        def calculate_cost(self, product):
            return 1234.56

    ft = FTApp(HighTotalService())
    expected = format_pt_number(
        calculate_food_cost(1234.56, 123, 23)
    )
    assert ft.lbFoodCosts[0].text() == expected
    ft.close()
