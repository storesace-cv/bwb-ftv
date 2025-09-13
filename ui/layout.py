import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

DEV_OVERLAYS = True


_TAG_RE = re.compile(r"^C\d+(?:\.(?:A|B|\d+))*$")


def validate_tag(tag: str) -> bool:
    """Return ``True`` if ``tag`` complies with the expected pattern."""

    return bool(_TAG_RE.fullmatch(tag))


def bg_for_level(level: int) -> str:
    colors = ["#eafbf1", "#eef5ff", "#fff5e8", "#f7f0ff", "#fff0f0"]
    return colors[level % len(colors)] if DEV_OVERLAYS else "transparent"


class Zone(QWidget):
    """Célula real (com tag e overlay opcional)."""

    def __init__(
        self,
        tag: str,
        parent=None,
        flow="v",
        margins=8,
        spacing=6,
        level: int = 0,
        show_overlays: bool = True,
    ):
        if not validate_tag(tag):
            raise ValueError(f"Invalid zone tag: {tag}")
        super().__init__(parent)
        self.tag = tag
        self.setObjectName(tag)
        self._level = level
        self._labels: list[QLabel] = []
        if flow == "v":
            self.ly = QVBoxLayout(self)
        else:
            self.ly = QHBoxLayout(self)
        self.ly.setContentsMargins(margins, margins, margins, margins)
        self.ly.setSpacing(spacing)

        self._tag_lbl = QLabel(self.tag, self)
        self._tag_lbl.setStyleSheet("color:#c00; font-size:10px;")
        self._tag_lbl.setFixedHeight(12)
        self.ly.addWidget(self._tag_lbl, 0, Qt.AlignLeft)

        self.apply_overlays(show_overlays)

    def apply_overlays(self, on: bool) -> None:
        if on:
            self.setStyleSheet(
                f"background:{bg_for_level(self._level)}; border:1px dashed red;"
            )
            self._tag_lbl.show()
        else:
            self.setStyleSheet("")
            self._tag_lbl.hide()
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
    ) -> QLabel:
        row = QWidget(self)
        row.setStyleSheet("border:none; background:transparent;")
        grid = QGridLayout(row)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(vspacing)
        grid.setColumnStretch(1, 1)
        lbl = QLabel(label_text, row)
        lbl.setStyleSheet("border:none; background:transparent;")
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        if label_minw is not None:
            lbl.setFixedWidth(label_minw)
        value_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        try:
            value_widget.setStyleSheet(
                value_widget.styleSheet() + "border:none; background:transparent;"
            )
        except Exception:
            pass
        grid.addWidget(lbl, 0, 0, alignment=Qt.AlignVCenter | Qt.AlignRight)
        grid.addWidget(value_widget, 0, 1, alignment=Qt.AlignVCenter | Qt.AlignLeft)
        self.ly.addWidget(row)
        self._labels.append(lbl)
        self.sync_label_widths()
        return lbl

    def sync_label_widths(self) -> None:
        if not self._labels:
            return
        maxw = max(label.sizeHint().width() for label in self._labels)
        for label in self._labels:
            label.setFixedWidth(maxw)

    def split_h(self, ratios=(1, 1)):
        cont = QWidget(self)
        cont.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        h = QHBoxLayout(cont)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(self.ly.spacing())
        left_tag = self.tag + ".A"
        right_tag = self.tag + ".B"
        for t in (left_tag, right_tag):
            if not validate_tag(t):
                raise ValueError(f"Invalid zone tag: {t}")
        left = Zone(
            left_tag,
            cont,
            flow="v",
            margins=4,
            spacing=self.ly.spacing(),
            level=self._level + 1,
            show_overlays=DEV_OVERLAYS,
        )
        right = Zone(
            right_tag,
            cont,
            flow="v",
            margins=4,
            spacing=self.ly.spacing(),
            level=self._level + 1,
            show_overlays=DEV_OVERLAYS,
        )
        h.addWidget(left, ratios[0])
        h.addWidget(right, ratios[1])
        self.ly.addWidget(cont, 1)
        return left, right

    def split_v(self, ratios=(1, 1)):
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
            zone = Zone(
                tag,
                cont,
                flow="v",
                margins=4,
                spacing=self.ly.spacing(),
                level=self._level + 1,
                show_overlays=DEV_OVERLAYS,
            )
            v.addWidget(zone, ratio)
            zones.append(zone)
        self.ly.addWidget(cont, 1)
        return tuple(zones)
