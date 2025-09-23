"""Helpers related to printing/exporting UI artefacts."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterable as IterableABC
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from PyQt5.QtWidgets import QFileDialog, QWidget

from domain.models import Product
from services.products import calculate_food_cost
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
    lines = list(_build_pdf_lines(payload))
    sanitized_lines = [_to_pdf_ascii(line) for line in lines]
    margin = 36.0
    font_size = 10
    leading = font_size + 4
    width, height = page_metrics
    y_cursor = height - margin
    text_ops = []
    for line in sanitized_lines:
        text_ops.append(
            f"BT /F1 {font_size} Tf {margin:.2f} {y_cursor:.2f} Td ({_escape_pdf_text(line)}) Tj ET"
        )
        y_cursor -= leading
        if y_cursor <= margin:
            break

    content_stream = "\n".join(text_ops)
    payload_json = json.dumps(payload, ensure_ascii=True)

    objects = []
    objects.append("1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj")
    objects.append("2 0 obj<< /Type /Pages /Count 1 /Kids [3 0 R] >>endobj")
    objects.append(
        "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] /Resources "
        "<< /Font << /F1 5 0 R >> >> /Contents 4 0 R >>endobj" % page_metrics
    )
    objects.append(
        "4 0 obj<< /Length %d >>stream\n%s\nendstream endobj"
        % (len(content_stream.encode("latin-1", "ignore")), content_stream)
    )
    objects.append(
        "5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj"
    )

    xref_positions = []
    body_parts = []
    offset = 0
    header = "%PDF-1.4\n"
    prefix = f"%FT_GESTAO_PAYLOAD {payload_json}\n"
    offset += len(header) + len(prefix)
    for obj in objects:
        xref_positions.append(offset)
        part = f"{obj}\n"
        body_parts.append(part)
        offset += len(part)

    xref_start = offset
    xref_entries = ["0000000000 65535 f "]
    for pos in xref_positions:
        xref_entries.append(f"{pos:010} 00000 n ")

    xref_table = "xref\n0 %d\n%s\n" % (
        len(xref_entries),
        "\n".join(xref_entries),
    )
    trailer = (
        "trailer<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (
            len(xref_entries),
            xref_start,
        )
    )

    pdf_content = header + prefix + "".join(body_parts) + xref_table + trailer
    destination.write_bytes(pdf_content.encode("latin-1", "ignore"))


def _build_pdf_lines(payload: dict[str, Any]) -> Iterable[str]:
    blocks = payload.get("blocks", {})
    b1 = blocks.get("B1", {})
    b2 = blocks.get("B2", {})
    b3 = blocks.get("B3", {})

    yield f"{payload.get('page_title', 'Ficha de Gestão')} — {payload.get('identifier')}"
    yield f"Gerado em: {payload.get('generated_at')}"
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
        yield f"{label}: {b1.get(key) or '--'}"

    yield ""
    yield "[B2] Ingredientes"
    yield "# | Código | Ingrediente | Qtd | Un. | PPU | Total | Peso"
    for entry in b2.get("ingredientes", []):
        yield " | ".join(
            [
                f"{entry.get('ordem', '')}",
                str(entry.get("codigo") or "--"),
                str(entry.get("nome") or "--"),
                _format_number(entry.get("quantidade")),
                str(entry.get("unidade") or "--"),
                _format_number(entry.get("ppu")),
                _format_number(entry.get("total")),
                _format_number(entry.get("peso")),
            ]
        )

    totals = b2.get("totais", {})
    yield f"Custo Total: {_format_number(totals.get('custo_total'))}"
    yield f"Peso Total: {_format_number(totals.get('peso_total'))}"
    yield f"N.º Ingredientes: {totals.get('num_ingredientes', 0)}"

    yield ""
    yield "[B3] Food Cost"
    pvps = list(b3.get("pvps", []))
    fcs = list(b3.get("food_cost", []))
    iva = b3.get("iva")
    yield f"IVA: {_format_number(iva)}"
    for idx, pvp in enumerate(pvps, start=1):
        fc = fcs[idx - 1] if idx - 1 < len(fcs) else None
        yield f"PVP{idx}: {_format_number(pvp)} | Food Cost: {_format_number(fc)}%"


def _format_number(value: Any, missing: str = "--") -> str:
    number = _safe_float(value)
    if number is None:
        return missing
    return f"{number:,.2f}"


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


def _to_pdf_ascii(text: str) -> str:
    return re.sub(r"[^\x20-\x7E]", "?", str(text))


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
