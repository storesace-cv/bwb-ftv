"""Embedded ReportBro Designer window presented in kiosk mode."""

from __future__ import annotations

import importlib.util
import logging
from typing import TYPE_CHECKING, Any

QT_AVAILABLE = importlib.util.find_spec("PyQt5") is not None
QT_WEBENGINE_AVAILABLE = bool(
    QT_AVAILABLE and importlib.util.find_spec("PyQt5.QtWebEngineWidgets") is not None
)

if QT_AVAILABLE:
    from PyQt5.QtCore import QEvent, Qt, QUrl
    from PyQt5.QtGui import QKeyEvent
    from PyQt5.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
else:  # pragma: no cover - executed when Qt is not installed
    QEvent = Qt = QUrl = QKeyEvent = None  # type: ignore[assignment]
    QDialog = QHBoxLayout = QLabel = QPushButton = QVBoxLayout = QWidget = object  # type: ignore[assignment]

if QT_AVAILABLE and QT_WEBENGINE_AVAILABLE:
    from PyQt5.QtWebEngineWidgets import QWebEngineView

else:  # pragma: no cover - executed when QtWebEngine is not installed
    QWebEngineView = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from ui.reportbro_server import ReportBroEndpoint
    from PyQt5.QtWidgets import QWidget as QWidgetType
else:  # pragma: no cover - runtime fallback
    QWidgetType = Any

logger = logging.getLogger(__name__)

if QT_AVAILABLE:

    class ReportBroKioskDialog(QDialog):

        """Dialog embedding the ReportBro Designer."""

        def __init__(self, parent: QWidget | None, url: QUrl) -> None:
            super().__init__(parent)
            self._url = url
            self._title_label: QLabel | None = None
            self._web_view: QWebEngineView | None = None
            self._build_ui()

        def _build_ui(self) -> None:
            self.setObjectName("reportbroKioskDialog")
            self.setWindowModality(Qt.ApplicationModal)
            self.setAttribute(Qt.WA_DeleteOnClose, True)
            self.setMinimumSize(960, 640)
            self.resize(1280, 800)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            header = QWidget(self)
            header.setObjectName("reportbroKioskHeader")
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(24, 12, 24, 12)
            header_layout.setSpacing(12)

            title = QLabel("ReportBro Designer", header)
            title.setObjectName("reportbroKioskTitle")
            title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            header_layout.addWidget(title)
            self._title_label = title

            header_layout.addStretch(1)

            open_button = QPushButton("Abrir", header)
            open_button.setObjectName("reportbroKioskOpen")
            open_button.clicked.connect(self._trigger_open)
            header_layout.addWidget(open_button)

            close_button = QPushButton("Fechar", header)
            close_button.setObjectName("reportbroKioskClose")
            close_button.clicked.connect(self.accept)
            header_layout.addWidget(close_button)

            layout.addWidget(header, 0)

            if QWebEngineView is None:
                placeholder = QLabel(
                    "O modo kiosk requer o componente QtWebEngine instalado.",
                    self,
                )
                placeholder.setAlignment(Qt.AlignCenter)
                layout.addWidget(placeholder, 1)
                return

            web_view = QWebEngineView(self)
            web_view.setObjectName("reportbroKioskWebView")
            web_view.setContextMenuPolicy(Qt.NoContextMenu)
            web_view.load(self._url)
            web_view.titleChanged.connect(self._on_title_changed)
            self._web_view = web_view
            layout.addWidget(web_view, 1)

            self._apply_styles()

        def _apply_styles(self) -> None:
            self.setStyleSheet(
                """
                #reportbroKioskDialog {
                    background-color: #0f172a;
                }
                #reportbroKioskHeader {
                    background-color: #111827;
                    color: #f8fafc;
                }
                #reportbroKioskTitle {
                    font-size: 16px;
                    font-weight: 600;
                }
                #reportbroKioskOpen {
                    background-color: #2563eb;
                    border-radius: 6px;
                    padding: 6px 20px;
                    color: #f9fafb;
                }
                #reportbroKioskOpen:hover {
                    background-color: #1d4ed8;
                }
                #reportbroKioskOpen:pressed {
                    background-color: #1e40af;
                }
                #reportbroKioskClose {
                    background-color: #ef4444;
                    border-radius: 6px;
                    padding: 6px 20px;
                    color: #f9fafb;
                }
                #reportbroKioskClose:hover {
                    background-color: #dc2626;
                }
                #reportbroKioskClose:pressed {
                    background-color: #b91c1c;
                }

            """
            )

        def showEvent(self, event: QEvent) -> None:  # pragma: no cover - GUI runtime
            super().showEvent(event)
            self.activateWindow()

        def keyPressEvent(self, event: QKeyEvent) -> None:  # pragma: no cover - GUI runtime
            if event.key() in {Qt.Key_Escape, Qt.Key_F11}:
                self.accept()
                return
            super().keyPressEvent(event)

        def _trigger_open(self) -> None:
            if self._web_view is None:
                return
            page = self._web_view.page()
            if page is None:
                return
            page.runJavaScript("document.getElementById('btn-open')?.click();")

        def _on_title_changed(self, title: str) -> None:
            if self._title_label is None:
                return
            if title:
                self._title_label.setText(f"ReportBro Designer — {title}")
            else:
                self._title_label.setText("ReportBro Designer")

else:  # pragma: no cover - executed when Qt is not installed

    class ReportBroKioskDialog:  # type: ignore[too-many-ancestors]
        """Placeholder used when Qt is unavailable at runtime."""

        def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
            raise RuntimeError("QtWebEngine não está disponível para o modo kiosk.")


def open_reportbro_kiosk(parent: QWidgetType | None, endpoint: "ReportBroEndpoint") -> bool:

    """Open the ReportBro Designer in a modal dialog."""

    if not QT_AVAILABLE or QWebEngineView is None:
        logger.info("[ReportBro] QtWebEngine não está disponível para o modo kiosk.")
        return False

    url = QUrl(f"http://{endpoint.host}:{endpoint.port}/designer")
    dialog = ReportBroKioskDialog(parent, url)
    dialog.exec_()
    return True


__all__ = ["open_reportbro_kiosk", "ReportBroKioskDialog"]
