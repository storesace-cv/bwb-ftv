"""Serviços de domínio relacionados a produtos."""
from __future__ import annotations

from typing import List, Optional

from ftv.data.datastore import DataStore
from ftv.domain import Product, Ingredient


class ProductService:
    """Fornece operações de negócio para produtos."""

    def __init__(self, datastore: DataStore):
        self._ds = datastore

    # Expor conexão bruta quando necessário pela UI
    @property
    def conn(self):
        return getattr(self._ds, "conn", None)

    # ---- Operações básicas de navegação ----
    def total(self) -> int:
        return self._ds.total()

    def codigo_at(self, idx: int) -> Optional[str]:
        return self._ds.codigo_at(idx)

    # ---- Listagens auxiliares ----
    def list_active_allergens(self):
        return self._ds.list_active_allergens()

    def list_tipos_artigos(self):
        return self._ds.list_tipos_artigos()

    def list_validade(self):
        return self._ds.list_validade()

    def list_temperaturas(self):
        return self._ds.list_temperaturas()

    # ---- Produto ----
    def get_product(self, codigo: str) -> Product:
        info = self._ds.get_produto_info(codigo) or {}
        pvps = self._ds.get_pvps(codigo) or {}
        ing_raw = self._ds.get_ingredientes(codigo) or []
        ingredients: List[Ingredient] = []
        for row in ing_raw:
            ingredients.append(
                Ingredient(
                    name=str(row.get("nome") or row.get("designacao") or row.get("ingrediente") or ""),
                    quantity=float(row.get("qtd") or row.get("quantidade") or 0),
                    unit=str(row.get("unidade") or ""),
                    ppu=float(row.get("ppu") or 0),
                    total=float(row.get("total") or 0),
                    code=row.get("codigo"),
                )
            )
        return Product(
            code=str(info.get("codigo", "")),
            name=str(info.get("nome", "")),
            familia=str(info.get("familia", "")),
            subfamilia=str(info.get("subfamilia", "")),
            tipo_artigo_cod=info.get("tipo_artigo_cod"),
            validade_cod=info.get("validade_cod"),
            temperatura_cod=info.get("temperatura_cod"),
            pvps=pvps,
            ingredients=ingredients,
        )

    def calculate_cost(self, product: Product) -> float:
        """Calcula o custo total de um produto pela soma dos ingredientes."""
        return sum(ing.total for ing in product.ingredients)
