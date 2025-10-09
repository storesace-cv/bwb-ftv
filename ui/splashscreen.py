from pathlib import Path

import logging
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QDialogButtonBox, QPushButton

from .qt_compat import exec_modal
from .utilities import apply_label_style


logger = logging.getLogger(__name__)


class SplashScreen(QDialog):
    """Simple splash screen with optional message and buttons."""

    _DEFAULT_SIZE = QSize(800, 500)
    _MESSAGE_Y = 260
    _MESSAGE_HEIGHT = 40
    _BUTTON_DEFAULT_Y = 300

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setAutoFillBackground(False)

        pixmap = QPixmap(str(Path(__file__).with_name("bwb-Splash.png")))
        if pixmap.isNull():
            logger.warning(
                "[SplashScreen] Falha ao carregar imagem transparente; a usar dimensão padrão %sx%s.",
                self._DEFAULT_SIZE.width(),
                self._DEFAULT_SIZE.height(),
            )
            self._design_size = QSize(self._DEFAULT_SIZE.width(), self._DEFAULT_SIZE.height())
        else:
            self._design_size = pixmap.size()
        self.setFixedSize(self._design_size)

        self._background = QLabel(self)
        self._background.setAttribute(Qt.WA_TranslucentBackground)
        self._background.setStyleSheet("background: transparent;")
        self._background.setGeometry(self.rect())
        self._background.setPixmap(pixmap)
        self._background.setStyleSheet("background: transparent;")

        self._message: QLabel | None = None
        self._box: QDialogButtonBox | None = None
        self._box_design_y: int | None = None

    def mousePressEvent(self, event):  # type: ignore[override]
        self.close()
        self.clicked.emit()
        super().mousePressEvent(event)

    def show_message(self, text: str) -> None:
        """Overlay ``text`` on the splash image."""
        if self._message is None:
            self._message = QLabel(self)
            apply_label_style(
                self._message,
                "QLabel { color: white; }",
            )
            self._message.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._message.setText(text)
        self._position_message()
        self._message.show()
        self._message.raise_()
        self.show()

    def add_button_box(
        self, buttons: QDialogButtonBox.StandardButtons = QDialogButtonBox.Ok
    ) -> QDialogButtonBox:
        """Add a :class:`QDialogButtonBox` at y=300."""
        if self._box is None:
            self._box = QDialogButtonBox(buttons, parent=self)
            self._box_design_y = self._BUTTON_DEFAULT_Y
        self._position_button_box()
        return self._box

    def overlay(self, text: str, buttons: list[str], y: int = 300) -> str:
        """Display ``text`` with custom ``buttons`` and return the choice."""
        choice: dict[str, str] = {"value": ""}

        def _set_choice(label: str) -> None:
            choice["value"] = label
            self.accept()

        self.show_message(text)
        box = self.add_button_box()
        self._box_design_y = y
        self._position_button_box()
        for btn in list(box.buttons()):
            box.removeButton(btn)
        for label in buttons:
            btn = QPushButton(label)
            box.addButton(btn, QDialogButtonBox.ActionRole)
            btn.clicked.connect(lambda _, lbl=label: _set_choice(lbl))
        exec_modal(self)
        return choice["value"]

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        self._background.setGeometry(self.rect())
        self._position_message()
        self._position_button_box()

    def _scale_width(self, value: int) -> int:
        base_width = max(1, self._design_size.width())
        return int(round(value * self.width() / base_width))

    def _scale_height(self, value: int) -> int:
        base_height = max(1, self._design_size.height())
        return int(round(value * self.height() / base_height))

    def _position_message(self) -> None:
        if self._message is None:
            return
        self._message.setGeometry(
            0,
            self._scale_height(self._MESSAGE_Y),
            self.width(),
            self._scale_height(self._MESSAGE_HEIGHT),
        )

    def _position_button_box(self) -> None:
        if self._box is None:
            return
        design_y = self._box_design_y if self._box_design_y is not None else self._BUTTON_DEFAULT_Y
        self._box.setGeometry(
            0,
            self._scale_height(design_y),
            self.width(),
            self._box.sizeHint().height(),
        )
