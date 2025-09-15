import logging
import pytest
from unittest.mock import MagicMock

from services.products import (
    calculate_cost,
    calculate_food_cost,
    get_product_info,
    ProductService,
)
from data.datastore import DataStore
from domain.models import Ingredient
from utils.formatting import format_pt_number


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


def test_calculate_food_cost_basic():
    result = calculate_food_cost(25, 50, 23)
    assert result == pytest.approx(61.5)


def test_calculate_food_cost_invalid_inputs():
    assert calculate_food_cost(None, 50, 23) is None
    assert calculate_food_cost(10, 0, 23) is None
    assert calculate_food_cost(10, 50, None) is None


def test_calculate_food_cost_logs_product(caplog):
    with caplog.at_level(logging.WARNING):
        assert calculate_food_cost(10, "x", 23, product="P1") is None
    assert "P1" in caplog.text


def test_get_product_info_builds_product_from_datastore():
    ds = MagicMock(spec=DataStore)
    ds.get_produto_info.return_value = {"codigo": "P1", "produto": "Produto 1"}
    ds.get_pvps.return_value = {"pvps": [10.0], "iva": None}
    ds.get_ingredientes.return_value = [
        {
            "ComponenteNome": "Ing1",
            "Qtd": 2,
            "Unidade": "kg",
            "Ppu": 3.0,
            "Preco": 6.0,
            "ComponenteCodigo": "I1",
        },
        {
            "ComponenteNome": "Ing2",
            "Qtd": 1,
            "Unidade": "kg",
            "Ppu": 2.0,
            "ComponenteCodigo": "I2",
        },
    ]

    product = get_product_info(ds, "P1")

    ds.get_produto_info.assert_called_once_with("P1")
    ds.get_ingredientes.assert_called_once_with("P1")

    assert product.code == "P1"
    assert product.name == "Produto 1"
    assert product.pvps == [10.0]
    assert len(product.ingredients) == 2
    assert product.ingredients[0].name == "Ing1"
    assert format_pt_number(product.ingredients[0].total) == format_pt_number(6.0)
    assert product.ingredients[1].name == "Ing2"
    assert format_pt_number(product.ingredients[1].total) == format_pt_number(2.0)
    assert product.ingredients[1].ppu == 2.0


def test_list_fichas_tecnicas_logs_missing_ingredient_name(caplog):
    ds = MagicMock(spec=DataStore)
    ds.get_ingredientes.return_value = [
        {"Qtd": 1, "Unidade": "kg", "ComponenteCodigo": "I1"}
    ]
    service = ProductService(ds)

    with caplog.at_level(logging.WARNING):
        fichas = service.list_fichas_tecnicas("P1")

    assert fichas[0].ingredient == ""
    assert "P1" in caplog.text


def test_list_fichas_tecnicas_calculates_total_when_preco_missing():
    ds = MagicMock(spec=DataStore)
    ds.get_ingredientes.return_value = [
        {
            "ComponenteNome": "Ing1",
            "Qtd": 2,
            "Unidade": "kg",
            "Ppu": 3.0,
            "Preco": 6.0,
            "ComponenteCodigo": "I1",
        },
        {
            "ComponenteNome": "Ing2",
            "Qtd": 1.5,
            "Unidade": "kg",
            "Ppu": 2.0,
            "ComponenteCodigo": "I2",
        },
    ]
    service = ProductService(ds)

    fichas = service.list_fichas_tecnicas("P1")

    assert format_pt_number(fichas[0].total) == format_pt_number(6.0)
    assert format_pt_number(fichas[1].total) == format_pt_number(3.0)


def test_get_product_info_logs_missing_ingredient_name(caplog):
    ds = MagicMock(spec=DataStore)
    ds.get_produto_info.return_value = {"codigo": "P1", "produto": "Produto 1"}
    ds.get_pvps.return_value = {}
    ds.get_ingredientes.return_value = [
        {"Qtd": 2, "Unidade": "kg", "ComponenteCodigo": "I1"}
    ]

    with caplog.at_level(logging.WARNING):
        product = get_product_info(ds, "P1")

    assert product.ingredients[0].name == ""
    assert "P1" in caplog.text
