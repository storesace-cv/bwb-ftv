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

    # --- [B1] Ficha do Artigo -------------------------------------------
    # Root containers
    "general_root": "B1.A1",
    "general_aux_root": "B1.A1",
    "general_aux_stack": "B1.A1.A",
    "general_aux_primary": "B1.A1.A",

    # Identification (B1.A1.A.1)
    "general_aux_identification_slot": "B1.A1.A.1",
    "general_aux_family_slot": "B1.A1.A.2",
    "general_aux_secondary_slot": "B1.A1.A.3",
    "general_ident_labels": "B1.A1.A.1.A",
    "general_ident_label_codigo": "B1.A1.A.1.A.1",
    "general_ident_label_nome": "B1.A1.A.1.A.2",
    "viewer_identification_code": "B1.A1.A.1.B.1",
    "viewer_identification_name": "B1.A1.A.1.B.2",
    "general_name_zone": "B1.A1.A.1.B.2",

    # Família & Combos (B1.A1.A.2)
    "family_root": "B1.A1.A.2",
    "family_section": "B1.A1.A.2",
    "family_row": "B1.A1.A.2.A",
    "family_labels_column": "B1.A1.A.2.A",
    "family_label_familia": "B1.A1.A.2.A.1",
    "family_label_subfamilia": "B1.A1.A.2.A.2",
    "family_values_column": "B1.A1.A.2.B",
    "family_value_familia": "B1.A1.A.2.B.1",
    "family_value_subfamilia": "B1.A1.A.2.B.2",
    "general_aux_additional_info_section": "B1.A1.A.2.C",
    "general_aux_additional_info_legend": "B1.A1.A.2.C.1",
    "general_aux_additional_info_field": "B1.A1.A.2.C.2",

    # Prices & preview columns
    "general_aux_prices_slot": "B1.A1.A.4",
    "general_aux_preview": "B1.A1.E",
    "general_aux_preview_image": "B1.A1.E.1",

    # Reserved/auxiliary slots off the root
    "general_aux_reserved_slot_2": "B1.A1.2",
    "general_aux_reserved_slot_3": "B1.A1.3",
    "general_aux_reserved_slot_4": "B1.A1.4",

    # PVPs (nested under prices slot)
    "pvps_root": "B1.A1.A.4",
    "pvps_grid": "B1.A1.A.4.A",
    "pvps_col_1": "B1.A1.A.4.A.1",
    "pvps_col_1_legend": "B1.A1.A.4.A.1.1",
    "pvps_col_1_field": "B1.A1.A.4.A.1.2",
    "pvps_col_2": "B1.A1.A.4.A.2",
    "pvps_col_2_legend": "B1.A1.A.4.A.2.1",
    "pvps_col_2_field": "B1.A1.A.4.A.2.2",
    "pvps_col_3": "B1.A1.A.4.A.3",
    "pvps_col_3_legend": "B1.A1.A.4.A.3.1",
    "pvps_col_3_field": "B1.A1.A.4.A.3.2",
    "pvps_col_4": "B1.A1.A.4.A.4",
    "pvps_col_4_legend": "B1.A1.A.4.A.4.1",
    "pvps_col_4_field": "B1.A1.A.4.A.4.2",
    "pvps_col_5": "B1.A1.A.4.A.5",
    "pvps_col_5_legend": "B1.A1.A.4.A.5.1",
    "pvps_col_5_field": "B1.A1.A.4.A.5.2",

    # --- Simplified viewer aliases (other blocks) -----------------------
    "viewer_technical_state": "B4.C3",
    "viewer_technical_validity": "B4.C4",
    "viewer_notes_observations": "B5.C1",

    # --- Ficha Técnica ----------------------------------------------------
    "ingredients_root": "B4.C1",
    "ingredients_secondary": "B4.C2",

    # --- FOOD COST --------------------------------------------------------
    "food_cost_root": "B5.C1",

    # --- PREPARAÇÃO -------------------------------------------------------
    "preparation_root": "B6.C1",

    # --- NUTRIÇÃO / ALERGÉNIOS -------------------------------------------
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

