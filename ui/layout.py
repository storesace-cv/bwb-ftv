"""Componentes de layout para a ficha técnica.

Aviso: legendas usadas pelos overlays de desenvolvimento têm estilos inline
específicos; não utilize ``apply_label_style`` nem folhas de estilo globais
nesses rótulos.
"""

import os
import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .bwb_style_1 import ZONE_STYLES
from .utilities import (
    apply_label_style,
    apply_overlay_label_style,
    install_tooltip_copy_handler,
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

# Updated to allow block-prefixed cell identifiers like ``B1.C1``
_TAG_RE = re.compile(r"^B\d+(?:\.C\d+(?:\.(?:A|B|\d+))*)?$")


def _escape_object_name(name: str) -> str:
    """Return ``name`` escaped for usage within Qt style sheets."""

    return re.sub(r"([^\w-])", r"\\\1", name)


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


class Zone(QWidget):
    """Célula real (com tag e overlay opcional)."""

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
        theme_name: str | None = None,
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
        self._labels: list[QLabel] = []
        self._overlay_active = False
        self._theme_name: str | None = None
        self._widget_type: str | None = widget_type or None
        self._zone_type: str | None = zone_type or None
        self._widget_qt_class: str | None = widget_qt_class or None
        self._style_dev_info: str | None = None
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
        self._base_stylesheet = (
            f"{selector} {{ background: transparent; border: none; }}"
            if selector
            else "background: transparent; border: none;"
        )

        self.apply_overlays(show_overlays)

        if theme_name is not None:
            self.set_theme(theme_name)

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
        self._sync_style_label()

    @property
    def zone_type(self) -> str | None:
        return self._zone_type

    def set_zone_type(self, zone_type: str | None) -> None:
        self._zone_type = zone_type or None
        self._sync_style_label()

    def set_style_dev_info(self, info: str | None) -> None:
        self._style_dev_info = info or None
        self._sync_style_label()

    @property
    def widget_qt_class(self) -> str | None:
        return self._widget_qt_class

    def set_widget_qt_class(self, widget_qt_class: str | None) -> None:
        self._widget_qt_class = widget_qt_class or None
        self._sync_style_label()

    @property
    def base_stylesheet(self) -> str:
        return self._base_stylesheet

    def set_theme(self, name: str) -> None:
        try:
            declarations = ZONE_STYLES[name]
        except KeyError as exc:
            raise ValueError(f"Unknown zone theme: {name}") from exc

        selector = f"#{_escape_object_name(self.objectName())}" if self.objectName() else ""
        stylesheet = f"{selector} {{ {declarations} }}" if selector else declarations
        self._theme_name = name
        self._base_stylesheet = stylesheet
        if not self._overlay_active:
            self.setStyleSheet(self._base_stylesheet)
            refresh_style(self)
        self._sync_style_label()

    def _style_label_text(self) -> str | None:
        segments = [
            self._zone_type,
            self._widget_qt_class,
            self._widget_type,
            self._theme_name,
        ]
        filtered = [segment for segment in segments if segment]
        return " | ".join(filtered) if filtered else None

    def _sync_style_label(self) -> None:
        if self._overlay_active:
            text = self._style_label_text()
            tooltip = self._build_label_tooltip(text, self._style_dev_info)
            if text:
                self._style_lbl.setText(text)
                self._style_lbl.show()
            else:
                self._style_lbl.clear()
                self._style_lbl.hide()
            if text or self._style_dev_info:
                self._style_lbl.setToolTip(tooltip)
            else:
                self._style_lbl.setToolTip("")
        else:
            self._style_lbl.clear()
            self._style_lbl.hide()
            self._style_lbl.setToolTip("")
        refresh_style(self._style_lbl)

    def apply_overlays(self, on: bool) -> None:
        active = bool(on) and DEV_OVERLAYS
        self._overlay_active = active
        self.setProperty("overlays", "on" if active else "off")
        name = self.objectName()
        selector = f"#{_escape_object_name(name)}" if name else ""
        header_present = self.ly.indexOf(self._tag_container) != -1
        if active:
            style = (
                f"{selector} {{ background:{bg_for_level(self._level)}; border:2px dashed blue; }}"
                if selector
                else f"background:{bg_for_level(self._level)}; border:2px dashed blue;"
            )
            self.setStyleSheet(style)
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
            self.setStyleSheet(self._base_stylesheet)
            if header_present:
                self.ly.removeWidget(self._tag_container)
            self._tag_container.hide()
            self._tag_lbl.hide()
            self._style_lbl.setToolTip("")
        self._sync_style_label()
        for lbl in self._labels:
            user_label = lbl.property("userLabel")
            dev_label = lbl.property("devLabel")
            lbl.setText(dev_label if active and dev_label else user_label)
            lbl.setToolTip(
                self._build_label_tooltip(user_label, dev_label) if active else ""
            )
            font = QFont(lbl.font())
            alignment = lbl.alignment()
            if active:
                apply_overlay_label_style(lbl)
            else:
                extra = lbl.property("labelExtraStyle")
                apply_label_style(lbl, extra if extra else None)
            lbl.setFont(font)
            lbl.setAlignment(alignment)
            refresh_style(lbl)
        self.sync_label_widths()
        refresh_style(self._tag_lbl)
        refresh_style(self)
        for ch in self.findChildren(Zone):
            ch.apply_overlays(on)

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
        else:
            apply_label_style(lbl, debug_extra)
        lbl.setProperty("userLabel", label_text)
        lbl.setProperty("devLabel", overlay_text)
        lbl.setAlignment(Qt.AlignTop | Qt.AlignRight)
        if label_minw is not None:
            lbl.setFixedWidth(label_minw)
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
        grid.addWidget(lbl, 0, 0, alignment=Qt.AlignTop | Qt.AlignRight)
        grid.addWidget(value_widget, 0, 1, alignment=Qt.AlignTop | Qt.AlignLeft)
        self.ly.addWidget(row, 0, Qt.AlignTop)
        self._labels.append(lbl)
        install_tooltip_copy_handler(lbl)
        if self._overlay_active and overlay_text is not None:
            lbl.setToolTip(self._build_label_tooltip(label_text, overlay_text))
        else:
            lbl.setToolTip("")
        self.sync_label_widths()
        return lbl

    def sync_label_widths(self) -> None:
        if not self._labels:
            return
        for label in self._labels:
            # Release any fixed width constraint so the label's size hint reflects
            # the currently visible text before we compute the shared width.
            label.setMinimumWidth(0)
            label.setMaximumWidth(_QT_MAX_WIDGET_WIDTH)
            label.updateGeometry()
        maxw = max(label.sizeHint().width() for label in self._labels)
        for label in self._labels:
            label.setFixedWidth(maxw)

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
                theme_name=self._theme_name,
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
                theme_name=self._theme_name,
                widget_type=child_widget_type,
                zone_type=child_zone_type,
                widget_qt_class=child_widget_qt_class,
            )
            v.addWidget(zone, ratio)
            zones.append(zone)
        self.ly.addWidget(cont, 1)
        return tuple(zones)
