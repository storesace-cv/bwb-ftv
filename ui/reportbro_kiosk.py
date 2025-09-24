"""Embedded ReportBro Designer window presented in kiosk mode."""

from __future__ import annotations

import importlib.util
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

QT_AVAILABLE = importlib.util.find_spec("PyQt5") is not None
QT_WEBENGINE_AVAILABLE = bool(
    QT_AVAILABLE and importlib.util.find_spec("PyQt5.QtWebEngineWidgets") is not None
)

if QT_AVAILABLE:
    from PyQt5.QtCore import Qt, QUrl
    from PyQt5.QtGui import QKeyEvent
    from PyQt5.QtWidgets import (
        QDialog,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
else:  # pragma: no cover - executed when Qt is not installed
    Qt = QUrl = QKeyEvent = None  # type: ignore[assignment]
    QFileDialog = QMessageBox = None  # type: ignore[assignment]
    QDialog = QHBoxLayout = QLabel = QPushButton = QVBoxLayout = QWidget = object  # type: ignore[assignment]

if QT_AVAILABLE and QT_WEBENGINE_AVAILABLE:
    try:  # pragma: no cover - heavy import guarded for runtime availability
        from PyQt5.QtWebEngineWidgets import QWebEngineView
    except ImportError as exc:  # pragma: no cover - runtime guard on misconfiguration
        logger.warning(
            "[ReportBro] QtWebEngine indisponível: %s", exc,
        )
        QT_WEBENGINE_AVAILABLE = False
        QWebEngineView = None  # type: ignore[assignment]
else:  # pragma: no cover - executed when QtWebEngine is not installed
    QWebEngineView = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from ui.reportbro_server import ReportBroEndpoint
    from PyQt5.QtWidgets import QWidget as QWidgetType
else:  # pragma: no cover - runtime fallback
    QWidgetType = Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolve_default_templates_dir(project_root: Path | None = None) -> Path:
    """Discover the most relevant directory to initialise file dialogs."""

    base = project_root or _PROJECT_ROOT
    candidates = [
        base / "app" / "templates_store" / "templates",
        base / "reporting" / "templates",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return base


def _build_template_injection_script(report: dict[str, Any], source_label: str) -> str:
    """Prepare a JavaScript snippet that loads a template inside the designer."""

    serialized_report = json.dumps(report, ensure_ascii=False)
    label_literal = json.dumps(source_label)
    return """
        (function() {
            if (typeof designerInstance === 'undefined' || !designerInstance) {
                return {status: 'error', message: 'Designer ainda não está pronto. Tente novamente.'};
            }
            try {
                const report = {report_payload};
                designerInstance.load(report);
                if (typeof designerInstance.setModified === 'function') {
                    designerInstance.setModified(false);
                }
                if (typeof currentTemplateName !== 'undefined') {
                    currentTemplateName = null;
                }
                if (typeof selectElement !== 'undefined' && selectElement) {
                    selectElement.value = "";
                }
                if (typeof setStatus === 'function') {
                    setStatus('Template carregado de ficheiro: ' + {label});
                }
                if (typeof showToast === 'function') {
                    showToast('Template carregado a partir de ficheiro.');
                }
                return {status: 'ok'};
            } catch (error) {
                const message = error && error.message ? error.message : String(error);
                return {status: 'error', message};
            }
        })();
    """.replace("{report_payload}", serialized_report).replace("{label}", label_literal)


if QT_AVAILABLE:

    class ReportBroKioskDialog(QDialog):
        """Modal dialog embedding the ReportBro Designer."""

        def __init__(self, parent: QWidget | None, url: QUrl) -> None:
            super().__init__(parent)
            self._url = url
            self._title_label: QLabel | None = None
            self._web_view: QWebEngineView | None = None
            self._templates_dir = _resolve_default_templates_dir()
            self._build_ui()

        def _build_ui(self) -> None:
            self.setObjectName("reportbroKioskDialog")
            self.setWindowModality(Qt.ApplicationModal)
            self.setWindowFlag(Qt.FramelessWindowHint, True)
            self.setAttribute(Qt.WA_DeleteOnClose, True)
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

            open_file_button = QPushButton("Abrir ficheiro…", header)
            open_file_button.setObjectName("reportbroKioskOpenFile")
            open_file_button.clicked.connect(self._on_open_file_clicked)
            header_layout.addWidget(open_file_button)

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
            layout.addWidget(web_view, 1)
            self._web_view = web_view

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
                #reportbroKioskOpenFile {
                    background-color: #2563eb;
                    border-radius: 6px;
                    padding: 6px 20px;
                    color: #f9fafb;
                }
                #reportbroKioskOpenFile:hover {
                    background-color: #1d4ed8;
                }
                #reportbroKioskOpenFile:pressed {
                    background-color: #1e40af;
                }
            """
            )

        def keyPressEvent(self, event: QKeyEvent) -> None:  # pragma: no cover - GUI runtime
            if event.key() in {Qt.Key_Escape, Qt.Key_F11}:
                self.accept()
                return
            super().keyPressEvent(event)

        def _on_title_changed(self, title: str) -> None:
            if self._title_label is None:
                return
            if title:
                self._title_label.setText(f"ReportBro Designer — {title}")
            else:
                self._title_label.setText("ReportBro Designer")

        def _on_open_file_clicked(self) -> None:
            if self._web_view is None:
                return
            initial_dir = self._templates_dir if self._templates_dir.exists() else Path.home()
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Abrir ficheiro ReportBro",
                str(initial_dir),
                "Templates ReportBro (*.json);;Todos os ficheiros (*)",
            )
            if not filename:
                return

            path = Path(filename)
            try:
                content = path.read_text(encoding="utf-8")
            except OSError as exc:
                logger.warning("[ReportBro] Falha ao ler ficheiro seleccionado: %s", exc)
                QMessageBox.warning(
                    self,
                    "ReportBro",
                    "Não foi possível ler o ficheiro seleccionado.",
                )
                return

            try:
                report = json.loads(content)
            except json.JSONDecodeError:
                QMessageBox.warning(
                    self,
                    "ReportBro",
                    "O ficheiro seleccionado não contém JSON válido.",
                )
                return

            if not isinstance(report, dict):
                QMessageBox.warning(
                    self,
                    "ReportBro",
                    "O ficheiro seleccionado não contém um template ReportBro válido.",
                )
                return

            script = _build_template_injection_script(report, path.name)

            def _handle_result(result: Any) -> None:
                if isinstance(result, dict) and result.get("status") != "ok":
                    QMessageBox.warning(
                        self,
                        "ReportBro",
                        result.get("message", "Não foi possível carregar o template."),
                    )
                    return
                self._templates_dir = path.parent

            self._web_view.page().runJavaScript(script, _handle_result)

else:  # pragma: no cover - executed when Qt is not installed

    class ReportBroKioskDialog:  # type: ignore[too-many-ancestors]
        """Placeholder used when Qt is unavailable at runtime."""

        def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
            raise RuntimeError("QtWebEngine não está disponível para o modo kiosk.")


def open_reportbro_kiosk(parent: QWidgetType | None, endpoint: "ReportBroEndpoint") -> bool:
    """Open the ReportBro Designer in a kiosk dialog."""

    if not QT_AVAILABLE or QWebEngineView is None:
        logger.info("[ReportBro] QtWebEngine não está disponível para o modo kiosk.")
        return False

    url = QUrl(f"http://{endpoint.host}:{endpoint.port}/designer")
    dialog = ReportBroKioskDialog(parent, url)
    dialog.exec_()
    return True


__all__ = ["open_reportbro_kiosk", "ReportBroKioskDialog"]
