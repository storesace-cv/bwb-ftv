"""Official mapping of Excel headers to database columns for imports."""

from __future__ import annotations

from typing import Dict, Mapping, Set

# Mapping of Excel headers to the canonical database column names for each
# supported table. Keys are the headers expected in the spreadsheets (after
# CamelCase normalization) and the values are the corresponding SQLite column
# names.
HEADER_MAP: Dict[str, Dict[str, str]] = {
    "Produtos": {
        "Codigo": "Codigo",
        "Produto": "Produto",
        "Nome": "Nome",
        "Familia": "Familia",
        "SubFamilia": "SubFamilia",
        "InformacaoAdicional": "InformacaoAdicional",
        "AfetaStk": "AfetaStk",
        "Menu": "Menu",
        "CodBarras": "CodBarras",
        "TipoMercad": "TipoMercad",
        "TipoVenda": "TipoVenda",
        "TipoProducao": "TipoProducao",
        "TipoGener": "TipoGener",
        "UnStockVMPG": "UnStockVMPG",
        "UnVendaVMV": "UnVendaVMV",
        "UnInvVMMMPG": "UnInvVMMMPG",
        "UnProduFtPV": "UnProduFtPV",
        "CodAuxiliar": "CodAuxiliar",
        "CodAuxiliar2": "CodAuxiliar2",
        "PCU": "PCU",
        "PCM": "PCM",
        "Descontinuado": "Descontinuado",
        "DispLojas": "DispLojas",
        "TipoArtigo": "TipoArtigo",
        "Validade": "Validade",
        "Temperatura": "Temperatura",
        "Preco1G": "Preco1G",
        "Preco2G": "Preco2G",
        "Preco3G": "Preco3G",
        "Preco4G": "Preco4G",
        "Preco5G": "Preco5G",
        "Iva": "Iva",
        "Iva1": "Iva1",
        "Iva2": "Iva2",
    },
    "FichasTecnicas": {
        "FamiliaSubfamilia": "FamiliaSubfamilia",
        "ProdutoCodigo": "ProdutoCodigo",
        "ProdutoNome": "ProdutoNome",
        "ComponenteCodigo": "ComponenteCodigo",
        "ComponenteNome": "ComponenteNome",
        "Qtd": "Qtd",
        "Unidade": "Unidade",
        "Ppu": "Ppu",
        "Preco": "Preco",
        "Peso": "Peso",
        "Ordem": "Ordem",
    },
    "PrecosTaxas": {
        "Codigo": "Codigo",
        "Loja": "Loja",
        "Preco1": "Preco1",
        "Preco2": "Preco2",
        "Preco3": "Preco3",
        "Preco4": "Preco4",
        "Preco5": "Preco5",
        "Iva1": "Iva1",
        "Iva2": "Iva2",
        "IsencaoIva": "IsencaoIva",
        "NomeProdVenda": "NomeProdVenda",
        "Familia": "Familia",
        "SubFamilia": "SubFamilia",
        "Ativo": "Ativo",
    },
}


def allowed_headers_for(table: str) -> Set[str]:
    """Return the set of allowed canonical headers for ``table``."""

    mapping: Mapping[str, str] | None = HEADER_MAP.get(table)
    if not mapping:
        return set()
    return set(mapping.values())
