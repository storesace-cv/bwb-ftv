from __future__ import annotations

from pathlib import Path

import base64

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
    return Product(
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


def test_build_reportbro_context_formats_sections():
    payload = _prepare_management_payload(_sample_product())
    dataset = build_reportbro_context(payload)

    assert dataset["title"] == "Ficha Técnica de Gestão"
    assert "Produto" in dataset["product_details"]
    assert "Preços e IVA" in dataset["pricing_details"]
    assert "Ingredientes" in dataset["ingredients"]
    assert "Totais" in dataset["totals"]
    assert isinstance(dataset["product_image"], (str, type(None)))


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

    template = load_template_definition(
        Path("app/templates_store/templates/ft_gestao_reportbro.json")
    )
    destination = tmp_path / "gestao_reportbro.pdf"

    render_pdf_to_path(template, dataset, destination)

    assert destination.exists()
    streams = _extract_pdf_streams(destination)
    combined = "\n".join(streams)
    assert "FICHA DE ARTIGO" in combined
    assert "Produto ReportBro" in combined
    assert "ingredientes" in combined.lower()
