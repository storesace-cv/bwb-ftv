# -*- coding: utf-8 -*-
"""
ftv.ui.auxiliares_dialogs
-------------------------
Diálogos CRUD simples para:
 - Tipos de Artigos
 - Validade
 - Temperaturas
"""

import traceback

try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QMessageBox, QAbstractItemView, QHeaderView, QLineEdit, QLabel
    )
    from PyQt5.QtCore import Qt
except Exception:
    from PySide2.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QMessageBox, QAbstractItemView, QHeaderView, QLineEdit, QLabel
    )
    from PySide2.QtCore import Qt


class _BaseCrudDialog(QDialog):
    TITLE = "Registos"
    KIND = "generico"  # 'tipos', 'validade', 'temperaturas'

    def __init__(self, ds, parent=None):
        super().__init__(parent)
        self.ds = ds
        self.setWindowTitle(self.TITLE)
        self.setModal(True)
        self.resize(640, 440)

        self.tbl = QTableWidget(self)
        self.tbl.setColumnCount(3)
        self.tbl.setHorizontalHeaderLabels(["Código", "Descrição", "Ativo"])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.btn_add = QPushButton("Adicionar")
        self.btn_edit = QPushButton("Editar")
        self.btn_toggle = QPushButton("Inativar/Ativar")
        self.btn_close = QPushButton("Fechar")

        hl = QHBoxLayout()
        hl.addWidget(self.btn_add)
        hl.addWidget(self.btn_edit)
        hl.addWidget(self.btn_toggle)
        hl.addStretch(1)
        hl.addWidget(self.btn_close)

        lay = QVBoxLayout(self)
        lay.addWidget(self.tbl)
        lay.addLayout(hl)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_toggle.clicked.connect(self._on_toggle)
        self.btn_close.clicked.connect(self.accept)

        self.refresh()

    # --- Métodos que as subclasses devem fornecer ---
    def _repo_list(self):
        """Devolve [(cod, descricao, ativo:int)]"""
        raise NotImplementedError

    def _repo_add(self, descricao: str):
        """Cria, devolve cod (ou None em erro)."""
        raise NotImplementedError

    def _repo_update(self, cod, descricao: str) -> bool:
        raise NotImplementedError

    def _repo_toggle(self, cod, ativo: bool) -> bool:
        raise NotImplementedError

    # --- UI helpers ---
    def refresh(self):
        try:
            dados = self._repo_list() or []
        except Exception as e:
            print(f"[AuxDialog][ERRO] _repo_list({self.KIND}): {e}")
            traceback.print_exc()
            dados = []
        self.tbl.setRowCount(len(dados))
        for r, (cod, desc, ativo) in enumerate(dados):
            self.tbl.setItem(r, 0, QTableWidgetItem(str(cod)))
            self.tbl.setItem(r, 1, QTableWidgetItem("" if desc is None else str(desc)))
            self.tbl.setItem(r, 2, QTableWidgetItem("Sim" if int(ativo or 0) else "Não"))
        if self.tbl.rowCount():
            self.tbl.selectRow(0)

    def _selected_cod(self):
        row = self.tbl.currentRow()
        if row < 0: return None
        it = self.tbl.item(row, 0)
        return it.text() if it else None

    def _selected_desc(self):
        row = self.tbl.currentRow()
        if row < 0: return None
        it = self.tbl.item(row, 1)
        return it.text() if it else None

    def _input_descricao(self, titulo: str, valor_inicial: str = ""):
        dlg = QDialog(self)
        dlg.setWindowTitle(titulo)
        vl = QVBoxLayout(dlg)
        vl.addWidget(QLabel("Descrição:"))
        edit = QLineEdit(valor_inicial, dlg)
        vl.addWidget(edit)
        hl = QHBoxLayout()
        ok = QPushButton("OK", dlg); cancel = QPushButton("Cancelar", dlg)
        hl.addStretch(1); hl.addWidget(ok); hl.addWidget(cancel)
        vl.addLayout(hl)
        ok.clicked.connect(dlg.accept); cancel.clicked.connect(dlg.reject)
        if dlg.exec_() == QDialog.Accepted:
            txt = edit.text().strip()
            return txt if txt else None
        return None

    # --- Ações ---
    def _on_add(self):
        desc = self._input_descricao("Adicionar")
        if desc is None: return
        try:
            cod = self._repo_add(desc)
            if not cod:
                QMessageBox.warning(self, "Aviso", "Não foi possível criar o registo.")
            else:
                print(f"[AuxDialog][OK] criado {self.KIND}: cod={cod}")
        except Exception as e:
            print(f"[AuxDialog][ERRO] add({self.KIND}): {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", f"Falha ao adicionar: {e}")
        self.refresh()

    def _on_edit(self):
        cod = self._selected_cod()
        if cod is None: return
        desc_old = self._selected_desc() or ""
        desc_new = self._input_descricao("Editar", desc_old)
        if desc_new is None or desc_new == desc_old: return
        try:
            ok = self._repo_update(cod, desc_new)
            if not ok:
                QMessageBox.warning(self, "Aviso", "Não foi possível atualizar o registo.")
            else:
                print(f"[AuxDialog][OK] atualizado {self.KIND}: cod={cod}")
        except Exception as e:
            print(f"[AuxDialog][ERRO] update({self.KIND}): {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", f"Falha ao atualizar: {e}")
        self.refresh()

    def _on_toggle(self):
        cod = self._selected_cod()
        if cod is None: return
        row = self.tbl.currentRow()
        ativo_txt = self.tbl.item(row, 2).text().strip().lower() if row >= 0 else "não"
        ativo = (ativo_txt == "sim")
        try:
            ok = self._repo_toggle(cod, not ativo)
            if not ok:
                QMessageBox.warning(self, "Aviso", "Não foi possível alterar o estado.")
            else:
                print(f"[AuxDialog][OK] toggle {self.KIND}: cod={cod} -> ativo={not ativo}")
        except Exception as e:
            print(f"[AuxDialog][ERRO] toggle({self.KIND}): {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", f"Falha ao alterar estado: {e}")
        self.refresh()


