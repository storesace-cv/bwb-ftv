# --- Qt Widgets import bootstrap (debug-friendly) ---
# Tenta importar classes usadas nas anotações e utilitários.
# Se PyPyQt5 falhar, tenta a outra binding. Em último caso, mostra erros claros.
try:
    from PyQt5.QtWidgets import QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
except Exception as _e1:
    try:
        from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
        print("[Qt Import] Usar binding alternativo de Qt (fallback).")
    except Exception as _e2:
        print("[Qt Import][ERRO] Falhou importar QtWidgets em PyQt5 e PySide6.")
        print(" - Primeiro erro:", _e1)
        print(" - Segundo  erro:", _e2)
        raise
# --- fim do bootstrap Qt ---

from pathlib import Path
from .repositories import ProdutosRepo, IngredientesRepo, AuxiliaresRepo, PreparacaoRepo
import os
import json
import sqlite3

class DataStore:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(".", "databases", "ftv.db")
        self.db_path = db_path
        self.demo = False
        self.conn = None
        if os.path.exists(db_path):
            try:
                self.conn = sqlite3.connect(db_path)
                self.conn.row_factory = sqlite3.Row
            except Exception:
                self.demo = True
        else:
            self.demo = True
        self.ids = self._load_ids()
        if not self.demo and self.conn:
            # Repositories (Fase 2)
            try:
                self.produtos = ProdutosRepo(self.conn)
                self.ingredientes = IngredientesRepo(self.conn)
                self.aux = AuxiliaresRepo(self.conn)
                self.prep = PreparacaoRepo(self.conn)
            except Exception:
                self.produtos = None; self.ingredientes = None; self.aux = None; self.prep = None
            self._ensure_preparacao_table()

        if self.demo or not self.conn or getattr(self, 'produtos', None) is None:
            return []
        # Auto-migração (Fase 3)
        try:
            self._run_migrations()
        except Exception as e:
            print(f"[AutoMigração][ERRO] {e}")

    # Auto-patch: garantir cache de códigos
    try:
        self._ids  # já existe?
    except Exception:
        self._ids = []
    try:
        self.reload_ids()
    except Exception as e:
        print(f"[DataStore][AVISO] reload_ids falhou: {e}")
        return self.produtos.listar_codigos()



    def list_active_allergens(self):
        """Se existir BD com alergenios( id,nome,ativo ), usa; senão tenta allergens.json; fallback lista fixa."""
        if self.conn and not self.demo:
            try:
                cur = self.conn.cursor()
                cur.execute("SELECT id, nome FROM alergenios WHERE ativo=1 ORDER BY nome")
                rows = cur.fetchall()
                if rows:
                    return [(r["id"], r["nome"]) for r in rows]
            except Exception:
                pass
        # JSON ao lado (facilita testes)
        json_path = os.path.join(os.path.dirname(__file__), "allergens.json")
        names = []
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            names = [ (i+1, item["name"]) for i, item in enumerate(data.get("allergens", [])) ]
        except Exception:
            names = [(1,"Glúten"),(2,"Crustáceos"),(3,"Ovos"),(4,"Peixe"),(5,"Amendoins"),(6,"Soja"),
                     (7,"Leite"),(8,"Frutos de casca rija"),(9,"Aipo"),(10,"Mostarda"),(11,"Sementes de sésamo"),
                     (12,"Dióxido de enxofre e sulfitos"),(13,"Tremoço"),(14,"Moluscos")]
        return names


    def get_pvps(self, codigo):
        """Devolve PVP1..PVP5 (gross). Na BD atual só existem PVP1 e PVP2; os restantes ficam a None."""
        if self.demo or not self.conn or getattr(self, 'produtos', None) is None:
            return {"pvp1": None, "pvp2": None, "pvp3": None, "pvp4": None, "pvp5": None}
        return self.produtos.get_pvps(codigo)


        if self.demo or not self.conn or getattr(self, 'aux', None) is None:
            return [(None, "—")]
        return self.aux.list_tipos_artigos()

        if self.demo or not self.conn or getattr(self, 'aux', None) is None:
            return []
        return self.aux.list_validade()

        if self.demo or not self.conn or getattr(self, 'aux', None) is None:
            return []
        return self.aux.list_temperaturas()


    # ---------- [B4] Preparação: persistência ----------
    def _ensure_preparacao_table(self):
            try:
                if not getattr(self, "conn", None):
                    return
                cur = self.conn.cursor()
                cur.executescript(
                    "PRAGMA foreign_keys = ON;"
                    "CREATE TABLE IF NOT EXISTS produto_preparacao ("
                    "  produto_codigo TEXT PRIMARY KEY,"
                    "  html TEXT NOT NULL DEFAULT '',"
                    "  FOREIGN KEY (produto_codigo) REFERENCES produtos(codigo) "
                    "    ON UPDATE CASCADE ON DELETE CASCADE"
                    ");"
                    "CREATE INDEX IF NOT EXISTS idx_produto_preparacao_codigo "
                    "  ON produto_preparacao(produto_codigo);"
                )
                self.conn.commit()
            except Exception as e:
                import traceback as _tb
                print(f"[AutoMigração][ERRO] {e}")
                _tb.print_exc()
    def _run_migrations(self):
        """
        Executa migrações idempotentes necessárias (Fase 3).
        - Corre ftv_project/ftv/data/migrations/preparacao.sql se existir.
        - Não levanta exceções (não interrompe a app).
        """
        try:
            if not getattr(self, "conn", None):
                return
            from pathlib import Path as _Path
            sql_path = _Path(".").resolve() / "ftv_project" / "ftv" / "data" / "migrations" / "preparacao.sql"
            if not sql_path.exists():
                # Log silencioso e técnico
                print(f"[AutoMigração] SQL não encontrado: {sql_path}")
                return
            sql = sql_path.read_text(encoding="utf-8")
            cur = self.conn.cursor()
            cur.executescript(sql)
            self.conn.commit()
            print("[AutoMigração] preparacao.sql aplicado/validado.")
        except Exception as e:
            import traceback as _tb
            print(f"[AutoMigração][ERRO] Falha ao aplicar preparacao.sql: {e}")
            _tb.print_exc()
            # não relançar para não quebrar o arranque/UI

