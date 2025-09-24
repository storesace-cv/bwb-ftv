"""Helpers to prepare ReportBro payloads for FT Gestão exports."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


def _format_number(value: Any, *, decimals: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"

    text = f"{number:,.{decimals}f}"
    return text.replace(",", " ").replace(".", ",")


def _format_optional(value: Any) -> str:
    if value is None:
        return "—"
    text = str(value).strip()
    return text or "—"


def _format_currency(value: Any) -> str:
    formatted = _format_number(value)
    return formatted if formatted == "—" else f"{formatted} €"


def _format_percentage(value: Any) -> str:
    formatted = _format_number(value)
    return formatted if formatted == "—" else f"{formatted} %"


def _join_lines(lines: Iterable[str]) -> str:
    filtered = [line.rstrip() for line in lines if line and line.strip()]
    return "\n".join(filtered) if filtered else "—"


def _build_product_section(block: Mapping[str, Any]) -> str:
    lines = [
        "Produto",
        f"Código: {_format_optional(block.get('codigo'))}",
    ]

    name = block.get("nome")
    if name:
        lines.append(f"Nome: {name}")

    lines.append(f"Família: {_format_optional(block.get('familia'))}")
    lines.append(f"Subfamília: {_format_optional(block.get('subfamilia'))}")
    lines.append(
        f"Tipo de artigo (código): {_format_optional(block.get('tipo_artigo_cod'))}"
    )
    lines.append(
        f"Validade (código): {_format_optional(block.get('validade_cod'))}"
    )
    lines.append(
        f"Temperatura (código): {_format_optional(block.get('temperatura_cod'))}"
    )
    extra = block.get("informacao_adicional")
    if extra:
        lines.append("Notas adicionais:")
        lines.append(extra)

    return _join_lines(lines)


def _build_pricing_section(block: Mapping[str, Any]) -> str:
    lines = ["Preços e IVA"]

    iva = block.get("iva")
    lines.append(f"IVA: {_format_percentage(iva)}")

    pvps = list(block.get("pvps") or [])
    food_cost = list(block.get("food_cost") or [])
    for index, pvp in enumerate(pvps, start=1):
        entry = f"PVP{index}: {_format_currency(pvp)}"
        try:
            fc_value = food_cost[index - 1]
        except IndexError:
            fc_value = None
        fc_text = _format_percentage(fc_value)
        if fc_text != "—":
            entry += f" (Food cost: {fc_text})"
        lines.append(entry)

    return _join_lines(lines)


def _build_ingredients_section(block: Mapping[str, Any]) -> str:
    lines = ["Ingredientes"]
    ingredients = list(block.get("ingredientes") or [])
    for entry in ingredients:
        order = entry.get("ordem")
        name = entry.get("nome") or entry.get("codigo") or "—"
        prefix = f"{int(order):02d}. " if isinstance(order, (int, float)) else ""
        label = f"{prefix}{name}"
        details: list[str] = []
        code = entry.get("codigo")
        if code and code != name:
            details.append(f"Código: {code}")
        quantity = entry.get("quantidade")
        unit = entry.get("unidade")
        if quantity is not None:
            qty_text = _format_number(quantity, decimals=3 if (quantity and quantity < 1) else 2)
            if unit:
                details.append(f"Qtd: {qty_text} {unit}")
            else:
                details.append(f"Qtd: {qty_text}")
        ppu = entry.get("ppu")
        if ppu is not None:
            unit_label = f"/{unit}" if unit else ""
            details.append(f"PPU: {_format_currency(ppu)}{unit_label}")
        total = entry.get("total")
        if total is not None:
            details.append(f"Custo: {_format_currency(total)}")
        weight = entry.get("peso")
        if weight is not None:
            details.append(f"Peso: {_format_number(weight)}")

        if details:
            label += " — " + " | ".join(details)
        lines.append(label)

    if len(lines) == 1:
        lines.append("—")
    return "\n".join(lines)


def _build_totals_section(block: Mapping[str, Any]) -> str:
    lines = ["Totais"]
    totals = block.get("totais") or {}
    lines.append(f"Custo total: {_format_currency(totals.get('custo_total'))}")
    lines.append(f"Peso total: {_format_number(totals.get('peso_total'))}")
    lines.append(
        f"Número de ingredientes: {_format_optional(totals.get('num_ingredientes'))}"
    )
    return _join_lines(lines)


def build_reportbro_context(payload: Mapping[str, Any]) -> dict[str, str]:
    """Convert ``generate_ft_gestao`` payload to the ReportBro dataset structure."""

    blocks = payload.get("blocks", {})
    block_b1 = blocks.get("B1", {})
    block_b2 = blocks.get("B2", {})
    block_b3 = blocks.get("B3", {})

    subtitle_parts = [
        _format_optional(block_b1.get("codigo")),
        _format_optional(block_b1.get("nome")),
    ]
    subtitle = " — ".join(part for part in subtitle_parts if part != "—")

    return {
        "title": payload.get("page_title", "Ficha Técnica"),
        "subtitle": subtitle or _format_optional(payload.get("identifier")),
        "metadata": f"Gerado em {_format_optional(payload.get('generated_at'))}",
        "product_details": _build_product_section(block_b1),
        "pricing_details": _build_pricing_section(block_b3),
        "ingredients": _build_ingredients_section(block_b2),
        "totals": _build_totals_section(block_b2),
    }