class TiposArtigosDialog(_BaseCrudDialog):
    TITLE = "Tipos de Artigos"
    KIND = "tipos"
    def _repo_list(self):
        return self.ds.aux.list_tipos_artigos_admin() if hasattr(self.ds, "aux") else []
    def _repo_add(self, descricao: str):
        return self.ds.aux.add_tipo_artigo(descricao) if hasattr(self.ds, "aux") else None
    def _repo_update(self, cod, descricao: str) -> bool:
        return bool(self.ds.aux.update_tipo_artigo(cod, descricao)) if hasattr(self.ds, "aux") else False
    def _repo_toggle(self, cod, ativo: bool) -> bool:
        return bool(self.ds.aux.set_tipo_artigo_ativo(cod, 1 if ativo else 0)) if hasattr(self.ds, "aux") else False


class ValidadeDialog(_BaseCrudDialog):
    TITLE = "Validade"
    KIND = "validade"
    def _repo_list(self):
        return self.ds.aux.list_validade_admin() if hasattr(self.ds, "aux") else []
    def _repo_add(self, descricao: str):
        return self.ds.aux.add_validade(descricao) if hasattr(self.ds, "aux") else None
    def _repo_update(self, cod, descricao: str) -> bool:
        return bool(self.ds.aux.update_validade(cod, descricao)) if hasattr(self.ds, "aux") else False
    def _repo_toggle(self, cod, ativo: bool) -> bool:
        return bool(self.ds.aux.set_validade_ativo(cod, 1 if ativo else 0)) if hasattr(self.ds, "aux") else False


class TemperaturasDialog(_BaseCrudDialog):
    TITLE = "Temperaturas"
    KIND = "temperaturas"
    def _repo_list(self):
        return self.ds.aux.list_temperaturas_admin() if hasattr(self.ds, "aux") else []
    def _repo_add(self, descricao: str):
        return self.ds.aux.add_temperatura(descricao) if hasattr(self.ds, "aux") else None
    def _repo_update(self, cod, descricao: str) -> bool:
        return bool(self.ds.aux.update_temperatura(cod, descricao)) if hasattr(self.ds, "aux") else False
    def _repo_toggle(self, cod, ativo: bool) -> bool:
        return bool(self.ds.aux.set_temperatura_ativo(cod, 1 if ativo else 0)) if hasattr(self.ds, "aux") else False
