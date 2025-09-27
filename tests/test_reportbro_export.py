from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import pytest
from app.server.routes_reportbro import _normalise_template_payload
from app.server.services.report_service import (
    _render_fallback_pdf as service_render_fallback_pdf,
)
from domain.models import Ingredient, Product
from reporting.ft_gestao import EMPTY_FIELD, build_reportbro_context
from reporting.reportbro_export import (
    load_template_definition,
    render_pdf_bytes,
    render_pdf_to_path,
    _render_fallback_pdf as export_render_fallback_pdf,
)
from reporting.reportbro_normalizer import STATIC_SECTION_PARAMETER
from ui.printing import _prepare_management_payload, generate_ft_gestao_reportbro_pdf
from utils.paths import get_project_root


def _placeholder_image_path() -> Path:
    return get_project_root() / "ui" / "no-image-thumb.png"


def _extract_pdf_streams(path: Path) -> list[str]:
    data = path.read_bytes()
    streams: list[str] = []
    start = 0
    while True:
        stream_pos = data.find(b"stream", start)
        if stream_pos == -1:
            break
        line_end = data.find(b"\n", stream_pos)
        if line_end == -1:
            break
        end = data.find(b"endstream", line_end)
        if end == -1:
            break
        chunk = data[line_end + 1 : end].strip(b"\r\n")
        try:
            import zlib

            decoded = zlib.decompress(chunk)
        except zlib.error:
            decoded = chunk
        streams.append(decoded.decode("latin-1", "ignore"))
        start = end + len("endstream")
    return streams


def _sample_product() -> Product:
    product = Product(
        code="RB-01",
        name="Produto ReportBro",
        familia="Família",
        subfamilia="Sub",
        informacao_adicional="Notas adicionais",
        tipo_artigo_cod=2,
        validade_cod=5,
        temperatura_cod=3,
        pvps=[10.0, 15.5],
        iva=23,
        ingredients=[
            Ingredient(
                name="Ingrediente A",
                quantity=1.25,
                unit="kg",
                ppu=2.5,
                total=3.125,
                code="IA-01",
                weight=1.25,
            ),
            Ingredient(
                name="Ingrediente B",
                quantity=0.5,
                unit="L",
                ppu=1.2,
                total=0.6,
                code="IB-02",
                weight=0.5,
            ),
        ],
    )

    product.produtos_row = {
        "codigo": "RB-01",
        "produto": "Produto ReportBro",
        "familia": "Família",
        "subfamilia": "Sub",
        "afetastk": "Sim",
        "menu": "Principal",
        "codbarras": "1234567890123",
        "tipomercad": "Canal",
        "tipovenda": "Direta",
        "tipoproducao": "Manual",
        "tipogener": "G",
        "unstockvmpg": "kg",
        "unvendavmv": "kg",
        "uninvvmmpg": "kg",
        "unproduftpv": "kg",
        "codauxiliar": "AUX1",
        "codauxiliar2": "AUX2",
        "pcu": "12,5",
        "pcm": 8.75,
        "descontinuado": datetime(2024, 5, 1),
        "displojas": "Loja A",
        "tipoartigo": 2,
        "validade": 5,
        "temperatura": 3,
    }
    product.tipos_artigos_row = {"cod": 2, "descricao": "Produto acabado"}
    product.validade_row = {"cod": 5, "descricao": "72 horas"}
    product.temperaturas_row = {"cod": 3, "descricao": "Frio"}
    product.produto_preparacao_row = {
        "produtocodigo": "RB-01",
        "html": "<p>Preparar e servir.</p>",
    }
    product.fichas_tecnicas_rows = [
        {
            "familiasubfamilia": "Família>Sub",
            "produtocodigo": "RB-01",
            "produtonome": "Produto ReportBro",
            "componentecodigo": "IA-01",
            "componentenome": "Ingrediente A",
            "qtd": 1.25,
            "unidade": "kg",
            "ppu": 2.5,
            "preco": 3.125,
            "peso": 1.25,
            "ordem": 1,
        }
    ]
    product.precos_taxas_row = {
        "codigo": "RB-01",
        "loja": "Loja Central",
        "ativo": "Sim",
        "preco1": 10.0,
        "preco2": 15.5,
        "preco3": None,
        "preco4": None,
        "preco5": None,
        "iva1": 23,
        "iva2": 6,
        "isencaoiva": "",
        "nomeprodvenda": "Produto ReportBro",
        "familia": "Família",
        "subfamilia": "Sub",
    }
    return product


