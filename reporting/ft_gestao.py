"""Helpers to prepare ReportBro payloads for FT Gestão exports."""

from __future__ import annotations

import logging

from pathlib import Path
from typing import Any, Iterable, Mapping

from .reportbro_normalizer import STATIC_SECTION_PARAMETER

from .ft_gestao_schema import (
    FT_GESTAO_PARAMETER_DEFINITIONS,
    default_for_parameter,
)

from utils.formatting import (
    format_currency_locale,
    normalise_currency_context,
    parse_decimal,
)


logger = logging.getLogger(__name__)


EMPTY_FIELD = "--/--"


_DEFAULT_CURRENCY_CONTEXT = {
    "currency": "EUR",
    "currency_code": "EUR",
    "currency_symbol": "€",
    "locale_code": "pt_PT",
}

_CURRENCY_CONTEXT = normalise_currency_context({}, defaults=_DEFAULT_CURRENCY_CONTEXT)


def set_currency_context(context: Any | None) -> dict[str, Any]:
    """Update the currency context used by formatting helpers."""

    global _CURRENCY_CONTEXT
    _CURRENCY_CONTEXT = normalise_currency_context(
        context, defaults=_DEFAULT_CURRENCY_CONTEXT
    )
    return _CURRENCY_CONTEXT


