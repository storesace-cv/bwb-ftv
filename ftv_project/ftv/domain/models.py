from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Ingredient:
    """Representa um ingrediente de um produto."""
    name: str
    quantity: float
    unit: str
    ppu: float  # preço por unidade
    total: float  # custo total do ingrediente
    code: Optional[str] = None

@dataclass
class Product:
    """Representa um produto com os seus ingredientes e PVPs."""
    code: str
    name: str
    familia: str = ""
    subfamilia: str = ""
    tipo_artigo_cod: Optional[int] = None
    validade_cod: Optional[int] = None
    temperatura_cod: Optional[int] = None
    pvps: Dict[str, Optional[float]] = field(default_factory=dict)
    ingredients: List[Ingredient] = field(default_factory=list)
