from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


FIELD_STYLE = (
    "border:none;"
    "border-radius:4px;"
    "background-color: rgba(0, 0, 0, 0.1);"
)


LABEL_STYLE = (
    "QLabel {\n"
    "    background-color: rgba(200,200,200,0.5);\n"
    "    border: 1px solid rgba(0,0,0,0.3);\n"
    "    border-top-color: rgba(255,255,255,0.8);\n"
    "    border-left-color: rgba(255,255,255,0.8);\n"
    "    border-bottom-color: rgba(0,0,0,0.4);\n"
    "    border-right-color: rgba(0,0,0,0.4);\n"
    "    border-radius: 6px;\n"
    "    padding: 4px;\n"
    "}\n"
    "QLabel:pressed {\n"
    "    background-color: rgba(200,200,200,0.8);\n"
    "}"
)


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
