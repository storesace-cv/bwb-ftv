from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QDialogButtonBox


class SplashScreen(QDialog):
    """Simple splash screen with optional message and buttons."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        self.setFixedSize(800, 500)

        pixmap = QPixmap(str(Path(__file__).with_name("bwb-Splash.png")))
        self._background = QLabel(self)
        self._background.setPixmap(pixmap)
        self._background.setGeometry(0, 0, 800, 500)

        self._message: QLabel | None = None
        self._box: QDialogButtonBox | None = None

    def mousePressEvent(self, event):  # type: ignore[override]
        self.close()
        self.clicked.emit()
        super().mousePressEvent(event)

    def show_message(self, text: str) -> None:
        """Overlay ``text`` on the splash image."""
        if self._message is None:
            self._message = QLabel(self)
            self._message.setAlignment(Qt.AlignCenter)
            self._message.setStyleSheet("color: white; background: transparent;")
            self._message.setGeometry(0, 260, 800, 40)
        self._message.setText(text)
        self._message.show()

    def add_button_box(
        self, buttons: QDialogButtonBox.StandardButtons = QDialogButtonBox.Ok
    ) -> QDialogButtonBox:
        """Add a :class:`QDialogButtonBox` at y=300."""
        if self._box is None:
            self._box = QDialogButtonBox(buttons, parent=self)
            self._box.setGeometry(0, 300, 800, self._box.sizeHint().height())
        return self._box
