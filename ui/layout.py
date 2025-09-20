"""Componentes de layout para a ficha técnica.

Aviso: legendas usadas pelos overlays de desenvolvimento têm estilos inline
específicos; não utilize ``apply_label_style`` nem folhas de estilo globais
nesses rótulos.
"""

import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Sequence

from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QToolTip,
)

from .utilities import (
    AlignmentVariant,
    OVERLAY_ON_CLASS,
    _normalize_alignment,
    apply_label_style,
    apply_overlay_label_style,
)


_ENV_DEV_OVERLAYS = os.getenv("BWB_DEV_OVERLAYS")
DEV_OVERLAYS = (
    _ENV_DEV_OVERLAYS.strip().lower() in {"1", "true", "yes", "on"}
    if _ENV_DEV_OVERLAYS is not None
    else False
)

DEFAULT_ZONE_MARGINS = (3, 5)
# Default maximum widget width used by Qt when no explicit constraint is set.
_QT_MAX_WIDGET_WIDTH = 16777215

_DEFAULT_ZONE_BASE_DECLARATIONS = (
    "border-radius: 12px;\n",
    "padding: 6px;\n",
)

# Updated to allow block-prefixed cell identifiers like ``B1.C1``
_TAG_RE = re.compile(r"^B\d+(?:\.C\d+(?:\.(?:A|B|\d+))*)?$")


def _escape_object_name(name: str) -> str:
    """Return ``name`` escaped for usage within Qt style sheets."""

    return re.sub(r"([^\w-])", r"\\\1", name)


def compose_stylesheet(widget: QWidget, declarations: str) -> str:
    """Return a stylesheet applying ``declarations`` to ``widget``."""

    selector = (
        f"#{_escape_object_name(widget.objectName())}" if widget.objectName() else ""
    )
    return f"{selector} {{ {declarations} }}" if selector else declarations


def validate_tag(tag: str) -> bool:
    """Return ``True`` if ``tag`` complies with the expected pattern."""

    return bool(_TAG_RE.fullmatch(tag))


def bg_for_level(level: int) -> str:
    colors = ["#eafbf1", "#eef5ff", "#fff5e8", "#f7f0ff", "#fff0f0"]
    return colors[level % len(colors)] if DEV_OVERLAYS else "transparent"


def refresh_style(widget: QWidget) -> None:
    """Force ``widget`` to refresh its style after property updates."""

    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


_KEEP_LABEL = object()


class _ZoneLabelList(list[QLabel]):
    """List that keeps zone label metadata in sync."""

    def __init__(self, zone: "Zone") -> None:
        super().__init__()
        self._zone = zone

    def append(self, label: QLabel) -> None:  # type: ignore[override]
        super().append(label)
        self._zone._on_label_registered(label)

    def extend(self, labels: Iterable[QLabel]) -> None:  # type: ignore[override]
        for label in labels:
            self.append(label)

    def insert(self, index: int, label: QLabel) -> None:  # type: ignore[override]
        super().insert(index, label)
        self._zone._on_label_registered(label)


def _clear_overlay_class(label: QLabel) -> None:
    """Remove the overlay marker class from ``label`` if present."""

    value = label.property("class")
    if value is None:
        return
    if isinstance(value, str):
        classes = value.split()
    elif isinstance(value, (list, tuple)):
        classes = [str(cls) for cls in value if str(cls)]
    else:
        text = str(value).strip()
        classes = [text] if text else []
    filtered = [cls for cls in classes if cls != OVERLAY_ON_CLASS]
    if filtered:
        label.setProperty("class", " ".join(filtered))
    else:
        label.setProperty("class", None)


