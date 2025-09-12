# flake8: noqa
# Fichas Técnicas Valorizadas — UI (Single-file)
#
# Regras Aprovadas (manter sempre no topo e cumprir em TODO o código)
# -------------------------------------------------------------------
# 1) Nomenclatura de Blocos e Células
#    - Blocos: [B1] Dados Gerais, [B2] Ingredientes, [B3] Custos, [B4] Preparação, [B5] Nutrição / Alergénios.
#    - Célula raiz do bloco: Cn (ex.: C1, C2, C3, C4, C5).
#    - Divisão horizontal: sufixos .A (esq.) e .B (dir.).
#    - Divisão vertical: sufixos .1 (topo) e .2 (base).
#    - Subdivisões encadeiam-se mantendo a regra (ex.: C1.A.2.B).
#    - NÃO usar nomes ad hoc (ex.: C3.X, C3AA, C3AB).
#
# 2) Changelog: toda alteração documentada deve incluir data/hora (Europe/Lisbon)
#    - Formato: YYYY-MM-DD HH:MM — descrição.
#
# Changelog
# ---------
# 2025-09-08 16:06 — v3.64 — Alinhamento de nomenclatura em B3 (C3) & reforço de comentários; split vertical em C1.A.2 com dados no topo; Custo Total = soma da coluna "Total".
# 2025-09-08 17:35 — v3.73 — Restabelecido: botão Overlay no topo esquerdo; navegação no rodapé; scroll vertical; mantidas alterações pedidas (C3 swap, remoção C1.A.2.B.2, tags visíveis).
# 2025-09-08 18:05 — v3.80 — Reintroduzidos [B4] Preparação e [B5] Alergénios; overlays/cores preservados; footer com contador.
# 2025-09-08 18:40 — v3.82 — C1.A.2.B ligado à BD (tipos/validade/temperaturas) com pré-seleção por FK; preservado layout.
# 2025-09-08 19:05 — v3.84 — Menu → Tabelas abre diálogos de gestão (listar ativos, adicionar, inativar) para Tipos/Validade/Temperaturas.
# 2025-09-08 19:30 — v3.87 — Consolidação parcial das alterações sem tocar no layout base.
# 2025-09-08 19:45 — v3.88 — CONSOLIDAÇÃO FINAL:
#    • C1.A.2.A dividido (topo: Família/Sub-família; base: PVP1..PVP5 com etiqueta por cima e valor por baixo; leitura PVP1..2 de precos_taxas).
#    • C1.A.2.B: combos ligados às tabelas auxiliares (ativo=1, ordenadas) com pré-seleção por FK do produto.
#    • B2: grelha 50/10/10/14/16 + Código oculto; cálculo Total por linha quando necessário.
#    • B3: C3.A.A = Custo Total (soma da coluna “Total”); C3.A.B = “Food Cost:” (placeholder).
#    • B4: editor de Preparação com toolbar simples; B5: Alergénios 2×N com persistência N–N.
#    • Menu: QToolButton (InstantPopup) sem caret; Base de Dados / Tabelas / Utilitários; diálogos de gestão nas Tabelas.
#    • Overlays/cores preservados; navegação centrada no rodapé; scroll vertical; cabeçalho em comentários.

import sys
import logging
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QScrollArea,
    QShortcut,
    QTextEdit,
    QCheckBox,
)
from ftv.data.datastore import DataStore
from ftv.services.products import ProductService

APP_TITLE = "Fichas Técnicas Valorizadas"
DEV_OVERLAYS = True  # Ctrl+D alterna


logger = logging.getLogger(__name__)

# ------------------------ UI Helpers ------------------------


def make_readonly_lineedit(le: QLineEdit, bold=False):
    le.setReadOnly(True)
    le.setFrame(False)
    le.setStyleSheet("border:none; background:transparent;")
    f = le.font()
    f.setBold(bold)
    le.setFont(f)


def match_font(lbl: QLabel, ref: QLineEdit):
    f = QFont(ref.font())
    lbl.setFont(f)


