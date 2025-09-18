from __future__ import annotations

import pytest

pytest.importorskip("PyQt5")
pytest.importorskip("PyQt5.QtQml")
pytest.importorskip("PyQt5.QtQuick")

from PyQt5.QtCore import QObject

from ui.qquick_app import build_sample_product, create_engine


class DummyService:
    def __init__(self):
        self.ds = object()


def _find_zone(root: QObject, tag: str) -> QObject | None:
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

        codigo_zone = _find_zone(root, "B1.C1")
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
        legend_meta = zones_metadata.get("B1.C1.A.1.A.1")
        assert legend_meta is not None
        assert legend_meta.get("zoneType") == "linha-legenda"
        assert legend_meta.get("widgetQtClass") == "QLabels"
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
