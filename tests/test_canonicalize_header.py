from services.products import canonicalize_header


def test_suffix_removed_and_ignored():
    assert canonicalize_header("Nome (não necessário p/ importar)") == "nome"
    assert canonicalize_header("(não necessário p/ importar)") == ""


def test_space_pascalcase_and_alias_preserved():
    assert canonicalize_header("Prod venda") == "codigo"
    assert canonicalize_header("Prod venda (não necessário p/ importar)") == "codigo"
    assert canonicalize_header("Nome prod venda") == "nomeprodvenda"
