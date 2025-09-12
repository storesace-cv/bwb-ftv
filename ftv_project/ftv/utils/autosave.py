"""Utilities for wiring automatic save of auxiliary fields in FTApp."""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


def _ensure_produto_attrs_schema(ds):
    try:
        if getattr(ds, "conn", None) is None:
            return
        cur = ds.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS produto_attrs (
                produto_codigo TEXT PRIMARY KEY,
                tipo_artigo    INTEGER,
                validade       INTEGER,
                temperatura    INTEGER
            )
            """
        )
        ds.conn.commit()
        logger.info("[AutosaveAux] esquema OK (produto_attrs).")
    except Exception as e:
        logger.error("[AutosaveAux][ERRO] schema: %s", e)


def _read_attrs(ds, codigo):
    out = {"tipo_artigo": None, "validade": None, "temperatura": None}
    try:
        cur = ds.conn.cursor()
        cur.execute(
            "SELECT tipo_artigo, validade, temperatura FROM produto_attrs "
            "WHERE produto_codigo=?",
            (codigo,),
        )
        row = cur.fetchone()
        if row:
            out["tipo_artigo"], out["validade"], out["temperatura"] = row
    except Exception as e:
        logger.error("[AutosaveAux][ERRO] read %s: %s", codigo, e)
    return out


def _write_attr(ds, codigo, campo, valor):
    try:
        cur = ds.conn.cursor()
        cur.execute(
            """
            INSERT INTO produto_attrs (produto_codigo, tipo_artigo, validade,
            temperatura)
            VALUES (?, NULL, NULL, NULL)
            ON CONFLICT(produto_codigo) DO NOTHING
            """,
            (codigo,),
        )
        if campo == "tipo_artigo":
            cur.execute(
                "UPDATE produto_attrs SET tipo_artigo=? WHERE produto_codigo=?",
                (valor, codigo),
            )
        elif campo == "validade":
            cur.execute(
                "UPDATE produto_attrs SET validade=? WHERE produto_codigo=?",
                (valor, codigo),
            )
        elif campo == "temperatura":
            cur.execute(
                "UPDATE produto_attrs SET temperatura=? WHERE produto_codigo=?",
                (valor, codigo),
            )
        ds.conn.commit()
        logger.info("[AutosaveAux] gravado %s=%s para %s", campo, valor, codigo)
    except Exception as e:
        logger.error("[AutosaveAux][ERRO] write %s/%s: %s", campo, codigo, e)


def _find_combo_candidates(win):
    """
    Tenta localizar as comboboxes por nomes comuns e por heurística (texto de rótulos).
    Retorna dict {"tipos": QComboBox|None, "validade": ..., "temp": ...}
    """
    from PyQt5.QtWidgets import QComboBox

    out = {"tipos": None, "validade": None, "temp": None}

    for name in ("cbTipos", "cbTipoArtigos", "cbTipo", "cbTiposArtigos"):
        w = getattr(win, name, None)
        if isinstance(w, QComboBox):
            out["tipos"] = w
            break
    for name in ("cbValidade", "cbVal", "cbPrazo"):
        w = getattr(win, name, None)
        if isinstance(w, QComboBox):
            out["validade"] = w
            break
    for name in ("cbTemp", "cbTemperatura", "cbTemperaturas"):
        w = getattr(win, name, None)
        if isinstance(w, QComboBox):
            out["temp"] = w
            break

    def pick_by_clues(key, clue_words):
        if out[key] is not None:
            return
        for w in win.findChildren(QComboBox):
            try:
                text_join = " | ".join(
                    [w.itemText(i) for i in range(min(w.count(), 8))]
                ).lower()
                if all(c in text_join for c in clue_words):
                    out[key] = w
                    return
            except Exception:
                pass

    pick_by_clues("tipos", ["—"])
    pick_by_clues("validade", ["h", "dia"])
    pick_by_clues("temp", ["frio", "ambiente"])

    return out


def wire_autosave_aux(FTApp_cls, ds):
    """Envolve ``FTApp._load_record`` para gerir atributos auxiliares."""
    if not hasattr(FTApp_cls, "_load_record"):
        logger.warning(
            "[AutosaveAux][AVISO] FTApp não tem _load_record — nada a fazer."
        )
        return

    _ensure_produto_attrs_schema(ds)
    _orig = FTApp_cls._load_record

    def _set_combo_by_data(combo, target_value):
        if combo is None or target_value is None:
            return
        try:
            from PyQt5.QtCore import Qt

            for i in range(combo.count()):
                data = combo.itemData(i, role=Qt.UserRole)
                if data is None:
                    data = combo.itemData(i)
                if data == target_value:
                    combo.setCurrentIndex(i)
                    return
            tv = str(target_value)
            for i in range(combo.count()):
                if combo.itemText(i) == tv:
                    combo.setCurrentIndex(i)
                    return
        except Exception as e:
            logger.error("[AutosaveAux][ERRO] _set_combo_by_data: %s", e)

    def _get_current_data(combo):
        if combo is None:
            return None
        try:
            from PyQt5.QtCore import Qt

            data = combo.currentData(role=Qt.UserRole)
            if data is None:
                data = combo.currentData()
            if data is None:
                return combo.currentText() or None
            return data
        except Exception:
            return None

    def _wrap(self, idx: int):
        _orig(self, idx)
        combos = _find_combo_candidates(self)
        cb_tipos, cb_val, cb_temp = (
            combos["tipos"],
            combos["validade"],
            combos["temp"],
        )

        codigo = None
        try:
            codigo = self.ds.codigo_at(idx)
        except Exception:
            pass
        if not codigo:
            try:
                codigo = self.ds.codigo_at(self.cur_index)
            except Exception:
                pass
        if not codigo:
            return

        attrs = _read_attrs(self.ds, codigo)
        _set_combo_by_data(cb_tipos, attrs.get("tipo_artigo"))
        _set_combo_by_data(cb_val, attrs.get("validade"))
        _set_combo_by_data(cb_temp, attrs.get("temperatura"))

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
                logger.error("[AutosaveAux][ERRO] ligar '%s': %s", campo, e)

        ensure_connected(cb_tipos, "tipo_artigo")
        ensure_connected(cb_val, "validade")
        ensure_connected(cb_temp, "temperatura")

    FTApp_cls._load_record = _wrap
    logger.info("[AutosaveAux] _load_record envolvido com auto-save.")
