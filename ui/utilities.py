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

from .bwb_style_1 import (
    CENTER_FIELD_STYLE,
    CENTER_LABEL_STYLE,
    FIELD_STYLE,
    LABEL_STYLE,
    OVERLAY_ON_CLASS,
    FCFILTER_BUTTON_STYLE_TEMPLATE,
)


class AlignmentVariant(str, Enum):
    """Supported alignment variants for styled labels and fields."""

    DEFAULT = "default"
    CENTER = "center"


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
    """Apply the beveled label style to ``label``.

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
    base_style = CENTER_LABEL_STYLE if variant is AlignmentVariant.CENTER else LABEL_STYLE
    style = base_style if not extra else f"{base_style}\n{extra}"
    label.setStyleSheet(style)
    if variant is AlignmentVariant.CENTER:
        label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
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
    bold: bool = False,
    *,
    alignment: AlignmentVariant | str | None = None,
) -> None:
    le.setReadOnly(True)
    le.setFrame(False)
    variant = _normalize_alignment(
        alignment if alignment is not None else le.property(_LINEEDIT_ALIGNMENT_PROPERTY)
    )
    le.setProperty(_LINEEDIT_ALIGNMENT_PROPERTY, variant.value)
    if variant is AlignmentVariant.CENTER:
        le.setStyleSheet(CENTER_FIELD_STYLE)
        le.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
    else:
        le.setStyleSheet(FIELD_STYLE)
    f = le.font()
    f.setBold(bold)
    le.setFont(f)
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
    if widget.property(_TOOLTIP_COPY_HANDLER_FLAG):
        return

    def _copy_from_global(global_pos: QPoint | None) -> None:
        text = widget.toolTip()
        if not text:
            return
        QApplication.clipboard().setText(text)
        if feedback and global_pos is not None:
            QToolTip.showText(global_pos, feedback, widget)

    def _copy_tooltip(pos: QPoint) -> None:
        _copy_from_global(widget.mapToGlobal(pos))

    class _TooltipCopyFilter(QObject):
        def __init__(self, parent: QObject | None = None) -> None:
            super().__init__(parent)

        def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # pragma: no cover - Qt glue
            if obj is widget and event.type() == QEvent.MouseButtonPress:
                if getattr(event, "button", None) and event.button() == Qt.RightButton:
                    global_pos = getattr(event, "globalPos", None)
                    if callable(global_pos):
                        global_pos = global_pos()
                    _copy_from_global(global_pos)
            return False

    widget.setContextMenuPolicy(Qt.CustomContextMenu)
    widget.customContextMenuRequested.connect(_copy_tooltip)
    widget.setProperty(_TOOLTIP_COPY_HANDLER_FLAG, True)
    if widget.property(_TOOLTIP_COPY_FILTER_OBJECT) is None:
        filter_obj = _TooltipCopyFilter(widget)
        widget.installEventFilter(filter_obj)
        widget.setProperty(_TOOLTIP_COPY_FILTER_OBJECT, filter_obj)

