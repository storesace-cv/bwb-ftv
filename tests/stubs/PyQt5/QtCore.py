"""QtCore stub definitions for PyQt5-dependent tests."""

from __future__ import annotations

from enum import IntEnum
from typing import Callable

__STUB__ = True


class QtMsgType(IntEnum):
    """Subset of Qt message severities used by the application."""

    QtDebugMsg = 0
    QtWarningMsg = 1
    QtCriticalMsg = 2
    QtFatalMsg = 3
    QtInfoMsg = 4


_MessageHandler = Callable[[QtMsgType, object | None, str], None]


def qInstallMessageHandler(handler: _MessageHandler) -> _MessageHandler:
    """Return the provided handler without installing global hooks."""

    return handler


__all__ = ["QtMsgType", "qInstallMessageHandler"]
