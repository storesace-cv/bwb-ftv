"""Formatting helpers for user-facing numbers."""

from decimal import Decimal, InvalidOperation

NBSP = "\u00A0"


def format_pt_number(value, missing="—") -> str:
    """Return a Portuguese-formatted number string.

    The output uses a non-breaking space as thousands separator and a comma
    as decimal separator (e.g., ``1 234,56``). ``None`` or empty values return
    ``missing``.
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return missing
    try:
        number = float(Decimal(str(value)))
    except (InvalidOperation, TypeError, ValueError):
        return str(value)
    int_part, dec_part = f"{number:,.2f}".split(".")
    int_part = int_part.replace(",", NBSP)
    return f"{int_part},{dec_part}"
