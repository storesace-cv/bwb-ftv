"""Utility helpers for working with project paths."""

from pathlib import Path


def get_project_root() -> Path:
    """Return the root directory of the repository.

    The search walks up the directory tree looking for a ``pyproject.toml``
    or ``.git`` directory.  If none of these markers are found, the function
    falls back to the parent directory of this module.  Should that directory
    be missing, a clear :class:`RuntimeError` is raised.
    """

    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent

    if here.parent.exists():
        # Safe fallback when no project markers are present
        return here.parent

    raise RuntimeError(
        "Could not determine project root: no 'pyproject.toml' or '.git' found"
    )
