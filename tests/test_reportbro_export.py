from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import pytest
from app.server.routes_reportbro import _normalise_template_payload
from domain.models import Ingredient, Product
from reporting.ft_gestao import build_reportbro_context
from reporting.reportbro_export import load_template_definition, render_pdf_to_path
from reporting.reportbro_normalizer import STATIC_SECTION_PARAMETER
from ui.printing import _prepare_management_payload, generate_ft_gestao_reportbro_pdf
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
    assert dataset["product_image_filename"] == ""
    assert dataset["Produtos_Codigo"] == "RB-01"
    assert dataset["Produtos_PCU"] == pytest.approx(12.5)
    assert dataset["Produtos_Descontinuado"] == "2024-05-01"
    assert dataset["FichasTecnicas_ComponenteNome"] == "Ingrediente A"
    assert dataset["PrecosTaxas_Preco1"] == pytest.approx(10.0)
    assert dataset[STATIC_SECTION_PARAMETER] == [{}]


def test_build_reportbro_context_includes_product_image_filename(tmp_path):
    product = _sample_product()
    product.code = "RB-IMG"
    product.produtos_row["codigo"] = product.code
    product.precos_taxas_row["codigo"] = product.code
    product.fichas_tecnicas_rows[0]["produtocodigo"] = product.code

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
    finally:
        if image_path.exists():
            image_path.unlink()


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

        template = load_template_definition(Path("reporting/templates/ft_gestao_02.json"))
        destination = tmp_path / "gestao_reportbro.pdf"

        render_pdf_to_path(template, dataset, destination)

        assert destination.exists()
        streams = _extract_pdf_streams(destination)
        combined = "\n".join(streams)
        assert "CÓDIGO" in combined
        assert "NOME:" in combined
    finally:
        if image_path.exists():
            image_path.unlink()


def test_reportbro_template_without_image_element(tmp_path, caplog):
    product = _sample_product()
    product.code = "RB-TEMPLATE"
    product.produtos_row["codigo"] = product.code
    product.precos_taxas_row["codigo"] = product.code
    product.fichas_tecnicas_rows[0]["produtocodigo"] = product.code

    root = get_project_root()
    image_path = root / "databases" / "images" / f"{product.code}.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    fallback_image = root / "ui" / "no-image-thumb.png"
    image_path.write_bytes(fallback_image.read_bytes())

    template_path = Path("app/templates_store/templates/ft_gestao_02.json")
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

    template_path = Path("app/templates_store/templates/ft_gestao_02.json")
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
