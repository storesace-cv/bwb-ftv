import logging
import sqlite3
import types
import pytest

from ftv.utils import autosave


class DummyDS:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")


def test_read_write_attr_errors(caplog):
    ds = DummyDS()
    with caplog.at_level(logging.ERROR):
        assert autosave._read_attrs(ds, "P1") == {
            "tipo_artigo": None,
            "validade": None,
            "temperatura": None,
        }
        autosave._write_attr(ds, "P1", "tipo_artigo", 1)
    assert any(
        "read P1" in r.message or "write tipo_artigo" in r.message
        for r in caplog.records
    )


def test_ensure_schema_raises_on_error():
    class BadConn:
        def cursor(self):
            raise sqlite3.OperationalError("fail")

    ds = types.SimpleNamespace(conn=BadConn())
    with pytest.raises(sqlite3.Error):
        autosave._ensure_produto_attrs_schema(ds)
