"""Helpers related to printing/exporting UI artefacts."""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Iterable as IterableABC, MutableMapping as MutableMappingABC
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

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

from domain.models import Product
from reporting import (
    build_reportbro_context,
    load_template_definition,
    render_pdf_to_path,
)
from reporting.graphics import gerar_grafico_foodcost_pie
from reporting.ft_gestao_schema import (
    FT_GESTAO_PARAMETER_DEFINITIONS,
    default_for_parameter,
)
from services.products import calculate_food_cost
from utils.paths import get_project_root
from utils.formatting import (
    format_currency_locale,
    normalise_currency_context,
    parse_decimal,
)

try:  # PyQt5 may be unavailable during headless unit tests
    from .utilities import FOOD_COST_LEVEL_RGB_MAP
except ModuleNotFoundError:  # pragma: no cover - exercised when Qt bindings missing
    FOOD_COST_LEVEL_RGB_MAP = {
        "Bom": (198, 216, 112),
        "Aceitável": (248, 222, 126),
        "Mau": (255, 158, 145),
        "Todos": (200, 200, 200),
    }

_USE_BASIC_PDF = False

_DEFAULT_CURRENCY_CONTEXT = {
    "currency": "EUR",
    "currency_code": "EUR",
    "currency_symbol": "€",
    "locale_code": "pt_PT",
}

_CURRENCY_CONTEXT = normalise_currency_context({}, defaults=_DEFAULT_CURRENCY_CONTEXT)


def _set_currency_context(context: Any | None) -> dict[str, Any]:
    global _CURRENCY_CONTEXT
    _CURRENCY_CONTEXT = normalise_currency_context(
        context, defaults=_DEFAULT_CURRENCY_CONTEXT
    )
    return _CURRENCY_CONTEXT

logger = logging.getLogger(__name__)

_DEFAULT_PAGE_SIZES = {
    "A4": (595.28, 841.89),
    "LETTER": (612.0, 792.0),
}

_REPORTBRO_RUNTIME_TEMPLATE_DIR = (
    Path(__file__).resolve().parent.parent / "reporting" / "templates"
)
_REPORTBRO_STORE_TEMPLATE_DIR = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "templates_store"
    / "templates"
)
_DEFAULT_REPORTBRO_TEMPLATE_NAME = "ft_gestao_00_base.json"
_DEFAULT_REPORTBRO_TEMPLATE = (
    _REPORTBRO_RUNTIME_TEMPLATE_DIR / _DEFAULT_REPORTBRO_TEMPLATE_NAME
)


class ExportCancelled(RuntimeError):
    """Raised when the user cancels the export dialog."""


