import os
from pathlib import Path

from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileDialog

import services.products as products
from ui.ui_editor_fonte import ImagePreview

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_get_image_path(tmp_path, monkeypatch):
    monkeypatch.setattr(products, "get_project_root", lambda: tmp_path)
    path = products.get_image_path("ABC")
    assert path == tmp_path / "databases" / "images" / "ABC.png"


def test_save_product_image_resizes_and_saves_png(tmp_path, monkeypatch):
    monkeypatch.setattr(products, "get_project_root", lambda: tmp_path)
    src = tmp_path / "src.png"
    Image.new("RGB", (1200, 1200), "red").save(src)
    dest = products.save_product_image("P1", src)
    assert dest.exists()
    img = Image.open(dest)
    assert img.size == (600, 600)
    assert img.format == "PNG"


def test_delete_product_image_renames_with_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr(products, "get_project_root", lambda: tmp_path)
    img_dir = tmp_path / "databases" / "images"
    img_dir.mkdir(parents=True)
    original = img_dir / "P1.png"
    Image.new("RGB", (100, 100), "blue").save(original)
    monkeypatch.setattr(products.time, "time", lambda: 1234567890)
    backup = products.delete_product_image("P1")
    assert backup == img_dir / "P1.1234567890.png"
    assert backup.exists()
    assert not original.exists()


def test_save_product_image_missing_file(tmp_path, monkeypatch, caplog):
    """Missing source image should be logged and return None."""

    monkeypatch.setattr(products, "get_project_root", lambda: tmp_path)
    missing = tmp_path / "missing.png"
    with caplog.at_level("ERROR"):
        dest = products.save_product_image("P1", missing)
    assert dest is None
    assert "missing.png" in caplog.text


def test_save_product_image_invalid_file(tmp_path, monkeypatch, caplog):
    """Invalid image data should be logged and return None."""

    monkeypatch.setattr(products, "get_project_root", lambda: tmp_path)
    src = tmp_path / "src.png"
    src.write_text("not an image")
    with caplog.at_level("ERROR"):
        dest = products.save_product_image("P1", src)
    assert dest is None
    assert "src.png" in caplog.text
    assert not products.get_image_path("P1").exists()


def test_image_preview_click_flow(qtbot, tmp_path, monkeypatch):
    class DummyService:
        def __init__(self):
            self.saved: list[tuple[str, str]] = []
            self.deleted: list[str] = []

        def get_image_path(self, codigo: str) -> Path:
            return tmp_path / f"{codigo}.png"

        def save_product_image(self, codigo: str, src_path: str) -> None:
            self.saved.append((codigo, src_path))
            Image.new("RGB", (10, 10), "green").save(self.get_image_path(codigo))

        def delete_product_image(self, codigo: str) -> None:
            self.deleted.append(codigo)
            path = self.get_image_path(codigo)
            if path.exists():
                path.unlink()

    svc = DummyService()
    preview = ImagePreview("P1", svc)
    qtbot.addWidget(preview)

    src = tmp_path / "src.png"
    Image.new("RGB", (10, 10), "yellow").save(src)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *a, **k: (str(src), ""),
    )

    qtbot.mouseClick(preview, Qt.LeftButton)
    assert svc.saved == [("P1", str(src))]

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

        def clickedButton(self):
            return self.btn_del

    monkeypatch.setattr("ui.ui_editor_fonte.QMessageBox", DummyMsg)
    monkeypatch.setattr("ui.ui_editor_fonte.exec_modal", lambda dlg: 0)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))

    qtbot.mouseClick(preview, Qt.LeftButton)
    assert svc.deleted == ["P1"]


def test_image_preview_uses_placeholder_when_missing(qtbot, tmp_path):
    class DummyService:
        def get_image_path(self, codigo: str) -> Path:
            return tmp_path / f"{codigo}.png"

    svc = DummyService()
    preview = ImagePreview("P1", svc)
    qtbot.addWidget(preview)
    preview.show()
    qtbot.wait(50)
    preview.resize(300, 300)
    qtbot.wait(50)

    import ui.ui_editor_fonte as editor

    placeholder_path = Path(editor.__file__).with_name("no-image-thumb.png")
    expected = QPixmap(str(placeholder_path))
    expected = expected.scaled(
        preview.size(),
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )

    pixmap = preview.pixmap()
    assert pixmap is not None
    assert not pixmap.isNull()
    assert pixmap.width() <= preview.width()
    assert pixmap.height() <= preview.height()
    assert pixmap.toImage() == expected.toImage()
