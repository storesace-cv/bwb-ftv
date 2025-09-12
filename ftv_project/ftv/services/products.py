"""Utilities and service layer for product related operations."""

from typing import Iterable, List

from ftv.data.datastore import DataStore
from ftv.domain import Product, Ingredient


class ProductService:
    """High level API used by the UI to interact with products and helpers."""

    def __init__(self, ds: DataStore):
        self.ds = ds
        self.conn = getattr(ds, "conn", None)

    # -- pagination / ids -------------------------------------------------
    def total(self) -> int:
        return self.ds.total()

    def codigo_at(self, idx: int):
        return self.ds.codigo_at(idx)

    # -- auxiliary tables -------------------------------------------------
    def list_tipos_artigos(self):
        return self.ds.list_tipos_artigos()

    def list_validade(self):
        return self.ds.list_validade()

    def list_temperaturas(self):
        return self.ds.list_temperaturas()

    def list_active_allergens(self):
        return self.ds.list_active_allergens()

    # -- product retrieval ------------------------------------------------
    def get_product_info(self, codigo: str) -> Product:
        return get_product_info(self.ds, codigo)

    # -- cost calculations ------------------------------------------------
    def calculate_cost(
        self, product_or_ingredients: Iterable[Ingredient] | Product
    ) -> float:
        """Calculate total cost from a Product or iterable of Ingredients."""
        if isinstance(product_or_ingredients, Product):
            ingredients = product_or_ingredients.ingredients
        else:
            ingredients = list(product_or_ingredients)
        return calculate_cost(ingredients)


def get_product_info(ds: DataStore, codigo: str) -> Product:
    """Retrieve product information, pvps and ingredients as a :class:`Product`."""
    info = ds.get_produto_info(codigo) if ds else {}
    pvps = ds.get_pvps(codigo) if ds else {}
    ing_rows = ds.get_ingredientes(codigo) if ds else []

    ingredients: List[Ingredient] = []
    for row in ing_rows:
        ingredients.append(
            Ingredient(
                name=row.get("nome")
                or row.get("ingrediente")
                or row.get("designacao")
                or "",
                quantity=row.get("qtd") or row.get("quantidade") or row.get("QTD") or 0,
                unit=row.get("unidade") or "",
                ppu=row.get("ppu"),
                total=row.get("total"),
                code=row.get("codigo"),
            )
        )

    return Product(
        code=info.get("codigo") or codigo,
        name=info.get("nome"),
        familia=info.get("familia"),
        subfamilia=info.get("subfamilia"),
        tipo_artigo_cod=info.get("tipo_artigo_cod"),
        validade_cod=info.get("validade_cod"),
        temperatura_cod=info.get("temperatura_cod"),
        pvps=pvps,
        ingredients=ingredients,
    )


def calculate_cost(ingredients: Iterable[Ingredient]) -> float:
    """Return total cost for a list/iterable of ingredients."""
    total = 0.0
    for ing in ingredients:
        if ing.total is not None:
            try:
                total += float(ing.total)
                continue
            except (TypeError, ValueError):
                pass
        if ing.ppu is not None:
            try:
                total += float(ing.ppu) * float(ing.quantity)
            except (TypeError, ValueError):
                pass
    return total
