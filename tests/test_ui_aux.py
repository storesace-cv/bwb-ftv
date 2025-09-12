import sqlite3
import types

from ui.ui_editor_fonte import FTApp


class DummySignal:
    def __init__(self):
        self._handlers = []

    def connect(self, handler):
        self._handlers.append(handler)

    def emit(self, *args, **kwargs):
        for h in list(self._handlers):
            h(*args, **kwargs)


class DummyComboBox:
    def __init__(self):
        self._items = []
        self._index = 0
        self._blocked = False
        self.currentIndexChanged = DummySignal()

    def blockSignals(self, flag):
        self._blocked = flag

    def clear(self):
        self._items.clear()

    def addItem(self, text, data):
        self._items.append((text, data))

    def count(self):
        return len(self._items)

    def itemData(self, idx):
        return self._items[idx][1] if idx < len(self._items) else None

    def currentIndex(self):
        return self._index

    def currentData(self):
        return self.itemData(self._index)

    def setCurrentIndex(self, idx):
        self._index = idx
        if not self._blocked:
            self.currentIndexChanged.emit(idx)


class DummyLabel:
    def __init__(self, text=""):
        self._text = text

    def text(self):
        return self._text


def _make_dummy():
    class DummyService:
        def __init__(self):
            self.conn = sqlite3.connect(":memory:")
            self.conn.execute(
                """
                CREATE TABLE produto_auxiliar (
                    produto_codigo TEXT PRIMARY KEY,
                    tipo_artigo_id INTEGER,
                    validade_id INTEGER,
                    temperatura_id INTEGER
                )
                """
            )
            self.conn.commit()

        def codigo_at(self, idx):
            return "P1"

    svc = DummyService()
    dummy = types.SimpleNamespace(
        service=svc,
        cur_index=0,
        _loading=False,
        lbCodigo=DummyLabel("P1"),
        cbTipoArtigo=DummyComboBox(),
        cbValidade=DummyComboBox(),
        cbTemp=DummyComboBox(),
    )
    return dummy, svc


def test_populate_and_autosave():
    dummy, svc = _make_dummy()
    lists = {
        "tipo_artigo": [(1, "Tipo A")],
        "validade": [(1, "1d")],
        "temperatura": [(1, "Frio")],
    }
    cbs = (dummy.cbTipoArtigo, dummy.cbValidade, dummy.cbTemp)
    FTApp._aux_populate_cbs(dummy, lists, cbs)
    assert dummy.cbTipoArtigo.count() == 2
    assert dummy.cbValidade.count() == 2
    assert dummy.cbTemp.count() == 2

    FTApp._aux_wire_autosave(dummy, cbs)
    dummy.cbTipoArtigo.setCurrentIndex(1)

    cur = svc.conn.cursor()
    cur.execute("SELECT tipo_artigo_id FROM produto_auxiliar WHERE produto_codigo='P1'")
    assert cur.fetchone()[0] == 1
