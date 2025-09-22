import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

try:
    from PyQt5.QtWidgets import QApplication  # noqa: E402
except ImportError:
    QApplication = None  # type: ignore[assignment]

PYQT5_STUB_ACTIVE = QApplication is None


@pytest.fixture(scope="session")
def qapp():
    if PYQT5_STUB_ACTIVE:
        pytest.skip("PyQt5 QtWidgets is unavailable", allow_module_level=True)
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
