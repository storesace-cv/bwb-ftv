# Fichas Técnicas Valorizadas — UI (Single-file)
#
# Regras Aprovadas (manter sempre no topo e cumprir em TODO o código)
# -------------------------------------------------------------------
# 1) Nomenclatura de Blocos e Células
#    - Blocos: [B1] Ficha do Artigo (inclui Família, Combos & PVPs),
#      [B4] FICHA TÉCNICA, [B5] FOOD COST,
#      [B6] PREPARAÇÃO, [B7] NUTRIÇÃO / ALERGÉNIOS.
#      • PVPs passaram do bloco [B3] para a mesma grelha de Família/
#        Sub-família e mantêm etiquetas-c centradas (por omissão) por coluna.
#    - Célula raiz do bloco: Bn.C1 (ex.: B1.C1, B4.C1, B5.C1).
#    - Divisão horizontal: sufixos .A (esq.) e .B (dir.).
#    - Divisão vertical: sufixos .1 (topo) e .2 (base).
#    - Subdivisões encadeiam-se mantendo a regra (ex.: B2.C1.B.1).
#    - NÃO usar nomes ad hoc (ex.: C1.X, C1AA, C1AB).
#
# 2) Changelog: toda alteração documentada deve incluir data/hora
#    (Europe/Lisbon)
#    - Formato: YYYY-MM-DD HH:MM — descrição.
#
# Changelog
# ---------
# 2025-09-08 16:06 — v3.64 — Alinhamento de nomenclatura na secção de PVPs (C1)
#    & reforço de comentários; split vertical em C1.A.2 com dados no topo;
#    Custo Total = soma da coluna "Total".
# 2025-09-08 17:35 — v3.73 — Restabelecido: botão Overlay no topo
#    esquerdo; navegação no rodapé; scroll vertical; mantidas alterações
#    pedidas (C1 swap, remoção C1.A.2.B.2, tags visíveis).
# 2025-09-08 18:05 — v3.80 — Reintroduzidos [B6] PREPARAÇÃO e [B7]
#    NUTRIÇÃO / ALERGÉNIOS; overlays/cores preservados; footer com contador.
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
#      etiqueta-c centrada por cima e valor por baixo; leitura PVP1..2 de
#      precos_taxas).
#    • C1.A.2.B: combos ligados às tabelas auxiliares (ativo=1,
#      ordenadas) com pré-seleção por FK do produto.
#    • B2: grelha 50/10/10/14/16 + Código oculto; cálculo Total por linha
#      quando necessário.
#    • Secção de PVPs alinhada por coluna com etiqueta-c centrada por cima e
#      valor por baixo; leitura PVP1..2 de precos_taxas.
#    • B6: editor de Preparação com toolbar simples; B7: Alergénios 2×N
#      com persistência N–N.
#    • Menu: QToolButton (InstantPopup) sem caret; Base de Dados /
#      Tabelas / Utilitários; diálogos de gestão nas Tabelas.
#    • Overlays/cores preservados; navegação centrada no rodapé; scroll
#      vertical; cabeçalho em comentários.
# 2025-09-13 17:16 — v3.89 — Raiz dos blocos B2–B5 renomeada para ".C1".
# 2025-09-13 23:08 — v3.90 — Menu Segurança com ações de cópia e reposição.
# 2025-09-14 18:23 — v3.91 — Largura da página adaptativa; scroll horizontal
#    desativado.
# 2025-09-15 01:19 — v3.92 — Placeholder padrão para imagens ausentes.
# 2025-09-15 02:40 — v3.93 — B4 com galeria de 4 imagens (PrepImagePreview).
# 2025-09-15 02:51 — v3.94 — Preenchimento sequencial das imagens de
#    preparação.
# 2025-09-15 04:12 — v3.95 — Food Cost "--N/A--" sem PVP ou falha de cálculo;
#    mantém "0%" quando falta IVA.
# 2025-09-15 05:15 — v3.96 — Food Cost "--" quando falta IVA; loga "missing Iva1".
# 2025-09-15 15:40 — v3.97 — Filtro Food Cost (Bom/Aceitável/Mau) com botões exclusivos.
# 2025-09-15 17:15 — v3.98 — Código/Nome fixos fora do scroll;
#    B1.C1 inicia após cabeçalho.
# 2025-09-18 01:41 — v3.99 — Títulos das secções regressam ao peso
#    normal e alinhamentos ajustados para legibilidade sem sobrescritas
#    agressivas de estilo.
# 2025-09-18 23:41 — v3.100 — Família/Sub-família e combos extraídos de
#    B1.D1 para o novo bloco [B2] com raiz B2.C1; alinhamento de tags
#    atualizado nas verificações automáticas.
# 2025-09-19 10:45 — v3.101 — Família/Sub-família e combos reintegrados em
#    B1.C1.A.*, preservando metadados de bloco e alinhamentos partilhados.

import sys
import json
import logging
import html as html_module
import html.parser as html_parser
import itertools
import re
from pathlib import Path
try:  # PyQt 5.15.10 wheels omit QWIDGETSIZE_MAX on some platforms
    from PyQt5.QtCore import Qt, QTimer, QPoint, QWIDGETSIZE_MAX
except ImportError:  # pragma: no cover - fallback for stripped builds
    from PyQt5.QtCore import Qt, QTimer, QPoint

    QWIDGETSIZE_MAX = 16777215
from PyQt5.QtGui import QFont, QIcon, QKeySequence, QTextOption, QPixmap
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
    QButtonGroup,
    QToolBar,
    QAction,
    QFileDialog,
    QFrame,
    QStyle,
    QComboBox,
)
from data.datastore import DataStore
from services.products import ProductService, calculate_food_cost
from domain import FichaTecnica
from utils.formatting import format_pt_number, parse_decimal

from . import layout
from .layout import Zone
from .models import (
    apply_fichas_tecnicas_headers,
    build_fichas_tecnicas_model,
    update_fichas_tecnicas_model,
)
from .qt_compat import exec_modal
from .utilities import (
    AlignmentVariant,
    FIELD_STYLE,
    apply_fcfilter_btn_style,
    apply_label_style,
    apply_overlay_label_style,
    make_readonly_lineedit,
    match_font,
)
from .dialogs import (
    import_data,
    manage_aux_table,
    update_data,
    backup_database,
    restore_database,
    edit_fcost_values,
)

APP_TITLE = "Fichas Técnicas Valorizadas"

APP_STYLESHEET = (
    "QWidget {\n"
    "    font-size: 12px;\n"
    "    color: #1d1f23;\n"
    "}\n"
    "QMainWindow {\n"
    "    background-color: #f6f7fb;\n"
    "}\n"
    "QToolTip {\n"
    "    color: #1d1f23;\n"
    "    background-color: rgba(255, 255, 255, 0.95);\n"
    "    border: 1px solid rgba(0, 0, 0, 0.15);\n"
    "    padding: 4px 6px;\n"
    "}\n"
    "QLabel[class~='overlay-active'] {\n"
    "    color: #0b63ce;\n"
    "}"
)

logger = logging.getLogger(__name__)

# ---------------------- Image Preview ----------------------


class ImagePreview(QLabel):
    """Simple preview widget for product images."""

    def __init__(
        self,
        codigo: str | None = None,
        service: ProductService | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border:1px solid #ccc; padding:8px;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 200)
        self.codigo = None
        self.service = service
        self._orig_pix: QPixmap | None = None
        if codigo and self.service:
            self.load_image(codigo)

    # Helper methods -------------------------------------------------
    def _update_pixmap(self) -> None:
        """Scale original pixmap to current widget size."""
        if self._orig_pix:
            pix = self._orig_pix.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(pix)

    def set_placeholder(self) -> None:
        """Load and display the default placeholder image."""
        path = Path(__file__).with_name("no-image-thumb.png")
        self._orig_pix = QPixmap(str(path))
        self._update_pixmap()
        self.setText("")

    def load_image(self, codigo: str):
        """Load and show the image for ``codigo`` if available."""
        self.codigo = codigo
        if not self.service:
            return
        path = self.service.get_image_path(codigo)
        if path.exists():
            self._orig_pix = QPixmap(str(path))
            self._update_pixmap()
            self.setText("")
        else:
            self.set_placeholder()

    def save_image(self, src: str):
        """Copy ``src`` to the images folder resizing to 600×600."""
        if not self.codigo or not src or not self.service:
            return
        try:
            self.service.save_product_image(self.codigo, src)
        except Exception:
            logger.exception("[ImagePreview] save_image")
            return
        self.load_image(self.codigo)

    def delete_image(self):
        """Archive the current image and clear the preview."""
        if not self.codigo or not self.service:
            return
        try:
            self.service.delete_product_image(self.codigo)
        except Exception:
            logger.exception("[ImagePreview] delete_image")
        self.set_placeholder()

    # Events ---------------------------------------------------------
    def resizeEvent(self, event):  # pragma: no cover - GUI
        super().resizeEvent(event)
        self._update_pixmap()

    def mousePressEvent(self, event):  # pragma: no cover - GUI
        if not self.codigo or not self.service:
            return
        path = self.service.get_image_path(self.codigo)
        if not path.exists():
            fname, _ = QFileDialog.getOpenFileName(
                self,
                "Selecionar imagem",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp)",
            )
            if fname:
                self.save_image(fname)
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Imagem")
            msg.setText("Pretende substituir ou apagar a imagem?")
            btn_sub = msg.addButton("Substituir", QMessageBox.AcceptRole)
            btn_del = msg.addButton("Apagar", QMessageBox.DestructiveRole)
            msg.addButton("Cancelar", QMessageBox.RejectRole)
            exec_modal(msg)
            clicked = msg.clickedButton()
            if clicked == btn_sub:
                fname, _ = QFileDialog.getOpenFileName(
                    self,
                    "Selecionar imagem",
                    "",
                    "Images (*.png *.jpg *.jpeg *.bmp)",
                )
                if fname:
                    self.save_image(fname)
            elif clicked == btn_del:
                self.delete_image()

