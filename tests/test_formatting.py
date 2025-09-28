from utils.formatting import (
    format_currency_locale,
    normalise_currency_context,
    parse_decimal,
)


def test_parse_decimal_nbsp():
    assert parse_decimal("1\u00A0234,56") == 1234.56


def test_parse_decimal_strips_currency_suffix():
    assert parse_decimal("5\u00A0482,925\u00A0Kz") == 5482.925


def test_parse_decimal_strips_percent_suffix():
    assert parse_decimal("12,5%") == 12.5


def test_format_currency_locale_en_us():
    context = normalise_currency_context(
        {"currency_symbol": "US$", "currency_code": "USD", "locale_code": "en_US"}
    )
    result = format_currency_locale(
        1234.5,
        locale_code=context["locale_code"],
        currency_symbol=context["currency_symbol"],
        currency_code=context["currency_code"],
    )
    assert result == "US$1,234.50"


def test_format_currency_locale_pt_br():
    context = normalise_currency_context(
        {"currency_symbol": "BRL$", "currency_code": "BRL", "locale_code": "pt_BR"}
    )
    result = format_currency_locale(
        9876.54,
        locale_code=context["locale_code"],
        currency_symbol=context["currency_symbol"],
        currency_code=context["currency_code"],
    )
    assert result == "BRL$\u00a09.876,54"


def test_format_currency_locale_fallback_places_symbol_to_the_right(monkeypatch):
    monkeypatch.setattr("utils.formatting.Locale", None)
    monkeypatch.setattr("utils.formatting.babel_format_decimal", None)

    result = format_currency_locale(
        1234.56,
        locale_code=None,
        currency_symbol="€",
        currency_code=None,
    )

    assert result == "1\u00a0234,56\u00a0€"
