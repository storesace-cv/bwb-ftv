from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Ingredient:
    name: str
    quantity: float
    unit: str
    ppu: Optional[float] = None
    total: Optional[float] = None
    code: Optional[str] = None

@dataclass
class Product:
    code: str
    name: Optional[str] = None
    familia: Optional[str] = None
    subfamilia: Optional[str] = None
    tipo_artigo_cod: Optional[int] = None
    validade_cod: Optional[int] = None
    temperatura_cod: Optional[int] = None
    pvps: Dict[str, Optional[float]] = field(default_factory=dict)
    ingredients: List[Ingredient] = field(default_factory=list)
