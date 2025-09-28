"""Helpers for generating business reports."""

from .ft_gestao import build_reportbro_context
from .graphics import gerar_grafico_foodcost_pie
from .reportbro_export import (
    ReportBroIntegrationError,
    ReportBroRenderError,
    ReportBroTemplateError,
    load_template_definition,
    render_pdf_bytes,
    render_pdf_to_path,
)

__all__ = [
    "build_reportbro_context",
    "ReportBroIntegrationError",
    "ReportBroRenderError",
    "ReportBroTemplateError",
    "gerar_grafico_foodcost_pie",
    "load_template_definition",
    "render_pdf_bytes",
    "render_pdf_to_path",
]
