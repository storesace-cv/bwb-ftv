import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from data.datastore import DataStore
from domain.models import Ingredient, Product
from matplotlib.axes import Axes
from reporting.ft_gestao import _format_percentage, build_reportbro_context
from reporting.graphics import gerar_grafico_foodcost_pie
from reporting.reportbro_export import load_template_definition
from reporting.reportbro_normalizer import STATIC_SECTION_PARAMETER
from services.products import get_product_info
from ui.printing import _prepare_management_payload, _validate_reportbro_inputs
from utils.paths import get_project_root


def _placeholder_image_path() -> Path:
    return get_project_root() / "ui" / "no-image-thumb.png"


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

    tipos_row = {"cod": 2, "descricao": "Tipo padrão"}
    tipos_row.update(overrides.get("tipos_artigos_row", {}))
    product.tipos_artigos_row = tipos_row

    validade_row = {"cod": 5, "descricao": "Validade padrão"}
    validade_row.update(overrides.get("validade_row", {}))
    product.validade_row = validade_row

    temperaturas_row = {"cod": 3, "descricao": "Frio"}
    temperaturas_row.update(overrides.get("temperaturas_row", {}))
    product.temperaturas_row = temperaturas_row

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

    preparacao_row = {
        "produtocodigo": product.code,
        "html": "<p>Preparação padrão.</p>",
    }
    preparacao_row.update(overrides.get("produto_preparacao_row", {}))
    product.produto_preparacao_row = preparacao_row

    return product


def _build_dataset(product: Product):
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)
    template_path = Path("app/templates_store/templates/ft_gestao_00_base.json")
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
    assert dataset["TiposArtigos_Cod"] == 2
    assert dataset["TiposArtigos_Descricao"] == "Tipo padrão"
    assert dataset["product_tipo_artigo_cod"] == "Tipo padrão"
    assert dataset["Validade_Cod"] == 5
    assert dataset["Validade_Descricao"] == "Validade padrão"
    assert dataset["product_validade_cod"] == "Validade padrão"
    assert dataset["Temperaturas_Cod"] == 3
    assert dataset["Temperaturas_Descricao"] == "Frio"
    assert dataset["product_temperatura_cod"] == "Frio"
    assert dataset["ProdutoPreparacao_ProdutoCodigo"] == "TEST-01"
    assert dataset["ProdutoPreparacao_Html"] == "<p>Preparação padrão.</p>"
    assert not warnings
    assert dataset[STATIC_SECTION_PARAMETER] == [{}]
    placeholder = _placeholder_image_path()
    assert dataset["product_image_filename"] == str(placeholder)
    assert dataset["product_image_uri"] == placeholder.as_uri()
    assert dataset["product_image_path"] == str(placeholder)


def test_missing_text_normalises_to_none(caplog):
    product = _make_product(produtos_row={"menu": "   "})
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    assert dataset["Produtos_Menu"] is None

    template = load_template_definition(
        Path("app/templates_store/templates/ft_gestao_00_base.json")
    )
    caplog.set_level(logging.WARNING, logger="ui.printing")
    _validate_reportbro_inputs(template, dataset, payload["reportbro"]["warnings"])

    assert any("Produtos_Menu" in record.message for record in caplog.records)


def test_invalid_number_coerces_to_none():
    product = _make_product(produtos_row={"pcu": "abc"})
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    assert dataset["Produtos_PCU"] is None
    reasons = {entry["reason"] for entry in payload["reportbro"]["warnings"]}
    assert "invalid-number" in reasons


def test_invalid_date_coerces_to_empty():
    product = _make_product(produtos_row={"descontinuado": "2024-99-01"})
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    assert dataset["Produtos_Descontinuado"] == ""
    reasons = {entry["reason"] for entry in payload["reportbro"]["warnings"]}
    assert "invalid-date" in reasons


