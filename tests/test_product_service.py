import pytest
from unittest.mock import MagicMock

from ftv.services.products import calculate_cost, get_product_info
from ftv.data.datastore import DataStore
from ftv.domain.models import Ingredient


def test_calculate_cost_uses_ppu_when_total_missing():
    ingredients = [
        Ingredient(name="Ing1", quantity=2, unit="kg", ppu=3.0),
        Ingredient(name="Ing2", quantity=1.5, unit="kg", ppu=2.0),
    ]

    cost = calculate_cost(ingredients)

    assert cost == pytest.approx(9.0)


def test_calculate_cost_prefers_total_when_present():
    ingredients = [
        Ingredient(name="Ing1", quantity=2, unit="kg", ppu=3.0, total=5.0),
        Ingredient(name="Ing2", quantity=1.5, unit="kg", ppu=2.0),
    ]

    cost = calculate_cost(ingredients)

    assert cost == pytest.approx(8.0)


def test_get_product_info_builds_product_from_datastore():
    ds = MagicMock(spec=DataStore)
    ds.get_produto_info.return_value = {"codigo": "P1", "nome": "Produto 1"}
    ds.get_pvps.return_value = {"1": 10.0}
    ds.get_ingredientes.return_value = [
        {
            "nome": "Ing1",
            "qtd": 2,
            "unidade": "kg",
            "ppu": 3.0,
            "total": 6.0,
            "codigo": "I1",
        },
        {"nome": "Ing2", "qtd": 1, "unidade": "kg", "ppu": 2.0, "codigo": "I2"},
    ]

    product = get_product_info(ds, "P1")

    ds.get_produto_info.assert_called_once_with("P1")
    ds.get_pvps.assert_called_once_with("P1")
    ds.get_ingredientes.assert_called_once_with("P1")

    assert product.code == "P1"
    assert product.name == "Produto 1"
    assert product.pvps == {"1": 10.0}
    assert len(product.ingredients) == 2
    assert product.ingredients[0].name == "Ing1"
    assert product.ingredients[0].total == 6.0
    assert product.ingredients[1].total is None
    assert product.ingredients[1].ppu == 2.0