# ------------------------ UI Helpers ------------------------

def make_readonly_lineedit(le: "QLineEdit", bold=False):
    le.setReadOnly(True)
    le.setFrame(False)
    le.setStyleSheet("border:none; background:transparent;")
    f = le.font(); f.setBold(bold); le.setFont(f)

def match_font(lbl: "QLabel", ref: "QLineEdit"):
    f = QFont(ref.font()); lbl.setFont(f)


    # --- Métodos de paginação/ids garantidos (auto-patch) ---
    def _load_all_codes_from_db(self):
        """Devolve lista de códigos a partir de 'produtos'; se vazio, tenta 'fichas_tecnicas'."""
        try:
            cur = self.conn.cursor()
            try:
                cur.execute("SELECT DISTINCT codigo FROM produtos ORDER BY codigo")
                rows = [r[0] for r in cur.fetchall() if r and r[0] not in (None, "")]
            except Exception:
                rows = []
            if not rows:
                try:
                    cur.execute("SELECT DISTINCT produto_codigo FROM fichas_tecnicas ORDER BY produto_codigo")
                    rows = [r[0] for r in cur.fetchall() if r and r[0] not in (None, "")]
                except Exception:
                    rows = []
            return rows or []
        except Exception:
            return []

    def reload_ids(self):
        """Recarrega a cache de códigos."""
        if getattr(self, 'demo', False) or not getattr(self, 'conn', None):
            self._ids = []
            try:
                self.ids = self._ids
            except Exception:
                pass
            return len(self._ids)
        self._ids = self._load_all_codes_from_db()
        try:
            self.ids = self._ids
        except Exception:
            pass
        return len(self._ids)

    def total(self):
        """Total de registos disponíveis."""
        try:
            if hasattr(self, '_ids') and isinstance(self._ids, list):
                return len(self._ids)
        except Exception:
            pass
        try:
            return len(self.ids)  # compat
        except Exception:
            return 0

    def codigo_at(self, idx: int):
        """Código na posição idx (ou None se fora dos limites)."""
        try:
            if idx is None: 
                return None
            if idx < 0: 
                return None
            if hasattr(self, '_ids') and isinstance(self._ids, list):
                return self._ids[idx] if idx < len(self._ids) else None
            if hasattr(self, 'ids') and isinstance(self.ids, list):
                return self.ids[idx] if idx < len(self.ids) else None
        except Exception:
            return None
        return None