def test_datastore_product_populates_auxiliary_descriptions():
    with DataStore(db_path=":memory:") as ds:
        conn = ds.conn
        assert conn is not None

        conn.execute(
            "INSERT INTO TiposArtigos (Cod, Descricao, Ativo) VALUES (?, ?, 1)",
            (7, "Tipo proveniente da BD"),
        )
        conn.execute(
            "INSERT INTO Validade (Cod, Descricao, Ativo) VALUES (?, ?, 1)",
            (12, "Validade fresca"),
        )
        conn.execute(
            "INSERT INTO Temperaturas (Cod, Descricao, Ativo) VALUES (?, ?, 1)",
            (3, "Frio positivo"),
        )
        conn.execute(
            "INSERT INTO Produtos (Codigo, Produto, TipoArtigo, Validade, Temperatura) "
            "VALUES (?, ?, ?, ?, ?)",
            ("DB-001", "Produto BD", 7, 12, 3),
        )
        conn.execute(
            "INSERT INTO FichasTecnicas (ProdutoCodigo, ProdutoNome, ComponenteCodigo, "
            "ComponenteNome, Qtd, Unidade, Ppu, Preco, Peso, Ordem) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("DB-001", "Produto BD", "ING-1", "Ingrediente 1", 1.0, "kg", 2.5, 2.5, 1.0, 1),
        )
        conn.execute(
            "INSERT INTO PrecosTaxas (Codigo, Loja, Preco1, Iva1) VALUES (?, ?, ?, ?)",
            ("DB-001", "Loja Central", 10.0, 23.0),
        )
        conn.commit()

        product = get_product_info(ds, "DB-001")
        dataset, warnings = _build_dataset(product)

    assert dataset["TiposArtigos_Cod"] == 7
    assert dataset["TiposArtigos_Descricao"] == "Tipo proveniente da BD"
    assert dataset["Validade_Cod"] == 12
    assert dataset["Validade_Descricao"] == "Validade fresca"
    assert dataset["Temperaturas_Cod"] == 3
    assert dataset["Temperaturas_Descricao"] == "Frio positivo"
    warning_fields = {entry.get("field") for entry in warnings}
    assert "TiposArtigos_Descricao" not in warning_fields
    assert "Validade_Descricao" not in warning_fields
    assert "Temperaturas_Descricao" not in warning_fields


def test_product_image_filename_with_existing_file(caplog):
    product = _make_product(code="IMG-VALID")
    root = get_project_root()
    image_path = root / "databases" / "images" / f"{product.code}.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"binary-image-data")

    caplog.set_level(logging.INFO, logger="ui.printing")
    caplog.set_level(logging.INFO, logger="reporting.ft_gestao")
    try:
        payload = _prepare_management_payload(product)
        dataset = build_reportbro_context(payload)
        expected_uri = image_path.as_uri()

        assert payload["product_image_filename"] == str(image_path)
        assert payload["product_image_uri"] == expected_uri
        assert dataset["product_image_filename"] == str(image_path)
        assert dataset["product_image_uri"] == expected_uri
        warning_messages = [
            record.getMessage()
            for record in caplog.records
            if record.levelno == logging.WARNING
        ]
        assert not warning_messages
        printing_info = [
            record.getMessage()
            for record in caplog.records
            if record.name == "ui.printing" and record.levelno == logging.INFO
        ]
        assert any(
            product.code in message
            and str(image_path) in message
            and "payload" in message
            and expected_uri in message
            for message in printing_info
        )

        gestao_info = [
            record.getMessage()
            for record in caplog.records
            if record.name == "reporting.ft_gestao" and record.levelno == logging.INFO
        ]
        assert any(
            "product_image_filename" in message
            and str(image_path) in message
            and "product_image_path" in message
            and "product_image_uri" in message
            and expected_uri in message
            for message in gestao_info
        )
    finally:
        if image_path.exists():
            image_path.unlink()


def test_product_image_filename_missing_code_logs_warning(caplog):
    product = _make_product(code=" ")
    product.produtos_row["codigo"] = "   "

    caplog.set_level(logging.INFO, logger="ui.printing")
    caplog.set_level(logging.INFO, logger="reporting.ft_gestao")
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    placeholder = _placeholder_image_path()
    expected_path = str(placeholder)
    expected_uri = placeholder.as_uri()

    assert payload["product_image_filename"] == expected_path
    assert payload["product_image_uri"] == expected_uri
    assert dataset["product_image_filename"] == expected_path
    assert dataset["product_image_uri"] == expected_uri
    assert dataset["product_image_path"] == expected_path
    warning_messages = [
        record.getMessage() for record in caplog.records if record.levelno == logging.WARNING
    ]
    assert any("Produtos_Codigo em falta" in message for message in warning_messages)

    printing_info = [
        record.getMessage()
        for record in caplog.records
        if record.name == "ui.printing" and record.levelno == logging.INFO
    ]
    assert any(
        "normalizado=''" in message
        and f"caminho='{expected_path}'" in message
        and expected_uri in message
        for message in printing_info
    )
    assert any("destino=" in message for message in printing_info)

    gestao_info = [
        record.getMessage()
        for record in caplog.records
        if record.name == "reporting.ft_gestao" and record.levelno == logging.INFO
    ]
    assert any(
        "product_image_filename" in message and expected_path in message
        for message in gestao_info
    )
    assert any(
        "product_image_uri" in message and expected_uri in message
        for message in gestao_info
    )


