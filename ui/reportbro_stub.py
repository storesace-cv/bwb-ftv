"""Offline fallback for the ReportBro document manager."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "reporting" / "templates"

if TYPE_CHECKING:  # pragma: no cover - hints only
    from PyQt5.QtWidgets import QWidget


def discover_reportbro_templates(directory: Path | None = None) -> list[Path]:
    """Return the available ReportBro template files sorted alphabetically."""

    directory = directory or TEMPLATES_DIR
    if not directory.exists():
        logger.warning("[ReportBro] Diretório de templates inexistente: %s", directory)
        return []

    return sorted(
        path
        for path in directory.glob("*.json")
        if path.is_file()
    )


def resolve_reportbro_url(target: str) -> "QUrl | None":
    """Return a :class:`QUrl` pointing to ``target`` or ``None`` if invalid."""

    try:
        from PyQt5.QtCore import QUrl
    except (ModuleNotFoundError, ImportError):  # pragma: no cover - fallback for stripped CI images
        logger.debug("[ReportBro] PyQt5 indisponível ao resolver URL de editor")
        return None

    if not target:
        return None

    path = Path(target)
    if path.exists():
        if path.is_dir():
            path = path / "index.html"
        return QUrl.fromLocalFile(str(path))

    url = QUrl.fromUserInput(target)
    if not url.isValid() or url.isEmpty():
        return None

    return url


def open_reportbro_stub_dialog(parent: "QWidget | None") -> None:  # pragma: no cover - GUI
    """Show the ReportBro stub dialog modally."""

    from PyQt5.QtCore import Qt, QUrl
    from PyQt5.QtGui import QDesktopServices
    from PyQt5.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QVBoxLayout,
    )

    class TemplateEditorDialog(QDialog):
        """Lightweight JSON editor for local ReportBro templates."""

        def __init__(self, template_path: Path, parent_widget: "QWidget | None") -> None:
            super().__init__(parent_widget)
            self._template_path = template_path
            self.setWindowTitle(f"Editar template — {template_path.name}")
            self.resize(720, 520)

            layout = QVBoxLayout(self)

            header = QLabel(
                "Revise o conteúdo JSON do template selecionado. "
                "As alterações serão guardadas diretamente no ficheiro."
            )
            header.setWordWrap(True)
            layout.addWidget(header)

            path_label = QLabel(f"<code>{template_path}</code>")
            path_label.setTextFormat(Qt.RichText)
            layout.addWidget(path_label)

            self._editor = QPlainTextEdit(self)
            self._editor.setLineWrapMode(QPlainTextEdit.NoWrap)
            layout.addWidget(self._editor, 1)

            button_box = QDialogButtonBox(
                QDialogButtonBox.Save | QDialogButtonBox.Cancel,
                Qt.Horizontal,
                self,
            )
            button_box.accepted.connect(self._save_and_close)
            button_box.rejected.connect(self.reject)
            layout.addWidget(button_box)

            self._load_template()

        def _load_template(self) -> None:
            try:
                content = self._template_path.read_text(encoding="utf-8")
            except OSError as exc:
                QMessageBox.warning(
                    self,
                    self.windowTitle(),
                    "Não foi possível ler o template selecionado:\n" f"{exc}",
                )
                content = ""
            self._editor.setPlainText(content)

        def _save_and_close(self) -> None:
            raw_content = self._editor.toPlainText()
            try:
                parsed = json.loads(raw_content)
            except json.JSONDecodeError as exc:
                QMessageBox.warning(
                    self,
                    self.windowTitle(),
                    "O conteúdo não é JSON válido:\n"
                    f"Linha {exc.lineno}, coluna {exc.colno}: {exc.msg}",
                )
                return

            formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
            if not formatted.endswith("\n"):
                formatted += "\n"

            try:
                self._template_path.write_text(formatted, encoding="utf-8")
            except OSError as exc:
                QMessageBox.critical(
                    self,
                    self.windowTitle(),
                    "Não foi possível guardar o template:\n" f"{exc}",
                )
                return

            self.accept()

    class ReportBroEditorStubDialog(QDialog):

        """Simple dialog guiding the user while the real editor is unavailable."""

        def __init__(self, parent_widget: "QWidget | None" = None) -> None:
            super().__init__(parent_widget)
            self.setWindowTitle("Gestor de Documentos (modo offline)")
            self.setModal(True)
            self.resize(560, 360)

            self._remote_target = os.getenv("FTV_REPORTBRO_EDITOR_URL", "").strip()

            layout = QVBoxLayout(self)

            intro = QLabel(
                "O editor original do ReportBro não está configurado. Pode abrir "
                "os templates locais para edição manual ou definir a variável "
                "de ambiente <code>FTV_REPORTBRO_EDITOR_URL</code> para usar "
                "uma instância remota."
            )
            intro.setWordWrap(True)
            intro.setTextFormat(Qt.RichText)
            layout.addWidget(intro)

            self.templates_list = QListWidget(self)
            self.templates_list.itemDoubleClicked.connect(self._open_selected_template)
            layout.addWidget(self.templates_list)

            actions_layout = QHBoxLayout()
            if self._remote_target:
                self.open_remote_button = QPushButton("Abrir editor remoto", self)
                self.open_remote_button.clicked.connect(self._open_remote_editor)
                actions_layout.addWidget(self.open_remote_button)
            else:
                self.open_remote_button = None
            self.open_folder_button = QPushButton("Abrir pasta de templates", self)
            self.open_folder_button.clicked.connect(self._open_templates_directory)
            actions_layout.addWidget(self.open_folder_button)

            self.reload_button = QPushButton("Recarregar", self)
            self.reload_button.clicked.connect(self._populate_templates)
            actions_layout.addWidget(self.reload_button)

            actions_layout.addStretch(1)
            layout.addLayout(actions_layout)

            button_box = QDialogButtonBox(QDialogButtonBox.Close, Qt.Horizontal, self)
            button_box.rejected.connect(self.reject)
            layout.addWidget(button_box)

            self._populate_templates()

        # ------------------------- Helpers -------------------------

        def _populate_templates(self) -> None:
            self.templates_list.clear()
            templates = discover_reportbro_templates()
            if not templates:
                empty_item = QListWidgetItem(
                    "Nenhum template encontrado em reporting/templates/"
                )
                empty_item.setFlags(Qt.NoItemFlags)
                self.templates_list.addItem(empty_item)
                return

            for template_path in templates:
                item = QListWidgetItem(template_path.name)
                item.setData(Qt.UserRole, template_path)
                self.templates_list.addItem(item)

        def _open_selected_template(self, item: QListWidgetItem) -> None:
            path = item.data(Qt.UserRole)
            if not isinstance(path, Path):
                return

            logger.info("[ReportBro] A editar template local: %s", path)
            editor = TemplateEditorDialog(path, self)
            editor.exec_()

        def _open_templates_directory(self) -> None:
            logger.info("[ReportBro] Abrir pasta de templates: %s", TEMPLATES_DIR)
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(TEMPLATES_DIR))):
                QMessageBox.warning(
                    self,
                    self.windowTitle(),
                    "Não foi possível abrir a pasta de templates no gestor de ficheiros.",
                )

        def _open_remote_editor(self) -> None:
            if not self._remote_target:
                return

            url = resolve_reportbro_url(self._remote_target)
            if url is None:
                QMessageBox.warning(
                    self,
                    self.windowTitle(),
                    "Endereço configurado inválido para o editor ReportBro.",
                )
                logger.warning(
                    "[ReportBro] URL inválida configurada: %s", self._remote_target
                )
                return

            logger.info("[ReportBro] A abrir editor remoto em %s", url.toString())
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(
                    self,
                    self.windowTitle(),
                    "Não foi possível abrir o editor remoto. Verifique a ligação.",
                )
                logger.warning(
                    "[ReportBro] Falha ao abrir editor remoto em %s",
                    url.toString(),
                )

    dialog = ReportBroEditorStubDialog(parent)
    dialog.exec_()


__all__ = [
    "open_reportbro_stub_dialog",
    "discover_reportbro_templates",
    "resolve_reportbro_url",
]
