from __future__ import annotations

import zlib
import re
from pathlib import Path

import pytest

from tests._qt import require_real_qt_modules

from domain.models import Ingredient, Product
from services.products import get_image_path
from ui.printing import _configure_printer, _prepare_management_payload, _render_pdf


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


def _rect_widths(stream: str) -> list[float]:
    pattern = re.compile(r"-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?\s+(-?\d+(?:\.\d+)?)\s+-?\d+(?:\.\d+)?\s+re")
    widths: list[float] = []
    for match in pattern.finditer(stream):
        widths.append(float(match.group(1)))
    return widths


def test_management_pdf_contains_brand_elements(qapp, tmp_path):
    require_real_qt_modules(
        "PyQt5.QtWidgets", "PyQt5.QtGui", "PyQt5.QtPrintSupport"
    )
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


def test_qt_pdf_block_width_matches_printable_area(qapp, tmp_path):
    modules = require_real_qt_modules(
        "PyQt5.QtWidgets", "PyQt5.QtGui", "PyQt5.QtPrintSupport"
    )
    if not modules:
        pytest.skip("Real Qt modules are required")

    from PyQt5.QtPrintSupport import QPrinter

    product = Product(
        code="P010",
        name="Produto Largura",
        familia="Família",
        subfamilia="Sub",
        informacao_adicional="Notas",
        tipo_artigo_cod=2,
        validade_cod=5,
        temperatura_cod=3,
        pvps=[12.5],
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
            )
        ],
    )

    payload = _prepare_management_payload(product)
    pdf_path = tmp_path / "ft_gestao_width.pdf"
    printer = _configure_printer(pdf_path, (595.28, 841.89))
    printable_width = printer.pageRect(QPrinter.Point).width()
    del printer

    _render_pdf(payload, pdf_path, (595.28, 841.89))

    streams = _extract_pdf_streams(pdf_path)
    assert streams, "expected at least one PDF stream"

    widths: list[float] = []
    for stream in streams:
        widths.extend(_rect_widths(stream))

    assert widths, "expected at least one rectangle command"
    widest = max(widths)
    assert widest == pytest.approx(printable_width, abs=0.6)


def test_qt_pdf_font_sizes_respect_scale(qapp, tmp_path):
    modules = require_real_qt_modules(
        "PyQt5.QtWidgets", "PyQt5.QtGui", "PyQt5.QtPrintSupport"
    )
    if not modules:
        pytest.skip("Real Qt modules are required")

    from PyQt5.QtPrintSupport import QPrinter

    product = Product(
        code="P020",
        name="Produto Fontes",
        familia="Família",
        subfamilia="Sub",
        informacao_adicional="Notas",
        tipo_artigo_cod=2,
        validade_cod=5,
        temperatura_cod=3,
        pvps=[9.5],
        iva=23,
        ingredients=[
            Ingredient(
                name="Ingrediente Único",
                quantity=2.0,
                unit="kg",
                ppu=3.0,
                total=6.0,
                code="I900",
                weight=2.0,
            )
        ],
    )

    payload = _prepare_management_payload(product)
    pdf_path = tmp_path / "ft_gestao_fonts.pdf"

    printer = _configure_printer(pdf_path, (595.28, 841.89))
    page_rect_points = printer.pageRect(QPrinter.Point)
    page_rect_pixels = printer.pageRect(QPrinter.DevicePixel)
    del printer

    if not page_rect_points.height():
        pytest.skip("Printer did not report a point-based page height")

    scale_y = page_rect_pixels.height() / page_rect_points.height()

    _render_pdf(payload, pdf_path, (595.28, 841.89))

    streams = _extract_pdf_streams(pdf_path)
    assert streams, "expected at least one PDF stream"

    font_pattern = re.compile(r"(\d+(?:\.\d+)?)\s+Tf")
    font_sizes: list[float] = []
    for stream in streams:
        font_sizes.extend(float(match.group(1)) for match in font_pattern.finditer(stream))

    assert font_sizes, "expected to extract font sizes from PDF"

    expected_point_sizes = [22.0, 16.0, 12.0, 10.0, 9.0]
    for expected in expected_point_sizes:
        target = expected / scale_y
        assert any(abs(size - target) <= 0.1 for size in font_sizes), (
            f"missing scaled font size for {expected}pt (expected around {target})"
        )


def test_qt_pdf_embeds_product_image(qapp, tmp_path):
    modules = require_real_qt_modules(
        "PyQt5.QtWidgets", "PyQt5.QtGui", "PyQt5.QtPrintSupport"
    )
    if not modules:
        pytest.skip("Real Qt modules are required")

    from PyQt5.QtGui import QImage

    codigo = "PDF_IMG_TEST"
    image_path = get_image_path(codigo)
    try:
        img = QImage(48, 48, QImage.Format_ARGB32)
        img.fill(0xFF336699)
        img.save(str(image_path))

        product = Product(
            code=codigo,
            name="Produto com Imagem",
            familia="Família",
            subfamilia="Sub",
            informacao_adicional="Notas",
            tipo_artigo_cod=2,
            validade_cod=5,
            temperatura_cod=3,
            pvps=[9.5],
            iva=23,
            ingredients=[
                Ingredient(
                    name="Ingrediente Único",
                    quantity=1.0,
                    unit="kg",
                    ppu=3.5,
                    total=3.5,
                    code="I900",
                    weight=1.0,
                )
            ],
        )

        payload = _prepare_management_payload(product)
        pdf_path = tmp_path / "ft_gestao_image.pdf"
        _render_pdf(payload, pdf_path, (595.28, 841.89))

        assert pdf_path.exists()
        pdf_bytes = pdf_path.read_bytes()
        assert b"/Subtype /Image" in pdf_bytes

        streams = _extract_pdf_streams(pdf_path)
        assert streams, "expected at least one PDF stream"
        combined = "\n".join(streams)
        assert re.search(r"/Im\d+\s+Do", combined), "expected an image draw command"
    finally:
        if image_path.exists():
            image_path.unlink()


def test_basic_pdf_preserves_unicode(tmp_path, monkeypatch):
    from ui import printing as printing_mod

    product = Product(
        code="P002",
        name="Bolo de Maçã",
        familia="Sobremesas",
        subfamilia="Bolos",
        informacao_adicional="Feito com maçã e canela",
        tipo_artigo_cod=2,
        validade_cod=5,
        temperatura_cod=3,
        pvps=[12.5],
        iva=23,
        ingredients=[
            Ingredient(
                name="Maçã",
                quantity=1.0,
                unit="kg",
                ppu=2.0,
                total=2.0,
                code="I003",
                weight=1.0,
            ),
        ],
    )

    payload = _prepare_management_payload(product)
    pdf_path = tmp_path / "ft_gestao_unicode.pdf"
    monkeypatch.setattr(printing_mod, "_USE_BASIC_PDF", True)
    _render_pdf(payload, pdf_path, (595.28, 841.89))

    content = pdf_path.read_bytes().decode("utf-8")
    assert "Bolo de Maçã" in content
    assert "Feito com maçã e canela" in content
    assert '"name": "Bolo de Maçã"' in content or '"nome": "Bolo de Maçã"' in content
