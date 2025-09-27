from tests._qt import require_real_qt_modules

require_real_qt_modules("PyQt5.QtWidgets")

import logging

from domain import Product
from services.products import calculate_food_cost
from ui.ui_editor_fonte import FTApp
from utils.formatting import (
    format_currency_locale,
    format_pt_number,
    normalise_currency_context,
)


class DummyAuxRepo:
    def __getattr__(self, name):
        def _method(*_args, **_kwargs):
            return [] if name.startswith("list") else True

        return _method


class DummyFCostRepo:
    def list_levels(self):
        return []


class DummyDataStore:
    def __init__(self, locale=None):
        self._locale = normalise_currency_context(locale or {})
        self.aux = DummyAuxRepo()
        self.fcost = DummyFCostRepo()
        self._saved_html: dict[str, str] = {}
        self._fcost_level = None

    def get_localizacao_ativa(self):
        return self._locale

    def set_locale(self, data):
        self._locale = normalise_currency_context(data or {})

    def get_preparacao_html(self, _codigo):
        return self._saved_html.get(_codigo, "")

    def save_preparacao_html(self, codigo, html):
        self._saved_html[codigo] = html or ""

    def set_fcost_level(self, level):
        self._fcost_level = level


class DummyService:
    def __init__(self, locale=None):
        self.ds = DummyDataStore(locale)
        self.conn = None

    def total(self):
        return 1

    def codigo_at(self, idx):
        return None

    def list_tipos_artigos(self):
        return []

    def list_validade(self):
        return []

    def list_temperaturas(self):
        return []

    def list_active_allergens(self):
        return []

    def get_image_path(self, codigo: str) -> None:
        return None

    def save_product_image(self, codigo: str, src_path: str) -> None:
        pass

    def delete_product_image(self, codigo: str) -> None:
        pass

    def get_product_info(self, codigo):
        return Product(
            code=codigo,
            pvps=[123, 246, None, 0, 615],
            iva=23,
            ingredients=[],
        )

    def calculate_cost(self, product):
        return 100


def test_format_pt_number_basic():
    assert format_pt_number(1234.56) == "1\u00A0234,56"
    assert format_pt_number(None) == "—"


def test_ftapp_formats_numbers(qapp):
    service = DummyService()
    ft = FTApp(service)
    locale = service.ds.get_localizacao_ativa()

    def fmt(value):
        return format_currency_locale(
            value,
            locale_code=locale.get("locale_code"),
            currency_symbol=locale.get("currency_symbol"),
            currency_code=locale.get("currency_code"),
        )

    expected_texts = [
        fmt(123),
        fmt(246),
        "--N/A--",
        "--N/A--",
        fmt(615),
    ]
    assert [lb.text() for lb in ft.lbPVPs] == expected_texts
    assert ft.edCustoTotal.text() == fmt(100)
    expected_fc_texts = [
        format_pt_number(100),
        format_pt_number(50),
        "--N/A--",
        "--N/A--",
        format_pt_number(20),
    ]
    assert [lb.text() for lb in ft.lbFoodCosts] == expected_fc_texts
    ft.close()


def test_ftapp_reloads_locale_info_on_change(qapp):
    service = DummyService()
    ft = FTApp(service)
    try:
        assert "€" in ft.lbPVPs[0].text()
        service.ds.set_locale({
            "currency_code": "USD",
            "currency_symbol": "$",
            "locale_code": "en_US",
        })
        ft._on_localizacao_changed()
        updated_locale = service.ds.get_localizacao_ativa()
        expected = format_currency_locale(
            123,
            locale_code=updated_locale.get("locale_code"),
            currency_symbol=updated_locale.get("currency_symbol"),
            currency_code=updated_locale.get("currency_code"),
        )
        assert ft.lbPVPs[0].text() == expected
        assert ft.edCustoTotal.text() == format_currency_locale(
            100,
            locale_code=updated_locale.get("locale_code"),
            currency_symbol=updated_locale.get("currency_symbol"),
            currency_code=updated_locale.get("currency_code"),
        )
        assert ft.locale_info.get("currency_code") == "USD"
    finally:
        ft.close()


def test_ftapp_food_cost_missing_iva(qapp, caplog):
    class NoIVAService(DummyService):
        def get_product_info(self, codigo):
            return Product(
                code=codigo,
                pvps=[123, 246, 615, 1000, 2000],
                iva=None,
                ingredients=[],
            )

    with caplog.at_level(logging.WARNING):
        ft = FTApp(NoIVAService())
    assert [lb.text() for lb in ft.lbFoodCosts] == ["--"] * 5
    assert any("missing Iva1" in rec.message for rec in caplog.records)
    ft.close()


def test_ftapp_food_costs_large_total(qapp):
    class HighTotalService(DummyService):
        def calculate_cost(self, product):
            return 1234.56

    ft = FTApp(HighTotalService())
    expected = format_pt_number(
        calculate_food_cost(1234.56, 123, 23)
    )
    assert ft.lbFoodCosts[0].text() == expected
    ft.close()


def test_ftapp_zero_pvps_no_warning(qapp, caplog):
    class ZeroPVPService(DummyService):
        def get_product_info(self, codigo):
            return Product(
                code=codigo,
                pvps=[123, 0, 0, 0, 0],
                iva=23,
                ingredients=[],
            )

    service = ZeroPVPService()
    locale = service.ds.get_localizacao_ativa()

    def fmt(value):
        return format_currency_locale(
            value,
            locale_code=locale.get("locale_code"),
            currency_symbol=locale.get("currency_symbol"),
            currency_code=locale.get("currency_code"),
        )

    with caplog.at_level(logging.WARNING):
        ft = FTApp(service)
    expected_pvp_texts = [
        fmt(123),
        "--N/A--",
        "--N/A--",
        "--N/A--",
        "--N/A--",
    ]
    assert [lb.text() for lb in ft.lbPVPs] == expected_pvp_texts
    expected_fc_texts = [
        format_pt_number(calculate_food_cost(100, 123, 23)),
        "--N/A--",
        "--N/A--",
        "--N/A--",
        "--N/A--",
    ]
    assert [lb.text() for lb in ft.lbFoodCosts] == expected_fc_texts
    assert not any("missing pvp" in rec.message for rec in caplog.records)
    ft.close()