class _OverlayMetadataClickFilter(QObject):
    """Show the zone metadata tooltip when a target widget is clicked."""

    def __init__(self, zone: "Zone") -> None:
        super().__init__(zone)
        self._zone = zone

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # type: ignore[override]
        event_type = event.type()
        if event_type == QEvent.ToolTip:
            if self._zone._overlay_active and self._zone._metadata_tooltip_text:
                widget = watched if isinstance(watched, QWidget) else None
                if widget is not None:
                    global_pos = (
                        event.globalPos()
                        if hasattr(event, "globalPos")
                        else None
                    )
                    if global_pos is None:
                        pos = getattr(event, "pos", lambda: None)()
                        if pos is not None:
                            pos_point = pos.toPoint() if hasattr(pos, "toPoint") else pos
                            global_pos = widget.mapToGlobal(pos_point)
                    if global_pos is not None:
                        QToolTip.showText(
                            global_pos,
                            self._zone._metadata_tooltip_text,
                            self._zone,
                        )
                        if hasattr(event, "accept"):
                            event.accept()
                        return True
        elif (
            event_type == QEvent.MouseButtonPress
            and self._zone._overlay_active
            and self._zone._metadata_tooltip_text
        ):
            widget = watched if isinstance(watched, QWidget) else None
            if widget is not None:
                pos = getattr(event, "pos", lambda: None)()
                if pos is not None:
                    pos_point = pos.toPoint() if hasattr(pos, "toPoint") else pos
                    QToolTip.showText(
                        widget.mapToGlobal(pos_point),
                        self._zone._metadata_tooltip_text,
                        self._zone,
                    )
        return QObject.eventFilter(self, watched, event)


@dataclass(slots=True)
class ZoneMetadata:
    """Serializable snapshot of a :class:`Zone` for Qt Quick bindings."""

    tag: str
    level: int = 0
    zone_type: str | None = None
    widget_type: str | None = None
    widget_qt_class: str | None = None
    base_style_label: str | None = None
    margin_h: int | None = None
    margin_v: int | None = None
    overlays_active: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "level": self.level,
            "zoneType": self.zone_type,
            "widgetType": self.widget_type,
            "widgetQtClass": self.widget_qt_class,
            "baseStyleLabel": self.base_style_label,
            "marginH": self.margin_h,
            "marginV": self.margin_v,
            "overlaysActive": self.overlays_active,
        }