def stack_combo(title: str):
    w = QWidget()
    v = QVBoxLayout(w); v.setContentsMargins(0,0,0,0); v.setSpacing(2)
    lbl = QLabel(title); v.addWidget(lbl, 0, Qt.AlignLeft|Qt.AlignVCenter)
    cb = QComboBox(); cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    v.addWidget(cb, 0)
    return w, cb

# ------------------------ Zone (Cell) System ------------------------

def bg_for_level(level:int):
    colors = ["#eafbf1","#eef5ff","#fff5e8","#f7f0ff","#fff0f0"]
    return colors[level % len(colors)] if DEV_OVERLAYS else "transparent"

class Zone(QWidget):
    """Célula real (com tag e overlay opcional)."""
    def __init__(self, tag: str, parent=None, flow="v", margins=8, spacing=6, level:int=0, show_overlays:bool=True):
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
            self.setStyleSheet(f"background:{bg_for_level(self._level)}; border:1px dashed red;")
            self._tag_lbl.show()
        else:
            self.setStyleSheet("")
            self._tag_lbl.hide()
        for ch in self.findChildren(Zone):
            ch.apply_overlays(on)

    def add(self, w: "QWidget", stretch:int=0):
        self.ly.addWidget(w, stretch)

    def add_row(self, label_text: str, value_widget: "QWidget", label_minw: int=None, vspacing: int=2):
        row = QWidget(self); row.setStyleSheet("border:none; background:transparent;")
        grid = QGridLayout(row); grid.setContentsMargins(0,0,0,0)
        grid.setHorizontalSpacing(12); grid.setVerticalSpacing(vspacing)
        grid.setColumnStretch(1,1)
        lbl = QLabel(label_text, row); lbl.setStyleSheet("border:none; background:transparent;")
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        if label_minw: lbl.setFixedWidth(label_minw)
        value_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        try:
            value_widget.setStyleSheet(value_widget.styleSheet() + "border:none; background:transparent;")
        except Exception:
            pass
        grid.addWidget(lbl, 0, 0, alignment=Qt.AlignVCenter | Qt.AlignRight)
        grid.addWidget(value_widget, 0, 1, alignment=Qt.AlignVCenter | Qt.AlignLeft)
        self.ly.addWidget(row)
        self._labels.append(lbl); self.sync_label_widths()
        return lbl

    def sync_label_widths(self):
        if not self._labels: return
        maxw = max(l.sizeHint().width() for l in self._labels)
        for l in self._labels: l.setFixedWidth(maxw)

    def split_h(self, ratios=(1,1)):
        cont = QWidget(self); cont.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        h = QHBoxLayout(cont); h.setContentsMargins(0,0,0,0); h.setSpacing(self.ly.spacing())
        left  = Zone(self.tag + ".A", cont, flow='v', margins=4, spacing=self.ly.spacing(), level=self._level+1, show_overlays=DEV_OVERLAYS)
        right = Zone(self.tag + ".B", cont, flow='v', margins=4, spacing=self.ly.spacing(), level=self._level+1, show_overlays=DEV_OVERLAYS)
        h.addWidget(left, ratios[0]); h.addWidget(right, ratios[1])
        self.ly.addWidget(cont, 1)
        return left, right

    def split_v(self, ratios=(1,1)):
        cont = QWidget(self); cont.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        v = QVBoxLayout(cont); v.setContentsMargins(0,0,0,0); v.setSpacing(self.ly.spacing())
        top    = Zone(self.tag + ".1", cont, flow='v', margins=4, spacing=self.ly.spacing(), level=self._level+1, show_overlays=DEV_OVERLAYS)
        bottom = Zone(self.tag + ".2", cont, flow='v', margins=4, spacing=self.ly.spacing(), level=self._level+1, show_overlays=DEV_OVERLAYS)
        v.addWidget(top, ratios[0]); v.addWidget(bottom, ratios[1])
        self.ly.addWidget(cont, 1)
        return top, bottom