def test_build_reportbro_context_formats_sections():
    payload = _prepare_management_payload(_sample_product())

    class LocalisedStr(str):
        def __float__(self):
            return float(self.replace(",", "."))

        def __lt__(self, other):
            try:
                return float(self) < other
            except TypeError:
                return super().__lt__(other)

    payload["blocks"]["B2"]["ingredientes"].append(
        {
            "nome": "Ingrediente Localizado",
            "quantidade": LocalisedStr("0,25"),
            "unidade": "kg",
            "ppu": LocalisedStr("1,50"),
            "total": LocalisedStr("1,50"),
            "peso": LocalisedStr("0,25"),
            "ordem": 3,
        }
    )
    dataset = build_reportbro_context(payload)

    placeholder = _placeholder_image_path()

    assert dataset["title"] == "Ficha Técnica de Gestão"
    assert "Produto" in dataset["product_details"]
    assert "Preços e IVA" in dataset["pricing_details"]
    assert "Ingredientes" in dataset["ingredients"]
    assert "Totais" in dataset["totals"]
    assert dataset["product_image_filename"] == str(placeholder)
    assert dataset["product_image_path"] == str(placeholder)
    assert dataset["product_image_uri"] == placeholder.as_uri()
    assert dataset["Produtos_Codigo"] == "RB-01"
    assert dataset["Produtos_PCU"] == pytest.approx(12.5)
    assert dataset["Produtos_Descontinuado"] == "2024-05-01"
    assert dataset["FichasTecnicas_ComponenteNome"] == "Ingrediente A"
    assert dataset["FichasTecnicas_Peso"] == pytest.approx(1.25)
    assert dataset["PrecosTaxas_Preco1"] == pytest.approx(10.0)
    assert dataset["PrecosTaxas_Preco2"] == pytest.approx(15.5)
    assert dataset["PrecosTaxas_Preco1_display"] == "10,00 €"
    assert dataset["PrecosTaxas_Preco2_display"] == "15,50 €"
    assert dataset["TiposArtigos_Cod"] == 2
    assert dataset["TiposArtigos_Descricao"] == "Produto acabado"
    assert dataset["Validade_Cod"] == 5
    assert dataset["Validade_Descricao"] == "72 horas"
    assert dataset["Temperaturas_Cod"] == 3
    assert dataset["Temperaturas_Descricao"] == "Frio"
    assert dataset["ProdutoPreparacao_ProdutoCodigo"] == "RB-01"
    assert dataset["ProdutoPreparacao_Html"] == "<p>Preparar e servir.</p>"
    assert dataset[STATIC_SECTION_PARAMETER] == [{}]

    pricing_rows = dataset["pricing_rows"]
    assert pricing_rows[0]["pvp"] == "10,00 €"
    assert pricing_rows[1]["pvp"] == "15,50 €"

    ingredientes = dataset["ingredientes"]
    assert isinstance(ingredientes, list)
    assert len(ingredientes) == 3

    first, second, third = ingredientes
    assert first["FichasTecnicas_ComponenteNome"] == "Ingrediente A"
    assert first["FichasTecnicas_Qtd"] == pytest.approx(1.25)
    assert first["FichasTecnicas_Unidade"] == "kg"
    assert first["FichasTecnicas_Ppu"] == pytest.approx(2.5)
    assert first["FichasTecnicas_Preco"] == pytest.approx(3.125)
    assert first["FichasTecnicas_Peso"] == pytest.approx(1.25)

    assert second["FichasTecnicas_ComponenteNome"] == "Ingrediente B"
    assert second["FichasTecnicas_Qtd"] == pytest.approx(0.5)
    assert second["FichasTecnicas_Unidade"] == "L"
    assert second["FichasTecnicas_Ppu"] == pytest.approx(1.2)
    assert second["FichasTecnicas_Preco"] == pytest.approx(0.6)
    assert second["FichasTecnicas_Peso"] == pytest.approx(0.5)

    assert third["FichasTecnicas_ComponenteNome"] == "Ingrediente Localizado"
    assert third["FichasTecnicas_Qtd"] == pytest.approx(0.25)
    assert third["FichasTecnicas_Unidade"] == "kg"
    assert third["FichasTecnicas_Ppu"] == pytest.approx(1.5)
    assert third["FichasTecnicas_Preco"] == pytest.approx(1.5)
    assert third["FichasTecnicas_Peso"] == pytest.approx(0.25)


