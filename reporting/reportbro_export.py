"""Utilities to render ReportBro templates from Python."""

from __future__ import annotations

import json
import logging
import numbers
import os
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping

try:  # pragma: no cover - exercised only when the dependency is available
    from reportbro import Report, ReportBroError
except ModuleNotFoundError:  # pragma: no cover - fallback used in CI and dev without reportbro-lib
    from ._stubs.reportbro import Report, ReportBroError

from .reportbro_normalizer import normalise_template
from .ft_gestao import (
    EMPTY_FIELD,
    _format_currency,
    _format_ingredient_quantity,
    _format_optional,
    set_currency_context,
)
from utils.formatting import parse_decimal

logger = logging.getLogger(__name__)


def _coerce_numeric(value: Any) -> float | None:
    """Convert *value* to a numeric ``float`` when possible."""

    if value is None:
        return None

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, numbers.Number):
        return float(value)

    candidate = parse_decimal(value)
    if isinstance(candidate, numbers.Number):
        return float(candidate)

    try:
        return float(candidate)
    except (TypeError, ValueError):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


def _reportbro_sum(values: Any) -> float:
    """Return the sum of numeric *values* ignoring ``None`` or invalid entries."""

    numeric = _coerce_numeric(values)
    if numeric is not None:
        return numeric

    if isinstance(values, Mapping):
        iterable = values.values()
    else:
        iterable = values

    total = 0.0
    if isinstance(iterable, Iterable) and not isinstance(iterable, (str, bytes, bytearray)):
        for entry in iterable:
            coerced = _coerce_numeric(entry)
            if coerced is not None:
                total += coerced
        return total

    return 0.0


_REPORTBRO_CUSTOM_FUNCTIONS = {"sum": _reportbro_sum}


def _is_feature_enabled(env_var: str) -> bool:
    value = os.getenv(env_var)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


_ENABLE_DOCUMENT_DIMENSION_NORMALISATION = _is_feature_enabled(
    "REPORTBRO_ENABLE_DOCUMENT_DIMENSION_NORMALISATION"
)


class ReportBroIntegrationError(RuntimeError):
    """Base exception for ReportBro integration issues."""


class ReportBroTemplateError(ReportBroIntegrationError):
    """Raised when a ReportBro template cannot be loaded or parsed."""


class ReportBroRenderError(ReportBroIntegrationError):
    """Raised when ReportBro fails to render the requested output."""


