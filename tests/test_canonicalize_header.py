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
    assert canonicalize_header("preco1") == "Preco1"
    assert canonicalize_header("preco1g", table="Produtos") == "Preco1G"
    assert canonicalize_header("preco1g", table="Outros") == "Preco1"
    assert canonicalize_header("iva1") == "Iva1"
    assert canonicalize_header("iva2") == "Iva2"
    assert canonicalize_header("IsencaoIva") == "IsencaoIva"