def _should_use_empty_field(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return True
        value = parse_decimal(stripped)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return number == 0.0


def _format_number(value: Any, *, decimals: int = 2) -> str:
    if _should_use_empty_field(value):
        return EMPTY_FIELD

    candidate = parse_decimal(value)
    try:
        number = float(candidate)
    except (TypeError, ValueError):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return EMPTY_FIELD

    if number == 0.0:
        return EMPTY_FIELD

    text = f"{number:,.{decimals}f}"
    return text.replace(",", " ").replace(".", ",")


def _format_optional(value: Any) -> str:
    if _should_use_empty_field(value):
        return EMPTY_FIELD
    text = str(value).strip()
    return text or EMPTY_FIELD


def _format_description_with_fallback(description: Any, code: Any) -> str:
    formatted_description = _format_optional(description)
    if formatted_description != EMPTY_FIELD:
        return formatted_description
    return _format_optional(code)


def _format_currency(value: Any, currency: Mapping[str, Any] | None = None) -> str:
    numeric = _normalise_numeric_value(value)
    if numeric is None:
        return EMPTY_FIELD
    if numeric == 0:
        return EMPTY_FIELD
    context = currency or _CURRENCY_CONTEXT
    return format_currency_locale(
        numeric,
        locale_code=context.get("locale_code"),
        currency_symbol=context.get("currency_symbol"),
        currency_code=context.get("currency_code"),
    )


def _format_percentage(value: Any) -> str:
    formatted = _format_number(value)
    return formatted if formatted == EMPTY_FIELD else f"{formatted} %"


def _normalise_numeric_value(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    cleaned: Any = value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped == EMPTY_FIELD:
            return None
        cleaned = stripped.replace("€", "").replace("%", "").strip()

    candidate = parse_decimal(cleaned)

    for possible in (candidate, cleaned, value):
        if isinstance(possible, (int, float)):
            return float(possible)
        try:
            return float(possible)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue

    return None


def _join_lines(lines: Iterable[str]) -> str:
    filtered = [line.rstrip() for line in lines if line and line.strip()]
    return "\n".join(filtered) if filtered else EMPTY_FIELD


def _build_product_section(
    block: Mapping[str, Any], *, formatted: Mapping[str, str] | None = None
) -> str:
    def _get_formatted(key: str) -> str:
        if formatted and key in formatted:
            return formatted[key]
        return _format_optional(block.get(key))

    lines = [
        "Produto",
        f"Código: {_get_formatted('codigo')}",
    ]

    name = block.get("nome")
    formatted_name = _get_formatted("nome")
    if formatted_name != EMPTY_FIELD:
        lines.append(f"Nome: {formatted_name}")

    lines.append(f"Família: {_get_formatted('familia')}")
    lines.append(f"Subfamília: {_get_formatted('subfamilia')}")
    lines.append(
        f"Tipo de artigo (código): {_get_formatted('tipo_artigo_cod')}"
    )
    lines.append(f"Validade (código): {_get_formatted('validade_cod')}")
    lines.append(
        f"Temperatura (código): {_get_formatted('temperatura_cod')}"
    )
    extra = block.get("informacao_adicional")
    if extra:
        lines.append("Notas adicionais:")
        lines.append(extra)

    return _join_lines(lines)


def _build_product_data(
    block: Mapping[str, Any],
    *,
    tipo_artigo_description: Any = None,
    validade_description: Any = None,
    temperatura_description: Any = None,
) -> dict[str, str]:
    return {
        "codigo": _format_optional(block.get("codigo")),
        "nome": _format_optional(block.get("nome")),
        "familia": _format_optional(block.get("familia")),
        "subfamilia": _format_optional(block.get("subfamilia")),
        "informacao_adicional": _format_optional(
            block.get("informacao_adicional")
        ),
        "tipo_artigo_cod": _format_description_with_fallback(
            tipo_artigo_description, block.get("tipo_artigo_cod")
        ),
        "validade_cod": _format_description_with_fallback(
            validade_description, block.get("validade_cod")
        ),
        "temperatura_cod": _format_description_with_fallback(
            temperatura_description, block.get("temperatura_cod")
        ),
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
        if fc_text != EMPTY_FIELD:
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
        if food_cost and food_cost != EMPTY_FIELD:
            entry += f" | Food cost: {food_cost}"
        lines.append(entry)
    return "\n".join(lines) if lines else EMPTY_FIELD


def _build_ingredients_section(block: Mapping[str, Any]) -> str:
    lines = ["Ingredientes"]
    ingredients = list(block.get("ingredientes") or [])
    for entry in ingredients:
        order = entry.get("ordem")
        name_value = entry.get("nome")
        name = _format_optional(name_value)
        if name == EMPTY_FIELD:
            name = _format_optional(entry.get("codigo"))
        prefix = f"{int(order):02d}. " if isinstance(order, (int, float)) else ""
        label = f"{prefix}{name}"
        details: list[str] = []
        code = entry.get("codigo")
        code_text = _format_optional(code)
        if code_text != EMPTY_FIELD and code_text != name:
            details.append(f"Código: {code_text}")
        quantity = entry.get("quantidade")
        unit = entry.get("unidade")
        quantity_text = _format_ingredient_quantity(quantity, unit)
        details.append(f"Qtd: {quantity_text}")
        ppu = entry.get("ppu")
        if ppu is not None:
            ppu_text = _format_currency(ppu)
            unit_text = _format_optional(unit)
            unit_label = f"/{unit_text}" if unit_text != EMPTY_FIELD else ""
            details.append(f"PPU: {ppu_text}{unit_label}")
        total = entry.get("total")
        if total is not None:
            total_text = _format_currency(total)
            details.append(f"Custo: {total_text}")
        weight = entry.get("peso")
        if weight is not None:
            weight_text = _format_number(weight)
            details.append(f"Peso: {weight_text}")

        if details:
            label += " — " + " | ".join(details)
        lines.append(label)

    if len(lines) == 1:
        lines.append(EMPTY_FIELD)
    return "\n".join(lines)


def _format_ingredient_quantity(quantity: Any, unit: Any) -> str:
    candidate = parse_decimal(quantity)
    decimals = 2
    number: float | None
    try:
        number = float(candidate)
    except (TypeError, ValueError):
        try:
            number = float(quantity)
        except (TypeError, ValueError):
            number = None
    if isinstance(number, float):
        if number != 0.0 and abs(number) < 1:
            decimals = 3
        formatted = _format_number(number, decimals=decimals)
    else:
        formatted = _format_number(quantity, decimals=decimals)
    if formatted == EMPTY_FIELD:
        return EMPTY_FIELD
    unit_text = _format_optional(unit)
    if unit_text == EMPTY_FIELD:
        return formatted
    return f"{formatted} {unit_text}".strip()


def _build_ingredients_rows(block: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    ingredients = list(block.get("ingredientes") or [])
    for entry in ingredients:
        order = entry.get("ordem")
        order_text = _format_optional(order)
        if order_text != EMPTY_FIELD:
            try:
                order_text = f"{int(float(order))}"
            except (TypeError, ValueError):
                pass
        nome_text = _format_optional(entry.get("nome"))
        if nome_text == EMPTY_FIELD:
            nome_text = _format_optional(entry.get("codigo"))
        rows.append(
            {
                "ordem": order_text,
                "nome": nome_text,
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
    return "\n".join(lines) if lines else EMPTY_FIELD


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
    payload_currency: Any | None = None
    flattened_currency: dict[str, Any] = {}

    def _is_missing(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        return False

    if isinstance(payload, Mapping):
        payload_currency = payload.get("currency")

        currency_keys = (
            "id",
            "country",
            "country_code",
            "code",
            "currency",
            "currency_name",
            "currency_code",
            "currency_symbol",
            "symbol",
            "locale_code",
            "format",
            "fmt",
            "active",
        )
        for key in currency_keys:
            if key in payload and not _is_missing(payload[key]):
                flattened_currency[key] = payload[key]

        reportbro_section = payload.get("reportbro")
        if isinstance(reportbro_section, Mapping):
            provided = reportbro_section.get("parameters")
            if isinstance(provided, Mapping):
                parameters.update(provided)

    currency_source: Any = payload_currency
    if flattened_currency:
        if isinstance(payload_currency, Mapping):
            merged: dict[str, Any] = dict(payload_currency)
            for key, value in flattened_currency.items():
                merged[key] = value
            currency_source = merged
        elif _is_missing(payload_currency):
            currency_source = flattened_currency

    currency_context = set_currency_context(currency_source)

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
    subtitle = " — ".join(part for part in subtitle_parts if part != EMPTY_FIELD)

    product_data = _build_product_data(
        block_b1,
        tipo_artigo_description=parameters.get("TiposArtigos_Descricao"),
        validade_description=parameters.get("Validade_Descricao"),
        temperatura_description=parameters.get("Temperaturas_Descricao"),
    )
    product_details = _build_product_section(block_b1, formatted=product_data)
    pricing_rows = _build_pricing_rows(block_b3)
    pricing_lines = _build_pricing_lines(pricing_rows)
    ingredients_rows = _build_ingredients_rows(block_b2)
    ingredients_lines = _build_ingredients_lines(ingredients_rows)

    ingredientes_table: list[dict[str, Any]] = []
    ingredientes_source = list(block_b2.get("ingredientes") or [])

    def _safe_numeric(value: Any) -> float:
        if value is None:
            return 0.0
        parsed = parse_decimal(value)
        try:
            return float(parsed)
        except (TypeError, ValueError):
            pass
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    ingredientes_totais_preco: list[float] = []

    for entry in ingredientes_source:
        ingrediente_nome = entry.get("nome") or entry.get("codigo") or ""
        ppu_value = entry.get("ppu")
        total_value = entry.get("total")
        total_numeric = _safe_numeric(total_value)
        ingredientes_totais_preco.append(total_numeric)
        ingredientes_table.append(
            {
                "FichasTecnicas_ComponenteNome": ingrediente_nome,
                "FichasTecnicas_Qtd": _safe_numeric(entry.get("quantidade")),
                "FichasTecnicas_Unidade": entry.get("unidade") or "",
                "FichasTecnicas_Ppu": _safe_numeric(ppu_value),
                "FichasTecnicas_Ppu_display": _format_currency(ppu_value),
                "FichasTecnicas_Preco": total_numeric,
                "FichasTecnicas_Preco_display": _format_currency(total_value),
                "FichasTecnicas_Peso": _safe_numeric(entry.get("peso")),
            }
        )

    totals_data = _build_totals_data(block_b2.get("totais") or {})
    totals_lines = _build_totals_lines(totals_data)

    def _normalise_image_value(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return str(value)

    def _normalise_file_uri(value: Any) -> str | None:
        normalised = _normalise_image_value(value)
        if not normalised:
            return None
        if isinstance(normalised, str) and normalised.startswith(
            ("http://", "https://", "file:", "data:")
        ):
            return normalised
        try:
            return Path(str(normalised)).resolve().as_uri()
        except (TypeError, ValueError, OSError):
            return str(normalised)

    grafico_foodcost_filename = _normalise_file_uri(
        payload.get("GraficoFoodCost_Filename")
    )
    if not grafico_foodcost_filename:
        grafico_foodcost_filename = _normalise_file_uri(
            parameters.get("GraficoFoodCost_Filename")
        )
    if grafico_foodcost_filename:
        parameters["GraficoFoodCost_Filename"] = grafico_foodcost_filename
    elif "GraficoFoodCost_Filename" in parameters:
        parameters["GraficoFoodCost_Filename"] = ""

    parameter_image_filename = _normalise_image_value(
        parameters.get("product_image_filename")
    )
    parameter_image_uri = _normalise_image_value(parameters.get("product_image_uri"))

    raw_image_filename = payload.get("product_image_filename")
    product_image_filename = _normalise_image_value(raw_image_filename)
    if not product_image_filename:
        product_image_filename = parameter_image_filename

    raw_image_uri = payload.get("product_image_uri")
    product_image_uri = _normalise_image_value(raw_image_uri)
    if not product_image_uri and product_image_filename:
        product_image_uri = parameter_image_uri

    if product_image_filename:
        parameters["product_image_filename"] = product_image_filename
        if product_image_uri:
            parameters["product_image_uri"] = product_image_uri
        else:
            parameters.pop("product_image_uri", None)
    else:
        parameters.pop("product_image_filename", None)
        parameters.pop("product_image_uri", None)

    current_image_path = product_data.get("image_path")
    if product_image_filename and (not current_image_path or current_image_path == EMPTY_FIELD):
        product_data["image_path"] = product_image_filename

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
        if generated_at != EMPTY_FIELD
        else page_title
    )

    dataset: dict[str, Any] = dict(parameters)
    dataset_update = {
        "currency": dict(currency_context),
        "currency_symbol": currency_context.get("currency_symbol"),
        "currency_code": currency_context.get("currency_code"),
        "locale_code": currency_context.get("locale_code"),
        "title": page_title,
        "subtitle": subtitle or _format_optional(payload.get("identifier")),
        "metadata": metadata,
        "product_details": product_details,
        "pricing_details": _build_pricing_section(block_b3),
        "ingredients": _build_ingredients_section(block_b2),
        "ingredientes": ingredientes_table,
        "ingredientes_FichasTecnicas_Preco": [
            entry.get("FichasTecnicas_Preco", 0.0) for entry in ingredientes_table
        ],
        "ingredientes_sum_FichasTecnicas_Preco": sum(ingredientes_totais_preco),
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
        "GraficoFoodCost_Filename": grafico_foodcost_filename or "",
    }

    precos_taxas_values = list(block_b3.get("pvps") or [])
    for index in range(1, 6):
        key = f"PrecosTaxas_Preco{index}"
        display_key = f"{key}_display"
        if index - 1 < len(precos_taxas_values):
            price_value = precos_taxas_values[index - 1]
        else:
            price_value = None
        if price_value in (None, ""):
            price_value = parameters.get(key)

        dataset_update[key] = _normalise_numeric_value(price_value)
        dataset_update[display_key] = _format_currency(price_value)

    if product_image_filename:
        dataset_update["product_image_filename"] = product_image_filename
        if product_image_uri:
            dataset_update["product_image_uri"] = product_image_uri
    dataset.update(dataset_update)
    for numeric_name in ("TiposArtigos_Cod", "Validade_Cod", "Temperaturas_Cod"):
        value = dataset.get(numeric_name)
        if value in (None, "", EMPTY_FIELD):
            dataset[numeric_name] = 0
            continue
        candidate = parse_decimal(value)
        try:
            dataset[numeric_name] = int(float(candidate))
        except (TypeError, ValueError):
            try:
                dataset[numeric_name] = int(value)
            except (TypeError, ValueError):
                logger.debug(
                    "[ReportBro] unable to normalise %s=%r to int", numeric_name, value
                )
    dataset[STATIC_SECTION_PARAMETER] = [{}]
    return dataset
