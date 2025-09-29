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
#    - Célula raiz do bloco: Bn.C1 (ex.: B4.C1, B5.C1) ou sub-blocos como B1.A1.
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
# 2025-09-23 18:23 — v3.110 — Menu de impressão dedicado com atalhos para
#    relatórios de FT's Gestão e Operacionais.
# 2025-09-21 11:20 — v3.108 — Inserida célula reservada B1.A1.A.2 e
#    realinhados os separadores auxiliares para corresponder à nomenclatura.
# 2025-09-21 14:45 — v3.109 — Família/Sub-família e combos passam para
#    B1.A1.A.2.*, mantendo B1.A1.A.3 como placeholder reservado.
# 2025-09-21 10:30 — v3.107 — Slot reservado removido; combos de família
#    reposicionados para B1.A1.A.B com grelha horizontal partilhada.
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
#    B1.A1 inicia após cabeçalho.
# 2025-09-18 01:41 — v3.99 — Títulos das secções regressam ao peso
#    normal e alinhamentos ajustados para legibilidade sem sobrescritas
#    agressivas de estilo.
# 2025-09-18 23:41 — v3.100 — Família/Sub-família e combos extraídos de
#    B1.A1.A.2.C para o novo bloco [B2] com raiz B2.C1; alinhamento de tags
#    atualizado nas verificações automáticas.
# 2025-09-19 21:45 — v3.102 — Nomenclatura do bloco auxiliar B1.A1 alinhada
#    com zonas canónicas e aliases partilhados.
# 2025-09-19 10:45 — v3.101 — Família/Sub-família e combos reintegrados em
#    B1.A1.A.*, preservando metadados de bloco e alinhamentos partilhados.

import sys
import json
import logging
import os
import html as html_module
import html.parser as html_parser
import itertools
from collections.abc import Iterable, Mapping
import re
import shutil
from pathlib import Path

from reporting import ReportBroIntegrationError
from reporting.template_updater import apply_template_updaters
try:  # PyQt 5.15.10 wheels omit QWIDGETSIZE_MAX on some platforms
    from PyQt5.QtCore import (
        Qt,
        QTimer,
        QPoint,
        QWIDGETSIZE_MAX,
        QSize,
        pyqtSignal,
        QUrl,
        QLocale,
    )
except ImportError:  # pragma: no cover - fallback for stripped builds
    from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, pyqtSignal, QUrl, QLocale

    QWIDGETSIZE_MAX = 16777215
from PyQt5.QtGui import (
    QDesktopServices,
    QFont,
    QIcon,
    QKeySequence,
    QTextOption,
    QPixmap,
    QStandardItemModel,
    QStandardItem,
)
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
    QListView,
)
from data.datastore import DataStore
from services.products import ProductService, calculate_food_cost
from domain import FichaTecnica
from utils.formatting import (
    format_currency_locale,
    format_pt_number,
    normalise_currency_context,
    parse_decimal,
)

from . import layout
from .layout import Zone
from .models import (
    apply_fichas_tecnicas_headers,
    build_fichas_tecnicas_model,
    update_fichas_tecnicas_model,
)
from .qt_compat import exec_modal
from .reportbro_stub import open_reportbro_stub_dialog, open_reportbro_template_from_label
from .reportbro_kiosk import open_reportbro_kiosk
from . import reportbro_server
from .utilities import (
    AlignmentVariant,
    FIELD_STYLE,
    FOOD_COST_LEVEL_RGB_MAP,
    apply_fcfilter_btn_style,
    apply_label_style,
    apply_overlay_label_style,
    food_cost_lineedit_stylesheet,
    make_readonly_lineedit,
    match_font,
)
from .dialogs import (
    import_data,
    manage_aux_table,
    manage_localizacao_table,
    update_data,
    backup_database,
    restore_database,
    edit_fcost_values,
    ActiveModelsDialog,
)
from .printing import (
    ExportCancelled,
    _serialise_food_cost_levels,
    generate_ft_gestao_pdf,
    generate_ft_gestao_reportbro_pdf,
)
from . import printing_models
APP_TITLE = "Fichas Técnicas Valorizadas"


def resolve_reportbro_url(target: str) -> QUrl | None:
    """Interpret ``target`` and return a suitable ``QUrl`` instance.

    The function accepts HTTP(S) endpoints as well as filesystem paths.  It uses
    ``QUrl.fromUserInput`` to benefit from Qt's heuristics (e.g. automatically
    prefixing ``http://`` for bare hostnames) and falls back to converting the
    value into an absolute local path when no scheme is provided.
    """

    sanitized = target.strip()
    if not sanitized:
        return None

    url = QUrl.fromUserInput(sanitized)
    if url.isValid() and url.scheme():
        return url

    candidate_path = Path(sanitized).expanduser()
    if not candidate_path.is_absolute():
        candidate_path = (Path.cwd() / candidate_path).resolve()

    return QUrl.fromLocalFile(str(candidate_path))

