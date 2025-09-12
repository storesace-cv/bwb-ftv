from typing import List

from PyQt5.QtWidgets import QMessageBox


class StartupDialog(QMessageBox):
    """Simple dialog to display startup messages with configurable buttons."""

    def __init__(self, text: str, buttons: List[str], parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setIcon(QMessageBox.Information)
        self._buttons = []
        for idx, label in enumerate(buttons):
            btn = self.addButton(label, QMessageBox.AcceptRole)
            self._buttons.append(btn)
            if idx == 0:
                self.setDefaultButton(btn)

    def get_choice(self) -> str | None:
        self.exec_()
        clicked = self.clickedButton()
        return clicked.text() if clicked else None