# -----------------------------------------------------------


class PrepImagePreview(ImagePreview):
    """Preview widget for preparation step images."""

    def __init__(
        self,
        idx: int,
        service: ProductService | None = None,
        parent=None,
    ):
        super().__init__(codigo=None, service=service, parent=parent)
        self.idx = idx

    def load_image(self, codigo: str):  # type: ignore[override]
        """Load and show the preparation image for ``codigo`` and step ``idx``."""
        self.codigo = codigo
        if not self.service:
            return
        path = self.service.get_preparacao_image_path(codigo, self.idx)
        if path.exists():
            self._orig_pix = QPixmap(str(path))
            self._update_pixmap()
            self.setText("")
        else:
            self.set_placeholder()

    def save_image(self, src: str):  # type: ignore[override]
        if not self.codigo or not src or not self.service:
            return
        try:
            self.service.save_preparacao_image(self.codigo, self.idx, src)
        except Exception:
            logger.exception("[PrepImagePreview] save_image")
            return
        self.load_image(self.codigo)

    def delete_image(self):  # type: ignore[override]
        if not self.codigo or not self.service:
            return
        try:
            self.service.delete_preparacao_image(self.codigo, self.idx)
        except Exception:
            logger.exception("[PrepImagePreview] delete_image")
        self.set_placeholder()

    def mousePressEvent(self, event):  # pragma: no cover - GUI
        if not self.codigo or not self.service:
            return

        # Antes de permitir ações no passo atual, garantir que todas as
        # imagens anteriores existem. Se alguma estiver em falta,
        # delegar o clique para o respetivo ``PrepImagePreview`` e sair.
        for prev_idx in range(1, self.idx):
            prev_path = self.service.get_preparacao_image_path(
                self.codigo, prev_idx
            )
            if not prev_path.exists():
                parent = self.parent()
                while parent and not hasattr(parent, "prep_previews"):
                    parent = parent.parent()
                if parent is not None:
                    parent.prep_previews[prev_idx - 1].mousePressEvent(event)
                return

        path = self.service.get_preparacao_image_path(self.codigo, self.idx)
        if not path.exists():
            fname, _ = QFileDialog.getOpenFileName(
                self,
                "Selecionar imagem",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp)",
            )
            if fname:
                self.save_image(fname)
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Imagem")
            msg.setText("Pretende substituir ou apagar a imagem?")
            btn_sub = msg.addButton("Substituir", QMessageBox.AcceptRole)
            btn_del = msg.addButton("Apagar", QMessageBox.DestructiveRole)
            msg.addButton("Cancelar", QMessageBox.RejectRole)
            exec_modal(msg)
            clicked = msg.clickedButton()
            if clicked == btn_sub:
                fname, _ = QFileDialog.getOpenFileName(
                    self,
                    "Selecionar imagem",
                    "",
                    "Images (*.png *.jpg *.jpeg *.bmp)",
                )
                if fname:
                    self.save_image(fname)
            elif clicked == btn_del:
                self.delete_image()

# ------------------------ Main App ------------------------