def test_build_reportbro_context_uses_empty_field_for_missing_values():
    product = _sample_product()
    product.tipo_artigo_cod = None
    product.validade_cod = None
    product.temperatura_cod = None
    product.tipos_artigos_row = {}
    product.validade_row = {}
    product.temperaturas_row = {}
    product.produtos_row["tipoartigo"] = None
    product.produtos_row["validade"] = None
    product.produtos_row["temperatura"] = None

    payload = _prepare_management_payload(product)

    block_b1 = payload["blocks"]["B1"]
    block_b1["codigo"] = ""
    block_b1["nome"] = None

    block_b3 = payload["blocks"]["B3"]
    block_b3["iva"] = 0
    block_b3["pvps"] = [0]
    block_b3["food_cost"] = [0]

    block_b2 = payload["blocks"]["B2"]
    block_b2["ingredientes"] = [
        {
            "nome": "",
            "codigo": "",
            "quantidade": 0,
            "unidade": "",
            "ppu": 0,
            "total": 0,
            "peso": 0,
            "ordem": 0,
        }
    ]
    block_b2["totais"] = {
        "custo_total": 0,
        "peso_total": 0,
        "num_ingredientes": 0,
    }

    payload["generated_at"] = ""

    dataset = build_reportbro_context(payload)

    assert dataset["TiposArtigos_Cod"] == 0
    assert dataset["Validade_Cod"] == 0
    assert dataset["Temperaturas_Cod"] == 0
    assert dataset["product_tipo_artigo_cod"] == EMPTY_FIELD
    assert dataset["product_validade_cod"] == EMPTY_FIELD
    assert dataset["product_temperatura_cod"] == EMPTY_FIELD
    assert dataset["pricing_rows"][0]["pvp"] == EMPTY_FIELD
    assert dataset["pricing_rows"][0]["food_cost"] == EMPTY_FIELD
    assert dataset["PrecosTaxas_Preco1"] == pytest.approx(0.0)
    assert dataset["PrecosTaxas_Preco1_display"] == EMPTY_FIELD
    assert dataset["pricing_iva"] == EMPTY_FIELD
    assert EMPTY_FIELD in dataset["pricing_lines"]
    assert dataset["ingredients_data"][0]["quantidade"] == EMPTY_FIELD
    assert dataset["ingredients_data"][0]["ppu"] == EMPTY_FIELD
    assert dataset["ingredients_data"][0]["total"] == EMPTY_FIELD
    assert dataset["ingredients_data"][0]["peso"] == EMPTY_FIELD
    assert EMPTY_FIELD in dataset["ingredients_lines"]
    assert dataset["totals_custo_total"] == EMPTY_FIELD
    assert dataset["totals_peso_total"] == EMPTY_FIELD
    assert dataset["totals_num_ingredientes"] == EMPTY_FIELD
    assert EMPTY_FIELD in dataset["totals_lines"]


