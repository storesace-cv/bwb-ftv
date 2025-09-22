import logging
import sqlite3
from collections.abc import Callable
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QToolTip
from ui.utilities import DEFAULT_TOOLTIP_DURATION_MS
from utils.paths import get_project_root
from utils.formatting import format_pt_number
from data import create_backup, restore_backup
from .qt_compat import exec_modal

logger = logging.getLogger(__name__)


def missing_import_files() -> list[str]:
    base = get_project_root() / "imports"
    files = [
        base / "Produtos_Base.xlsx",
        base / "FichasTecnicas_base.xlsx",
        base / "PreçosTaxas_base.xlsx",
    ]
    return [fp.name for fp in files if not fp.exists()]


def import_data(parent, service, load_record, cur_index):
    missing = missing_import_files()
    if missing:
        QMessageBox.warning(
            parent,
            "Importar Dados",
            "Ficheiros em falta: " + ", ".join(sorted(missing)),
        )
        return
    try:
        service.import_from_excel()
        load_record(cur_index)
        QMessageBox.information(parent, "Importar Dados", "Importação concluída.")
    except Exception as exc:  # pragma: no cover - UI feedback only
        logger.exception("Import failed", exc_info=exc)
        QMessageBox.critical(parent, "Importar Dados", f"Falha na importação: {exc}")


def update_data(parent, service, load_record, cur_index):
    missing = missing_import_files()
    if missing:
        QMessageBox.warning(
            parent,
            "Atualizar Dados",
            "Ficheiros em falta: " + ", ".join(sorted(missing)),
        )
        return
    try:
        report_path = service.update_from_excel()
        load_record(cur_index)
        message = "Atualização concluída."
        if report_path:
            message += f"\nRelatório: {report_path}"
        QMessageBox.information(parent, "Atualizar Dados", message)
    except Exception as exc:  # pragma: no cover - UI feedback only
        logger.exception("Update failed", exc_info=exc)
        QMessageBox.critical(parent, "Atualizar Dados", f"Falha na atualização: {exc}")


def backup_database(parent, datastore):
    """Create a timestamped backup of the database file."""

    if getattr(datastore, "conn", None) is None:
        QMessageBox.warning(parent, "Segurança", "Base de dados indisponível.")
        return
    try:
        backup = create_backup()
        QMessageBox.information(
            parent, "Segurança", f"Ficheiro copiado: {backup.name}."
        )
    except Exception as exc:  # pragma: no cover - UI feedback only
        logger.exception("Backup failed", exc_info=exc)
        QMessageBox.critical(parent, "Segurança", f"Falha na cópia: {exc}")


def restore_database(parent, datastore, on_restore: Callable | None = None):
    """Restore ``ftv.db`` from a selected backup file and rebuild caches.

    Parameters
    ----------
    parent
        Parent widget for message boxes.
    datastore
        :class:`DataStore` instance to rebind to the restored database.
    on_restore
        Optional callback invoked after caches are reloaded. This allows the
        UI to refresh any state that depends on database contents.
    """

    backups_dir = get_project_root() / "databases" / "backups"
    if not backups_dir.exists() or not any(backups_dir.glob("*.db")):
        QMessageBox.warning(parent, "Reposição", "Nenhum backup encontrado.")
        return

    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        "Selecionar backup",
        str(backups_dir),
        "Database Files (*.db)",
    )
    if not file_path:
        return

    if getattr(datastore, "conn", None) is None:
        QMessageBox.warning(parent, "Reposição", "Base de dados indisponível.")
        return

    try:
        datastore.close()
        restore_backup(Path(file_path))
        db_path = get_project_root() / "databases" / "ftv.db"
        datastore.conn = sqlite3.connect(str(db_path))
        datastore.conn.row_factory = sqlite3.Row
        from data.repositories import (
            ProdutosRepo,
            IngredientesRepo,
            AuxiliaresRepo,
            PreparacaoRepo,
        )

        datastore.produtos = ProdutosRepo(datastore.conn)
        datastore.ingredientes = IngredientesRepo(datastore.conn)
        datastore.aux = AuxiliaresRepo(datastore.conn)
        datastore.prep = PreparacaoRepo(datastore.conn)
        datastore.reload_ids()
        if callable(on_restore):
            on_restore()
        QMessageBox.information(parent, "Reposição", "Reposição concluída.")
    except Exception as exc:  # pragma: no cover - UI feedback only
        logger.exception("Restore failed", exc_info=exc)
        QMessageBox.critical(parent, "Reposição", f"Falha na reposição: {exc}")


