# flake8: noqa

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import types
from PyQt5.QtWidgets import QTextEdit, QWidget, QShortcut

from data.datastore import DataStore
from ui.ui_editor_fonte import FTApp


# ------- Helpers -------


def _make_datastore():
    ds = DataStore(db_path=":memory:")
    ds.conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ProdutoPreparacao (
            ProdutoCodigo TEXT PRIMARY KEY,
            Html TEXT NOT NULL DEFAULT ''
        )
        """
    )
    ds.conn.commit()
    return ds


def _make_ftapp(qapp):
    ft = FTApp.__new__(FTApp)
    QWidget.__init__(ft)

    class _Svc:
        def list_active_allergens(self):
            return []

        def total(self):
            return 5

    ft.service = _Svc()
    ft.ds = None
    ft.cur_index = 0
    ft._load_record = lambda idx: None
    ft._build_ui()
    ft.show()
    ft.activateWindow()
    ft.setFocus()
    qapp.processEvents()
    return ft


# ------- Tests -------


def test_save_and_get_preparacao_html():
    ds = _make_datastore()
    ds.save_preparacao_html("P1", "<p>Olá</p>")
    assert ds.get_preparacao_html("P1") == "<p>Olá</p>"
    ds.close()


def test_sanitize_prep_html_removes_disallowed():
    inst = FTApp.__new__(FTApp)
    dirty = (
        '<p onclick="x"><script>alert(1)</script><b>t</b><i>e</i>'
        '<span style="text-align:center;color:red">x</span></p><div>y</div>'
    )
    clean = FTApp._sanitize_prep_html(inst, dirty)
    low = clean.lower()
    assert "<script" not in low
    assert "onclick" not in low
    assert "<div" not in low
    assert "color" not in low
    assert "<strong>" in low and "<em>" in low


def test_apply_prep_autofit_or_scroll(qapp):
    inst = FTApp.__new__(FTApp)
    inst.edPrep = QTextEdit()
    inst.edPrep.resize(400, 200)

    inst.edPrep.setPlainText("short")
    inst.edPrep.document().setTextWidth(inst.edPrep.viewport().width())
    FTApp._apply_prep_autofit_or_scroll(inst)
    assert inst.edPrep.minimumHeight() == 160
    assert inst.edPrep.verticalScrollBar().maximum() == 0

    inst.edPrep.setPlainText("line\n" * 200)
    inst.edPrep.document().setTextWidth(inst.edPrep.viewport().width())
    FTApp._apply_prep_autofit_or_scroll(inst)
    assert inst.edPrep.minimumHeight() == 520
    assert inst.edPrep.verticalScrollBar().maximum() > 0


def test_save_prep_called_on_ctrl_s_and_navigation(qapp):
    ft = _make_ftapp(qapp)
    calls: list[bool] = []
    ft._save_prep = types.MethodType(lambda self, force: calls.append(force), ft)
    ft._on_prep_changed()
    for sc in ft.findChildren(QShortcut):
        if sc.key().toString().upper() == "CTRL+S":
            sc.activated.emit()
            break
    assert calls == [True]

    calls.clear()
    ft._save_prep = types.MethodType(lambda self, force: calls.append(force), ft)
    ft._prep_dirty = True
    ft._go(1)
    assert calls == [False]

    calls.clear()
    ft._save_prep = types.MethodType(lambda self, force: calls.append(force), ft)
    ft._prep_dirty = True
    ft._goto(2)
    assert calls == [False]
    ft.close()
    ft.deleteLater()
    qapp.processEvents()
