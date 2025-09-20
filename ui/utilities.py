from enum import Enum
from typing import Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# --- Shared UI style constants -------------------------------------------------

# Labels use a light, neutral palette that matches the mock-ups from the
# functional specification.  The centre variants keep the same palette but allow
# per-widget alignment overrides (the helpers later force the desired Qt
# alignment, so the selector keeps the text-decoration consistent).
LABEL_STYLE = (
    "QLabel {\n"
    "    color: #1d1f23;\n"
    "    font-size: 13px;\n"
    "    font-weight: bold;\n"
    "    background-color: rgba(200, 200, 200, 0.5);\n"
    "    border: 1px solid rgba(0, 0, 0, 0.3);\n"
    "    border-top-color: rgba(255, 255, 255, 0.8);\n"
    "    border-left-color: rgba(255, 255, 255, 0.8);\n"
    "    border-bottom-color: rgba(0, 0, 0, 0.4);\n"
    "    border-right-color: rgba(0, 0, 0, 0.4);\n"
    "    border-radius: 6px;\n"
    "    padding: 4px;\n"
    "}"
)

CENTER_LABEL_STYLE = (
    "QLabel {\n"
    "    color: #1d1f23;\n"
    "    font-size: 13px;\n"
    "    font-weight: bold;\n"
    "    background-color: rgba(200, 200, 200, 0.5);\n"
    "    border: 1px solid rgba(0, 0, 0, 0.3);\n"
    "    border-top-color: rgba(255, 255, 255, 0.8);\n"
    "    border-left-color: rgba(255, 255, 255, 0.8);\n"
    "    border-bottom-color: rgba(0, 0, 0, 0.4);\n"
    "    border-right-color: rgba(0, 0, 0, 0.4);\n"
    "    border-radius: 6px;\n"
    "    padding: 4px;\n"
    "    text-align: center;\n"
    "}"
)

# Read-only fields keep the muted glassmorphism look: translucent background,
# subtle border and rounded corners.  The centred variant only differs by the
# alignment declaration so that it can be reused wherever visual centring is
# preferred.
FIELD_STYLE = (
    "QLineEdit {\n"
    "    background: transparent;\n"
    "    padding: 4px 6px;\n"
    "    selection-background-color: rgba(0, 110, 255, 0.45);\n"
    "}"
)

CENTER_FIELD_STYLE = (
    "QLineEdit {\n"
    "    background: transparent;\n"
    "    padding: 4px 6px;\n"
    "    selection-background-color: rgba(0, 110, 255, 0.45);\n"
    "    qproperty-alignment: 'AlignHCenter | AlignVCenter';\n"
    "}"
)

# Overlay mode tags rely on a class property so they can be styled globally via
# a single selector.
OVERLAY_ON_CLASS = "overlay-active"

# Base template used by the Food Cost filter buttons.  RGB components are filled
# dynamically, maintaining the same hover/checked contrast the designers
# specified while keeping the neutral typography.
FCFILTER_BUTTON_STYLE_TEMPLATE = (
    "QPushButton {{\n"
    "    background-color: rgba({r}, {g}, {b}, {normal_alpha});\n"
    "    border: 1px solid rgba({r}, {g}, {b}, 0.4);\n"
    "    border-radius: 12px;\n"
    "    padding: 6px 12px;\n"
    "    font-weight: 600;\n"
    "    color: #1d1f23;\n"
    "}}\n"
    "QPushButton:hover {{\n"
    "    background-color: rgba({r}, {g}, {b}, {active_alpha});\n"
    "}}\n"
    "QPushButton:checked {{\n"
    "    background-color: rgba({r}, {g}, {b}, {active_alpha});\n"
    "    border-color: rgba({r}, {g}, {b}, 0.6);\n"
    "}}"
)


class AlignmentVariant(str, Enum):
    """Supported alignment variants for styled labels and fields."""

    DEFAULT = "default"
    CENTER = "center"
    RIGHT = "right"


def _normalize_alignment(value: AlignmentVariant | str | None) -> AlignmentVariant:
    if value is None:
        return AlignmentVariant.DEFAULT
    if isinstance(value, AlignmentVariant):
        return value
    try:
        return AlignmentVariant(str(value))
    except ValueError as exc:  # pragma: no cover - defensive path
        raise ValueError(f"Unsupported alignment variant: {value!r}") from exc


_LABEL_ALIGNMENT_PROPERTY = "labelAlignmentVariant"
_LINEEDIT_ALIGNMENT_PROPERTY = "lineEditAlignmentVariant"
DEFAULT_TOOLTIP_DURATION_MS = 0


def _get_widget_classes(widget: QWidget) -> list[str]:
    value = widget.property("class")
    if value is None:
        return []
    if isinstance(value, str):
        return [cls for cls in value.split() if cls]
    if isinstance(value, (list, tuple)):
        return [str(cls) for cls in value if str(cls)]
    return [str(value)]


def _set_widget_classes(widget: QWidget, classes: list[str]) -> None:
    seen: list[str] = []
    for cls in classes:
        text = str(cls).strip()
        if text and text not in seen:
            seen.append(text)
    if seen:
        widget.setProperty("class", " ".join(seen))
    else:
        widget.setProperty("class", None)


