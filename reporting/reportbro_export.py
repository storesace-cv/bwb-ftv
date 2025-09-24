"""Utilities to render ReportBro templates from Python."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Mapping

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


def render_pdf_bytes(
    template_definition: Mapping[str, Any],
    data: Mapping[str, Any],
) -> bytes:
    """Return the PDF bytes rendered from *template_definition* using *data*."""

    try:
        report = Report(dict(template_definition), dict(data))
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
