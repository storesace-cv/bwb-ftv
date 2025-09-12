from typing import List

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class StartupDialog(QDialog):
    """Simple dialog to display startup messages with configurable buttons."""

    def __init__(self, text: str, buttons: List[str], parent=None):
        super().__init__(parent)
        self._choice = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(text))
        self._box = QDialogButtonBox()
        for idx, label in enumerate(buttons):
            btn = self._box.addButton(label, QDialogButtonBox.AcceptRole)
            if idx == 0:
                btn.setDefault(True)
        self._box.clicked.connect(self._on_clicked)
        layout.addWidget(self._box)

    def _on_clicked(self, button):
        self._choice = button.text()
        self.accept()

    def get_choice(self) -> str | None:
        self.exec_()
        return self._choice
