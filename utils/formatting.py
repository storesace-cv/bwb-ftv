"""Formatting helpers for user-facing numbers."""

from decimal import Decimal, InvalidOperation

NBSP = "\u00A0"


def parse_decimal(value):
    """Return a float parsed from a potentially localized decimal string.

    Spaces are treated as thousand separators and commas as decimal
    separators. If ``value`` isn't a string or can't be parsed, it is
    returned unchanged.
    """

    if isinstance(value, str):
        cleaned = value.replace(" ", "").replace(",", ".")
        try:
            return float(Decimal(cleaned))
        except (InvalidOperation, ValueError):
            return value
    return value


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
