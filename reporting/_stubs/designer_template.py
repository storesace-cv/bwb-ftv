"""Helpers that emulate ReportBro Designer's JSON sanitisation."""

from __future__ import annotations

from typing import Any, Iterable, MutableMapping

_ALLOWED_PARAMETER_KEYS: tuple[str, ...] = (
    "id",
    "name",
    "type",
    "arrayItemType",
    "eval",
    "nullable",
    "pattern",
    "expression",
    "showOnlyNameType",
    "testData",
    "testDataBoolean",
    "testDataImage",
    "testDataImageFilename",
    "testDataRichText",
)


def sanitise_template_in_place(template: MutableMapping[str, Any] | None) -> None:
    """Strip fields that are ignored by the official Designer."""

    if not isinstance(template, MutableMapping):
        return

    parameters = template.get("parameters")
    if not isinstance(parameters, Iterable):
        return

    cleaned: list[dict[str, Any]] = []
    for parameter in parameters:
        if not isinstance(parameter, MutableMapping):
            continue
        sanitised = {
            key: parameter[key]
            for key in _ALLOWED_PARAMETER_KEYS
            if key in parameter
        }
        if sanitised:
            cleaned.append(sanitised)

    template["parameters"] = cleaned


__all__ = ["sanitise_template_in_place"]
