"""Helpers related to printing/exporting UI artefacts."""

from __future__ import annotations

from pathlib import Path

from domain.models import Product


def generate_ft_gestao_pdf(product: Product, *, page_size: str = "A4") -> Path:
    """Generate the Gestão PDF for the given product on the specified page size.

    This helper is a placeholder that should produce the A4 PDF representation of
    the currently active product in the editor.
    """

    raise NotImplementedError("FT Gestão PDF generation is not implemented yet")