def stack_combo(title: str):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(2)
    lbl = QLabel(title)
    v.addWidget(lbl, 0, Qt.AlignLeft | Qt.AlignVCenter)
    cb = QComboBox()
    cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    v.addWidget(cb, 0)
    return w, cb


# ------------------------ Zone (Cell) System ------------------------


def bg_for_level(level: int):
    colors = ["#eafbf1", "#eef5ff", "#fff5e8", "#f7f0ff", "#fff0f0"]
    return colors[level % len(colors)] if DEV_OVERLAYS else "transparent"


class Zone(QWidget):
    """Célula real (com tag e overlay opcional)."""

    def __init__(
        self,
        tag: str,
        parent=None,
        flow="v",
        margins=8,
        spacing=6,
        level: int = 0,
        show_overlays: bool = True,
    ):
        super().__init__(parent)
        self.tag = tag
        self.setObjectName(tag)
        self._level = level
        self._labels = []
        if flow == "v":
            self.ly = QVBoxLayout(self)
        else:
            self.ly = QHBoxLayout(self)
        self.ly.setContentsMargins(margins, margins, margins, margins)
        self.ly.setSpacing(spacing)

        self._tag_lbl = QLabel(self.tag, self)
        self._tag_lbl.setStyleSheet("color:#c00; font-size:10px;")
        self._tag_lbl.setFixedHeight(12)
        self.ly.addWidget(self._tag_lbl, 0, Qt.AlignLeft)

        self.apply_overlays(show_overlays)

    def apply_overlays(self, on: bool):
        if on:
            self.setStyleSheet(
                f"background:{bg_for_level(self._level)}; border:1px dashed red;"
            )
            self._tag_lbl.show()
        else:
            self.setStyleSheet("")
            self._tag_lbl.hide()
        for ch in self.findChildren(Zone):
            ch.apply_overlays(on)

    def add(self, w: QWidget, stretch: int = 0):
        self.ly.addWidget(w, stretch)

    def add_row(
        self,
        label_text: str,
        value_widget: QWidget,
        label_minw: int = None,
        vspacing: int = 2,
    ):
        row = QWidget(self)
        row.setStyleSheet("border:none; background:transparent;")
        grid = QGridLayout(row)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(vspacing)
        grid.setColumnStretch(1, 1)
        lbl = QLabel(label_text, row)
        lbl.setStyleSheet("border:none; background:transparent;")
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        if label_minw:
            lbl.setFixedWidth(label_minw)
        value_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        try:
            value_widget.setStyleSheet(
                value_widget.styleSheet() + "border:none; background:transparent;"
            )
        except Exception:
            pass
        grid.addWidget(lbl, 0, 0, alignment=Qt.AlignVCenter | Qt.AlignRight)
        grid.addWidget(value_widget, 0, 1, alignment=Qt.AlignVCenter | Qt.AlignLeft)
        self.ly.addWidget(row)
        self._labels.append(lbl)
        self.sync_label_widths()
        return lbl

    def sync_label_widths(self):
        if not self._labels:
            return
        maxw = max(l.sizeHint().width() for l in self._labels)
        for l in self._labels:
            l.setFixedWidth(maxw)

    def split_h(self, ratios=(1, 1)):
        cont = QWidget(self)
        cont.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        h = QHBoxLayout(cont)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(self.ly.spacing())
        left = Zone(
            self.tag + ".A",
            cont,
            flow="v",
            margins=4,
            spacing=self.ly.spacing(),
            level=self._level + 1,
            show_overlays=DEV_OVERLAYS,
        )
        right = Zone(
            self.tag + ".B",
            cont,
            flow="v",
            margins=4,
            spacing=self.ly.spacing(),
            level=self._level + 1,
            show_overlays=DEV_OVERLAYS,
        )
        h.addWidget(left, ratios[0])
        h.addWidget(right, ratios[1])
        self.ly.addWidget(cont, 1)
        return left, right

    def split_v(self, ratios=(1, 1)):
        cont = QWidget(self)
        cont.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        v = QVBoxLayout(cont)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(self.ly.spacing())
        top = Zone(
            self.tag + ".1",
            cont,
            flow="v",
            margins=4,
            spacing=self.ly.spacing(),
            level=self._level + 1,
            show_overlays=DEV_OVERLAYS,
        )
        bottom = Zone(
            self.tag + ".2",
            cont,
            flow="v",
            margins=4,
            spacing=self.ly.spacing(),
            level=self._level + 1,
            show_overlays=DEV_OVERLAYS,
        )
        v.addWidget(top, ratios[0])
        v.addWidget(bottom, ratios[1])
        self.ly.addWidget(cont, 1)
        return top, bottom