def generate_ft_gestao_pdf(
    product: Product,
    *,
    page_size: str = "A4",
    parent: QWidget | None = None,
    locale: Any | None = None,
    food_cost_levels: Iterable[Any] | None = None,
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
    food_cost_levels:
        Lista opcional com intervalos de Food Cost já normalizados para
        transportar para o payload e realçar a grelha impressa.

    Returns
    -------
    Path | None
        Caminho final para o PDF gerado ou ``None`` quando o utilizador cancela.
    """

    product_obj = _validate_product(product)
    payload = _prepare_management_payload(
        product_obj, locale=locale, food_cost_levels=food_cost_levels
    )
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


def _validate_reportbro_inputs(
    template: Mapping[str, Any],
    dataset: Mapping[str, Any],
    warnings: Iterable[Mapping[str, Any]] | None,
) -> None:
    expected: set[str] = {
        param.get("name")
        for param in template.get("parameters", [])
        if isinstance(param, Mapping) and isinstance(param.get("name"), str)
    }
    missing = sorted(name for name in expected if name not in dataset)
    skip_fallback = {"product_image_filename", "product_image_uri"}
    if missing:
        mutable_dataset = dataset if isinstance(dataset, MutableMappingABC) else None
        for name in missing:
            if name in skip_fallback:
                logger.debug(
                    "[ReportBro] parâmetro %s ausente; não será preenchido automaticamente",
                    name,
                )
                continue
            fallback = default_for_parameter(name)
            if mutable_dataset is not None:
                mutable_dataset[name] = fallback
            logger.warning(
                "[ReportBro] Dados em falta para o parâmetro %s; a usar valor por omissão %r",
                name,
                fallback,
            )

    for warning in warnings or []:
        field = warning.get("field")
        reason = warning.get("reason")
        original = warning.get("original")
        normalised = warning.get("normalised")
        if not field or not reason:
            continue
        logger.warning(
            "[ReportBro] Valor normalizado para %s: %r → %r (%s)",
            field,
            original,
            normalised,
            reason,
        )


def generate_ft_gestao_reportbro_pdf(
    product: Product,
    *,
    template_path: str | Path | None = None,
    destination: Path | None = None,
    parent: QWidget | None = None,
    locale: Any | None = None,
    food_cost_levels: Iterable[Any] | None = None,
) -> Path | None:
    """Generate the Gestão PDF using the ReportBro template pipeline."""

    product_obj = _validate_product(product)
    payload = _prepare_management_payload(
        product_obj, locale=locale, food_cost_levels=food_cost_levels
    )
    dataset = build_reportbro_context(payload)

    template_location = _resolve_reportbro_template_location(template_path)
    template = load_template_definition(template_location, dataset=dataset)

    reportbro_metadata = payload.get("reportbro", {}) if isinstance(payload, Mapping) else {}
    warnings = (
        reportbro_metadata.get("warnings")
        if isinstance(reportbro_metadata, Mapping)
        else []
    )
    _validate_reportbro_inputs(template, dataset, warnings)

    if destination is None:
        destination = _prompt_pdf_destination(product_obj, parent=parent)

    destination = Path(destination)
    debug_enabled = _should_enable_reportbro_debug()
    if debug_enabled:
        logger.debug("[ReportBro] Modo debug ativo para geração de PDF")

    render_pdf_to_path(template, dataset, destination, debug=debug_enabled)
    logger.info(
        "[ReportBro] FT Gestão criada com sucesso em %s usando template %s",
        destination,
        template_location,
    )
    return destination


def _resolve_reportbro_template_location(
    template_path: str | Path | None,
) -> Path:
    """Resolve the template path, falling back to the template store if needed."""

    if template_path:
        candidate = Path(template_path)
        if candidate.exists():
            return candidate
        message = (
            "Não foi possível encontrar o template ReportBro solicitado em "
            f"{candidate}."
        )
        logger.error("[ReportBro] %s", message)
        raise FileNotFoundError(message)

    runtime_template = _DEFAULT_REPORTBRO_TEMPLATE
    if runtime_template.exists():
        return runtime_template

    store_template = _REPORTBRO_STORE_TEMPLATE_DIR / _DEFAULT_REPORTBRO_TEMPLATE_NAME
    if store_template.exists():
        logger.debug(
            "[ReportBro] Template %s não encontrado em %s, a usar store %s",
            _DEFAULT_REPORTBRO_TEMPLATE_NAME,
            runtime_template.parent,
            store_template,
        )
        return store_template

    message = (
        "Não foi possível localizar o template ReportBro "
        f"'{_DEFAULT_REPORTBRO_TEMPLATE_NAME}'. "
        "Confirme se o ficheiro existe em "
        f"{runtime_template.parent} ou {store_template.parent}."
    )
    logger.error("[ReportBro] %s", message)
    raise FileNotFoundError(message)


def _validate_product(product: Product) -> Product:
    if not isinstance(product, Product):
        raise TypeError("product must be an instance of domain.models.Product")

    ingredients = getattr(product, "ingredients", None)
    if ingredients is None:
        product.ingredients = []
    elif not isinstance(ingredients, IterableABC):
        raise TypeError("product.ingredients must be an iterable")
    return product


def _normalise_mapping(record: Any) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        return {}
    return {str(key).lower(): value for key, value in record.items() if isinstance(key, str)}


def _normalise_rows(rows: Iterable[Any]) -> list[dict[str, Any]]:
    normalised: list[dict[str, Any]] = []
    for row in rows or []:
        normalised.append(_normalise_mapping(row))
    return normalised


def _build_produtos_fallback(product: Product) -> dict[str, Any]:
    fallback: dict[str, Any] = {}
    if product.code:
        fallback["codigo"] = product.code
    if product.name:
        fallback["produto"] = product.name
    if product.familia:
        fallback["familia"] = product.familia
    if product.subfamilia:
        fallback["subfamilia"] = product.subfamilia
    if product.tipo_artigo_cod is not None:
        fallback["tipoartigo"] = product.tipo_artigo_cod
    if product.validade_cod is not None:
        fallback["validade"] = product.validade_cod
    if product.temperatura_cod is not None:
        fallback["temperatura"] = product.temperatura_cod
    return fallback


def _is_missing_price(value: Any) -> bool:
    if value in (None, ""):
        return True
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return True
        value = parse_decimal(stripped)
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


def _build_precos_fallback(product: Product) -> dict[str, Any]:
    fallback: dict[str, Any] = {}
    if product.code:
        fallback["codigo"] = product.code
    if product.name:
        fallback["nomeprodvenda"] = product.name
    if product.familia:
        fallback["familia"] = product.familia
    if product.subfamilia:
        fallback["subfamilia"] = product.subfamilia

    pvps = list(getattr(product, "pvps", []) or [])
    for idx in range(1, 6):
        try:
            price = pvps[idx - 1]
        except IndexError:
            price = None
        if _is_missing_price(price):
            continue
        fallback[f"preco{idx}"] = price

    iva = getattr(product, "iva", None)
    if iva not in (None, ""):
        fallback["iva1"] = iva

    return fallback


def _build_ficha_fallback(
    product: Product, ingredient_rows: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    fallback: dict[str, Any] = {}
    if product.code:
        fallback["produtocodigo"] = product.code
    if product.name:
        fallback["produtonome"] = product.name

    familia = product.familia or ""
    subfamilia = product.subfamilia or ""
    if familia and subfamilia:
        fallback["familiasubfamilia"] = f"{familia}>{subfamilia}"
    elif familia or subfamilia:
        fallback["familiasubfamilia"] = familia or subfamilia

    ingredient_list = list(ingredient_rows or [])
    if ingredient_list:
        first = ingredient_list[0]
        name = first.get("nome")
        if name:
            fallback["componentenome"] = name
        code = first.get("codigo")
        if code:
            fallback["componentecodigo"] = code
        for src_key, dst_key in [
            ("quantidade", "qtd"),
            ("unidade", "unidade"),
            ("ppu", "ppu"),
            ("total", "preco"),
            ("peso", "peso"),
            ("ordem", "ordem"),
        ]:
            if first.get(src_key) not in (None, ""):
                fallback[dst_key] = first.get(src_key)

    return fallback


def _coerce_text_value(value: Any) -> tuple[str | None, str | None]:
    if value is None:
        return None, "missing-text"
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d"), None
    text = str(value).strip()
    if not text:
        return None, "missing-text"
    return text, None


def _parse_date_string(value: str) -> date | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    if not any(ch.isdigit() for ch in cleaned):
        return None

    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        parsed = None
    if parsed is not None:
        return parsed.date()

    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            parsed_dt = datetime.strptime(cleaned, pattern)
        except ValueError:
            continue
        return parsed_dt.date()

    return None


def _normalise_date_value(value: Any) -> tuple[str, str | None]:
    if value is None:
        return "", "missing-date"
    if isinstance(value, datetime):
        return value.date().isoformat(), None
    if isinstance(value, date):
        return value.isoformat(), None
    text = str(value).strip()
    if not text:
        return "", "missing-date"
    parsed = _parse_date_string(text)
    if parsed is None:
        # Preserve text that clearly isn't a date (e.g. "Sim")
        if not any(ch.isdigit() for ch in text):
            return text, None
        return "", "invalid-date"
    return parsed.isoformat(), None


def _coerce_number_value(
    value: Any, numeric_type: str | None
) -> tuple[int | float | None, str | None]:
    if value in (None, ""):
        return None, "missing-number"

    if isinstance(value, bool):
        value = int(value)

    if isinstance(value, (int, float)):
        number = float(value)
    else:
        candidate = value
        if isinstance(candidate, str):
            candidate = parse_decimal(candidate)
        try:
            number = float(candidate)
        except (TypeError, ValueError):
            number = None

    if number is None:
        return None, "invalid-number"

    if numeric_type == "int":
        try:
            return int(round(number)), None
        except (TypeError, ValueError):
            return None, "invalid-number"

    return float(number), None


def _build_reportbro_parameters(
    product: Product,
    ingredient_rows: Iterable[Mapping[str, Any]],
    *,
    raw_produtos: Mapping[str, Any] | None = None,
    raw_fichas: Iterable[Mapping[str, Any]] | None = None,
    raw_precos: Mapping[str, Any] | None = None,
    raw_tipos_artigos: Mapping[str, Any] | None = None,
    raw_validade: Mapping[str, Any] | None = None,
    raw_temperaturas: Mapping[str, Any] | None = None,
    raw_preparacao: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    produtos = _build_produtos_fallback(product)
    produtos.update(_normalise_mapping(raw_produtos))

    precos = _build_precos_fallback(product)
    precos.update(_normalise_mapping(raw_precos))

    fichas_normalised = _normalise_rows(raw_fichas or [])
    ficha_base = _build_ficha_fallback(product, ingredient_rows)
    if fichas_normalised:
        ficha_base.update(fichas_normalised[0])

    tipos_artigos = {}
    if product.tipo_artigo_cod is not None:
        tipos_artigos["cod"] = product.tipo_artigo_cod
    tipos_artigos.update(_normalise_mapping(raw_tipos_artigos))

    validade = {}
    if product.validade_cod is not None:
        validade["cod"] = product.validade_cod
    validade.update(_normalise_mapping(raw_validade))

    temperaturas = {}
    if product.temperatura_cod is not None:
        temperaturas["cod"] = product.temperatura_cod
    temperaturas.update(_normalise_mapping(raw_temperaturas))

    preparacao = {}
    if product.code:
        preparacao["produtocodigo"] = product.code
    preparacao.update(_normalise_mapping(raw_preparacao))

    dataset_section = {
        "product_tipo_artigo_cod": (
            tipos_artigos.get("descricao")
            or tipos_artigos.get("cod")
            or getattr(product, "tipo_artigo_cod", None)
        ),
        "product_validade_cod": (
            validade.get("descricao")
            or validade.get("cod")
            or getattr(product, "validade_cod", None)
        ),
        "product_temperatura_cod": (
            temperaturas.get("descricao")
            or temperaturas.get("cod")
            or getattr(product, "temperatura_cod", None)
        ),
    }

    parameters: dict[str, Any] = {}
    warnings: list[dict[str, Any]] = []

    section_map: dict[str, Mapping[str, Any]] = {
        "produtos": produtos,
        "fichas_tecnicas": ficha_base,
        "precos_taxas": precos,
        "tipos_artigos": tipos_artigos,
        "validade": validade,
        "temperaturas": temperaturas,
        "produto_preparacao": preparacao,
        "dataset": dataset_section,
    }

    for name, meta in FT_GESTAO_PARAMETER_DEFINITIONS.items():
        section = meta.get("section")
        field = meta.get("field")
        record = section_map.get(section, {})
        raw_value = record.get(field) if isinstance(record, Mapping) else None

        if meta.get("format") == "date":
            coerced, reason = _normalise_date_value(raw_value)
        elif meta.get("type") == "number":
            coerced, reason = _coerce_number_value(raw_value, meta.get("numeric_type"))
        else:
            coerced, reason = _coerce_text_value(raw_value)

        if name.startswith("FoodCost_Nivel") and reason == "missing-text":
            coerced = default_for_parameter(name)
            reason = None

        parameters[name] = coerced
        if reason:
            warnings.append(
                {
                    "field": name,
                    "original": raw_value,
                    "normalised": coerced,
                    "reason": reason,
                }
            )

    legacy_numeric_aliases = {
        "Produtos_TipoArtigo": (tipos_artigos.get("cod"), "int"),
        "Produtos_Validade": (validade.get("cod"), "int"),
        "Produtos_Temperatura": (temperaturas.get("cod"), "int"),
    }
    for alias, (source_value, numeric_type) in legacy_numeric_aliases.items():
        coerced, reason = _coerce_number_value(source_value, numeric_type)
        parameters[alias] = coerced
        if reason:
            warnings.append(
                {
                    "field": alias,
                    "original": source_value,
                    "normalised": coerced,
                    "reason": reason,
                }
            )

    for name in FT_GESTAO_PARAMETER_DEFINITIONS:
        parameters.setdefault(name, default_for_parameter(name))

    return parameters, warnings


_MISSING_CODE_WARNING = (
    "[ReportBro] Produtos_Codigo em falta; 'product_image_filename' não foi definido."
)
_MISSING_FILE_WARNING = (
    "[ReportBro] Imagem de produto inexistente para Produtos_Codigo %s em %s"
)


def resolve_product_image(
    payload: MutableMappingABC[str, Any] | Mapping[str, Any],
    *,
    parameters: MutableMappingABC[str, Any] | Mapping[str, Any] | None = None,
    check_exists: bool = True,
) -> str | None:
    """Populate ``product_image_filename`` in ``payload`` based on ``Produtos_Codigo``.

    When the product code is missing or the image file is unavailable the
    function points ``product_image_filename``/``product_image_uri`` to the
    shared ``ui/no-image-thumb.png`` placeholder while keeping the warning log.
    """

    params: Mapping[str, Any] | None = parameters
    if params is None and isinstance(payload, Mapping):
        reportbro_section = payload.get("reportbro")
        if isinstance(reportbro_section, Mapping):
            maybe_params = reportbro_section.get("parameters")
            if isinstance(maybe_params, Mapping):
                params = maybe_params

    code_value = None
    if isinstance(params, Mapping):
        code_value = params.get("Produtos_Codigo")

    code = str(code_value).strip() if code_value is not None else ""
    root = get_project_root()
    fallback_path = root / "ui" / "no-image-thumb.png"

    def _path_to_uri(path: Path) -> str:
        try:
            return path.as_uri()
        except ValueError:
            return path.resolve(strict=False).as_uri()

    filename: str | None = None
    uri: str | None = None
    fallback_filename = str(fallback_path)
    fallback_uri = _path_to_uri(fallback_path)
    if not code:
        logger.warning(_MISSING_CODE_WARNING)
        filename = fallback_filename
        uri = fallback_uri
    else:
        candidate = root / "databases" / "images" / f"{code}.png"
        if check_exists and not candidate.exists():
            logger.warning(_MISSING_FILE_WARNING, code, candidate)
            filename = fallback_filename
            uri = fallback_uri
        else:
            filename = str(candidate)
            uri = _path_to_uri(candidate)

    targets: list[str] = []
    has_image = filename is not None

    def _apply_target(target: MutableMappingABC[str, Any], label: str) -> None:
        if has_image:
            target["product_image_filename"] = filename
            if uri is None:
                target.pop("product_image_uri", None)
            else:
                target["product_image_uri"] = uri
        else:
            target.pop("product_image_filename", None)
            target.pop("product_image_uri", None)
        targets.append(label)

    if isinstance(payload, MutableMappingABC):
        _apply_target(payload, "payload")

    target_parameters: MutableMappingABC[str, Any] | None = None
    if isinstance(parameters, MutableMappingABC):
        target_parameters = parameters
    elif isinstance(params, MutableMappingABC):
        target_parameters = params

    if target_parameters is not None:
        _apply_target(target_parameters, "parameters")

    destination = "+".join(sorted(set(targets))) or "none"
    logger.info(
        "[ReportBro] product_image_filename resolvido: Produtos_Codigo=%r normalizado=%r caminho=%r uri=%r destino=%s",
        code_value,
        code,
        filename,
        uri,
        destination,
    )

    return filename


def _prepare_management_payload(
    product: Product,
    *,
    locale: Any | None = None,
    food_cost_levels: Iterable[Any] | None = None,
) -> dict[str, Any]:
    code = getattr(product, "code", None)
    name = getattr(product, "name", None)
    identifier = code or name or "<desconhecido>"
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

    serialised_levels = _serialise_food_cost_levels(food_cost_levels)

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
            "image_path": "",
        },
        "B2": {
            "ingredientes": ing_data,
            "totais": totals,
        },
        "B3": {
            "pvps": pvps_serialised,
            "iva": iva_serialised,
            "food_cost": food_cost,
            "food_cost_levels": serialised_levels,
        },
    }

    reportbro_params, reportbro_warnings = _build_reportbro_parameters(
        product,
        ing_data,
        raw_produtos=getattr(product, "produtos_row", None),
        raw_fichas=getattr(product, "fichas_tecnicas_rows", None),
        raw_precos=getattr(product, "precos_taxas_row", None),
        raw_tipos_artigos=getattr(product, "tipos_artigos_row", None),
        raw_validade=getattr(product, "validade_row", None),
        raw_temperaturas=getattr(product, "temperaturas_row", None),
        raw_preparacao=getattr(product, "produto_preparacao_row", None),
    )
    currency_context = _set_currency_context(locale)

    grafico_foodcost_filename = ""
    try:
        grafico_foodcost_filename = gerar_grafico_foodcost_pie(ing_data)
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("[Print] Falha ao gerar gráfico de food cost")
        grafico_foodcost_filename = ""
    reportbro_params["GraficoFoodCost_Filename"] = grafico_foodcost_filename

    payload = {
        "identifier": identifier,
        "generated_at": generated_at,
        "page_title": "Ficha Técnica de Gestão",
        "blocks": blocks,
        "reportbro": {
            "parameters": reportbro_params,
            "warnings": reportbro_warnings,
        },
        "currency": dict(currency_context),
        "currency_symbol": currency_context.get("currency_symbol"),
        "currency_code": currency_context.get("currency_code"),
        "locale_code": currency_context.get("locale_code"),
        "GraficoFoodCost_Filename": grafico_foodcost_filename,
    }

    image_filename = resolve_product_image(payload, parameters=reportbro_params)
    blocks["B1"]["image_path"] = image_filename or ""
    return payload


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


def _serialise_food_cost_levels(
    levels: Iterable[Any] | None,
) -> list[dict[str, float]]:
    serialised: list[dict[str, float]] = []

    def _extract_mapping(entry: Mapping[str, Any]) -> tuple[Any, Any, Any]:
        name = (
            entry.get("name")
            or entry.get("Nome")
            or entry.get("nome")
            or entry.get("level")
        )
        minimum = (
            entry.get("min")
            if entry.get("min") is not None
            else entry.get("valor_min")
        )
        if minimum is None:
            minimum = entry.get("ValorMin")
        maximum = (
            entry.get("max")
            if entry.get("max") is not None
            else entry.get("valor_max")
        )
        if maximum is None:
            maximum = entry.get("ValorMax")
        return name, minimum, maximum

    for entry in levels or []:
        raw_name: Any
        raw_min: Any
        raw_max: Any
        if isinstance(entry, Mapping):
            raw_name, raw_min, raw_max = _extract_mapping(entry)
        else:
            try:
                raw_name = entry[1]
                raw_min = entry[2]
                raw_max = entry[3]
            except (TypeError, IndexError):
                continue

        min_value = _safe_float(raw_min)
        max_value = _safe_float(raw_max)
        if not raw_name or min_value is None or max_value is None:
            continue

        serialised.append(
            {
                "name": str(raw_name),
                "min": float(min_value),
                "max": float(max_value),
            }
        )

    return serialised


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

    _set_currency_context(payload.get("currency"))

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


def _line_spacing(painter: QPainter, font: QFont, *, scale_y: float = 1.0) -> float:
    """Return the line spacing for ``font`` in the painter's coordinate space."""

    if not _QT_AVAILABLE or QFontMetricsF is None:  # pragma: no cover - defensive guard
        raise RuntimeError("PyQt5 is required to measure line spacing")

    painter.save()
    try:
        painter.setFont(font)
        device = painter.device()
        if device is not None:
            metrics = QFontMetricsF(font, device)
        else:  # pragma: no cover - fallback when no device is available
            metrics = QFontMetricsF(font)
        spacing = metrics.lineSpacing()
    finally:
        painter.restore()

    if scale_y:
        return spacing / scale_y
    return spacing


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
    header_height = _line_spacing(painter, header_font, scale_y=scale_y)
    header_rect = QRectF(rect.left(), y, rect.width(), header_height)
    painter.drawText(header_rect, Qt.AlignLeft | Qt.AlignVCenter, title)

    subtitle_font = _scaled_font(12, QFont.Bold, scale_y=scale_y)
    painter.setFont(subtitle_font)
    painter.setPen(QColor("#4a6fa5"))
    sub_height = _line_spacing(painter, subtitle_font, scale_y=scale_y)
    sub_y = y + header_height + 4
    subtitle_rect = QRectF(rect.left(), sub_y, rect.width(), sub_height)
    painter.drawText(subtitle_rect, Qt.AlignLeft | Qt.AlignVCenter, subtitle)

    if generated_at:
        meta_font = _scaled_font(9, scale_y=scale_y)
        painter.setFont(meta_font)
        painter.setPen(QColor("#6b778c"))
        meta_height = _line_spacing(painter, meta_font, scale_y=scale_y)
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
        painter,
        rows,
        title,
        scale_y=scale_y,
        image_height=_B1_IMAGE_BOX_SIZE,
    )
    block_rect = QRectF(rect.left(), rect.top(), rect.width(), block_height)
    _draw_block_background(painter, block_rect)
    inner = block_rect.adjusted(_BLOCK_PADDING, _BLOCK_PADDING, -_BLOCK_PADDING, -_BLOCK_PADDING)

    painter.save()
    title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
    painter.setFont(title_font)
    painter.setPen(QColor("#253858"))
    title_height = _line_spacing(painter, title_font, scale_y=scale_y)
    title_rect = QRectF(inner.left(), inner.top(), inner.width(), title_height)
    painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, title)

    label_font = _scaled_font(10, QFont.Bold, scale_y=scale_y)
    value_font = _scaled_font(10, scale_y=scale_y)
    label_color = QColor("#6b778c")
    value_color = QColor("#172b4d")
    painter.setFont(label_font)
    label_height = _line_spacing(painter, label_font, scale_y=scale_y)
    painter.setFont(value_font)
    value_height = _line_spacing(painter, value_font, scale_y=scale_y)
    line_height = max(label_height, value_height)
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
    block_height = _estimate_table_block_height(
        painter, len(ingredientes), scale_y=scale_y
    )
    block_rect = QRectF(rect.left(), rect.top(), rect.width(), block_height)
    _draw_block_background(painter, block_rect)
    inner = block_rect.adjusted(_BLOCK_PADDING, _BLOCK_PADDING, -_BLOCK_PADDING, -_BLOCK_PADDING)

    painter.save()
    title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
    painter.setFont(title_font)
    painter.setPen(QColor("#253858"))
    title_height = _line_spacing(painter, title_font, scale_y=scale_y)
    title_rect = QRectF(inner.left(), inner.top(), inner.width(), title_height)
    painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, title)

    table_top = title_rect.bottom() + 16
    table_rect = QRectF(inner.left(), table_top, inner.width(), _table_height(len(ingredientes)))
    _draw_ingredient_table(painter, table_rect, ingredientes, scale_y=scale_y)

    totals_font = _scaled_font(10, QFont.Bold, scale_y=scale_y)
    painter.setFont(totals_font)
    painter.setPen(QColor("#253858"))
    totals_height = _line_spacing(painter, totals_font, scale_y=scale_y)
    totals_y = table_rect.bottom() + 16
    totals_rows = [
        ("Custo Total", totals.get("custo_total")),
        ("Peso Total", totals.get("peso_total")),
        ("N.º Ingredientes", totals.get("num_ingredientes")),
    ]
    value_font = _scaled_font(10, scale_y=scale_y)
    painter.setFont(value_font)
    value_color = QColor("#42526e")
    value_height = _line_spacing(painter, value_font, scale_y=scale_y)

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

    max_slots = 5
    pvp_row: list[tuple[str, Any]] = []
    food_row: list[tuple[str, Any]] = []
    for idx in range(max_slots):
        pvp_value = pvps[idx] if idx < len(pvps) else None
        pvp_row.append((f"PVP{idx + 1}", pvp_value))

        fc_value = fcs[idx] if idx < len(fcs) else None
        food_row.append((f"Food Cost {idx + 1}", fc_value))

    block_height = _estimate_food_cost_height(painter, scale_y=scale_y)
    block_rect = QRectF(rect.left(), rect.top(), rect.width(), block_height)
    _draw_block_background(painter, block_rect)
    inner = block_rect.adjusted(_BLOCK_PADDING, _BLOCK_PADDING, -_BLOCK_PADDING, -_BLOCK_PADDING)

    painter.save()
    title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
    painter.setFont(title_font)
    painter.setPen(QColor("#253858"))
    title_height = _line_spacing(painter, title_font, scale_y=scale_y)
    title_rect = QRectF(inner.left(), inner.top(), inner.width(), title_height)
    painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, title)

    meta_font = _scaled_font(10, QFont.Bold, scale_y=scale_y)
    painter.setFont(meta_font)
    painter.setPen(QColor("#4a6fa5"))
    meta_height = _line_spacing(painter, meta_font, scale_y=scale_y)
    meta_rect = QRectF(
        inner.left(),
        title_rect.bottom() + 12,
        inner.width(),
        meta_height,
    )
    painter.drawText(
        meta_rect,
        Qt.AlignLeft | Qt.AlignVCenter,
        f"IVA: {_format_percentage(iva)}",
    )

    rows_top = meta_rect.bottom() + 12
    table_height = 2 * _FOOD_ROW_HEIGHT + _FOOD_ROW_GAP
    table_rect = QRectF(inner.left(), rows_top, inner.width(), table_height)
    _draw_food_cost_grid(
        painter,
        table_rect,
        pvp_row,
        food_row,
        food_cost_levels=data.get("food_cost_levels"),
        scale_y=scale_y,
    )

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


