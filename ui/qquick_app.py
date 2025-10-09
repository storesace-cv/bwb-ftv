"""Qt Quick bootstrap helpers for the ficha técnica viewer."""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from PyQt5.QtCore import QLocale, QObject, QUrl, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QColor, QSurfaceFormat
from PyQt5.QtQuick import QQuickWindow
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication

from domain import Product

from utils.formatting import normalise_currency_context

from . import layout
from .tagging import zone_tag_map

logger = logging.getLogger(__name__)


class _AuxiliaryDataStub:
    """Provide minimal aux-table hooks required by :mod:`ui.ui_editor_fonte`."""

    def __getattr__(self, name: str):  # pragma: no cover - trivial stub
        def _method(*_args: Any, **_kwargs: Any) -> Any:
            return [] if name.startswith("list") else None

        return _method


class _MetadataDataStoreStub:
    """Emulate the subset of ``DataStore`` touched during metadata snapshots."""

    def __init__(self) -> None:
        self.aux = _AuxiliaryDataStub()
        self.fcost = object()
        self._prep_html: dict[str, str] = {}
        self._fcost_level: Any = None

    def get_preparacao_html(self, codigo: str) -> str:
        return self._prep_html.get(codigo, "")

    def save_preparacao_html(self, codigo: str, html: str) -> None:
        self._prep_html[codigo] = html or ""

    def set_fcost_level(self, level: Any) -> None:
        self._fcost_level = level


class _MetadataServiceStub:
    """Lightweight service exposing the API expected by :class:`FTApp`."""

    def __init__(self) -> None:
        self.ds = _MetadataDataStoreStub()
        self._product = Product(code="FT-METADATA", name="Metadata Stub")

    # --- Product navigation -------------------------------------------------
    def codigo_at(self, _idx: int) -> str:
        return self._product.code

    def total(self) -> int:
        return 1

    # --- Product payload ----------------------------------------------------
    def get_product_info(self, _codigo: str) -> Product:
        return self._product

    def list_fichas_tecnicas(self, _codigo: str) -> list[Any]:
        return []

    def calculate_cost(self, _product: Product) -> float:
        return 0.0

    # --- Auxiliary lookups --------------------------------------------------
    def list_tipos_artigos(self) -> list[Any]:
        return []

    def list_validade(self) -> list[Any]:
        return []

    def list_temperaturas(self) -> list[Any]:
        return []

    # --- Mutators / no-ops --------------------------------------------------
    def set_product_allergens(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def set_tipo_artigo(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def set_validade(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def set_temperatura(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def save_product_image(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def delete_product_image(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def save_preparacao_image(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def delete_preparacao_image(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    # --- Lookups returning empty payloads ----------------------------------
    def get_image_path(self, *_args: Any, **_kwargs: Any) -> str:
        return ""

    def get_preparacao_image_path(self, *_args: Any, **_kwargs: Any) -> str:
        return ""

    def list_active_allergens(self) -> list[Any]:
        return []

    def get_allergen_details(self, *_args: Any, **_kwargs: Any) -> Any:
        return None

    def get_product_allergens(self, *_args: Any, **_kwargs: Any) -> list[Any]:
        return []


_ZONE_METADATA_CACHE: dict[str, Any] | None = None


def _collect_zone_metadata_snapshot() -> dict[str, Any]:
    """Materialise ``ZoneMetadata`` for every widget zone once."""

    global _ZONE_METADATA_CACHE
    if _ZONE_METADATA_CACHE is not None:
        return _ZONE_METADATA_CACHE

    try:
        from .ui_editor_fonte import FTApp
    except Exception:  # pragma: no cover - guard for stripped builds
        logger.exception("Failed to import widget editor for metadata snapshot")
        _ZONE_METADATA_CACHE = {}
        return _ZONE_METADATA_CACHE

    widget = FTApp(_MetadataServiceStub())
    widget.hide()
    try:
        snapshot: dict[str, Any] = {}
        for zone in widget.findChildren(layout.Zone):
            data = zone.to_metadata().as_dict()
            snapshot[data["tag"]] = data
        _ZONE_METADATA_CACHE = snapshot
        return snapshot
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Failed to build zone metadata snapshot")
        _ZONE_METADATA_CACHE = {}
        return _ZONE_METADATA_CACHE
    finally:
        widget.deleteLater()


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

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    _ensure_translucent_quick_windows()

    zones_metadata = dict(_collect_zone_metadata_snapshot())

    engine = QQmlApplicationEngine()
    context = engine.rootContext()

    currency_context = normalise_currency_context({})

    if service is not None:
        context.setContextProperty("productService", service)
        datastore = getattr(service, "ds", None)
        if datastore is not None:
            context.setContextProperty("dataStore", datastore)
            get_locale = getattr(datastore, "get_localizacao_ativa", None)
            if callable(get_locale):
                try:
                    currency_context = normalise_currency_context(
                        get_locale(), defaults=currency_context
                    )
                except Exception:
                    logger.debug(
                        "[QQuick] Falha ao obter localização ativa; a usar omissões.",
                        exc_info=True,
                    )

    context.setContextProperty("ftvCurrency", currency_context)
    locale_code = currency_context.get("locale_code")
    if locale_code:
        try:
            QLocale.setDefault(QLocale(str(locale_code)))
        except Exception:
            logger.debug(
                "[QQuick] Falha ao aplicar QLocale padrão '%s'", locale_code,
                exc_info=True,
            )

    if show_overlays is None:
        show_overlays = _default_show_overlays()
    overlay_controller = OverlayController(bool(show_overlays))
    context.setContextProperty("overlayController", overlay_controller)

    product_data = dict(_product_to_mapping(product))
    if not product_data:
        product_data = dict(build_sample_product())
    context.setContextProperty("productModel", product_data)
    context.setContextProperty("zonesMetadata", zones_metadata)
    context.setContextProperty("zoneOverlayLightenStep", layout.OVERLAY_LIGHTEN_STEP)
    context.setContextProperty("zoneOverlayLightenMax", layout.OVERLAY_LIGHTEN_MAX)
    context.setContextProperty("zoneTagMap", dict(zone_tag_map()))

    qml_path = _resolve_qml_path(main_qml)
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    root_objects = engine.rootObjects()
    if not root_objects:
        raise RuntimeError(f"Failed to load QML file: {qml_path}")

    _apply_transparent_background(root_objects)

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
) -> tuple[QApplication, QQmlApplicationEngine, OverlayController]:
    """Create an application/engine triple ready to ``exec``."""

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    engine, overlay_controller = create_engine(
        service,
        product=product if product is not None else build_sample_product(),
        show_overlays=show_overlays if show_overlays is not None else False,
        main_qml=main_qml,
    )
    return app, engine, overlay_controller


def _ensure_translucent_quick_windows() -> None:
    """Guarantee Qt Quick surfaces reserve an alpha buffer."""

    QQuickWindow.setDefaultAlphaBuffer(True)

    current_format = QSurfaceFormat.defaultFormat()
    if current_format.alphaBufferSize() >= 8:
        return

    current_format.setAlphaBufferSize(8)
    QSurfaceFormat.setDefaultFormat(current_format)


def _apply_transparent_background(root_objects: Iterable[QObject]) -> None:
    """Ensure the root QML windows preserve a transparent background."""

    for obj in root_objects:
        set_color = getattr(obj, "setColor", None)
        if not callable(set_color):
            continue
        try:
            set_color(QColor("transparent"))
        except Exception:  # pragma: no cover - defensive safety net
            logger.debug(
                "[QQuick] Falha ao aplicar fundo transparente a %r.",
                obj,
                exc_info=True,
            )
