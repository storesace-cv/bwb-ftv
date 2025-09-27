import logging
import sqlite3
from collections.abc import Callable
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHeaderView,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
)
from ui.utilities import DEFAULT_TOOLTIP_DURATION_MS
from utils.paths import get_project_root
from utils.formatting import format_pt_number
from data import create_backup, restore_backup
from services.products import IMPORT_FILE_BASENAMES
from .qt_compat import exec_modal
from .reportbro_stub import discover_reportbro_templates
from . import printing_models

logger = logging.getLogger(__name__)


def missing_import_files() -> list[str]:
    base = get_project_root() / "imports"
    files = [base / name for name in IMPORT_FILE_BASENAMES.values()]
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


class ActiveModelsDialog(QDialog):
    """Manage active ReportBro templates for each supported document."""

    _MODEL_IDENTIFIERS: list[tuple[str, str]] = [
        ("FT's Gestão (filtro)", "ft_gestao_filtro"),
        ("FT's Gestão (Actual)", "ft_gestao_actual"),
        ("FT's Operacionais (filtro)", "ft_operacionais_filtro"),
        ("FT's Operacionais (Actual)", "ft_operacionais_actual"),
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Modelos Activos")
        self._initialising = True
        self._combo_boxes: dict[str, QComboBox] = {}

        main_layout = QVBoxLayout(self)

        self._table = QTableWidget(len(self._MODEL_IDENTIFIERS), 2, self)
        self._table.setFrameShape(QFrame.NoFrame)
        self._table.setHorizontalHeaderLabels(["Relatório", "Template"])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        main_layout.addWidget(self._table)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate_rows()
        self._initialising = False

    @property
    def combo_boxes(self) -> dict[str, QComboBox]:
        """Return a copy of the combo box mapping for tests."""

        return dict(self._combo_boxes)

    def _populate_rows(self) -> None:
        templates = [path.resolve() for path in discover_reportbro_templates()]
        saved_models = printing_models.load_active_models()

        for row, (label, identifier) in enumerate(self._MODEL_IDENTIFIERS):
            item = QTableWidgetItem(label)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(row, 0, item)

            combo = QComboBox(self)
            combo.addItem("— Seleccionar —", "")

            for template_path in templates:
                friendly_name = self._format_template_label(template_path)
                combo.addItem(friendly_name, str(template_path))
                index = combo.count() - 1
                combo.setItemData(index, str(template_path), Qt.ToolTipRole)

            saved_template = saved_models.get(identifier, {}).get("template", "")
            saved_template = saved_template or ""
            if saved_template and saved_template not in {
                combo.itemData(i) for i in range(combo.count())
            }:
                missing_label = self._format_missing_template_label(Path(saved_template))
                combo.addItem(missing_label, saved_template)
                index = combo.count() - 1
                combo.setItemData(index, saved_template, Qt.ToolTipRole)

            combo.currentIndexChanged.connect(
                lambda _idx, ident=identifier: self._on_combo_changed(ident)
            )

            if saved_template:
                combo.blockSignals(True)
                index = combo.findData(saved_template)
                if index >= 0:
                    combo.setCurrentIndex(index)
                combo.blockSignals(False)

            self._combo_boxes[identifier] = combo
            self._table.setCellWidget(row, 1, combo)

    def _format_template_label(self, template_path: Path) -> str:
        friendly = template_path.stem.replace("_", " ").strip()
        friendly = friendly.title()
        friendly = friendly.replace("Ft", "FT")
        return friendly or template_path.name

    def _format_missing_template_label(self, template_path: Path) -> str:
        try:
            relative = template_path.resolve().relative_to(printing_models.PROJECT_ROOT)
            display_path = str(relative)
        except ValueError:
            display_path = str(template_path)
        return f"[Indisponível] {display_path}"

    def _on_combo_changed(self, identifier: str) -> None:
        if self._initialising:
            return
        self._persist_selection(identifier)

    def _persist_selection(self, identifier: str) -> None:
        combo = self._combo_boxes.get(identifier)
        if combo is None:
            return

        data = combo.currentData()
        if not data:
            folder = template = None
        else:
            template_path = Path(str(data))
            folder = template_path.parent
            template = template_path

        try:
            printing_models.save_active_model(identifier, folder, template)
        except Exception as exc:  # pragma: no cover - defensive UI feedback
            logger.exception(
                "[ReportBro] Falha ao guardar modelo activo '%s'", identifier
            )
            QMessageBox.critical(
                self,
                "Modelos Activos",
                "Não foi possível guardar o modelo selecionado."
                " Verifique as permissões da pasta e tente novamente."
                f"\nErro: {exc}",
            )

    def accept(self) -> None:  # pragma: no cover - requires UI interaction
        for identifier in self._combo_boxes:
            self._persist_selection(identifier)
        super().accept()


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


def manage_localizacao_table(parent, repo, on_change: Callable | None = None) -> None:
    """Display and edit localisation/currency entries."""

    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QBrush
    from PyQt5.QtWidgets import (
        QAbstractItemView,
        QDialog,
        QFormLayout,
        QHBoxLayout,
        QLineEdit,
        QPushButton,
        QStyle,
        QVBoxLayout,
    )

    dlg = QDialog(parent)
    dlg.setWindowTitle("Localização e Moeda")
    layout = QVBoxLayout(dlg)

    table = QTableWidget(0, 6, dlg)
    table.setFrameShape(QFrame.NoFrame)
    table.setShowGrid(False)
    table.setHorizontalHeaderLabels(
        ["País", "Código", "Moeda", "Símbolo", "Formato", "Ativo"]
    )
    table.verticalHeader().setVisible(False)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setStyleSheet(
        """
        QTableWidget { border: none; }
        QTableWidget::item { margin: 0; padding: 0; border: none; }
        QTableWidget::item:hover { background: #00008b; color: #fff; }
        QHeaderView::section { border: none; }
        """
    )
    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(4, QHeaderView.Stretch)
    header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
    layout.addWidget(table)

    button_row = QHBoxLayout()
    layout.addLayout(button_row)

    add_btn = QPushButton("Adicionar", dlg)
    edit_btn = QPushButton("Editar", dlg)
    active_btn = QPushButton("Definir como ativo", dlg)
    active_btn.setIcon(dlg.style().standardIcon(QStyle.SP_DialogApplyButton))
    close_btn = QPushButton("Fechar", dlg)

    button_row.addWidget(add_btn)
    button_row.addWidget(edit_btn)
    button_row.addWidget(active_btn)
    button_row.addStretch(1)
    button_row.addWidget(close_btn)

    entries: list[tuple[int, str, str, str, str, str, int]] = []

    default_background = QBrush(dlg.palette().base())
    default_foreground = QBrush(dlg.palette().text())
    active_background = QBrush(dlg.palette().highlight())
    active_foreground = QBrush(dlg.palette().highlightedText())

    def code_exists(code: str, ignore_id: int | None = None) -> bool:
        code_upper = code.strip().upper()
        for entry in entries:
            if entry[2].strip().upper() == code_upper and entry[0] != ignore_id:
                return True
        return False

    def get_selected_id() -> int | None:
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        return int(value) if value is not None else None

    def is_active_id(localizacao_id: int | None) -> bool:
        if localizacao_id is None:
            return False
        for entry in entries:
            if entry[0] == localizacao_id:
                return bool(entry[6])
        return False

    def update_buttons() -> None:
        selected_id = get_selected_id()
        has_selection = selected_id is not None
        edit_btn.setEnabled(has_selection)
        active_btn.setEnabled(has_selection and not is_active_id(selected_id))

    def refresh(select_id: int | None = None) -> None:
        nonlocal entries

        current_id = select_id if select_id is not None else get_selected_id()
        table.blockSignals(True)
        table.setRowCount(0)
        entries = repo.list_localizacao_admin() or []

        for entry in entries:
            (
                entry_id,
                country,
                code,
                currency,
                symbol,
                fmt,
                active,
            ) = entry
            row = table.rowCount()
            table.insertRow(row)
            values = [
                country or "",
                code or "",
                currency or "",
                symbol or "",
                fmt or "",
                "Sim" if active else "Não",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setData(Qt.UserRole, entry_id)
                if active:
                    item.setBackground(active_background)
                    item.setForeground(active_foreground)
                else:
                    item.setBackground(default_background)
                    item.setForeground(default_foreground)
                table.setItem(row, column, item)

        table.blockSignals(False)

        target_id = current_id
        if target_id is None:
            for entry in entries:
                if entry[6]:
                    target_id = entry[0]
                    break

        if target_id is not None:
            for row in range(table.rowCount()):
                item = table.item(row, 0)
                if item and item.data(Qt.UserRole) == target_id:
                    table.selectRow(row)
                    break
        else:
            table.clearSelection()

        update_buttons()
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        dlg.adjustSize()

    def show_form(entry: tuple[int, str, str, str, str, str, int] | None = None) -> int | None:
        editing = entry is not None
        form = QDialog(dlg)
        form.setWindowTitle("Editar registo" if editing else "Adicionar registo")
        form_layout = QVBoxLayout(form)
        fields_layout = QFormLayout()
        form_layout.addLayout(fields_layout)

        country_edit = QLineEdit(form)
        code_edit = QLineEdit(form)
        currency_edit = QLineEdit(form)
        symbol_edit = QLineEdit(form)
        format_edit = QLineEdit(form)

        fields_layout.addRow("País:", country_edit)
        fields_layout.addRow("Código:", code_edit)
        fields_layout.addRow("Moeda:", currency_edit)
        fields_layout.addRow("Símbolo:", symbol_edit)
        fields_layout.addRow("Formato:", format_edit)

        if editing:
            (
                entry_id,
                country,
                code,
                currency,
                symbol,
                fmt,
                _active,
            ) = entry
            country_edit.setText(country or "")
            code_edit.setText(code or "")
            currency_edit.setText(currency or "")
            symbol_edit.setText(symbol or "")
            format_edit.setText(fmt or "")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, form)
        form_layout.addWidget(buttons)

        result_holder: dict[str, int | None] = {"id": None}

        def accept_form() -> None:
            if editing:
                target_id = entry_id
            else:
                target_id = None

            values = {
                "country": country_edit.text().strip(),
                "code": code_edit.text().strip(),
                "currency": currency_edit.text().strip(),
                "symbol": symbol_edit.text().strip(),
                "fmt": format_edit.text().strip(),
            }

            if not all(values.values()):
                QMessageBox.warning(
                    form,
                    "Localização e Moeda",
                    "Todos os campos são obrigatórios.",
                )
                return

            if code_exists(values["code"], ignore_id=target_id):
                QMessageBox.warning(
                    form,
                    "Localização e Moeda",
                    "Já existe um registo com o mesmo código.",
                )
                return

            if editing:
                success = repo.update_localizacao(
                    entry_id,
                    country=values["country"],
                    code=values["code"],
                    currency=values["currency"],
                    symbol=values["symbol"],
                    fmt=values["fmt"],
                )
                if not success:
                    QMessageBox.warning(
                        form,
                        "Localização e Moeda",
                        "Não foi possível atualizar o registo.",
                    )
                    return
                result_holder["id"] = entry_id
            else:
                new_id = repo.add_localizacao(
                    values["country"],
                    values["code"],
                    values["currency"],
                    values["symbol"],
                    values["fmt"],
                )
                if not new_id:
                    QMessageBox.warning(
                        form,
                        "Localização e Moeda",
                        "Não foi possível adicionar o registo.",
                    )
                    return
                result_holder["id"] = int(new_id)

            form.accept()

        buttons.accepted.connect(accept_form)
        buttons.rejected.connect(form.reject)

        result = exec_modal(form)
        if result == QDialog.Accepted:
            return result_holder["id"]
        return None

    def add_entry() -> None:
        new_id = show_form()
        if new_id is None:
            return
        refresh(select_id=new_id)
        if callable(on_change):
            on_change()

    def edit_selected() -> None:
        selected_id = get_selected_id()
        if selected_id is None:
            return
        for entry in entries:
            if entry[0] == selected_id:
                updated_id = show_form(entry)
                break
        else:
            return
        if updated_id is None:
            return
        refresh(select_id=updated_id)
        if callable(on_change):
            on_change()

    def set_active() -> None:
        selected_id = get_selected_id()
        if selected_id is None:
            return
        if repo.set_localizacao_ativo(selected_id):
            refresh(select_id=selected_id)
            if callable(on_change):
                on_change()
        else:
            QMessageBox.warning(
                dlg,
                "Localização e Moeda",
                "Não foi possível definir o registo como ativo.",
            )

    add_btn.clicked.connect(add_entry)
    edit_btn.clicked.connect(edit_selected)
    active_btn.clicked.connect(set_active)
    close_btn.clicked.connect(dlg.accept)
    table.itemDoubleClicked.connect(lambda _item: edit_selected())
    table.itemSelectionChanged.connect(update_buttons)

    refresh()
    exec_modal(dlg)
