from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def make_readonly_lineedit(le: QLineEdit, bold: bool = False) -> None:
    le.setReadOnly(True)
    le.setFrame(False)
    le.setStyleSheet("border:none; background:transparent;")
    f = le.font()
    f.setBold(bold)
    le.setFont(f)


def match_font(lbl: QLabel, ref: QLineEdit) -> None:
    f = ref.font()
    lbl.setFont(f)


def stack_combo(title: str):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(2)
    lbl = QLabel(title)
    v.addWidget(lbl, 0, Qt.AlignLeft | Qt.AlignVCenter)
    cb = QComboBox()
    cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    v.addWidget(cb, 0)
    return w, cb
