import logging
import sqlite3
from collections.abc import Callable
from pathlib import Path
from shutil import copy2

from PyQt5.QtWidgets import QMessageBox
from utils.paths import get_project_root

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
        service.update_from_excel()
        load_record(cur_index)
        QMessageBox.information(parent, "Atualizar Dados", "Atualização concluída.")
    except Exception as exc:  # pragma: no cover - UI feedback only
        logger.exception("Update failed", exc_info=exc)
        QMessageBox.critical(parent, "Atualizar Dados", f"Falha na atualização: {exc}")


def backup_db(parent, ds):
    """Create a ``.bak`` copy of the current database."""

    conn = getattr(ds, "conn", None)
    if conn is None:
        QMessageBox.warning(parent, "Segurança", "Base de dados indisponível.")
        return
    try:
        db_file = Path(conn.execute("PRAGMA database_list").fetchone()[2])
        backup = db_file.with_suffix(db_file.suffix + ".bak")
        copy2(db_file, backup)
        QMessageBox.information(parent, "Segurança", f"Cópia criada: {backup.name}.")
    except Exception as exc:  # pragma: no cover - UI feedback only
        logger.exception("Backup failed", exc_info=exc)
        QMessageBox.critical(parent, "Segurança", f"Falha na cópia: {exc}")


def restore_db(parent, ds):
    """Restore the database from its ``.bak`` copy."""

    conn = getattr(ds, "conn", None)
    if conn is None:
        QMessageBox.warning(parent, "Reposição", "Base de dados indisponível.")
        return
    try:
        db_file = Path(conn.execute("PRAGMA database_list").fetchone()[2])
        backup = db_file.with_suffix(db_file.suffix + ".bak")
        if not backup.exists():
            QMessageBox.warning(
                parent, "Reposição", f"Backup não encontrado: {backup.name}"
            )
            return
        conn.close()
        copy2(backup, db_file)
        ds.conn = sqlite3.connect(str(db_file))
        ds.conn.row_factory = sqlite3.Row
        QMessageBox.information(parent, "Reposição", "Reposição concluída.")
    except Exception as exc:  # pragma: no cover - UI feedback only
        logger.exception("Restore failed", exc_info=exc)
        QMessageBox.critical(parent, "Reposição", f"Falha na reposição: {exc}")


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
        Mapping providing callables for ``list``, ``add``, ``set_active`` and
        ``update``.
    on_change
        Optional callback invoked whenever the table content changes.

    The ``repo_methods`` mapping must provide callables for ``list``, ``add``,
    ``set_active`` and ``update`` which correspond to admin methods from
    :class:`data.repositories.AuxiliaresRepo`.
    """

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QInputDialog,
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
    tbl.setHorizontalHeaderLabels(["Código", "Descrição"])
    tbl.horizontalHeader().setStretchLastSection(True)
    tbl.setStyleSheet("QTableWidget::item:hover { background: #00008b; color: #fff; }")
    vbox.addWidget(tbl)

    hbox = QHBoxLayout()
    vbox.addLayout(hbox)
    bt_add = QPushButton("Adicionar")
    hbox.addWidget(bt_add)
    bt_toggle = QPushButton("Inactivar/Activar")
    bt_toggle.setToolTip("Inactivar ou activar o registo selecionado")
    bt_toggle.setIcon(dlg.style().standardIcon(QStyle.SP_BrowserReload))
    hbox.addWidget(bt_toggle)
    bt_close = QPushButton("Fechar")
    hbox.addWidget(bt_close)

    def refresh():
        tbl.setRowCount(0)
        for cod, desc, ativo in repo_methods["list"]():
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
        cod, ativo = cod_item.data(Qt.UserRole)
        new_state = 0 if ativo else 1
        if repo_methods["set_active"](cod, new_state):
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
    dlg.exec_()
