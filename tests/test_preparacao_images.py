import os
from pathlib import Path

from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog

import services.products as products
from ui.ui_editor_fonte import PrepImagePreview

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_get_preparacao_image_path(tmp_path, monkeypatch):
    monkeypatch.setattr(products, "get_project_root", lambda: tmp_path)
    path = products.get_preparacao_image_path("ABC", 1)
    assert path == tmp_path / "databases" / "images" / "preparacoes" / "ABC-1.png"


def test_save_preparacao_image_resizes_and_saves_png(tmp_path, monkeypatch):
    monkeypatch.setattr(products, "get_project_root", lambda: tmp_path)
    src = tmp_path / "src.png"
    Image.new("RGB", (1200, 1200), "red").save(src)
    dest = products.save_preparacao_image("P1", 1, src)
    assert dest.exists()
    img = Image.open(dest)
    assert img.size == (600, 600)
    assert img.format == "PNG"


def test_delete_preparacao_image_renames_with_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr(products, "get_project_root", lambda: tmp_path)
    img_dir = tmp_path / "databases" / "images" / "preparacoes"
    img_dir.mkdir(parents=True)
    original = img_dir / "P1-1.png"
    Image.new("RGB", (100, 100), "blue").save(original)
    monkeypatch.setattr(products.time, "time", lambda: 1234567890)
    backup = products.delete_preparacao_image("P1", 1)
    assert backup == img_dir / "P1-1.1234567890.png"
    assert backup.exists()
    assert not original.exists()


def test_prep_image_preview_click_flow(qtbot, tmp_path, monkeypatch):
    class DummyService:
        def __init__(self):
            self.saved: list[tuple[str, int, str]] = []
            self.deleted: list[tuple[str, int]] = []

        def get_preparacao_image_path(self, codigo: str, idx: int) -> Path:
            return tmp_path / f"{codigo}-{idx}.png"

        def save_preparacao_image(self, codigo: str, idx: int, src_path: str) -> None:
            self.saved.append((codigo, idx, src_path))
            Image.new("RGB", (10, 10), "green").save(
                self.get_preparacao_image_path(codigo, idx)
            )

        def delete_preparacao_image(self, codigo: str, idx: int) -> None:
            self.deleted.append((codigo, idx))
            path = self.get_preparacao_image_path(codigo, idx)
            if path.exists():
                path.unlink()

    svc = DummyService()
    preview = PrepImagePreview(1, svc)
    preview.load_image("P1")
    qtbot.addWidget(preview)

    src = tmp_path / "src.png"
    Image.new("RGB", (10, 10), "yellow").save(src)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *a, **k: (str(src), ""),
    )

    qtbot.mouseClick(preview, Qt.LeftButton)
    assert svc.saved == [("P1", 1, str(src))]

    class DummyMsg:
        AcceptRole = 0
        RejectRole = 1
        DestructiveRole = 2

        def __init__(self, parent):
            self.btn_sub = object()
            self.btn_del = object()

        def setWindowTitle(self, *a):
            pass

        def setText(self, *a):
            pass

        def addButton(self, text, role):
            if role == self.AcceptRole:
                return self.btn_sub
            if role == self.DestructiveRole:
                return self.btn_del
            return object()

        def exec_(self):
            pass

        def clickedButton(self):
            return self.btn_del

    monkeypatch.setattr("ui.ui_editor_fonte.QMessageBox", DummyMsg)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))

    qtbot.mouseClick(preview, Qt.LeftButton)
    assert svc.deleted == [("P1", 1)]