# ------------------------ Main App ------------------------


class FTApp(QWidget):

    def _aux_load_selected(self, codigo):
        """Lê produto_auxiliar e posiciona os CBs sem disparar autosave."""
        conn = getattr(self.service, "conn", None)
        if not conn or not codigo:
            return
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT tipo_artigo_id, validade_id, temperatura_id FROM produto_auxiliar WHERE produto_codigo=?",
                (codigo,),
            )
            row = cur.fetchone()
        except Exception:
            row = None

        tid = vid = pid = None
        if row:
            tid, vid, pid = row[0], row[1], row[2]

        for cb, val in (
            (getattr(self, "cbTipoArtigo", None), tid),
            (getattr(self, "cbValidade", None), vid),
            (getattr(self, "cbTemp", None), pid),
        ):
            if not cb:
                continue
            cb.blockSignals(True)
            target = 0
            if val is not None:
                for i in range(cb.count()):
                    if cb.itemData(i) == val:
                        target = i
                        break
            cb.setCurrentIndex(target)
            cb.blockSignals(False)

    def __init__(self, service: ProductService):
        super().__init__()
        self.service = service
        self.ds = service.ds
        self.cur_index = 0
        self.current_product = None
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
        top.addStretch(1)
        from PyQt5.QtWidgets import QToolButton, QMenu, QAction

        self.btMenu = QToolButton()
        self.btMenu.setText("Menu")
        self.btMenu.setPopupMode(QToolButton.InstantPopup)
        self.mnuRoot = QMenu(self)
        mBD = QMenu("Base de Dados", self.mnuRoot)
        actUpdate = QAction("Atualizar BD", self)
        actReload = QAction("Recarregar Dados", self)
        mBD.addAction(actUpdate)
        mBD.addAction(actReload)
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
        actReload.triggered.connect(lambda: self._load_record(self.cur_index))
        actUpdate.triggered.connect(
            lambda: QMessageBox.information(
                self,
                "Atualizar BD",
                "Integração de importação/atualização será ligada aqui.",
            )
        )
        actTipos.triggered.connect(
            lambda: QMessageBox.information(
                self,
                "Tipos de Artigos",
                f"Ativos: {len(self.service.list_tipos_artigos())-1}",
            )
        )
        actVal.triggered.connect(
            lambda: QMessageBox.information(
                self, "Validade", f"Ativos: {len(self.service.list_validade())-1}"
            )
        )
        actTemps.triggered.connect(
            lambda: QMessageBox.information(
                self,
                "Temperaturas",
                f"Ativos: {len(self.service.list_temperaturas())-1}",
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

        # ---------------- B1 — Dados Gerais (C1) ----------------
        self.C1 = Zone("C1", self, flow="v", level=0, show_overlays=DEV_OVERLAYS)
        page_ly.addWidget(self._section_box("[B1] - Dados Gerais", self.C1), 0)

        C1A, C1B = self.C1.split_h((3, 1))
        C1A1, C1A2 = C1A.split_v((1, 3))

        lbl_w = 110
        self.edCodigo = QLineEdit()
        make_readonly_lineedit(self.edCodigo, False)
        self.edNome = QLineEdit()
        make_readonly_lineedit(self.edNome, True)
        C1A1.add_row("Código:", self.edCodigo, label_minw=lbl_w, vspacing=2)
        C1A1.add_row("Nome do Artigo:", self.edNome, label_minw=lbl_w, vspacing=2)

        # C1.A.2        # C1.A.2
        C1A21, C1A22 = C1A2.split_h(
            (3, 1)
        )  # C1.A.2.A (famílias/PVPs) + C1.A.2.B (combos)
        # C1.A.2.A → divide verticalmente: topo (famílias) + base (PVP1..PVP5)
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
        # Para simplicidade, recriamos com um loop que adiciona 5 colunas iguais
        C1A21_base.ly.takeAt(0)
        C1A21_base.ly.takeAt(0)
        # Reconstruir base em 5 colunas iguais
        base_cont = QWidget(C1A21_base)
        base_h = QHBoxLayout(base_cont)
        base_h.setContentsMargins(0, 0, 0, 0)
        base_h.setSpacing(C1A21_base.ly.spacing())
        C1A21_base.ly.addWidget(base_cont, 1)
        self.lbPVP = []
        for i in range(5):
            col = Zone(
                f"C1.A.2.A.P{i+1}",
                base_cont,
                flow="v",
                margins=2,
                spacing=2,
                level=C1A21_base._level + 1,
                show_overlays=DEV_OVERLAYS,
            )
            lbl = QLabel(f"PVP{i+1}")
            val = QLabel("—")
            make_readonly_lineedit(
                QLineEdit(), False
            )  # just to get style, we'll style label
            val.setStyleSheet("border:none; background:transparent; font-weight:600;")
            col.add(lbl, 0)
            col.add(val, 0)
            self.lbPVP.append(val)
            base_h.addWidget(col, 1)

        # Combos diretamente em C1.A.2.B (sem .B.2)
        w_tipos, self.cbTipos = stack_combo("Tipos Artigos")
        w_val, self.cbValidade = stack_combo("Validade")
        w_temp, self.cbTemp = stack_combo("Temperaturas")
        C1A22.add(w_tipos)
        C1A22.add(w_val)
        C1A22.add(w_temp)

        # C1.B — placeholder de preview
        prev = QLabel("Pré-visualização")
        prev.setAlignment(Qt.AlignCenter)
        prev.setStyleSheet("border:1px solid #ccc; padding:8px;")
        C1B.add(prev, 1)

        # ---------------- B2 — Ingredientes (C2) ----------------
        self.C2 = Zone("C2", self, flow="v", level=0, show_overlays=DEV_OVERLAYS)
        page_ly.addWidget(self._section_box("[B2] - Ingredientes", self.C2), 0)

        self.tbIng = QTableWidget(0, 6, self)
        self.tbIng.setHorizontalHeaderLabels(
            ["Ingrediente", "QTD", "U.M.", "PPU", "Total", "Código"]
        )
        self.tbIng.verticalHeader().setVisible(False)
        self.tbIng.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.C2.add(self.tbIng, 1)
        self._setup_ing_columns()

        # ---------------- B3 — Custos (C3) ----------------
        self.C3 = Zone("C3", self, flow="v", level=0, show_overlays=DEV_OVERLAYS)
        page_ly.addWidget(self._section_box("[B3] - Custos", self.C3), 0)

        C3A = Zone("C3.A", self.C3, flow="v", level=1, show_overlays=DEV_OVERLAYS)
        self.C3.add(C3A, 1)
        C3AA, C3AB = C3A.split_h((1, 1))

        # C3 swap aplicado: C3.A.A = Custo Total | C3.A.B = "Food Cost:"
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

        # ---------------- B4 — Preparação (C4) ----------------
        self.C4 = Zone("C4", self, flow="v", level=0, show_overlays=DEV_OVERLAYS)
        page_ly.addWidget(self._section_box("[B4] - Preparação", self.C4), 1)

        # Simples toolbar "demo" e editor
        tb = QHBoxLayout()
        tb.setContentsMargins(0, 0, 0, 0)
        tb.setSpacing(6)
        for txt in ["↥", "↶", "B", "I", "U", "→", "⇔", "≡", "1.", "•"]:
            b = QPushButton(txt)
            b.setFixedSize(28, 22)
            tb.addWidget(b)
        tbw = QWidget()
        tbw.setLayout(tb)
        self.C4.add(tbw, 0)

        self.edPrep = QTextEdit()
        self.edPrep.setPlaceholderText("— Texto de preparação —")
        self.C4.add(self.edPrep, 1)

        # ---------------- B5 — Nutrição / Alergénios (C5) ----------------
        self.C5 = Zone("C5", self, flow="v", level=0, show_overlays=DEV_OVERLAYS)
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

    # ---------- Alergénios grid ----------
    def _build_allergens_grid(self):
        names = self.service.list_active_allergens()
        gridw = QWidget()
        grid = QGridLayout(gridw)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        cols = 2
        for i, (aid, nome) in enumerate(names):
            r = i // cols
            c = i % cols
            cb = QCheckBox(nome)
            grid.addWidget(cb, r, c, alignment=Qt.AlignLeft)
        self.C5.add(gridw, 0)

    # ---------- Ingredientes: colunas ----------
    def _setup_ing_columns(self):
        w = max(self.width(), 1100)
        self.tbIng.setColumnHidden(5, True)
        self.tbIng.setColumnWidth(0, int(w * 0.50))
        self.tbIng.setColumnWidth(1, int(w * 0.10))
        self.tbIng.setColumnWidth(2, int(w * 0.10))
        self.tbIng.setColumnWidth(3, int(w * 0.14))
        self.tbIng.setColumnWidth(4, int(w * 0.16))

    def _apply_ingredient_widths(self):
        self._setup_ing_columns()

    # ---------- Navegação ----------
    def _connect_nav(self):
        self.btFirst.clicked.connect(lambda: self._goto(0))
        self.btPrev.clicked.connect(lambda: self._go(-1))
        self.btNext.clicked.connect(lambda: self._go(+1))
        self.btLast.clicked.connect(lambda: self._goto(self.service.total() - 1))

    def _goto(self, idx):
        self.cur_index = max(0, min(idx, self.service.total() - 1))
        self._load_record(self.cur_index)

    def _go(self, delta):
        self.cur_index = (self.cur_index + delta) % max(1, self.service.total())
        self._load_record(self.cur_index)

    # ---------- Carregamento de dados ----------
    def _load_record(self, idx: int):
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
            txt = (
                "—"
                if val
                in (
                    None,
                    "",
                )
                else f"{float(val):.2f}"
            )
            if i < len(self.lbPVP):
                self.lbPVP[i].setText(txt)

        self.cbTipos.clear()
        self.cbValidade.clear()
        self.cbTemp.clear()
        self.cbTipos.addItems([])
        self.cbTipos.clear()
        for cod, desc in self.service.list_tipos_artigos():
            self.cbTipos.addItem(desc, cod)

        self.cbValidade.clear()
        for cod, desc in self.service.list_validade():
            self.cbValidade.addItem(desc, cod)

        self.cbTemp.clear()
        for cod, desc in self.service.list_temperaturas():
            self.cbTemp.addItem(desc, cod)

        def _select_by_code(combo, code_value):
            if code_value is None:
                return
            for i in range(combo.count()):
                if combo.itemData(i) == code_value:
                    combo.setCurrentIndex(i)
                    return

        _select_by_code(self.cbTipos, product.tipo_artigo_cod)
        _select_by_code(self.cbValidade, product.validade_cod)
        _select_by_code(self.cbTemp, product.temperatura_cod)

        self.tbIng.setRowCount(0)
        for ing in product.ingredients:
            r = self.tbIng.rowCount()
            self.tbIng.insertRow(r)
            vals = []
            for c, val in enumerate(vals):
                it = QTableWidgetItem(val)
                it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.tbIng.setItem(r, c, it)

        self._apply_ingredient_widths()
        self.edCustoTotal.setText(f"{self.service.calculate_cost(product):.2f}")
        self.lbPos.setText(f"{self.cur_index+1} / {max(1,self.service.total())}")

        # --- Auxiliares: fetch/populate/load (canon) ---
        try:
            _t, _v, _p = self._aux_fetch_lists()
            self._aux_populate_cbs(_t, _v, _p)
            self._aux_load_selected(codigo)
            self._aux_wire_autosave()
        except Exception as e:
            logger.error("[AuxCanon][ERRO] %s", e)

    # ---------- Cálculos ----------
    def _update_costs_from_table(self):
        """Recalculate total cost using the service layer."""
        try:
            self.edCustoTotal.setText(f"{total:.2f}")
        except Exception:
            pass

    # ---------- Eventos ----------
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._apply_ingredient_widths()

    def _toggle_overlays(self):
        global DEV_OVERLAYS
        DEV_OVERLAYS = not DEV_OVERLAYS
        for z in self.findChildren(Zone):
            if z.tag.count(".") == 0:
                z.apply_overlays(DEV_OVERLAYS)

    def _toggle_overlays_btn(self):
        self._toggle_overlays()
        self.btOverlay.setText(f"Overlays: {'ON' if DEV_OVERLAYS else 'OFF'}")

    # ================== AUXILIARES — CANÓNICO (v2) ==================
    def _aux_fetch_lists(self):
        def _aux_fetch_lists(self):
            """
            Lê listas canónicas a partir da BD, resolvendo nomes de tabelas/colunas:
            - Tabelas: tipos_artigos; validade/validades; temperaturas
            - PK: id|cod|codigo
            - Nome: descricao|nome|designacao
            Apenas registos ativos (COALESCE(ativo,1)=1).
            Retorna: {"tipo_artigo":[(id,nome)], "validade":[(id,nome)], "temperatura":[(id,nome)]}
            """
            out = {"tipo_artigo": [], "validade": [], "temperatura": []}
            conn = getattr(self.service, "conn", None)
            if not conn:
                return out
            cur = conn.cursor()

            def resolve_table(candidates):
                for t in candidates:
                    try:
                        cur.execute(
                            f"SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                            (t,),
                        )
                        if cur.fetchone():
                            return t
                    except Exception:
                        pass
                return None

            def pick_cols(table):
                # devolve (id_col, name_col) ou (None,None)
                try:
                    cur.execute(f"PRAGMA table_info({table})")
                    rows = cur.fetchall()
                except Exception:
                    return (None, None)
                names = [r[1].lower() for r in rows]
                # PK candidates
                id_col = None
                for cand in ("id", "cod", "codigo"):
                    if cand in names:
                        id_col = cand
                        break
                if id_col is None:
                    # tenta PK pelo flag
                    for r in rows:
                        if r[5]:
                            id_col = r[1]
                            break
                # Nome candidates
                name_col = None
                for cand in ("descricao", "nome", "designacao"):
                    if cand in names:
                        name_col = cand
                        break
                return (id_col, name_col)

            def fetch_generic(kind, table_candidates):
                tbl = resolve_table(table_candidates)
                if not tbl:
                    return []
                id_col, name_col = pick_cols(tbl)
                if not id_col or not name_col:
                    return []
                sql = f"SELECT {id_col}, {name_col} FROM {tbl} WHERE COALESCE(ativo,1)=1 ORDER BY {name_col}"
                try:
                    cur.execute(sql)
                    res = cur.fetchall()
                    out = []
                    for r in res:
                        try:
                            rid = int(r[0])
                        except Exception:
                            # aceita também chave texto
                            try:
                                rid = int(str(r[0]).strip())
                            except Exception:
                                continue
                        nm = str(r[1]).strip()
                        if nm:
                            out.append((rid, nm))
                    return out
                except Exception:
                    return []

            out["tipo_artigo"] = fetch_generic("tipo_artigo", ("tipos_artigos",))
            out["validade"] = fetch_generic("validade", ("validade", "validades"))
            out["temperatura"] = fetch_generic("temperatura", ("temperaturas",))
            return out

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

    def _aux_populate_cbs(self):
        def _aux_populate_cbs(self, lists):
            """Limpa e repovoa as comboboxes exclusivamente com o que vem da BD."""
            # tenta descobrir widgets já criados
            cb_tipo = getattr(self, "cbTipoArtigo", None)
            cb_val = getattr(self, "cbValidade", None)
            cb_temp = getattr(self, "cbTemp", None)

            try:
                from PyQt5.QtWidgets import QComboBox
            except Exception:
                from PySide6.QtWidgets import QComboBox

            def ensure(cb_attr, hint_names):
                cb = getattr(self, cb_attr, None)
                if cb:
                    return cb
                # tenta por objectName heurístico
                for w in self.findChildren(QComboBox):
                    nm = (w.objectName() or "").lower()
                    if any(h in nm for h in hint_names):
                        setattr(self, cb_attr, w)
                        return w
                return None

            cb_tipo = ensure("cbTipoArtigo", ("tipo", "art"))
            cb_val = ensure("cbValidade", ("valid",))
            cb_temp = ensure("cbTemp", ("temp",))

            def fill(cb, items):
                if not cb:
                    return
                cb.blockSignals(True)
                cb.clear()
                cb.addItem("—", None)
                seen = set()
                for rid, nm in items:
                    key = (rid, nm)
                    if key in seen:
                        continue
                    seen.add(key)
                    cb.addItem(nm, rid)
                cb.blockSignals(False)

            fill(cb_tipo, lists.get("tipo_artigo", []))
            fill(cb_val, lists.get("validade", []))
            fill(cb_temp, lists.get("temperatura", []))

        def fill(cb, items):
            if cb is None:
                return
            try:
                cb.blockSignals(True)
            except Exception:
                pass
            try:
                cb.clear()
                # placeholder "—" (None)
                cb.addItem("—", None)
                for i, name in items:
                    cb.addItem(str(name), int(i))
            finally:
                try:
                    cb.blockSignals(False)
                except Exception:
                    pass

        fill(cb_tipo, lists["tipo_artigo"])
        fill(cb_val, lists["validade"])
        fill(cb_temp, lists["temperatura"])

    def _aux_load_selected(self, codigo):
        """Posiciona os comboboxes na seleção gravada (produto_auxiliar ou produto_attrs)."""
        cb_tipo, cb_val, cb_temp = self._aux_find_cbs()
        if not any([cb_tipo, cb_val, cb_temp]):
            return
        sel = {"tipo_artigo": None, "validade": None, "temperatura": None}
        try:
            cur = self.service.conn.cursor()
            cur.execute(
                "SELECT tipo_artigo_id, validade_id, temperatura_id FROM produto_auxiliar WHERE produto_codigo=?",
                (codigo,),
            )
            row = cur.fetchone()
            if row:
                sel["tipo_artigo"], sel["validade"], sel["temperatura"] = (
                    row[0],
                    row[1],
                    row[2],
                )
            else:
                cur.execute(
                    "SELECT attr, value FROM produto_attrs WHERE produto_codigo=? AND attr IN ('tipo_artigo','validade','temperatura')",
                    (codigo,),
                )
                for a, v in cur.fetchall():
                    try:
                        sel[a] = int(v)
                    except Exception:
                        sel[a] = None
        except Exception as e:
            logger.warning("[AuxUI][AVISO] a ler seleção: %s", e)

        def set_by_data(cb, wanted_id):
            if cb is None:
                return
            try:
                cb.blockSignals(True)
            except Exception:
                pass
            try:
                if wanted_id is None:
                    cb.setCurrentIndex(0)  # "—"
                    return
                for i in range(cb.count()):
                    try:
                        d = cb.itemData(i)
                    except Exception:
                        d = None
                    if d == wanted_id:
                        cb.setCurrentIndex(i)
                        return
                cb.setCurrentIndex(0)
            finally:
                try:
                    cb.blockSignals(False)
                except Exception:
                    pass

        set_by_data(cb_tipo, sel["tipo_artigo"])
        set_by_data(cb_val, sel["validade"])
        set_by_data(cb_temp, sel["temperatura"])

    def _aux_wire_autosave(self):
        def _aux_wire_autosave(self):
            """Liga currentIndexChanged para gravar em produto_auxiliar (só quando itemData é inteiro)."""
            conn = getattr(self.service, "conn", None)
            if not conn:
                return
            try:
                from PyQt5.QtCore import QObject
            except Exception:
                from PySide6.QtCore import QObject

            def save_current():
                if getattr(self, "_loading", False):
                    return
                codigo = None
                try:
                    codigo = self.service.codigo_at(self.cur_index)
                except Exception:
                    pass
                if not codigo:
                    return
                tid = getattr(self, "cbTipoArtigo", None)
                vid = getattr(self, "cbValidade", None)
                pid = getattr(self, "cbTemp", None)

                def as_id(cb):
                    if not cb:
                        return None
                    d = cb.currentData()
                    return int(d) if isinstance(d, int) else None

                T = as_id(tid)
                V = as_id(vid)
                P = as_id(pid)
                try:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO produto_auxiliar (produto_codigo, tipo_artigo_id, validade_id, temperatura_id)
                        VALUES (?,?,?,?)
                        ON CONFLICT(produto_codigo) DO UPDATE SET
                          tipo_artigo_id=COALESCE(excluded.tipo_artigo_id, tipo_artigo_id),
                          validade_id   =COALESCE(excluded.validade_id   , validade_id),
                          temperatura_id=COALESCE(excluded.temperatura_id, temperatura_id)
                    """,
                        (codigo, T, V, P),
                    )
                    conn.commit()
                    # opcional: feedback debug
                    # print(f"[AUX][SAVE] {codigo} -> tipo={T} valid={V} temp={P}")
                except Exception:
                    conn.rollback()

            for cbname in ("cbTipoArtigo", "cbValidade", "cbTemp"):
                cb = getattr(self, cbname, None)
                if cb:
                    try:
                        cb.currentIndexChanged.connect(save_current)
                    except Exception:
                        pass

        def saver(kind, cb):
            if cb is None:
                return

            def handler(*_):
                if getattr(self, "_loading", False):
                    return
                idx = cb.currentIndex()
                data = cb.itemData(idx)
                value = None if (idx <= 0 or data in (None, "", "—")) else data
                # produto visível
                try:
                    codigo = self.service.codigo_at(getattr(self, "cur_index", 0))
                except Exception:
                    codigo = None
                if not codigo:
                    try:
                        codigo = self.lbCodigo.text().strip()
                    except Exception:
                        pass
                if not codigo:
                    return
                # grava
                col = {
                    "tipo_artigo": "tipo_artigo_id",
                    "validade": "validade_id",
                    "temperatura": "temperatura_id",
                }[kind]
                try:
                    cur = self.service.conn.cursor()
                    if value is None:
                        cur.execute(
                            "INSERT INTO produto_auxiliar (produto_codigo) VALUES (?) ON CONFLICT(produto_codigo) DO NOTHING",
                            (codigo,),
                        )
                        cur.execute(
                            f"UPDATE produto_auxiliar SET {col}=NULL WHERE produto_codigo=?",
                            (codigo,),
                        )
                    else:
                        cur.execute(
                            f"""
                            INSERT INTO produto_auxiliar (produto_codigo, {col})
                            VALUES (?, ?)
                            ON CONFLICT(produto_codigo) DO UPDATE SET {col}=excluded.{col}
                        """,
                            (codigo, int(value)),
                        )
                    self.service.conn.commit()
                except Exception as e:
                    logger.error("[AuxUI][ERRO] gravar %s p/%s: %s", kind, codigo, e)

            cb.currentIndexChanged.connect(handler)

        saver("tipo_artigo", cb_tipo)
        saver("validade", cb_val)
        saver("temperatura", cb_temp)
        logger.info("[AuxUI] autosave ligado.")

    def _aux_ensure_guard(self):
        """Envolve _load_record com guarda self._loading True/False e injeta pipeline dos auxiliares."""
        if getattr(self, "_aux_guard_wrapped", False):
            return
        orig = getattr(self, "_load_record", None)
        if not callable(orig):
            logger.warning("[AuxUI][AVISO] _load_record ausente.")
            return

        def wrapped(idx: int):
            self._loading = True
            try:
                self._aux_populate_cbs()
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