def edit_fcost_values(parent, repo) -> None:
    """Edit ``FcostValues`` ranges using a simple table dialog."""

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QFrame,
        QTableWidget,
        QTableWidgetItem,
        QPushButton,
        QVBoxLayout,
    )

    dlg = QDialog(parent)
    dlg.setWindowTitle("Valores FCOST")
    vbox = QVBoxLayout(dlg)

    tbl = QTableWidget(0, 5)
    tbl.setFrameShape(QFrame.NoFrame)
    tbl.setShowGrid(False)
    tbl.setHorizontalHeaderLabels(
        ["Nivel", "Nome", "ValorMin", "ValorMax", "Comentário"]
    )
    tbl.horizontalHeader().setStretchLastSection(True)
    tbl.setStyleSheet(
        """
        QTableWidget { border: none; }
        QTableWidget::item { margin: 0; padding: 0; border: none; }
        QTableWidget::item:hover { background: #00008b; color: #fff; }
        QHeaderView::section { border: none; }
        """
    )
    tbl.setContextMenuPolicy(Qt.CustomContextMenu)
    if hasattr(tbl, "setToolTipDuration"):
        tbl.setToolTipDuration(DEFAULT_TOOLTIP_DURATION_MS)
    viewport = tbl.viewport()
    if viewport is not None and hasattr(viewport, "setToolTipDuration"):
        viewport.setToolTipDuration(DEFAULT_TOOLTIP_DURATION_MS)

    def _copy_comment_tooltip(pos):
        viewport_pos = tbl.viewport().mapFrom(tbl, pos)
        item = tbl.itemAt(viewport_pos)
        if item is None:
            return
        text = item.toolTip()
        if not text:
            return
        QApplication.clipboard().setText(text)
        global_pos = tbl.viewport().mapToGlobal(viewport_pos)
        QToolTip.showText(global_pos, "Copiado para a área de transferência", tbl)

    tbl.customContextMenuRequested.connect(_copy_comment_tooltip)
    vbox.addWidget(tbl)

    hbox = QHBoxLayout()
    vbox.addLayout(hbox)
    bt_save = QPushButton("Gravar")
    hbox.addWidget(bt_save)
    bt_close = QPushButton("Fechar")
    hbox.addWidget(bt_close)

    def refresh():
        tbl.setRowCount(0)
        for nivel, nome, vmin, vmax, comentario in repo.list_levels():
            row = tbl.rowCount()
            tbl.insertRow(row)

            nivel_item = QTableWidgetItem(str(nivel))
            nivel_item.setFlags(nivel_item.flags() & ~Qt.ItemIsEditable)

            nome_item = QTableWidgetItem(nome)
            nome_item.setFlags(nome_item.flags() & ~Qt.ItemIsEditable)

            vmin_item = QTableWidgetItem(format_pt_number(vmin, missing=""))
            vmin_item.setFlags(vmin_item.flags() | Qt.ItemIsEditable)

            vmax_item = QTableWidgetItem(format_pt_number(vmax, missing=""))
            vmax_item.setFlags(vmax_item.flags() | Qt.ItemIsEditable)

            comentario_item = QTableWidgetItem(comentario or "")
            comentario_item.setFlags(
                comentario_item.flags() & ~Qt.ItemIsEditable
            )

            for item in [
                nivel_item,
                nome_item,
                vmin_item,
                vmax_item,
                comentario_item,
            ]:
                if comentario:
                    item.setToolTip(comentario)

            tbl.setItem(row, 0, nivel_item)
            tbl.setItem(row, 1, nome_item)
            tbl.setItem(row, 2, vmin_item)
            tbl.setItem(row, 3, vmax_item)
            tbl.setItem(row, 4, comentario_item)

    def save_changes():
        for row in range(tbl.rowCount()):
            vmin_item = tbl.item(row, 2)
            vmax_item = tbl.item(row, 3)
            if not vmin_item.text().strip() or not vmax_item.text().strip():
                QMessageBox.warning(
                    dlg,
                    "Valores FCOST",
                    "Todos os valores devem estar preenchidos.",
                )
                return

        for row in range(tbl.rowCount()):
            nivel = int(tbl.item(row, 0).text())
            vmin_text = tbl.item(row, 2).text()
            vmax_text = tbl.item(row, 3).text()
            if not repo.update_range(nivel, vmin_text, vmax_text):
                QMessageBox.warning(
                    dlg,
                    "Valores FCOST",
                    "Intervalo inválido detectado.",
                )
                refresh()
                return

        QMessageBox.information(dlg, "Valores FCOST", "Valores atualizados.")
        dlg.accept()

    bt_save.clicked.connect(save_changes)
    bt_close.clicked.connect(dlg.reject)

    refresh()
    exec_modal(dlg)


