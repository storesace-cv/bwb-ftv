from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Ingredient:
    """Basic ingredient information used in product compositions."""
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None
    code: Optional[str] = None


@dataclass
class Product:
    """Domain representation of a product with its ingredients."""
    code: str
    name: Optional[str] = None
    family: Optional[str] = None
    subfamily: Optional[str] = None
    tipo_artigo_cod: Optional[int] = None
    validade_cod: Optional[int] = None
    temperatura_cod: Optional[int] = None
    ingredients: List[Ingredient] = field(default_factory=list)
