# Fichas Técnicas Valorizadas — UI (Single-file)
#
# Regras Aprovadas (manter sempre no topo e cumprir em TODO o código)
# -------------------------------------------------------------------
# 1) Nomenclatura de Blocos e Células
#    - Blocos: [B1] Dados Gerais, [B2] Ingredientes,
#      [B3] Custos, [B4] Preparação, [B5] Nutrição / Alergénios.
#    - Célula raiz do bloco: Bn.C1 (ex.: B1.C1, B2.C1, B3.C1, B4.C1, B5.C1).
#    - Divisão horizontal: sufixos .A (esq.) e .B (dir.).
#    - Divisão vertical: sufixos .1 (topo) e .2 (base).
#    - Subdivisões encadeiam-se mantendo a regra (ex.: B1.C1.A.2.B).
#    - NÃO usar nomes ad hoc (ex.: C1.X, C1AA, C1AB).
#
# 2) Changelog: toda alteração documentada deve incluir data/hora
#    (Europe/Lisbon)
#    - Formato: YYYY-MM-DD HH:MM — descrição.
#
# Changelog
# ---------
# 2025-09-08 16:06 — v3.64 — Alinhamento de nomenclatura em B3 (C1)
#    & reforço de comentários; split vertical em C1.A.2 com dados no topo;
#    Custo Total = soma da coluna "Total".
# 2025-09-08 17:35 — v3.73 — Restabelecido: botão Overlay no topo
#    esquerdo; navegação no rodapé; scroll vertical; mantidas alterações
#    pedidas (C1 swap, remoção C1.A.2.B.2, tags visíveis).
# 2025-09-08 18:05 — v3.80 — Reintroduzidos [B4] Preparação e [B5]
#    Alergénios; overlays/cores preservados; footer com contador.
# 2025-09-08 18:40 — v3.82 — C1.A.2.B ligado à BD
#    (tipos/validade/temperaturas) com pré-seleção por FK; preservado
#    layout.
# 2025-09-08 19:05 — v3.84 — Menu → Tabelas abre diálogos de gestão
#    (listar ativos, adicionar, inativar) para Tipos/Validade/
#    Temperaturas.
# 2025-09-08 19:30 — v3.87 — Consolidação parcial das alterações sem
#    tocar no layout base.
# 2025-09-08 19:45 — v3.88 — CONSOLIDAÇÃO FINAL:
#    • C1.A.2.A dividido (topo: Família/Sub-família; base: PVP1..PVP5 com
#      etiqueta por cima e valor por baixo; leitura PVP1..2 de
#      precos_taxas).
#    • C1.A.2.B: combos ligados às tabelas auxiliares (ativo=1,
#      ordenadas) com pré-seleção por FK do produto.
#    • B2: grelha 50/10/10/14/16 + Código oculto; cálculo Total por linha
#      quando necessário.
#    • B3: C1.A.A = Custo Total (soma da coluna “Total”); C1.A.B =
#      “Food Cost:” (placeholder).
#    • B4: editor de Preparação com toolbar simples; B5: Alergénios 2×N
#      com persistência N–N.
#    • Menu: QToolButton (InstantPopup) sem caret; Base de Dados /
#      Tabelas / Utilitários; diálogos de gestão nas Tabelas.
#    • Overlays/cores preservados; navegação centrada no rodapé; scroll
#      vertical; cabeçalho em comentários.
# 2025-09-13 17:16 — v3.89 — Raiz dos blocos B2–B5 renomeada para ".C1".
# 2025-09-13 23:08 — v3.90 — Menu Segurança com ações de cópia e reposição.

import sys
import logging
import html as html_module
import html.parser as html_parser
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtGui import QFont, QKeySequence, QTextOption
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableView,
    QMessageBox,
    QScrollArea,
    QShortcut,
    QTextEdit,
    QCheckBox,
    QToolBar,
    QAction,
)
from data.datastore import DataStore
from services.products import ProductService
from domain import FichaTecnica
from utils.formatting import format_pt_number

from . import layout
from .layout import Zone
from .utilities import make_readonly_lineedit, match_font, stack_combo
from .dialogs import (
    import_data,
    manage_aux_table,
    update_data,
    backup_database,
    restore_database,
)

APP_TITLE = "Fichas Técnicas Valorizadas"

logger = logging.getLogger(__name__)

# ------------------------ Main App ------------------------


