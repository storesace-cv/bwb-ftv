"""Embedded ReportBro Designer window presented in kiosk mode."""

from __future__ import annotations

import importlib.util
import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable
from urllib import error, request

QT_AVAILABLE = importlib.util.find_spec("PyQt5") is not None
QT_WEBENGINE_AVAILABLE = bool(
    QT_AVAILABLE and importlib.util.find_spec("PyQt5.QtWebEngineWidgets") is not None
)

if QT_AVAILABLE:
    from PyQt5.QtCore import QEvent, Qt, QUrl
    from PyQt5.QtGui import QKeyEvent
    from PyQt5.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
else:  # pragma: no cover - executed when Qt is not installed
    QEvent = Qt = QUrl = QKeyEvent = None  # type: ignore[assignment]
    QDialog = (
        QDialogButtonBox
    ) = (  # type: ignore[assignment]
        QHBoxLayout
    ) = (
        QLabel
    ) = (
        QListWidget
    ) = (
        QListWidgetItem
    ) = (
        QMessageBox
    ) = (
        QPushButton
    ) = (
        QVBoxLayout
    ) = QWidget = object

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

    @dataclass
    class TemplateInfo:
        """Metadata about a ReportBro template exposed by the kiosk."""

        name: str
        updated_at: str

    class TemplatePickerDialog(QDialog):
        """Simple dialog that lets the user choose a template to load."""

        def __init__(self, parent: QWidget | None, templates: Iterable[TemplateInfo]) -> None:
            super().__init__(parent)
            self._templates = list(templates)
            self._list_widget: QListWidget | None = None
            self._selected: str | None = None
            self.setWindowTitle("Abrir template")
            self.setModal(True)
            self._build_ui()

        def _build_ui(self) -> None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            info_label = QLabel("Seleccione um template da lista:", self)
            layout.addWidget(info_label)

            list_widget = QListWidget(self)
            list_widget.setObjectName("reportbroTemplatePickerList")
            for template in self._templates:
                item = QListWidgetItem(f"{template.name} — {template.updated_at}")
                item.setData(Qt.UserRole, template.name)
                list_widget.addItem(item)
            if list_widget.count() > 0:
                list_widget.setCurrentRow(0)
            list_widget.itemDoubleClicked.connect(self._accept_current)
            layout.addWidget(list_widget)
            self._list_widget = list_widget

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
            buttons.accepted.connect(self._accept_current)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

        def _accept_current(self) -> None:
            if self._list_widget is None:
                self.reject()
                return
            current = self._list_widget.currentItem()
            if current is None:
                QMessageBox.information(self, "Abrir template", "Seleccione um template primeiro.")
                return
            self._selected = current.data(Qt.UserRole)
            self.accept()

        @property
        def selected_template(self) -> str | None:
            return self._selected

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
            open_button.clicked.connect(self._show_template_picker)
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

        def _show_template_picker(self) -> None:
            templates = self._fetch_templates()
            if not templates:
                return

            dialog = TemplatePickerDialog(self, templates)
            if dialog.exec_() != QDialog.Accepted:
                return

            target = dialog.selected_template
            if not target:
                return

            self._load_template(target)

        def _fetch_templates(self) -> list[TemplateInfo]:
            base = self._url
            if not base.isValid():
                QMessageBox.critical(
                    self,
                    "Abrir template",
                    "Não foi possível determinar o endereço do servidor ReportBro.",
                )
                return []

            try:
                with request.urlopen(base.resolved(QUrl("/templates/list")).toString(), timeout=10) as response:
                    payload = response.read()
            except error.URLError as exc:
                logger.error("[ReportBro] Falha ao obter lista de templates: %s", exc)
                QMessageBox.critical(
                    self,
                    "Abrir template",
                    "Não foi possível carregar a lista de templates.",
                )
                return []

            try:
                data = json.loads(payload.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:  # pragma: no cover - defensive
                logger.error("[ReportBro] Resposta inválida da lista de templates: %s", exc)
                QMessageBox.critical(
                    self,
                    "Abrir template",
                    "Resposta inválida do servidor ao carregar templates.",
                )
                return []

            templates: list[TemplateInfo] = []
            for entry in data:
                name = entry.get("name")
                updated_at = entry.get("updated_at", "")
                if not name:
                    continue
                templates.append(TemplateInfo(str(name), str(updated_at)))
            if not templates:
                QMessageBox.information(
                    self,
                    "Abrir template",
                    "Não foram encontrados templates disponíveis.",
                )
            return templates

        def _load_template(self, template_name: str) -> None:
            if self._web_view is None:
                return
            page = self._web_view.page()
            if page is None:
                return
            script = f"""
(() => {{
    const select = document.getElementById('template-select');
    const openButton = document.getElementById('btn-open');
    if (!select || !openButton) {{
        return false;
    }}
    const value = {json.dumps(template_name)};
    const option = Array.from(select.options).find((item) => item.value === value);
    if (!option) {{
        return false;
    }}
    select.value = value;
    select.dispatchEvent(new Event('change', {{ bubbles: true }}));
    openButton.click();
    return true;
}})();
            """
                """
(() => {
    const select = document.getElementById('template-select');
    if (!select) {
        return;
    }
    if (!select.dataset.rbKioskAutoload) {
        select.addEventListener('change', () => {
            if (select.value) {
                document.getElementById('btn-open')?.click();
            }
        });
        select.dataset.rbKioskAutoload = '1';
    }
    if (!select.value) {
        select.focus();
        if (typeof select.showPicker === 'function') {
            select.showPicker();
        } else {
            const event = new MouseEvent('mousedown', { bubbles: true });
            select.dispatchEvent(event);
        }
        return;
    }
    document.getElementById('btn-open')?.click();
})();
                """
            )


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
