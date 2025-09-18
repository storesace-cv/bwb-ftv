from enum import Enum
from typing import Sequence

from PyQt5.QtCore import Qt, QPoint, QObject, QEvent
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QToolTip,
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
    "    font-weight: 500;\n"
    "    background: transparent;\n"
    "    border: none;\n"
    "    padding: 0;\n"
    "}"
)

CENTER_LABEL_STYLE = (
    "QLabel {\n"
    "    color: #1d1f23;\n"
    "    font-size: 13px;\n"
    "    font-weight: 500;\n"
    "    background: transparent;\n"
    "    border: none;\n"
    "    padding: 0;\n"
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
DEFAULT_TOOLTIP_DURATION_MS = 3000


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
) -> None:
    """Apply the neutral label style to ``label``.

    ``extra`` may contain additional stylesheet rules appended to the base style.
    ``alignment`` selects between the default (left-aligned) and centred variants.
    """

    variant = _normalize_alignment(
        alignment if alignment is not None else label.property(_LABEL_ALIGNMENT_PROPERTY)
    )
    label.setProperty(_LABEL_ALIGNMENT_PROPERTY, variant.value)
    classes = _get_widget_classes(label)
    if OVERLAY_ON_CLASS in classes:
        classes = [cls for cls in classes if cls != OVERLAY_ON_CLASS]
        _set_widget_classes(label, classes)
    if variant is AlignmentVariant.CENTER:
        base_style = CENTER_LABEL_STYLE
        alignment_flag = Qt.AlignLeft | Qt.AlignVCenter
    elif variant is AlignmentVariant.RIGHT:
        base_style = LABEL_STYLE
        alignment_flag = Qt.AlignRight | Qt.AlignVCenter
    else:
        base_style = LABEL_STYLE
        alignment_flag = Qt.AlignLeft | Qt.AlignVCenter
    label.setAlignment(alignment_flag)
    style = base_style if not extra else f"{base_style}\n{extra}"
    label.setStyleSheet(style)
    _refresh_widget_style(label)


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
    lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    lbl.setStyleSheet("")
    v.addWidget(lbl, 0, Qt.AlignLeft | Qt.AlignVCenter)
    cb = QComboBox()
    cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    cb.setStyleSheet(FIELD_STYLE)
    v.addWidget(cb, 0)
    return w, cb


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


_TOOLTIP_COPY_HANDLER_FLAG = "tooltipCopyHandlerInstalled"
_TOOLTIP_COPY_FILTER_OBJECT = "_tooltipCopyEventFilter"
_TOOLTIP_COPY_FEEDBACK_PROPERTY = "_tooltipCopyFeedbackText"
_GLOBAL_TOOLTIP_FILTER: QObject | None = None


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


def _event_global_position(event: QEvent, widget: QWidget | None) -> QPoint | None:
    global_pos = getattr(event, "globalPos", None)
    if callable(global_pos):
        global_pos = global_pos()
    if global_pos is not None:
        return global_pos
    if widget is not None:
        local_pos = getattr(event, "pos", None)
        if callable(local_pos):
            local_pos = local_pos()
        if isinstance(local_pos, QPoint):
            return widget.mapToGlobal(local_pos)
    return None


def _copy_visible_tooltip(
    feedback: str | None,
    global_pos: QPoint | None,
    widget: QWidget | None,
) -> bool:
    if not QToolTip.isVisible():
        return False
    if not _overlay_context(widget):
        return False
    text = QToolTip.text()
    if not text:
        return False
    QApplication.clipboard().setText(text)
    if feedback and global_pos is not None:
        display = f"{text}\n\n{feedback}" if text else feedback
        anchor = widget if isinstance(widget, QWidget) else None
        QToolTip.showText(global_pos, display, anchor)
    return True


def _copy_widget_tooltip(
    widget: QWidget,
    feedback: str | None,
    global_pos: QPoint | None,
) -> None:
    text = widget.toolTip()
    if not text:
        return
    QApplication.clipboard().setText(text)
    if feedback and global_pos is not None:
        QToolTip.showText(global_pos, feedback, widget)


