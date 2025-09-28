"""Formatting helpers for user-facing numbers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any

try:  # pragma: no cover - optional dependency, exercised when available
    from babel.core import Locale, UnknownLocaleError
    from babel.numbers import format_decimal as babel_format_decimal
except ImportError:  # pragma: no cover - handled gracefully in helpers
    UnknownLocaleError = ValueError  # type: ignore[assignment]
    Locale = None  # type: ignore[assignment]
    babel_format_decimal = None

NBSP = "\u00A0"

_DEFAULT_CURRENCY_CONTEXT = {
    "currency": "EUR",
    "currency_code": "EUR",
    "currency_symbol": "€",
    "locale_code": "pt_PT",
}


def parse_decimal(value):
    """Return a float parsed from a potentially localized decimal string.

    Spaces are treated as thousand separators and commas as decimal
    separators. If ``value`` isn't a string or can't be parsed, it is
    returned unchanged.
    """

    if isinstance(value, str):
        allowed_suffix_chars = set("0123456789-.,") | {NBSP}
        trimmed = value.rstrip(" \t\r\n")
        while trimmed and trimmed[-1] not in allowed_suffix_chars:
            trimmed = trimmed[:-1].rstrip(" \t\r\n")

        cleaned = trimmed.replace(" ", "").replace(NBSP, "").replace(",", ".")
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


def normalise_currency_code(value: Any) -> str | None:
    """Return a 3-letter ISO currency code or ``None`` when invalid."""

    if value is None:
        return None
    text = str(value).strip()
    if len(text) == 3 and text.isalpha():
        return text.upper()
    return None


def normalise_currency_context(
    data: Any, *, defaults: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Return a normalised currency context dictionary.

    The resulting mapping always contains ``currency_symbol``, ``currency_code``
    (which may be ``None`` when the input is invalid) and ``locale_code``.
    Additional metadata such as ``country`` or ``currency`` are preserved when
    present in *data*.
    """

    context: dict[str, Any] = {
        "id": None,
        "country": None,
        "country_code": None,
        "currency": None,
        "currency_name": None,
        "currency_code": None,
        "currency_symbol": "€",
        "locale_code": "pt_PT",
        "format": None,
        "active": None,
    }

    if defaults:
        for key, value in defaults.items():
            if value is not None:
                context[key] = value

    if isinstance(data, Mapping):
        context.update({
            "id": data.get("id", context["id"]),
            "country": data.get("country", context["country"]),
            "country_code": data.get("country_code", data.get("code", context["country_code"])),
            "currency": data.get("currency", context["currency"]),
            "currency_name": data.get("currency_name", data.get("currency", context["currency_name"])),
            "format": data.get("format", data.get("fmt", data.get("locale_code", context["format"]))),
            "active": data.get("active", context["active"]),
        })
        symbol = data.get("currency_symbol", data.get("symbol"))
        if symbol:
            context["currency_symbol"] = str(symbol)
        locale = data.get("locale_code", data.get("format", data.get("fmt")))
        if locale:
            context["locale_code"] = str(locale)
        currency_code = data.get("currency_code", data.get("currency"))
        code = normalise_currency_code(currency_code)
        if code:
            context["currency_code"] = code
    elif isinstance(data, Sequence):
        if len(data) > 0:
            context["id"] = data[0]
        if len(data) > 1:
            context["country"] = data[1]
        if len(data) > 2:
            context["country_code"] = data[2]
        if len(data) > 3:
            context["currency"] = data[3]
            context["currency_name"] = data[3]
            code = normalise_currency_code(data[3])
            if code:
                context["currency_code"] = code
        if len(data) > 4 and data[4]:
            context["currency_symbol"] = str(data[4])
        if len(data) > 5 and data[5]:
            context["locale_code"] = str(data[5])
            context["format"] = data[5]
        if len(data) > 6:
            context["active"] = bool(data[6])

    if context.get("format") is None:
        context["format"] = context.get("locale_code")

    if context.get("currency_code") is None:
        context["currency_code"] = normalise_currency_code(context.get("currency"))
    if context.get("currency_code") is None:
        context["currency_code"] = normalise_currency_code(context.get("currency_name"))

    return context


def format_currency_locale(
    value: Any,
    *,
    locale_code: str | None,
    currency_symbol: str | None,
    currency_code: str | None,
) -> str:
    """Format *value* as currency using the provided locale details."""

    try:
        numeric = float(Decimal(str(value)))
    except (InvalidOperation, TypeError, ValueError):
        return str(value)

    locales_to_try: list[str] = []
    if locale_code:
        locales_to_try.append(str(locale_code))
    locales_to_try.append(_DEFAULT_CURRENCY_CONTEXT["locale_code"])

    symbol = currency_symbol or currency_code or ""

    if Locale is not None and currency_code:
        for candidate in locales_to_try:
            try:
                locale_obj = Locale.parse(candidate)
                pattern = locale_obj.currency_formats.get("standard")
                if pattern is None:
                    continue
                placeholder = pattern.apply(numeric, locale=locale_obj)
            except (UnknownLocaleError, ValueError):
                continue
            except (TypeError, AttributeError):
                continue

            if symbol:
                return placeholder.replace("¤", symbol)

            cleaned = placeholder.replace("¤", "").strip()
            if cleaned:
                return cleaned

    formatted = None
    if babel_format_decimal:
        for candidate in locales_to_try:
            try:
                formatted = babel_format_decimal(numeric, locale=candidate)
                break
            except (UnknownLocaleError, ValueError):
                continue

    if formatted is None:
        formatted = format_pt_number(numeric)

    if symbol:
        return f"{formatted}{NBSP}{symbol}"
    return formatted
