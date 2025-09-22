import pytest

from services.products import canonicalize_header


def test_suffix_removed_and_ignored():
    assert canonicalize_header("Nome (não necessário p/ importar)") == "Nome"
    assert canonicalize_header("(não necessário p/ importar)") == ""


def test_space_pascalcase_and_alias_preserved():
    assert canonicalize_header("Prod venda") == "ProdVenda"
    assert canonicalize_header("Prod venda (não necessário p/ importar)") == "ProdVenda"
    assert canonicalize_header("Nome prod venda") == "NomeProdVenda"


def test_nome_and_produto_alias_removed():
    assert canonicalize_header("Produto") == "Produto"
    assert canonicalize_header("Nome") == "Nome"


def test_list_canonicalization_handles_suffix_and_duplicates():
    headers = [
        "Nome (não necessário p/ importar)",
        "Nome",
        "Prod venda",
        "Prod venda (não necessário p/ importar)",
        "Nome prod venda (não necessário p/ importar)",
    ]
    cleaned = [canonicalize_header(h) for h in headers]
    assert cleaned == ["Nome", "Nome", "ProdVenda", "ProdVenda", "NomeProdVenda"]


def test_price_and_iva_aliases():
    assert canonicalize_header("preco1_5") == "Preco1"
    assert canonicalize_header("preco5") == "Preco5"
    assert canonicalize_header("preco1g", table="Produtos") == "Preco1G"
    assert canonicalize_header("preco1g", table="Outros") == "Preco1"
    assert canonicalize_header("iva1") == "Iva1"
    assert canonicalize_header("iva2") == "Iva2"
    assert canonicalize_header("IsencaoIva") == "IsencaoIva"


def test_iva_space_variations():
    assert canonicalize_header("iva 1") == "Iva1"
    assert canonicalize_header("iva 2") == "Iva2"


def test_invalid_iva_aliases_remain_unmapped():
    assert canonicalize_header("iva12") == "Iva12"
    assert canonicalize_header("iva1_2") == "Iva12"


def test_prod_venda_header_for_precos_taxas_maps_to_codigo():
    assert canonicalize_header("Prod venda", table="PrecosTaxas") == "Codigo"
    assert (
        canonicalize_header(
            "Prod venda (não necessário p/ importar)", table="PrecosTaxas"
        )
        == "Codigo"
    )


def test_nome_prod_venda_header_remains_available_for_precos_taxas():
    assert (
        canonicalize_header("Nome prod venda", table="PrecosTaxas")
        == "NomeProdVenda"
    )


def test_valid_header_for_table_is_allowed():
    assert canonicalize_header("Preco1", table="PrecosTaxas") == "Preco1"


def test_uninvvmmpg_alias_for_produtos():
    assert (
        canonicalize_header("Un Inv (V+M,M,P,G)", table="Produtos")
        == "UnInvVMMMPG"
    )


def test_ppu_header_is_uppercase_for_fichas_tecnicas():
    assert canonicalize_header("PPU", table="FichasTecnicas") == "PPU"
    assert canonicalize_header("Ppu", table="FichasTecnicas") == "PPU"
