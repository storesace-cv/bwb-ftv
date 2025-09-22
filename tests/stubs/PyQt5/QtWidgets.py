"""Stub implementations of QtWidgets classes for tests."""

from __future__ import annotations

from typing import Any, Sequence

__STUB__ = True


class QApplication:
    """Minimal QApplication stub to satisfy tests."""

    _instance: "QApplication | None" = None

    def __init__(self, args: Sequence[Any] | None = None) -> None:
        # Store provided args to mimic API compatibility
        self.args = list(args) if args is not None else []
        QApplication._instance = self

    @classmethod
    def instance(cls) -> "QApplication | None":
        return cls._instance


__all__ = ["QApplication"]
