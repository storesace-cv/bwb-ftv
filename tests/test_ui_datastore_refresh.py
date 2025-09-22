from types import SimpleNamespace

import pytest

pytest.importorskip("PyQt5.QtWidgets")

from ui import dialogs
from ui.ui_editor_fonte import FTApp


class DummyService:
    def __init__(self):
        self.ds = SimpleNamespace(name="original")

    def update_from_excel(self):
        self.ds = SimpleNamespace(name="replacement")
        raise RuntimeError("boom")


class DummyMessageBox:
    @staticmethod
    def information(*args, **kwargs):
        return None

    @staticmethod
    def warning(*args, **kwargs):
        return None

    @staticmethod
    def critical(*args, **kwargs):
        return None


@pytest.mark.usefixtures("qapp")
def test_ftapp_refreshes_datastore_after_failed_update(monkeypatch):
    """UI should rebind to the datastore recreated by the service."""

    monkeypatch.setattr(dialogs, "missing_import_files", lambda: [])
    monkeypatch.setattr(dialogs, "QMessageBox", DummyMessageBox)

    def fake_build_ui(self):
        self.prep_previews = []

    def fake_connect_nav(self):
        return None

    def fake_load_record(self, index):
        self.cur_index = index
        self.current_product = SimpleNamespace(code=None)

    monkeypatch.setattr(FTApp, "_build_ui", fake_build_ui)
    monkeypatch.setattr(FTApp, "_connect_nav", fake_connect_nav)
    monkeypatch.setattr(FTApp, "_load_record", fake_load_record)

    service = DummyService()
    app = FTApp(service)

    original_ds = app.ds
    assert original_ds.name == "original"

    app._on_update_data()

    assert service.ds.name == "replacement"
    assert app.ds is service.ds
