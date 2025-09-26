"""Helpers to prepare ReportBro payloads for FT Gestão exports."""

from __future__ import annotations

import logging

from typing import Any, Iterable, Mapping

from .reportbro_normalizer import STATIC_SECTION_PARAMETER

from .ft_gestao_schema import (
    FT_GESTAO_PARAMETER_DEFINITIONS,
    default_for_parameter,
)


logger = logging.getLogger(__name__)


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


def _build_product_data(block: Mapping[str, Any]) -> dict[str, str]:
    return {
        "codigo": _format_optional(block.get("codigo")),
        "nome": _format_optional(block.get("nome")),
        "familia": _format_optional(block.get("familia")),
        "subfamilia": _format_optional(block.get("subfamilia")),
        "informacao_adicional": _format_optional(
            block.get("informacao_adicional")
        ),
        "tipo_artigo_cod": _format_optional(block.get("tipo_artigo_cod")),
        "validade_cod": _format_optional(block.get("validade_cod")),
        "temperatura_cod": _format_optional(block.get("temperatura_cod")),
        "image_path": _format_optional(block.get("image_path")),
    }


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


def _build_pricing_rows(block: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    pvps = list(block.get("pvps") or [])
    food_cost = list(block.get("food_cost") or [])
    for index, pvp in enumerate(pvps, start=1):
        try:
            fc_value = food_cost[index - 1]
        except IndexError:
            fc_value = None
        rows.append(
            {
                "label": f"PVP{index}",
                "pvp": _format_currency(pvp),
                "food_cost": _format_percentage(fc_value),
            }
        )
    return rows


def _build_pricing_lines(rows: Iterable[Mapping[str, str]]) -> str:
    lines: list[str] = []
    for row in rows:
        entry = f"{row.get('label')}: {row.get('pvp')}"
        food_cost = row.get("food_cost")
        if food_cost and food_cost != "—":
            entry += f" | Food cost: {food_cost}"
        lines.append(entry)
    return "\n".join(lines) if lines else "—"


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


def _format_ingredient_quantity(quantity: Any, unit: Any) -> str:
    if quantity is None and not unit:
        return "—"
    decimals = 2
    try:
        number = float(quantity)
    except (TypeError, ValueError):
        number = None
    else:
        if abs(number) < 1:
            decimals = 3
    formatted = _format_number(number, decimals=decimals) if number is not None else "—"
    if formatted == "—":
        return _format_optional(unit)
    if unit:
        return f"{formatted} {unit}".strip()
    return formatted


def _build_ingredients_rows(block: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    ingredients = list(block.get("ingredientes") or [])
    for entry in ingredients:
        order = entry.get("ordem")
        order_text = _format_optional(order)
        if order_text != "—":
            try:
                order_text = f"{int(float(order))}"
            except (TypeError, ValueError):
                pass
        rows.append(
            {
                "ordem": order_text,
                "nome": _format_optional(entry.get("nome") or entry.get("codigo")),
                "codigo": _format_optional(entry.get("codigo")),
                "quantidade": _format_ingredient_quantity(
                    entry.get("quantidade"), entry.get("unidade")
                ),
                "ppu": _format_currency(entry.get("ppu")),
                "total": _format_currency(entry.get("total")),
                "peso": _format_number(entry.get("peso")),
            }
        )
    return rows


def _build_ingredients_lines(rows: Iterable[Mapping[str, str]]) -> str:
    lines: list[str] = []
    for row in rows:
        lines.append(
            " | ".join(
                [
                    f"Ordem: {row.get('ordem')}",
                    f"Nome: {row.get('nome')}",
                    f"Código: {row.get('codigo')}",
                    f"Quantidade: {row.get('quantidade')}",
                    f"PPU: {row.get('ppu')}",
                    f"Custo: {row.get('total')}",
                    f"Peso: {row.get('peso')}",
                ]
            )
        )
    return "\n".join(lines) if lines else "—"


def _build_totals_section(block: Mapping[str, Any]) -> str:
    lines = ["Totais"]
    totals = block.get("totais") or {}
    lines.append(f"Custo total: {_format_currency(totals.get('custo_total'))}")
    lines.append(f"Peso total: {_format_number(totals.get('peso_total'))}")
    lines.append(
        f"Número de ingredientes: {_format_optional(totals.get('num_ingredientes'))}"
    )
    return _join_lines(lines)


def _build_totals_data(block: Mapping[str, Any]) -> dict[str, str]:
    return {
        "custo_total": _format_currency(block.get("custo_total")),
        "peso_total": _format_number(block.get("peso_total")),
        "num_ingredientes": _format_optional(block.get("num_ingredientes")),
    }


def _build_totals_lines(totals: Mapping[str, str]) -> str:
    return "\n".join(
        [
            f"Custo total: {totals.get('custo_total')}",
            f"Peso total: {totals.get('peso_total')}",
            f"Número de ingredientes: {totals.get('num_ingredientes')}",
        ]
    )


def build_reportbro_context(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Convert ``generate_ft_gestao`` payload to the ReportBro dataset structure."""

    parameters: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        reportbro_section = payload.get("reportbro")
        if isinstance(reportbro_section, Mapping):
            provided = reportbro_section.get("parameters")
            if isinstance(provided, Mapping):
                parameters.update(provided)

    image_parameter_names = {"product_image_filename", "product_image_uri"}
    for name in FT_GESTAO_PARAMETER_DEFINITIONS:
        if name in image_parameter_names:
            continue
        parameters.setdefault(name, default_for_parameter(name))

    blocks = payload.get("blocks", {})
    block_b1 = blocks.get("B1", {})
    block_b2 = blocks.get("B2", {})
    block_b3 = blocks.get("B3", {})

    page_title = payload.get("page_title", "Ficha Técnica")
    subtitle_parts = [
        _format_optional(block_b1.get("codigo")),
        _format_optional(block_b1.get("nome")),
    ]
    subtitle = " — ".join(part for part in subtitle_parts if part != "—")

    product_data = _build_product_data(block_b1)
    pricing_rows = _build_pricing_rows(block_b3)
    pricing_lines = _build_pricing_lines(pricing_rows)
    ingredients_rows = _build_ingredients_rows(block_b2)
    ingredients_lines = _build_ingredients_lines(ingredients_rows)
    totals_data = _build_totals_data(block_b2.get("totais") or {})
    totals_lines = _build_totals_lines(totals_data)
    def _normalise_image_value(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return str(value)

    raw_image_filename = payload.get("product_image_filename")
    product_image_filename = _normalise_image_value(raw_image_filename)

    raw_image_uri = payload.get("product_image_uri")
    product_image_uri = _normalise_image_value(raw_image_uri)

    if product_image_filename:
        parameters["product_image_filename"] = product_image_filename
        if product_image_uri:
            parameters["product_image_uri"] = product_image_uri
        else:
            parameters.pop("product_image_uri", None)
    else:
        parameters.pop("product_image_filename", None)
        parameters.pop("product_image_uri", None)

    logger.info(
        "[ReportBro] product_image_filename dataset: entrada=%r -> product_image_filename=%r, product_image_path=%r, product_image_uri=%r",
        raw_image_filename,
        product_image_filename,
        product_data.get("image_path"),
        product_image_uri,
    )

    generated_at = _format_optional(payload.get("generated_at"))
    metadata = (
        f"{page_title} — Gerado em {generated_at}"
        if generated_at != "—"
        else page_title
    )

    dataset: dict[str, Any] = dict(parameters)
    dataset_update = {
            "title": page_title,
            "subtitle": subtitle or _format_optional(payload.get("identifier")),
            "metadata": metadata,
            "product_details": _build_product_section(block_b1),
            "pricing_details": _build_pricing_section(block_b3),
            "ingredients": _build_ingredients_section(block_b2),
            "totals": _build_totals_section(block_b2),
            "product_data": product_data,
            "pricing_data": {
                "iva": _format_percentage(block_b3.get("iva")),
                "rows": pricing_rows,
            },
            "product_codigo": product_data["codigo"],
            "product_nome": product_data["nome"],
            "product_familia": product_data["familia"],
            "product_subfamilia": product_data["subfamilia"],
            "product_tipo_artigo_cod": product_data["tipo_artigo_cod"],
            "product_validade_cod": product_data["validade_cod"],
            "product_temperatura_cod": product_data["temperatura_cod"],
            "product_informacao_adicional": product_data["informacao_adicional"],
            "product_image_path": product_data["image_path"],
            "pricing_rows": pricing_rows,
            "pricing_lines": pricing_lines,
            "pricing_iva": _format_percentage(block_b3.get("iva")),
            "ingredients_data": ingredients_rows,
            "ingredients_lines": ingredients_lines,
            "totals_data": totals_data,
            "totals_lines": totals_lines,
            "totals_custo_total": totals_data["custo_total"],
            "totals_peso_total": totals_data["peso_total"],
            "totals_num_ingredientes": totals_data["num_ingredientes"],
        }

    if product_image_filename:
        dataset_update["product_image_filename"] = product_image_filename
        if product_image_uri:
            dataset_update["product_image_uri"] = product_image_uri
    dataset.update(dataset_update)
    dataset[STATIC_SECTION_PARAMETER] = [{}]
    return dataset