class Zone(QWidget):
    """Célula real (com tag e overlay opcional)."""

    _WIDGET_QT_CLASS_MAP = {
        "campo": "QLineEdits",
        "legenda": "QLabels",
        "etiqueta-c": "QLabels",
        "lista": "QComboBoxes",
        "tabela": "QTableViews",
        "botão": "QPushButtons",
        "editor": "QTextEdits",
        "caixa de seleção": "QCheckBoxes",
    }

    def __init__(
        self,
        tag: str,
        parent=None,
        flow="v",
        margins: int | tuple[int, int] | None = DEFAULT_ZONE_MARGINS,
        *,
        margin_h: int | None = None,
        margin_v: int | None = None,
        spacing=6,
        level: int = 0,
        show_overlays: bool = True,
        base_stylesheet: str | None = None,
        base_style_label: str | None = None,
        widget_type: str | None = None,
        zone_type: str | None = None,
        widget_qt_class: str | None = None,
    ):
        if not validate_tag(tag):
            raise ValueError(f"Invalid zone tag: {tag}")
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.tag = tag
        self.setObjectName(tag)
        self._level = level
        self._legend_label_force_expanding = False
        self._labels: _ZoneLabelList = _ZoneLabelList(self)
        self._overlay_active = False
        self._label_alignment = AlignmentVariant.DEFAULT
        self._base_style_label: str | None = base_style_label or None
        self._widget_type: str | None = widget_type or None
        self._zone_type: str | None = zone_type or None
        self._widget_qt_class: str | None = widget_qt_class or None
        self._style_dev_info: str | None = None
        self._suspend_base_tracking = False
        self._next_base_style_label: Any = _KEEP_LABEL
        self._metadata_snapshot: dict[str, str] = {}
        self._metadata_tooltip_text: str = ""
        self._metadata_click_filter = _OverlayMetadataClickFilter(self)
        self._overlay_metadata_targets: set[QWidget] = set()
        self._rows: list[tuple[QWidget, QLabel, QWidget]] = []
        self._update_metadata_snapshot(
            zone_type=self._zone_type,
            widget_type=self._widget_type,
            widget_qt_class=self._widget_qt_class,
            base_style_label=self._base_style_label,
        )
        if flow == "v":
            self.ly = QVBoxLayout(self)
        else:
            self.ly = QHBoxLayout(self)

        if margins is None:
            margin_h_val, margin_v_val = DEFAULT_ZONE_MARGINS
        elif isinstance(margins, (tuple, list)):
            if len(margins) != 2:
                raise ValueError("Expected a (horizontal, vertical) margin tuple")
            margin_h_val, margin_v_val = margins
        else:
            margin_h_val = margin_v_val = margins

        if margin_h is not None:
            margin_h_val = margin_h
        if margin_v is not None:
            margin_v_val = margin_v

        self._margin_h = int(margin_h_val)
        self._margin_v = int(margin_v_val)
        self._margin_spec: tuple[int, int] = (self._margin_h, self._margin_v)

        if self._margin_spec == DEFAULT_ZONE_MARGINS:
            self.ly.setContentsMargins(3, 5, 3, 5)
        else:
            self.ly.setContentsMargins(
                self._margin_h,
                self._margin_v,
                self._margin_h,
                self._margin_v,
            )
        self.ly.setSpacing(spacing)

        self._tag_container = QWidget(self)
        header_layout = QVBoxLayout(self._tag_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        self._tag_lbl = QLabel(self.tag, self._tag_container)
        self._tag_lbl.setStyleSheet(
            "color:#c00; font-size:10px; background:none; border:none;"
        )
        self._tag_lbl.setFixedHeight(12)
        header_layout.addWidget(self._tag_lbl, 0, Qt.AlignLeft)

        self._style_lbl = QLabel("", self._tag_container)
        self._style_lbl.setStyleSheet(
            "color:#c00; font-size:10px; background:none; border:none;"
        )
        self._style_lbl.setFixedHeight(12)
        self._style_lbl.hide()
        header_layout.addWidget(self._style_lbl, 0, Qt.AlignLeft)

        self._tag_container_alignment = Qt.AlignLeft
        self.ly.addWidget(self._tag_container, 0, self._tag_container_alignment)
        self._tag_container_index = self.ly.indexOf(self._tag_container)
        if self._tag_container_index < 0:
            self._tag_container_index = 0

        selector = f"#{_escape_object_name(self.objectName())}" if self.objectName() else ""
        default_stylesheet = (
            f"{selector} {{ background: transparent; border: none; }}"
            if selector
            else "background: transparent; border: none;"
        )

        initial_label: Any = (
            self._base_style_label if self._base_style_label is not None else _KEEP_LABEL
        )
        self._base_stylesheet = ""
        self.set_zone_stylesheet(default_stylesheet, label=initial_label)
        self.apply_overlays(show_overlays)

        if base_stylesheet is not None:
            self.set_zone_stylesheet(base_stylesheet, label=initial_label)
        elif base_style_label is not None:
            self._sync_style_label()

    @staticmethod
    def _build_label_tooltip(
        user_label: str | None, dev_label: str | None
    ) -> str:
        segments = [
            str(segment)
            for segment in (user_label, dev_label)
            if segment
        ]
        return " — ".join(segments) if segments else ""

    @property
    def widget_type(self) -> str | None:
        return self._widget_type

    def set_widget_type(self, widget_type: str | None) -> None:
        self._widget_type = widget_type or None
        self._update_metadata_snapshot(widget_type=self._widget_type)
        self._sync_style_label()

    @property
    def base_style_label(self) -> str | None:
        return self._base_style_label

    @property
    def level(self) -> int:
        return self._level

    @property
    def margin_h(self) -> int:
        return self._margin_h

    @property
    def margin_v(self) -> int:
        return self._margin_v

    @property
    def overlays_active(self) -> bool:
        return bool(self._overlay_active)

    @property
    def zone_type(self) -> str | None:
        return self._zone_type

    def set_zone_type(self, zone_type: str | None) -> None:
        self._zone_type = zone_type or None
        self._update_metadata_snapshot(zone_type=self._zone_type)
        self._sync_style_label()

    def set_style_dev_info(self, info: str | None) -> None:
        self._style_dev_info = info or None
        self._update_metadata_snapshot(style_dev_info=self._style_dev_info)
        self._sync_style_label()

    @property
    def widget_qt_class(self) -> str | None:
        return self._widget_qt_class

    def set_widget_qt_class(self, widget_qt_class: str | None) -> None:
        self._widget_qt_class = widget_qt_class or None
        self._update_metadata_snapshot(widget_qt_class=self._widget_qt_class)
        self._sync_style_label()

    @classmethod
    def _resolve_widget_qt_class(cls, widget_type: str | None) -> str | None:
        if widget_type is None:
            return None
        return cls._WIDGET_QT_CLASS_MAP.get(widget_type)

    @staticmethod
    def _normalize_declarations(
        declarations: str | Sequence[str] | None,
    ) -> str:
        if declarations is None:
            declarations = _DEFAULT_ZONE_BASE_DECLARATIONS
        if isinstance(declarations, (list, tuple)):
            return "".join(str(part) for part in declarations)
        return str(declarations)

    def apply_metadata(
        self,
        *,
        zone_type: str | None = None,
        widget_type: str | None = None,
        style_dev_info: str | None = None,
        base_declarations: str | Sequence[str] | None = None,
        apply_base_style: bool = True,
        base_style_label: str | None = None,
    ) -> "Zone":
        if apply_base_style:
            declarations_text = self._normalize_declarations(base_declarations)
            self.set_zone_stylesheet(
                compose_stylesheet(self, declarations_text),
                label=base_style_label,
            )
        elif base_style_label is not None:
            self.set_zone_stylesheet(
                self.base_stylesheet,
                label=base_style_label,
            )

        if zone_type is not None:
            self.set_zone_type(zone_type)

        effective_widget_type = widget_type
        if widget_type is not None:
            self.set_widget_type(widget_type)
        elif self.widget_type is not None:
            effective_widget_type = self.widget_type

        if effective_widget_type is not None:
            self.set_widget_qt_class(
                self._resolve_widget_qt_class(effective_widget_type)
            )
            if effective_widget_type == "etiqueta-c":
                apply_bwb_etiqueta_c_normal(self)
        effective_zone_type = zone_type if zone_type is not None else self.zone_type
        self._configure_legend_label_policy(
            effective_zone_type == "linha-legenda"
            and effective_widget_type in {"legenda", "etiqueta-c"}
        )
        info = style_dev_info if style_dev_info is not None else self.objectName()
        self.set_style_dev_info(info)
        return self

    def to_metadata(self) -> ZoneMetadata:
        """Return a :class:`ZoneMetadata` snapshot of the current zone."""

        snapshot = self._metadata_snapshot
        return ZoneMetadata(
            tag=self.tag,
            level=self.level,
            zone_type=self.zone_type or snapshot.get("zone_type"),
            widget_type=self.widget_type or snapshot.get("widget_type"),
            widget_qt_class=self.widget_qt_class
            or snapshot.get("widget_qt_class"),
            base_style_label=self.base_style_label
            or snapshot.get("base_style_label"),
            margin_h=self.margin_h,
            margin_v=self.margin_v,
            overlays_active=self.overlays_active,
        )

    @property
    def base_stylesheet(self) -> str:
        return self._base_stylesheet

    def set_zone_stylesheet(
        self,
        stylesheet: str,
        *,
        label: str | None | Any = _KEEP_LABEL,
    ) -> None:
        if not isinstance(stylesheet, str):
            raise TypeError("Stylesheet must be a string")

        if self._overlay_active:
            self._base_stylesheet = stylesheet
            if label is not _KEEP_LABEL:
                self._base_style_label = label
                self._update_metadata_snapshot(
                    base_style_label=self._base_style_label
                )
            self._sync_style_label()
            return

        previous_next_label = self._next_base_style_label
        try:
            if label is not _KEEP_LABEL:
                self._next_base_style_label = label
            self.setStyleSheet(stylesheet)
        finally:
            self._next_base_style_label = previous_next_label

    def _update_metadata_snapshot(
        self,
        *,
        zone_type: str | None = None,
        widget_type: str | None = None,
        widget_qt_class: str | None = None,
        base_style_label: str | None = None,
        style_dev_info: str | None = None,
    ) -> None:
        mapping = (
            ("zone_type", zone_type),
            ("widget_type", widget_type),
            ("widget_qt_class", widget_qt_class),
            ("base_style_label", base_style_label),
            ("style_dev_info", style_dev_info),
        )
        for key, value in mapping:
            if value is None or value == "":
                self._metadata_snapshot.pop(key, None)
            elif value:
                self._metadata_snapshot[key] = value
        self._refresh_metadata_tooltip()

    def _refresh_metadata_tooltip(self) -> None:
        snapshot = self._metadata_snapshot

        def _resolve(attr_name: str, key: str) -> str | None:
            value = getattr(self, attr_name)
            if value:
                return value
            return snapshot.get(key)

        entries: list[str] = []

        def _append(label: str, value: str | None) -> None:
            if value:
                entries.append(f"{label}: {value}")

        _append("tag", self.tag)
        _append("zoneType", _resolve("_zone_type", "zone_type"))
        _append("widgetType", _resolve("_widget_type", "widget_type"))
        _append("widgetQtClass", _resolve("_widget_qt_class", "widget_qt_class"))
        _append(
            "baseStyleLabel",
            _resolve("_base_style_label", "base_style_label"),
        )
        _append(
            "style_dev_info",
            _resolve("_style_dev_info", "style_dev_info"),
        )
        self._metadata_tooltip_text = "\n".join(entries)

    def _sync_style_label(self) -> None:
        self._style_lbl.clear()
        self._style_lbl.hide()
        self._style_lbl.setToolTip("")
        refresh_style(self._style_lbl)
        self._refresh_metadata_tooltip()

    def _iter_metadata_tooltip_widgets(self):
        yield self
        yield self._tag_container
        yield self._tag_lbl
        yield self._style_lbl
        for row, label, value_widget in self._rows:
            yield row
            yield label
            yield value_widget

    def _register_overlay_metadata_target(self, widget: QWidget | None) -> None:
        if widget is None or not isinstance(widget, QWidget):
            return
        if widget in self._overlay_metadata_targets:
            return
        previous_flag = widget.testAttribute(Qt.WA_AlwaysShowToolTips)
        widget.setProperty("_zoneOverlayPrevAlwaysShowToolTips", previous_flag)
        widget.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        widget.installEventFilter(self._metadata_click_filter)
        self._overlay_metadata_targets.add(widget)
        widget.destroyed.connect(  # type: ignore[union-attr]
            lambda _=None, w=widget: self._overlay_metadata_targets.discard(w)
        )

    def _install_metadata_click_filters(self) -> None:
        for widget in self._iter_metadata_tooltip_widgets():
            self._register_overlay_metadata_target(widget)

    def _remove_metadata_click_filters(self) -> None:
        for widget in list(self._overlay_metadata_targets):
            try:
                widget.removeEventFilter(self._metadata_click_filter)
            except RuntimeError:
                # Widget may have been deleted while overlays were active.
                pass
            previous_flag = widget.property("_zoneOverlayPrevAlwaysShowToolTips")
            widget.setProperty("_zoneOverlayPrevAlwaysShowToolTips", None)
            try:
                widget.setAttribute(
                    Qt.WA_AlwaysShowToolTips, bool(previous_flag)
                )
            except Exception:
                # Some QWidget subclasses may refuse attribute changes during
                # teardown; ignore and continue cleanup.
                pass
        self._overlay_metadata_targets.clear()

    def _on_label_registered(self, label: QLabel) -> None:
        self._apply_registered_label_policy(label)

    def _apply_registered_label_policy(self, label: QLabel) -> None:
        if not self._legend_label_force_expanding:
            return
        policy = label.sizePolicy()
        if policy.horizontalPolicy() == QSizePolicy.Expanding:
            return
        policy.setHorizontalPolicy(QSizePolicy.Expanding)
        label.setSizePolicy(policy)

    def _configure_legend_label_policy(self, enabled: bool) -> None:
        self._legend_label_force_expanding = enabled
        if not enabled:
            return
        zone_policy = self.sizePolicy()
        if zone_policy.horizontalPolicy() != QSizePolicy.Expanding:
            zone_policy.setHorizontalPolicy(QSizePolicy.Expanding)
            self.setSizePolicy(zone_policy)
        for registered_label in self._labels:
            self._apply_registered_label_policy(registered_label)

    def _label_alignment_flag(self) -> Qt.Alignment:
        if self._label_alignment is AlignmentVariant.RIGHT:
            return Qt.AlignRight | Qt.AlignVCenter
        return Qt.AlignHCenter | Qt.AlignVCenter

    def set_label_alignment(
        self, alignment: AlignmentVariant | str | None
    ) -> None:
        variant = _normalize_alignment(alignment)
        self._label_alignment = variant
        alignment_flag = self._label_alignment_flag()
        for lbl in self._labels:
            lbl.setProperty("labelAlignmentVariant", variant.value)
            if self._overlay_active:
                lbl.setAlignment(alignment_flag)
                refresh_style(lbl)
                continue
            if lbl.property("prefersQtDefaultLabelStyle"):
                _clear_overlay_class(lbl)
                lbl.setStyleSheet("")
                lbl.setAlignment(alignment_flag)
                refresh_style(lbl)
                continue
            extra = lbl.property("labelExtraStyle")
            apply_label_style(
                lbl,
                extra if extra else None,
                alignment=variant,
            )
            refresh_style(lbl)
        if not self._overlay_active:
            self.sync_label_widths()

    def apply_overlays(self, on: bool) -> None:
        active = bool(on) and DEV_OVERLAYS
        self._overlay_active = active
        self.setProperty("overlays", "on" if active else "off")
        if active:
            self._install_metadata_click_filters()
        else:
            self._remove_metadata_click_filters()
        name = self.objectName()
        selector = f"#{_escape_object_name(name)}" if name else ""
        header_present = self.ly.indexOf(self._tag_container) != -1
        if active:
            style = (
                f"{selector} {{ background:{bg_for_level(self._level)}; border:2px dashed blue; }}"
                if selector
                else f"background:{bg_for_level(self._level)}; border:2px dashed blue;"
            )
            self._suspend_base_tracking = True
            try:
                self.setStyleSheet(style)
            finally:
                self._suspend_base_tracking = False
            if not header_present:
                self.ly.insertWidget(
                    self._tag_container_index,
                    self._tag_container,
                    0,
                    self._tag_container_alignment,
                )
            self._tag_container.show()
            self._tag_lbl.show()
        else:
            self._suspend_base_tracking = True
            try:
                self.setStyleSheet(self._base_stylesheet)
            finally:
                self._suspend_base_tracking = False
            if header_present:
                self.ly.removeWidget(self._tag_container)
            self._tag_container.hide()
            self._tag_lbl.hide()
        self._sync_style_label()
        for lbl in self._labels:
            user_label = lbl.property("userLabel")
            dev_label = lbl.property("devLabel")
            lbl.setText(dev_label if active and dev_label else user_label)
            tooltip = self._build_label_tooltip(user_label, dev_label)
            lbl.setToolTip("" if active else tooltip)
            font = QFont(lbl.font())
            previous_alignment = lbl.alignment()
            alignment_flag = self._label_alignment_flag()
            lbl.setProperty("labelAlignmentVariant", self._label_alignment.value)
            if active:
                apply_overlay_label_style(lbl)
                lbl.setAlignment(previous_alignment)
            else:
                extra = lbl.property("labelExtraStyle")
                if lbl.property("prefersQtDefaultLabelStyle"):
                    _clear_overlay_class(lbl)
                    lbl.setStyleSheet("")
                    lbl.setAlignment(alignment_flag)
                else:
                    apply_label_style(
                        lbl,
                        extra if extra else None,
                        alignment=self._label_alignment,
                    )
                    lbl.setAlignment(alignment_flag)
            lbl.setFont(font)
            refresh_style(lbl)
        self.sync_label_widths()
        refresh_style(self._tag_lbl)
        refresh_style(self)
        for ch in self.findChildren(Zone):
            ch.apply_overlays(on)

    def setStyleSheet(self, stylesheet: str) -> None:  # type: ignore[override]
        QWidget.setStyleSheet(self, stylesheet)
        if self._suspend_base_tracking:
            refresh_style(self)
            return

        self._base_stylesheet = stylesheet
        if self._next_base_style_label is not _KEEP_LABEL:
            self._base_style_label = self._next_base_style_label
        self._next_base_style_label = _KEEP_LABEL
        self._update_metadata_snapshot(
            base_style_label=self._base_style_label
        )
        self._sync_style_label()
        refresh_style(self)

    def add(self, w: QWidget, stretch: int = 0) -> None:
        self.ly.addWidget(w, stretch)

    def add_row(
        self,
        label_text: str,
        value_widget: QWidget,
        label_minw: int | None = None,
        vspacing: int = 2,
        overlay_text: str | None = None,
        *,
        debug_styles: bool = False,
    ) -> QLabel:
        row = QWidget(self)
        row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if debug_styles:
            row.setStyleSheet(
                "background-color: rgba(0, 0, 0, 0.05); border-radius: 4px;"
            )
        grid = QGridLayout(row)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(min(vspacing, 5))
        grid.setColumnStretch(1, 1)
        display = (
            overlay_text
            if (self._overlay_active and overlay_text is not None)
            else label_text
        )
        lbl = QLabel(display, row)
        debug_extra = (
            "QLabel { background-color: rgba(0, 0, 0, 0.03); border-radius: 4px; }"
            if debug_styles
            else None
        )
        lbl.setProperty("labelExtraStyle", debug_extra)
        if self._overlay_active:
            apply_overlay_label_style(lbl)
            lbl.setAlignment(self._label_alignment_flag())
            lbl.setProperty("labelAlignmentVariant", self._label_alignment.value)
        else:
            apply_label_style(lbl, debug_extra, alignment=self._label_alignment)
        lbl.setProperty("userLabel", label_text)
        lbl.setProperty("devLabel", overlay_text)
        if label_minw is not None:
            lbl.setProperty("labelMinimumWidth", int(label_minw))
            lbl.setFixedWidth(label_minw)
        else:
            lbl.setProperty("labelMinimumWidth", None)
        value_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if debug_styles:
            try:
                existing_style = value_widget.styleSheet()
                extra = "background-color: rgba(0, 0, 0, 0.03); border-radius: 4px;"
                value_widget.setStyleSheet(
                    (existing_style + (" " if existing_style else "")) + extra
                )
            except Exception:
                pass
        grid.addWidget(lbl, 0, 0, alignment=self._label_alignment_flag())
        grid.addWidget(value_widget, 0, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.ly.addWidget(row, 0)
        self._labels.append(lbl)
        self._rows.append((row, lbl, value_widget))
        if self._overlay_active:
            lbl.setToolTip("")
        else:
            tooltip = (
                self._build_label_tooltip(label_text, overlay_text)
                if overlay_text is not None
                else ""
            )
            lbl.setToolTip(tooltip)
        if self._overlay_active:
            self._register_overlay_metadata_target(row)
            self._register_overlay_metadata_target(lbl)
            self._register_overlay_metadata_target(value_widget)
        self.sync_label_widths()
        return lbl

    def sync_label_widths(self) -> None:
        if not self._labels:
            return
        min_widths: list[int] = []
        target_widths: list[int] = []
        for label in self._labels:
            # Release any fixed width constraint so the label's size hint reflects
            # the currently visible text before we compute the shared width.
            label.setMinimumWidth(0)
            label.setMaximumWidth(_QT_MAX_WIDGET_WIDTH)
            label.updateGeometry()
            stored_min = label.property("labelMinimumWidth")
            try:
                min_width = int(stored_min)
            except (TypeError, ValueError):
                min_width = 0
            min_width = max(min_width, 0)
            min_widths.append(min_width)
            target_widths.append(max(label.sizeHint().width(), min_width))
        maxw = max(target_widths)
        for label, min_width in zip(self._labels, min_widths):
            label.setFixedWidth(max(maxw, min_width))

    def split_h(
        self,
        ratios=(1, 1),
        *,
        zone_type: str | None = None,
        widget_type: str | None = None,
        widget_qt_class: str | None = None,
    ):
        cont = QWidget(self)
        cont.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        h = QHBoxLayout(cont)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(self.ly.spacing())
        if len(ratios) == 2:
            tags = ["A", "B"]
        else:
            tags = [str(i) for i in range(1, len(ratios) + 1)]
        zones = []
        for tag_suf, ratio in zip(tags, ratios):
            tag = f"{self.tag}.{tag_suf}"
            if not validate_tag(tag):
                raise ValueError(f"Invalid zone tag: {tag}")
            child_zone_type = self._zone_type if zone_type is None else zone_type
            child_widget_type = (
                self._widget_type if widget_type is None else widget_type
            )
            child_widget_qt_class = (
                self._widget_qt_class
                if widget_qt_class is None
                else widget_qt_class
            )
            zone = Zone(
                tag,
                cont,
                flow="v",
                margins=self._margin_spec,
                spacing=self.ly.spacing(),
                level=self._level + 1,
                show_overlays=DEV_OVERLAYS,
                base_style_label=self._base_style_label,
                widget_type=child_widget_type,
                zone_type=child_zone_type,
                widget_qt_class=child_widget_qt_class,
            )
            h.addWidget(zone, ratio)
            zones.append(zone)
        self.ly.addWidget(cont, 1)
        return tuple(zones)

    def split_v(
        self,
        ratios=(1, 1),
        *,
        zone_type: str | None = None,
        widget_type: str | None = None,
        widget_qt_class: str | None = None,
    ):
        cont = QWidget(self)
        cont.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        v = QVBoxLayout(cont)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(self.ly.spacing())
        zones = []
        for idx, ratio in enumerate(ratios, start=1):
            tag = f"{self.tag}.{idx}"
            if not validate_tag(tag):
                raise ValueError(f"Invalid zone tag: {tag}")
            child_zone_type = self._zone_type if zone_type is None else zone_type
            child_widget_type = (
                self._widget_type if widget_type is None else widget_type
            )
            child_widget_qt_class = (
                self._widget_qt_class
                if widget_qt_class is None
                else widget_qt_class
            )
            zone = Zone(
                tag,
                cont,
                flow="v",
                margins=self._margin_spec,
                spacing=self.ly.spacing(),
                level=self._level + 1,
                show_overlays=DEV_OVERLAYS,
                base_style_label=self._base_style_label,
                widget_type=child_widget_type,
                zone_type=child_zone_type,
                widget_qt_class=child_widget_qt_class,
            )
            v.addWidget(zone, ratio)
            zones.append(zone)
        self.ly.addWidget(cont, 1)
        return tuple(zones)


def apply_bwb_etiqueta_c_normal(zone: Zone) -> None:
    """Apply the etiqueta-c default: centered labels with stripped spacing CSS."""

    # etiqueta-c zones now default to centered labels while keeping the
    # zero-margin/padding cleanup required by their legacy stylesheet.
    zone.set_label_alignment(AlignmentVariant.CENTER)
    zone.ly.setContentsMargins(0, 0, 0, 0)
    stylesheet = zone.base_stylesheet
    selector = (
        f"#{_escape_object_name(zone.objectName())}" if zone.objectName() else ""
    )
    declarations_text = ""
    if stylesheet:
        stripped = stylesheet.strip()
        if selector and stripped.startswith(selector):
            open_brace = stripped.find("{")
            close_brace = stripped.rfind("}")
            if 0 <= open_brace < close_brace:
                declarations_text = stripped[open_brace + 1 : close_brace].strip()
        else:
            declarations_text = stripped
    parts: list[str] = []
    if declarations_text:
        raw_parts = [
            segment.strip()
            for segment in declarations_text.split(";")
            if segment.strip()
        ]
        parts.extend(
            segment
            for segment in raw_parts
            if not segment.lower().startswith(("margin", "padding"))
        )
    parts.extend(["margin: 0", "padding: 0"])
    declarations = "; ".join(parts) + ";"
    zone.set_zone_stylesheet(compose_stylesheet(zone, declarations))
