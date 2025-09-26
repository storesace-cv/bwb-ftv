from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path

import pytest
from app.server.routes_reportbro import _normalise_template_payload
from domain.models import Ingredient, Product
from reporting.ft_gestao import build_reportbro_context
from reporting.reportbro_export import load_template_definition, render_pdf_to_path
from services.products import get_image_path
from ui.printing import _prepare_management_payload
from utils.paths import get_project_root


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
    dataset = build_reportbro_context(payload)

    assert dataset["title"] == "Ficha Técnica de Gestão"
    assert "Produto" in dataset["product_details"]
    assert "Preços e IVA" in dataset["pricing_details"]
    assert "Ingredientes" in dataset["ingredients"]
    assert "Totais" in dataset["totals"]
    assert isinstance(dataset["product_image"], (str, type(None)))
    assert dataset["Produtos_Codigo"] == "RB-01"
    assert dataset["Produtos_PCU"] == pytest.approx(12.5)
    assert dataset["Produtos_Descontinuado"] == "2024-05-01"
    assert dataset["FichasTecnicas_ComponenteNome"] == "Ingrediente A"
    assert dataset["PrecosTaxas_Preco1"] == pytest.approx(10.0)


def test_build_reportbro_context_embeds_product_image(tmp_path):
    product = _sample_product()
    product.code = "RB-IMG"

    image_path = get_image_path(product.code)
    image_path.parent.mkdir(parents=True, exist_ok=True)

    fallback_image = get_project_root() / "ui" / "no-image-thumb.png"
    image_bytes = fallback_image.read_bytes()
    image_path.write_bytes(image_bytes)

    try:
        payload = _prepare_management_payload(product)
        dataset = build_reportbro_context(payload)

        assert isinstance(dataset["product_image"], str)
        prefix, encoded = dataset["product_image"].split(",", 1)
        assert prefix.startswith("data:image/")
        decoded = base64.b64decode(encoded)
        assert decoded == image_bytes
        assert dataset["product_image_path"] == str(image_path)
    finally:
        if image_path.exists():
            image_path.unlink()


def test_reportbro_pdf_generation(tmp_path):
    payload = _prepare_management_payload(_sample_product())
    dataset = build_reportbro_context(payload)

    template = load_template_definition(Path("reporting/templates/ft_gestao_reportbro.json"))
    destination = tmp_path / "gestao_reportbro.pdf"

    render_pdf_to_path(template, dataset, destination)

    assert destination.exists()
    streams = _extract_pdf_streams(destination)
    combined = "\n".join(streams)
    assert "Ficha Técnica de Gestão" in combined
    assert "ingredientes" in combined.lower()


def test_load_template_definition_normalises_ft_gestao_template():
    template_path = Path("app/templates_store/templates/ft_gestao_02.json")
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


def test_template_payload_normalisation_discards_extra_metadata():
    raw_template = json.loads(Path("app/templates_store/templates/ft_gestao_02.json").read_text())
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
