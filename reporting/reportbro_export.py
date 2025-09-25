"""Utilities to render ReportBro templates from Python."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

try:  # pragma: no cover - exercised only when the dependency is available
    from reportbro import Report, ReportBroError
except ModuleNotFoundError:  # pragma: no cover - fallback used in CI and dev without reportbro-lib
    from ._stubs.reportbro import Report, ReportBroError

logger = logging.getLogger(__name__)


class ReportBroIntegrationError(RuntimeError):
    """Base exception for ReportBro integration issues."""


class ReportBroTemplateError(ReportBroIntegrationError):
    """Raised when a ReportBro template cannot be loaded or parsed."""


class ReportBroRenderError(ReportBroIntegrationError):
    """Raised when ReportBro fails to render the requested output."""


def load_template_definition(source: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    """Return the ReportBro template definition stored in *source*.

    Parameters
    ----------
    source:
        Either a mapping already containing the template definition or the
        filesystem location of the template JSON file.
    """

    if isinstance(source, Mapping):
        return dict(source)

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

    return template


def _format_errors(errors: list[Any]) -> str:
    messages = []
    for error in errors:
        try:
            messages.append(str(error))
        except Exception:  # pragma: no cover - defensive
            messages.append(repr(error))
    return "; ".join(messages)


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


def _normalise_parameter_ids(template: dict[str, Any]) -> None:
    parameters = template.get("parameters")
    if not isinstance(parameters, Iterable):
        return

    normalised: list[dict[str, Any]] = []
    for index, parameter in enumerate(parameters, start=1):
        if not isinstance(parameter, Mapping):
            continue
        mutable = dict(parameter)

        raw_id = mutable.get("id")
        if isinstance(raw_id, int):
            normalised.append(mutable)
            continue

        candidate = None
        if isinstance(raw_id, str):
            digits = "".join(ch for ch in raw_id if ch.isdigit())
            if digits:
                candidate = int(digits)

        mutable["id"] = candidate if candidate is not None else index
        normalised.append(mutable)

    template["parameters"] = normalised


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
                stripped = source.strip()
                if stripped.startswith("${") and stripped.endswith("}"):
                    pass
                else:
                    if stripped.startswith("@"):
                        stripped = stripped.lstrip("@")
                    if stripped in parameters and stripped:
                        mutable["source"] = f"${{{stripped}}}"
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


def render_pdf_bytes(
    template_definition: Mapping[str, Any],
    data: Mapping[str, Any],
) -> bytes:
    """Return the PDF bytes rendered from *template_definition* using *data*."""

    template = deepcopy(dict(template_definition))
    _normalise_document_properties(template)
    _normalise_parameter_ids(template)
    _normalise_image_sources(template)
    _ensure_title_binding(template)

    payload = dict(data)
    try:
        report = Report(template, payload)
    except AssertionError as exc:  # pragma: no cover - defensive guard
        raise ReportBroTemplateError(f"Invalid template definition: {exc}") from exc

    if report.errors:
        message = _format_errors(report.errors)
        raise ReportBroTemplateError(
            f"Template validation failed with errors: {message or '<sem detalhes>'}"
        )

    try:
        return report.generate_pdf()
    except ReportBroError as exc:
        raise ReportBroRenderError(f"Failed to generate ReportBro PDF: {exc}") from exc


def render_pdf_to_path(
    template_definition: Mapping[str, Any],
    data: Mapping[str, Any],
    destination: Path,
) -> Path:
    """Render *template_definition* and write the resulting PDF into *destination*."""

    destination = Path(destination)
    pdf_bytes = render_pdf_bytes(template_definition, data)
    destination.write_bytes(pdf_bytes)
    logger.info("[ReportBro] PDF export completed at %s", destination)
    return destination
