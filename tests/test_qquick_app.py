from __future__ import annotations

import pytest

pytest.importorskip("PyQt5")
pytest.importorskip("PyQt5.QtQml")
pytest.importorskip("PyQt5.QtQuick")

from PyQt5.QtCore import QObject

from ui.qquick_app import build_sample_product, create_engine
from ui.tagging import zone_tag, zone_tag_map


_ZONE_TAG_CACHE = dict(zone_tag_map())


def _optional_tag(key: str) -> str | None:
    return _ZONE_TAG_CACHE.get(key)


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
        assert legend_meta.get("widgetType") == "etiqueta-c"
        assert legend_meta.get("widgetQtClass") == "QLabels"

        legend_zone = _find_zone(root, "general_ident_label_codigo")
        assert legend_zone is not None
        assert legend_zone.property("overlayActive") is True
        assert legend_zone.property("zoneType") == "linha-legenda"
        assert legend_zone.property("widgetQtClass") == "QLabels"
        overlay_metadata = legend_zone.property("overlayMetadata")
        assert overlay_metadata == "linha-legenda | QLabels | etiqueta-c"

        combo_label_tags = [
            tag
            for tag in (
                _optional_tag("family_combo_label_col_1"),
                _optional_tag("family_combo_label_col_2"),
                _optional_tag("family_combo_label_col_3"),
            )
            if tag is not None
        ]
        for combo_label_tag in combo_label_tags:
            assert zones_metadata.get(combo_label_tag) is None

        combo_field_tags = [
            tag
            for tag in (
                _optional_tag("family_combo_field_col_1"),
                _optional_tag("family_combo_field_col_2"),
                _optional_tag("family_combo_field_col_3"),
            )
            if tag is not None
        ]
        for combo_field_tag in combo_field_tags:
            assert zones_metadata.get(combo_field_tag) is None

        family_label_tags = [
            zone_tag("family_label_familia"),
            zone_tag("family_label_subfamilia"),
        ]
        for family_label_tag in family_label_tags:
            family_label_meta = zones_metadata.get(family_label_tag)
            assert family_label_meta is not None
            assert family_label_meta.get("zoneType") == "linha-legenda"
            assert family_label_meta.get("widgetType") == "etiqueta-c"
            assert family_label_meta.get("widgetQtClass") == "QLabels"

            family_label_zone = _find_zone(root, family_label_tag)
            assert family_label_zone is not None
            assert family_label_zone.property("zoneType") == "linha-legenda"
            assert family_label_zone.property("widgetQtClass") == "QLabels"

        pvps_root_tag = zone_tag("pvps_root")
        pvps_root_meta = zones_metadata.get(pvps_root_tag)
        assert pvps_root_meta is not None
        assert pvps_root_meta.get("zoneType") == "secao-pvps"
        assert pvps_root_meta.get("widgetType") == "campo"
        assert pvps_root_meta.get("widgetQtClass") == "QLineEdits"

        pvps_grid_tag = zone_tag("pvps_grid")
        pvps_grid_meta = zones_metadata.get(pvps_grid_tag)
        assert pvps_grid_meta is not None
        assert pvps_grid_meta.get("zoneType") == "grade-pvps"
        assert pvps_grid_meta.get("widgetType") == "campo"
        assert pvps_grid_meta.get("widgetQtClass") == "QLineEdits"

        for idx in range(1, 6):
            legend_key = f"pvps_col_{idx}_legend"
            legend_tag = zone_tag(legend_key)
            legend_meta = zones_metadata.get(legend_tag)
            assert legend_meta is not None
            assert legend_meta.get("zoneType") == "linha-legenda"
            assert legend_meta.get("widgetType") == "etiqueta-c"
            assert legend_meta.get("widgetQtClass") == "QLabels"

            legend_zone = _find_zone(root, legend_key)
            assert legend_zone is not None
            assert legend_zone.property("zoneType") == "linha-legenda"
            assert legend_zone.property("widgetQtClass") == "QLabels"

            field_key = f"pvps_col_{idx}_field"
            field_tag = zone_tag(field_key)
            field_meta = zones_metadata.get(field_tag)
            assert field_meta is not None
            assert field_meta.get("zoneType") == "linha-campo"
            assert field_meta.get("widgetType") == "campo"
            assert field_meta.get("widgetQtClass") == "QLineEdits"

            field_zone = _find_zone(root, field_key)
            assert field_zone is not None
            assert field_zone.property("zoneType") == "linha-campo"
            assert field_zone.property("widgetQtClass") == "QLineEdits"

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

        optional_empty_metadata_tags = [
            _optional_tag("family_combos_container"),
            _optional_tag("family_combos_section"),
        ]
        for tag in optional_empty_metadata_tags:
            if tag:
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