APP_STYLESHEET = (
    "QWidget {\n"
    "    font-size: 12px;\n"
    "    color: #1d1f23;\n"
    "}\n"
    "#headerNomeCampo, #identificacaoNomeCampo {\n"
    "    font-size: 20px;\n"
    "    font-weight: 600;\n"
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


class SquarePreviewContainer(QWidget):
    """Wrapper that keeps a square viewport for the embedded child widget."""

    def __init__(self, child: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._child = child
        self._child.setParent(self)
        self._child.show()

        policy = child.sizePolicy()
        self.setSizePolicy(policy)
        self.setMinimumSize(child.minimumSize())

    def resizeEvent(self, event) -> None:  # pragma: no cover - UI interaction
        side = min(self.width(), self.height())
        offset_x = max(0, (self.width() - side) // 2)
        offset_y = max(0, (self.height() - side) // 2)

        self._child.setGeometry(offset_x, offset_y, side, side)

        super().resizeEvent(event)


class MultiSelectComboBox(QComboBox):
    """Combo box that supports multiple selections via checkable items."""

    selectionChanged = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setModel(QStandardItemModel(self))
        view = QListView(self)
        view.setSelectionMode(QListView.MultiSelection)
        self.setView(view)
        self.setEditable(True)
        line_edit = QLineEdit(self)
        line_edit.setReadOnly(True)
        line_edit.setFocusPolicy(Qt.NoFocus)
        line_edit.setText("")
        self.setLineEdit(line_edit)
        self.lineEdit().setPlaceholderText("")
        self.setInsertPolicy(QComboBox.NoInsert)
        self.view().pressed.connect(self._handle_item_pressed)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._placeholder_text = ""
        self._separator = ", "
        self._block_hide = False
        self._update_display_text()

    def showPopup(self) -> None:  # pragma: no cover - UI integration
        self._block_hide = False
        super().showPopup()

    def hidePopup(self) -> None:  # pragma: no cover - UI integration
        if self._block_hide:
            self._block_hide = False
            return
        super().hidePopup()

    def focusOutEvent(self, event):  # pragma: no cover - UI integration
        reason = event.reason() if hasattr(event, "reason") else Qt.OtherFocusReason
        if reason != Qt.PopupFocusReason and self.view() and self.view().isVisible():
            self._block_hide = False
            super().hidePopup()
        super().focusOutEvent(event)

    def _handle_item_pressed(self, index) -> None:
        model = self.model()
        if model is None:
            return
        item = model.itemFromIndex(index)
        if item is None:
            return
        new_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        item.setCheckState(new_state)
        # Keep the popup open so the user can select multiple entries.
        self._block_hide = True
        QTimer.singleShot(0, self.showPopup)
        self._update_display_text()
        self.selectionChanged.emit()

    def set_placeholder_text(self, text: str) -> None:
        self._placeholder_text = text
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText(text)
        self._update_display_text()

    def set_options(
        self,
        options: Iterable[str],
        *,
        checked: Iterable[str] | None = None,
    ) -> None:
        model = self.model()
        if model is None:
            return
        existing_selection = (
            {text for text in checked}
            if checked is not None
            else set(self.selected_items())
        )
        model.clear()
        for option in options:
            if option is None:
                continue
            text = str(option).strip()
            if not text:
                continue
            item = QStandardItem(text)
            item.setFlags(
                Qt.ItemIsEnabled
                | Qt.ItemIsUserCheckable
                | Qt.ItemIsSelectable
            )
            item.setData(text, Qt.DisplayRole)
            item.setCheckable(True)
            if text in existing_selection:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            model.appendRow(item)
        self._update_display_text()

    def selected_items(self) -> list[str]:
        model = self.model()
        if model is None:
            return []
        selections: list[str] = []
        for row in range(model.rowCount()):
            item = model.item(row)
            if item is None:
                continue
            if item.checkState() == Qt.Checked:
                selections.append(item.text())
        return selections

    def select_items(self, values: Iterable[str]) -> None:
        model = self.model()
        if model is None:
            return
        wanted = {str(value).strip() for value in values if value}
        for row in range(model.rowCount()):
            item = model.item(row)
            if item is None:
                continue
            item.setCheckState(
                Qt.Checked if item.text() in wanted else Qt.Unchecked
            )
        self._update_display_text()
        self.selectionChanged.emit()

    def clear_selection(self) -> None:
        self.select_items([])

    def _update_display_text(self) -> None:
        selections = self.selected_items()
        line_edit = self.lineEdit()
        if line_edit is None:
            return
        if not selections:
            line_edit.setText("")
            line_edit.setPlaceholderText(self._placeholder_text)
        elif len(selections) == 1:
            line_edit.setText(selections[0])
        else:
            line_edit.setText("-- Selecção Múltipla")

    # QObject API ----------------------------------------------------
    def blockSignals(self, block: bool) -> bool:
        prev = super().blockSignals(block)
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.blockSignals(block)
        return prev


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
        self.locale_info = normalise_currency_context({})
        self._refresh_locale_info()
        self.cur_index = 0
        self.current_product = None
        self._prep_dirty = False
        self._active_fcost_filter: int | None = None
        self._allergen_checkboxes: dict[int, QCheckBox] = {}
        self._allergen_tooltips: dict[int, str] = {}
        self._allergen_zone: Zone | None = None
        self._window_aspect_ratio = 1754 / 1240
        self._resizing_lock = False
        self._build_ui()
        self._connect_nav()
        self._load_record(self.cur_index)
        codigo = getattr(self.current_product, "code", None)
        if codigo:
            for pv in getattr(self, "prep_previews", []):
                pv.load_image(codigo)

    def _refresh_datastore(self) -> None:
        """Synchronize the UI datastore reference with the service."""

        self.ds = self.service.ds
        self._refresh_locale_info()

    def _resolve_locale_info(self) -> dict[str, str | None]:
        """Return the active locale context from the datastore."""

        fallback = normalise_currency_context({})
        datastore = getattr(self, "ds", None)
        get_locale = getattr(datastore, "get_localizacao_ativa", None)
        if callable(get_locale):
            try:
                info = get_locale()
            except Exception:
                logger.debug(
                    "[FTApp] Falha ao obter localização ativa; a usar omissões.",
                    exc_info=True,
                )
            else:
                if info in (None, ""):
                    return fallback
                try:
                    return normalise_currency_context(info, defaults=fallback)
                except Exception:
                    logger.debug(
                        "[FTApp] Localização inválida recebida; a usar omissões.",
                        exc_info=True,
                    )
        return fallback

    def _apply_locale_defaults(self) -> None:
        """Align Qt's default locale with the active currency context."""

        locale_info = self.locale_info if isinstance(self.locale_info, Mapping) else {}
        locale_code = locale_info.get("locale_code") if isinstance(locale_info, Mapping) else None
        if not locale_code:
            return
        try:
            qt_locale = QLocale(str(locale_code))
            QLocale.setDefault(qt_locale)
        except Exception:
            logger.debug(
                "[FTApp] Falha ao aplicar QLocale padrão '%s'", locale_code,
                exc_info=True,
            )

    def _refresh_locale_info(self) -> None:
        """Reload cached locale metadata from the datastore."""

        self.locale_info = self._resolve_locale_info()
        self._apply_locale_defaults()

    def _format_currency_value(self, value, *, missing: str = "—") -> str:
        """Return ``value`` formatted according to the active locale."""

        if value is None or value == "":
            return missing
        context = self.locale_info if isinstance(self.locale_info, Mapping) else {}
        return format_currency_locale(
            value,
            locale_code=context.get("locale_code"),
            currency_symbol=context.get("currency_symbol"),
            currency_code=context.get("currency_code"),
        )

    def _on_localizacao_changed(self) -> None:
        """Refresh locale-sensitive UI elements after currency changes."""

        self._refresh_locale_info()
        try:
            self._aux_refresh_lists()
        except Exception:
            logger.exception("[AuxUI] Falha ao recarregar listas auxiliares")
        try:
            self._load_record(getattr(self, "cur_index", 0))
        except Exception:
            logger.exception(
                "[FTApp] Falha ao recarregar o registo atual após alterar localização"
            )

    def _on_import_data(self) -> None:
        """Run the import workflow and refresh datastore bindings."""

        import_data(self, self.service, self._load_record, self.cur_index)
        self._refresh_datastore()

    def _on_update_data(self) -> None:
        """Run the update workflow and refresh datastore bindings."""

        update_data(self, self.service, self._load_record, self.cur_index)
        self._refresh_datastore()

    def _on_update_templates(self) -> None:
        """Confirm before synchronising ReportBro document templates."""

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Actualizar Documentos")
        message_box.setIcon(QMessageBox.Question)
        message_box.setText("Pretende actualizar os modelos de documentos?")

        confirm_button = QPushButton("Actualizar", message_box)
        confirm_button.setStyleSheet(
            """
            QPushButton {
                background-color: #c62828;
                color: white;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
            """
        )
        cancel_button = QPushButton("Cancelar", message_box)
        cancel_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2e7d32;
                color: white;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #1b5e20;
            }
            """
        )

        message_box.addButton(confirm_button, QMessageBox.AcceptRole)
        message_box.addButton(cancel_button, QMessageBox.RejectRole)
        message_box.setDefaultButton(cancel_button)
        message_box.exec_()

        if message_box.clickedButton() is confirm_button:
            self._update_reportbro_templates()

    def _open_reportbro_editor(self) -> None:
        """Open the ReportBro editor or fall back to the bundled stub."""

        editor_target = os.getenv("FTV_REPORTBRO_EDITOR_URL", "").strip()
        kiosk_opt_in = os.getenv("FTV_REPORTBRO_EDITOR_KIOSK", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not editor_target:
            try:
                endpoint = reportbro_server.ensure_reportbro_server()
            except Exception:
                logger.exception("[ReportBro] Falha ao iniciar servidor integrado do ReportBro")
                open_reportbro_stub_dialog(self)
                return

            url = QUrl(f"http://{endpoint.host}:{endpoint.port}/designer")
            if kiosk_opt_in:
                try:
                    if open_reportbro_kiosk(self, endpoint):
                        logger.info(
                            "[ReportBro] Editor integrado aberto em modo kiosk (via FTV_REPORTBRO_EDITOR_KIOSK)"
                        )
                        return
                except Exception:
                    logger.exception(
                        "[ReportBro] Falha ao abrir editor integrado em modo kiosk (FTV_REPORTBRO_EDITOR_KIOSK)"
                    )

            logger.info(
                "[ReportBro] A abrir editor integrado no navegador predefinido em %s",
                url.toString(),
            )
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(
                    self,
                    APP_TITLE,
                    "Não foi possível abrir o editor ReportBro integrado.",
                )
                logger.warning(
                    "[ReportBro] Falha ao abrir editor integrado no navegador em %s",
                    url.toString(),
                )
            return
        url = resolve_reportbro_url(editor_target)
        if url is None:
            QMessageBox.warning(
                self,
                APP_TITLE,
                "Não foi possível determinar o endereço do editor ReportBro.",
            )
            logger.warning("[ReportBro] URL inválida configurada: %s", editor_target)
            return

        logger.info("[ReportBro] A abrir editor em %s", url.toString())
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(
                self,
                APP_TITLE,
                "Não foi possível abrir o editor ReportBro. Verifique a ligação.",
            )
            logger.warning("[ReportBro] Falha ao abrir editor em %s", url.toString())

    def _update_reportbro_templates(self) -> None:
        """Copy ReportBro templates from the templates store into runtime."""

        project_root = Path(__file__).resolve().parent.parent
        source_dir = project_root / "app" / "templates_store" / "templates"
        target_dir = project_root / "reporting" / "templates"

        try:
            templates = sorted(
                path for path in source_dir.glob("*.json") if path.is_file()
            )
        except Exception:
            logger.exception("[ReportBro] Falha ao listar templates em %s", source_dir)
            QMessageBox.critical(
                self,
                "Actualizar Documentos",
                "Não foi possível listar os modelos disponíveis para actualização.",
            )
            return

        if not templates:
            QMessageBox.information(
                self,
                "Actualizar Documentos",
                "Não foram encontrados modelos para actualizar.",
            )
            return

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.exception(
                "[ReportBro] Falha ao preparar diretório de destino em %s", target_dir
            )
            QMessageBox.critical(
                self,
                "Actualizar Documentos",
                "Não foi possível preparar a pasta de destino para os modelos.",
            )
            return

        copied: list[str] = []
        failed: list[str] = []
        for template in templates:
            destination = target_dir / template.name
            try:
                shutil.copy2(template, destination)
            except Exception:
                failed.append(template.name)
                logger.exception(
                    "[ReportBro] Falha ao actualizar template %s", template.name
                )
            else:
                copied.append(template.name)
                logger.info(
                    "[ReportBro] Template %s actualizado em %s",
                    template.name,
                    destination,
                )

        summary = apply_template_updaters(target_dir)

        if not copied and not summary.any_updates():
            QMessageBox.warning(
                self,
                "Actualizar Documentos",
                "Não foi possível actualizar nenhum modelo.",
            )
            return

        lines = ["Modelos actualizados com sucesso."]
        lines.extend(f"• {name}" for name in copied)
        if failed:
            lines.append("")
            lines.append("Os seguintes modelos não puderam ser actualizados:")
            lines.extend(f"• {name}" for name in failed)

        if summary.updated:
            lines.append("")
            lines.append(
                "Modelos base actualizados a partir dos respectivos ficheiros updater:"
            )
            lines.extend(f"• {path.name}" for path in summary.updated)

        if summary.missing_updater:
            lines.append("")
            lines.append(
                "Os seguintes modelos base não possuem ficheiro updater correspondente (ver registos):"
            )
            lines.extend(f"• {path.name}" for path in summary.missing_updater)

        if summary.errors:
            lines.append("")
            lines.append(
                "Ocorreram erros ao aplicar alguns ficheiros updater (consulte os registos):"
            )
            lines.extend(f"• {path.name}" for path, _ in summary.errors)

        QMessageBox.information(self, "Actualizar Documentos", "\n".join(lines))

    def _open_reportbro_template(self, template_label: str) -> None:
        """Open the ReportBro template associated with ``template_label``."""

        try:
            open_reportbro_template_from_label(template_label, self)
        except Exception:
            logger.exception(
                "[ReportBro] Falha ao abrir modelo activo para a ação '%s'", template_label
            )
            QMessageBox.warning(
                self,
                APP_TITLE,
                "Não foi possível abrir o modelo seleccionado. Consulte os registos para mais detalhes.",
            )

    def _open_active_models_dialog(self) -> None:
        """Open the Active Models dialog modally."""

        try:
            dialog = ActiveModelsDialog(self)
        except Exception as exc:  # pragma: no cover - defensive safeguard
            logger.exception("[ReportBro] Falha ao criar diálogo de modelos activos")
            QMessageBox.critical(
                self,
                APP_TITLE,
                "Não foi possível abrir o diálogo de modelos activos."
                " Consulte os registos para mais detalhes."
                f"\nErro: {exc}",
            )
            return

        exec_modal(dialog)

    def _on_print_ft_gestao_actual(self) -> None:
        """Export the currently loaded product as FT Gestão (single record)."""

        product = getattr(self, "current_product", None)
        if product is None:
            QMessageBox.warning(
                self,
                APP_TITLE,
                "Não existe ficha técnica carregada para exportação.",
            )
            return

        identifier = (
            getattr(product, "code", None)
            or getattr(product, "name", None)
            or "<desconhecido>"
        )
        use_reportbro_flag = os.getenv("FTV_USE_REPORTBRO", "").strip().lower()
        template_override_env = os.getenv("FTV_REPORTBRO_TEMPLATE", "").strip()
        active_template = printing_models.resolve_active_model_template(
            "ft_gestao_actual"
        )
        env_template: Path | None = None
        if template_override_env:
            env_template = Path(template_override_env).expanduser()
            if not env_template.is_absolute():
                env_template = (Path.cwd() / env_template).resolve()

        template_override: Path | None = active_template or env_template

        if template_override is not None:
            use_reportbro = True
        elif use_reportbro_flag in {"0", "false", "no"}:
            use_reportbro = False
        elif use_reportbro_flag in {"1", "true", "yes"}:
            use_reportbro = True
        else:
            use_reportbro = True

        food_cost_levels = self._get_food_cost_levels()

        try:
            logger.info(
                "[Print] FT Gestão (Actual) solicitado para produto %s", identifier
            )
            locale_info = None
            get_locale = getattr(self.ds, "get_localizacao_ativa", None)
            if callable(get_locale):
                try:
                    locale_info = get_locale()
                except Exception:
                    logger.debug(
                        "[Print] Falha ao obter localização ativa; a usar omissões",
                        exc_info=True,
                    )
            if use_reportbro:
                try:
                    output_path = generate_ft_gestao_reportbro_pdf(
                        product,
                        template_path=template_override,
                        parent=self,
                        locale=locale_info,
                        food_cost_levels=food_cost_levels,
                    )
                except ReportBroIntegrationError as exc:
                    logger.warning(
                        "[ReportBro] Falha ao gerar PDF para %s via ReportBro: %s",
                        identifier,
                        exc,
                    )
                    QMessageBox.warning(
                        self,
                        APP_TITLE,
                        "Não foi possível gerar a ficha com o ReportBro."
                        " Será utilizada a versão anterior.",
                    )
                    output_path = generate_ft_gestao_pdf(
                        product,
                        parent=self,
                        locale=locale_info,
                        food_cost_levels=food_cost_levels,
                    )
            else:
                output_path = generate_ft_gestao_pdf(
                    product,
                    parent=self,
                    locale=locale_info,
                    food_cost_levels=food_cost_levels,
                )
        except ExportCancelled:
            logger.info(
                "[Print] Exportação FT Gestão cancelada pelo utilizador (%s)",
                identifier,
            )
            return
        except (TypeError, ValueError) as exc:
            logger.warning(
                "[Print] Dados inválidos para exportar FT Gestão de %s: %s",
                identifier,
                exc,
            )
            QMessageBox.warning(
                self,
                APP_TITLE,
                "Não foi possível exportar a ficha de gestão: dados incompletos.",
            )
            return
        except Exception:
            logger.exception(
                "[Print] Erro ao gerar FT Gestão (Actual) para produto %s", identifier
            )
            QMessageBox.critical(
                self,
                APP_TITLE,
                "Ocorreu um erro ao exportar a ficha de gestão. Consulte os logs.",
            )
            return

        if not output_path:
            logger.info(
                "[Print] Exportação FT Gestão ignorada para %s (sem destino)",
                identifier,
            )
            return

        QMessageBox.information(
            self,
            APP_TITLE,
            f"Ficha de Gestão exportada com sucesso para:\n{output_path}",
        )
        logger.info(
            "[Print] FT Gestão (Actual) concluída em %s para %s",
            output_path,
            identifier,
        )

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
        self.resize(1240, 1754)
        root = QVBoxLayout(self)
        root.setContentsMargins(3, 5, 3, 5)
        root.setSpacing(5)

        # --- Top bar: Overlay (esq) + Menu (dir) ---
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 10, 0)
        top.setSpacing(8)
        self.btOverlay = QPushButton(
            f"Overlays: {'ON' if layout.DEV_OVERLAYS else 'OFF'}"
        )
        self.btOverlay.clicked.connect(self._toggle_overlays_btn)
        top.addWidget(self.btOverlay, 0, Qt.AlignLeft)
        top.addStretch(1)
        from PyQt5.QtWidgets import QMenu, QToolButton

        self.btMenu = QToolButton()
        self.btPrintMenu = QToolButton()
        self.btPrintMenu.setPopupMode(QToolButton.InstantPopup)
        self.btPrintMenu.setToolButtonStyle(Qt.ToolButtonIconOnly)
        print_icon = QIcon.fromTheme("document-print")
        if print_icon.isNull():
            print_icon = self.style().standardIcon(QStyle.SP_FileIcon)
        self.btPrintMenu.setIcon(print_icon)
        self.btMenu.setText("Menu")
        self.btMenu.setPopupMode(QToolButton.InstantPopup)
        size_hint = self.btMenu.sizeHint()
        menu_height = int(size_hint.height() * 1.5)
        self.btMenu.setFixedSize(int(size_hint.width() * 1.5), menu_height)
        self.btPrintMenu.setFixedSize(menu_height, menu_height)
        self.btPrintMenu.setIconSize(QSize(menu_height, menu_height))
        menu_font = QFont()
        menu_font.setPointSize(12)

        def apply_menu_font(widget: QWidget | QAction) -> None:
            if hasattr(widget, "setFont"):
                widget.setFont(menu_font)
            if hasattr(widget, "setStyleSheet"):
                widget.setStyleSheet("font-size: 12pt;")

        apply_menu_font(self.btPrintMenu)
        apply_menu_font(self.btMenu)
        self.mnuRoot = QMenu(self)
        apply_menu_font(self.mnuRoot)
        mPrint = QMenu(self.btPrintMenu)
        apply_menu_font(mPrint)
        mPrint.addAction("FT's Gestão (filtro)")
        actPrintGestaoActual = mPrint.addAction("FT's Gestão (Actual)")
        mPrint.addAction("FT's Operacionais (filtro)")
        mPrint.addAction("FT's Operacionais (Actual)")
        self.btPrintMenu.setMenu(mPrint)
        mBD = QMenu("Base de Dados", self.mnuRoot)
        apply_menu_font(mBD)
        actUpdate = QAction("Atualizar Dados", self)
        actReload = QAction("Importar Dados", self)
        mBD.addAction(actUpdate)
        mBD.addAction(actReload)
        mSeg = QMenu("Segurança", mBD)
        apply_menu_font(mSeg)
        actBackup = QAction("Segurança", self)
        actRestore = QAction("Reposição", self)
        mSeg.addAction(actBackup)
        mSeg.addAction(actRestore)
        mBD.addMenu(mSeg)
        self.mnuRoot.addMenu(mBD)
        mTab = QMenu("Tabelas", self.mnuRoot)
        apply_menu_font(mTab)
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
        apply_menu_font(mUtil)
        gestao_docs_menu = QMenu("Gestão de Documentos", mUtil)
        apply_menu_font(gestao_docs_menu)
        actDocEditor = QAction("Editor de Documentos", self)
        apply_menu_font(actDocEditor)
        gestao_docs_menu.addAction(actDocEditor)
        actActiveModels = QAction("Modelos Activos", self)
        apply_menu_font(actActiveModels)
        gestao_docs_menu.addAction(actActiveModels)
        actUpdateTemplates = QAction("Actualizar Documentos", self)
        apply_menu_font(actUpdateTemplates)
        gestao_docs_menu.addAction(actUpdateTemplates)
        mUtil.addMenu(gestao_docs_menu)
        mUtil.addSeparator()
        actTheme = QAction("Tema", self)
        apply_menu_font(actTheme)
        mUtil.addAction(actTheme)
        self.mnuRoot.addMenu(mUtil)
        mConf = QMenu("Configurações", self.mnuRoot)
        apply_menu_font(mConf)
        mParams = QMenu("Parametrizações", mConf)
        apply_menu_font(mParams)
        actFoodCost = QAction("Food Cost", self)
        apply_menu_font(actFoodCost)
        actCurrency = QAction("Moeda", self)
        apply_menu_font(actCurrency)
        mParams.addAction(actFoodCost)
        mParams.addAction(actCurrency)
        mConf.addMenu(mParams)
        self.mnuRoot.addMenu(mConf)
        self.btMenu.setMenu(self.mnuRoot)
        # ligações básicas
        actReload.triggered.connect(self._on_import_data)
        actPrintGestaoActual.triggered.connect(self._on_print_ft_gestao_actual)
        actUpdate.triggered.connect(self._on_update_data)
        actDocEditor.triggered.connect(self._open_reportbro_editor)
        actActiveModels.triggered.connect(self._open_active_models_dialog)
        actUpdateTemplates.triggered.connect(self._on_update_templates)
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
        actCurrency.triggered.connect(
            lambda: manage_localizacao_table(
                self,
                self.ds.aux,
                on_change=self._on_localizacao_changed,
            )
        )
        self.btSearchToggle = QToolButton()
        self.btSearchToggle.setCheckable(True)
        self.btSearchToggle.setAutoRaise(True)
        self.btSearchToggle.setFixedSize(menu_height, menu_height)
        self.btSearchToggle.setIconSize(QSize(menu_height, menu_height))
        search_icon = self.style().standardIcon(QStyle.SP_FileDialogContentsView)
        if isinstance(search_icon, QIcon):
            self.btSearchToggle.setIcon(search_icon)
        else:  # pragma: no cover - defensive fallback
            self.btSearchToggle.setText("🔍")
        self.btSearchToggle.setToolTip("Pesquisar fichas")
        self.btSearchToggle.toggled.connect(self._toggle_search_panel)
        top.addWidget(self.btSearchToggle, 0, Qt.AlignRight)
        top.addWidget(self.btPrintMenu, 0, Qt.AlignRight)
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

        search_center_widget = QWidget(self.searchCenterZone)
        search_center_layout = QGridLayout(search_center_widget)
        search_center_layout.setContentsMargins(6, 6, 6, 6)
        search_center_layout.setHorizontalSpacing(6)
        search_center_layout.setVerticalSpacing(4)

        self.searchFamilyCombo = MultiSelectComboBox(search_center_widget)
        self.searchFamilyCombo.set_placeholder_text("Famílias")
        self.searchSubfamilyCombo = MultiSelectComboBox(search_center_widget)
        self.searchSubfamilyCombo.set_placeholder_text("Subfamílias")
        # ``searchFamilyField``/``searchSubfamilyField`` eram QLineEdit; manter alias
        # para compatibilidade com código legado e testes externos.
        self.searchFamilyField = self.searchFamilyCombo
        self.searchSubfamilyField = self.searchSubfamilyCombo
        self.searchFamilyButton = QPushButton("IR", search_center_widget)
        self.searchFamilyButton.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.searchFamilyApplyButton = self.searchFamilyButton

        search_center_layout.addWidget(self.searchFamilyCombo, 0, 0)
        search_center_layout.addWidget(self.searchSubfamilyCombo, 1, 0, 1, 2)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)
        buttons_layout.addWidget(self.searchFamilyButton)

        self.searchFamilyResetButton = QPushButton(
            "Mostrar todas as famílias", self.searchCenterZone
        )
        self.searchFamilyResetButton.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        buttons_layout.addWidget(self.searchFamilyResetButton)

        search_center_layout.addLayout(buttons_layout, 2, 0, 1, 2)
        search_center_layout.setColumnStretch(0, 1)
        search_center_layout.setColumnStretch(1, 0)

        self.searchCenterZone.ly.addWidget(search_center_widget)

        self.searchFamilyCombo.selectionChanged.connect(
            self._on_family_selection_changed
        )
        self.searchFamilyResetButton.clicked.connect(self._reset_family_filters)
        self.searchFamilyApplyButton.clicked.connect(self._apply_search_filters)

        self._family_hierarchy: dict[str, tuple[str, ...]] = {}
        self._init_family_filters()

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
        self.headerEdNome.setObjectName("headerNomeCampo")
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

        # ---------------- B1 — Ficha de Artigo (B1.C1) ----------------
        self.B1 = Zone(
            "B1.C1",
            self,
            flow="v",
            margins=2,
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
        )
        self.B1.apply_metadata(
            zone_type="secao-ficha-artigo",
            widget_type="campo",
            base_declarations=(
                "border-radius: 12px;\n",
                "padding: 2px;\n",
            ),
        )
        self.B1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.B1.ly.setContentsMargins(2, 2, 2, 2)

        (
            self.zone_article_sheet_left,
            self.zone_article_sheet_right,
        ) = self.B1.split_h((2, 1))
        for zone in (self.zone_article_sheet_left, self.zone_article_sheet_right):
            zone.ly.setContentsMargins(0, 0, 0, 0)
            zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.zone_article_sheet_left.apply_metadata(
            zone_type="coluna-campos", widget_type="campo"
        )
        self.zone_article_sheet_right.apply_metadata(
            zone_type="coluna-campos", widget_type="campo"
        )

        left_slot_shares = (5, 3, 5, 7)
        (
            self.zone_article_sheet_left_slot_1,
            self.zone_article_sheet_left_slot_2,
            self.zone_article_sheet_left_slot_3,
            self.zone_article_sheet_left_slot_4,
        ) = self.zone_article_sheet_left.split_v(left_slot_shares)
        self.zone_article_sheet_left_slots = (
            self.zone_article_sheet_left_slot_1,
            self.zone_article_sheet_left_slot_2,
            self.zone_article_sheet_left_slot_3,
            self.zone_article_sheet_left_slot_4,
        )
        left_slot_spacing = self.zone_article_sheet_left.ly.spacing()
        for slot in self.zone_article_sheet_left_slots:
            slot.ly.setContentsMargins(0, 0, 0, 0)
            slot.ly.setSpacing(left_slot_spacing)
            slot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            slot.apply_metadata(zone_type="coluna-campos", widget_type="campo")

        slot2_base_declarations = tuple(
            "padding: 3px 6px 3px;\n"
            if declaration.strip().startswith("padding:")
            else declaration
            for declaration in layout._DEFAULT_ZONE_BASE_DECLARATIONS
        )
        self.zone_article_sheet_left_slot_2.apply_metadata(
            base_declarations=slot2_base_declarations
        )
        self.zone_article_sheet_left_slot_2.ly.setSpacing(
            max(0, left_slot_spacing // 2)
        )

        slot_parent = self.zone_article_sheet_left_slot_2.parentWidget()
        slot_layout = slot_parent.layout() if slot_parent is not None else None
        if slot_layout is not None:
            for slot, share in zip(self.zone_article_sheet_left_slots, left_slot_shares):
                index = slot_layout.indexOf(slot)
                if index != -1:
                    slot_layout.setStretch(index, share)
            layout.update_vertical_split_shares(slot_layout)

        # --- Identificação e família (B1.C1.A.1) ---
        self.zone_general_aux_stack = self.zone_article_sheet_left_slot_1
        self.zone_general_aux_stack.ly.setSpacing(2)
        # Alias explícito para o widget que ancora o cabeçalho flutuante.
        self._header_scroll_anchor = self.zone_general_aux_stack

        (
            self.zone_general_aux_identification_slot,
            self.zone_general_aux_family_slot,
            self.zone_general_aux_secondary_slot,
        ) = self.zone_general_aux_stack.split_v((1, 1, 0))
        for zone in (
            self.zone_general_aux_identification_slot,
            self.zone_general_aux_family_slot,
            self.zone_general_aux_secondary_slot,
        ):
            zone.ly.setContentsMargins(0, 0, 0, 0)
            current_policy = zone.sizePolicy()
            zone.setSizePolicy(
                QSizePolicy.Expanding,
                current_policy.verticalPolicy(),
            )

        self.zone_general_aux_family_slot.ly.setContentsMargins(0, 8, 0, 8)
        self.zone_general_aux_family_slot.apply_metadata(
            zone_type="coluna-campos",
            widget_type="campo",
            base_declarations=(
                *layout._DEFAULT_ZONE_BASE_DECLARATIONS,
                "border-bottom-width: 2px;\n",
                "border-bottom-style: groove;\n",
                "border-bottom: 2px groove #f7f9fc;\n",
            ),
        )

        self.zone_general_aux_identification_slot.ly.setContentsMargins(0, 8, 0, 8)
        self.zone_general_aux_identification_slot.apply_metadata(
            zone_type="coluna-campos",
            widget_type="campo",
            base_declarations=(
                *layout._DEFAULT_ZONE_BASE_DECLARATIONS,
                "border-bottom-width: 2px;\n",
                "border-bottom-style: groove;\n",
                "border-bottom: 2px groove #f7f9fc;\n",
            ),
        )

        self.edCodigo = QLineEdit()
        make_readonly_lineedit(self.edCodigo)
        self.edCodigo.setStyleSheet(FIELD_STYLE)
        self.edNome = QLineEdit()
        make_readonly_lineedit(self.edNome)
        self.edNome.setStyleSheet(FIELD_STYLE)
        self.edNome.setObjectName("identificacaoNomeCampo")

        label_col, field_col = self.zone_general_aux_identification_slot.split_h((1, 4))
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
            zone.apply_metadata(
                zone_type="linha-legenda",
                widget_type="etiqueta-c",
                base_declarations=(
                    "border-radius: 12px;\n",
                    "padding: 6px;\n",
                ),
            )
            zone.set_label_alignment(AlignmentVariant.RIGHT)

        field_top, field_bottom = field_col.split_v((1, 1))
        for field_zone in (field_top, field_bottom):
            field_zone.ly.setContentsMargins(0, 0, 0, 0)
            field_zone.apply_metadata(zone_type="linha-campo", widget_type="campo")

        overlay_active = bool(getattr(label_col, "_overlay_active", False))

        def _make_ident_label(zone: Zone, text: str, overlay: str) -> QLabel:
            lbl = QLabel(zone)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setProperty("userLabel", text)
            lbl.setProperty("devLabel", overlay)
            lbl.setProperty("userLabelDisplay", text.upper())
            if overlay_active:
                apply_overlay_label_style(lbl)
                lbl.setText(overlay)
            else:
                lbl.setStyleSheet("")
                display_text = lbl.property("userLabelDisplay") or text
                if not isinstance(display_text, str):
                    display_text = text
                lbl.setText(display_text)
            zone.ly.addWidget(lbl, 0, Qt.AlignRight | Qt.AlignVCenter)
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

        scroll.verticalScrollBar().valueChanged.connect(
            self._toggle_header_on_scroll
        )
        self.edCodigo.textChanged.connect(self.headerEdCodigo.setText)
        self.edNome.textChanged.connect(self._sync_header_nome)

        family_row_margin_value = 4
        family_row_spacing_value = 2

        family_row_container = QWidget(self.zone_general_aux_family_slot)
        family_row_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        family_row_layout = QHBoxLayout(family_row_container)
        family_row_layout.setContentsMargins(0, 0, 0, 0)
        family_row_layout.setSpacing(family_row_spacing_value)
        self.zone_general_aux_family_slot.add(family_row_container, 0)

        family_labels_zone = Zone(
            "B1.C1.A.1.1.C",
            family_row_container,
            flow="v",
            margins=family_row_margin_value,
            spacing=family_row_spacing_value,
            level=self.zone_general_aux_family_slot._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
            base_style_label=self.zone_general_aux_family_slot.base_style_label,
        )
        family_values_zone = Zone(
            "B1.C1.A.1.1.D",
            family_row_container,
            flow="v",
            margins=family_row_margin_value,
            spacing=family_row_spacing_value,
            level=self.zone_general_aux_family_slot._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
            base_style_label=self.zone_general_aux_family_slot.base_style_label,
        )
        family_labels_zone.ly.setContentsMargins(0, 0, 0, 0)
        family_values_zone.ly.setContentsMargins(0, 0, 0, 0)

        family_row_layout.addWidget(family_labels_zone, 1)
        family_row_layout.addWidget(family_values_zone, 4)

        familia_label_zone, subfamilia_label_zone = family_labels_zone.split_v((1, 1))
        familia_values_zone, subfamilia_values_zone = family_values_zone.split_v((1, 1))

        for zone in (familia_label_zone, subfamilia_label_zone):
            zone_margins = zone.ly.contentsMargins()
            zone.ly.setContentsMargins(
                0,
                zone_margins.top(),
                0,
                zone_margins.bottom(),
            )
            zone.apply_metadata(
                zone_type="linha-legenda",
                widget_type="etiqueta-c",
            )
        family_labels_zone.set_label_alignment(AlignmentVariant.RIGHT)

        overlay_active = bool(getattr(family_labels_zone, "_overlay_active", False))

        def _make_family_label(zone: Zone, text: str, overlay: str) -> QLabel:
            lbl = QLabel(zone)
            lbl.setProperty("userLabel", text)
            lbl.setProperty("devLabel", overlay)
            lbl.setProperty("userLabelDisplay", text.upper())
            apply_label_style(lbl, alignment=AlignmentVariant.RIGHT)
            if overlay_active:
                apply_overlay_label_style(lbl)
                lbl.setText(overlay)
            else:
                display_text = lbl.property("userLabelDisplay") or text
                if not isinstance(display_text, str):
                    display_text = text
                lbl.setText(display_text)
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
        self.lbSubFamiliaVal.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.lbSubFamiliaVal.setFont(self.edNome.font())

        familia_values_zone.ly.addWidget(self.lbFamiliaVal, 0, Qt.AlignVCenter)
        subfamilia_values_zone.ly.addWidget(
            self.lbSubFamiliaVal, 0, Qt.AlignVCenter
        )

        self._family_label_zone = family_labels_zone
        self._refresh_family_label_column_widths()

        self.zone_general_aux_secondary_slot.hide()
        self.zone_general_aux_secondary_slot.ly.setSpacing(
            family_row_spacing_value
        )

        # --- Informação adicional (B1.C1.A.2.A) ---
        info_zone_tag = f"{self.zone_article_sheet_left_slot_2.tag}.A"
        info_zone = Zone(
            info_zone_tag,
            self.zone_article_sheet_left_slot_2,
            flow="v",
            margins=family_row_margin_value,
            margin_v=family_row_margin_value // 2,
            spacing=family_row_spacing_value,
            level=self.zone_article_sheet_left_slot_2._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
            base_style_label=self.zone_article_sheet_left_slot_2.base_style_label,
        )
        self.zone_article_sheet_left_slot_2.add(info_zone, 0)
        info_zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        info_zone.apply_metadata(
            zone_type="secao-informacao",
            base_style_label=self.zone_article_sheet_left_slot_2.base_style_label,
            base_declarations=(
                *slot2_base_declarations,
                "border-bottom-width: 2px;\n",
                "border-bottom-style: groove;\n",
                "border-bottom: 2px groove #f7f9fc;\n",
            ),
        )

        info_zone.ly.setSpacing(family_row_spacing_value)

        info_field_zone = Zone(
            f"{info_zone.tag}.2",
            info_zone,
            flow="v",
            margins=(0, 0),
            spacing=family_row_spacing_value,
            level=info_zone.level + 1,
            show_overlays=layout.DEV_OVERLAYS,
            base_style_label=info_zone.base_style_label,
        )
        info_field_zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        info_field_zone.apply_metadata(
            zone_type="linha-campo",
            apply_base_style=False,
        )
        info_field_zone.ly.setContentsMargins(0, 0, 0, 0)
        info_zone.add(info_field_zone, 1)

        combo_container = QWidget(info_field_zone)
        combo_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        combo_container_layout = QHBoxLayout(combo_container)
        combo_container_layout.setContentsMargins(0, 0, 0, 0)
        combo_container_layout.setSpacing(info_field_zone.ly.spacing())
        info_field_zone.add(combo_container, 0)

        combo_columns: list[Zone] = []
        for suffix in ("A", "B", "C"):
            column_zone = Zone(
                f"{info_field_zone.tag}.{suffix}",
                combo_container,
                flow="v",
                margins=(0, 0),
                spacing=family_row_spacing_value,
                level=info_field_zone.level + 1,
                show_overlays=layout.DEV_OVERLAYS,
                base_style_label=info_field_zone.base_style_label,
                widget_type=info_field_zone.widget_type,
                zone_type=info_field_zone.zone_type,
            )
            column_zone.apply_metadata(apply_base_style=False)
            column_zone.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Preferred
            )
            column_zone.ly.setContentsMargins(0, 0, 0, 0)
            column_zone.ly.setSpacing(family_row_spacing_value)
            combo_container_layout.addWidget(column_zone, 1)
            combo_columns.append(column_zone)

        combo_zone_specs = (
            (combo_columns[0], "Tipos Artigos", "cbTipos"),
            (combo_columns[1], "Validade", "cbValidade"),
            (combo_columns[2], "Temperaturas", "cbTemp"),
        )

        for column_zone, label_text, attr_name in combo_zone_specs:
            column_zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            column_zone.ly.setContentsMargins(0, 0, 0, 0)
            column_zone.ly.setSpacing(family_row_spacing_value)

            legend_zone, field_zone = column_zone.split_v((1, 1))
            legend_zone.apply_metadata(
                zone_type="linha-legenda",
                widget_type="legenda-c",
                apply_base_style=False,
                style_dev_info=legend_zone.objectName(),
            )
            legend_zone.ly.setContentsMargins(0, 0, 0, 0)
            legend_zone.ly.setSpacing(0)

            field_zone.apply_metadata(
                zone_type="linha-campo",
                widget_type="lista",
                apply_base_style=False,
                style_dev_info=field_zone.objectName(),
            )
            field_zone.ly.setContentsMargins(0, 0, 0, 0)
            field_zone.ly.setSpacing(0)

            display_text = label_text.upper()
            label = QLabel(display_text, legend_zone)
            label.setProperty("userLabel", label_text)
            label.setProperty("devLabel", label_text)
            match_font(label, self.edNome)
            if legend_zone._overlay_active and layout.DEV_OVERLAYS:
                apply_label_style(label, alignment=AlignmentVariant.DEFAULT)
                apply_overlay_label_style(label)
                label.setToolTip("")
            else:
                apply_label_style(label, alignment=AlignmentVariant.DEFAULT)
                label.setToolTip(label_text)
            legend_zone.add(label, 0)
            legend_zone._labels.append(label)

            combo = QComboBox(field_zone)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo.setStyleSheet(FIELD_STYLE)
            field_zone.ly.addWidget(combo, 0)
            setattr(self, attr_name, combo)

        self.cbTipos: QComboBox
        self.cbValidade: QComboBox
        self.cbTemp: QComboBox
        self.cbTipos.currentIndexChanged.connect(self._on_tipo_artigo_changed)
        self.cbValidade.currentIndexChanged.connect(self._on_validade_changed)
        self.cbTemp.currentIndexChanged.connect(self._on_temperatura_changed)

        self.lbInformacaoAdicional = QLineEdit("", info_field_zone)
        make_readonly_lineedit(self.lbInformacaoAdicional)
        self.lbInformacaoAdicional.setStyleSheet(FIELD_STYLE)
        self.lbInformacaoAdicional.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbInformacaoAdicional.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.lbInformacaoAdicional.setFont(self.edNome.font())
        info_field_zone.ly.addWidget(self.lbInformacaoAdicional, 0, Qt.AlignVCenter)

        # --- PVPs (B1.C1.A.3) ---
        pvps_section = self.zone_article_sheet_left_slot_3
        self.zone_general_aux_prices_slot = pvps_section
        pvps_section.show()
        pvps_section.ly.setContentsMargins(
            family_row_margin_value,
            family_row_margin_value,
            family_row_margin_value,
            family_row_margin_value,
        )
        pvps_section.ly.setSpacing(family_row_spacing_value)
        pvps_section.apply_metadata(
            zone_type="secao-pvps",
            widget_type="campo",
            apply_base_style=False,
        )
        pvps_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.lbPVPs: list[QLineEdit] = []

        pvps_columns = pvps_section.split_h((1, 1, 1, 1, 1))

        for idx, column_zone in enumerate(pvps_columns, start=1):
            column_zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            column_zone.ly.setContentsMargins(0, 0, 0, 0)
            column_zone.ly.setSpacing(2)
            column_zone.apply_metadata(
                zone_type="grade-pvps",
                widget_type="campo",
                apply_base_style=False,
            )

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
            display_text = display_label.upper()
            lbl = QLabel(display_text, legend_zone)
            lbl.setProperty("userLabel", user_label)
            lbl.setProperty("devLabel", dev_label)
            match_font(lbl, self.edNome)
            if legend_zone._overlay_active and layout.DEV_OVERLAYS:
                # Ensure the etiqueta inherits the centred alignment from the zone
                # before overlay styling clears the base stylesheet.
                apply_label_style(lbl, alignment=AlignmentVariant.DEFAULT)
                apply_overlay_label_style(lbl)
                lbl.setToolTip("")
            else:
                apply_label_style(lbl, alignment=AlignmentVariant.DEFAULT)
                lbl.setToolTip(f"{user_label} — {dev_label}")
            legend_zone.add(lbl, 0)
            legend_zone._labels.append(lbl)

            val = QLineEdit("—", field_zone)
            val.setFont(self.edNome.font())
            make_readonly_lineedit(val)
            val.setAlignment(Qt.AlignCenter)
            val.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            field_zone.ly.addWidget(val, 0, Qt.AlignCenter)
            self.lbPVPs.append(val)

        article_sheet_preview_container = QWidget(self.zone_article_sheet_right)
        article_sheet_preview_container.setObjectName(
            "article_sheet_preview_container"
        )
        article_sheet_preview_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        article_sheet_preview_layout = QVBoxLayout(
            article_sheet_preview_container
        )
        article_sheet_preview_layout.setContentsMargins(4, 4, 4, 4)
        article_sheet_preview_layout.setSpacing(2)
        self.zone_article_sheet_right.add(article_sheet_preview_container, 1)

        # B1.C1.B — preview de imagem
        try:
            init_code = self.service.codigo_at(self.cur_index)
        except Exception:
            init_code = None
        self.image_preview = ImagePreview(init_code, self.service)
        self.image_preview_container = SquarePreviewContainer(self.image_preview)
        article_sheet_preview_layout.addWidget(self.image_preview_container, 1)

        page_ly.addWidget(
            self._section_box("[B1] - FICHA DE ARTIGO", self.B1),
            0,
        )

        # ---------------- B2 — FICHA TÉCNICA (B2.C1) ----------------
        self.B2_C1 = Zone(
            "B2.C1",
            self,
            flow="v",
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
        )
        page_ly.addWidget(
            self._section_box("[B2] - FICHA TÉCNICA", self.B2_C1),
            0,
        )

        B2_ing_zone, B2_totals_zone = self.B2_C1.split_v((1, 0))
        B2_ing_zone.apply_metadata(
            zone_type="secao-tabela-ingredientes",
            widget_type="tabela",
        )

        self.ingModel = build_fichas_tecnicas_model(
            [],
            overlays=layout.DEV_OVERLAYS,
            currency_context=self.locale_info,
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
        B2_ing_zone.add(self.tbIng, 1)
        nome_font = QFont(self.edNome.font())
        nome_font.setPixelSize(20)
        nome_font.setBold(True)
        self.edNome.setFont(nome_font)
        self.edNome.setFixedHeight(self.edNome.sizeHint().height())
        self.edNome.updateGeometry()

        header_nome_font = QFont(nome_font)
        self.headerEdNome.setFont(header_nome_font)
        self.headerEdNome.setFixedHeight(self.headerEdNome.sizeHint().height())
        self.headerEdNome.updateGeometry()

        self._setup_ing_columns()

        # Zona para custos totais após a tabela de ingredientes
        self.B2Custo = Zone(
            f"{B2_totals_zone.tag}.A",
            B2_totals_zone,
            flow="h",
            level=B2_totals_zone._level + 1,
            show_overlays=layout.DEV_OVERLAYS,
            widget_type="campo",
        )
        self.B2Custo.apply_metadata(
            zone_type="barra-totais",
            widget_type="campo",
        )
        self.B2Custo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        B2_totals_zone.add(self.B2Custo, 0)
        self.B2Custo.ly.addStretch(1)
        custo_total_label = QLabel("Custo Total:")
        apply_label_style(custo_total_label)
        self.B2Custo.add(custo_total_label, 0)
        self.edCustoTotal = QLineEdit()
        make_readonly_lineedit(self.edCustoTotal)
        self.edCustoTotal.setStyleSheet(FIELD_STYLE)
        self.edCustoTotal.setFixedWidth(self.edCustoTotal.sizeHint().width() * 2)
        self.B2Custo.add(self.edCustoTotal, 0)

        # ---------------- B3 — FOOD COST (B3.C1) ----------------
        self.B3_C1 = Zone(
            "B3.C1",
            self,
            flow="v",
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
        )
        page_ly.addWidget(self._section_box("[B3] - FOOD COST", self.B3_C1), 0)

        B3A = Zone(
            "B3.C1.A",
            self.B3_C1,
            flow="v",
            level=1,
            show_overlays=layout.DEV_OVERLAYS,
        )
        self.B3_C1.add(B3A, 1)
        B3AA = Zone(
            "B3.C1.A.A",
            B3A,
            flow="h",
            level=2,
            show_overlays=layout.DEV_OVERLAYS,
        )
        B3AA.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        B3A.add(B3AA, 0)
        fc1, fc2, fc3, fc4, fc5 = B3AA.split_h((1, 1, 1, 1, 1))

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
            overlay_active = bool(label_zone._overlay_active and layout.DEV_OVERLAYS)
            display_label = dev_label if overlay_active else user_label
            display_text = display_label if overlay_active else display_label.upper()
            lbl = QLabel(display_text, label_zone)
            lbl.setProperty("userLabel", user_label)
            lbl.setProperty("userLabelDisplay", user_label.upper())
            lbl.setProperty("devLabel", dev_label)
            apply_label_style(lbl, alignment=AlignmentVariant.DEFAULT)
            if overlay_active:
                apply_overlay_label_style(lbl)
                lbl.setToolTip("")
            else:
                lbl.setToolTip(f"{user_label} — {dev_label}")
            label_zone.add(lbl, 0)
            label_zone._labels.append(lbl)

            val = QLineEdit("—", field_zone)
            make_readonly_lineedit(val)
            val.setAlignment(Qt.AlignCenter)
            val.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            field_zone.ly.addWidget(val, 0, Qt.AlignCenter)
            self.lbFoodCosts.append(val)

        B3AB = Zone(
            "B3.C1.A.B",
            B3A,
            flow="h",
            level=2,
            show_overlays=layout.DEV_OVERLAYS,
        )
        B3AB.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        B3A.add(B3AB, 0)
        fcB1, fcB2, fcB3, fcB4, fcB5 = B3AB.split_h((1, 1, 1, 1, 1))

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

        # ---------------- B4 — PREPARAÇÃO (B4.C1) ----------------
        self.B4_C1 = Zone(
            "B4.C1",
            self,
            flow="v",
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
        )
        page_ly.addWidget(self._section_box("[B4] - PREPARAÇÃO", self.B4_C1), 1)

        B4_text, B4_gallery = self.B4_C1.split_v((3, 2))
        B4_text.apply_metadata(
            zone_type="secao-texto-preparacao",
            widget_type="editor",
        )
        B4_gallery.apply_overlays(layout.DEV_OVERLAYS)

        self.prep_previews: list[PrepImagePreview] = []
        gallery_slots = B4_gallery.split_h((1, 1, 1, 1))
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

        B4_text.add(toolbar, 0)

        self.edPrep = QTextEdit()
        self.edPrep.setAcceptRichText(True)
        self.edPrep.setWordWrapMode(QTextOption.WordWrap)
        self.edPrep.setTabChangesFocus(False)
        self.edPrep.setUndoRedoEnabled(True)
        self.edPrep.setLineWrapMode(QTextEdit.WidgetWidth)
        self.edPrep.document().setDefaultStyleSheet("img { max-width:100%; }")
        self.edPrep.setPlaceholderText("— Texto de preparação —")
        self.edPrep.textChanged.connect(self._on_prep_changed)
        B4_text.add(self.edPrep, 1)

        # ---------------- B5 — NUTRIÇÃO / ALERGÉNIOS (B5.C1) ----------------
        self.B5_C1 = Zone(
            "B5.C1",
            self,
            flow="v",
            level=0,
            show_overlays=layout.DEV_OVERLAYS,
            widget_type="caixa de seleção",
        )
        # ``self.C7`` is kept for backward compatibility with legacy code.
        self.C7 = self.B5_C1

        self.B5_C1.apply_metadata(
            zone_type="bloco-alergenios",
            widget_type="caixa de seleção",
        )
        page_ly.addWidget(
            self._section_box("[B5] - NUTRIÇÃO / ALERGÉNIOS", self.B5_C1),
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


    def _sync_header_nome(self, text: str | None = None) -> None:
        header_nome = getattr(self, "headerEdNome", None)
        nome_field = getattr(self, "edNome", None)
        if header_nome is None or nome_field is None:
            return
        if text is None:
            text = nome_field.text()
        header_nome.setText(text or "")
        header_nome.setCursorPosition(0)


    def _toggle_header_on_scroll(self, value: int):
        del value  # a mudança de visibilidade não depende do valor numérico.
        header = getattr(self, "header", None)
        scroll = getattr(self, "scroll", None)
        zone = getattr(self, "_header_scroll_anchor", None)
        if not header or scroll is None or zone is None:
            return
        viewport = scroll.viewport()
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
        zone = getattr(self, "B5_C1", None)
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
        ratios = [0.46, 0.08, 0.115, 0.13, 0.11, 0.105]
        for idx, ratio in enumerate(ratios):
            self.tbIng.setColumnWidth(idx, int(w * ratio))
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

    def _init_family_filters(self) -> None:
        hierarchy = self._load_family_hierarchy()
        self._family_hierarchy = hierarchy
        families = [family for family in hierarchy.keys()]
        self.searchFamilyCombo.set_options(families)
        self.searchFamilyCombo.setEnabled(bool(families))
        self._update_subfamily_options(preserve_selection=False)
        self.searchSubfamilyCombo.setEnabled(bool(hierarchy))

    def _load_family_hierarchy(self) -> dict[str, tuple[str, ...]]:
        provider_names = (
            "list_families_with_subfamilies",
            "list_family_hierarchy",
            "list_family_groups",
            "list_family_options",
            "list_familias",
        )
        for name in provider_names:
            loader = getattr(self.service, name, None)
            if not callable(loader):
                continue
            try:
                raw = loader()
            except Exception:  # pragma: no cover - defensive logging
                logger.exception(
                    "[SearchPanel] Falha ao obter famílias através de %s", name
                )
                return {}
            normalized = self._normalize_family_hierarchy(raw)
            if normalized is not None:
                return normalized
        return {}

    @staticmethod
    def _clean_family_value(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @classmethod
    def _normalize_family_hierarchy(
        cls, raw: object
    ) -> dict[str, tuple[str, ...]] | None:
        if raw is None:
            return {}

        families: dict[str, set[str]] = {}

        def _add_family(family_value: object, subs_value: object | None) -> None:
            family_name = cls._clean_family_value(family_value)
            if family_name is None:
                return
            bucket = families.setdefault(family_name, set())
            if subs_value is None:
                return
            if isinstance(subs_value, (str, bytes)):
                sub_name = cls._clean_family_value(subs_value)
                if sub_name is not None:
                    bucket.add(sub_name)
                return
            if isinstance(subs_value, dict):
                iterable = subs_value.values()
            elif isinstance(subs_value, Iterable):
                iterable = subs_value
            else:
                iterable = []
            for entry in iterable:
                sub_name = cls._clean_family_value(entry)
                if sub_name is not None:
                    bucket.add(sub_name)

        if isinstance(raw, dict):
            items = raw.items()
        elif isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
            items = raw
        else:
            return {}

        for entry in items:
            if isinstance(entry, dict):
                family_value = (
                    entry.get("familia")
                    or entry.get("family")
                    or entry.get("nome")
                    or entry.get("name")
                )
                subs_value = (
                    entry.get("subfamilias")
                    or entry.get("subfamilies")
                    or entry.get("subFamilias")
                    or entry.get("subFamilia")
                    or entry.get("subfamily")
                )
                if subs_value is None and "subfamilia" in entry:
                    subs_value = entry.get("subfamilia")
                _add_family(family_value, subs_value)
            elif isinstance(entry, tuple) or isinstance(entry, list):
                if len(entry) == 2:
                    family_value, subs_value = entry
                    _add_family(family_value, subs_value)
                elif len(entry) == 1:
                    _add_family(entry[0], None)
            else:
                _add_family(entry, None)

        sorted_families: dict[str, tuple[str, ...]] = {}
        for family_name in sorted(families.keys(), key=str.casefold):
            subs = families[family_name]
            sorted_families[family_name] = tuple(
                sorted(subs, key=str.casefold)
            )
        return sorted_families

    def _update_subfamily_options(self, *, preserve_selection: bool = True) -> None:
        hierarchy = self._family_hierarchy
        current_selection = (
            self.searchSubfamilyCombo.selected_items() if preserve_selection else []
        )
        selected_families = self.searchFamilyCombo.selected_items()
        if selected_families:
            families = selected_families
        else:
            families = hierarchy.keys()

        collected: list[str] = []
        for family in families:
            for sub in hierarchy.get(family, ()):  # ``hierarchy`` stores tuples
                collected.append(sub)

        seen: dict[str, str] = {}
        for name in collected:
            key = name.casefold()
            if key not in seen:
                seen[key] = name
        available_subfamilies = [seen[key] for key in sorted(seen.keys())]
        checked = (
            [name for name in current_selection if name in available_subfamilies]
            if preserve_selection
            else []
        )
        self.searchSubfamilyCombo.set_options(available_subfamilies, checked=checked)
        self.searchSubfamilyCombo.setEnabled(bool(hierarchy))

    def _on_family_selection_changed(self) -> None:
        self._update_subfamily_options()

    def _reset_family_filters(self, *, apply: bool = True) -> None:
        self.searchFamilyCombo.blockSignals(True)
        self._clear_family_selection()
        self.searchFamilyCombo.blockSignals(False)
        self._update_subfamily_options(preserve_selection=False)
        self.searchSubfamilyCombo.blockSignals(True)
        self._clear_subfamily_selection()
        self.searchSubfamilyCombo.blockSignals(False)
        if apply:
            self._apply_search_filters()

    def _apply_search_filters(self):
        product_name = (self.searchProductField.text() or "").strip() or None
        ingredient_name = (self.searchIngredientField.text() or "").strip() or None
        family_selection = self._selected_families()
        subfamily_selection = self._selected_subfamilies()
        family_names = tuple(family_selection) or None
        subfamily_names = tuple(subfamily_selection) or None
        setter = getattr(self.service, "set_search_filters", None)
        if callable(setter):
            setter(
                produto=product_name,
                ingrediente=ingredient_name,
                familia=family_names,
                subfamilia=subfamily_names,
            )
        self.cur_index = 0
        self._load_record(0)

    def _selected_families(self) -> list[str]:
        return self.searchFamilyCombo.selected_items()

    def _selected_subfamilies(self) -> list[str]:
        return self.searchSubfamilyCombo.selected_items()

    def _clear_family_selection(self) -> None:
        self.searchFamilyCombo.clear_selection()

    def _clear_subfamily_selection(self) -> None:
        self.searchSubfamilyCombo.clear_selection()

    def _reset_search_filters(self):
        self.searchProductField.setText("")
        self.searchIngredientField.setText("")
        self._reset_family_filters(apply=False)
        self._apply_search_filters()

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
            self._sync_header_nome()
            self.lbFamiliaVal.setText(product.familia or "")
            self.lbSubFamiliaVal.setText(product.subfamilia or "")
            self.lbInformacaoAdicional.setText(
                product.informacao_adicional or ""
            )

            pvps = list(product.pvps or [])
            pvps.extend([None] * (5 - len(pvps)))
            for lbl, price in zip(self.lbPVPs, pvps):
                if price in (None, 0):
                    lbl.setText("--N/A--")
                else:
                    lbl.setText(self._format_currency_value(price))

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
                self.ingModel,
                fichas,
                overlays=layout.DEV_OVERLAYS,
                currency_context=self.locale_info,
            )
            self._apply_ingredient_widths()
            self._apply_ing_autofit_or_scroll()

            self.edCustoTotal.setText(
                self._format_currency_value(self.service.calculate_cost(product))
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
    def _get_food_cost_levels(self) -> list[dict[str, float]]:
        """Fetch and normalise Food Cost levels from the datastore."""
        repo = getattr(getattr(self.service, "ds", None), "fcost", None)
        levels: list[dict[str, float]] = []

        def _level_value(entry, key: str, index: int):
            if isinstance(entry, dict):
                return entry.get(key)
            try:
                return entry[index]
            except (TypeError, IndexError):
                return None

        if repo is not None:
            try:
                for entry in repo.list_levels():
                    nome = _level_value(entry, "Nome", 1)
                    vmin = parse_decimal(_level_value(entry, "ValorMin", 2))
                    vmax = parse_decimal(_level_value(entry, "ValorMax", 3))
                    if not nome:
                        continue
                    try:
                        vmin_f = float(vmin) if vmin is not None else None
                        vmax_f = float(vmax) if vmax is not None else None
                    except (TypeError, ValueError):
                        continue
                    if vmin_f is None or vmax_f is None:
                        continue
                    levels.append(
                        {
                            "name": str(nome),
                            "min": vmin_f,
                            "max": vmax_f,
                        }
                    )
            except Exception:
                logger.exception(
                    "[FoodCost] failed to retrieve cost levels for styling."
                )

        return levels

    def _update_food_costs(self):
        """Update food cost percentage labels based on current product."""
        product = getattr(self, "current_product", None)
        if not product:
            return
        identifier = (
            getattr(product, "code", None)
            or getattr(product, "name", None)
            or "<desconhecido>"
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

        level_styles = {
            name: food_cost_lineedit_stylesheet(rgb)
            for name, rgb in FOOD_COST_LEVEL_RGB_MAP.items()
        }
        default_style = level_styles.get("Todos") or food_cost_lineedit_stylesheet(
            (200, 200, 200)
        )

        serialised_levels = _serialise_food_cost_levels(
            self._get_food_cost_levels()
        )
        level_ranges: list[tuple[str, float, float]] = []
        lowest_range: tuple[str, float, float] | None = None
        highest_range: tuple[str, float, float] | None = None
        for entry in serialised_levels:
            level_tuple = (
                entry["name"],
                float(entry["min"]),
                float(entry["max"]),
            )
            level_ranges.append(level_tuple)
            if lowest_range is None or level_tuple[1] < lowest_range[1]:
                lowest_range = level_tuple
            if highest_range is None or level_tuple[2] > highest_range[2]:
                highest_range = level_tuple

        def resolve_level(cost_value):
            if cost_value is None or not level_ranges:
                return None
            for level_name, vmin, vmax in level_ranges:
                if vmin <= cost_value <= vmax:
                    return level_name
            if lowest_range is not None and cost_value < lowest_range[1]:
                return lowest_range[0]
            if highest_range is not None and cost_value > highest_range[2]:
                return highest_range[0]
            return None

        for idx, (lbl, pvp) in enumerate(zip(self.lbFoodCosts, pvps)):
            lbl.setStyleSheet(default_style)
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
                try:
                    pct_value = float(pct)
                except (TypeError, ValueError):
                    pct_value = None
                if pct_value is None:
                    lbl.setText("--N/A--")
                else:
                    level_name = resolve_level(pct_value)
                    if level_name:
                        style = level_styles.get(level_name, default_style)
                        lbl.setStyleSheet(style)
                    lbl.setText(format_pt_number(pct_value))

    def _update_costs_from_table(self):
        """Recalculate total cost using the service layer."""
        try:
            total = self.service.calculate_cost(self.current_product)
            self.edCustoTotal.setText(self._format_currency_value(total))
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
        if getattr(self, "_resizing_lock", False):
            super().resizeEvent(ev)
            self._update_page_width()
            self._apply_ingredient_widths()
            self._apply_prep_autofit_or_scroll()
            self._resizing_lock = False
            return

        new_size = ev.size()
        old_size = ev.oldSize()
        new_width = max(1, new_size.width())
        new_height = max(1, new_size.height())
        old_width = old_size.width() if old_size.width() > 0 else new_width
        old_height = old_size.height() if old_size.height() > 0 else new_height

        width_change = abs(new_width - old_width)
        height_change = abs(new_height - old_height)
        aspect_ratio = self._window_aspect_ratio

        if width_change >= height_change:
            adjusted_width = new_width
            adjusted_height = int(round(adjusted_width * aspect_ratio))
        else:
            adjusted_height = new_height
            adjusted_width = int(round(adjusted_height / aspect_ratio))

        adjusted_width = max(1, adjusted_width)
        adjusted_height = max(1, adjusted_height)

        if adjusted_width != new_width or adjusted_height != new_height:
            self._resizing_lock = True
            self.resize(adjusted_width, adjusted_height)
            return

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
            user_display_lbl = lbl.property("userLabelDisplay")
            dev_lbl = lbl.property("devLabel")
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

        self._refresh_datastore()
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
