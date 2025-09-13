import logging
from collections.abc import Callable

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
        Mapping providing callables for ``list``, ``add`` and ``set_active``.
    on_change
        Optional callback invoked whenever the table content changes.

    The ``repo_methods`` mapping must provide callables for ``list``, ``add``
    and ``set_active`` which correspond to admin methods from
    :class:`data.repositories.AuxiliaresRepo`.
    """

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QInputDialog,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QVBoxLayout,
    )

    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    vbox = QVBoxLayout(dlg)
    lst = QListWidget()
    vbox.addWidget(lst)

    hbox = QHBoxLayout()
    vbox.addLayout(hbox)
    bt_add = QPushButton("Adicionar")
    hbox.addWidget(bt_add)
    bt_close = QPushButton("Fechar")
    hbox.addWidget(bt_close)

    def refresh():
        lst.clear()
        for cod, desc, ativo in repo_methods["list"]():
            item = QListWidgetItem(f"{cod} - {desc}")
            item.setData(Qt.UserRole, (cod, ativo))
            if not ativo:
                item.setForeground(Qt.gray)
            lst.addItem(item)

    def add_item():
        text, ok = QInputDialog.getText(dlg, "Adicionar", "Descrição:")
        if ok and text.strip():
            repo_methods["add"](text.strip())
            refresh()
            if callable(on_change):
                on_change()

    def toggle(item: QListWidgetItem):
        cod, ativo = item.data(Qt.UserRole)
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

    bt_add.clicked.connect(add_item)
    bt_close.clicked.connect(dlg.accept)
    lst.itemDoubleClicked.connect(toggle)

    refresh()
    dlg.exec_()
