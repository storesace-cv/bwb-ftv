from __future__ import annotations

import zlib
from pathlib import Path

from tests._qt import require_real_qt_modules

require_real_qt_modules("PyQt5.QtWidgets", "PyQt5.QtGui", "PyQt5.QtPrintSupport")

from domain.models import Ingredient, Product
from ui.printing import _prepare_management_payload, _render_pdf


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
            decoded = zlib.decompress(chunk)
        except zlib.error:
            decoded = chunk
        streams.append(decoded.decode("latin-1", "ignore"))
        start = end + len("endstream")
    return streams


def test_management_pdf_contains_brand_elements(qapp, tmp_path):
    product = Product(
        code="P001",
        name="Produto Teste",
        familia="Família",
        subfamilia="Sub",
        informacao_adicional="Notas",
        tipo_artigo_cod=2,
        validade_cod=5,
        temperatura_cod=3,
        pvps=[12.5, 15.0],
        iva=23,
        ingredients=[
            Ingredient(
                name="Ingrediente A",
                quantity=1.5,
                unit="kg",
                ppu=2.5,
                total=3.75,
                code="I001",
                weight=1.5,
            ),
            Ingredient(
                name="Ingrediente B",
                quantity=0.75,
                unit="kg",
                ppu=4.0,
                total=3.0,
                code="I002",
                weight=0.5,
            ),
        ],
    )

    payload = _prepare_management_payload(product)
    pdf_path = tmp_path / "ft_gestao.pdf"
    _render_pdf(payload, pdf_path, (595.28, 841.89))

    assert pdf_path.exists()
    streams = _extract_pdf_streams(pdf_path)
    assert streams, "expected at least one PDF stream"
    combined = "\n".join(streams)

    assert "0.145098039 0.219607843 0.345098039 scn" in combined
    assert "0.933333333 0.960784313 1 scn" in combined
    assert "0.290196078 0.435294117 0.647058823 scn" in combined
    assert combined.count(" re") >= 6
