"""Product related business operations."""
from __future__ import annotations

from typing import Iterable

from ftv.domain import Product, Ingredient
from ftv.data.datastore import DataStore


def get_product_info(ds: DataStore, codigo: str) -> Product:
    """Fetch a product and its ingredients from the datastore."""
    info = ds.get_produto_info(codigo) or {}
    raw_ingredients: Iterable[dict] = ds.get_ingredientes(codigo) or []

    ingredients = [
        Ingredient(
            name=row.get("nome") or row.get("ingrediente"),
            quantity=row.get("qtd") or row.get("quantidade"),
            unit=row.get("unidade"),
            unit_cost=row.get("ppu"),
            total_cost=row.get("total"),
            code=row.get("codigo"),
        )
        for row in raw_ingredients
    ]

    return Product(
        code=info.get("codigo", codigo),
        name=info.get("nome") or info.get("descricao"),
        family=info.get("familia"),
        subfamily=info.get("subfamilia"),
        tipo_artigo_cod=info.get("tipo_artigo_cod"),
        validade_cod=info.get("validade_cod"),
        temperatura_cod=info.get("temperatura_cod"),
        ingredients=ingredients,
    )


def calculate_cost(product: Product) -> float:
    """Calculate the total cost of a product by summing ingredient totals."""
    total = 0.0
    for ing in product.ingredients:
        if ing.total_cost is not None:
            try:
                total += float(ing.total_cost)
            except (TypeError, ValueError):
                continue
        elif ing.unit_cost is not None and ing.quantity is not None:
            try:
                total += float(ing.unit_cost) * float(ing.quantity)
            except (TypeError, ValueError):
                continue
    return total