def _extract_currency_metadata(data: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    symbol: str | None = None
    code: str | None = None
    locale: str | None = None

    def _collect_from(source: Mapping[str, Any]) -> None:
        nonlocal symbol, code, locale
        candidate_symbol = source.get("currency_symbol") or source.get("symbol")
        if isinstance(candidate_symbol, str) and not symbol:
            stripped = candidate_symbol.strip()
            if stripped:
                symbol = stripped

        candidate_code = source.get("currency_code") or source.get("currency")
        if isinstance(candidate_code, str) and not code:
            stripped = candidate_code.strip()
            if stripped:
                code = stripped

        candidate_locale = (
            source.get("locale_code")
            or source.get("format")
            or source.get("fmt")
        )
        if isinstance(candidate_locale, str) and not locale:
            stripped = candidate_locale.strip()
            if stripped:
                locale = stripped

    if isinstance(data, Mapping):
        _collect_from(data)
        nested_currency = data.get("currency")
        if isinstance(nested_currency, Mapping):
            _collect_from(nested_currency)

    return symbol, code, locale


def _apply_currency_overrides(
    template: Mapping[str, Any],
    dataset: Mapping[str, Any] | None,
) -> None:
    if not isinstance(template, Mapping) or not isinstance(dataset, Mapping):
        return

    document_properties = template.get("documentProperties")
    if not isinstance(document_properties, dict):
        return

    symbol, code, locale = _extract_currency_metadata(dataset)
    replacement = symbol or code
    if replacement:
        document_properties["patternCurrencySymbol"] = replacement
    if locale:
        document_properties["patternLocale"] = locale


_COLOR_KEYS = {"backgroundColor", "cs_backgroundColor"}


def _apply_color_parameter_overrides(
    template: Mapping[str, Any],
    dataset: Mapping[str, Any] | None,
) -> None:
    """Replace color placeholders with concrete dataset values."""

    if not isinstance(template, Mapping) or not isinstance(dataset, Mapping):
        return

    def _resolve(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                if isinstance(value, str) and key in _COLOR_KEYS:
                    text = value.strip()
                    if text.startswith("${") and text.endswith("}"):
                        parameter = text[2:-1].strip()
                        replacement = dataset.get(parameter, "")
                        if isinstance(replacement, str):
                            node[key] = replacement.strip()
                        else:
                            node[key] = ""
                _resolve(value)
        elif isinstance(node, Iterable) and not isinstance(node, (str, bytes, bytearray)):
            for item in node:
                _resolve(item)

    _resolve(template.get("docElements"))
    _resolve(template.get("styles"))


def load_template_definition(
    source: str | Path | Mapping[str, Any],
    *,
    dataset: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the ReportBro template definition stored in *source*.

    Parameters
    ----------
    source:
        Either a mapping already containing the template definition or the
        filesystem location of the template JSON file.
    """

    if isinstance(source, Mapping):
        normalised, _ = normalise_template(source)
        _normalise_image_sources(normalised)
        _apply_currency_overrides(normalised, dataset)
        _apply_color_parameter_overrides(normalised, dataset)
        return normalised

    path = Path(source)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:  # pragma: no cover - explicit message
        raise ReportBroTemplateError(f"Template not found at {path}") from exc

    try:
        template = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReportBroTemplateError(
            f"Invalid JSON in ReportBro template {path}: {exc.msg}"
        ) from exc

    if not isinstance(template, dict):
        raise ReportBroTemplateError(
            f"ReportBro template {path} must be a JSON object"
        )

    normalised, _ = normalise_template(template)
    _normalise_image_sources(normalised)
    _apply_currency_overrides(normalised, dataset)
    _apply_color_parameter_overrides(normalised, dataset)
    return normalised


def _format_errors(errors: list[Any]) -> str:
    messages = []
    for error in errors:
        try:
            messages.append(str(error))
        except Exception:  # pragma: no cover - defensive
            messages.append(repr(error))
    return "; ".join(messages)


def _is_invalid_size_error(entry: Any) -> bool:
    if isinstance(entry, Mapping):
        key = entry.get("msg_key")
        if isinstance(key, str) and key == "errorMsgInvalidSize":
            return True
    if isinstance(entry, str) and "errorMsgInvalidSize" in entry:
        return True
    return False


def _initialise_report(
    template: Mapping[str, Any],
    payload: Mapping[str, Any],
    *,
    debug: bool | None,
):
    attempts: list[dict[str, Any]] = []
    if debug is not None:
        attempts.append(
            {
                "debug": debug,
                "custom_functions": dict(_REPORTBRO_CUSTOM_FUNCTIONS),
            }
        )
        attempts.append({"debug": debug})
    attempts.append({"custom_functions": dict(_REPORTBRO_CUSTOM_FUNCTIONS)})
    attempts.append({})

    last_error: TypeError | None = None
    for kwargs in attempts:
        try:
            return Report(template, payload, **kwargs)
        except TypeError as exc:
            message = str(exc)
            if "keyword" not in message:
                raise
            last_error = exc
            continue

    if last_error is not None:
        raise last_error

    return Report(template, payload)


def _ensure_sum_parameter(template: dict[str, Any]) -> None:
    parameters = template.get("parameters")
    if not isinstance(parameters, list):
        return

    for entry in parameters:
        if isinstance(entry, Mapping) and entry.get("name") == "ingredientes_sum_FichasTecnicas_Preco":
            return

    parameters.append(
        {
            "name": "ingredientes_sum_FichasTecnicas_Preco",
            "type": "number",
            "arrayItemType": "string",
            "eval": False,
            "nullable": False,
            "pattern": "",
            "expression": "",
            "showOnlyNameType": False,
            "testData": "",
            "testDataBoolean": False,
            "testDataImage": "",
            "testDataImageFilename": "",
            "testDataRichText": "",
        }
    )


def _replace_sum_expression_targets(template: dict[str, Any]) -> None:
    target = "${sum(ingredientes.FichasTecnicas_Preco)}"
    replacement = "${ingredientes_sum_FichasTecnicas_Preco}"

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            content = node.get("content")
            if isinstance(content, str) and content.strip() == target:
                node["content"] = replacement
                node["eval"] = True
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(template.get("docElements"))


def _render_fallback_pdf(data: Mapping[str, Any]) -> bytes:
    set_currency_context(data.get("currency"))

    try:
        from ._stubs.reportbro import _build_pdf_bytes
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive guard
        raise ReportBroRenderError("ReportBro fallback renderer is unavailable") from exc

    def _coalesce_value(source: Mapping[str, Any], keys: Iterable[str], *, allow_empty: bool = False) -> Any:
        for key in keys:
            if key in source:
                value = source.get(key)
                if allow_empty or _format_optional(value) != EMPTY_FIELD:
                    return value
        return None

    codigo_value = _coalesce_value(data, ("product_codigo", "Produtos_Codigo"))
    nome_value = _coalesce_value(data, ("product_nome", "Produtos_Nome"))
    codigo = _format_optional(codigo_value)
    nome = _format_optional(nome_value)
    ingredientes = list(data.get("ingredientes") or [])
    totals = data.get("totals_data") or data.get("totais_data") or {}

    lines = [
        "Ficha Técnica de Gestão (fallback)",
        f"CÓDIGO: {codigo}",
        f"NOME: {nome}",
        "Ingredientes:",
    ]

    if ingredientes:
        for entry in ingredientes:
            nome_ingrediente = _format_optional(
                _coalesce_value(
                    entry,
                    (
                        "FichasTecnicas_ComponenteNome",
                        "ingrediente",
                        "nome",
                        "codigo",
                    ),
                )
            )
            quantidade = _coalesce_value(
                entry,
                ("FichasTecnicas_Qtd", "quantidade"),
                allow_empty=True,
            )
            unidade = _coalesce_value(
                entry,
                ("FichasTecnicas_Unidade", "um", "unidade"),
                allow_empty=True,
            )
            quantidade_text = _format_ingredient_quantity(quantidade, unidade)
            parts = [nome_ingrediente]
            if quantidade_text != EMPTY_FIELD:
                parts.append(quantidade_text)
            else:
                unit_text = _format_optional(unidade)
                if unit_text != EMPTY_FIELD:
                    parts.append(unit_text)
            line_text = " ".join(str(part).strip() for part in parts if str(part).strip())
            lines.append(f" - {line_text if line_text else EMPTY_FIELD}")
    else:
        lines.append(f" - {EMPTY_FIELD}")

    custo_total = _format_currency(totals.get("custo_total"))
    lines.append(f"Custo total: {custo_total}")

    text = "\n".join(str(line) for line in lines)
    return _build_pdf_bytes(text)


def _normalise_document_properties(template: dict[str, Any]) -> None:
    if "documentProperties" not in template:
        raise ReportBroTemplateError(
            "Template JSON inválido: faltam 'documentProperties'."
        )

    properties = template.get("documentProperties")
    if not isinstance(properties, dict):
        return

    page_format = properties.get("pageFormat")
    if isinstance(page_format, str) and page_format.strip():
        properties["pageFormat"] = page_format.strip()
        return

    page_size = properties.get("pageSize")
    if isinstance(page_size, str) and page_size.strip():
        properties["pageFormat"] = page_size.strip()
    else:
        properties["pageFormat"] = "A4"

    if not _ENABLE_DOCUMENT_DIMENSION_NORMALISATION:
        return

    def _looks_like_point_dimension(value: Any) -> bool:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        return number > 400

    doc_elements = template.get("docElements")
    suspect_point_units = False
    if isinstance(doc_elements, Iterable):
        for element in doc_elements:
            if not isinstance(element, Mapping):
                continue
            if _looks_like_point_dimension(element.get("height")):
                suspect_point_units = True
                break
            content = element.get("contentData")
            if isinstance(content, Mapping) and _looks_like_point_dimension(
                content.get("height")
            ):
                suspect_point_units = True
                break

    unit = properties.get("unit")
    if isinstance(unit, str):
        cleaned_unit = unit.strip().lower()
    else:
        cleaned_unit = ""

    if cleaned_unit == "mm" and suspect_point_units:
        point_to_mm = 25.4 / 72.0
        dimension_keys = {
            "x",
            "y",
            "width",
            "height",
            "paddingLeft",
            "paddingRight",
            "paddingTop",
            "paddingBottom",
            "marginLeft",
            "marginRight",
            "marginTop",
            "marginBottom",
            "pageWidth",
            "pageHeight",
            "headerSize",
            "footerSize",
        }
        always_convert_keys = {
            "marginLeft",
            "marginRight",
            "marginTop",
            "marginBottom",
            "pageWidth",
            "pageHeight",
            "headerSize",
            "footerSize",
        }

        def _convert_entry(mapping: Mapping[str, Any]) -> dict[str, Any]:
            converted: dict[str, Any] = dict(mapping)
            for key in dimension_keys:
                if key in converted:
                    value = converted.get(key)
                    try:
                        number = float(value)
                    except (TypeError, ValueError):
                        continue
                    if key == "height" and number <= 0:
                        converted[key] = 120.0
                        continue
                    if number <= 50 and key not in always_convert_keys:
                        continue
                    converted[key] = round(number * point_to_mm, 3)
            return converted

        if isinstance(properties, Mapping):
            updated_properties = _convert_entry(properties)
            template["documentProperties"] = updated_properties
            properties = updated_properties

        def _convert_node(node: Any) -> Any:
            if isinstance(node, Mapping):
                converted = _convert_entry(node)
                for key, value in list(converted.items()):
                    converted[key] = _convert_node(value)
                return converted
            if isinstance(node, Iterable) and not isinstance(node, (str, bytes, bytearray)):
                return [_convert_node(item) for item in node]
            return node

        template["docElements"] = _convert_node(doc_elements)


def _normalise_parameter_ids(template: dict[str, Any]) -> None:
    parameters = template.get("parameters")
    if not isinstance(parameters, Iterable):
        return

    def _assign_child_ids(children: Iterable[Any]) -> list[dict[str, Any]]:
        normalised_children: list[dict[str, Any]] = []
        for index, child in enumerate(children, start=1):
            if not isinstance(child, Mapping):
                continue

            mutable_child = dict(child)
            raw_child_id = mutable_child.get("id")
            child_id: int | None = None
            if isinstance(raw_child_id, int):
                child_id = raw_child_id
            elif isinstance(raw_child_id, str):
                digits = "".join(ch for ch in raw_child_id if ch.isdigit())
                if digits:
                    try:
                        child_id = int(digits)
                    except ValueError:
                        child_id = None

            if child_id is None:
                child_id = index

            mutable_child["id"] = child_id

            grand_children = mutable_child.get("children")
            if isinstance(grand_children, Iterable) and not isinstance(
                grand_children, (str, bytes, bytearray)
            ):
                mutable_child["children"] = _assign_child_ids(grand_children)

            normalised_children.append(mutable_child)

        return normalised_children

    normalised: list[dict[str, Any]] = []
    for index, parameter in enumerate(parameters, start=1):
        if not isinstance(parameter, Mapping):
            continue

        mutable = dict(parameter)

        raw_id = mutable.get("id")
        assigned: int | None = None
        if isinstance(raw_id, int):
            assigned = raw_id
        elif isinstance(raw_id, str):
            digits = "".join(ch for ch in raw_id if ch.isdigit())
            if digits:
                try:
                    assigned = int(digits)
                except ValueError:
                    assigned = None

        if assigned is None:
            assigned = index

        mutable["id"] = assigned

        children = mutable.get("children")
        if isinstance(children, Iterable) and not isinstance(children, (str, bytes, bytearray)):
            mutable["children"] = _assign_child_ids(children)

        normalised.append(mutable)

    template["parameters"] = normalised


def _ensure_price_parameters_are_strings(template: dict[str, Any]) -> None:
    target_names = {f"PrecosTaxas_Preco{index}_display" for index in range(1, 6)}

    def _convert_parameter(entry: Mapping[str, Any]) -> dict[str, Any]:
        mutable = dict(entry)
        name = mutable.get("name")
        if isinstance(name, str) and name in target_names:
            mutable["type"] = "string"
            if not isinstance(mutable.get("testData"), str):
                mutable["testData"] = ""
        children = mutable.get("children")
        if isinstance(children, Iterable) and not isinstance(children, (str, bytes, bytearray)):
            mutable["children"] = [
                _convert_parameter(child)
                for child in children
                if isinstance(child, Mapping)
            ]
        return mutable

    parameters = template.get("parameters")
    if not isinstance(parameters, Iterable):
        return

    template["parameters"] = [
        _convert_parameter(param)
        for param in parameters
        if isinstance(param, Mapping)
    ]


def _normalise_image_sources(template: dict[str, Any]) -> None:
    parameters = {
        param.get("name"): param
        for param in template.get("parameters", [])
        if isinstance(param, Mapping)
    }

    elements = template.get("docElements")
    if not isinstance(elements, Iterable):
        return

    normalised_elements: list[dict[str, Any]] = []
    for element in elements:
        if not isinstance(element, Mapping):
            continue
        mutable = dict(element)
        if mutable.get("elementType") == "image":
            source = mutable.get("source")
            if isinstance(source, str):
                stripped_source = source.strip()
                if stripped_source.startswith("${") and stripped_source.endswith("}"):
                    pass
                else:
                    lookup_key = stripped_source
                    if lookup_key.startswith("@"):
                        lookup_key = lookup_key.lstrip("@")
                    if lookup_key in parameters and lookup_key:
                        mutable["source"] = f"${{{lookup_key}}}"
                if not stripped_source:
                    image_filename = mutable.get("imageFilename")
                    image_filename_str = (
                        image_filename.strip()
                        if isinstance(image_filename, str)
                        else ""
                    )
                    if (
                        "product_image_uri" in parameters
                        and image_filename_str == "${product_image_filename}"
                    ):
                        mutable["source"] = "${product_image_uri}"
                    elif (
                        image_filename_str.startswith("${")
                        and image_filename_str.endswith("}")
                    ):
                        param_name = image_filename_str[2:-1]
                        if param_name and param_name in parameters:
                            mutable["source"] = image_filename_str
        normalised_elements.append(mutable)

    template["docElements"] = normalised_elements


def _ensure_title_binding(template: dict[str, Any]) -> None:
    elements = template.get("docElements")
    if not isinstance(elements, Iterable):
        return

    for element in elements:
        if not isinstance(element, Mapping):
            continue
        if element.get("elementType") != "text":
            continue
        content = element.get("content")
        if not isinstance(content, str):
            continue
        stripped = content.strip()
        if stripped.startswith("${") and stripped.endswith("}"):
            return
        if stripped.upper() == "FICHA DE ARTIGO":
            element_dict = dict(element)
            element_dict["content"] = "${title}"
            template["docElements"] = [
                element_dict if item is element else dict(item)
                for item in elements
                if isinstance(item, Mapping)
            ]
            return


def _clamp_image_heights(template: dict[str, Any]) -> None:
    elements = template.get("docElements")
    if not isinstance(elements, Iterable):
        return

    capacities: dict[str, float] = {}

    for entry in elements:
        if not isinstance(entry, Mapping):
            continue
        element_type = entry.get("elementType")
        if element_type == "section":
            for key in ("headerData", "contentData", "footerData"):
                block = entry.get(key)
                if not isinstance(block, Mapping):
                    continue
                linked = block.get("linkedContainerId")
                height = block.get("height")
                if isinstance(height, (int, float)) and linked is not None:
                    capacities[str(linked)] = max(capacities.get(str(linked), 0.0), float(height))
        elif element_type == "frame":
            container_id = entry.get("id")
            height = entry.get("height")
            if isinstance(height, (int, float)) and container_id is not None:
                capacities[str(container_id)] = max(capacities.get(str(container_id), 0.0), float(height))

    for entry in elements:
        if not isinstance(entry, Mapping):
            continue
        if entry.get("elementType") != "image":
            continue
        container_id = entry.get("containerId")
        capacity = capacities.get(str(container_id)) if container_id is not None else None
        if capacity is None:
            continue
        try:
            y_value = float(entry.get("y", 0) or 0)
        except (TypeError, ValueError):
            y_value = 0.0
        try:
            height_value = float(entry.get("height", 0) or 0)
        except (TypeError, ValueError):
            height_value = 0.0
        max_height = max(capacity - y_value, 0.0)
        if height_value > max_height:
            entry["height"] = max_height


def _resolve_debug_flag(debug: bool) -> bool:
    """Return whether ReportBro debug mode should be enabled."""

    if debug:
        return True

    env_value = os.getenv("FTV_REPORTBRO_DEBUG")
    if env_value is not None:
        normalised = env_value.strip().lower()
        if normalised in {"", "0", "false", "no", "off"}:
            return False
        return True

    return logger.isEnabledFor(logging.DEBUG)


def render_pdf_bytes(
    template_definition: Mapping[str, Any],
    data: Mapping[str, Any],
    *,
    debug: bool = False,
) -> bytes:
    """Return the PDF bytes rendered from *template_definition* using *data*."""

    template = deepcopy(dict(template_definition))
    _normalise_document_properties(template)
    _ensure_sum_parameter(template)
    _normalise_parameter_ids(template)
    _ensure_price_parameters_are_strings(template)
    _normalise_image_sources(template)
    _ensure_title_binding(template)
    _clamp_image_heights(template)
    _replace_sum_expression_targets(template)

    payload = dict(data)
    _apply_currency_overrides(template, payload)
    resolved_debug = _resolve_debug_flag(debug)

    try:
        report = _initialise_report(template, payload, debug=resolved_debug)
    except AssertionError as exc:  # pragma: no cover - defensive guard
        raise ReportBroTemplateError(f"Invalid template definition: {exc}") from exc

    if report.errors:
        message = _format_errors(report.errors)
        if any(_is_invalid_size_error(error) for error in report.errors):
            logger.warning(
                "[ReportBro] Detetado erro de dimensão inválida; a usar renderer de fallback"
            )
            return _render_fallback_pdf(payload)
        raise ReportBroTemplateError(
            f"Template validation failed with errors: {message or '<sem detalhes>'}"
        )

    try:
        return report.generate_pdf()
    except ReportBroError as exc:
        message = str(exc)
        if "errorMsgInvalidSize" in message:
            logger.warning(
                "[ReportBro] Erro de dimensão inválida durante renderização; fallback ativado"
            )
            return _render_fallback_pdf(payload)
        raise ReportBroRenderError(f"Failed to generate ReportBro PDF: {exc}") from exc


def render_pdf_to_path(
    template_definition: Mapping[str, Any],
    data: Mapping[str, Any],
    destination: Path,
    *,
    debug: bool = False,
) -> Path:
    """Render *template_definition* and write the resulting PDF into *destination*."""

    destination = Path(destination)
    pdf_bytes = render_pdf_bytes(template_definition, data, debug=debug)
    destination.write_bytes(pdf_bytes)
    logger.info("[ReportBro] PDF export completed at %s", destination)
    return destination