def test_product_image_filename_missing_file_logs_warning(caplog):
    product = _make_product(code="IMG-NOFILE")

    root = get_project_root()
    image_path = root / "databases" / "images" / f"{product.code}.png"
    if image_path.exists():
        image_path.unlink()

    caplog.set_level(logging.INFO, logger="ui.printing")
    caplog.set_level(logging.INFO, logger="reporting.ft_gestao")
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    placeholder = _placeholder_image_path()
    expected_path = str(placeholder)
    expected_uri = placeholder.as_uri()

    assert payload["product_image_filename"] == expected_path
    assert payload["product_image_uri"] == expected_uri
    assert dataset["product_image_filename"] == expected_path
    assert dataset["product_image_uri"] == expected_uri
    assert dataset["product_image_path"] == expected_path
    warning_messages = [
        record.getMessage() for record in caplog.records if record.levelno == logging.WARNING
    ]
    assert any("Imagem de produto inexistente" in message for message in warning_messages)

    printing_info = [
        record.getMessage()
        for record in caplog.records
        if record.name == "ui.printing" and record.levelno == logging.INFO
    ]
    assert any(
        product.code in message
        and f"caminho='{expected_path}'" in message
        and expected_uri in message
        for message in printing_info
    )

    gestao_info = [
        record.getMessage()
        for record in caplog.records
        if record.name == "reporting.ft_gestao" and record.levelno == logging.INFO
    ]
    assert any(
        "product_image_filename" in message and expected_path in message
        for message in gestao_info
    )
    assert any(
        "product_image_uri" in message and expected_uri in message
        for message in gestao_info
    )


def test_foodcost_graph_integration(monkeypatch):
    product = _make_product()
    captured: dict[str, Any] = {}

    def fake_graph(ingredients):
        captured["ingredients"] = ingredients
        return "/tmp/chart.png"

    monkeypatch.setattr("ui.printing.gerar_grafico_foodcost_pie", fake_graph)

    payload = _prepare_management_payload(product)
    assert payload["GraficoFoodCost_Filename"] == "/tmp/chart.png"
    params = payload["reportbro"]["parameters"]
    assert params["GraficoFoodCost_Filename"] == "/tmp/chart.png"

    dataset = build_reportbro_context(payload)
    assert dataset["GraficoFoodCost_Filename"] == Path("/tmp/chart.png").resolve().as_uri()

    assert "ingredients" in captured
    ingredient_weights = [entry.get("peso") for entry in captured["ingredients"]]
    assert ingredient_weights == [pytest.approx(1.0)]

    food_cost_values = list(payload["blocks"]["B3"].get("food_cost") or [])
    for index in range(1, 6):
        fc_value = food_cost_values[index - 1] if index - 1 < len(food_cost_values) else None
        assert dataset[f"FoodCost_Nivel{index}"] == _format_percentage(fc_value)


def test_foodcost_graph_sem_dados_fallback(monkeypatch):
    recorded: dict[str, Any] = {}

    original_pie = Axes.pie

    def spy_pie(self, x, *args, **kwargs):
        recorded["sizes"] = list(x)
        recorded["labels"] = list(kwargs.get("labels", []))
        return original_pie(self, x, *args, **kwargs)

    monkeypatch.setattr(Axes, "pie", spy_pie)

    path = gerar_grafico_foodcost_pie(
        [
            {"FichasTecnicas_ComponenteNome": "Sem peso", "FichasTecnicas_Peso": 0},
            {"nome": "Negativo", "peso": -2},
        ]
    )

    assert Path(path).name == "foodcost_pie.png"
    assert recorded["labels"] == ["Sem dados"]
    assert recorded["sizes"] == [1.0]

    Path(path).unlink(missing_ok=True)


def test_validation_accepts_string_style_id():
    product = _make_product()
    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    template = load_template_definition(
        Path("app/templates_store/templates/ft_gestao_00_base.json")
    )
    # Should not raise despite template mixing string style identifiers
    _validate_reportbro_inputs(template, dataset, payload["reportbro"]["warnings"])
