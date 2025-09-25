"""Services responsible for rendering ReportBro templates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from reportbro import Report, ReportBroError
except ModuleNotFoundError:  # pragma: no cover - fallback in dev without reportbro-lib
    from reporting._stubs.reportbro import Report, ReportBroError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DATA_PATH = PROJECT_ROOT / "reporting" / "samples" / "sample_data.json"


class TemplateError(ValueError):
    """Raised when a template payload is invalid."""


class DataError(ValueError):
    """Raised when the data payload is invalid."""


class RenderError(RuntimeError):
    """Raised when ReportBro fails to render a document."""


@dataclass
class RenderContext:
    """Payload passed to ReportBro."""

    template: dict[str, Any]
    data: dict[str, Any]


def _validate_template(template: dict[str, Any]) -> None:
    if "documentProperties" not in template:
        raise TemplateError("Template JSON inválido: faltam 'documentProperties'.")


def _normalise_document_properties(template: dict[str, Any]) -> None:
    properties = template.get("documentProperties")
    if not isinstance(properties, dict):
        return

    page_format = properties.get("pageFormat")
    if not isinstance(page_format, str) or not page_format.strip():
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
        if not isinstance(parameter, dict):
            continue

        mutable = parameter.copy()

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
        if isinstance(param, dict)
    }

    elements = template.get("docElements")
    if not isinstance(elements, Iterable):
        return

    normalised_elements: list[dict[str, Any]] = []
    for element in elements:
        if not isinstance(element, dict):
            continue

        mutable = element.copy()
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

    normalised_elements: list[dict[str, Any]] = []
    replacement_done = False
    for element in elements:
        if not isinstance(element, dict):
            continue
        mutable = element.copy()
        if not replacement_done and mutable.get("elementType") == "text":
            content = mutable.get("content")
            if isinstance(content, str):
                stripped = content.strip()
                if stripped.startswith("${") and stripped.endswith("}"):
                    replacement_done = True
                elif stripped.upper() == "FICHA DE ARTIGO":
                    mutable["content"] = "${title}"
                    replacement_done = True
        normalised_elements.append(mutable)

    if normalised_elements:
        template["docElements"] = normalised_elements


def _load_default_data() -> dict[str, Any]:
    if not SAMPLE_DATA_PATH.exists():
        raise DataError(
            "Ficheiro sample_data.json não encontrado. Execute o script de bootstrap para o criar."
        )
    try:
        return json.loads(SAMPLE_DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise DataError(f"sample_data.json inválido: {exc}.") from exc


def _normalise_data(data: dict[str, Any] | None) -> dict[str, Any]:
    if data is None:
        return _load_default_data()
    return data


def _build_context(template: dict[str, Any], data: dict[str, Any] | None) -> RenderContext:
    if not isinstance(template, dict):
        raise TemplateError("Template JSON inválido.")
    _validate_template(template)
    _normalise_document_properties(template)
    _normalise_parameter_ids(template)
    _normalise_image_sources(template)
    _ensure_title_binding(template)
    normalised_data = _normalise_data(data)
    if not isinstance(normalised_data, dict):
        raise DataError("Dados inválidos: deve ser um objeto JSON.")
    return RenderContext(template=template, data=normalised_data)


def generate_pdf(template_dict: dict[str, Any], data_dict: dict[str, Any] | None = None) -> bytes:
    """Render the provided template and return a PDF document."""

    context = _build_context(template_dict, data_dict)
    try:
        report = Report(context.template, context.data)
        pdf_bytes = report.generate_pdf()
    except ReportBroError as exc:  # pragma: no cover - requires reportbro-lib
        raise RenderError(f"Falha ao gerar PDF: {exc}.") from exc
    return pdf_bytes


def generate_xlsx(template_dict: dict[str, Any], data_dict: dict[str, Any] | None = None) -> bytes:
    """Render the provided template and return an XLSX document."""

    context = _build_context(template_dict, data_dict)
    try:
        report = Report(context.template, context.data)
        if hasattr(report, "generate_xlsx"):
            xlsx_bytes = report.generate_xlsx()
        else:  # pragma: no cover - fallback quando se usa o stub
            raise RenderError(
                "A biblioteca reportbro-lib instalada não suporta exportação XLSX nesta configuração."
            )
    except ReportBroError as exc:  # pragma: no cover - requires reportbro-lib
        raise RenderError(f"Falha ao gerar XLSX: {exc}.") from exc
    return xlsx_bytes


__all__ = [
    "DataError",
    "RenderError",
    "TemplateError",
    "generate_pdf",
    "generate_xlsx",
]
