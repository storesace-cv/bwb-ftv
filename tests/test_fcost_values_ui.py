# flake8: noqa
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import ui.dialogs as dialogs
from data.datastore import DataStore
from PyQt5.QtWidgets import QTableWidget, QPushButton
from PyQt5.QtCore import Qt


# helper to open dialog non-blocking and return widgets

def _open_dialog(qtbot, repo, monkeypatch):
    captured = {}

    def fake_exec_modal(dialog):
        captured["dlg"] = dialog
        dialog.show()
        return 0

    monkeypatch.setattr(dialogs, "exec_modal", fake_exec_modal)
    dialogs.edit_fcost_values(None, repo)
    dlg = captured["dlg"]
    qtbot.addWidget(dlg)
    tbl = dlg.findChild(QTableWidget)
    save_btn = None
    for btn in dlg.findChildren(QPushButton):
        if btn.text() == "Gravar":
            save_btn = btn
            break
    assert save_btn is not None
    return dlg, tbl, save_btn


def test_tooltip_duration_is_indefinite(qtbot, monkeypatch):
    with DataStore(db_path=":memory:") as ds:
        dlg, tbl, _ = _open_dialog(qtbot, ds.fcost, monkeypatch)
        try:
            assert tbl.toolTipDuration() == 0
            viewport = tbl.viewport()
            assert viewport is not None
            assert viewport.toolTipDuration() == 0
        finally:
            dlg.close()
            dlg.deleteLater()


def test_tooltips_display_repository_comments(qtbot, monkeypatch):
    with DataStore(db_path=":memory:") as ds:
        dlg, tbl, _ = _open_dialog(qtbot, ds.fcost, monkeypatch)
        levels = ds.fcost.list_levels()
        for row, level in enumerate(levels):
            comment = level["Comentario"]
            for col in range(tbl.columnCount()):
                assert tbl.item(row, col).toolTip() == comment
        dlg.close()
        dlg.deleteLater()


def test_valid_edit_updates_repository(qtbot, monkeypatch):
    with DataStore(db_path=":memory:") as ds:
        dlg, tbl, save_btn = _open_dialog(qtbot, ds.fcost, monkeypatch)
        messages = {}

        def fake_info(parent, title, text):
            messages["info"] = (title, text)

        monkeypatch.setattr(dialogs.QMessageBox, "information", fake_info)
        monkeypatch.setattr(dialogs.QMessageBox, "warning", lambda *a, **k: None)

        tbl.item(1, 2).setText("31")
        tbl.item(1, 3).setText("33")

        qtbot.mouseClick(save_btn, Qt.LeftButton)

        assert messages.get("info") == ("Valores FCOST", "Valores atualizados.")
        level2 = ds.fcost.list_levels()[1]
        assert level2["ValorMin"] == 31.0
        assert level2["ValorMax"] == 33.0
        dlg.close()
        dlg.deleteLater()


def test_invalid_edit_shows_warning_and_keeps_values(qtbot, monkeypatch):
    with DataStore(db_path=":memory:") as ds:
        dlg, tbl, save_btn = _open_dialog(qtbot, ds.fcost, monkeypatch)
        messages = {}

        def fake_warn(parent, title, text):
            messages["warn"] = (title, text)

        monkeypatch.setattr(dialogs.QMessageBox, "warning", fake_warn)
        monkeypatch.setattr(dialogs.QMessageBox, "information", lambda *a, **k: None)

        before = ds.fcost.list_levels()[1]

        tbl.item(1, 2).setText("29")
        tbl.item(1, 3).setText("31")

        qtbot.mouseClick(save_btn, Qt.LeftButton)

        assert messages.get("warn") == (
            "Valores FCOST",
            "Intervalo inválido detectado.",
        )
        after = ds.fcost.list_levels()[1]
        assert (after["ValorMin"], after["ValorMax"]) == (
            before["ValorMin"],
            before["ValorMax"],
        )
        dlg.close()
        dlg.deleteLater()
