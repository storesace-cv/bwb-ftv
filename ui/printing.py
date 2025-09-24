"""Helpers related to printing/exporting UI artefacts."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterable as IterableABC
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

try:  # pragma: no cover - import guard depends on environment
    from PyQt5.QtCore import QRectF, QSizeF, Qt
    from PyQt5.QtGui import QColor, QFont, QFontMetricsF, QImage, QPainter, QPen, QPixmap
    from PyQt5.QtPrintSupport import QPrinter
    from PyQt5.QtWidgets import QFileDialog, QWidget
except ImportError:  # pragma: no cover - executed when stubs are active
    QRectF = QSizeF = Qt = QColor = QFont = QFontMetricsF = QImage = QPainter = QPen = QPixmap = QPrinter = None  # type: ignore[assignment]
    QFileDialog = QWidget = None  # type: ignore[assignment]
    _QT_AVAILABLE = False
else:  # pragma: no cover - exercised in integration tests
    _QT_AVAILABLE = True

_USE_BASIC_PDF = False

from domain.models import Product
from services.products import calculate_food_cost, get_image_path
from utils.formatting import parse_decimal

logger = logging.getLogger(__name__)

_DEFAULT_PAGE_SIZES = {
    "A4": (595.28, 841.89),
    "LETTER": (612.0, 792.0),
}


class ExportCancelled(RuntimeError):
    """Raised when the user cancels the export dialog."""


def generate_ft_gestao_pdf(
    product: Product,
    *,
    page_size: str = "A4",
    parent: QWidget | None = None,
) -> Path | None:
    """Generate the Gestão PDF for the given product on the specified page size.

    Parameters
    ----------
    product:
        Product instance representing the ficha técnica currently selecionada.
    page_size:
        Nome do tamanho da página (``"A4"`` por omissão) usado na renderização.
    parent:
        Widget pai utilizado para apresentar diálogos modais.

    Returns
    -------
    Path | None
        Caminho final para o PDF gerado ou ``None`` quando o utilizador cancela.
    """

    product_obj = _validate_product(product)
    payload = _prepare_management_payload(product_obj)
    try:
        destination = _prompt_pdf_destination(product_obj, parent=parent)
    except ExportCancelled:
        logger.info(
            "[Print] Exportação FT Gestão cancelada para %s",
            payload["identifier"],
        )
        return None

    page_size_key = str(page_size or "").strip().upper() or "A4"
    page_metrics = _DEFAULT_PAGE_SIZES.get(page_size_key, _DEFAULT_PAGE_SIZES["A4"])
    logger.debug(
        "[Print] Exportação FT Gestão preparada para %s em %s (%.2f×%.2f)",
        payload["identifier"],
        page_size_key,
        *page_metrics,
    )
    _render_pdf(payload, destination, page_metrics)
    logger.info(
        "[Print] FT Gestão criada com sucesso em %s",
        destination,
    )
    return destination


def _validate_product(product: Product) -> Product:
    if not isinstance(product, Product):
        raise TypeError("product must be an instance of domain.models.Product")

    identifier = getattr(product, "code", None) or getattr(product, "name", None)
    if not identifier:
        raise ValueError(
            "product must define at least a code or a name for export purposes"
        )

    ingredients = getattr(product, "ingredients", None)
    if ingredients is None:
        product.ingredients = []
    elif not isinstance(ingredients, IterableABC):
        raise TypeError("product.ingredients must be an iterable")
    return product


def _prepare_management_payload(product: Product) -> dict[str, Any]:
    identifier = product.code or product.name or "<desconhecido>"
    generated_at = datetime.now().isoformat(timespec="seconds")

    ingredients = list(getattr(product, "ingredients", []) or [])
    ing_data, totals = _normalise_ingredients(ingredients)
    pvps_raw = list(getattr(product, "pvps", []) or [])
    pvps_serialised = [_serialise_numeric(p) for p in pvps_raw]
    iva_raw = getattr(product, "iva", None)
    iva_serialised = _serialise_numeric(iva_raw)
    pvps_numeric = [_safe_float(p) for p in pvps_raw]
    food_cost = _compute_food_costs(
        totals.get("custo_total"), pvps_numeric, _safe_float(iva_raw), identifier
    )

    fallback_image = Path(__file__).resolve().parent / "no-image-thumb.png"
    image_path = fallback_image
    if product.code:
        candidate = get_image_path(product.code)
        if candidate.exists():
            image_path = candidate

    blocks = {
        "B1": {
            "codigo": product.code,
            "nome": product.name,
            "familia": product.familia,
            "subfamilia": product.subfamilia,
            "informacao_adicional": product.informacao_adicional,
            "tipo_artigo_cod": product.tipo_artigo_cod,
            "validade_cod": product.validade_cod,
            "temperatura_cod": product.temperatura_cod,
            "image_path": str(image_path),
        },
        "B2": {
            "ingredientes": ing_data,
            "totais": totals,
        },
        "B3": {
            "pvps": pvps_serialised,
            "iva": iva_serialised,
            "food_cost": food_cost,
        },
    }

    return {
        "identifier": identifier,
        "generated_at": generated_at,
        "page_title": "Ficha Técnica de Gestão",
        "blocks": blocks,
    }


def _normalise_ingredients(ingredients: Iterable[Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    total_cost = 0.0
    total_weight = 0.0
    have_cost = False
    have_weight = False

    for index, ingredient in enumerate(ingredients, start=1):
        name = getattr(ingredient, "name", None) or getattr(
            ingredient, "ingredient", None
        )
        quantity = _safe_float(getattr(ingredient, "quantity", None))
        unit = getattr(ingredient, "unit", None)
        ppu = _safe_float(getattr(ingredient, "ppu", None))
        total = _safe_float(getattr(ingredient, "total", None))
        code = getattr(ingredient, "code", None)
        weight = _safe_float(getattr(ingredient, "weight", None))

        if total is None and ppu is not None and quantity is not None:
            total = round(ppu * quantity, 4)
        if total is not None:
            have_cost = True
            total_cost += float(total)
        if weight is not None:
            have_weight = True
            total_weight += float(weight)

        entries.append(
            {
                "ordem": index,
                "nome": name,
                "codigo": code,
                "quantidade": quantity,
                "unidade": unit,
                "ppu": ppu,
                "total": total,
                "peso": weight,
            }
        )

    totals = {
        "custo_total": round(total_cost, 4) if have_cost else None,
        "peso_total": round(total_weight, 4) if have_weight else None,
        "num_ingredientes": len(entries),
    }
    return entries, totals


def _compute_food_costs(
    total_cost: float | None,
    pvps: Iterable[Any],
    iva: Any,
    identifier: str,
) -> list[float | None]:
    result: list[float | None] = []
    if total_cost is None:
        return [None for _ in pvps]

    for pvp in pvps:
        pct = calculate_food_cost(total_cost, pvp, iva, identifier)
        if pct is None:
            result.append(None)
        else:
            try:
                pct_float = round(float(pct), 2)
            except (TypeError, ValueError):
                pct_float = None
            result.append(pct_float)
    return result


def _prompt_pdf_destination(product: Product, parent: QWidget | None = None) -> Path:
    if QFileDialog is None:
        raise RuntimeError("PyQt5 QtWidgets is required to export PDFs")
    identifier = product.code or product.name or "ficha_gestao"
    safe_identifier = re.sub(r"[^\w\-]+", "_", identifier).strip("_") or "ficha_gestao"
    suggested = f"{safe_identifier}_ft_gestao.pdf"
    default_path = Path.cwd() / suggested
    filename, _ = QFileDialog.getSaveFileName(
        parent,
        "Exportar Ficha de Gestão",
        str(default_path),
        "Ficheiros PDF (*.pdf)",
    )
    if not filename:
        raise ExportCancelled()
    path = Path(filename)
    if path.suffix.lower() != ".pdf":
        path = path.with_suffix(".pdf")
    return path


def _render_pdf(payload: dict[str, Any], destination: Path, page_metrics: tuple[float, float]) -> None:
    """Render *payload* into a PDF written to *destination* using the configured backend."""

    if _QT_AVAILABLE and not _USE_BASIC_PDF:
        _render_pdf_qt(payload, destination, page_metrics)
        return

    _render_pdf_basic(payload, destination, page_metrics)


def _render_pdf_qt(
    payload: dict[str, Any], destination: Path, page_metrics: tuple[float, float]
) -> None:
    if not _QT_AVAILABLE:
        raise RuntimeError("PyQt5 is required to render PDFs")
    printer = _configure_printer(destination, page_metrics)
    painter = QPainter(printer)
    page_rect_points = printer.pageRect(QPrinter.Point)
    page_rect_pixels = printer.pageRect(QPrinter.DevicePixel)
    scale_x = 1.0
    scale_y = 1.0
    if page_rect_points.width() and page_rect_points.height():
        scale_x = page_rect_pixels.width() / page_rect_points.width()
        scale_y = page_rect_pixels.height() / page_rect_points.height()
    painter.scale(scale_x, scale_y)
    painter.setRenderHint(QPainter.Antialiasing, True)
    try:
        _draw_management_sheet(
            painter,
            printer.pageRect(QPrinter.Point),
            payload,
            scale_x=scale_x,
            scale_y=scale_y,
        )
    finally:
        painter.end()


def _scaled_font(
    point_size: float,
    weight: int | None = None,
    *,
    family: str = "Helvetica",
    scale_y: float = 1.0,
) -> QFont:
    if not _QT_AVAILABLE or QFont is None:  # pragma: no cover - defensive guard
        raise RuntimeError("PyQt5 is required to create scaled fonts")
    font = QFont(family)
    font.setWeight(weight if weight is not None else QFont.Normal)
    effective_size = point_size
    if scale_y:
        effective_size = point_size / scale_y
    font.setPointSizeF(effective_size)
    return font


def _render_pdf_basic(
    payload: dict[str, Any], destination: Path, page_metrics: tuple[float, float]
) -> None:
    lines = list(_build_pdf_lines(payload))
    margin = 36.0
    font_size = 10
    leading = font_size + 4
    _, height = page_metrics
    y_cursor = height - margin
    text_ops: list[str] = []
    for line in lines:
        text_ops.append(
            "BT /F1 {size} Tf {x:.2f} {y:.2f} Td ({text}) Tj ET".format(
                size=font_size,
                x=margin,
                y=y_cursor,
                text=_escape_pdf_text(line),
            )
        )
        y_cursor -= leading
        if y_cursor <= margin:
            break

    content_stream = "\n".join(text_ops)
    payload_json = json.dumps(payload, ensure_ascii=False)

    objects: list[str] = []
    objects.append("1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj")
    objects.append("2 0 obj<< /Type /Pages /Count 1 /Kids [3 0 R] >>endobj")
    objects.append(
        "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] /Resources "
        "<< /Font << /F1 5 0 R >> >> /Contents 4 0 R >>endobj" % page_metrics
    )
    content_bytes = content_stream.encode("utf-8")
    objects.append(
        "4 0 obj<< /Length %d >>stream\n%s\nendstream endobj"
        % (len(content_bytes), content_stream)
    )
    objects.append(
        "5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj"
    )

    header = b"%PDF-1.4\n"
    prefix = f"%FT_GESTAO_PAYLOAD {payload_json}\n".encode("utf-8")

    xref_positions: list[int] = []
    body_parts: list[bytes] = []
    offset = len(header) + len(prefix)
    for obj in objects:
        part = f"{obj}\n".encode("utf-8")
        xref_positions.append(offset)
        body_parts.append(part)
        offset += len(part)

    xref_start = offset
    xref_entries = [b"0000000000 65535 f "]
    for pos in xref_positions:
        xref_entries.append(f"{pos:010} 00000 n ".encode("utf-8"))

    xref_table = b"xref\n0 %d\n%s\n" % (
        len(xref_entries),
        b"\n".join(xref_entries),
    )
    trailer = (
        b"trailer<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF"
        % (len(xref_entries), xref_start)
    )

    pdf_content = b"".join([header, prefix, *body_parts, xref_table, trailer])
    destination.write_bytes(pdf_content)


def _configure_printer(destination: Path, page_metrics: tuple[float, float]) -> QPrinter:
    width_pt, height_pt = page_metrics
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(str(destination))
    printer.setFullPage(True)
    page_width_mm, page_height_mm = _points_to_mm(width_pt, height_pt)
    page_size_mm = QSizeF(page_width_mm, page_height_mm)
    printer.setPaperSize(page_size_mm, QPrinter.Millimeter)
    margin_mm = _points_to_mm(_PAGE_MARGIN)[0]
    printer.setPageMargins(margin_mm, margin_mm, margin_mm, margin_mm, QPrinter.Millimeter)
    printer.setResolution(300)
    printer.setCreator("BWB Fichas Técnicas")
    try:
        printer.setCompressionEnabled(False)
    except AttributeError:  # pragma: no cover - method absent on older bindings
        pass
    return printer


def _draw_management_sheet(
    painter: QPainter,
    rect: QRectF,
    payload: dict[str, Any],
    *,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> None:
    block_spacing = 24.0
    y = rect.top()

    title = f"{payload.get('page_title', 'Ficha Técnica de Gestão')}"
    subtitle = f"{payload.get('identifier', '--')}"
    generated_at = payload.get("generated_at")

    y = _draw_page_header(
        painter,
        rect,
        y,
        title,
        subtitle,
        generated_at,
        scale_y=scale_y,
    )

    blocks = payload.get("blocks", {})
    y += block_spacing
    y = _draw_block_b1(
        painter,
        QRectF(rect.left(), y, rect.width(), 0),
        blocks.get("B1", {}),
        scale_y=scale_y,
    )
    y += block_spacing
    y = _draw_block_b2(
        painter,
        QRectF(rect.left(), y, rect.width(), 0),
        blocks.get("B2", {}),
        scale_y=scale_y,
    )
    y += block_spacing
    _draw_block_b3(
        painter,
        QRectF(rect.left(), y, rect.width(), 0),
        blocks.get("B3", {}),
        scale_y=scale_y,
    )


def _draw_page_header(
    painter: QPainter,
    rect: QRectF,
    y: float,
    title: str,
    subtitle: str,
    generated_at: str | None,
    *,
    scale_y: float = 1.0,
) -> float:
    painter.save()
    header_font = _scaled_font(22, QFont.Bold, scale_y=scale_y)
    painter.setFont(header_font)
    painter.setPen(QColor("#253858"))
    fm_header = QFontMetricsF(header_font)
    header_height = fm_header.lineSpacing()
    header_rect = QRectF(rect.left(), y, rect.width(), header_height)
    painter.drawText(header_rect, Qt.AlignLeft | Qt.AlignVCenter, title)

    subtitle_font = _scaled_font(12, QFont.Bold, scale_y=scale_y)
    painter.setFont(subtitle_font)
    painter.setPen(QColor("#4a6fa5"))
    fm_sub = QFontMetricsF(subtitle_font)
    sub_height = fm_sub.lineSpacing()
    sub_y = y + header_height + 4
    subtitle_rect = QRectF(rect.left(), sub_y, rect.width(), sub_height)
    painter.drawText(subtitle_rect, Qt.AlignLeft | Qt.AlignVCenter, subtitle)

    if generated_at:
        meta_font = _scaled_font(9, scale_y=scale_y)
        painter.setFont(meta_font)
        painter.setPen(QColor("#6b778c"))
        fm_meta = QFontMetricsF(meta_font)
        meta_height = fm_meta.lineSpacing()
        meta_y = sub_y + sub_height + 2
        meta_rect = QRectF(rect.left(), meta_y, rect.width(), meta_height)
        painter.drawText(
            meta_rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            f"Gerado em: {generated_at}",
        )
        painter.restore()
        return meta_rect.bottom()

    painter.restore()
    return subtitle_rect.bottom()


def _draw_block_b1(
    painter: QPainter,
    rect: QRectF,
    data: dict[str, Any],
    *,
    scale_y: float = 1.0,
) -> float:
    title = "Ficha de Artigo"
    rows = [
        ("Código", data.get("codigo")),
        ("Nome", data.get("nome")),
        ("Família", data.get("familia")),
        ("Sub-família", data.get("subfamilia")),
        ("Informação adicional", data.get("informacao_adicional")),
        ("Tipo artigo", data.get("tipo_artigo_cod")),
        ("Validade", data.get("validade_cod")),
        ("Temperatura", data.get("temperatura_cod")),
    ]

    block_height = _estimate_block_height(
        rows, title, scale_y=scale_y, image_height=_B1_IMAGE_BOX_SIZE
    )
    block_rect = QRectF(rect.left(), rect.top(), rect.width(), block_height)
    _draw_block_background(painter, block_rect)
    inner = block_rect.adjusted(_BLOCK_PADDING, _BLOCK_PADDING, -_BLOCK_PADDING, -_BLOCK_PADDING)

    painter.save()
    title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
    painter.setFont(title_font)
    painter.setPen(QColor("#253858"))
    fm_title = QFontMetricsF(title_font)
    title_height = fm_title.lineSpacing()
    title_rect = QRectF(inner.left(), inner.top(), inner.width(), title_height)
    painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, title)

    label_font = _scaled_font(10, QFont.Bold, scale_y=scale_y)
    value_font = _scaled_font(10, scale_y=scale_y)
    label_color = QColor("#6b778c")
    value_color = QColor("#172b4d")
    fm_label = QFontMetricsF(label_font)
    fm_value = QFontMetricsF(value_font)
    line_height = max(fm_label.lineSpacing(), fm_value.lineSpacing())
    current_y = title_rect.bottom() + 12

    image_box_width = min(_B1_IMAGE_BOX_SIZE, inner.width() * 0.35)
    image_box_width = max(0.0, image_box_width)
    image_spacing = _B1_IMAGE_SPACING if image_box_width else 0.0
    text_right = inner.right() - image_box_width - image_spacing
    if text_right < inner.left():
        text_right = inner.left()
        image_spacing = 0.0
    text_width = max(text_right - inner.left(), 0.0)
    col_width = text_width * 0.35 if text_width else inner.width() * 0.35

    for label, raw_value in rows:
        value = _format_text(raw_value)
        painter.setFont(label_font)
        painter.setPen(label_color)
        painter.drawText(
            QRectF(inner.left(), current_y, col_width, line_height),
            Qt.AlignLeft | Qt.AlignVCenter,
            label,
        )
        painter.setFont(value_font)
        painter.setPen(value_color)
        painter.drawText(
            QRectF(
                inner.left() + col_width + 12,
                current_y,
                max(text_width - col_width - 12, 0.0),
                line_height,
            ),
            Qt.AlignLeft | Qt.AlignVCenter,
            value,
        )
        current_y += line_height + 8

    if image_box_width and QImage is not None and QPixmap is not None:
        image_top = title_rect.bottom() + 12
        image_left = text_right + image_spacing
        if image_left < inner.left():
            image_left = inner.left()
        image_rect = QRectF(image_left, image_top, image_box_width, image_box_width)

        painter.setPen(QPen(QColor("#d0d7e3")))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(image_rect, 12, 12)

        pixmap: QPixmap | None = None
        path = data.get("image_path")
        if path:
            qimage = QImage(str(path))
            if not qimage.isNull():
                pixmap = QPixmap.fromImage(qimage)

        if pixmap is not None and not pixmap.isNull():
            scaled = pixmap.scaled(
                int(image_rect.width()),
                int(image_rect.height()),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            target = QRectF(
                image_rect.left() + (image_rect.width() - scaled.width()) / 2,
                image_rect.top() + (image_rect.height() - scaled.height()) / 2,
                scaled.width(),
                scaled.height(),
            )
            painter.drawPixmap(target.toAlignedRect(), scaled)

    painter.restore()
    return block_rect.bottom()


def _draw_block_b2(
    painter: QPainter,
    rect: QRectF,
    data: dict[str, Any],
    *,
    scale_y: float = 1.0,
) -> float:
    title = "Ingredientes"
    ingredientes = list(data.get("ingredientes", []))
    totals = data.get("totais", {}) or {}
    block_height = _estimate_table_block_height(len(ingredientes), scale_y=scale_y)
    block_rect = QRectF(rect.left(), rect.top(), rect.width(), block_height)
    _draw_block_background(painter, block_rect)
    inner = block_rect.adjusted(_BLOCK_PADDING, _BLOCK_PADDING, -_BLOCK_PADDING, -_BLOCK_PADDING)

    painter.save()
    title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
    painter.setFont(title_font)
    painter.setPen(QColor("#253858"))
    fm_title = QFontMetricsF(title_font)
    title_height = fm_title.lineSpacing()
    title_rect = QRectF(inner.left(), inner.top(), inner.width(), title_height)
    painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, title)

    table_top = title_rect.bottom() + 16
    table_rect = QRectF(inner.left(), table_top, inner.width(), _table_height(len(ingredientes)))
    _draw_ingredient_table(painter, table_rect, ingredientes, scale_y=scale_y)

    totals_font = _scaled_font(10, QFont.Bold, scale_y=scale_y)
    painter.setFont(totals_font)
    painter.setPen(QColor("#253858"))
    fm_totals = QFontMetricsF(totals_font)
    totals_height = fm_totals.lineSpacing()
    totals_y = table_rect.bottom() + 16
    totals_rows = [
        ("Custo Total", totals.get("custo_total")),
        ("Peso Total", totals.get("peso_total")),
        ("N.º Ingredientes", totals.get("num_ingredientes")),
    ]
    value_font = _scaled_font(10, scale_y=scale_y)
    painter.setFont(value_font)
    value_color = QColor("#42526e")
    fm_value = QFontMetricsF(value_font)
    value_height = fm_value.lineSpacing()

    for label, raw_value in totals_rows:
        painter.setFont(totals_font)
        painter.setPen(QColor("#253858"))
        painter.drawText(
            QRectF(inner.left(), totals_y, inner.width() * 0.35, totals_height),
            Qt.AlignLeft | Qt.AlignVCenter,
            label,
        )
        painter.setFont(value_font)
        painter.setPen(value_color)
        painter.drawText(
            QRectF(
                inner.left() + inner.width() * 0.35 + 12,
                totals_y,
                inner.width() * 0.65 - 12,
                value_height,
            ),
            Qt.AlignLeft | Qt.AlignVCenter,
            _format_measure(raw_value),
        )
        totals_y += value_height + 6

    painter.restore()
    return block_rect.bottom()


def _draw_block_b3(
    painter: QPainter,
    rect: QRectF,
    data: dict[str, Any],
    *,
    scale_y: float = 1.0,
) -> float:
    title = "Food Cost"
    pvps = list(data.get("pvps", []))
    fcs = list(data.get("food_cost", []))
    iva = data.get("iva")

    rows = []
    for idx, pvp in enumerate(pvps, start=1):
        fc = fcs[idx - 1] if idx - 1 < len(fcs) else None
        rows.append((f"PVP{idx}", pvp, f"Food Cost", fc))

    block_height = _estimate_food_cost_height(max(1, len(rows)), scale_y=scale_y)
    block_rect = QRectF(rect.left(), rect.top(), rect.width(), block_height)
    _draw_block_background(painter, block_rect)
    inner = block_rect.adjusted(_BLOCK_PADDING, _BLOCK_PADDING, -_BLOCK_PADDING, -_BLOCK_PADDING)

    painter.save()
    title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
    painter.setFont(title_font)
    painter.setPen(QColor("#253858"))
    fm_title = QFontMetricsF(title_font)
    title_height = fm_title.lineSpacing()
    title_rect = QRectF(inner.left(), inner.top(), inner.width(), title_height)
    painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, title)

    meta_font = _scaled_font(10, QFont.Bold, scale_y=scale_y)
    painter.setFont(meta_font)
    painter.setPen(QColor("#4a6fa5"))
    fm_meta = QFontMetricsF(meta_font)
    meta_height = fm_meta.lineSpacing()
    meta_rect = QRectF(
        inner.left(),
        title_rect.bottom() + 12,
        inner.width(),
        meta_height,
    )
    painter.drawText(meta_rect, Qt.AlignLeft | Qt.AlignVCenter, f"IVA: {_format_measure(iva)}")

    rows_top = meta_rect.bottom() + 12
    row_height = _FOOD_ROW_HEIGHT
    table_rect = QRectF(inner.left(), rows_top, inner.width(), row_height * max(1, len(rows)))
    _draw_food_cost_table(painter, table_rect, rows, scale_y=scale_y)

    painter.restore()
    return block_rect.bottom()


def _draw_block_background(painter: QPainter, rect: QRectF) -> None:
    painter.save()
    border_pen = QPen(QColor("#d0d7e3"))
    border_pen.setWidthF(1.2)
    border_pen.setCosmetic(True)
    painter.setPen(border_pen)
    painter.setBrush(QColor("#ffffff"))
    painter.drawRoundedRect(rect, 16, 16)
    painter.restore()


def _draw_ingredient_table(
    painter: QPainter,
    rect: QRectF,
    ingredientes: list[dict[str, Any]],
    *,
    scale_y: float = 1.0,
) -> None:
    painter.save()
    header_bg = QColor("#eef5ff")
    header_text = QColor("#2c3e66")
    grid_color = QColor("#4a6fa5")
    body_text = QColor("#172b4d")
    secondary_text = QColor("#42526e")
    header_outline_pen = QPen(grid_color)
    header_outline_pen.setWidthF(1.0)
    header_outline_pen.setCosmetic(True)
    grid_pen = QPen(grid_color)
    grid_pen.setWidthF(0.8)
    grid_pen.setCosmetic(True)

    headers = [
        "Ingrediente",
        "Quantidade",
        "Unidade",
        "PPU",
        "Total",
        "Peso",
    ]

    fixed_widths = [96.0, 61.2, 85.0, 93.5, 46.75]
    spacing = 12.0
    total_spacing = spacing * (len(headers) - 1)
    available = rect.width() - total_spacing
    fixed_sum = sum(fixed_widths)
    name_width = max(available - fixed_sum, 120.0)
    column_widths = [name_width, *fixed_widths]

    positions = [rect.left()]
    for width in column_widths[:-1]:
        positions.append(positions[-1] + width + spacing)

    header_height = _TABLE_ROW_HEIGHT
    painter.setBrush(header_bg)
    painter.setPen(Qt.NoPen)
    header_rect = QRectF(rect.left(), rect.top(), rect.width(), header_height)
    painter.drawRoundedRect(header_rect, 6, 6)

    painter.setPen(header_outline_pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(header_rect, 6, 6)

    header_font = _scaled_font(10, QFont.Bold, scale_y=scale_y)
    painter.setFont(header_font)
    fm_header = QFontMetricsF(header_font)

    for idx, header in enumerate(headers):
        x = positions[idx]
        width = column_widths[idx]
        cell_rect = QRectF(x, rect.top(), width, header_height)
        align = Qt.AlignCenter if idx > 0 else Qt.AlignVCenter | Qt.AlignLeft
        painter.setPen(header_text)
        painter.drawText(cell_rect.adjusted(6, 0, -6, 0), align, header.upper())

    row_font = _scaled_font(10, scale_y=scale_y)
    painter.setFont(row_font)
    row_height = _TABLE_ROW_HEIGHT
    rows = ingredientes or [{}]
    top = rect.top() + header_height

    for entry in rows:
        for col, width in enumerate(column_widths):
            x = positions[col]
            cell_rect = QRectF(x, top, width, row_height)
            painter.setPen(grid_pen)
            painter.drawRect(cell_rect)
            painter.setPen(body_text if col == 0 else secondary_text)
            painter.drawText(
                cell_rect.adjusted(6, 0, -6, 0),
                _column_alignment(col),
                _ingredient_cell_text(col, entry),
            )
        top += row_height

    painter.restore()


def _draw_food_cost_table(
    painter: QPainter,
    rect: QRectF,
    rows: list[tuple[str, Any, str, Any]],
    *,
    scale_y: float = 1.0,
) -> None:
    painter.save()
    grid_color = QColor("#4a6fa5")
    label_color = QColor("#2c3e66")
    value_color = QColor("#172b4d")
    grid_pen = QPen(grid_color)
    grid_pen.setWidthF(0.8)
    grid_pen.setCosmetic(True)
    painter.setPen(grid_pen)

    row_font = _scaled_font(10, scale_y=scale_y)
    painter.setFont(row_font)

    col_width = rect.width() / 2
    top = rect.top()
    rows = rows or [("PVP1", None, "Food Cost", None)]

    for left_label, left_value, right_label, right_value in rows:
        row_rect = QRectF(rect.left(), top, rect.width(), _FOOD_ROW_HEIGHT)
        painter.setPen(grid_pen)
        painter.drawRect(row_rect)

        painter.setPen(label_color)
        painter.drawText(
            QRectF(rect.left() + 6, top, col_width - 12, _FOOD_ROW_HEIGHT / 2),
            Qt.AlignLeft | Qt.AlignVCenter,
            left_label,
        )
        painter.drawText(
            QRectF(rect.left() + col_width + 6, top, col_width - 12, _FOOD_ROW_HEIGHT / 2),
            Qt.AlignLeft | Qt.AlignVCenter,
            right_label,
        )
        painter.setPen(value_color)
        painter.drawText(
            QRectF(rect.left() + 6, top + _FOOD_ROW_HEIGHT / 2, col_width - 12, _FOOD_ROW_HEIGHT / 2),
            Qt.AlignLeft | Qt.AlignVCenter,
            _format_currency(left_value),
        )
        painter.drawText(
            QRectF(
                rect.left() + col_width + 6,
                top + _FOOD_ROW_HEIGHT / 2,
                col_width - 12,
                _FOOD_ROW_HEIGHT / 2,
            ),
            Qt.AlignLeft | Qt.AlignVCenter,
            _format_percentage(right_value),
        )
        top += _FOOD_ROW_HEIGHT
        painter.setPen(grid_pen)

    painter.restore()


def _column_alignment(index: int) -> Qt.AlignmentFlag:
    if index == 0:
        return Qt.AlignVCenter | Qt.AlignLeft
    if index in {1, 2}:
        return Qt.AlignCenter
    return Qt.AlignVCenter | Qt.AlignRight


def _ingredient_cell_text(index: int, entry: dict[str, Any]) -> str:
    if not entry:
        return "—"
    if index == 0:
        name = entry.get("nome") or entry.get("ingrediente")
        code = entry.get("codigo")
        if code:
            return f"{code} — {name or '—'}"
        return _format_text(name)
    if index == 1:
        return _format_number(entry.get("quantidade"), precision=3)
    if index == 2:
        return _format_text(entry.get("unidade"))
    if index == 3:
        return _format_currency(entry.get("ppu"))
    if index == 4:
        return _format_currency(entry.get("total"))
    return _format_number(entry.get("peso"), precision=3)


def _estimate_block_height(
    rows: Iterable[tuple[str, Any]],
    title: str,
    *,
    scale_y: float = 1.0,
    image_height: float | None = None,
) -> float:
    base = 2 * _BLOCK_PADDING
    title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
    fm_title = QFontMetricsF(title_font)
    title_height = fm_title.lineSpacing()
    base += title_height + 12
    value_font = _scaled_font(10, scale_y=scale_y)
    fm_value = QFontMetricsF(value_font)
    value_height = fm_value.lineSpacing()
    for _ in rows:
        base += value_height + 8
    if image_height is not None:
        base = max(base, 2 * _BLOCK_PADDING + title_height + 12 + image_height)
    return base


def _estimate_table_block_height(num_rows: int, *, scale_y: float = 1.0) -> float:
    base = 2 * _BLOCK_PADDING
    title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
    fm_title = QFontMetricsF(title_font)
    base += fm_title.lineSpacing() + 16
    base += _table_height(num_rows)
    totals_font = _scaled_font(10, scale_y=scale_y)
    fm_totals = QFontMetricsF(totals_font)
    totals_height = fm_totals.lineSpacing()
    base += 3 * (totals_height + 6) + 10
    return base


def _estimate_food_cost_height(num_rows: int, *, scale_y: float = 1.0) -> float:
    base = 2 * _BLOCK_PADDING
    title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
    fm_title = QFontMetricsF(title_font)
    base += fm_title.lineSpacing() + 12
    meta_font = _scaled_font(10, QFont.Bold, scale_y=scale_y)
    fm_meta = QFontMetricsF(meta_font)
    base += fm_meta.lineSpacing() + 12
    base += num_rows * _FOOD_ROW_HEIGHT
    return base


def _table_height(num_rows: int) -> float:
    rows = max(1, num_rows)
    return _TABLE_ROW_HEIGHT + rows * _TABLE_ROW_HEIGHT


def _format_text(value: Any) -> str:
    if value in (None, ""):
        return "—"
    return str(value)


def _format_measure(value: Any) -> str:
    if value in (None, ""):
        return "—"
    numeric = _safe_float(value)
    if numeric is None:
        return str(value)
    if float(numeric).is_integer():
        return f"{int(round(numeric))}"
    return f"{numeric:,.2f}"


def _format_currency(value: Any) -> str:
    if value in (None, ""):
        return "—"
    numeric = _safe_float(value)
    if numeric is None:
        return str(value)
    return f"€ {numeric:,.2f}"


def _format_percentage(value: Any) -> str:
    if value in (None, ""):
        return "—"
    numeric = _safe_float(value)
    if numeric is None:
        return str(value)
    return f"{numeric:,.2f}%"


def _format_number(value: Any, *, precision: int = 2) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "—"
    return f"{numeric:,.{precision}f}"


def _points_to_mm(*values: float) -> tuple[float, ...]:
    return tuple(v * 25.4 / 72.0 for v in values)


_PAGE_MARGIN = 36.0
_BLOCK_PADDING = 16.0
_TABLE_ROW_HEIGHT = 28.0
_FOOD_ROW_HEIGHT = 36.0
_B1_IMAGE_BOX_SIZE = 160.0
_B1_IMAGE_SPACING = 16.0


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        parsed = parse_decimal(value)
        if isinstance(parsed, (int, float)):
            try:
                return float(parsed)
            except (TypeError, ValueError):
                return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _serialise_numeric(value: Any) -> float | str | None:
    if value in (None, ""):
        return None
    numeric = _safe_float(value)
    if numeric is None:
        return str(value)
    return numeric


def _build_pdf_lines(payload: dict[str, Any]) -> Iterable[str]:
    blocks = payload.get("blocks", {})
    block_b1 = blocks.get("B1", {}) or {}
    block_b2 = blocks.get("B2", {}) or {}
    block_b3 = blocks.get("B3", {}) or {}

    yield f"{payload.get('page_title', 'Ficha Técnica de Gestão')} — {payload.get('identifier')}"
    generated_at = payload.get("generated_at")
    if generated_at:
        yield f"Gerado em: {generated_at}"
    yield ""

    yield "[B1] Ficha de Artigo"
    for label, key in (
        ("Código", "codigo"),
        ("Nome", "nome"),
        ("Família", "familia"),
        ("Sub-família", "subfamilia"),
        ("Informação adicional", "informacao_adicional"),
        ("Tipo artigo", "tipo_artigo_cod"),
        ("Validade", "validade_cod"),
        ("Temperatura", "temperatura_cod"),
    ):
        value = block_b1.get(key)
        yield f"{label}: {_format_text(value)}"

    yield ""
    yield "[B2] Ingredientes"
    yield "# | Código | Ingrediente | Qtd | Un. | PPU | Total | Peso"
    for entry in block_b2.get("ingredientes", []) or []:
        row = " | ".join(
            [
                str(entry.get("ordem") or ""),
                _format_text(entry.get("codigo")),
                _format_text(entry.get("nome")),
                _format_measure(entry.get("quantidade")),
                _format_text(entry.get("unidade")),
                _format_currency(entry.get("ppu")),
                _format_currency(entry.get("total")),
                _format_number(entry.get("peso"), precision=3),
            ]
        )
        yield row

    totals = block_b2.get("totais", {}) or {}
    yield f"Custo Total: {_format_currency(totals.get('custo_total'))}"
    yield f"Peso Total: {_format_measure(totals.get('peso_total'))}"
    yield f"N.º Ingredientes: {totals.get('num_ingredientes', 0)}"

    yield ""
    yield "[B3] Food Cost"
    iva_value = block_b3.get("iva")
    yield f"IVA: {_format_percentage(iva_value)}"
    pvps = list(block_b3.get("pvps", []) or [])
    food_costs = list(block_b3.get("food_cost", []) or [])
    for index, pvp in enumerate(pvps, start=1):
        fc = food_costs[index - 1] if index - 1 < len(food_costs) else None
        yield f"PVP{index}: {_format_currency(pvp)} | Food Cost: {_format_percentage(fc)}"


def _escape_pdf_text(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
