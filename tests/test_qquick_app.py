from __future__ import annotations

import pytest

pytest.importorskip("PyQt5")
pytest.importorskip("PyQt5.QtQml")
pytest.importorskip("PyQt5.QtQuick")

from PyQt5.QtCore import QObject

from ui.qquick_app import build_sample_product, create_engine
from ui.tagging import zone_tag, zone_tag_map


_ZONE_TAG_CACHE = dict(zone_tag_map())


def _tag_with_fallback(key: str, fallback: str) -> str:
    return _ZONE_TAG_CACHE.get(key, fallback)


class DummyService:
    def __init__(self):
        self.ds = object()


def _find_zone(root: QObject, tag_key: str) -> QObject | None:
    tag = zone_tag(tag_key)
    object_name = f"zone_{tag.replace('.', '_')}"
    return root.findChild(QObject, object_name)


def test_qquick_engine_loads_and_binds_metadata(qapp):
    service = DummyService()
    engine, overlay = create_engine(
        service,
        product={"code": "FT-42", "name": "Rissol", "estado": "Fresco"},
        show_overlays=True,
    )
    try:
        root_objects = engine.rootObjects()
        assert root_objects, "Expected QML root object to be available"
        root = root_objects[0]
        assert root.property("showDevOverlays") is True

        codigo_zone = _find_zone(root, "general_root")
        assert codigo_zone is not None
        assert codigo_zone.property("displayValue") == "FT-42"
        assert codigo_zone.property("overlayActive") is True
        assert codigo_zone.property("zoneType") == "bloco-dados-gerais"

        overlay.showOverlays = False
        qapp.processEvents()
        assert codigo_zone.property("overlayActive") is False

        overlay.showOverlays = True
        qapp.processEvents()
        assert codigo_zone.property("overlayActive") is True

        context = engine.rootContext()
        zones_metadata = context.contextProperty("zonesMetadata")
        assert isinstance(zones_metadata, dict)
        legend_tag = zone_tag("general_ident_label_codigo")
        legend_meta = zones_metadata.get(legend_tag)
        assert legend_meta is not None
        assert legend_meta.get("zoneType") == "linha-legenda"
        assert legend_meta.get("widgetQtClass") == "QLabels"

        legend_zone = _find_zone(root, "general_ident_label_codigo")
        assert legend_zone is not None
        assert legend_zone.property("overlayActive") is True
        assert legend_zone.property("zoneType") == "linha-legenda"
        assert legend_zone.property("widgetQtClass") == "QLabels"
        overlay_metadata = legend_zone.property("overlayMetadata")
        assert overlay_metadata == "linha-legenda | QLabels | legenda"

        combo_label_tags = [
            zone_tag("family_combo_label_col_1"),
            zone_tag("family_combo_label_col_2"),
            zone_tag("family_combo_label_col_3"),
        ]
        for combo_label_tag in combo_label_tags:
            assert zones_metadata.get(combo_label_tag) is None

        assert zones_metadata.get(zone_tag("family_combo_field_col_1")) is None

        family_label_tags = [
            zone_tag("family_label_familia"),
            zone_tag("family_label_subfamilia"),
        ]
        for family_label_tag in family_label_tags:
            family_label_meta = zones_metadata.get(family_label_tag)
            assert family_label_meta is not None
            assert family_label_meta.get("zoneType") == "linha-legenda"
            assert family_label_meta.get("widgetType") == "legenda"
            assert family_label_meta.get("widgetQtClass") == "QLabels"

            family_label_zone = _find_zone(root, family_label_tag)
            assert family_label_zone is not None
            assert family_label_zone.property("zoneType") == "linha-legenda"
            assert family_label_zone.property("widgetQtClass") == "QLabels"

        for idx in range(1, 6):
            legend_tag = _tag_with_fallback(
                f"pvps_col_{idx}_legend", f"B1.C1.A.2.B.B.1.{idx}.1"
            )
            assert zones_metadata.get(legend_tag) is None

            field_tag = _tag_with_fallback(
                f"pvps_col_{idx}_field", f"B1.C1.A.2.B.B.1.{idx}.2"
            )
            assert zones_metadata.get(field_tag) is None

        expected_zone_types = {
            zone_tag("family_root"): "bloco-familias-combos",
            zone_tag("ingredients_root"): "bloco-ingredientes",
            zone_tag("food_cost_root"): "bloco-food-cost",
            zone_tag("preparation_root"): "bloco-preparacao",
            zone_tag("allergens_root"): "bloco-alergenios",
        }
        for tag, expected_type in expected_zone_types.items():
            tag_meta = zones_metadata.get(tag)
            assert tag_meta is not None, f"metadata missing for {tag}"
            assert tag_meta.get("zoneType") == expected_type

        empty_metadata_tags = (
            _tag_with_fallback("family_combos_container", "B1.C1.A.2.A.2"),
            _tag_with_fallback("family_combos_section", "B1.C1.A.2.B.A"),
            _tag_with_fallback("pvps_root", "B1.C1.A.2.B.B"),
            _tag_with_fallback("pvps_grid", "B1.C1.A.2.B.B.1"),
        )
        for tag in empty_metadata_tags:
            assert zones_metadata.get(tag) is None
    finally:
        engine.deleteLater()


def test_qquick_engine_uses_sample_product_when_missing(qapp):
    engine, _ = create_engine(DummyService(), product=None, show_overlays=False)
    try:
        root = engine.rootObjects()[0]
        product = root.property("product")
        assert product["code"] == build_sample_product()["code"]
    finally:
        engine.deleteLater()
