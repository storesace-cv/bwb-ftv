"""Services responsible for rendering ReportBro templates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