def _refresh_widget_style(widget: QWidget) -> None:
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def apply_label_style(
    label: QLabel,
    extra: str | None = None,
    *,
    alignment: AlignmentVariant | str | None = None,
) -> str:
    """Apply the neutral label style to ``label``.

    ``extra`` may contain additional stylesheet rules appended to the base style.
    ``alignment`` selects between the default (centred) and right-aligned variants.
    The computed style sheet is returned so callers can persist or inspect it.
    """

    variant = _normalize_alignment(
        alignment if alignment is not None else label.property(_LABEL_ALIGNMENT_PROPERTY)
    )
    label.setProperty(_LABEL_ALIGNMENT_PROPERTY, variant.value)
    classes = _get_widget_classes(label)
    if OVERLAY_ON_CLASS in classes:
        classes = [cls for cls in classes if cls != OVERLAY_ON_CLASS]
        _set_widget_classes(label, classes)
    if variant is AlignmentVariant.RIGHT:
        base_style = LABEL_STYLE
        alignment_flag = Qt.AlignRight | Qt.AlignVCenter
    else:
        base_style = (
            CENTER_LABEL_STYLE
            if variant is AlignmentVariant.CENTER
            else LABEL_STYLE
        )
        alignment_flag = Qt.AlignHCenter | Qt.AlignVCenter
    label.setAlignment(alignment_flag)
    style = base_style if not extra else f"{base_style}\n{extra}"
    label.setStyleSheet(style)
    _refresh_widget_style(label)
    return style


def apply_overlay_label_style(label: QLabel) -> None:
    """Apply the transparent overlay style to ``label``.

    The existing font metrics and alignment flags are preserved.
    """

    font = QFont(label.font())
    alignment = label.alignment()
    label.setStyleSheet("")
    classes = _get_widget_classes(label)
    if OVERLAY_ON_CLASS not in classes:
        classes.append(OVERLAY_ON_CLASS)
    _set_widget_classes(label, classes)
    _refresh_widget_style(label)
    label.setFont(font)
    label.setAlignment(alignment)


def make_readonly_lineedit(
    le: QLineEdit,
    *,
    alignment: AlignmentVariant | str | None = None,
) -> None:
    """Configure ``le`` as a neutral read-only field with normal font weight."""

    le.setReadOnly(True)
    le.setFrame(False)
    variant = _normalize_alignment(
        alignment if alignment is not None else le.property(_LINEEDIT_ALIGNMENT_PROPERTY)
    )
    le.setProperty(_LINEEDIT_ALIGNMENT_PROPERTY, variant.value)
    if variant is AlignmentVariant.CENTER:
        le.setStyleSheet(CENTER_FIELD_STYLE)
        alignment_flag = Qt.AlignLeft | Qt.AlignVCenter
    else:
        le.setStyleSheet(FIELD_STYLE)
        alignment_flag = (
            Qt.AlignRight | Qt.AlignVCenter
            if variant is AlignmentVariant.RIGHT
            else Qt.AlignLeft | Qt.AlignVCenter
        )
    le.setAlignment(alignment_flag)
    font = QFont(le.font())
    if font.bold() or font.weight() != QFont.Normal:
        font.setBold(False)
        font.setWeight(QFont.Normal)
    le.setFont(font)
    le.setFixedHeight(le.sizeHint().height())


def match_font(lbl: QLabel, ref: QLineEdit) -> None:
    f = ref.font()
    lbl.setFont(f)


def stack_combo(title: str):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(2)
    lbl = QLabel(title)
    apply_label_style(lbl)
    lbl.setProperty("userLabel", lbl.text())
    lbl.setProperty("devLabel", None)
    v.addWidget(lbl, 0, Qt.AlignHCenter | Qt.AlignVCenter)
    cb = QComboBox()
    cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    cb.setStyleSheet(FIELD_STYLE)
    v.addWidget(cb, 0)
    return w, cb, lbl


def apply_fcfilter_btn_style(
    button: QPushButton,
    rgb: Sequence[int],
    *,
    normal_alpha: float = 0.5,
    active_alpha: float = 0.8,
) -> None:
    """Apply the ``bwb-style-fcfilters-btn`` template using ``rgb``."""

    if len(rgb) != 3:
        raise ValueError("apply_fcfilter_btn_style expects exactly three RGB values")

    def _clamp_component(value: int) -> int:
        return max(0, min(255, int(value)))

    r, g, b = (_clamp_component(component) for component in rgb)

    def _format_alpha(value: float) -> str:
        bounded = max(0.0, min(1.0, float(value)))
        text = f"{bounded:.3f}".rstrip("0").rstrip(".")
        return text or "0"

    stylesheet = FCFILTER_BUTTON_STYLE_TEMPLATE.format(
        r=r,
        g=g,
        b=b,
        normal_alpha=_format_alpha(normal_alpha),
        active_alpha=_format_alpha(active_alpha),
    )
    button.setStyleSheet(stylesheet)


def _layout_overlays_enabled() -> bool:
    try:  # pragma: no cover - defensive import path
        from . import layout  # type: ignore circular import
    except Exception:  # pragma: no cover - defensive path
        return False
    return bool(getattr(layout, "DEV_OVERLAYS", False))


def _overlay_context(widget: QWidget | None) -> bool:
    current = widget
    while isinstance(current, QWidget):
        value = current.property("overlays")
        if value is not None:
            if isinstance(value, str):
                return value.strip().lower() == "on"
            return bool(value)
        parent = current.parentWidget
        if callable(parent):
            current = parent()
        else:  # pragma: no cover - unexpected Qt object
            break
    return _layout_overlays_enabled()