def _draw_food_cost_grid(
    painter: QPainter,
    rect: QRectF,
    pvp_columns: list[tuple[str, Any]],
    food_columns: list[tuple[str, Any]],
    *,
    food_cost_levels: Iterable[Any] | None = None,
    scale_y: float = 1.0,
) -> None:
    painter.save()
    grid_color = QColor("#4a6fa5")
    label_color = QColor("#2c3e66")
    value_color = QColor("#172b4d")
    grid_pen = QPen(grid_color)
    grid_pen.setWidthF(0.8)
    grid_pen.setCosmetic(True)

    label_font = _scaled_font(10, QFont.Bold, scale_y=scale_y)
    value_font = _scaled_font(10, scale_y=scale_y)

    total_columns = max(len(pvp_columns), len(food_columns), 1)
    column_width = rect.width() / float(total_columns)

    palette: dict[str, QColor] = {}
    for name, rgb in FOOD_COST_LEVEL_RGB_MAP.items():
        if not isinstance(rgb, IterableABC):
            continue
        components = tuple(rgb)
        if len(components) != 3:
            continue
        palette[name] = QColor(*components)
    neutral_color = palette.get("Todos", value_color)
    normalised_levels = _serialise_food_cost_levels(food_cost_levels)

    def _resolve_food_cost_colour(raw_value: Any) -> QColor:
        numeric = _safe_float(raw_value)
        if numeric is None:
            return neutral_color
        for entry in normalised_levels:
            lower = entry.get("min")
            upper = entry.get("max")
            if lower is None or upper is None:
                continue
            if lower <= float(numeric) <= upper:
                colour = palette.get(entry.get("name"))
                if colour is not None:
                    return colour
                break
        return neutral_color

    def _draw_row(entries: list[tuple[str, Any]], top: float, *, percentage: bool = False) -> None:
        for column, (label, raw_value) in enumerate(entries):
            left = rect.left() + column * column_width
            cell_rect = QRectF(left, top, column_width, _FOOD_ROW_HEIGHT)
            painter.setPen(grid_pen)
            painter.drawRect(cell_rect)

            label_rect = QRectF(left + 6, top, column_width - 12, _FOOD_ROW_HEIGHT / 2)
            value_rect = QRectF(
                left + 6,
                top + _FOOD_ROW_HEIGHT / 2,
                column_width - 12,
                _FOOD_ROW_HEIGHT / 2,
            )

            painter.setFont(label_font)
            painter.setPen(label_color)
            painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter, label)

            painter.setFont(value_font)
            highlight_color = None
            if percentage:
                highlight_color = _resolve_food_cost_colour(raw_value)
                painter.fillRect(value_rect, highlight_color)
            painter.setPen(value_color)
            formatted = (
                _format_percentage(raw_value)
                if percentage
                else _format_currency(raw_value)
            )
            painter.drawText(value_rect, Qt.AlignLeft | Qt.AlignVCenter, formatted)

        for column in range(len(entries), total_columns):
            left = rect.left() + column * column_width
            cell_rect = QRectF(left, top, column_width, _FOOD_ROW_HEIGHT)
            painter.setPen(grid_pen)
            painter.drawRect(cell_rect)

    pvp_entries = pvp_columns or [("PVP1", None)]
    food_entries = food_columns or [("Food Cost 1", None)]

    current_top = rect.top()
    _draw_row(pvp_entries, current_top, percentage=False)
    current_top += _FOOD_ROW_HEIGHT + _FOOD_ROW_GAP
    _draw_row(food_entries, current_top, percentage=True)

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
    painter: QPainter,
    rows: Iterable[tuple[str, Any]],
    title: str,
    *,
    scale_y: float = 1.0,
    image_height: float | None = None,
) -> float:
    painter.save()
    try:
        base = 2 * _BLOCK_PADDING
        title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
        title_height = _line_spacing(painter, title_font, scale_y=scale_y)
        base += title_height + 12

        value_font = _scaled_font(10, scale_y=scale_y)
        value_height = _line_spacing(painter, value_font, scale_y=scale_y)
        for _ in rows:
            base += value_height + 8

        if image_height is not None:
            base = max(base, 2 * _BLOCK_PADDING + title_height + 12 + image_height)
    finally:
        painter.restore()
    return base