class FTApp(QWidget):
    def __init__(self, service: ProductService):
        super().__init__()
        self.service = service
        self.ds = service.ds
        self.cur_index = 0
        self.current_product = None
        self._prep_dirty = False
        self._active_fcost_filter: int | None = None
        self._allergen_checkboxes: dict[int, QCheckBox] = {}
        self._allergen_tooltips: dict[int, str] = {}
        self._allergen_zone: Zone | None = None
        self._build_ui()
        self._connect_nav()
        self._load_record(self.cur_index)
        codigo = getattr(self.current_product, "code", None)
        if codigo:
            for pv in getattr(self, "prep_previews", []):
                pv.load_image(codigo)

    def _section_box(self, title: str, zone: Zone) -> QGroupBox:
        user_title = re.sub(r"^\[[^\]]+\]\s*-\s*", "", title).strip()
        box = QGroupBox()
        box.setTitle("")
        box.setProperty("devTitle", title)
        box.setProperty("userTitle", user_title)
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        header = QLabel(title if layout.DEV_OVERLAYS else user_title)
        header.setObjectName("sectionHeader")
        header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setProperty("devLabel", title)
        header.setProperty("userLabel", user_title)
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_font = QFont(header.font())
        header_font.setPointSize(18)
        header_font.setBold(True)
        header_font.setWeight(QFont.Bold)
        header.setFont(header_font)
        header.setStyleSheet(
            """
            QLabel#sectionHeader {
                background-color: rgba(200,200,200,0.5);
                border: 1px solid rgba(0,0,0,0.3);
                border-top-color: rgba(255,255,255,0.8);
                border-left-color: rgba(255,255,255,0.8);
                border-bottom-color: rgba(0,0,0,0.4);
                border-right-color: rgba(0,0,0,0.4);
                border-radius: 6px;
                padding: 4px 10px;
            }
            """
        )

        ly = QVBoxLayout(box)
        ly.setContentsMargins(3, 5, 3, 5)
        ly.setSpacing(5)
        ly.addWidget(header)
        ly.addWidget(zone)

        box._section_header = header
        return box

    def _build_ui(self):
        self.setWindowTitle(APP_TITLE)
        self.resize(1180, 860)
        root = QVBoxLayout(self)
        root.setContentsMargins(3, 5, 3, 5)
        root.setSpacing(5)

        # --- Top bar: Overlay (esq) + Menu (dir) ---
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        self.btOverlay = QPushButton(
            f"Overlays: {'ON' if layout.DEV_OVERLAYS else 'OFF'}"
        )
        self.btOverlay.clicked.connect(self._toggle_overlays_btn)
        top.addWidget(self.btOverlay, 0, Qt.AlignLeft)
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
        actAlerg = QAction("Alergénios", self)
        mTab.addAction(actTipos)
        mTab.addAction(actVal)
        mTab.addAction(actTemps)
        mTab.addAction(actAlerg)
        self.mnuRoot.addMenu(mTab)
        mUtil = QMenu("Utilitários", self.mnuRoot)
        actTheme = QAction("Tema", self)
        mUtil.addAction(actTheme)
        self.mnuRoot.addMenu(mUtil)
        mConf = QMenu("Configurações", self.mnuRoot)
        mParams = QMenu("Parametrizações", mConf)
        actFoodCost = QAction("Food Cost", self)
        mParams.addAction(actFoodCost)
        mConf.addMenu(mParams)
        self.mnuRoot.addMenu(mConf)
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
        actAlerg.triggered.connect(
            lambda: manage_aux_table(
                self,
                "Alergénios",
                {
                    "list": self.ds.aux.list_alergenios_admin,
                    "add": self.ds.aux.add_alergenio,
                    "set_active": self.ds.aux.set_alergenio_ativo,
                    "update": self.ds.aux.update_alergenio,
                },
                on_change=self._aux_refresh_lists,
            )
        )
        actTheme.triggered.connect(
            lambda: QMessageBox.information(
                self, "Tema", "Alternância de tema pendente."
            )
        )
        actFoodCost.triggered.connect(
            lambda: edit_fcost_values(self, self.ds.fcost)
        )
        self.btSearchToggle = QToolButton()
        self.btSearchToggle.setCheckable(True)
        self.btSearchToggle.setAutoRaise(True)
        search_icon = self.style().standardIcon(QStyle.SP_FileDialogContentsView)
        if isinstance(search_icon, QIcon):
            self.btSearchToggle.setIcon(search_icon)
        else:  # pragma: no cover - defensive fallback
            self.btSearchToggle.setText("🔍")
        self.btSearchToggle.setToolTip("Pesquisar fichas")
        self.btSearchToggle.toggled.connect(self._toggle_search_panel)
        top.addWidget(self.btSearchToggle, 0, Qt.AlignRight)
        top.addWidget(self.btMenu, 0, Qt.AlignRight)
        root.addLayout(top)

        # --- Pesquisa de produtos/ingredientes ---
        self.searchContainer = Zone(
            "B0.C2",
            self,
            flow="v",
            show_overlays=layout.DEV_OVERLAYS,
        )
        self.searchContainer.setVisible(False)
        self.searchLeftZone, self.searchCenterZone, self.searchRightZone = (
            self.searchContainer.split_h((1, 1, 1))
        )

        search_left_widget = QWidget(self.searchLeftZone)
        search_left_layout = QGridLayout(search_left_widget)
        search_left_layout.setContentsMargins(6, 6, 6, 6)
        search_left_layout.setHorizontalSpacing(6)
        search_left_layout.setVerticalSpacing(4)

        self.searchProductField = QLineEdit(search_left_widget)
        self.searchProductField.setPlaceholderText("Nome do produto")
        self.searchProductButton = QPushButton("IR", search_left_widget)
        self.searchIngredientField = QLineEdit(search_left_widget)
        self.searchIngredientField.setPlaceholderText("Nome do ingrediente")
        self.searchIngredientButton = QPushButton("IR", search_left_widget)
        self.searchResetButton = QPushButton("Mostrar todos os registos", search_left_widget)
        self.searchResetButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        search_left_layout.addWidget(self.searchProductField, 0, 0)
        search_left_layout.addWidget(self.searchProductButton, 0, 1)
        search_left_layout.addWidget(self.searchIngredientField, 1, 0)
        search_left_layout.addWidget(self.searchIngredientButton, 1, 1)
        search_left_layout.addWidget(self.searchResetButton, 2, 0, 1, 2)
        search_left_layout.setColumnStretch(0, 1)

        self.searchLeftZone.ly.addWidget(search_left_widget)

        self.searchProductButton.clicked.connect(self._apply_search_filters)
        self.searchIngredientButton.clicked.connect(self._apply_search_filters)
        self.searchProductField.returnPressed.connect(self._apply_search_filters)
        self.searchIngredientField.returnPressed.connect(self._apply_search_filters)
        self.searchResetButton.clicked.connect(self._reset_search_filters)

        root.addWidget(self.searchContainer, 0)

        lbl_w = 110

        # --- Cabeçalho flutuante (duplicado de B0.C1.A) ---
        header = QWidget(self)
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_ly = QVBoxLayout(header)
        header_ly.setContentsMargins(0, 0, 0, 0)
        header_ly.setSpacing(8)
        self.header = header
        self.headerC1 = Zone(
            "B0.C1",
            header,
            flow="v",
            margins=4,
            spacing=2,
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
            widget_type="campo",
        )
        self.headerC1.apply_metadata(
            zone_type="secao-cabecalho",
            widget_type="campo",
        )
        header_ly.addWidget(self.headerC1, 0)
        self.headerC1A = Zone(
            "B0.C1.A",
            self.headerC1,
            flow="v",
            margins=4,
            spacing=2,
            level=1,
            show_overlays=layout.DEV_OVERLAYS,
            widget_type="campo",
        )
        self.headerC1A.apply_metadata(
            zone_type="secao-cabecalho-detalhes",
            widget_type="campo",
        )
        self.headerC1.add(self.headerC1A)
        self.headerEdCodigo = QLineEdit()
        make_readonly_lineedit(self.headerEdCodigo)
        self.headerEdCodigo.setStyleSheet(FIELD_STYLE)
        self.headerEdNome = QLineEdit()
        make_readonly_lineedit(self.headerEdNome)
        self.headerEdNome.setStyleSheet(FIELD_STYLE)
        self.headerC1A.add_row(
            "Código:",
            self.headerEdCodigo,
            label_minw=lbl_w,
            vspacing=0,
            overlay_text="Produtos.Codigo",
        )
        self.headerC1A.add_row(
            "Nome do Artigo:",
            self.headerEdNome,
            label_minw=lbl_w,
            vspacing=1,
            overlay_text="Produtos.Nome",
        )
        root.addWidget(header, 0)
        header.hide()

        # --- Conteúdo com scroll vertical ---
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        page = QWidget()
        page_ly = QVBoxLayout(page)
        page_ly.setContentsMargins(0, 0, 0, 0)
        page_ly.setSpacing(8)
        scroll.setWidget(page)
        self.scroll = scroll
        self.page = page
        root.addWidget(scroll, 1)
        self._update_page_width()

        self.B1 = Zone(
            "B1",
            self,
            flow="v",
            margins=0,
            spacing=6,
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
        )
        self.B1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.B1.ly.setContentsMargins(0, 0, 0, 0)

        # ---------------- B1.A1 — zona auxiliar ----------------
        self.B1A1 = Zone(
            "B1.A1",
            self.B1,
            flow="v",
            margins=4,
            spacing=4,
            level=self.B1._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
        )
        self.B1.ly.addWidget(self.B1A1, 0)

        self.B1A1A = Zone(
            "B1.A1.A",
            self.B1A1,
            flow="v",
            margins=4,
            spacing=2,
            level=self.B1A1._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
        )
        self.B1A1.ly.addWidget(self.B1A1A, 0)
        self.B1A1AA, self.B1A1AB = self.B1A1A.split_h((3, 1))
        self.B1A1AAA, self.B1A1AAB, self.B1A1AAC = self.B1A1AA.split_v((1, 1, 1))
        for zone in (self.B1A1AAA, self.B1A1AAB, self.B1A1AAC):
            zone.ly.setContentsMargins(0, 0, 0, 0)
            current_policy = zone.sizePolicy()
            zone.setSizePolicy(
                QSizePolicy.Expanding,
                current_policy.verticalPolicy(),
            )

        # ---------------- B1 — Ficha do Artigo (B1.C1) ----------------
        self.C1 = Zone(
            "B1.C1",
            self.B1,
            flow="v",
            level=self.B1._level,
            show_overlays=layout.DEV_OVERLAYS,
            spacing=2,
        )
        C1_margins = self.C1.ly.contentsMargins()
        self.C1.ly.setContentsMargins(
            C1_margins.left(),
            C1_margins.top(),
            C1_margins.right(),
            0,
        )
        self.B1.ly.addWidget(self.C1, 0)
        page_ly.addWidget(
            self._section_box("[B1] - FICHA DO ARTIGO", self.B1),
            0,
        )

        C1A = self.C1
        C1A_margins = C1A.ly.contentsMargins()
        C1A.ly.setContentsMargins(
            C1A_margins.left(),
            C1A_margins.top(),
            C1A_margins.right(),
            0,
        )

        C1A_cont = QWidget(C1A)
        C1A_cont.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        C1A_cont_ly = QVBoxLayout(C1A_cont)
        C1A_cont_ly.setContentsMargins(0, 0, 0, 0)
        C1A_section_spacing = 3
        C1A_cont_ly.setSpacing(C1A_section_spacing)
        C1A.ly.addWidget(C1A_cont, 1)

        # --- Identificação do produto (B1.C1.A.1) ---
        self.C1A1 = Zone(
            "B1.C1.A.1",
            C1A_cont,
            flow="v",
            margins=4,
            spacing=C1A_section_spacing,
            level=C1A._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
        )
        C1A1_margins = self.C1A1.ly.contentsMargins()
        self.C1A1.ly.setContentsMargins(
            C1A1_margins.left(),
            C1A1_margins.top(),
            C1A1_margins.right(),
            0,
        )
        C1A_cont_ly.addWidget(self.C1A1, 0)

        C1A_cont_ly.addStretch(1)

        # --- Combos & PVP (B1.E1) ---
        self.E1 = Zone(
            "B1.E1",
            self.B1,
            flow="v",
            margins=4,
            spacing=2,
            level=self.C1._level,
            show_overlays=layout.DEV_OVERLAYS,
        )
        E1_margins = self.E1.ly.contentsMargins()
        self.E1.ly.setContentsMargins(
            E1_margins.left(),
            0,
            E1_margins.right(),
            0,
        )
        self.B1.ly.addWidget(self.E1, 0)

        # --- Família (B1.D1) ---
        self.D1 = Zone(
            "B1.D1",
            self.B1,
            flow="v",
            margins=4,
            spacing=2,
            level=self.C1._level,
            show_overlays=layout.DEV_OVERLAYS,
        )
        D1_margins = self.D1.ly.contentsMargins()
        self.D1.ly.setContentsMargins(
            D1_margins.left(),
            0,
            D1_margins.right(),
            0,
        )
        self.B1.ly.addWidget(self.D1, 0)

        self.edCodigo = QLineEdit()
        make_readonly_lineedit(self.edCodigo)
        self.edCodigo.setStyleSheet(FIELD_STYLE)
        self.edNome = QLineEdit()
        make_readonly_lineedit(self.edNome)
        self.edNome.setStyleSheet(FIELD_STYLE)
        label_col, field_col = self.C1A1.split_h((4, 8))
        label_col.apply_metadata(zone_type="coluna-legendas", widget_type="legenda")
        field_col.apply_metadata(zone_type="coluna-campos", widget_type="campo")
        field_col_margins = field_col.ly.contentsMargins()
        field_col.ly.setContentsMargins(
            3,
            field_col_margins.top(),
            3,
            field_col_margins.bottom(),
        )
        label_top, label_bottom = label_col.split_v((1, 1))
        for zone in (label_top, label_bottom):
            zone_margins = zone.ly.contentsMargins()
            zone.ly.setContentsMargins(
                0,
                zone_margins.top(),
                0,
                zone_margins.bottom(),
            )
        label_top.apply_metadata(
            zone_type="linha-legenda",
            widget_type="etiqueta-c",
            base_declarations=(
                "border-radius: 12px;\n",
                "padding: 6px;\n",
            ),
        )
        label_bottom.apply_metadata(
            zone_type="linha-legenda",
            widget_type="etiqueta-c",
            base_declarations=(
                "border-radius: 12px;\n",
                "padding: 6px;\n",
            ),
        )
        for zone in (label_top, label_bottom):
            zone.set_label_alignment(AlignmentVariant.RIGHT)
        field_top, field_bottom = field_col.split_v((1, 1))
        field_top.ly.setContentsMargins(0, 0, 0, 0)
        field_bottom.ly.setContentsMargins(0, 0, 0, 0)
        field_top.apply_metadata(zone_type="linha-campo", widget_type="campo")
        field_bottom.apply_metadata(zone_type="linha-campo", widget_type="campo")

        def _make_ident_label(zone: Zone, text: str, overlay: str) -> QLabel:
            display = overlay if zone._overlay_active and overlay else text
            lbl = QLabel(display, zone)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setProperty("userLabel", text)
            lbl.setProperty("devLabel", overlay)
            if zone._overlay_active and overlay:
                apply_overlay_label_style(lbl)
            else:
                lbl.setStyleSheet("")
            zone.ly.addWidget(lbl, 0, Qt.AlignLeft | Qt.AlignVCenter)
            label_col._labels.append(lbl)
            return lbl

        _make_ident_label(label_top, "Código:", "Produtos.Codigo")
        _make_ident_label(label_bottom, "Nome do Artigo:", "Produtos.Nome")
        label_col.set_label_alignment(AlignmentVariant.RIGHT)
        label_col.sync_label_widths()
        self._ident_label_zone = label_col

        for field in (self.edCodigo, self.edNome):
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        field_top.ly.addWidget(self.edCodigo, 0, Qt.AlignLeft)
        field_bottom.ly.addWidget(self.edNome, 0)

        codigo_aux_container = QWidget(self.B1A1AAA)
        codigo_aux_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        codigo_aux_layout = QVBoxLayout(codigo_aux_container)
        codigo_aux_layout.setContentsMargins(0, 0, 0, 0)
        codigo_aux_layout.setSpacing(self.B1A1AAA.ly.spacing())
        self.B1A1AAA.add(codigo_aux_container, 0)

        def _relocate_ident_row(label_zone: Zone, field_zone: Zone) -> None:
            row_container = QWidget(codigo_aux_container)
            row_container.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Fixed
            )
            row_layout = QHBoxLayout(row_container)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(self.B1A1AAA.ly.spacing())

            for zone, stretch in ((label_zone, 4), (field_zone, 8)):
                parent_widget = zone.parentWidget()
                parent_layout = parent_widget.layout() if parent_widget else None
                if parent_layout is not None:
                    parent_layout.removeWidget(zone)
                zone.setParent(row_container)
                row_layout.addWidget(zone, stretch)

            codigo_aux_layout.addWidget(row_container)

        _relocate_ident_row(label_top, field_top)
        _relocate_ident_row(label_bottom, field_bottom)

        scroll.verticalScrollBar().valueChanged.connect(
            self._toggle_header_on_scroll
        )
        self.edCodigo.textChanged.connect(self.headerEdCodigo.setText)
        self.edNome.textChanged.connect(self.headerEdNome.setText)

        # B1.A1.A.B — preview de imagem
        try:
            init_code = self.service.codigo_at(self.cur_index)
        except Exception:
            init_code = None
        self.image_preview = ImagePreview(init_code, self.service)
        self.B1A1AB.add(self.image_preview, 1)

        # ---------------- Família & Combos (B1.D1) ----------------
        D1_familias = Zone(
            "B1.D1.A",
            self.D1,
            flow="v",
            margins=(self.D1.margin_h, self.D1.margin_v),
            spacing=self.D1.ly.spacing(),
            level=self.D1._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
            base_style_label=self.D1.base_style_label,
        )
        D1_familias_margins = D1_familias.ly.contentsMargins()
        D1_familias.ly.setContentsMargins(
            D1_familias_margins.left(),
            0,
            D1_familias_margins.right(),
            0,
        )
        self.D1.add(D1_familias, 1)

        D1_familias_row_margin_value = 4
        D1_familias_row_spacing_value = 2
        D1_familias_row = Zone(
            "B1.D1.A.1",
            D1_familias,
            flow="v",
            margins=D1_familias_row_margin_value,
            spacing=D1_familias_row_spacing_value,
            level=D1_familias._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
        )
        D1_familias_row.ly.setContentsMargins(0, 0, 0, 0)
        D1_familias_row.set_zone_stylesheet(
            layout.compose_stylesheet(
                D1_familias_row,
                "font-size: 1px; margin: 0px; padding: 0px;",
            )
        )
        D1_familias_row.apply_overlays(True)
        D1_familias.add(D1_familias_row, 1)

        D1_familias_reserva = Zone(
            "B1.D1.A.3",
            D1_familias,
            flow="h",
            margins=D1_familias_row_margin_value,
            spacing=D1_familias_row_spacing_value,
            level=D1_familias_row._level,
            show_overlays=layout.DEV_OVERLAYS,
            base_style_label=D1_familias.base_style_label,
        )
        D1_familias_reserva.ly.setContentsMargins(0, 0, 0, 0)
        D1_familias_reserva.apply_overlays(layout.DEV_OVERLAYS)
        D1_familias_reserva.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        D1_familias.add(D1_familias_reserva, 2)

        combos_pvp_container = Zone(
            "B1.E1.A",
            self.E1,
            flow="v",
            margins=D1_familias_row_margin_value,
            spacing=D1_familias_row_spacing_value,
            level=self.E1._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
            widget_type="campo",
        )
        combos_pvp_container.ly.setContentsMargins(0, 0, 0, 0)
        combos_pvp_container.apply_overlays(layout.DEV_OVERLAYS)
        combos_pvp_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.E1.add(combos_pvp_container, 1)

        combos_section = QWidget(combos_pvp_container)
        combos_section.setObjectName("B1.E1.A.A")
        combos_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        combos_section_layout = QHBoxLayout(combos_section)
        combos_section_layout.setContentsMargins(0, 0, 0, 0)
        combos_section_layout.setSpacing(D1_familias_row_spacing_value)
        combos_pvp_container.add(combos_section, 0)

        pvps_section = Zone(
            "B1.E1.A.B",
            combos_pvp_container,
            flow="v",
            margins=D1_familias_row_margin_value,
            spacing=D1_familias_row_spacing_value,
            level=combos_pvp_container._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
            widget_type="campo",
        )
        pvps_section.apply_metadata(
            zone_type="secao-pvps",
            widget_type="campo",
            apply_base_style=False,
        )
        pvps_section.ly.setContentsMargins(0, 0, 0, 0)
        pvps_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        combos_pvp_container.add(pvps_section, 0)

        self.lbPVPs: list[QLineEdit] = []

        pvp_label = QLabel("PREÇOS DE VENDA", pvps_section)
        pvp_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        pvp_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        pvp_label.setStyleSheet("")
        match_font(pvp_label, self.edNome)
        pvps_section.add(pvp_label, 0)

        pvps_grid = Zone(
            "B1.E1.A.B.1",
            pvps_section,
            flow="h",
            margins=0,
            spacing=D1_familias_row_spacing_value,
            level=pvps_section._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
        )
        pvps_grid.ly.setContentsMargins(0, 0, 0, 0)
        pvps_grid.set_zone_stylesheet(
            layout.compose_stylesheet(
                pvps_grid,
                "font-size: 1px; margin: 0px; padding: 0px;",
            )
        )
        pvps_section.add(pvps_grid, 0)

        for idx in range(1, 6):
            column_zone = Zone(
                f"B1.E1.A.B.1.{idx}",
                pvps_grid,
                flow="v",
                margins=0,
                spacing=2,
                level=pvps_grid._level + 1,
                show_overlays=layout.DEV_OVERLAYS,
            )
            column_zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            column_zone.ly.setContentsMargins(0, 0, 0, 0)
            pvps_grid.add(column_zone, 1)

            legend_zone, field_zone = column_zone.split_v((1, 1))
            legend_zone.apply_metadata(
                zone_type="linha-legenda",
                widget_type="etiqueta-c",
                apply_base_style=False,
            )
            field_zone.apply_metadata(
                zone_type="linha-campo",
                widget_type="campo",
                apply_base_style=False,
            )
            field_zone.ly.setContentsMargins(0, 0, 0, 0)

            user_label = f"PVP #{idx}"
            dev_label = f"PrecosTaxas.Preco{idx}"
            display_label = (
                dev_label
                if legend_zone._overlay_active and layout.DEV_OVERLAYS
                else user_label
            )
            lbl = QLabel(display_label, legend_zone)
            lbl.setProperty("userLabel", user_label)
            lbl.setProperty("devLabel", dev_label)
            match_font(lbl, self.edNome)
            if legend_zone._overlay_active and layout.DEV_OVERLAYS:
                apply_overlay_label_style(lbl)
                lbl.setToolTip("")
            else:
                apply_label_style(lbl, alignment=AlignmentVariant.DEFAULT)
                lbl.setToolTip(f"{user_label} — {dev_label}")
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            legend_zone.add(lbl, 0)
            legend_zone._labels.append(lbl)

            val = QLineEdit("—", field_zone)
            val.setFont(self.edNome.font())
            make_readonly_lineedit(val)
            val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            val.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            field_zone.ly.addWidget(val, 0, Qt.AlignLeft | Qt.AlignVCenter)
            self.lbPVPs.append(val)

        family_labels_zone, family_values_zone = D1_familias_row.split_h((4, 8))
        familia_values_zone, subfamilia_values_zone = family_values_zone.split_v((1, 1))

        familia_label_zone, subfamilia_label_zone = family_labels_zone.split_v((1, 1))
        for zone in (familia_label_zone, subfamilia_label_zone):
            zone_margins = zone.ly.contentsMargins()
            zone.ly.setContentsMargins(
                0,
                zone_margins.top(),
                0,
                zone_margins.bottom(),
            )
        familia_label_zone.apply_metadata(
            zone_type="linha-legenda",
            widget_type="etiqueta-c",
        )
        subfamilia_label_zone.apply_metadata(
            zone_type="linha-legenda",
            widget_type="etiqueta-c",
        )
        family_labels_zone.set_label_alignment(AlignmentVariant.RIGHT)

        def _make_family_label(zone: Zone, text: str, overlay: str) -> QLabel:
            display = overlay if zone._overlay_active and overlay else text
            lbl = QLabel(display, zone)
            lbl.setProperty("userLabel", text)
            lbl.setProperty("devLabel", overlay)
            apply_label_style(lbl, alignment=AlignmentVariant.RIGHT)
            if zone._overlay_active and overlay:
                apply_overlay_label_style(lbl)
            zone.ly.addWidget(lbl, 0)
            zone._labels.append(lbl)
            family_labels_zone._labels.append(lbl)
            return lbl

        _make_family_label(familia_label_zone, "Família:", "Produtos.Familia")
        _make_family_label(
            subfamilia_label_zone, "Sub-família:", "Produtos.SubFamilia"
        )

        self.lbFamiliaVal = QLineEdit("")
        make_readonly_lineedit(self.lbFamiliaVal)
        self.lbFamiliaVal.setStyleSheet(FIELD_STYLE)
        self.lbFamiliaVal.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbFamiliaVal.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lbFamiliaVal.setFont(self.edNome.font())

        self.lbSubFamiliaVal = QLineEdit("")
        make_readonly_lineedit(self.lbSubFamiliaVal)
        self.lbSubFamiliaVal.setStyleSheet(FIELD_STYLE)
        self.lbSubFamiliaVal.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbSubFamiliaVal.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lbSubFamiliaVal.setFont(self.edNome.font())

        familia_values_zone.ly.addWidget(self.lbFamiliaVal, 0, Qt.AlignVCenter)
        subfamilia_values_zone.ly.addWidget(
            self.lbSubFamiliaVal, 0, Qt.AlignVCenter
        )

        self._family_label_zone = family_labels_zone
        self._refresh_family_label_column_widths()

        combo_zone_specs = (
            ("B1.E1.A.A.1", "Tipos Artigos", "cbTipos"),
            ("B1.E1.A.A.2", "Validade", "cbValidade"),
            ("B1.E1.A.A.3", "Temperaturas", "cbTemp"),
        )
        for tag_prefix, label_text, attr_name in combo_zone_specs:
            column_widget = QWidget(combos_section)
            column_widget.setObjectName(tag_prefix)
            column_widget.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Preferred
            )
            column_layout = QVBoxLayout(column_widget)
            column_layout.setContentsMargins(0, 0, 0, 0)
            column_layout.setSpacing(2)
            combos_section_layout.addWidget(column_widget, 1)

            label = QLabel(label_text, column_widget)
            label.setProperty("userLabel", label_text)
            label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            apply_label_style(label)
            column_layout.addWidget(label, 0)

            combo = QComboBox(column_widget)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo.setStyleSheet(FIELD_STYLE)
            column_layout.addWidget(combo, 0)
            setattr(self, attr_name, combo)

        self.cbTipos: QComboBox
        self.cbValidade: QComboBox
        self.cbTemp: QComboBox
        self.cbTipos.currentIndexChanged.connect(self._on_tipo_artigo_changed)
        self.cbValidade.currentIndexChanged.connect(self._on_validade_changed)
        self.cbTemp.currentIndexChanged.connect(self._on_temperatura_changed)

        # ---------------- B5 — FOOD COST (B5.C1) ----------------
        self.C5 = Zone(
            "B5.C1",
            self,
            flow="v",
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
        )
        page_ly.addWidget(self._section_box("[B5] - FOOD COST", self.C5), 0)

        C5A = Zone(
            "B5.C1.A",
            self.C5,
            flow="v",
            level=1,
            show_overlays=layout.DEV_OVERLAYS,
        )
        self.C5.add(C5A, 1)
        C5AA = Zone(
            "B5.C1.A.A",
            C5A,
            flow="h",
            level=2,
            show_overlays=layout.DEV_OVERLAYS,
        )
        C5AA.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        C5A.add(C5AA, 0)
        fc1, fc2, fc3, fc4, fc5 = C5AA.split_h((1, 1, 1, 1, 1))

        self.lbFoodCosts: list[QLineEdit] = []
        for idx, fc in enumerate((fc1, fc2, fc3, fc4, fc5), start=1):
            label_zone, field_zone = fc.split_v((1, 1))
            label_zone.apply_metadata(
                zone_type="linha-legenda",
                widget_type="etiqueta-c",
            )
            field_zone.apply_metadata(
                zone_type="linha-campo",
                widget_type="campo",
            )

            user_label = f"Food Cost #{idx}"
            dev_label = f"FoodCost.Nivel{idx}"
            display_label = dev_label if label_zone._overlay_active else user_label
            lbl = QLabel(display_label, label_zone)
            lbl.setProperty("userLabel", user_label)
            lbl.setProperty("devLabel", dev_label)
            label_zone.add(lbl, 0)
            label_zone._labels.append(lbl)
            apply_label_style(lbl, alignment=AlignmentVariant.DEFAULT)
            if label_zone._overlay_active and layout.DEV_OVERLAYS:
                apply_overlay_label_style(lbl)
                lbl.setToolTip("")
            else:
                lbl.setToolTip(f"{user_label} — {dev_label}")

            val = QLineEdit("—", field_zone)
            make_readonly_lineedit(val)
            val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            val.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            field_zone.ly.addWidget(val, 0, Qt.AlignLeft | Qt.AlignVCenter)
            self.lbFoodCosts.append(val)

        C5AB = Zone(
            "B5.C1.A.B",
            C5A,
            flow="h",
            level=2,
            show_overlays=layout.DEV_OVERLAYS,
        )
        C5AB.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        C5A.add(C5AB, 0)
        fcB1, fcB2, fcB3, fcB4, fcB5 = C5AB.split_h((1, 1, 1, 1, 1))

        level_comments: dict[str, str] = {}
        repo = getattr(self.ds, "fcost", None)

        def _row_value(row, key, index):
            try:
                return row[key]
            except (TypeError, KeyError, IndexError):
                try:
                    return row[index]
                except (TypeError, IndexError):
                    return None

        if repo is not None:
            try:
                for level in repo.list_levels():
                    nome = _row_value(level, "Nome", 1)
                    comentario = _row_value(level, "Comentario", 4) or ""
                    if nome:
                        level_comments[str(nome)] = comentario
            except Exception:
                logger.exception(
                    "[FTApp] Falha a obter comentários de Food Cost ao preparar botões."
                )

        self.btFcostBom = QPushButton("Bom")
        self.btFcostBom.setCheckable(True)
        apply_fcfilter_btn_style(self.btFcostBom, (198, 216, 112))
        fcB2.add(self.btFcostBom, 0)

        self.btFcostAceitavel = QPushButton("Aceitável")
        self.btFcostAceitavel.setCheckable(True)
        apply_fcfilter_btn_style(self.btFcostAceitavel, (248, 222, 126))
        fcB3.add(self.btFcostAceitavel, 0)

        self.btFcostMau = QPushButton("Mau")
        self.btFcostMau.setCheckable(True)
        apply_fcfilter_btn_style(self.btFcostMau, (255, 158, 145))
        fcB4.add(self.btFcostMau, 0)

        self.btFcostReset = QPushButton("Todos")
        self.btFcostReset.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(200,200,200,0.5);
                border: 1px solid rgba(0,0,0,0.3);
                border-top-color: rgba(255,255,255,0.8);
                border-left-color: rgba(255,255,255,0.8);
                border-bottom-color: rgba(0,0,0,0.4);
                border-right-color: rgba(0,0,0,0.4);
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton:pressed {
                background-color: rgba(200,200,200,0.8);
            }
            """
        )
        fcB5.add(self.btFcostReset, 0)

        self.fcostFilterGroup = QButtonGroup(self)
        self.fcostFilterGroup.setExclusive(True)
        self.fcostFilterGroup.addButton(self.btFcostBom, 1)
        self.fcostFilterGroup.addButton(self.btFcostAceitavel, 2)
        self.fcostFilterGroup.addButton(self.btFcostMau, 3)
        self.fcostFilterGroup.buttonClicked[int].connect(
            self._on_fcost_filter_selected
        )
        self.btFcostReset.clicked.connect(self._on_fcost_filter_reset)

        self._fcost_tooltip_entries = [
            (
                self.btFcostBom,
                fcB2,
                level_comments.get("Bom", ""),
            ),
            (
                self.btFcostAceitavel,
                fcB3,
                level_comments.get("Aceitável", ""),
            ),
            (
                self.btFcostMau,
                fcB4,
                level_comments.get("Mau", ""),
            ),
            (
                self.btFcostReset,
                fcB5,
                "Remover filtro e mostrar todos os níveis",
            ),
        ]
        self._refresh_fcost_tooltips()

        # ---------------- B4 — Ficha Técnica (B4.C1) ----------------
        self.C4 = Zone(
            "B4.C1",
            self,
            flow="v",
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
        )
        page_ly.addWidget(self._section_box("[B4] - FICHA TÉCNICA", self.C4), 0)

        C4_ing_zone, C4_totals_zone = self.C4.split_v((1, 0))
        C4_ing_zone.apply_metadata(
            zone_type="secao-tabela-ingredientes",
            widget_type="tabela",
        )

        self.ingModel = build_fichas_tecnicas_model(
            [], overlays=layout.DEV_OVERLAYS
        )

        self.tbIng = QTableView(self)
        self.tbIng.setModel(self.ingModel)
        self.tbIng.verticalHeader().setVisible(False)
        self.tbIng.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tbIng.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tbIng.setViewportMargins(0, 0, 0, 4)
        self.tbIng.setFrameShape(QFrame.NoFrame)
        self.tbIng.setShowGrid(False)
        self.tbIng.setStyleSheet(
            "\n".join(
                (
                    "QTableView {",
                    "    border: none;",
                    "    background-color: transparent;",
                    "    alternate-background-color: transparent;",
                    "}",
                    "QTableView::item {",
                    "    margin: 0;",
                    "    padding: 0;",
                    "    border: none;",
                    "    border-bottom: 1px solid #000000;",
                    "}",
                    "QTableView::item:hover {",
                    "    background-color: rgba(11, 99, 206, 0.08);",
                    "}",
                )
            )
        )
        hh = self.tbIng.horizontalHeader()
        hh.setStyleSheet(
            """
            QHeaderView {
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: rgba(200, 200, 200, 0.5);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-top-color: rgba(255, 255, 255, 0.8);
                border-left-color: rgba(255, 255, 255, 0.8);
                border-bottom-color: rgba(0, 0, 0, 0.4);
                border-right-color: rgba(0, 0, 0, 0.4);
                border-radius: 6px;
                padding: 4px;
            }
            QHeaderView::section:pressed {
                background-color: rgba(200, 200, 200, 0.8);
            }
            """
        )
        hh.setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        vh = self.tbIng.verticalHeader()
        header_h = hh.height() or hh.minimumSectionSize()
        initial_h = header_h + vh.defaultSectionSize() + self.tbIng.frameWidth() * 2
        self.tbIng.setFixedHeight(initial_h)
        self.tbIng.setEditTriggers(QTableView.DoubleClicked | QTableView.EditKeyPressed)
        C4_ing_zone.add(self.tbIng, 1)
        nome_font = QFont(self.edNome.font())
        nome_point_size_f = nome_font.pointSizeF()
        if nome_point_size_f > 0:
            nome_font.setPointSizeF(nome_point_size_f * 2)
        else:
            nome_point_size = nome_font.pointSize()
            if nome_point_size > 0:
                nome_font.setPointSize(nome_point_size * 2)
        self.edNome.setFont(nome_font)
        self.edNome.setFixedHeight(self.edNome.sizeHint().height())
        self.edNome.updateGeometry()

        header_nome_font = QFont(self.headerEdNome.font())
        header_point_size_f = header_nome_font.pointSizeF()
        if header_point_size_f > 0:
            header_nome_font.setPointSizeF(header_point_size_f * 2)
        else:
            header_point_size = header_nome_font.pointSize()
            if header_point_size > 0:
                header_nome_font.setPointSize(header_point_size * 2)
        self.headerEdNome.setFont(header_nome_font)
        self.headerEdNome.setFixedHeight(self.headerEdNome.sizeHint().height())
        self.headerEdNome.updateGeometry()

        self._setup_ing_columns()

        # Zona para custos totais após a tabela de ingredientes
        self.C4Custo = Zone(
            f"{C4_totals_zone.tag}.A",
            C4_totals_zone,
            flow="h",
            level=C4_totals_zone._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
            widget_type="campo",
        )
        self.C4Custo.apply_metadata(
            zone_type="barra-totais",
            widget_type="campo",
        )
        self.C4Custo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        C4_totals_zone.add(self.C4Custo, 0)
        self.C4Custo.ly.addStretch(1)
        custo_total_label = QLabel("Custo Total:")
        apply_label_style(custo_total_label)
        self.C4Custo.add(custo_total_label, 0)
        self.edCustoTotal = QLineEdit()
        make_readonly_lineedit(self.edCustoTotal)
        self.edCustoTotal.setStyleSheet(FIELD_STYLE)
        self.edCustoTotal.setFixedWidth(self.edCustoTotal.sizeHint().width() * 2)
        self.C4Custo.add(self.edCustoTotal, 0)

        # ---------------- B6 — PREPARAÇÃO (B6.C1) ----------------
        self.C6 = Zone(
            "B6.C1",
            self,
            flow="v",
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
        )
        page_ly.addWidget(self._section_box("[B6] - PREPARAÇÃO", self.C6), 1)

        C6_text, C6_gallery = self.C6.split_v((3, 2))
        C6_text.apply_metadata(
            zone_type="secao-texto-preparacao",
            widget_type="editor",
        )
        C6_gallery.apply_overlays(layout.DEV_OVERLAYS)

        self.prep_previews: list[PrepImagePreview] = []
        gallery_slots = C6_gallery.split_h((1, 1, 1, 1))
        for slot in gallery_slots:
            slot.apply_metadata(zone_type="slot-preparacao", widget_type="etiqueta-c")
        for idx, slot in enumerate(gallery_slots, start=1):
            preview = PrepImagePreview(idx, self.service)
            slot.add(preview, 1)
            self.prep_previews.append(preview)

        try:
            init_code_imgs = self.service.codigo_at(self.cur_index)
        except Exception:
            init_code_imgs = None
        if init_code_imgs:
            for pv in self.prep_previews:
                pv.load_image(init_code_imgs)

        # Toolbar de formatação
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        reset_style = self.btFcostReset.styleSheet()
        if reset_style:
            toolbar.setStyleSheet(reset_style.replace("QPushButton", "QToolButton"))
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

        for action in toolbar.actions():
            button = toolbar.widgetForAction(action)
            if isinstance(button, QToolButton):
                button.setAutoRaise(False)
                button.setToolButtonStyle(Qt.ToolButtonTextOnly)
                button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
                button.setMinimumWidth(button.sizeHint().width())

        C6_text.add(toolbar, 0)

        self.edPrep = QTextEdit()
        self.edPrep.setAcceptRichText(True)
        self.edPrep.setWordWrapMode(QTextOption.WordWrap)
        self.edPrep.setTabChangesFocus(False)
        self.edPrep.setUndoRedoEnabled(True)
        self.edPrep.setLineWrapMode(QTextEdit.WidgetWidth)
        self.edPrep.document().setDefaultStyleSheet("img { max-width:100%; }")
        self.edPrep.setPlaceholderText("— Texto de preparação —")
        self.edPrep.textChanged.connect(self._on_prep_changed)
        C6_text.add(self.edPrep, 1)

        # ---------------- B7 — NUTRIÇÃO / ALERGÉNIOS (B7.C1) ----------------
        self.B7_C1 = Zone(
            "B7.C1",
            self,
            flow="v",
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
            widget_type="caixa de seleção",
        )
        # ``self.C7`` is kept for backward compatibility with legacy code.
        self.C7 = self.B7_C1

        self.B7_C1.apply_metadata(
            zone_type="bloco-alergenios",
            widget_type="caixa de seleção",
        )
        page_ly.addWidget(
            self._section_box("[B7] - NUTRIÇÃO / ALERGÉNIOS", self.B7_C1),
            0,
        )

        self._build_allergens_grid()

        # --- Rodapé: navegação centrada + contador ---
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(8)
        footer.addStretch(1)
        self.btFirst = QPushButton("◀◀ Primeiro")
        self.btPrev = QPushButton("◀ Anterior")
        self.lbPos = QLabel("1 / 1")
        apply_label_style(self.lbPos)
        self.btNext = QPushButton("Seguinte ▶")
        self.btLast = QPushButton("Último ▶▶")
        footer.addWidget(self.btFirst)
        footer.addWidget(self.btPrev)
        footer.addWidget(self.lbPos)
        footer.addWidget(self.btNext)
        footer.addWidget(self.btLast)
        footer.addStretch(1)
        root.addLayout(footer)

        self._toggle_header_on_scroll(self.scroll.verticalScrollBar().value())

        # Atalho teclado para overlays
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self._toggle_overlays)
        QShortcut(
            QKeySequence("Ctrl+S"), self, activated=lambda: self._save_prep(force=True)
        )


    def _toggle_header_on_scroll(self, value: int):
        header = getattr(self, "header", None)
        zone = getattr(self, "C1A1", None)
        if not header or not getattr(self, "scroll", None) or zone is None:
            return
        viewport = self.scroll.viewport()
        top_left = zone.mapTo(viewport, QPoint(0, 0))
        should_show = top_left.y() < 0
        if should_show and not header.isVisible():
            header.show()
        elif not should_show and header.isVisible():
            header.hide()

    # ---------- Alergénios grid ----------
    def _build_allergens_grid(self):
        names = self.service.list_active_allergens()
        gridw = QWidget()
        grid = QGridLayout(gridw)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        cols = 3
        details_getter = getattr(self.service, "get_allergen_details", None)

        checkboxes: dict[int, QCheckBox] = {}
        tooltips: dict[int, str] = {}

        def _extract(values, key, idx):
            if isinstance(values, dict):
                return values.get(key)
            if isinstance(values, (list, tuple)):
                try:
                    return values[idx]
                except IndexError:
                    return None
            attr = getattr(values, key, None)
            if attr is None:
                attr = getattr(values, key.lower(), None)
            return attr

        def _parse_examples(raw):
            if raw in (None, ""):
                return ""
            parsed = raw
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                except (TypeError, ValueError, json.JSONDecodeError):
                    parsed = raw
            if isinstance(parsed, list):
                items = [str(item).strip() for item in parsed if str(item).strip()]
                return ", ".join(items)
            if isinstance(parsed, dict):
                items = [
                    str(value).strip()
                    for value in parsed.values()
                    if str(value).strip()
                ]
                return ", ".join(items)
            return str(parsed).strip()

        for i, (aid, nome) in enumerate(names):
            r = i // cols
            c = i % cols
            try:
                key = int(aid)
            except (TypeError, ValueError):
                continue
            cb = QCheckBox(nome)
            details = {}
            if callable(details_getter):
                try:
                    details = details_getter(aid) or {}
                except Exception:
                    details = {}
            exemplos_raw = _extract(details, "Exemplos", 0)
            notas_raw = _extract(details, "Notas", 1)
            tooltip_parts: list[str] = []
            exemplos_txt = _parse_examples(exemplos_raw)
            if exemplos_txt:
                tooltip_parts.append(exemplos_txt)
            if notas_raw not in (None, ""):
                notas_txt = str(notas_raw).strip()
                if notas_txt:
                    tooltip_parts.append(notas_txt)
            tooltip_text = "\n".join(tooltip_parts) if tooltip_parts else ""
            tooltips[key] = tooltip_text
            cb.stateChanged.connect(
                lambda state, key=key: self._on_allergen_state_changed(key, state)
            )
            grid.addWidget(cb, r, c, alignment=Qt.AlignLeft)
            checkboxes[key] = cb
        zone = getattr(self, "B7_C1", None)
        if zone is None:
            zone = getattr(self, "C7", None)
        if zone is None:  # pragma: no cover - defensive guard
            return
        zone.add(gridw, 0)
        self._allergen_checkboxes = checkboxes
        self._allergen_tooltips = tooltips
        self._allergen_zone = zone
        self._refresh_allergen_tooltips()

    # ---------- Ficha Técnica: colunas ----------
    def _collect_selected_allergens(self) -> list[int]:
        boxes = getattr(self, "_allergen_checkboxes", None)
        if not boxes:
            return []
        return [aid for aid, cb in boxes.items() if cb.isChecked()]

    def _apply_allergen_selection(self, allergen_ids):
        boxes = getattr(self, "_allergen_checkboxes", None)
        if not boxes:
            return
        selected: set[int] = set()
        if allergen_ids:
            for aid in allergen_ids:
                try:
                    selected.add(int(aid))
                except (TypeError, ValueError):
                    continue
        for aid, cb in boxes.items():
            prev = cb.blockSignals(True)
            cb.setChecked(aid in selected)
            cb.blockSignals(prev)

    def _on_allergen_state_changed(self, aid: int, _state: int):
        if getattr(self, "_loading", False):
            return
        codigo = getattr(self.current_product, "code", None)
        if not codigo:
            return
        try:
            selected = self._collect_selected_allergens()
            self.service.set_product_allergens(codigo, selected)
        except Exception:
            logger.exception(
                "[FTApp] Falha ao atualizar alergénios do produto %s", codigo
            )

    def _setup_ing_columns(self):
        w = self.tbIng.viewport().width()
        model = self.tbIng.model()
        if not model:
            return
        self.tbIng.setColumnWidth(0, int(w * 0.52))
        self.tbIng.setColumnWidth(1, int(w * 0.08))
        self.tbIng.setColumnWidth(2, int(w * 0.125))
        self.tbIng.setColumnWidth(3, int(w * 0.15))
        self.tbIng.setColumnWidth(4, int(w * 0.125))
        self.tbIng.horizontalHeader().setDefaultAlignment(
            Qt.AlignHCenter | Qt.AlignVCenter
        )

    def _apply_ingredient_widths(self):
        self._setup_ing_columns()

    def _apply_ing_autofit_or_scroll(self):
        vh = self.tbIng.verticalHeader()
        hh = self.tbIng.horizontalHeader()
        rows = self.tbIng.model().rowCount()
        row_h = vh.defaultSectionSize()
        max_visible = 5
        visible_rows = min(rows, max_visible)
        total_h = hh.height() + row_h * visible_rows + self.tbIng.frameWidth() * 2
        total_h += self.tbIng.horizontalScrollBar().height()
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

    def _update_page_width(self):
        """Ensure scroll page matches viewport width to avoid horizontal bars."""
        if hasattr(self, "scroll") and hasattr(self, "page"):
            self.page.setMinimumWidth(self.scroll.viewport().width())

    def _refresh_family_label_column_widths(self) -> None:
        """Keep identification/family label columns aligned and resizable."""

        label_col = getattr(self, "_ident_label_zone", None)
        family_col = getattr(self, "_family_label_zone", None)
        if label_col is None or family_col is None:
            return

        zones = (label_col, family_col)
        all_labels = list(
            itertools.chain.from_iterable(zone._labels for zone in zones)  # type: ignore[attr-defined]
        )
        if not all_labels:
            return

        for zone in zones:
            zone.setMinimumWidth(0)
            zone.setMaximumWidth(QWIDGETSIZE_MAX)
            zone.updateGeometry()

        for lbl in all_labels:
            lbl.setMinimumWidth(0)
            lbl.setMaximumWidth(QWIDGETSIZE_MAX)
            lbl.updateGeometry()

        shared_label_width = max((lbl.sizeHint().width() for lbl in all_labels), default=0)

        overhead_by_zone: dict[Zone, int] = {}
        for lbl in all_labels:
            parent_zone = lbl.parentWidget()
            if isinstance(parent_zone, Zone):
                overhead = max(
                    0, parent_zone.sizeHint().width() - lbl.sizeHint().width()
                )
                overhead_by_zone[parent_zone] = max(
                    overhead_by_zone.get(parent_zone, 0), overhead
                )

        max_overhead = max(overhead_by_zone.values(), default=0)
        shared_zone_width = shared_label_width + max_overhead

        for lbl in all_labels:
            lbl.setMinimumWidth(shared_label_width)
            lbl.setMaximumWidth(QWIDGETSIZE_MAX)
            lbl.updateGeometry()

        for zone in zones:
            zone.setMinimumWidth(shared_zone_width)
            zone.setMaximumWidth(QWIDGETSIZE_MAX)
            zone.updateGeometry()

        layout_root = self.layout()
        if layout_root is not None:
            layout_root.activate()

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
            "p": set(),
            "span": set(),
            "li": set(),
        }

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
                        continue
                    if attr_l in allowed_attrs.get(tag, set()):
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
                logger.exception(
                    "[Preparacao] failed to save preparation HTML for %s", codigo
                )
        else:
            try:
                self.ds.save_preparacao_html(codigo, "")
            except Exception:
                logger.exception(
                    "[Preparacao] failed to clear preparation HTML for %s", codigo
                )
        self._prep_dirty = False

    # ---------- Navegação ----------
    def _toggle_search_panel(self, checked: bool | None = None):
        desired = bool(checked) if checked is not None else not self.searchContainer.isVisible()
        self.searchContainer.setVisible(desired)
        if self.btSearchToggle.isChecked() != desired:
            self.btSearchToggle.blockSignals(True)
            self.btSearchToggle.setChecked(desired)
            self.btSearchToggle.blockSignals(False)
        if desired:
            self.searchProductField.setFocus(Qt.TabFocusReason)

    def _apply_search_filters(self):
        product_name = (self.searchProductField.text() or "").strip() or None
        ingredient_name = (self.searchIngredientField.text() or "").strip() or None
        setter = getattr(self.service, "set_search_filters", None)
        if callable(setter):
            setter(produto=product_name, ingrediente=ingredient_name)
        self.cur_index = 0
        self._load_record(0)

    def _reset_search_filters(self):
        self.searchProductField.clear()
        self.searchIngredientField.clear()
        setter = getattr(self.service, "set_search_filters", None)
        if callable(setter):
            setter(produto=None, ingrediente=None)
        self.cur_index = 0
        self._load_record(0)

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
            self._apply_allergen_selection([])
            product = self.service.get_product_info(codigo)
            self.current_product = product

            self.edCodigo.setText(product.code or "")
            self.edNome.setText(product.name or "")
            self.lbFamiliaVal.setText(product.familia or "")
            self.lbSubFamiliaVal.setText(product.subfamilia or "")

            pvps = list(product.pvps or [])
            pvps.extend([None] * (5 - len(pvps)))
            for lbl, price in zip(self.lbPVPs, pvps):
                lbl.setText(
                    "--N/A--" if price in (None, 0) else format_pt_number(price)
                )

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
            update_fichas_tecnicas_model(
                self.ingModel, fichas, overlays=layout.DEV_OVERLAYS
            )
            self._apply_ingredient_widths()
            self._apply_ing_autofit_or_scroll()

            self.edCustoTotal.setText(
                format_pt_number(self.service.calculate_cost(product))
            )
            self._update_food_costs()
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
                allergens = self.service.get_product_allergens(codigo) or []
            except Exception:
                logger.exception(
                    "[FTApp] Falha ao obter alergénios do produto %s", codigo
                )
                allergens = []
            self._apply_allergen_selection(allergens)

            try:
                cbs = (self.cbTipos, self.cbValidade, self.cbTemp)
                self._aux_fetch_lists(cbs)
                _select_by_code(self.cbTipos, product.tipo_artigo_cod)
                _select_by_code(self.cbValidade, product.validade_cod)
                _select_by_code(self.cbTemp, product.temperatura_cod)
            except Exception as e:
                logger.exception("[AuxCanon][ERRO] %s", e)
            try:
                self.image_preview.load_image(codigo)
            except Exception as e:
                logger.exception("[ImagePreview] %s", e)
            for pv in getattr(self, "prep_previews", []):
                try:
                    pv.load_image(codigo)
                except Exception as e:
                    logger.exception("[PrepImagePreview] %s", e)
        finally:
            self._loading = False

    # ---------- Cálculos ----------
    def _update_food_costs(self):
        """Update food cost percentage labels based on current product."""
        product = getattr(self, "current_product", None)
        if not product:
            return
        identifier = (
            getattr(product, "code", None)
            or getattr(product, "name", "<unknown>")
        )
        try:
            total = parse_decimal(self.edCustoTotal.text())
            total = float(total)
        except (TypeError, ValueError) as exc:
            logger.warning("[FoodCost] invalid total for %s: %s", identifier, exc)
            total = None
        pvps = list(getattr(product, "pvps", []) or [])
        pvps.extend([None] * (5 - len(pvps)))
        iva = getattr(product, "iva", None)
        for idx, (lbl, pvp) in enumerate(zip(self.lbFoodCosts, pvps)):
            if pvp in (None, 0):
                lbl.setText("--N/A--")
                if idx == 0:
                    logger.warning(
                        "[FoodCost] missing pvp for %s (pvp=%s)",
                        identifier,
                        pvp,
                    )
                continue
            if iva in (None, 0):
                logger.warning(
                    "[FoodCost] missing Iva1 for %s (iva=%s)",
                    identifier,
                    iva,
                )
                lbl.setText("--")
                continue
            pct = calculate_food_cost(total, pvp, iva, identifier)
            if pct is None:
                logger.warning(
                    "[FoodCost] could not compute percentage for %s "
                    "(total=%s, pvp=%s, iva=%s)",
                    identifier,
                    total,
                    pvp,
                    iva,
                )
                lbl.setText("--N/A--")
            else:
                lbl.setText(format_pt_number(pct))

    def _update_costs_from_table(self):
        """Recalculate total cost using the service layer."""
        try:
            total = self.service.calculate_cost(self.current_product)
            self.edCustoTotal.setText(format_pt_number(total))
            self._update_food_costs()
        except Exception:
            pass

    def _on_fcost_filter_selected(self, level: int):
        if getattr(self, "_active_fcost_filter", None) == level:
            self._on_fcost_filter_reset()
            return
        self._active_fcost_filter = level
        try:
            self.service.ds.set_fcost_level(level)
        except Exception:
            logger.exception(
                "[FoodCost] failed to apply cost filter level %s", level
            )
        self.cur_index = 0
        self._load_record(0)

    def _on_fcost_filter_reset(self):
        self._active_fcost_filter = None
        try:
            self.service.ds.set_fcost_level(None)
        except Exception:
            logger.exception("[FoodCost] failed to reset cost filter")
        group = getattr(self, "fcostFilterGroup", None)
        if group:
            group.blockSignals(True)
            try:
                group.setExclusive(False)
                self.btFcostBom.setChecked(False)
                self.btFcostAceitavel.setChecked(False)
                self.btFcostMau.setChecked(False)
            finally:
                group.setExclusive(True)
                group.blockSignals(False)
        self.cur_index = 0
        self._load_record(0)

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
    def showEvent(self, ev):
        super().showEvent(ev)
        QTimer.singleShot(0, self._apply_ingredient_widths)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._update_page_width()
        self._apply_ingredient_widths()
        self._apply_prep_autofit_or_scroll()

    def _is_header_widget(self, widget) -> bool:
        """Return ``True`` if ``widget`` belongs to the floating header."""

        header = getattr(self, "header", None)
        if not header or widget is None:
            return False
        current = widget
        while current is not None:
            if current is header:
                return True
            parent_fn = getattr(current, "parentWidget", None)
            if not callable(parent_fn):
                break
            current = parent_fn()
        return False

    def _iter_layout_children(self, widget_type, *, include_header: bool = False):
        """Yield child widgets that belong to the printable ``self.page``.

        The floating header duplicates elements from ``self.page``. To avoid
        listing these widgets twice in exports or reports we keep it excluded by
        default. Pass ``include_header=True`` for operations (like toggling
        overlays) that must update both regions.
        """

        page = getattr(self, "page", None)
        if page is not None:
            yield from page.findChildren(widget_type)
        if include_header:
            header = getattr(self, "header", None)
            if header is not None:
                yield from header.findChildren(widget_type)

    def _refresh_fcost_tooltips(self) -> None:
        """Update Food Cost filter tooltips according to overlay state."""

        entries = getattr(self, "_fcost_tooltip_entries", None)
        if not entries:
            return

        overlays_enabled = bool(layout.DEV_OVERLAYS)
        for button, zone, tooltip_text in entries:
            if button is None:
                continue
            zone_overlay_active = bool(getattr(zone, "_overlay_active", False))
            if overlays_enabled and zone_overlay_active:
                button.setToolTip("")
            else:
                button.setToolTip(tooltip_text or "")

    def _refresh_allergen_tooltips(self) -> None:
        """Restore or clear allergen tooltips based on overlay state."""

        checkboxes = getattr(self, "_allergen_checkboxes", None)
        tooltips = getattr(self, "_allergen_tooltips", None)
        if not checkboxes or tooltips is None:
            return

        zone = getattr(self, "_allergen_zone", None)
        zone_overlay_active = bool(getattr(zone, "_overlay_active", False))
        overlays_enabled = bool(layout.DEV_OVERLAYS)
        show_tooltips = not overlays_enabled and not zone_overlay_active

        for aid, checkbox in checkboxes.items():
            if checkbox is None:
                continue
            tooltip_text = tooltips.get(aid, "") if show_tooltips else ""
            checkbox.setToolTip(tooltip_text)

    def _toggle_overlays(self):
        layout.DEV_OVERLAYS = not layout.DEV_OVERLAYS
        if hasattr(self, "searchContainer") and isinstance(self.searchContainer, Zone):
            self.searchContainer.apply_overlays(layout.DEV_OVERLAYS)
            for zone in (
                getattr(self, "searchLeftZone", None),
                getattr(self, "searchCenterZone", None),
                getattr(self, "searchRightZone", None),
            ):
                if isinstance(zone, Zone):
                    zone.apply_overlays(layout.DEV_OVERLAYS)
        for z in self._iter_layout_children(Zone, include_header=True):
            if z.tag.count(".") == 1 and layout.validate_tag(z.tag):
                z.apply_overlays(layout.DEV_OVERLAYS)
        for lbl in self._iter_layout_children(QLabel, include_header=True):
            user_lbl = lbl.property("userLabel")
            dev_lbl = lbl.property("devLabel")
            if user_lbl is not None and dev_lbl is not None:
                lbl.setText(dev_lbl if layout.DEV_OVERLAYS else user_lbl)
        for box in self._iter_layout_children(QGroupBox, include_header=True):
            user_title = box.property("userTitle")
            dev_title = box.property("devTitle")
            header = getattr(box, "_section_header", None)
            if (
                header is not None
                and isinstance(header, QLabel)
                and user_title is not None
                and dev_title is not None
            ):
                header.setText(dev_title if layout.DEV_OVERLAYS else user_title)
            elif user_title is not None and dev_title is not None:
                box.setTitle(dev_title if layout.DEV_OVERLAYS else user_title)
                layout.refresh_style(box)
        apply_fichas_tecnicas_headers(
            self.ingModel, overlays=layout.DEV_OVERLAYS
        )
        self._refresh_family_label_column_widths()
        self._refresh_fcost_tooltips()
        self._refresh_allergen_tooltips()

    def _toggle_overlays_btn(self):
        self._toggle_overlays()
        self.btOverlay.setText(f"Overlays: {'ON' if layout.DEV_OVERLAYS else 'OFF'}")

    def _after_restore(self):
        """Refresh UI state after a database restore."""
        try:
            self._aux_refresh_lists()
        except Exception:
            logger.exception("[Restore] failed to refresh auxiliary lists")
        try:
            self._load_record(getattr(self, "cur_index", 0))
        except Exception:
            logger.exception("[Restore] failed to reload current record")

    # ================== AUXILIARES — CANÓNICO (v2) ==================
    def _aux_fetch_lists(self, cbs=None):
        """Fetch auxiliary lists via the service layer and populate combo boxes."""

        lists = {"tipo_artigo": [], "validade": [], "temperatura": []}

        required_methods = (
            "list_tipos_artigos",
            "list_validade",
            "list_temperaturas",
        )
        missing = sorted(
            name for name in required_methods if not hasattr(self.service, name)
        )
        if missing:
            svc_name = type(self.service).__name__
            missing_fmt = ", ".join(missing)
            raise AttributeError(
                f"{svc_name} is missing required auxiliary list method(s): {missing_fmt}"
            )

        lists["tipo_artigo"] = self.service.list_tipos_artigos()
        lists["validade"] = self.service.list_validade()
        lists["temperatura"] = self.service.list_temperaturas()

        self._aux_populate_cbs(lists, cbs)
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
                for cb in self._iter_layout_children(QComboBox):
                    if self._is_header_widget(cb):
                        continue
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


def main() -> int:
    ds = DataStore()
    svc = ProductService(ds)

    from .app_launcher import launch_ftv_app

    return launch_ftv_app(svc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