class FichasTecnicasModel(QAbstractTableModel):
    """Table model for displaying ``FichasTecnicas`` records."""

    headers = ["ComponenteNome", "QTD", "U.M.", "PPU", "Total"]

    def __init__(self, rows: list[FichaTecnica] | None = None):
        super().__init__()
        self._rows: list[FichaTecnica] = rows or []

    def rowCount(self, parent=None):  # pragma: no cover - trivial
        return len(self._rows)

    def columnCount(self, parent=None):  # pragma: no cover - trivial
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        ficha = self._rows[index.row()]
        if role == Qt.DisplayRole:
            mapping = [
                ficha.ingredient,
                format_pt_number(ficha.quantity),
                ficha.unit,
                format_pt_number(ficha.ppu),
                format_pt_number(ficha.total),
            ]
            val = mapping[index.column()]
            return val if val is not None else ""
        return None

    def setData(self, index, value, role=Qt.EditRole):  # pragma: no cover - GUI
        if not index.isValid() or role != Qt.EditRole:
            return False
        ficha = self._rows[index.row()]
        col = index.column()
        try:
            if col == 1:
                ficha.quantity = float(value)
            elif col == 3:
                ficha.ppu = float(value)
            elif col == 4:
                ficha.total = float(value)
            else:
                return False
        except (TypeError, ValueError):
            return False
        self.dataChanged.emit(index, index, [Qt.DisplayRole])
        return True

    def flags(self, index):  # pragma: no cover - trivial
        if not index.isValid():
            return Qt.NoItemFlags
        base = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() in (1, 3, 4):
            return base | Qt.ItemIsEditable
        return base

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # pragma: no cover
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def update_data(self, rows: list[FichaTecnica]):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()


