from __future__ import annotations

from pathlib import Path

from domain.models import Ingredient, Product
from reporting.ft_gestao import build_reportbro_context
from reporting.reportbro_export import load_template_definition, render_pdf_to_path
from ui.printing import _prepare_management_payload


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
    assert "Ingredientes" in combined