def test_build_reportbro_context_includes_product_image_filename(tmp_path):
    product = _sample_product()
    product.code = "RB-IMG"
    product.produtos_row["codigo"] = product.code
    product.precos_taxas_row["codigo"] = product.code
    product.fichas_tecnicas_rows[0]["produtocodigo"] = product.code
    product.produto_preparacao_row["produtocodigo"] = product.code

    root = get_project_root()
    image_path = root / "databases" / "images" / f"{product.code}.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)

    fallback_image = root / "ui" / "no-image-thumb.png"
    image_bytes = fallback_image.read_bytes()
    image_path.write_bytes(image_bytes)

    try:
        payload = _prepare_management_payload(product)
        dataset = build_reportbro_context(payload)

        assert dataset["product_image_filename"] == str(image_path)
        assert dataset["product_image_path"] == str(image_path)
        assert dataset["product_image_uri"] == image_path.as_uri()
        assert payload["product_image_uri"] == image_path.as_uri()
    finally:
        if image_path.exists():
            image_path.unlink()


def test_reportbro_pdf_generation_ignores_missing_image(monkeypatch, tmp_path):
    product = _sample_product()
    root = get_project_root()
    image_path = root / "databases" / "images" / f"{product.code}.png"
    if image_path.exists():
        image_path.unlink()

    from reporting import reportbro_export

    captured: dict[str, Any] = {}

    class GuardedReport:
        def __init__(self, template: Any, data: Mapping[str, Any]):
            self.template = template
            self.data = dict(data)
            self.errors: list[Any] = []

        def generate_pdf(self) -> bytes:
            filename = self.data.get("product_image_filename")
            if filename == "":
                raise RuntimeError("empty filename should not be used")
            captured["dataset"] = dict(self.data)
            return b"%PDF-1.4\n%guarded\n"

    monkeypatch.setattr(reportbro_export, "Report", GuardedReport)

    destination = tmp_path / "gestao_reportbro_missing_image.pdf"
    result = generate_ft_gestao_reportbro_pdf(
        product,
        destination=destination,
    )

    assert destination.exists()
    assert result == destination
    assert "dataset" in captured
    placeholder = _placeholder_image_path()
    expected_uri = placeholder.as_uri()
    assert "product_image_filename" in captured["dataset"]
    assert "product_image_uri" in captured["dataset"]
    assert captured["dataset"].get("product_image_filename") == str(placeholder)
    assert captured["dataset"].get("product_image_uri") == expected_uri


def test_reportbro_pdf_generation(tmp_path):
    product = _sample_product()
    root = get_project_root()
    image_path = root / "databases" / "images" / f"{product.code}.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    fallback_image = root / "ui" / "no-image-thumb.png"
    image_path.write_bytes(fallback_image.read_bytes())

    try:
        payload = _prepare_management_payload(product)
        dataset = build_reportbro_context(payload)

        template = load_template_definition(Path("reporting/templates/ft_gestao_00_base.json"))
        destination = tmp_path / "gestao_reportbro.pdf"

        render_pdf_to_path(template, dataset, destination)

        assert destination.exists()
        assert dataset["product_image_uri"] == image_path.as_uri()
        streams = _extract_pdf_streams(destination)
        combined = "\n".join(streams)
        text_content = "".join(re.findall(r"\(([^)]*)\)", combined))
        assert "CÓDIGO" in text_content
        assert "NOME:" in text_content
    finally:
        if image_path.exists():
            image_path.unlink()