def manage_aux_table(
    parent,
    title: str,
    repo_methods: dict[str, Callable],
    on_change: Callable | None = None,
) -> None:
    """Display a simple dialog to manage auxiliary tables.

    Parameters
    ----------
    parent
        Parent widget for the dialog.
    title
        Window title for the dialog.
    repo_methods
        Mapping providing callables for ``list`` and ``add``.  The optional
        keys ``set_active`` and ``update`` enable toggling or renaming entries
        when present.
    on_change
        Optional callback invoked whenever the table content changes.

    The ``repo_methods`` mapping must provide callables for ``list`` and
    ``add``.  When a callable is supplied for ``set_active`` the dialog shows a
    toggle button to activate or deactivate entries.  When ``update`` is
    present the description column can be edited.
    """

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QInputDialog,
        QFrame,
        QTableWidget,
        QTableWidgetItem,
        QPushButton,
        QStyle,
        QVBoxLayout,
    )

    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    vbox = QVBoxLayout(dlg)
    tbl = QTableWidget(0, 2)
    tbl.setFrameShape(QFrame.NoFrame)
    tbl.setShowGrid(False)
    tbl.setHorizontalHeaderLabels(["Código", "Descrição"])
    tbl.horizontalHeader().setStretchLastSection(True)
    tbl.setStyleSheet(
        """
        QTableWidget { border: none; }
        QTableWidget::item { margin: 0; padding: 0; border: none; }
        QTableWidget::item:hover { background: #00008b; color: #fff; }
        QHeaderView::section { border: none; }
        """
    )
    vbox.addWidget(tbl)

    hbox = QHBoxLayout()
    vbox.addLayout(hbox)
    bt_add = QPushButton("Adicionar")
    hbox.addWidget(bt_add)
    bt_toggle = QPushButton("Inactivar/Activar")
    bt_toggle.setToolTip("Inactivar ou activar o registo selecionado")
    bt_toggle.setIcon(dlg.style().standardIcon(QStyle.SP_BrowserReload))
    hbox.addWidget(bt_toggle)

    toggle_handler = repo_methods.get("set_active")
    has_toggle = callable(toggle_handler)
    bt_toggle.setVisible(has_toggle)
    bt_close = QPushButton("Fechar")
    hbox.addWidget(bt_close)

    def refresh():
        tbl.setRowCount(0)
        for entry in repo_methods["list"]():
            try:
                cod, desc, ativo = entry
            except ValueError:
                try:
                    cod, desc = entry
                except ValueError:
                    continue
                ativo = 1
            row = tbl.rowCount()
            tbl.insertRow(row)
            cod_item = QTableWidgetItem(str(cod))
            cod_item.setFlags(cod_item.flags() & ~Qt.ItemIsEditable)
            cod_item.setData(Qt.UserRole, (cod, ativo))
            desc_item = QTableWidgetItem(desc)
            desc_item.setData(Qt.UserRole, (cod, ativo))
            desc_item.setFlags(desc_item.flags() | Qt.ItemIsEditable)
            if not ativo:
                cod_item.setForeground(Qt.gray)
                desc_item.setForeground(Qt.gray)
            tbl.setItem(row, 0, cod_item)
            tbl.setItem(row, 1, desc_item)

        rows = tbl.rowCount()
        max_rows = min(rows, 10)
        header_height = tbl.horizontalHeader().height()
        if rows:
            row_height = tbl.verticalHeader().sectionSize(0)
        else:
            row_height = tbl.verticalHeader().defaultSectionSize()
        frame = tbl.frameWidth() * 2
        visible_rows = max_rows or 1
        tbl.setFixedHeight(header_height + row_height * visible_rows + frame)
        tbl.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tbl.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        dlg.adjustSize()

    def add_item():
        text, ok = QInputDialog.getText(dlg, "Adicionar", "Descrição:")
        if ok and text.strip():
            repo_methods["add"](text.strip())
            refresh()
            if callable(on_change):
                on_change()

    def toggle_selected():
        row = tbl.currentRow()
        if row < 0:
            return
        cod_item = tbl.item(row, 0)
        if not has_toggle:
            return
        cod, ativo = cod_item.data(Qt.UserRole)
        new_state = 0 if ativo else 1
        if toggle_handler(cod, new_state):
            refresh()
            if callable(on_change):
                on_change()
        else:  # pragma: no cover - UI feedback only
            QMessageBox.warning(
                dlg,
                title,
                "Falha ao atualizar o registo.",
            )

    def rename_item(item: QTableWidgetItem):
        if item.column() != 1:
            return
        cod_item = tbl.item(item.row(), 0)
        cod, _ = cod_item.data(Qt.UserRole)
        text, ok = QInputDialog.getText(dlg, "Renomear", "Descrição:", text=item.text())
        if ok and text.strip() and text != item.text():
            try:
                ok_upd = repo_methods["update"](cod, text.strip())
            except Exception:  # pragma: no cover - UI feedback only
                ok_upd = False
            if ok_upd:
                refresh()
                if callable(on_change):
                    on_change()
            else:  # pragma: no cover - UI feedback only
                QMessageBox.warning(
                    dlg,
                    title,
                    "Falha ao atualizar o registo.",
                )

    bt_add.clicked.connect(add_item)
    bt_toggle.clicked.connect(toggle_selected)
    bt_close.clicked.connect(dlg.accept)
    tbl.itemDoubleClicked.connect(rename_item)

    refresh()
    exec_modal(dlg)
