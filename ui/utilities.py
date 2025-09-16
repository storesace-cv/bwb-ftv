from typing import Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .bwb_style_1 import FIELD_STYLE, LABEL_STYLE, FCFILTER_BUTTON_STYLE_TEMPLATE


def apply_label_style(label: QLabel, extra: str | None = None) -> None:
    """Apply the default beveled label style to ``label``.

    ``extra`` may contain additional stylesheet rules appended to the base style.
    """

    style = LABEL_STYLE if not extra else f"{LABEL_STYLE}\n{extra}"
    label.setStyleSheet(style)


def make_readonly_lineedit(le: QLineEdit, bold: bool = False) -> None:
    le.setReadOnly(True)
    le.setFrame(False)
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
