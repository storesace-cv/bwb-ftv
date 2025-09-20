"""Domain models for FTV project."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Ingredient:
    """Representation of an ingredient used in a product."""

    name: str
    quantity: float
    unit: str
    ppu: float | None = None
    total: float | None = None
    code: str | None = None


@dataclass
class FichaTecnica:
    """Representation of a row in the ``FichasTecnicas`` table."""

    ingredient: str
    quantity: float
    unit: str
    ppu: float | None = None
    total: float | None = None
    code: str | None = None


@dataclass
class Product:
    """Representation of a product with associated ingredients."""

    code: str
    name: str | None = None
    familia: str | None = None
    subfamilia: str | None = None
    informacao_adicional: str | None = None
    tipo_artigo_cod: int | None = None
    validade_cod: int | None = None
    temperatura_cod: int | None = None
    pvps: List[float | None] = field(default_factory=list)
    iva: float | None = None
    ingredients: List[Ingredient] = field(default_factory=list)
