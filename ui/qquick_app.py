"""Qt Quick bootstrap helpers for the ficha técnica viewer."""

from __future__ import annotations

import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from PyQt5.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine

from domain import Product


class OverlayController(QObject):
    """Expose the overlay toggle used by the QML scaffolding."""

    showOverlaysChanged = pyqtSignal()

    def __init__(self, show_overlays: bool = False) -> None:
        super().__init__()
        self._show_overlays = bool(show_overlays)

    @pyqtProperty(bool, notify=showOverlaysChanged)
    def showOverlays(self) -> bool:  # pragma: no cover - trivial binding
        return self._show_overlays

    @showOverlays.setter  # type: ignore[misc]
    def showOverlays(self, value: bool) -> None:
        value = bool(value)
        if self._show_overlays == value:
            return
        self._show_overlays = value
        self.showOverlaysChanged.emit()


def _resolve_qml_path(main_qml: str | Path | None = None) -> Path:
    if main_qml is not None:
        return Path(main_qml)
    return Path(__file__).resolve().parent / "qml" / "Main.qml"


def _default_show_overlays() -> bool:
    env_value = os.getenv("BWB_DEV_OVERLAYS")
    if env_value is None:
        return False
    return env_value.strip().lower() in {"1", "true", "yes", "on"}


def _product_to_mapping(product: Any | None) -> Mapping[str, Any]:
    if product is None:
        return {}
    if isinstance(product, Mapping):
        return product
    if isinstance(product, Product):
        data = asdict(product)
        data.setdefault("estado", "")
        data.setdefault("validade", "")
        data.setdefault("observacoes", "")
        return data
    if is_dataclass(product):
        return asdict(product)
    if hasattr(product, "__dict__"):
        data: dict[str, Any] = {}
        for key in dir(product):
            if key.startswith("_"):
                continue
            value = getattr(product, key)
            if callable(value):
                continue
            data[key] = value
        return data
    return {}


def create_engine(
    service: Any,
    *,
    product: Any | None = None,
    show_overlays: bool | None = None,
    main_qml: str | Path | None = None,
) -> tuple[QQmlApplicationEngine, OverlayController]:
    """Return a ``QQmlApplicationEngine`` configured for the ficha técnica UI."""

    app = QGuiApplication.instance()
    if app is None:
        QGuiApplication([])

    engine = QQmlApplicationEngine()
    context = engine.rootContext()

    if service is not None:
        context.setContextProperty("productService", service)
        datastore = getattr(service, "ds", None)
        if datastore is not None:
            context.setContextProperty("dataStore", datastore)

    if show_overlays is None:
        show_overlays = _default_show_overlays()
    overlay_controller = OverlayController(bool(show_overlays))
    context.setContextProperty("overlayController", overlay_controller)

    product_data = dict(_product_to_mapping(product))
    if not product_data:
        product_data = dict(build_sample_product())
    context.setContextProperty("productModel", product_data)

    qml_path = _resolve_qml_path(main_qml)
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        raise RuntimeError(f"Failed to load QML file: {qml_path}")

    return engine, overlay_controller


def build_sample_product() -> Mapping[str, Any]:
    """Return sample product data for preview/testing purposes."""

    return {
        "code": "FT-0001",
        "name": "Produto de Demonstração",
        "estado": "Congelado",
        "validade": "D+3",
        "observacoes": "Valores indicativos para testes de layout.",
    }


def load_qquick_app(
    service: Any,
    *,
    product: Any | None = None,
    show_overlays: bool | None = None,
    main_qml: str | Path | None = None,
) -> tuple[QGuiApplication, QQmlApplicationEngine, OverlayController]:
    """Create an application/engine triple ready to ``exec_``."""

    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication([])

    engine, overlay_controller = create_engine(
        service,
        product=product if product is not None else build_sample_product(),
        show_overlays=show_overlays if show_overlays is not None else False,
        main_qml=main_qml,
    )
    return app, engine, overlay_controller