def test_render_pdf_bytes_converts_small_point_margins(monkeypatch):
    from reporting import reportbro_export

    captured: dict[str, Any] = {}

    class RecordingReport:
        def __init__(self, template: Mapping[str, Any], data: Mapping[str, Any], **kwargs: Any):
            captured["template"] = deepcopy(template)
            captured["data"] = dict(data)
            captured["debug"] = kwargs.get("debug")
            self.template = template
            self.data = data
            self.errors: list[Any] = []

        def generate_pdf(self) -> bytes:
            return b"%PDF-1.4\n%recording\n"

    fallback_called = False

    def _fake_fallback(data: Mapping[str, Any]) -> bytes:
        nonlocal fallback_called
        fallback_called = True
        return b"%PDF-1.4\n%fallback\n"

    monkeypatch.setattr(reportbro_export, "Report", RecordingReport)
    monkeypatch.setattr(reportbro_export, "_render_fallback_pdf", _fake_fallback)

    template = {
        "documentProperties": {
            "unit": "mm",
            "marginLeft": 20,
            "marginRight": 20,
            "marginTop": 20,
            "marginBottom": 20,
            "headerSize": 20,
            "footerSize": 20,
            "pageWidth": 595,
            "pageHeight": 842,
        },
        "docElements": [
            {
                "elementType": "frame",
                "id": "Content",
                "width": 400,
                "height": 600,
            },
            {
                "elementType": "text",
                "styleId": "Body",
                "contentData": {
                    "height": 620,
                },
                "height": 620,
            },
        ],
        "parameters": [],
        "styles": [],
    }

    result = render_pdf_bytes(template, {"title": "Ficha"})

    assert result.startswith(b"%PDF-1.4")
    assert fallback_called is False
    properties = captured["template"]["documentProperties"]
    assert properties["marginLeft"] == 20
    assert properties["marginRight"] == 20
    assert properties["marginTop"] == 20
    assert properties["marginBottom"] == 20
    assert properties["headerSize"] == 20
    assert properties["footerSize"] == 20
    assert properties["pageWidth"] == 595
    assert properties["pageHeight"] == 842

    elements = captured["template"]["docElements"]
    assert elements[0]["height"] == 600
    assert elements[1]["height"] == 620


def test_render_pdf_bytes_handles_many_ingredients_without_fallback(monkeypatch):
    from reporting import reportbro_export

    fallback_called = False

    def _fake_fallback(data: Mapping[str, Any]) -> bytes:
        nonlocal fallback_called
        fallback_called = True
        return b"%PDF-1.4\n%fallback\n"

    monkeypatch.setattr(reportbro_export, "_render_fallback_pdf", _fake_fallback)

    product = _sample_product()

    base_order = len(product.fichas_tecnicas_rows)
    for index in range(24):
        ingredient = Ingredient(
            name=f"Ingrediente Extra {index:02d}",
            quantity=1.0 + index / 10.0,
            unit="kg",
            ppu=2.0 + index / 2.0,
            total=2.5 + index / 2.0,
            code=f"IE-{index:02d}",
            weight=0.5 + index / 10.0,
        )
        product.ingredients.append(ingredient)
        product.fichas_tecnicas_rows.append(
            {
                "familiasubfamilia": "Família>Sub",
                "produtocodigo": product.code,
                "produtonome": product.name,
                "componentecodigo": ingredient.code,
                "componentenome": ingredient.name,
                "qtd": ingredient.quantity,
                "unidade": ingredient.unit,
                "ppu": ingredient.ppu,
                "preco": ingredient.total,
                "peso": ingredient.weight,
                "ordem": base_order + index + 1,
            }
        )

    payload = _prepare_management_payload(product)
    dataset = build_reportbro_context(payload)

    assert len(dataset["ingredientes"]) == len(product.ingredients)

    template = load_template_definition(Path("reporting/templates/ft_gestao_00_base.json"))

    pdf_bytes = render_pdf_bytes(template, dataset)

    assert pdf_bytes.startswith(b"%PDF-")
    assert fallback_called is False


def test_generate_ft_gestao_reportbro_pdf_enables_debug(monkeypatch, tmp_path):
    from reporting import reportbro_export

    monkeypatch.setenv("FTV_REPORTBRO_DEBUG", "1")

    captured: dict[str, Any] = {}

    class DebugAwareReport:
        def __init__(self, template: Any, data: Mapping[str, Any], **kwargs: Any):
            self.template = template
            self.data = dict(data)
            self.errors: list[Any] = []
            captured["debug"] = kwargs.get("debug")

        def generate_pdf(self) -> bytes:
            return b"%PDF-1.4\n%debug\n"

    monkeypatch.setattr(reportbro_export, "Report", DebugAwareReport)

    product = _sample_product()
    destination = tmp_path / "gestao_reportbro_debug.pdf"
    template_path = Path("app/templates_store/templates/ft_gestao_00_base.json")

    result = generate_ft_gestao_reportbro_pdf(
        product,
        template_path=template_path,
        destination=destination,
    )

    assert destination.exists()
    assert result == destination
    assert captured.get("debug") is True


