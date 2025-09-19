"""Reusable Qt models for the fichas técnicas UI."""

from __future__ import annotations

from typing import Iterable

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from domain import FichaTecnica
from utils.formatting import format_pt_number, parse_decimal

_FT_HEADERS = ["INGREDIENTES", "QTD", "U.M.", "PPU", "TOTAL"]
_FT_DEV_HEADERS = [
    "FichasTecnicas.ComponenteNome",
    "FichasTecnicas.Qtd",
    "FichasTecnicas.Unidade",
    "FichasTecnicas.Ppu",
    "FichasTecnicas.Preco",
]
_EDITABLE_COLUMNS = {1, 3, 4}
_HEADER_ALIGNMENT = Qt.AlignHCenter | Qt.AlignVCenter
_CELL_ALIGNMENT = Qt.AlignLeft | Qt.AlignVCenter


def build_fichas_tecnicas_model(
    rows: Iterable[FichaTecnica] | None,
    *,
    overlays: bool,
) -> QStandardItemModel:
    """Return a ``QStandardItemModel`` configured for ingredient rows."""

    model = QStandardItemModel()
    model._ft_rows: list[FichaTecnica] = []  # type: ignore[attr-defined]
    model._ft_refreshing = False  # type: ignore[attr-defined]
    model._ft_item_handler = lambda item: _sync_item_to_ficha(model, item)  # type: ignore[attr-defined]
    model.itemChanged.connect(model._ft_item_handler)  # type: ignore[arg-type]
    update_fichas_tecnicas_model(model, rows, overlays=overlays)
    return model


def update_fichas_tecnicas_model(
    model: QStandardItemModel,
    rows: Iterable[FichaTecnica] | None,
    *,
    overlays: bool,
) -> None:
    """Replace ``model`` contents with ``rows`` respecting overlays."""

    ficha_rows = list(rows or [])
    model._ft_refreshing = True  # type: ignore[attr-defined]
    model.beginResetModel()
    try:
        model.clear()
        _apply_fichas_tecnicas_headers(model, overlays)
        for ficha in ficha_rows:
            model.appendRow(_build_ft_row_items(ficha))
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


def _build_ft_row_items(ficha: FichaTecnica) -> list[QStandardItem]:
    ingredient = ficha.ingredient or ""
    has_ingredient = bool(ingredient.strip())
    display_values = (
        ingredient if has_ingredient else "—",
        format_pt_number(ficha.quantity),
        ficha.unit or "",
        format_pt_number(ficha.ppu),
        format_pt_number(ficha.total),
    )
    if not has_ingredient:
        display_values = ("—", "", "", "", "")

    items: list[QStandardItem] = []
    for col, value in enumerate(display_values):
        item = QStandardItem(value if value is not None else "")
        item.setTextAlignment(_CELL_ALIGNMENT)
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
    formatted = format_pt_number(numeric)
    if item.text() != formatted:
        model.blockSignals(True)
        item.setText(formatted)
        model.blockSignals(False)
