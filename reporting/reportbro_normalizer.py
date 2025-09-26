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


def _normalise_doc_elements(entries: Any) -> list[dict[str, Any]]:
    if not isinstance(entries, Iterable):
        return []

    normalised: list[dict[str, Any]] = []
    for entry in entries:
        if isinstance(entry, Mapping):
            normalised.append(_normalise_mapping(entry))
    return normalised


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

    working["docElements"] = _normalise_doc_elements(working.get("docElements"))
    working["styles"] = _normalise_styles(working.get("styles"))
    working["parameters"] = _normalise_parameters(working.get("parameters"))

    return working, extras
