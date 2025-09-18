"""Centralised map of development overlay tags used across the project.

This module concentrates the canonical identifiers for well-known zones so
that tests, QML bindings and the widget layout reference the same source. When
the visual editor renames a block, the new value only needs to be updated here
instead of being scattered throughout the codebase.
"""

from __future__ import annotations

from typing import Mapping


# NOTE: Keys use snake_case to stay QML-friendly (bracket access) and Pythonic.
_ZONE_TAGS: Mapping[str, str] = {
    # --- Shared header ----------------------------------------------------
    "header_root": "B0.C1",

    # --- Dados Gerais / identificação ------------------------------------
    "general_root": "B1.C1",
    "general_name_zone": "B1.C2",
    "general_ident_labels": "B1.C1.A.1.A",
    "general_ident_label_codigo": "B1.C1.A.1.A.1",
    "general_ident_label_nome": "B1.C1.A.1.A.2",

    # --- Família & Combos -------------------------------------------------
    "family_root": "B2.C1",
    "family_section": "B2.C1.A",
    "family_row": "B2.C1.A.1",
    "family_labels_column": "B2.C1.A.1.A",
    "family_label_familia": "B2.C1.A.1.A.1",
    "family_label_subfamilia": "B2.C1.A.1.A.2",
    "family_values_column": "B2.C1.A.1.B",
    "family_value_familia": "B2.C1.A.1.B.1",
    "family_value_subfamilia": "B2.C1.A.1.B.2",
    "family_combos_section": "B2.C1.B",
    "family_combo_col_1": "B2.C1.B.1",
    "family_combo_col_2": "B2.C1.B.2",
    "family_combo_col_3": "B2.C1.B.3",

    # --- PVPs -------------------------------------------------------------
    "pvps_root": "B3.C1",

    # --- Ingredientes -----------------------------------------------------
    "ingredients_root": "B4.C1",
    "ingredients_secondary": "B4.C2",

    # --- Food Cost --------------------------------------------------------
    "food_cost_root": "B5.C1",

    # --- Preparação -------------------------------------------------------
    "preparation_root": "B6.C1",

    # --- Nutrição / Alergénios -------------------------------------------
    "allergens_root": "B7.C1",
    "allergens_secondary": "B7.C2",
}


def zone_tag(key: str) -> str:
    """Return the canonical tag for ``key``.

    Parameters
    ----------
    key:
        Symbolic identifier present in :data:`_ZONE_TAGS`.

    Raises
    ------
    KeyError
        If the requested ``key`` is unknown.
    """

    return _ZONE_TAGS[key]


def zone_tag_map() -> Mapping[str, str]:
    """Expose a read-only mapping with all known zone tags."""

    return _ZONE_TAGS


__all__ = ["zone_tag", "zone_tag_map"]