class _TooltipCopyGlobalFilter(QObject):
    def __init__(
        self,
        default_feedback: str | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.default_feedback = default_feedback

    def _feedback_for(self, widget: QWidget | None) -> str | None:
        current = widget
        while isinstance(current, QWidget):
            value = current.property(_TOOLTIP_COPY_FEEDBACK_PROPERTY)
            if isinstance(value, tuple) and len(value) == 2 and value[0] is True:
                return value[1]
            if isinstance(value, str):
                return value or None
            if value:
                return str(value)
            parent = current.parentWidget
            if callable(parent):
                current = parent()
            else:  # pragma: no cover - unexpected Qt object
                break
        return self.default_feedback

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # pragma: no cover - Qt glue
        if event.type() == QEvent.MouseButtonPress:
            button_getter = getattr(event, "button", None)
            button = button_getter() if callable(button_getter) else button_getter
            if button == Qt.RightButton:
                widget = obj if isinstance(obj, QWidget) else None
                global_pos = _event_global_position(event, widget)
                feedback = self._feedback_for(widget)
                _copy_visible_tooltip(feedback, global_pos, widget)
        return False


def _ensure_global_tooltip_filter(feedback: str | None) -> None:
    global _GLOBAL_TOOLTIP_FILTER
    app = QApplication.instance()
    if app is None:
        return
    if isinstance(_GLOBAL_TOOLTIP_FILTER, _TooltipCopyGlobalFilter):
        if feedback and not _GLOBAL_TOOLTIP_FILTER.default_feedback:
            _GLOBAL_TOOLTIP_FILTER.default_feedback = feedback
        return
    global_filter = _TooltipCopyGlobalFilter(feedback, parent=app)
    app.installEventFilter(global_filter)
    _GLOBAL_TOOLTIP_FILTER = global_filter


def install_tooltip_copy_handler(
    widget: QWidget,
    *,
    feedback: str | None = "Copiado para a área de transferência",
) -> None:
    """Allow ``widget`` to copy its tooltip text on right-click.

    The handler is idempotent and can be invoked multiple times on the same widget.
    When the tooltip is empty no clipboard update occurs.
    """

    if widget is None:
        return
    if hasattr(widget, "setToolTipDuration"):
        widget.setToolTipDuration(DEFAULT_TOOLTIP_DURATION_MS)

    if widget.property(_TOOLTIP_COPY_HANDLER_FLAG):
        widget.setProperty(_TOOLTIP_COPY_FEEDBACK_PROPERTY, (True, feedback))
        _ensure_global_tooltip_filter(feedback)
        return

    widget.setProperty(_TOOLTIP_COPY_FEEDBACK_PROPERTY, (True, feedback))
    _ensure_global_tooltip_filter(feedback)

    def _copy_tooltip(pos: QPoint) -> None:
        if QToolTip.isVisible() and _overlay_context(widget):
            return
        _copy_widget_tooltip(widget, feedback, widget.mapToGlobal(pos))

    class _TooltipCopyFilter(QObject):
        def __init__(self, parent: QObject | None = None) -> None:
            super().__init__(parent)

        def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # pragma: no cover - Qt glue
            if obj is widget and event.type() == QEvent.MouseButtonPress:
                if getattr(event, "button", None) and event.button() == Qt.RightButton:
                    if QToolTip.isVisible() and _overlay_context(widget):
                        return False
                    global_pos = _event_global_position(event, widget)
                    _copy_widget_tooltip(widget, feedback, global_pos)
            return False

    widget.setContextMenuPolicy(Qt.CustomContextMenu)
    widget.customContextMenuRequested.connect(_copy_tooltip)
    widget.setProperty(_TOOLTIP_COPY_HANDLER_FLAG, True)
    if widget.property(_TOOLTIP_COPY_FILTER_OBJECT) is None:
        filter_obj = _TooltipCopyFilter(widget)
        widget.installEventFilter(filter_obj)
        widget.setProperty(_TOOLTIP_COPY_FILTER_OBJECT, filter_obj)