def _estimate_table_block_height(
    painter: QPainter, num_rows: int, *, scale_y: float = 1.0
) -> float:
    painter.save()
    try:
        base = 2 * _BLOCK_PADDING
        title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
        title_height = _line_spacing(painter, title_font, scale_y=scale_y)
        base += title_height + 16
        base += _table_height(num_rows)
        totals_font = _scaled_font(10, scale_y=scale_y)
        totals_height = _line_spacing(painter, totals_font, scale_y=scale_y)
        base += 3 * (totals_height + 6) + 10
    finally:
        painter.restore()
    return base


def _estimate_food_cost_height(painter: QPainter, *, scale_y: float = 1.0) -> float:
    painter.save()
    try:
        base = 2 * _BLOCK_PADDING
        title_font = _scaled_font(16, QFont.Bold, scale_y=scale_y)
        base += _line_spacing(painter, title_font, scale_y=scale_y) + 12
        meta_font = _scaled_font(10, QFont.Bold, scale_y=scale_y)
        base += _line_spacing(painter, meta_font, scale_y=scale_y) + 12
        base += 2 * _FOOD_ROW_HEIGHT + _FOOD_ROW_GAP
    finally:
        painter.restore()
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


def _format_currency(value: Any, currency: Mapping[str, Any] | None = None) -> str:
    if value in (None, ""):
        return "—"
    numeric = _safe_float(value)
    if numeric is None:
        return str(value)
    context = currency or _CURRENCY_CONTEXT
    return format_currency_locale(
        numeric,
        locale_code=context.get("locale_code"),
        currency_symbol=context.get("currency_symbol"),
        currency_code=context.get("currency_code"),
    )


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
_FOOD_ROW_GAP = 12.0
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

def _should_enable_reportbro_debug() -> bool:
    env_value = os.getenv("FTV_REPORTBRO_DEBUG")
    if env_value is not None:
        normalised = env_value.strip().lower()
        if normalised in {"", "0", "false", "no", "off"}:
            return False
        return True
    return logger.isEnabledFor(logging.DEBUG)

