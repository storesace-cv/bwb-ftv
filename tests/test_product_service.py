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


def test_calculate_cost_logs_invalid_total_and_uses_fallback(caplog):
    ingredients = [
        Ingredient(name="Ing1", quantity=2, unit="kg", ppu=3.0, total="oops"),
    ]

    with caplog.at_level(logging.WARNING):
        cost = calculate_cost(ingredients)

    assert cost == pytest.approx(6.0)
    assert "Ing1" in caplog.text


def test_calculate_cost_logs_invalid_unit_cost(caplog):
    ingredients = [
        Ingredient(name="Ing2", quantity="two", unit="kg", ppu=2.0),
    ]

    with caplog.at_level(logging.DEBUG):
        cost = calculate_cost(ingredients)

    assert cost == pytest.approx(0.0)
    assert "Ing2" in caplog.text


def test_calculate_cost_collects_skipped_entries():
    ingredients = [
        Ingredient(name="Ing1", quantity=2, unit="kg", ppu=3.0, total="oops"),
        Ingredient(name="Ing2", quantity="two", unit="kg", ppu=2.0),
    ]

    cost, skipped = calculate_cost(ingredients, include_skipped=True)

    assert cost == pytest.approx(6.0)
    assert len(skipped) == 2
    assert {entry["stage"] for entry in skipped} == {"total", "ppu"}
    assert {entry["identifier"] for entry in skipped} == {"Ing1", "Ing2"}


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
    ds.get_produto_info.return_value = {
        "codigo": "P1",
        "produto": "Produto 1",
        "informacaoadicional": "Notas relevantes",
    }
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
    assert product.informacao_adicional == "Notas relevantes"
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


def test_product_service_get_product_allergens_delegates():
    ds = MagicMock(spec=DataStore)
    ds.get_product_allergens.return_value = [1, 3]
    service = ProductService(ds)

    result = service.get_product_allergens("PX")

    assert result == [1, 3]
    ds.get_product_allergens.assert_called_once_with("PX")


def test_product_service_set_product_allergens_delegates():
    ds = MagicMock(spec=DataStore)
    ds.set_product_allergens.return_value = True
    service = ProductService(ds)

    assert service.set_product_allergens("PX", [2, 4]) is True
    ds.set_product_allergens.assert_called_once_with("PX", [2, 4])


def test_product_service_set_search_filters_delegates():
    ds = MagicMock(spec=DataStore)
    service = ProductService(ds)

    service.set_search_filters(
        produto="bolo",
        ingrediente="chocolate",
        familia="Doces",
        subfamilia="Bolos",
    )

    ds.set_search_filters.assert_called_once_with(
        produto="bolo",
        ingrediente="chocolate",
        familia="Doces",
        subfamilia="Bolos",
    )


def test_product_service_set_search_filters_omits_unset_families():
    ds = MagicMock(spec=DataStore)
    service = ProductService(ds)

    service.set_search_filters(produto="bolo")

    ds.set_search_filters.assert_called_once_with(
        produto="bolo",
        ingrediente=None,
    )


def test_product_service_list_families_with_subfamilies_prefers_new_helper():
    ds = MagicMock(spec=DataStore)
    ds.list_families_with_subfamilies.return_value = {"A": ("B",)}
    service = ProductService(ds)

    assert service.list_families_with_subfamilies() == {"A": ("B",)}
    ds.list_families_with_subfamilies.assert_called_once_with()