def test_fallback_renderers_use_empty_field(tmp_path):
    data = {
        "product_codigo": "",
        "product_nome": None,
        "ingredientes": [
            {
                "FichasTecnicas_ComponenteNome": "",
                "FichasTecnicas_Qtd": 0,
                "FichasTecnicas_Unidade": "",
            }
        ],
        "totals_data": {"custo_total": 0},
    }

    export_bytes = export_render_fallback_pdf(data)
    export_path = tmp_path / "export_fallback.pdf"
    export_path.write_bytes(export_bytes)
    export_text = "\n".join(_extract_pdf_streams(export_path))
    assert EMPTY_FIELD in export_text
    assert "—" not in export_text

    service_bytes = service_render_fallback_pdf(data)
    service_path = tmp_path / "service_fallback.pdf"
    service_path.write_bytes(service_bytes)
    service_text = "\n".join(_extract_pdf_streams(service_path))
    assert EMPTY_FIELD in service_text
    assert "—" not in service_text


def test_reportbro_template_without_image_element(tmp_path, caplog):
    product = _sample_product()
    product.code = "RB-TEMPLATE"
    product.produtos_row["codigo"] = product.code
    product.precos_taxas_row["codigo"] = product.code
    product.fichas_tecnicas_rows[0]["produtocodigo"] = product.code
    product.produto_preparacao_row["produtocodigo"] = product.code

    root = get_project_root()
    image_path = root / "databases" / "images" / f"{product.code}.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    fallback_image = root / "ui" / "no-image-thumb.png"
    image_path.write_bytes(fallback_image.read_bytes())

    template_path = Path("app/templates_store/templates/ft_gestao_00_base.json")
    template = json.loads(template_path.read_text())
    template["docElements"] = [
        element
        for element in template.get("docElements", [])
        if not (
            isinstance(element, dict)
            and element.get("elementType") == "image"
            and element.get("imageFilename", "").strip() == "${product_image_filename}"
        )
    ]

    stripped_template_path = tmp_path / "ft_gestao_no_image.json"
    stripped_template_path.write_text(json.dumps(template))

    destination = tmp_path / "gestao_no_image.pdf"
    caplog.set_level(logging.WARNING, logger="ui.printing")

    try:
        result = generate_ft_gestao_reportbro_pdf(
            product,
            template_path=stripped_template_path,
            destination=destination,
        )

        assert destination.exists()
        assert result == destination
        warning_messages = [
            record.getMessage() for record in caplog.records if record.levelno == logging.WARNING
        ]
        assert not any(
            "Imagem de produto inexistente" in message
            or "Produtos_Codigo em falta" in message
            for message in warning_messages
        )
    finally:
        if image_path.exists():
            image_path.unlink()


