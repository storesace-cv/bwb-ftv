import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

# Guard import to avoid crashes when libGL.so.1 is missing.
try:  # noqa: E402
    from PyQt5.QtWidgets import QApplication
except ImportError:  # noqa: E402
    pytest.skip("PyQt5 QtWidgets is unavailable", allow_module_level=True)


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
