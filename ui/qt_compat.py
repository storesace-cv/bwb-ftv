"""Qt compatibility helpers for :func:`exec` vs. legacy :func:`exec_`."""

from __future__ import annotations

from typing import Any, Callable


def _resolve_exec(obj: Any) -> Callable[[], Any]:
    method = getattr(obj, "exec", None)
    if method is None:
        method = getattr(obj, "exec_", None)
    if method is None:
        raise AttributeError(
            f"{type(obj).__name__} does not expose an exec()/exec_() method"
        )
    return method


def exec_modal(widget: Any) -> Any:
    """Execute a dialog/widget using ``exec``/``exec_`` transparently."""

    return _resolve_exec(widget)()


def exec_app(app: Any) -> Any:
    """Execute a Qt application using ``exec``/``exec_`` transparently."""

    return _resolve_exec(app)()