class FTApp(QWidget):
    def __init__(self, service: ProductService):
        super().__init__()
        self.service = service
        self.ds = service.ds
        self.cur_index = 0
        self.current_product = None
        self._prep_dirty = False
        self._build_ui()
        self._connect_nav()
        self._load_record(self.cur_index)

    def _section_box(self, title: str, zone: Zone) -> QGroupBox:
        box = QGroupBox(title)
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        ly = QVBoxLayout(box)
        ly.setContentsMargins(8, 8, 8, 8)
        ly.setSpacing(8)
        ly.addWidget(zone)
        return box

    def _build_ui(self):
        self.setWindowTitle(APP_TITLE)
        self.resize(1180, 860)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # --- Top bar: Overlay (esq) + Menu (dir) ---
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        self.btOverlay = QPushButton("Overlays: ON")
        self.btOverlay.clicked.connect(self._toggle_overlays_btn)
        top.addWidget(self.btOverlay, 0, Qt.AlignLeft)
        self.btSave = QPushButton("Guardar")
        self.btSave.clicked.connect(lambda: self._save_prep(force=True))
        top.addWidget(self.btSave, 0, Qt.AlignLeft)
        top.addStretch(1)
        from PyQt5.QtWidgets import QMenu, QToolButton

        self.btMenu = QToolButton()
        self.btMenu.setText("Menu")
        self.btMenu.setPopupMode(QToolButton.InstantPopup)
        self.mnuRoot = QMenu(self)
        mBD = QMenu("Base de Dados", self.mnuRoot)
        actUpdate = QAction("Atualizar Dados", self)
        actReload = QAction("Importar Dados", self)
        mBD.addAction(actUpdate)
        mBD.addAction(actReload)
        mSeg = QMenu("Segurança", mBD)
        actBackup = QAction("Segurança", self)
        actRestore = QAction("Reposição", self)
        mSeg.addAction(actBackup)
        mSeg.addAction(actRestore)
        mBD.addMenu(mSeg)
        self.mnuRoot.addMenu(mBD)
        mTab = QMenu("Tabelas", self.mnuRoot)
        actTipos = QAction("Tipos Artigos", self)
        actVal = QAction("Validade", self)
        actTemps = QAction("Temperaturas", self)
        mTab.addAction(actTipos)
        mTab.addAction(actVal)
        mTab.addAction(actTemps)
        self.mnuRoot.addMenu(mTab)
        mUtil = QMenu("Utilitários", self.mnuRoot)
        actTheme = QAction("Tema", self)
        mUtil.addAction(actTheme)
        self.mnuRoot.addMenu(mUtil)
        self.btMenu.setMenu(self.mnuRoot)
        # ligações básicas
        actReload.triggered.connect(
            lambda: import_data(self, self.service, self._load_record, self.cur_index)
        )
        actUpdate.triggered.connect(
            lambda: update_data(self, self.service, self._load_record, self.cur_index)
        )
        actBackup.triggered.connect(lambda: backup_database(self, self.ds))
        actRestore.triggered.connect(
            lambda: restore_database(self, self.ds, self._after_restore)
        )
        actTipos.triggered.connect(
            lambda: manage_aux_table(
                self,
                "Tipos de Artigos",
                {
                    "list": self.ds.aux.list_tipos_artigos_admin,
                    "add": self.ds.aux.add_tipo_artigo,
                    "set_active": self.ds.aux.set_tipo_artigo_ativo,
                    "update": self.ds.aux.update_tipo_artigo,
                },
                on_change=self._aux_refresh_lists,
            )
        )
        actVal.triggered.connect(
            lambda: manage_aux_table(
                self,
                "Validade",
                {
                    "list": self.ds.aux.list_validade_admin,
                    "add": self.ds.aux.add_validade,
                    "set_active": self.ds.aux.set_validade_ativo,
                    "update": self.ds.aux.update_validade,
                },
                on_change=self._aux_refresh_lists,
            )
        )
        actTemps.triggered.connect(
            lambda: manage_aux_table(
                self,
                "Temperaturas",
                {
                    "list": self.ds.aux.list_temperaturas_admin,
                    "add": self.ds.aux.add_temperatura,
                    "set_active": self.ds.aux.set_temperatura_ativo,
                    "update": self.ds.aux.update_temperatura,
                },
                on_change=self._aux_refresh_lists,
            )
        )
        actTheme.triggered.connect(
            lambda: QMessageBox.information(
                self, "Tema", "Alternância de tema pendente."
            )
        )
        top.addWidget(self.btMenu, 0, Qt.AlignRight)
        root.addLayout(top)

        # --- Conteúdo com scroll vertical ---
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        page = QWidget()
        page_ly = QVBoxLayout(page)
        page_ly.setContentsMargins(0, 0, 0, 0)
        page_ly.setSpacing(8)
        scroll.setWidget(page)
        page.setMinimumWidth(1100)
        root.addWidget(scroll, 1)

        # ---------------- B1 — Dados Gerais (B1.C1) ----------------
        self.C1 = Zone(
            "B1.C1",
            self,
            flow="v",
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
            spacing=2,
        )
        page_ly.addWidget(self._section_box("[B1] - Dados Gerais", self.C1), 0)

        C1A, C1B = self.C1.split_h((3, 1))
        C1A1, C1A2 = C1A.split_v((1, 3))

        lbl_w = 110
        self.edCodigo = QLineEdit()
        make_readonly_lineedit(self.edCodigo, False)
        self.edNome = QLineEdit()
        make_readonly_lineedit(self.edNome, True)
        C1A1.add_row("Código:", self.edCodigo, label_minw=lbl_w, vspacing=0)
        C1A1.add_row("Nome do Artigo:", self.edNome, label_minw=lbl_w, vspacing=1)

        # B1.C1.A.2
        C1A21, C1A22 = C1A2.split_h(
            (3, 1)
        )  # B1.C1.A.2.A (famílias/PVPs) + B1.C1.A.2.B (combos)
        # B1.C1.A.2.A → divide verticalmente: topo (famílias) + base (PVP1..PVP5)
        C1A21_top, C1A21_base = C1A21.split_v((1, 2))
        C1A21_top.apply_overlays(True)
        self.lbFamiliaVal = QLabel("")
        self.lbSubFamiliaVal = QLabel("")
        match_font(self.lbFamiliaVal, self.edNome)
        match_font(self.lbSubFamiliaVal, self.edNome)
        C1A21_top.add_row("Família:", self.lbFamiliaVal, label_minw=lbl_w, vspacing=0)
        C1A21_top.add_row(
            "Sub-família:", self.lbSubFamiliaVal, label_minw=lbl_w, vspacing=0
        )

        # Base: cinco colunas iguais com PVP1..PVP5 (etiqueta por cima)
        P1, P2 = C1A21_base.split_h((1, 1))
        P11, P12 = P1.split_h((1, 1))
        P111, P112 = P11.split_h((1, 1))
        # Agora temos 5 zonas: P111, P112, P12.A, P12.B, (criar quinta)
        # Remove o contêiner original (preserva o _tag_lbl) e recria em 5 colunas iguais
        if C1A21_base.ly.count() > 1:
            old_item = C1A21_base.ly.takeAt(1)
            if old_item is not None:
                old_w = old_item.widget()
                if old_w is not None:
                    old_w.deleteLater()
        # Reconstruir base em 5 colunas iguais
        base_cont = QWidget(C1A21_base)
        base_h = QHBoxLayout(base_cont)
        base_h.setContentsMargins(0, 0, 0, 0)
        base_h.setSpacing(C1A21_base.ly.spacing())
        C1A21_base.ly.insertWidget(1, base_cont, 1)
        self.lbPVP = []
        for i in range(5):
            col = Zone(
                f"{C1A21_base.tag}.{i+1}",
                base_cont,
                flow="v",
                margins=2,
                spacing=2,
                level=C1A21_base._level + 1,
                show_overlays=layout.DEV_OVERLAYS,
            )
            lbl = QLabel(f"PVP{i+1}")
            val = QLabel("—")
            val.setStyleSheet("border:none; background:transparent; font-weight:600;")
            col.add(lbl, 0)
            col.add(val, 0)
            self.lbPVP.append(val)
            base_h.addWidget(col, 1)

        # Combos diretamente em B1.C1.A.2.B (sem .B.2)
        w_tipos, self.cbTipos = stack_combo("Tipos Artigos")
        w_val, self.cbValidade = stack_combo("Validade")
        w_temp, self.cbTemp = stack_combo("Temperaturas")
        C1A22_1, C1A22_2, C1A22_3 = C1A22.split_v((1, 1, 1))
        C1A22_1.add(w_tipos)
        C1A22_2.add(w_val)
        C1A22_3.add(w_temp)
        self.cbTipos.currentIndexChanged.connect(self._on_tipo_artigo_changed)
        self.cbValidade.currentIndexChanged.connect(self._on_validade_changed)
        self.cbTemp.currentIndexChanged.connect(self._on_temperatura_changed)

        # B1.C1.B — placeholder de preview
        prev = QLabel("Pré-visualização")
        prev.setAlignment(Qt.AlignCenter)
        prev.setStyleSheet("border:1px solid #ccc; padding:8px;")
        C1B.add(prev, 1)

        # ---------------- B2 — Ingredientes (B2.C1) ----------------
        self.C2 = Zone(
            "B2.C1", self, flow="v", level=0, show_overlays=layout.DEV_OVERLAYS
        )
        page_ly.addWidget(self._section_box("[B2] - Ingredientes", self.C2), 0)

        self.ingModel = FichasTecnicasModel([])

        self.tbIng = QTableView(self)
        self.tbIng.setModel(self.ingModel)
        self.tbIng.verticalHeader().setVisible(False)
        self.tbIng.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tbIng.setEditTriggers(QTableView.DoubleClicked | QTableView.EditKeyPressed)
        self.C2.add(self.tbIng, 1)
        self._setup_ing_columns()

        # ---------------- B3 — Custos (B3.C1) ----------------
        self.C3 = Zone(
            "B3.C1", self, flow="v", level=0, show_overlays=layout.DEV_OVERLAYS
        )
        page_ly.addWidget(self._section_box("[B3] - Custos", self.C3), 0)

        C3A = Zone(
            "B3.C1.A",
            self.C3,
            flow="v",
            level=1,
            show_overlays=layout.DEV_OVERLAYS,
        )
        self.C3.add(C3A, 1)
        C3AA, C3AB = C3A.split_h((1, 1))

        # C1 swap aplicado: C1.A.A = Custo Total | C1.A.B = "Food Cost:"
        ct_row = QWidget()
        ct_ly = QVBoxLayout(ct_row)
        ct_ly.setContentsMargins(0, 0, 0, 0)
        ct_ly.setSpacing(4)
        ct_ly.addWidget(QLabel("Custo Total:"))
        self.edCustoTotal = QLineEdit()
        make_readonly_lineedit(self.edCustoTotal, True)
        ct_ly.addWidget(self.edCustoTotal)
        C3AA.add(ct_row, 0)

        C3AB.add(QLabel("Food Cost:"), 0)

        # ---------------- B4 — Preparação (B4.C1) ----------------
        self.C4 = Zone(
            "B4.C1", self, flow="v", level=0, show_overlays=layout.DEV_OVERLAYS
        )
        page_ly.addWidget(self._section_box("[B4] - Preparação", self.C4), 1)

        # Toolbar de formatação
        toolbar = QToolBar()
        bold_act = QAction("B", self)
        bold_act.setShortcut(QKeySequence("Ctrl+B"))
        bold_act.triggered.connect(self._toggle_bold)
        toolbar.addAction(bold_act)

        italic_act = QAction("I", self)
        italic_act.setShortcut(QKeySequence("Ctrl+I"))
        italic_act.triggered.connect(self._toggle_italic)
        toolbar.addAction(italic_act)

        underline_act = QAction("U", self)
        underline_act.setShortcut(QKeySequence("Ctrl+U"))
        underline_act.triggered.connect(self._toggle_underline)
        toolbar.addAction(underline_act)

        toolbar.addSeparator()

        ol_act = QAction("1.", self)
        ol_act.triggered.connect(self._insert_ordered_list)
        toolbar.addAction(ol_act)

        ul_act = QAction("•", self)
        ul_act.triggered.connect(self._insert_unordered_list)
        toolbar.addAction(ul_act)

        clear_act = QAction("Limpar", self)
        clear_act.triggered.connect(self._clear_formatting)
        toolbar.addAction(clear_act)

        self.C4.add(toolbar, 0)

        self.edPrep = QTextEdit()
        self.edPrep.setAcceptRichText(True)
        self.edPrep.setWordWrapMode(QTextOption.WordWrap)
        self.edPrep.setTabChangesFocus(False)
        self.edPrep.setUndoRedoEnabled(True)
        self.edPrep.setLineWrapMode(QTextEdit.WidgetWidth)
        self.edPrep.document().setDefaultStyleSheet("img { max-width:100%; }")
        self.edPrep.setPlaceholderText("— Texto de preparação —")
        self.edPrep.textChanged.connect(self._on_prep_changed)
        self.C4.add(self.edPrep, 1)

        # ---------------- B5 — Nutrição / Alergénios (B5.C1) ----------------
        self.C5 = Zone(
            "B5.C1", self, flow="v", level=0, show_overlays=layout.DEV_OVERLAYS
        )
        page_ly.addWidget(self._section_box("[B5] - Nutrição / Alergénios", self.C5), 0)

        self._build_allergens_grid()

        # --- Rodapé: navegação centrada + contador ---
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(8)
        footer.addStretch(1)
        self.btFirst = QPushButton("◀◀ Primeiro")
        self.btPrev = QPushButton("◀ Anterior")
        self.lbPos = QLabel("1 / 1")
        self.btNext = QPushButton("Seguinte ▶")
        self.btLast = QPushButton("Último ▶▶")
        footer.addWidget(self.btFirst)
        footer.addWidget(self.btPrev)
        footer.addWidget(self.lbPos)
        footer.addWidget(self.btNext)
        footer.addWidget(self.btLast)
        footer.addStretch(1)
        root.addLayout(footer)

        # Atalho teclado para overlays
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self._toggle_overlays)
        QShortcut(
            QKeySequence("Ctrl+S"), self, activated=lambda: self._save_prep(force=True)
        )

    # ---------- Alergénios grid ----------
    def _build_allergens_grid(self):
        names = self.service.list_active_allergens()
        gridw = QWidget()
        grid = QGridLayout(gridw)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        cols = 3
        for i, (aid, nome) in enumerate(names):
            r = i // cols
            c = i % cols
            cb = QCheckBox(nome)
            grid.addWidget(cb, r, c, alignment=Qt.AlignLeft)
        self.C5.add(gridw, 0)

    # ---------- Ingredientes: colunas ----------
    def _setup_ing_columns(self):
        w = max(self.width(), 1100)
        model = self.tbIng.model()
        if not model:
            return
        self.tbIng.setColumnWidth(0, int(w * 0.50))
        self.tbIng.setColumnWidth(1, int(w * 0.10))
        self.tbIng.setColumnWidth(2, int(w * 0.10))
        self.tbIng.setColumnWidth(3, int(w * 0.14))
        self.tbIng.setColumnWidth(4, int(w * 0.16))

    def _apply_ingredient_widths(self):
        self._setup_ing_columns()

    def _apply_ing_autofit_or_scroll(self):
        vh = self.tbIng.verticalHeader()
        hh = self.tbIng.horizontalHeader()
        rows = self.tbIng.model().rowCount()
        row_h = vh.defaultSectionSize()
        max_visible = 8
        visible_rows = min(rows, max_visible)
        total_h = hh.height() + row_h * visible_rows + self.tbIng.frameWidth() * 2
        scroll = self.tbIng.verticalScrollBar()
        if rows <= max_visible:
            self.tbIng.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.hide()
        else:
            self.tbIng.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            scroll.show()
        self.tbIng.setFixedHeight(total_h)

    def _apply_prep_autofit_or_scroll(self):
        doc_h = self.edPrep.document().size().toSize().height()
        margins = self.edPrep.contentsMargins()
        padding = margins.top() + margins.bottom() + self.edPrep.frameWidth() * 2
        h = doc_h + padding
        h = max(160, min(520, h))
        self.edPrep.setMinimumHeight(h)
        self.edPrep.setMaximumHeight(h)
        self.edPrep.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def _on_prep_changed(self):
        self._prep_dirty = True
        self._apply_prep_autofit_or_scroll()

    def _toggle_bold(self):
        weight = QFont.Bold if self.edPrep.fontWeight() != QFont.Bold else QFont.Normal
        self.edPrep.setFontWeight(weight)

    def _toggle_italic(self):
        self.edPrep.setFontItalic(not self.edPrep.fontItalic())

    def _toggle_underline(self):
        self.edPrep.setFontUnderline(not self.edPrep.fontUnderline())

    def _insert_ordered_list(self):
        self.edPrep.insertHtml("<ol><li></li></ol>")

    def _insert_unordered_list(self):
        self.edPrep.insertHtml("<ul><li></li></ul>")

    def _clear_formatting(self):
        text = self.edPrep.toPlainText()
        self.edPrep.setPlainText(text)

    def _sanitize_prep_html(self, html: str) -> str:
        """Sanitize HTML from the preparation editor.

        Only a minimal subset of tags/attributes is allowed. ``<script>``
        elements are completely removed, ``on*`` attributes are stripped and
        style properties are whitelisted. ``<b>`` and ``<i>`` are normalised to
        ``<strong>`` and ``<em>`` respectively.
        """

        allowed_tags = {"p", "br", "strong", "em", "ul", "ol", "li", "span"}
        allowed_attrs: dict[str, set[str]] = {
            "p": {"style"},
            "span": {"style"},
            "li": {"style"},
        }
        allowed_styles = {"text-align"}

        def _sanitize_style(style: str) -> str:
            clean_props: list[str] = []
            for part in style.split(";"):
                if not part.strip():
                    continue
                key, _, value = part.partition(":")
                key = key.strip().lower()
                value = value.strip()
                if key in allowed_styles:
                    val_low = value.lower()
                    if any(x in val_low for x in ["javascript:", "expression", "url("]):
                        continue
                    clean_props.append(f"{key}: {value}")
            return "; ".join(clean_props)

        class _Sanitizer(html_parser.HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=False)
                self.result: list[str] = []
                self.skip_depth = 0

            def handle_starttag(self, tag, attrs):
                tag = tag.lower()
                if tag in {"script", "style"}:
                    self.skip_depth += 1
                    return
                if self.skip_depth:
                    return
                tag = "strong" if tag == "b" else tag
                tag = "em" if tag == "i" else tag
                if tag not in allowed_tags:
                    return
                clean_attrs: list[tuple[str, str]] = []
                for attr, value in attrs:
                    if attr is None:
                        continue
                    attr_l = attr.lower()
                    if attr_l.startswith("on"):
                        continue
                    if attr_l == "style":
                        val = _sanitize_style(value or "")
                        if val:
                            clean_attrs.append((attr_l, val))
                    elif attr_l in allowed_attrs.get(tag, set()):
                        clean_attrs.append(
                            (attr_l, html_module.escape(value or "", quote=True))
                        )
                attr_str = "".join(f' {name}="{val}"' for name, val in clean_attrs)
                self.result.append(f"<{tag}{attr_str}>")

            def handle_endtag(self, tag):
                tag = tag.lower()
                if tag in {"script", "style"}:
                    if self.skip_depth:
                        self.skip_depth -= 1
                    return
                if self.skip_depth:
                    return
                tag = "strong" if tag == "b" else tag
                tag = "em" if tag == "i" else tag
                if tag in allowed_tags:
                    self.result.append(f"</{tag}>")

            def handle_data(self, data):
                if not self.skip_depth:
                    self.result.append(html_module.escape(data))

            def handle_entityref(self, name):
                if not self.skip_depth:
                    self.result.append(f"&{name};")

            def handle_charref(self, name):
                if not self.skip_depth:
                    self.result.append(f"&#{name};")

        try:
            sanitizer = _Sanitizer()
            sanitizer.feed(html)
            sanitizer.close()
            return "".join(sanitizer.result).strip()
        except Exception:
            # In case of an unexpected error return the original html to avoid
            # losing data.
            return html

    def _save_prep(self, force: bool):
        if not force and not self._prep_dirty:
            return
        codigo = getattr(self.current_product, "code", None)
        if not codigo:
            return
        html = self.edPrep.toHtml()
        html = self._sanitize_prep_html(html)
        if html.strip():
            try:
                self.ds.save_preparacao_html(codigo, html)
            except Exception:
                pass
        else:
            try:
                self.ds.save_preparacao_html(codigo, "")
            except Exception:
                pass
        self._prep_dirty = False

    # ---------- Navegação ----------
    def _connect_nav(self):
        self.btFirst.clicked.connect(lambda: self._goto(0))
        self.btPrev.clicked.connect(lambda: self._go(-1))
        self.btNext.clicked.connect(lambda: self._go(+1))
        self.btLast.clicked.connect(lambda: self._goto(self.service.total() - 1))

    def _goto(self, idx):
        if self._prep_dirty:
            self._save_prep(force=False)
        self.cur_index = max(0, min(idx, self.service.total() - 1))
        self._load_record(self.cur_index)

    def _go(self, delta):
        if self._prep_dirty:
            self._save_prep(force=False)
        self.cur_index = (self.cur_index + delta) % max(1, self.service.total())
        self._load_record(self.cur_index)

    # ---------- Carregamento de dados ----------
    def _load_record(self, idx: int):
        self._loading = True
        try:
            codigo = self.service.codigo_at(idx)
            product = self.service.get_product_info(codigo)
            self.current_product = product

            self.edCodigo.setText(product.code or "")
            self.edNome.setText(product.name or "")
            self.lbFamiliaVal.setText(product.familia or "")
            self.lbSubFamiliaVal.setText(product.subfamilia or "")

            pvps = product.pvps
            values = [
                pvps.get("pvp1"),
                pvps.get("pvp2"),
                pvps.get("pvp3"),
                pvps.get("pvp4"),
                pvps.get("pvp5"),
            ]
            for i, val in enumerate(values):
                if i < len(self.lbPVP):
                    self.lbPVP[i].setText(format_pt_number(val))

            def _select_by_code(combo, code_value):
                if code_value is None:
                    return
                for i in range(combo.count()):
                    if combo.itemData(i) == code_value:
                        combo.setCurrentIndex(i)
                        return

            fichas_func = getattr(self.service, "list_fichas_tecnicas", None)
            if callable(fichas_func):
                fichas = fichas_func(codigo)
            else:
                fichas = [
                    FichaTecnica(
                        ingredient=ing.name,
                        quantity=ing.quantity,
                        unit=ing.unit,
                        ppu=ing.ppu,
                        total=ing.total,
                        code=ing.code,
                    )
                    for ing in product.ingredients
                ]
            self.ingModel.update_data(fichas)

            self._apply_ingredient_widths()
            self.edCustoTotal.setText(
                format_pt_number(self.service.calculate_cost(product))
            )
            self.lbPos.setText(f"{self.cur_index+1} / {max(1,self.service.total())}")

            try:
                html = self.ds.get_preparacao_html(codigo) or ""
            except Exception:
                html = ""
            self.edPrep.blockSignals(True)
            self.edPrep.setHtml(html)
            self.edPrep.blockSignals(False)
            self._prep_dirty = False
            self._apply_prep_autofit_or_scroll()

            try:
                cbs = (self.cbTipos, self.cbValidade, self.cbTemp)
                self._aux_fetch_lists(cbs)
                _select_by_code(self.cbTipos, product.tipo_artigo_cod)
                _select_by_code(self.cbValidade, product.validade_cod)
                _select_by_code(self.cbTemp, product.temperatura_cod)
            except Exception as e:
                logger.exception("[AuxCanon][ERRO] %s", e)
        finally:
            self._loading = False

    # ---------- Cálculos ----------
    def _update_costs_from_table(self):
        """Recalculate total cost using the service layer."""
        try:
            total = self.service.calculate_cost(self.current_product)
            self.edCustoTotal.setText(format_pt_number(total))
        except Exception:
            pass

    def _on_tipo_artigo_changed(self, idx: int):
        if getattr(self, "_loading", False):
            return
        codigo = getattr(self.current_product, "code", None)
        if not codigo:
            return
        tipo_cod = self.cbTipos.itemData(idx)
        try:
            self.service.set_tipo_artigo(codigo, tipo_cod)
            if self.current_product:
                self.current_product.tipo_artigo_cod = tipo_cod
        except Exception:
            pass

    def _on_validade_changed(self, idx: int):
        if getattr(self, "_loading", False):
            return
        codigo = getattr(self.current_product, "code", None)
        if not codigo:
            return
        validade_cod = self.cbValidade.itemData(idx)
        try:
            self.service.set_validade(codigo, validade_cod)
            if self.current_product:
                self.current_product.validade_cod = validade_cod
        except Exception:
            pass

    def _on_temperatura_changed(self, idx: int):
        if getattr(self, "_loading", False):
            return
        codigo = getattr(self.current_product, "code", None)
        if not codigo:
            return
        temperatura_cod = self.cbTemp.itemData(idx)
        try:
            self.service.set_temperatura(codigo, temperatura_cod)
            if self.current_product:
                self.current_product.temperatura_cod = temperatura_cod
        except Exception:
            pass

    # ---------- Eventos ----------
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._apply_ingredient_widths()
        self._apply_prep_autofit_or_scroll()

    def _toggle_overlays(self):
        layout.DEV_OVERLAYS = not layout.DEV_OVERLAYS
        for z in self.findChildren(Zone):
            if z.tag.count(".") == 1 and layout.validate_tag(z.tag):
                z.apply_overlays(layout.DEV_OVERLAYS)

    def _toggle_overlays_btn(self):
        self._toggle_overlays()
        self.btOverlay.setText(f"Overlays: {'ON' if layout.DEV_OVERLAYS else 'OFF'}")

    def _after_restore(self):
        """Refresh UI state after a database restore."""
        try:
            self._aux_refresh_lists()
        except Exception:
            pass
        try:
            self._load_record(getattr(self, "cur_index", 0))
        except Exception:
            pass

    # ================== AUXILIARES — CANÓNICO (v2) ==================
    def _aux_fetch_lists(self, cbs=None):
        """Fetch auxiliary lists via the service layer and populate combo boxes."""

        lists = {"tipo_artigo": [], "validade": [], "temperatura": []}

        if all(
            hasattr(self.service, m)
            for m in ("list_tipos_artigos", "list_validade", "list_temperaturas")
        ):
            try:
                lists["tipo_artigo"] = self.service.list_tipos_artigos()
            except Exception:
                pass
            try:
                lists["validade"] = self.service.list_validade()
            except Exception:
                pass
            try:
                lists["temperatura"] = self.service.list_temperaturas()
            except Exception:
                pass
        else:
            conn = getattr(self.service, "conn", None)
            if conn:
                cur = conn.cursor()

                def resolve_table(candidates):
                    for table in candidates:
                        try:
                            cur.execute(
                                "SELECT name FROM sqlite_master "
                                "WHERE type='table' AND name=?",
                                (table,),
                            )
                            if cur.fetchone():
                                return table
                        except Exception:
                            pass
                    return None

                def pick_cols(table):
                    try:
                        cur.execute(f"PRAGMA table_info({table})")
                        rows = cur.fetchall()
                    except Exception:
                        return None, None
                    names = [r[1].lower() for r in rows]
                    id_col = None
                    for cand in ("id", "cod", "codigo"):
                        if cand in names:
                            id_col = cand
                            break
                    if id_col is None:
                        for r in rows:
                            if r[5]:
                                id_col = r[1]
                                break
                    name_col = None
                    for cand in ("descricao", "nome", "designacao"):
                        if cand in names:
                            name_col = cand
                            break
                    return id_col, name_col

                def fetch_generic(table_candidates):
                    tbl = resolve_table(table_candidates)
                    if not tbl:
                        return []
                    id_col, name_col = pick_cols(tbl)
                    if not id_col or not name_col:
                        return []
                    sql = (
                        f"SELECT {id_col}, {name_col} FROM {tbl} "
                        f"WHERE COALESCE(ativo,1)=1 ORDER BY {name_col}"
                    )
                    try:
                        cur.execute(sql)
                        rows = cur.fetchall()
                    except Exception:
                        return []
                    result = []
                    for r in rows:
                        try:
                            rid = int(r[0])
                        except Exception:
                            try:
                                rid = int(str(r[0]).strip())
                            except Exception:
                                continue
                        name = str(r[1]).strip()
                        if name:
                            result.append((rid, name))
                    return result

                lists["tipo_artigo"] = fetch_generic(("tipos_artigos",))
                lists["validade"] = fetch_generic(("validade", "validades"))
                lists["temperatura"] = fetch_generic(("temperaturas",))

        try:
            self._aux_populate_cbs(lists, cbs)
        except Exception:
            pass
        return lists

    def _aux_find_cbs(self):
        """Tenta encontrar os 3 comboboxes. Usa objectName e heurística."""
        try:
            from PyQt5.QtWidgets import QComboBox
        except Exception:
            try:
                from PySide6.QtWidgets import QComboBox
            except Exception:
                QComboBox = None

        cb_tipo = getattr(self, "cbTipoArtigo", None)
        cb_val = getattr(self, "cbValidade", None)
        cb_temp = getattr(self, "cbTemp", None)

        if QComboBox is not None:

            def has_any(t, keys):
                s = (t or "").lower()
                return any(k in s for k in keys)

            if not (cb_tipo and cb_val and cb_temp):
                for cb in self.findChildren(QComboBox):
                    name = cb.objectName() or ""
                    if cb_tipo is None and has_any(name, ["tipo", "art"]):
                        cb_tipo = cb
                    elif cb_val is None and has_any(name, ["val", "valid"]):
                        cb_val = cb
                    elif cb_temp is None and has_any(name, ["temp"]):
                        cb_temp = cb
        return cb_tipo, cb_val, cb_temp

    def _aux_populate_cbs(self, lists, cbs=None):
        """Populate the combo boxes with canonical lists.

        Parameters
        ----------
        lists: dict
            Mapping of auxiliary types to ``[(id, name)]`` records.
        cbs: tuple[QComboBox, QComboBox, QComboBox] | None
            Optional comboboxes for ``tipo_artigo``, ``validade`` and
            ``temperatura``. If ``None`` they are resolved via
            ``_aux_find_cbs``.
        """

        if cbs is None:
            cbs = self._aux_find_cbs()
        cb_tipo, cb_val, cb_temp = cbs

        def fill(cb, items):
            if cb is None:
                return
            try:
                cb.blockSignals(True)
            except Exception:
                pass
            try:
                cb.clear()
                cb.addItem("—", None)
                for rid, name in items:
                    cb.addItem(str(name), int(rid))
            finally:
                try:
                    cb.blockSignals(False)
                except Exception:
                    pass

        fill(cb_tipo, lists.get("tipo_artigo", []))
        fill(cb_val, lists.get("validade", []))
        fill(cb_temp, lists.get("temperatura", []))
        return cbs

    def _aux_refresh_lists(self):
        """Recarrega as listas e atualiza os comboboxes auxiliares."""
        self._aux_fetch_lists((self.cbTipos, self.cbValidade, self.cbTemp))

    def _aux_load_selected(self, codigo):
        """Tabela de auxiliares removida."""
        return

    def _aux_ensure_guard(self):
        """Envolve _load_record com guarda self._loading True/False.

        Injeta pipeline dos auxiliares.
        """
        if getattr(self, "_aux_guard_wrapped", False):
            return
        orig = getattr(self, "_load_record", None)
        if not callable(orig):
            logger.warning("[AuxUI][AVISO] _load_record ausente.")
            return

        def wrapped(idx: int):
            self._loading = True
            try:
                cbs = self._aux_find_cbs()
                self._aux_fetch_lists(cbs)
                res = orig(idx)
                try:
                    codigo = self.service.codigo_at(getattr(self, "cur_index", 0))
                except Exception:
                    codigo = None
                if codigo:
                    self._aux_load_selected(codigo)
                return res
            finally:
                self._loading = False

        setattr(self, "_load_record", wrapped)
        self._aux_guard_wrapped = True
        logger.info("[AuxUI] _load_record protegido e pipeline de auxiliares ativado.")

    # ================== /AUXILIARES — CANÓNICO (v2) ==================


# ------------------------ Main ------------------------


def main():
    app = QApplication(sys.argv)
    ds = DataStore()
    svc = ProductService(ds)
    w = FTApp(svc)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
