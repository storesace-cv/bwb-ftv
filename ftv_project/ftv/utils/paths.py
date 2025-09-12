"""Utility helpers for working with project paths."""
from pathlib import Path


def get_project_root() -> Path:
    """Return the root directory of the repository."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return here.parents[2]  # fallback