# ------------------------ Main App ------------------------

class FTApp(QWidget):
    def __init__(self, ds: DataStore):
        super().__init__()
        self.ds = ds
        self.cur_index = 0
        self._build_ui()
        self._connect_nav()
        # [B4] Persistência — estado e autosave (sem alterações de UI)
        self._current_codigo = ""
        self._prep_dirty = False
        self._prep_last_hash = ""
        from PyQt5.QtCore import QTimer
        self._prep_autosave = QTimer(self)
        self._prep_autosave.setSingleShot(True)
        self._prep_autosave.setInterval(800)
        self._prep_autosave.timeout.connect(self._save_prep_if_needed)
        try:
            self.edPrep.textChanged.connect(self._on_prep_changed)
        except Exception:
            pass
        self._load_record(self.cur_index)

    def _section_box(self, title: str, zone: Zone) -> "QGroupBox":
        box = QGroupBox(title); box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        ly = QVBoxLayout(box); ly.setContentsMargins(8,8,8,8); ly.setSpacing(8)
        ly.addWidget(zone)
        return box

    def _build_ui(self):
        self.setWindowTitle(APP_TITLE)
        self.resize(1180, 860)
        root = QVBoxLayout(self); root.setContentsMargins(8,8,8,8); root.setSpacing(8)

        # --- Top bar: Overlay (esq) + Menu (dir) ---
        top = QHBoxLayout(); top.setContentsMargins(0,0,0,0); top.setSpacing(8)
        self.btOverlay = QPushButton("Overlays: ON"); self.btOverlay.clicked.connect(self._toggle_overlays_btn)
        top.addWidget(self.btOverlay, 0, Qt.AlignLeft)
        top.addStretch(1)
        from PyQt5.QtWidgets import QToolButton, QMenu, QAction
        self.btMenu = QToolButton(); self.btMenu.setText("Menu"); self.btMenu.setPopupMode(QToolButton.InstantPopup)
        self.mnuRoot = QMenu(self)
        mBD = QMenu("Base de Dados", self.mnuRoot)
        actUpdate = QAction("Atualizar BD", self); actReload = QAction("Recarregar Dados", self)
        mBD.addAction(actUpdate); mBD.addAction(actReload); self.mnuRoot.addMenu(mBD)
        mTab = QMenu("Tabelas", self.mnuRoot)
        actTipos = QAction("Tipos Artigos", self)
        actVal   = QAction("Validade", self)
        actTemps = QAction("Temperaturas", self)
        mTab.addAction(actTipos); mTab.addAction(actVal); mTab.addAction(actTemps)
        self.mnuRoot.addMenu(mTab)
        mUtil = QMenu("Utilitários", self.mnuRoot)
        actTheme = QAction("Tema", self); mUtil.addAction(actTheme); self.mnuRoot.addMenu(mUtil)
        self.btMenu.setMenu(self.mnuRoot)
        # ligações básicas
        actReload.triggered.connect(lambda: self._load_record(self.cur_index))
        actUpdate.triggered.connect(lambda: "QMessageBox".information(self, "Atualizar BD", "Integração de importação/atualização será ligada aqui."))
        actTipos.triggered.connect(lambda: "QMessageBox".information(self, "Tipos de Artigos", f"Ativos: {len(self.ds.list_tipos_artigos())-1}"))
        actVal.triggered.connect(lambda: "QMessageBox".information(self, "Validade", f"Ativos: {len(self.ds.list_validade())-1}"))
        actTemps.triggered.connect(lambda: "QMessageBox".information(self, "Temperaturas", f"Ativos: {len(self.ds.list_temperaturas())-1}"))
        actTheme.triggered.connect(lambda: "QMessageBox".information(self, "Tema", "Alternância de tema pendente."))
        top.addWidget(self.btMenu, 0, Qt.AlignRight)
        root.addLayout(top)

        # --- Conteúdo com scroll vertical ---
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        page = QWidget(); page_ly = QVBoxLayout(page); page_ly.setContentsMargins(0,0,0,0); page_ly.setSpacing(8)
        scroll.setWidget(page); page.setMinimumWidth(1100)
        root.addWidget(scroll, 1)

        # ---------------- B1 — Dados Gerais (C1) ----------------
        self.C1 = Zone("C1", self, flow="v", level=0, show_overlays=DEV_OVERLAYS)
        page_ly.addWidget(self._section_box("[B1] - Dados Gerais", self.C1), 0)

        C1A, C1B = self.C1.split_h((3,1))
        C1A1, C1A2 = C1A.split_v((1,3))

        lbl_w = 110
        self.edCodigo = QLineEdit(); make_readonly_lineedit(self.edCodigo, False)
        self.edNome   = QLineEdit(); make_readonly_lineedit(self.edNome, True)
        C1A1.add_row("Código:", self.edCodigo, label_minw=lbl_w, vspacing=2)
        C1A1.add_row("Nome do Artigo:", self.edNome, label_minw=lbl_w, vspacing=2)

        # C1.A.2        # C1.A.2
        C1A21, C1A22 = C1A2.split_h((3,1))              # C1.A.2.A (famílias/PVPs) + C1.A.2.B (combos)
        # C1.A.2.A → divide verticalmente: topo (famílias) + base (PVP1..PVP5)
        C1A21_top, C1A21_base = C1A21.split_v((1,2))
        C1A21_top.apply_overlays(True)
        self.lbFamiliaVal = QLabel(""); self.lbSubFamiliaVal = QLabel("")
        match_font(self.lbFamiliaVal, self.edNome); match_font(self.lbSubFamiliaVal, self.edNome)
        C1A21_top.add_row("Família:", self.lbFamiliaVal, label_minw=lbl_w, vspacing=0)
        C1A21_top.add_row("Sub-família:", self.lbSubFamiliaVal, label_minw=lbl_w, vspacing=0)

        # Base: cinco colunas iguais com PVP1..PVP5 (etiqueta por cima)
        P1, P2 = C1A21_base.split_h((1,1))
        P11, P12 = P1.split_h((1,1))
        P111, P112 = P11.split_h((1,1))
        # Agora temos 5 zonas: P111, P112, P12.A, P12.B, (criar quinta)
        # Para simplicidade, recriamos com um loop que adiciona 5 colunas iguais
        C1A21_base.ly.takeAt(0)
        C1A21_base.ly.takeAt(0)
        # Reconstruir base em 5 colunas iguais
        base_cont = QWidget(C1A21_base); base_h = QHBoxLayout(base_cont); base_h.setContentsMargins(0,0,0,0); base_h.setSpacing(C1A21_base.ly.spacing())
        C1A21_base.ly.addWidget(base_cont, 1)
        self.lbPVP = []
        for i in range(5):
            col = Zone(f"C1.A.2.A.P{i+1}", base_cont, flow='v', margins=2, spacing=2, level=C1A21_base._level+1, show_overlays=DEV_OVERLAYS)
            lbl = QLabel(f"PVP{i+1}")
            val = QLabel("—"); make_readonly_lineedit(QLineEdit(), False)  # just to get style, we'll style label
            val.setStyleSheet("border:none; background:transparent; font-weight:600;")
            col.add(lbl, 0); col.add(val, 0)
            self.lbPVP.append(val)
            base_h.addWidget(col, 1)

        # Combos diretamente em C1.A.2.B (sem .B.2)
        w_tipos, self.cbTipos = stack_combo("Tipos Artigos")
        w_val,   self.cbValidade = stack_combo("Validade")
        w_temp,  self.cbTemp = stack_combo("Temperaturas")
        C1A22.add(w_tipos); C1A22.add(w_val); C1A22.add(w_temp)

        # C1.B — placeholder de preview
        prev = QLabel("Pré-visualização"); prev.setAlignment(Qt.AlignCenter)
        prev.setStyleSheet("border:1px solid #ccc; padding:8px;")
        C1B.add(prev, 1)

        # ---------------- B2 — Ingredientes (C2) ----------------
        self.C2 = Zone("C2", self, flow="v", level=0, show_overlays=DEV_OVERLAYS)
        page_ly.addWidget(self._section_box("[B2] - Ingredientes", self.C2), 0)

        self.tbIng = QTableWidget(0, 6, self)
        self.tbIng.setHorizontalHeaderLabels(["Ingrediente","QTD","U.M.","PPU","Total","Código"])
        self.tbIng.verticalHeader().setVisible(False)
        self.tbIng.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.C2.add(self.tbIng, 1)
        self._setup_ing_columns()

        # ---------------- B3 — Custos (C3) ----------------
        self.C3 = Zone("C3", self, flow="v", level=0, show_overlays=DEV_OVERLAYS)
        page_ly.addWidget(self._section_box("[B3] - Custos", self.C3), 0)

        C3A = Zone("C3.A", self.C3, flow="v", level=1, show_overlays=DEV_OVERLAYS)
        self.C3.add(C3A, 1)
        C3AA, C3AB = C3A.split_h((1,1))

        # C3 swap aplicado: C3.A.A = Custo Total | C3.A.B = "Food Cost:"
        ct_row = QWidget(); ct_ly = QVBoxLayout(ct_row); ct_ly.setContentsMargins(0,0,0,0); ct_ly.setSpacing(4)
        ct_ly.addWidget(QLabel("Custo Total:"))
        self.edCustoTotal = QLineEdit(); make_readonly_lineedit(self.edCustoTotal, True)
        ct_ly.addWidget(self.edCustoTotal)
        C3AA.add(ct_row, 0)

        C3AB.add(QLabel("Food Cost:"), 0)

        # ---------------- B4 — Preparação (C4) ----------------
        self.C4 = Zone("C4", self, flow="v", level=0, show_overlays=DEV_OVERLAYS)
        page_ly.addWidget(self._section_box("[B4] - Preparação", self.C4), 1)

        # Simples toolbar "demo" e editor
        tb = QHBoxLayout(); tb.setContentsMargins(0,0,0,0); tb.setSpacing(6)
        for txt in ["↥","↶","B","I","U","→","⇔","≡","1.","•"]:
            b=QPushButton(txt); b.setFixedSize(28,22); tb.addWidget(b)
        tbw = QWidget(); tbw.setLayout(tb)
        self.C4.add(tbw, 0)

        self.edPrep = QTextEdit(); self.edPrep.setPlaceholderText("— Texto de preparação —")
        self.C4.add(self.edPrep, 1)

        # ---------------- B5 — Nutrição / Alergénios (C5) ----------------
        self.C5 = Zone("C5", self, flow="v", level=0, show_overlays=DEV_OVERLAYS)
        page_ly.addWidget(self._section_box("[B5] - Nutrição / Alergénios", self.C5), 0)

        self._build_allergens_grid()

        # --- Rodapé: navegação centrada + contador ---
        footer = QHBoxLayout(); footer.setContentsMargins(0,0,0,0); footer.setSpacing(8)
        footer.addStretch(1)
        self.btFirst = QPushButton("◀◀ Primeiro")
        self.btPrev  = QPushButton("◀ Anterior")
        self.lbPos   = QLabel("1 / 1")
        self.btNext  = QPushButton("Seguinte ▶")
        self.btLast  = QPushButton("Último ▶▶")
        footer.addWidget(self.btFirst); footer.addWidget(self.btPrev)
        footer.addWidget(self.lbPos)
        footer.addWidget(self.btNext); footer.addWidget(self.btLast)
        footer.addStretch(1)
        root.addLayout(footer)

        # Atalho teclado para overlays
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self._toggle_overlays)

    # ---------- Alergénios grid ----------
    def _build_allergens_grid(self):
        names = self.ds.list_active_allergens()
        gridw = QWidget()
        grid = QGridLayout(gridw); grid.setContentsMargins(0,0,0,0); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(6)
        cols = 2
        for i,(aid, nome) in enumerate(names):
            r = i//cols; c = i%cols
            cb = QCheckBox(nome)
            grid.addWidget(cb, r, c, alignment=Qt.AlignLeft)
        self.C5.add(gridw, 0)

    # ---------- Ingredientes: colunas ----------
    def _setup_ing_columns(self):
        w = max(self.width(), 1100)
        self.tbIng.setColumnHidden(5, True)
        self.tbIng.setColumnWidth(0, int(w*0.50))
        self.tbIng.setColumnWidth(1, int(w*0.10))
        self.tbIng.setColumnWidth(2, int(w*0.10))
        self.tbIng.setColumnWidth(3, int(w*0.14))
        self.tbIng.setColumnWidth(4, int(w*0.16))

    def _apply_ingredient_widths(self):
        self._setup_ing_columns()

    # ---------- Navegação ----------
    def _connect_nav(self):
        self.btFirst.clicked.connect(lambda: self._goto(0))
        self.btPrev.clicked.connect(lambda: self._go(-1))
        self.btNext.clicked.connect(lambda: self._go(+1))
        self.btLast.clicked.connect(lambda: self._goto(self.ds.total()-1))

    def _goto(self, idx):
        self.cur_index = max(0, min(idx, self.ds.total()-1))
        try:
            self._save_prep_if_needed(force=True)
        except Exception:
            pass

        self._load_record(self.cur_index)

    def _go(self, delta):
        self.cur_index = (self.cur_index + delta) % max(1, self.ds.total())
        try:
            self._save_prep_if_needed(force=True)
        except Exception:
            pass

        self._load_record(self.cur_index)
    # ---------- [B4] Persistência: handlers ----------
    def _on_prep_changed(self):
        self._prep_dirty = True
        try:
            self._prep_autosave.start()
        except Exception:
            pass

    def _save_prep_if_needed(self, force: bool=False):
        try:
            if not getattr(self, "_current_codigo", ""):
                return
            html = self.edPrep.toHtml()
            import hashlib as _hl
            h = _hl.sha256(html.encode("utf-8")).hexdigest()
            if force or (self._prep_dirty and h != self._prep_last_hash):
                self.ds.save_preparacao_html(self._current_codigo, html)
                self._prep_last_hash = h
                self._prep_dirty = False
        except Exception:
            pass

    def closeEvent(self, ev):
        try:
            self._save_prep_if_needed(force=True)
        except Exception:
            pass
        super().closeEvent(ev)


    # ---------- Carregamento de dados ----------
    def _load_record(self, idx: int):
        codigo = self.ds.codigo_at(idx) or "10001"
        p = self.ds.get_produto_info(codigo)
        self.edCodigo.setText(p.get("codigo",""))
        self.edNome.setText(p.get("nome",""))
        self.lbFamiliaVal.setText(p.get("familia",""))
        self.lbSubFamiliaVal.setText(p.get("subfamilia",""))
        # PVPs
        pvps = self.ds.get_pvps(codigo)
        values = [pvps.get("pvp1"), pvps.get("pvp2"), pvps.get("pvp3"), pvps.get("pvp4"), pvps.get("pvp5")]
        for i, val in enumerate(values):
            txt = "—" if val in (None, "",) else f"{float(val):.2f}"
            if i < len(self.lbPVP):
                self.lbPVP[i].setText(txt)


        self.cbTipos.clear(); self.cbValidade.clear(); self.cbTemp.clear()
        # Preencher combos a partir da BD (ou demo)
        self.cbTipos.addItems([])  # reset
        self.cbValidade.addItems([])
        self.cbTemp.addItems([])
        # [B4] Preparação — carregar HTML do produto atual
        self._current_codigo = codigo
        try:
            html = self.ds.get_preparacao_html(codigo) or ""
            self.edPrep.blockSignals(True)
            try:
                self.edPrep.setHtml(html)
            finally:
                self.edPrep.blockSignals(False)
            import hashlib as _hl
            self._prep_last_hash = _hl.sha256(self.edPrep.toHtml().encode("utf-8")).hexdigest()
            self._prep_dirty = False
        except Exception:
            pass



        # Tipos Artigos
        self.cbTipos.clear()
        for cod, desc in self.ds.list_tipos_artigos():
            self.cbTipos.addItem(desc, cod)

        # Validade
        self.cbValidade.clear()
        for cod, desc in self.ds.list_validade():
            self.cbValidade.addItem(desc, cod)

        # Temperaturas
        self.cbTemp.clear()
        for cod, desc in self.ds.list_temperaturas():
            self.cbTemp.addItem(desc, cod)

        # Pré-selecionar pelos FKs do produto (se existirem)
        def _select_by_code(combo, code_value):
            if code_value is None: return
            for i in range(combo.count()):
                if combo.itemData(i) == code_value:
                    combo.setCurrentIndex(i); return

        _select_by_code(self.cbTipos, p.get("tipo_artigo_cod"))
        _select_by_code(self.cbValidade, p.get("validade_cod"))
        _select_by_code(self.cbTemp, p.get("temperatura_cod"))
        self.cbTipos.addItems(["—","Matéria-prima","Preparado","Acabado"])
        self.cbValidade.addItems(["—","24h","48h","72h","7 dias"])
        self.cbTemp.addItems(["—","Frio positivo","Frio negativo","Ambiente"])

        data = self.ds.get_ingredientes(codigo)
        self.tbIng.setRowCount(0)
        for row in data:
            r = self.tbIng.rowCount(); self.tbIng.insertRow(r)
            vals = [
                str(row.get("nome","")),
                str(row.get("qtd",0)),
                str(row.get("unidade","")),
                f'{row.get("ppu",0):.2f}',
                f'{row.get("total",0):.2f}',
                str(row.get("codigo","")),
            ]
            for c, val in enumerate(vals):
                it = QTableWidgetItem(val); it.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
                self.tbIng.setItem(r, c, it)

        self._apply_ingredient_widths()
        self._update_costs_from_table()
        self.lbPos.setText(f"{self.cur_index+1} / {max(1,self.ds.total())}")

    # ---------- Cálculos ----------
    def _update_costs_from_table(self):
        """Soma a coluna 'Total' (índice 4) da tabela de ingredientes e escreve em C3.A.A (edCustoTotal)."""
        try:
            total = 0.0
            for r in range(self.tbIng.rowCount()):
                it = self.tbIng.item(r, 4)
                if not it: continue
                s = it.text().strip().replace(",", ".")
                try: total += float(s)
                except ValueError: pass
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
            if z.tag.count('.') == 0:
                z.apply_overlays(DEV_OVERLAYS)

    def _toggle_overlays_btn(self):
        self._toggle_overlays()
        self.btOverlay.setText(f"Overlays: {'ON' if DEV_OVERLAYS else 'OFF'}")

# ------------------------ Main ------------------------

def main():
    app = QApplication(sys.argv)
    ds = DataStore()
    w = FTApp(ds); w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
