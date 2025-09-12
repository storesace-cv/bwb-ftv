import sqlite3
import sys
import types


qt_module = types.ModuleType("PyQt5")
qt_core = types.ModuleType("PyQt5.QtCore")
qt_core.Qt = object()
qt_core.QSize = object
qt_core.QObject = object
qt_gui = types.ModuleType("PyQt5.QtGui")
qt_gui.QFont = object
qt_gui.QKeySequence = object
qt_widgets = types.ModuleType("PyQt5.QtWidgets")
for name in [
    "QApplication",
    "QWidget",
    "QVBoxLayout",
    "QHBoxLayout",
    "QGridLayout",
    "QGroupBox",
    "QLabel",
    "QLineEdit",
    "QComboBox",
    "QPushButton",
    "QSizePolicy",
    "QTableWidget",
    "QTableWidgetItem",
    "QMessageBox",
    "QScrollArea",
    "QShortcut",
    "QTextEdit",
    "QCheckBox",
]:
    setattr(qt_widgets, name, type(name, (), {}))
qt_module.QtCore = qt_core
qt_module.QtGui = qt_gui
qt_module.QtWidgets = qt_widgets
sys.modules.setdefault("PyQt5", qt_module)
sys.modules.setdefault("PyQt5.QtCore", qt_core)
sys.modules.setdefault("PyQt5.QtGui", qt_gui)
sys.modules.setdefault("PyQt5.QtWidgets", qt_widgets)

from ui.ui_editor_fonte import FTApp


def _make_app(conn):
    app = FTApp.__new__(FTApp)
    app.service = types.SimpleNamespace(conn=conn)
    return app


def test_aux_fetch_lists_returns_expected():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE tipos_artigos(id INTEGER, descricao TEXT, ativo INT)")
    cur.execute("INSERT INTO tipos_artigos VALUES (1, 'TipoA', 1), (2, 'TipoB', 0)")
    cur.execute("CREATE TABLE validades(cod INTEGER PRIMARY KEY, nome TEXT, ativo INT)")
    cur.executemany(
        "INSERT INTO validades(cod, nome, ativo) VALUES (?, ?, 1)",
        [(1, "Val1"), (2, "Val2")],
    )
    cur.execute("CREATE TABLE temperaturas(codigo INTEGER, designacao TEXT, ativo INT)")
    cur.executemany(
        "INSERT INTO temperaturas VALUES (?, ?, 1)",
        [(1, "Temp1"), (2, "Temp2")],
    )
    conn.commit()

    app = _make_app(conn)
    lists = app._aux_fetch_lists()
    assert lists == {
        "tipo_artigo": [(1, "TipoA")],
        "validade": [(1, "Val1"), (2, "Val2")],
        "temperatura": [(1, "Temp1"), (2, "Temp2")],
    }


def test_aux_fetch_lists_no_conn():
    app = _make_app(None)
    assert app._aux_fetch_lists() == {
        "tipo_artigo": [],
        "validade": [],
        "temperatura": [],
    }
