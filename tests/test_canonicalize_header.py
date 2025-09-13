from services.products import canonicalize_header


def test_suffix_removed_and_ignored():
    assert canonicalize_header("Nome (não necessário p/ importar)") == "Nome"
    assert canonicalize_header("(não necessário p/ importar)") == ""


def test_space_pascalcase_and_alias_preserved():
    assert canonicalize_header("Prod venda") == "Codigo"
    assert canonicalize_header("Prod venda (não necessário p/ importar)") == "Codigo"
    assert canonicalize_header("Nome prod venda") == "NomeProdVenda"


def test_list_canonicalization_handles_suffix_and_duplicates():
    headers = [
        "Nome (não necessário p/ importar)",
        "Nome",
        "Prod venda",
        "Prod venda (não necessário p/ importar)",
        "Nome prod venda (não necessário p/ importar)",
    ]
    cleaned = [canonicalize_header(h) for h in headers]
    assert cleaned == ["Nome", "Nome", "Codigo", "Codigo", "NomeProdVenda"]
