import logging
from datetime import datetime
from pathlib import Path

import pytest

from domain.models import Ingredient, Product
from reporting.ft_gestao import build_reportbro_context
from reporting.reportbro_export import load_template_definition
from reporting.reportbro_normalizer import STATIC_SECTION_PARAMETER
from ui.printing import _prepare_management_payload, _validate_reportbro_inputs
from utils.paths import get_project_root


def _make_product(**overrides) -> Product:
    product = Product(
        code=overrides.get("code", "TEST-01"),
        name=overrides.get("name", "Produto Teste"),
        familia=overrides.get("familia", "Família"),
        subfamilia=overrides.get("subfamilia", "Sub"),
        informacao_adicional="Notas",
        tipo_artigo_cod=2,
        validade_cod=5,
        temperatura_cod=3,
        pvps=[10.0, 15.5],
        iva=23,
        ingredients=[
            Ingredient(
                name="Ingrediente X",
                quantity=1.0,
                unit="kg",
                ppu=2.5,
                total=2.5,
                code="ING-X",
                weight=1.0,
            )
        ],
    )

    produtos_row = {
        "codigo": product.code,
        "produto": product.name,
        "familia": product.familia,
        "subfamilia": product.subfamilia,
        "afetastk": "Sim",
        "menu": "Menu Principal",
        "codbarras": "9988776655443",
        "tipomercad": "Direto",
        "tipovenda": "Balcao",
        "tipoproducao": "Manual",
        "tipogener": "G",
        "unstockvmpg": "kg",
        "unvendavmv": "kg",
        "uninvvmmpg": "kg",
        "unproduftpv": "kg",
        "codauxiliar": "AX1",
        "codauxiliar2": "AX2",
        "pcu": 12.5,
        "pcm": "8,40",
        "descontinuado": datetime(2024, 1, 15),
        "displojas": "Loja X",
        "tipoartigo": 2,
        "validade": 5,
        "temperatura": 3,
    }
    produtos_row.update(overrides.get("produtos_row", {}))
    product.produtos_row = produtos_row

    ficha_row = {
        "familiasubfamilia": "Família>Sub",
        "produtocodigo": product.code,
        "produtonome": product.name,
        "componentecodigo": "ING-X",
        "componentenome": "Ingrediente X",
        "qtd": 1.0,
        "unidade": "kg",
        "ppu": 2.5,
        "preco": 2.5,
        "peso": 1.0,
        "ordem": 1,
    }
    ficha_row.update(overrides.get("ficha_row", {}))
    product.fichas_tecnicas_rows = [ficha_row]

    precos_row = {
        "codigo": product.code,
        "loja": "Loja X",
        "ativo": "Sim",
        "preco1": 10.0,
        "preco2": 15.5,
        "preco3": 18.0,
        "preco4": 20.0,
        "preco5": 22.0,
        "iva1": 23,
        "iva2": 6,
        "isencaoiva": "N",
        "nomeprodvenda": product.name,
        "familia": product.familia,
        "subfamilia": product.subfamilia,
    }
    precos_row.update(overrides.get("precos_row", {}))
    product.precos_taxas_row = precos_row

    return product


def _build_dataset(product: Product):
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)
    template_path = Path("app/templates_store/templates/ft_gestao_02.json")
    template = load_template_definition(template_path)
    warnings = payload["reportbro"]["warnings"]
    _validate_reportbro_inputs(template, dataset, warnings)
    return dataset, warnings


def test_reportbro_dataset_with_complete_data():
    product = _make_product()
    dataset, warnings = _build_dataset(product)

    assert dataset["Produtos_Menu"] == "Menu Principal"
    assert dataset["Produtos_PCU"] == pytest.approx(12.5)
    assert dataset["Produtos_PCM"] == pytest.approx(8.4)
    assert dataset["Produtos_Descontinuado"] == "2024-01-15"
    assert dataset["FichasTecnicas_Qtd"] == pytest.approx(1.0)
    assert dataset["PrecosTaxas_Loja"] == "Loja X"
    assert not warnings
    assert dataset[STATIC_SECTION_PARAMETER] == [{}]


def test_missing_text_normalises_to_empty(caplog):
    product = _make_product(produtos_row={"menu": "   "})
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    assert dataset["Produtos_Menu"] == ""

    template = load_template_definition(
        Path("app/templates_store/templates/ft_gestao_02.json")
    )
    caplog.set_level(logging.WARNING, logger="ui.printing")
    _validate_reportbro_inputs(template, dataset, payload["reportbro"]["warnings"])

    assert any("Produtos_Menu" in record.message for record in caplog.records)


def test_invalid_number_coerces_to_zero():
    product = _make_product(produtos_row={"pcu": "abc"})
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    assert dataset["Produtos_PCU"] == 0
    reasons = {entry["reason"] for entry in payload["reportbro"]["warnings"]}
    assert "invalid-number" in reasons


def test_invalid_date_coerces_to_empty():
    product = _make_product(produtos_row={"descontinuado": "2024-99-01"})
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    assert dataset["Produtos_Descontinuado"] == ""
    reasons = {entry["reason"] for entry in payload["reportbro"]["warnings"]}
    assert "invalid-date" in reasons


def test_product_image_filename_with_existing_file(caplog):
    product = _make_product(code="IMG-VALID")
    root = get_project_root()
    image_path = root / "databases" / "images" / f"{product.code}.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"binary-image-data")

    caplog.set_level(logging.WARNING, logger="ui.printing")
    try:
        payload = _prepare_management_payload(product)
        dataset = build_reportbro_context(payload)

        assert payload["product_image_filename"] == str(image_path)
        assert dataset["product_image_filename"] == str(image_path)
        warning_messages = [
            record.getMessage()
            for record in caplog.records
            if record.levelno == logging.WARNING
        ]
        assert not warning_messages
    finally:
        if image_path.exists():
            image_path.unlink()


def test_product_image_filename_missing_code_logs_warning(caplog):
    product = _make_product(code=" ")
    product.produtos_row["codigo"] = "   "

    caplog.set_level(logging.WARNING, logger="ui.printing")
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    assert payload["product_image_filename"] == ""
    assert dataset["product_image_filename"] == ""
    warning_messages = [
        record.getMessage() for record in caplog.records if record.levelno == logging.WARNING
    ]
    assert any("Produtos_Codigo em falta" in message for message in warning_messages)


def test_product_image_filename_missing_file_logs_warning(caplog):
    product = _make_product(code="IMG-NOFILE")

    root = get_project_root()
    image_path = root / "databases" / "images" / f"{product.code}.png"
    if image_path.exists():
        image_path.unlink()

    caplog.set_level(logging.WARNING)
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    assert payload["product_image_filename"] == ""
    assert dataset["product_image_filename"] == ""
    warning_messages = [
        record.getMessage() for record in caplog.records if record.levelno == logging.WARNING
    ]
    assert any("Imagem de produto inexistente" in message for message in warning_messages)


def test_validation_accepts_string_style_id():
    product = _make_product()
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    template = load_template_definition(
        Path("app/templates_store/templates/ft_gestao_02.json")
    )
    # Should not raise despite template mixing string style identifiers
    _validate_reportbro_inputs(template, dataset, payload["reportbro"]["warnings"])
