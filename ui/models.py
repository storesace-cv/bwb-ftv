"""Reusable Qt models for the fichas técnicas UI."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Iterable, Any

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from domain import FichaTecnica
from utils.formatting import (
    NBSP,
    format_currency_locale,
    format_pt_number,
    normalise_currency_context,
    parse_decimal,
)

_FT_HEADERS = ["INGREDIENTES", "QTD", "U.M.", "PPU", "TOTAL", "PESO (%)"]
_FT_DEV_HEADERS = [
    "FichasTecnicas.ComponenteNome",
    "FichasTecnicas.Qtd",
    "FichasTecnicas.Unidade",
    "FichasTecnicas.Ppu",
    "FichasTecnicas.Preco",
    "FichasTecnicas.Peso",
]
_EDITABLE_COLUMNS = {1, 3, 4}
_HEADER_ALIGNMENT = Qt.AlignHCenter | Qt.AlignVCenter
_CELL_ALIGNMENT = Qt.AlignLeft | Qt.AlignVCenter


def _coerce_currency_context(
    context: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """Return a normalised currency context for formatting ingredients."""

    defaults = normalise_currency_context({})
    if context is None:
        return defaults
    if isinstance(context, Mapping):
        return normalise_currency_context(context, defaults=defaults)
    return defaults


def _format_ft_currency(
    value: Any,
    context: Mapping[str, Any] | None,
    *,
    missing: str = "—",
) -> str:
    """Format ingredient currency values ensuring trailing symbols."""

    if value is None or value == "":
        return missing

    currency_context = context or {}
    locale_code = currency_context.get("locale_code") if isinstance(currency_context, Mapping) else None
    currency_symbol = (
        currency_context.get("currency_symbol")
        if isinstance(currency_context, Mapping)
        else None
    )
    currency_code = (
        currency_context.get("currency_code")
        if isinstance(currency_context, Mapping)
        else None
    )
    formatted = format_currency_locale(
        value,
        locale_code=locale_code,
        currency_symbol=currency_symbol,
        currency_code=currency_code,
    )
    symbol = currency_symbol or currency_code
    if symbol and formatted.startswith(symbol):
        numeric_text = formatted[len(symbol) :].lstrip().lstrip(NBSP)
        if numeric_text:
            return f"{numeric_text}{NBSP}{symbol}".strip()
    return formatted


def build_fichas_tecnicas_model(
    rows: Iterable[FichaTecnica] | None,
    *,
    overlays: bool,
    currency_context: Mapping[str, Any] | None = None,
) -> QStandardItemModel:
    """Return a ``QStandardItemModel`` configured for ingredient rows."""

    model = QStandardItemModel()
    model._ft_rows: list[FichaTecnica] = []  # type: ignore[attr-defined]
    model._ft_refreshing = False  # type: ignore[attr-defined]
    model._ft_item_handler = lambda item: _sync_item_to_ficha(model, item)  # type: ignore[attr-defined]
    model.itemChanged.connect(model._ft_item_handler)  # type: ignore[arg-type]
    model._ft_currency_context = _coerce_currency_context(currency_context)  # type: ignore[attr-defined]
    update_fichas_tecnicas_model(
        model, rows, overlays=overlays, currency_context=currency_context
    )
    return model


def update_fichas_tecnicas_model(
    model: QStandardItemModel,
    rows: Iterable[FichaTecnica] | None,
    *,
    overlays: bool,
    currency_context: Mapping[str, Any] | None = None,
) -> None:
    """Replace ``model`` contents with ``rows`` respecting overlays."""

    ficha_rows = list(rows or [])
    model._ft_refreshing = True  # type: ignore[attr-defined]
    model.beginResetModel()
    try:
        model.clear()
        if currency_context is not None:
            model._ft_currency_context = _coerce_currency_context(currency_context)  # type: ignore[attr-defined]
        context = getattr(
            model,
            "_ft_currency_context",
            _coerce_currency_context(None),
        )
        _apply_fichas_tecnicas_headers(model, overlays)
        for ficha in ficha_rows:
            model.appendRow(_build_ft_row_items(ficha, context))
        model._ft_rows = ficha_rows  # type: ignore[attr-defined]
        model._ft_overlays = overlays  # type: ignore[attr-defined]
    finally:
        model.endResetModel()
        model._ft_refreshing = False  # type: ignore[attr-defined]


def apply_fichas_tecnicas_headers(
    model: QStandardItemModel,
    *,
    overlays: bool,
) -> None:
    """Update ``model`` headers when overlay mode changes."""

    _apply_fichas_tecnicas_headers(model, overlays)
    model._ft_overlays = overlays  # type: ignore[attr-defined]


def _apply_fichas_tecnicas_headers(model: QStandardItemModel, overlays: bool) -> None:
    headers = _FT_DEV_HEADERS if overlays else _FT_HEADERS
    model.setColumnCount(len(headers))
    for idx, label in enumerate(headers):
        model.setHeaderData(idx, Qt.Horizontal, label, Qt.DisplayRole)
        model.setHeaderData(idx, Qt.Horizontal, _HEADER_ALIGNMENT, Qt.TextAlignmentRole)


def _build_ft_row_items(
    ficha: FichaTecnica,
    context: Mapping[str, Any] | None,
) -> list[QStandardItem]:
    ingredient = ficha.ingredient or ""
    has_ingredient = bool(ingredient.strip())
    display_values = (
        ingredient if has_ingredient else "—",
        format_pt_number(ficha.quantity),
        ficha.unit or "",
        _format_ft_currency(ficha.ppu, context),
        _format_ft_currency(ficha.total, context),
        format_pt_number(ficha.weight),
    )
    if not has_ingredient:
        display_values = ("—", "", "", "", "", "")

    items: list[QStandardItem] = []
    for col, value in enumerate(display_values):
        item = QStandardItem(value if value is not None else "")
        if col == 0:
            alignment = _CELL_ALIGNMENT
        elif col in (1, 2, 5):
            alignment = Qt.AlignHCenter | Qt.AlignVCenter
        else:
            alignment = Qt.AlignRight | Qt.AlignVCenter
        item.setTextAlignment(alignment)
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if col in _EDITABLE_COLUMNS:
            flags |= Qt.ItemIsEditable
        item.setFlags(flags)
        if col == 0:
            item.setData(ficha, Qt.UserRole)
        items.append(item)
    return items


def _sync_item_to_ficha(model: QStandardItemModel, item: QStandardItem) -> None:
    if getattr(model, "_ft_refreshing", False):
        return

    col = item.column()
    if col not in _EDITABLE_COLUMNS:
        return

    rows: list[FichaTecnica] = getattr(model, "_ft_rows", [])
    if item.row() >= len(rows):
        return
    ficha = rows[item.row()]
    column_attr = {1: "quantity", 3: "ppu", 4: "total"}.get(col)
    if not column_attr:
        return

    value = parse_decimal(item.text())
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return

    setattr(ficha, column_attr, numeric)
    if column_attr == "quantity":
        formatted = format_pt_number(numeric)
    else:
        context = getattr(
            model,
            "_ft_currency_context",
            _coerce_currency_context(None),
        )
        formatted = _format_ft_currency(numeric, context)
    if item.text() != formatted:
        model.blockSignals(True)
        item.setText(formatted)
        model.blockSignals(False)
