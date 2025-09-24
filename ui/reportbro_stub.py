"""Offline helpers for the ReportBro document manager.

This module provides a light-weight user interface that is displayed when the
official ReportBro editor is not configured in the client environment.  The
dialog offers guidance on how to install the real dependency and keeps the
repository free of bundled binaries.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import shlex
from pathlib import Path
from typing import Iterable, TYPE_CHECKING

from utils import get_project_root
from utils import reportbro_installer

logger = logging.getLogger(__name__)

TEMPLATES_DIR = get_project_root() / "reporting" / "templates"

INSTALL_SCRIPT = Path("tools") / "install_reportbro.py"

if TYPE_CHECKING:  # pragma: no cover - imported lazily for runtime environments
    from PyQt5.QtWidgets import QWidget


def _iter_template_files(directory: Path) -> Iterable[Path]:
    try:
        yield from directory.iterdir()
    except FileNotFoundError:
        logger.warning("[ReportBro] Diretório de templates inexistente: %s", directory)
    except OSError as exc:  # pragma: no cover - defensive logging
        logger.warning("[ReportBro] Falha ao listar templates em %s: %s", directory, exc)


def discover_reportbro_templates(directory: Path | None = None) -> list[Path]:
    """Return the available ReportBro template files sorted alphabetically."""

    directory = directory or TEMPLATES_DIR
    candidates = [
        path
        for path in _iter_template_files(directory)
        if path.suffix.lower() == ".json" and path.is_file()
    ]
    return sorted(candidates)


def _format_command(arguments: Iterable[str]) -> str:
    return " ".join(shlex.quote(arg) for arg in arguments)


def _build_installation_hint() -> str:
    command = reportbro_installer.build_pip_install_command(
        reportbro_installer.REPORTBRO_REQUIREMENT,
        reportbro_installer.default_pip_args(),
    )
    return (
        "Execute o script abaixo numa consola com permissões de utilizador para "
        "instalar o ReportBro automaticamente e ativar o editor oficial.\n\n"
        f"    python {INSTALL_SCRIPT}\n\n"
        "O script tenta primeiro uma instalação padrão e, se necessário, "
        "repete com a flag --user. O comando inicial é:\n\n"
        f"    {_format_command(command)}"
    )


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
        QPushButton,
        QVBoxLayout,
    )

    @dataclass
    class _InstallResult:
        status: str
        details: str | None = None

    class ReportBroEditorStubDialog(QDialog):
        """Simple dialog guiding the user while the real editor is unavailable."""

        def __init__(self, parent_widget: "QWidget | None" = None) -> None:
            super().__init__(parent_widget)
            self.setWindowTitle("Gestor de Documentos (modo offline)")
            self.setModal(True)
            self.resize(620, 420)
            layout = QVBoxLayout(self)

            intro = QLabel(
                "O editor oficial do ReportBro não está configurado. Pode abrir os "
                "templates locais para edição manual ou executar o script de "
                "instalação automática para preparar o ambiente."
            )
            intro.setWordWrap(True)
            layout.addWidget(intro)

            hint = QLabel(_build_installation_hint())
            hint.setWordWrap(True)
            hint.setTextFormat(Qt.PlainText)
            hint.setObjectName("reportbroHintLabel")
            layout.addWidget(hint)

            self.templates_list = QListWidget(self)
            self.templates_list.itemDoubleClicked.connect(self._open_selected_template)
            layout.addWidget(self.templates_list)

            actions_layout = QHBoxLayout()
            self.open_folder_button = QPushButton("Abrir pasta de templates", self)
            self.open_folder_button.clicked.connect(self._open_templates_directory)
            actions_layout.addWidget(self.open_folder_button)

            self.install_button = QPushButton("Instalar ReportBro", self)
            self.install_button.clicked.connect(self._install_reportbro)
            actions_layout.addWidget(self.install_button)

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
            logger.info("[ReportBro] Abrir template local: %s", path)
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
                QMessageBox.warning(
                    self,
                    self.windowTitle(),
                    "Não foi possível abrir o template selecionado no gestor de ficheiros.",
                )

        def _open_templates_directory(self) -> None:
            logger.info("[ReportBro] Abrir pasta de templates: %s", TEMPLATES_DIR)
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(TEMPLATES_DIR))):
                QMessageBox.warning(
                    self,
                    self.windowTitle(),
                    "Não foi possível abrir a pasta de templates no gestor de ficheiros.",
                )

        def _install_reportbro(self) -> None:
            result = self._run_installer()
            if result.status == "skipped":
                QMessageBox.information(
                    self,
                    self.windowTitle(),
                    "O ReportBro já se encontra instalado nesta máquina.",
                )
            elif result.status == "success":
                QMessageBox.information(
                    self,
                    self.windowTitle(),
                    "Instalação concluída. Reinicie o gestor para usar o editor oficial.",
                )
            else:
                QMessageBox.critical(
                    self,
                    self.windowTitle(),
                    result.details
                    or "Não foi possível instalar o ReportBro automaticamente.",
                )

        def _run_installer(self) -> _InstallResult:
            try:
                logger.info("[ReportBro] A executar instalador de dependências")
                installed = reportbro_installer.ensure_reportbro_installed()
            except reportbro_installer.InstallationError as exc:
                logger.warning("[ReportBro] Instalação falhou: %s", exc)
                return _InstallResult("error", str(exc))
            except Exception:
                logger.exception("[ReportBro] Erro inesperado ao instalar ReportBro")
                return _InstallResult("error")
            return _InstallResult("success" if installed else "skipped")

    dialog = ReportBroEditorStubDialog(parent)
    dialog.exec_()


__all__ = [
    "open_reportbro_stub_dialog",
    "discover_reportbro_templates",
]