def test_reportbro_pdf_generation_with_extra_template_parameter(tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    product = _sample_product()
    root = get_project_root()
    image_path = root / "databases" / "images" / f"{product.code}.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    fallback_image = root / "ui" / "no-image-thumb.png"
    image_path.write_bytes(fallback_image.read_bytes())

    template_path = Path("app/templates_store/templates/ft_gestao_00_base.json")
    template = json.loads(template_path.read_text())
    extra_parameter = dict(template["parameters"][0])
    extra_parameter["name"] = "Extra_Parameter"
    template["parameters"].append(extra_parameter)

    custom_template_path = tmp_path / "ft_gestao_extra_parameter.json"
    custom_template_path.write_text(json.dumps(template))

    destination = tmp_path / "gestao_reportbro_extra.pdf"
    try:
        result = generate_ft_gestao_reportbro_pdf(
            product,
            template_path=custom_template_path,
            destination=destination,
        )

        assert destination.exists()
        assert result == destination
        warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
        assert any("Extra_Parameter" in record.getMessage() for record in warnings)
    finally:
        if image_path.exists():
            image_path.unlink()


def test_load_template_definition_normalises_ft_gestao_template():
    template_path = Path("app/templates_store/templates/ft_gestao_00_base.json")
    template = load_template_definition(template_path)

    assert all(isinstance(style.get("id"), str) for style in template.get("styles", []))

    text_elements = [
        element
        for element in template.get("docElements", [])
        if isinstance(element, dict) and element.get("elementType") == "text"
    ]
    assert text_elements, "expected at least one text element"
    for element in text_elements:
        assert isinstance(element.get("styleId", ""), str)
        assert isinstance(element.get("printIf", ""), str)
        assert element.get("richTextContent", "") == ""
        assert isinstance(element.get("richTextHtml", ""), str)

    image_elements = [
        element
        for element in template.get("docElements", [])
        if isinstance(element, dict) and element.get("elementType") == "image"
    ]
    assert image_elements, "expected at least one image element"
    for element in image_elements:
        assert element.get("source") == "${product_image_uri}"
        assert element.get("imageFilename", "").strip() == "${product_image_filename}"


def test_template_payload_normalisation_discards_extra_metadata():
    raw_template = json.loads(Path("app/templates_store/templates/ft_gestao_00_base.json").read_text())
    raw_template["designerState"] = {"zoom": 125}

    payload = {"template": raw_template, "other": "ignored"}
    template, extras = _normalise_template_payload(payload)

    assert "designerState" not in template
    assert extras == {"designerState": {"zoom": 125}}
    assert all(isinstance(style.get("id"), str) for style in template.get("styles", []))
    assert all(
        isinstance(element.get("styleId", ""), str)
        for element in template.get("docElements", [])
        if isinstance(element, dict)
    )


def test_resolve_reportbro_template_prefers_runtime(tmp_path, monkeypatch):
    from ui import printing

    runtime = tmp_path / "runtime" / printing._DEFAULT_REPORTBRO_TEMPLATE_NAME
    runtime.parent.mkdir(parents=True)
    runtime.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(printing, "_DEFAULT_REPORTBRO_TEMPLATE", runtime)
    monkeypatch.setattr(printing, "_REPORTBRO_STORE_TEMPLATE_DIR", tmp_path / "store")

    resolved = printing._resolve_reportbro_template_location(None)

    assert resolved == runtime


def test_resolve_reportbro_template_falls_back_to_store(tmp_path, monkeypatch):
    from ui import printing

    runtime = tmp_path / "runtime" / printing._DEFAULT_REPORTBRO_TEMPLATE_NAME
    store_dir = tmp_path / "store"
    store = store_dir / printing._DEFAULT_REPORTBRO_TEMPLATE_NAME
    store_dir.mkdir(parents=True)
    store.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(printing, "_DEFAULT_REPORTBRO_TEMPLATE", runtime)
    monkeypatch.setattr(printing, "_REPORTBRO_STORE_TEMPLATE_DIR", store_dir)

    resolved = printing._resolve_reportbro_template_location(None)

    assert resolved == store


def test_resolve_reportbro_template_missing_raises_friendly(tmp_path, monkeypatch):
    from ui import printing

    runtime = tmp_path / "runtime" / printing._DEFAULT_REPORTBRO_TEMPLATE_NAME
    store_dir = tmp_path / "store"

    monkeypatch.setattr(printing, "_DEFAULT_REPORTBRO_TEMPLATE", runtime)
    monkeypatch.setattr(printing, "_REPORTBRO_STORE_TEMPLATE_DIR", store_dir)

    with pytest.raises(FileNotFoundError) as exc:
        printing._resolve_reportbro_template_location(None)

    message = str(exc.value)
    assert "Não foi possível localizar o template ReportBro" in message
    assert printing._DEFAULT_REPORTBRO_TEMPLATE_NAME in message
