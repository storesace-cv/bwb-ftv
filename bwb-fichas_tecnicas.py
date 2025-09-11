#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- raiz móvel: adicionar ftv_project ao sys.path ---
import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent
_PKG  = _ROOT / 'ftv_project'
if str(_PKG) not in _sys.path:
    _sys.path.insert(0, str(_PKG))


import sys
from pathlib import Path

# --- Caminhos robustos ---
ROOT = Path(__file__).resolve().parent
FTV_PROJ = ROOT / "ftv_project"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if FTV_PROJ.exists() and str(FTV_PROJ) not in sys.path:
    sys.path.insert(0, str(FTV_PROJ))

# --- Qt ---
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from ftv.ui.ui_editor_fonte import FTApp
from ftv.data.datastore import DataStore

# --- UI principal ---

def _apply_global_theme(app):
    try:
        f = QFont()
        f.setPointSize(12)  # tamanho global 12pt
        app.setFont(f)
        # pode-se adicionar QSS leve aqui se precisares
    except Exception as e:
        print(f"[THEME] Falha a aplicar fonte global: {e}")


# === [AUTO-SAVE AUXILIARES] runtime shim =====================================
def _ensure_produto_attrs_schema(ds):
    try:
        if getattr(ds, "conn", None) is None:
            return
        cur = ds.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS produto_attrs (
                produto_codigo TEXT PRIMARY KEY,
                tipo_artigo    INTEGER,
                validade       INTEGER,
                temperatura    INTEGER
            )
        """)
        ds.conn.commit()
        print("[AutosaveAux] esquema OK (produto_attrs).")
    except Exception as e:
        print(f"[AutosaveAux][ERRO] schema: {e}")

def _read_attrs(ds, codigo):
    out = {"tipo_artigo": None, "validade": None, "temperatura": None}
    try:
        cur = ds.conn.cursor()
        cur.execute("SELECT tipo_artigo, validade, temperatura FROM produto_attrs WHERE produto_codigo=?", (codigo,))
        row = cur.fetchone()
        if row:
            out["tipo_artigo"], out["validade"], out["temperatura"] = row
    except Exception as e:
        print(f"[AutosaveAux][ERRO] read {codigo}: {e}")
    return out

def _write_attr(ds, codigo, campo, valor):
    try:
        cur = ds.conn.cursor()
        # upsert
        cur.execute("""
            INSERT INTO produto_attrs (produto_codigo, tipo_artigo, validade, temperatura)
            VALUES (?, NULL, NULL, NULL)
            ON CONFLICT(produto_codigo) DO NOTHING
        """, (codigo,))
        if campo == "tipo_artigo":
            cur.execute("UPDATE produto_attrs SET tipo_artigo=? WHERE produto_codigo=?", (valor, codigo))
        elif campo == "validade":
            cur.execute("UPDATE produto_attrs SET validade=? WHERE produto_codigo=?", (valor, codigo))
        elif campo == "temperatura":
            cur.execute("UPDATE produto_attrs SET temperatura=? WHERE produto_codigo=?", (valor, codigo))
        ds.conn.commit()
        print(f"[AutosaveAux] gravado {campo}={valor} para {codigo}")
    except Exception as e:
        print(f"[AutosaveAux][ERRO] write {campo}/{codigo}: {e}")

def _find_combo_candidates(win):
    """
    Tenta localizar as comboboxes por nomes comuns e por heurística (texto de rótulos).
    Retorna dict {"tipos": QComboBox|None, "validade": ..., "temp": ...}
    """
    from PyQt5.QtWidgets import QComboBox
    out = {"tipos": None, "validade": None, "temp": None}

    # 1) nomes típicos
    for name in ("cbTipos", "cbTipoArtigos", "cbTipo", "cbTiposArtigos"):
        w = getattr(win, name, None)
        if isinstance(w, QComboBox):
            out["tipos"] = w; break
    for name in ("cbValidade", "cbVal", "cbPrazo"):
        w = getattr(win, name, None)
        if isinstance(w, QComboBox):
            out["validade"] = w; break
    for name in ("cbTemp", "cbTemperatura", "cbTemperaturas"):
        w = getattr(win, name, None)
        if isinstance(w, QComboBox):
            out["temp"] = w; break

    # 2) fallback: varre children e tenta casar pelos itens/indícios
    def pick_by_clues(key, clue_words):
        if out[key] is not None:
            return
        for w in win.findChildren(QComboBox):
            try:
                text_join = " | ".join([w.itemText(i) for i in range(min(w.count(), 8))]).lower()
                if all(c in text_join for c in clue_words):
                    out[key] = w; return
            except Exception:
                pass

    # heurísticas: procuram padrões comuns
    pick_by_clues("tipos", ["—"])               # Tipos costuma ter "—" + descrições
    pick_by_clues("validade", ["h", "dia"])     # validade com horas/dias
    pick_by_clues("temp", ["frio", "ambiente"]) # temperaturas

    return out

def _wire_autosave_aux(FTApp_cls, ds):
    """
    Envolve FTApp._load_record para ler/gravar atributos auxiliares automaticamente.
    """
    if not hasattr(FTApp_cls, "_load_record"):
        print("[AutosaveAux][AVISO] FTApp não tem _load_record — nada a fazer.")
        return

    _ensure_produto_attrs_schema(ds)
    _orig = FTApp_cls._load_record

    def _set_combo_by_data(combo, target_value):
        if combo is None:
            return
        if target_value is None:
            return
        try:
            # Itens foram carregados via (cod, label) em .setItemData(index, cod)?
            # Tentamos primeiro por 'UserRole' (Qt.UserRole=32). Se não existir, tentamos texto direto.
            from PyQt5.QtCore import Qt
            for i in range(combo.count()):
                data = combo.itemData(i, role=Qt.UserRole)
                if data is None:
                    # fallback: tentar por data default (role=-1)
                    data = combo.itemData(i)
                if data == target_value:
                    combo.setCurrentIndex(i); return
            # último fallback por texto se target_value for string e coincidir com itemText
            tv = str(target_value)
            for i in range(combo.count()):
                if combo.itemText(i) == tv:
                    combo.setCurrentIndex(i); return
        except Exception as e:
            print(f"[AutosaveAux][ERRO] _set_combo_by_data: {e}")

    def _get_current_data(combo):
        if combo is None:
            return None
        try:
            from PyQt5.QtCore import Qt
            data = combo.currentData(role=Qt.UserRole)
            if data is None:
                data = combo.currentData()
            if data is None:
                # fallback texto
                return combo.currentText() or None
            return data
        except Exception:
            return None

    def _wrap(self, idx: int):
        # chama original para desenhar a UI
        _orig(self, idx)
        # localizar comboboxes
        combos = _find_combo_candidates(self)
        cb_tipos, cb_val, cb_temp = combos["tipos"], combos["validade"], combos["temp"]

        # ler attrs gravados e aplicar
        codigo = None
        try:
            codigo = self.ds.codigo_at(idx)
        except Exception:
            pass
        if not codigo:
            # alguns UIs usam self.cur_index já atualizado
            try:
                codigo = self.ds.codigo_at(self.cur_index)
            except Exception:
                pass

        if not codigo:
            return

        attrs = _read_attrs(self.ds, codigo)
        _set_combo_by_data(cb_tipos, attrs.get("tipo_artigo"))
        _set_combo_by_data(cb_val,   attrs.get("validade"))
        _set_combo_by_data(cb_temp,  attrs.get("temperatura"))

        # ligar sinais apenas uma vez por combobox
        def ensure_connected(combo, campo):
            if combo is None:
                return
            flag = f"__autosave_{campo}_wired"
            if getattr(combo, flag, False):
                return
            def on_change(_i):
                val = _get_current_data(combo)
                _write_attr(self.ds, codigo, campo, val)
            try:
                combo.currentIndexChanged.connect(on_change)
                setattr(combo, flag, True)
            except Exception as e:
                print(f"[AutosaveAux][ERRO] ligar '{campo}': {e}")

        ensure_connected(cb_tipos, "tipo_artigo")
        ensure_connected(cb_val,   "validade")
        ensure_connected(cb_temp,  "temperatura")

    FTApp_cls._load_record = _wrap
    print("[AutosaveAux] _load_record envolvido com auto-save.")

# === [/AUTO-SAVE AUXILIARES] ==================================================


def main():
    # Qt app
    app = QApplication(sys.argv)
    _apply_global_theme(app)

    # DataStore
    ds = DataStore()
    print(f"[LAUNCHER] DataStore importado de: {DataStore.__module__}")

    # Janela
    _wire_autosave_aux(FTApp, ds)

    win = FTApp(ds=ds)
    try:
        AutosaveAux(win, ds)
    except Exception as e:
        print(f"[AutosaveAux][AVISO] não consegui ligar autosave: {e}")
    win.show()

    # Loop
    sys.exit(app.exec_())


# === AutosaveAux (guardado) ===============================================
class AutosaveAux:
    """
    Liga autosave aos 3 comboboxes dos auxiliares com um guarda de carregamento.
    - Ignora eventos se self._loading == True (durante _load_record)
    - Valida/normaliza seleção (ignora '—', None, '')
    - Grava em produto_auxiliar (se existir), fallback produto_attrs
    """
    def __init__(self, app, ds):
        self.app = app
        self.ds = ds
        # Garante o atributo de guarda
        if not hasattr(self.app, "_loading"):
            self.app._loading = False
        # Envolve o _load_record
        self._wire_load_guard()
        # Liga os handlers dos combos
        self._wire_comboboxes()

    # ---------- guarda de carregamento ----------
    def _wire_load_guard(self):
        orig = getattr(self.app, "_load_record", None)
        if not callable(orig):
            print("[AutosaveAux][AVISO] _load_record não encontrado; autosave limitado.")
            return

        def wrapped_load(idx: int):
            # Guarda ON: ignoramos sinais
            self.app._loading = True
            try:
                return orig(idx)
            finally:
                # Guarda OFF
                self.app._loading = False

        setattr(self.app, "_load_record", wrapped_load)
        print("[AutosaveAux] _load_record envolvido com guard.")

    # ---------- localizar comboboxes ----------
    def _find_cb(self):
        # Preferência por objectName(s) usuais
        cb_tipo = getattr(self.app, "cbTipoArtigo", None)
        cb_valid = getattr(self.app, "cbValidade", None)
        cb_temp = getattr(self.app, "cbTemp", None)

        # Se algum faltar, varre os filhos à procura de QComboBox com pistas
        try:
            from PyQt5.QtWidgets import QComboBox
        except Exception:
            try:
                from PySide6.QtWidgets import QComboBox
            except Exception:
                QComboBox = None

        if QComboBox is not None:
            def contains_any(txt, keys):
                t = (txt or "").strip().lower()
                return any(k in t for k in keys)

            if cb_tipo is None or cb_valid is None or cb_temp is None:
                for cb in self.app.findChildren(QComboBox):
                    name = cb.objectName() or ""
                    if cb_tipo is None and contains_any(name, ["tipo", "art"]):
                        cb_tipo = cb
                    elif cb_valid is None and contains_any(name, ["val", "valid"]):
                        cb_valid = cb
                    elif cb_temp is None and contains_any(name, ["temp"]):
                        cb_temp = cb

        return cb_tipo, cb_valid, cb_temp

    # ---------- wiring ----------
    def _wire_comboboxes(self):
        cb_tipo, cb_valid, cb_temp = self._find_cb()
        wired = []

        def on_change(kind, get_value_callable):
            """Handler genérico — usa guarda e normaliza valor."""
            if getattr(self.app, "_loading", False):
                # Ignora eventos de carregamento
                return
            try:
                val_text, val_data = get_value_callable()
                # Normalização / ignorar placeholders
                if val_text in (None, "", "—") and val_data in (None, "", "—"):
                    norm = None
                else:
                    # Preferir data (id/código) se existir; senão, texto
                    norm = val_data if val_data not in (None, "", "—") else val_text

                codigo = None
                try:
                    codigo = self.app.ds.codigo_at(getattr(self.app, "cur_index", 0))
                except Exception:
                    # fallback (algumas UIs guardam último código carregado)
                    codigo = getattr(self.app, "last_codigo", None)

                if not codigo:
                    # como último recurso, tenta extrair de um label/campo
                    codigo = getattr(self.app, "edCodigo", None)
                    if codigo:
                        try:
                            codigo = codigo.text().strip()
                        except Exception:
                            codigo = None

                if not codigo:
                    print(f"[AutosaveAux][AVISO] Sem código de produto; ignorei {kind}={norm!r}")
                    return

                self._save(kind, codigo, norm)
            except Exception as e:
                print(f"[AutosaveAux][ERRO] {kind}: {e}")

        # Conectar cada combo com closure que lê (texto, dado) atual
        if cb_tipo is not None:
            def _get_tipo():
                i = cb_tipo.currentIndex()
                return cb_tipo.currentText(), cb_tipo.itemData(i)
            cb_tipo.currentIndexChanged.connect(lambda *_: on_change("tipo_artigo", _get_tipo))
            wired.append("tipo_artigo")

        if cb_valid is not None:
            def _get_valid():
                i = cb_valid.currentIndex()
                return cb_valid.currentText(), cb_valid.itemData(i)
            cb_valid.currentIndexChanged.connect(lambda *_: on_change("validade", _get_valid))
            wired.append("validade")

        if cb_temp is not None:
            def _get_temp():
                i = cb_temp.currentIndex()
                return cb_temp.currentText(), cb_temp.itemData(i)
            cb_temp.currentIndexChanged.connect(lambda *_: on_change("temperatura", _get_temp))
            wired.append("temperatura")

        if wired:
            print(f"[AutosaveAux] ligados: {', '.join(wired)}")
        else:
            print("[AutosaveAux][AVISO] Não encontrei os comboboxes dos auxiliares.")

    # ---------- persistência ----------
    def _save(self, kind: str, codigo: str, norm_value):
        """
        kind in ('tipo_artigo', 'validade', 'temperatura')
        norm_value é None, id/código (int/str) ou texto (fallback).
        """
        # Decide a tabela de destino
        use_prod_aux = False
        try:
            cur = self.ds.conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='produto_auxiliar'")
            use_prod_aux = (cur.fetchone() is not None)
        except Exception:
            pass

        if use_prod_aux:
            col = {"tipo_artigo": "tipo_artigo_id",
                   "validade": "validade_id",
                   "temperatura": "temperatura_id"}[kind]

            # DELETE quando norm_value é None
            if norm_value is None:
                sql = f"UPDATE produto_auxiliar SET {col}=NULL WHERE produto_codigo=?"
                args = (codigo,)
            else:
                # tenta converter para int (id). se falhar, mantém como está (algumas UIs podem passar código/str)
                try:
                    norm_id = int(norm_value)
                except Exception:
                    norm_id = None
                if norm_id is None:
                    # não há id — não escrevemos lixo. Apenas log.
                    print(f"[AutosaveAux][AVISO] {kind}: valor sem id ({norm_value!r}); não gravei.")
                    return
                # UPSERT
                sql = f"""
                    INSERT INTO produto_auxiliar (produto_codigo, {col})
                    VALUES (?, ?)
                    ON CONFLICT(produto_codigo) DO UPDATE SET {col}=excluded.{col}
                """
                args = (codigo, norm_id)

        else:
            # fallback antigo: produto_attrs (attr,value por produto)
            # apaga quando None; senão upsert
            if norm_value is None:
                sql = "DELETE FROM produto_attrs WHERE produto_codigo=? AND attr=?"
                args = (codigo, kind)
            else:
                sql = """
                    INSERT INTO produto_attrs (produto_codigo, attr, value)
                    VALUES (?, ?, ?)
                    ON CONFLICT(produto_codigo, attr) DO UPDATE SET value=excluded.value
                """
                args = (codigo, kind, str(norm_value))

        try:
            cur = self.ds.conn.cursor()
            cur.execute(sql, args)
            self.ds.conn.commit()
            print(f"[AutosaveAux] gravado {kind}={norm_value!r} para {codigo} ({'produto_auxiliar' if use_prod_aux else 'produto_attrs'})")
        except Exception as e:
            print(f"[AutosaveAux][ERRO] a gravar {kind} p/{codigo}: {e}")


if __name__ == "__main__":
    main()
