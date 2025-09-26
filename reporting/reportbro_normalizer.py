"""Shared utilities to normalise ReportBro templates before processing."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Tuple


__all__ = [
    "ALLOWED_TEMPLATE_KEYS",
    "normalise_template",
]


ALLOWED_TEMPLATE_KEYS: frozenset[str] = frozenset(
    {
        "docElements",
        "documentProperties",
        "parameters",
        "reportId",
        "styles",
        "version",
        "watermarks",
        "dataSets",
    }
)

_STRING_FIELDS = {
    "backgroundColor",
    "borderColor",
    "content",
    "font",
    "link",
    "pattern",
    "printIf",
    "richTextContent",
    "richTextHtml",
    "textColor",
}

STATIC_SECTION_PARAMETER = "__reportbro_static_section_rows__"

_PARAMETER_TYPE_ALIASES = {
    "text": "string",
    "decimal": "number",
    "float": "number",
}

_CS_STRING_FIELDS = {
    "cs_additionalRules",
    "cs_backgroundColor",
    "cs_borderColor",
    "cs_condition",
    "cs_font",
    "cs_horizontalAlignment",
    "cs_styleId",
    "cs_textColor",
    "cs_verticalAlignment",
}


def _ensure_string(value: Any) -> str:
    """Return *value* as a string, defaulting to ``""`` when empty."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8")
        except Exception:  # pragma: no cover - defensive
            return value.decode("utf-8", errors="ignore")
    return str(value)


def _ensure_style_id(value: Any) -> str:
    """Return *value* coerced to the canonical string style identifier."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "1" if value else ""
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    return _ensure_string(value)


def _normalise_mapping(node: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively normalise *node* converting textual fields to strings."""

    normalised: dict[str, Any] = {}
    for key, value in node.items():
        if isinstance(value, Mapping):
            value = _normalise_mapping(value)
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
            items: list[Any] = []
            for item in value:
                if isinstance(item, Mapping):
                    items.append(_normalise_mapping(item))
                else:
                    items.append(item)
            value = items

        if key in _STRING_FIELDS or key in _CS_STRING_FIELDS:
            value = _ensure_string(value)
        if key == "styleId" or key == "cs_styleId":
            value = _ensure_style_id(value)

        normalised[key] = value

    return normalised


def _normalise_doc_elements(entries: Any) -> tuple[list[dict[str, Any]], set[str]]:
    if not isinstance(entries, Iterable):
        return [], set()

    normalised: list[dict[str, Any]] = []
    static_sources: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue

        element = _normalise_mapping(entry)
        element_type = element.get("elementType")
        if element_type == "section":
            data_source = element.get("dataSource")
            if isinstance(data_source, str):
                cleaned = data_source.strip()
                if cleaned:
                    element["dataSource"] = cleaned
                else:
                    element["dataSource"] = STATIC_SECTION_PARAMETER
                    static_sources.add(STATIC_SECTION_PARAMETER)
        elif element_type == "image":
            if not element.get("horizontalAlignment"):
                element["horizontalAlignment"] = "left"
            if not element.get("verticalAlignment"):
                element["verticalAlignment"] = "top"
        normalised.append(element)

    return normalised, static_sources


def _normalise_parameters(entries: Any) -> list[dict[str, Any]]:
    if not isinstance(entries, Iterable):
        return []

    normalised: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        parameter = _normalise_mapping(entry)
        if "styleId" in parameter:
            parameter["styleId"] = _ensure_style_id(parameter.get("styleId"))
        param_type = parameter.get("type")
        if isinstance(param_type, str):
            normalised_type = _PARAMETER_TYPE_ALIASES.get(param_type.lower())
            if normalised_type:
                parameter["type"] = normalised_type
        normalised.append(parameter)
    return normalised


def _normalise_styles(entries: Any) -> list[dict[str, Any]]:
    if not isinstance(entries, Iterable):
        return []

    normalised: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        style = _normalise_mapping(entry)
        if "id" in style:
            style["id"] = _ensure_style_id(style.get("id"))
        if "styleId" in style:
            style["styleId"] = _ensure_style_id(style.get("styleId"))
        normalised.append(style)
    return normalised


def normalise_template(template: Mapping[str, Any]) -> Tuple[dict[str, Any], dict[str, Any]]:
    """Return the normalised template and the discarded designer metadata."""

    working = dict(template)
    extras: dict[str, Any] = {}

    for key in list(working):
        if key not in ALLOWED_TEMPLATE_KEYS:
            extras[key] = working.pop(key)

    doc_elements, static_sources = _normalise_doc_elements(working.get("docElements"))
    working["docElements"] = doc_elements

    raw_parameters = list(working.get("parameters", []) or [])
    if static_sources:
        existing_names = {
            param.get("name")
            for param in raw_parameters
            if isinstance(param, Mapping)
        }
        if STATIC_SECTION_PARAMETER not in existing_names:
            raw_parameters.append(
                {
                    "name": STATIC_SECTION_PARAMETER,
                    "type": "array",
                    "children": [],
                }
            )

    working["styles"] = _normalise_styles(working.get("styles"))
    working["parameters"] = _normalise_parameters(raw_parameters)

    return working, extras
