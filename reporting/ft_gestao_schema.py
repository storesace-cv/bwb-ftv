"""Schema metadata for the FT Gestão ReportBro integration."""

from __future__ import annotations

from typing import Any, Mapping


ParameterDefinition = Mapping[str, Any]


FT_GESTAO_PARAMETER_DEFINITIONS: dict[str, ParameterDefinition] = {
    # Produtos
    "Produtos_Codigo": {"section": "produtos", "field": "codigo", "type": "text"},
    "Produtos_Produto": {"section": "produtos", "field": "produto", "type": "text"},
    "Produtos_Familia": {"section": "produtos", "field": "familia", "type": "text"},
    "Produtos_SubFamilia": {
        "section": "produtos",
        "field": "subfamilia",
        "type": "text",
    },
    "Produtos_AfetaStk": {"section": "produtos", "field": "afetastk", "type": "text"},
    "Produtos_Menu": {"section": "produtos", "field": "menu", "type": "text"},
    "Produtos_CodBarras": {"section": "produtos", "field": "codbarras", "type": "text"},
    "Produtos_TipoMercad": {
        "section": "produtos",
        "field": "tipomercad",
        "type": "text",
    },
    "Produtos_TipoVenda": {
        "section": "produtos",
        "field": "tipovenda",
        "type": "text",
    },
    "Produtos_TipoProducao": {
        "section": "produtos",
        "field": "tipoproducao",
        "type": "text",
    },
    "Produtos_TipoGener": {
        "section": "produtos",
        "field": "tipogener",
        "type": "text",
    },
    "Produtos_UnStockVMPG": {
        "section": "produtos",
        "field": "unstockvmpg",
        "type": "text",
    },
    "Produtos_UnVendaVMV": {
        "section": "produtos",
        "field": "unvendavmv",
        "type": "text",
    },
    "Produtos_UnInvVMMMPG": {
        "section": "produtos",
        "field": "uninvvmmpg",
        "type": "text",
    },
    "Produtos_UnProduFtPV": {
        "section": "produtos",
        "field": "unproduftpv",
        "type": "text",
    },
    "Produtos_CodAuxiliar": {
        "section": "produtos",
        "field": "codauxiliar",
        "type": "text",
    },
    "Produtos_CodAuxiliar2": {
        "section": "produtos",
        "field": "codauxiliar2",
        "type": "text",
    },
    "Produtos_PCU": {
        "section": "produtos",
        "field": "pcu",
        "type": "number",
        "numeric_type": "float",
    },
    "Produtos_PCM": {
        "section": "produtos",
        "field": "pcm",
        "type": "number",
        "numeric_type": "float",
    },
    "Produtos_Descontinuado": {
        "section": "produtos",
        "field": "descontinuado",
        "type": "text",
        "format": "date",
    },
    "Produtos_DispLojas": {
        "section": "produtos",
        "field": "displojas",
        "type": "text",
    },
    "TiposArtigos_Cod": {
        "section": "tipos_artigos",
        "field": "cod",
        "type": "number",
        "numeric_type": "int",
    },
    "TiposArtigos_Descricao": {
        "section": "tipos_artigos",
        "field": "descricao",
        "type": "text",
    },
    "Validade_Cod": {
        "section": "validade",
        "field": "cod",
        "type": "number",
        "numeric_type": "int",
    },
    "Validade_Descricao": {
        "section": "validade",
        "field": "descricao",
        "type": "text",
    },
    "Temperaturas_Cod": {
        "section": "temperaturas",
        "field": "cod",
        "type": "number",
        "numeric_type": "int",
    },
    "Temperaturas_Descricao": {
        "section": "temperaturas",
        "field": "descricao",
        "type": "text",
    },
    "ProdutoPreparacao_ProdutoCodigo": {
        "section": "produto_preparacao",
        "field": "produtocodigo",
        "type": "text",
    },
    "ProdutoPreparacao_Html": {
        "section": "produto_preparacao",
        "field": "html",
        "type": "text",
    },
    # Fichas Técnicas
    "FichasTecnicas_FamiliaSubfamilia": {
        "section": "fichas_tecnicas",
        "field": "familiasubfamilia",
        "type": "text",
    },
    "FichasTecnicas_ProdutoCodigo": {
        "section": "fichas_tecnicas",
        "field": "produtocodigo",
        "type": "text",
    },
    "FichasTecnicas_ProdutoNome": {
        "section": "fichas_tecnicas",
        "field": "produtonome",
        "type": "text",
    },
    "FichasTecnicas_ComponenteCodigo": {
        "section": "fichas_tecnicas",
        "field": "componentecodigo",
        "type": "text",
    },
    "FichasTecnicas_ComponenteNome": {
        "section": "fichas_tecnicas",
        "field": "componentenome",
        "type": "text",
    },
    "FichasTecnicas_Qtd": {
        "section": "fichas_tecnicas",
        "field": "qtd",
        "type": "number",
        "numeric_type": "float",
    },
    "FichasTecnicas_Unidade": {
        "section": "fichas_tecnicas",
        "field": "unidade",
        "type": "text",
    },
    "FichasTecnicas_Ppu": {
        "section": "fichas_tecnicas",
        "field": "ppu",
        "type": "number",
        "numeric_type": "float",
    },
    "FichasTecnicas_Preco": {
        "section": "fichas_tecnicas",
        "field": "preco",
        "type": "number",
        "numeric_type": "float",
    },
    "FichasTecnicas_Peso": {
        "section": "fichas_tecnicas",
        "field": "peso",
        "type": "number",
        "numeric_type": "float",
    },
    "FichasTecnicas_Ordem": {
        "section": "fichas_tecnicas",
        "field": "ordem",
        "type": "number",
        "numeric_type": "int",
    },
    # Preços e taxas
    "PrecosTaxas_Codigo": {
        "section": "precos_taxas",
        "field": "codigo",
        "type": "text",
    },
    "PrecosTaxas_Loja": {
        "section": "precos_taxas",
        "field": "loja",
        "type": "text",
    },
    "PrecosTaxas_Ativo": {
        "section": "precos_taxas",
        "field": "ativo",
        "type": "text",
    },
    "PrecosTaxas_Preco1": {
        "section": "precos_taxas",
        "field": "preco1",
        "type": "number",
        "numeric_type": "float",
    },
    "PrecosTaxas_Preco2": {
        "section": "precos_taxas",
        "field": "preco2",
        "type": "number",
        "numeric_type": "float",
    },
    "PrecosTaxas_Preco3": {
        "section": "precos_taxas",
        "field": "preco3",
        "type": "number",
        "numeric_type": "float",
    },
    "PrecosTaxas_Preco4": {
        "section": "precos_taxas",
        "field": "preco4",
        "type": "number",
        "numeric_type": "float",
    },
    "PrecosTaxas_Preco5": {
        "section": "precos_taxas",
        "field": "preco5",
        "type": "number",
        "numeric_type": "float",
    },
    "PrecosTaxas_Iva1": {
        "section": "precos_taxas",
        "field": "iva1",
        "type": "number",
        "numeric_type": "float",
    },
    "PrecosTaxas_Iva2": {
        "section": "precos_taxas",
        "field": "iva2",
        "type": "number",
        "numeric_type": "float",
    },
    "PrecosTaxas_IsencaoIva": {
        "section": "precos_taxas",
        "field": "isencaoiva",
        "type": "text",
    },
    "PrecosTaxas_NomeProdVenda": {
        "section": "precos_taxas",
        "field": "nomeprodvenda",
        "type": "text",
    },
    "PrecosTaxas_Familia": {
        "section": "precos_taxas",
        "field": "familia",
        "type": "text",
    },
    "PrecosTaxas_SubFamilia": {
        "section": "precos_taxas",
        "field": "subfamilia",
        "type": "text",
    },
}


FT_GESTAO_EXPECTED_PARAMETERS = set(FT_GESTAO_PARAMETER_DEFINITIONS)


def default_for_parameter(name: str) -> Any:
    meta = FT_GESTAO_PARAMETER_DEFINITIONS.get(name, {})
    if meta.get("type") == "number":
        return 0
    if name.endswith("_Cod"):
        return 0
    return ""

