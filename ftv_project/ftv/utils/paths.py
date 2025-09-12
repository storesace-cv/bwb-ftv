"""Utility helpers for working with project paths."""
from pathlib import Path


def get_project_root() -> Path:
    """Return the root directory of the repository."""
    return Path(__file__).resolve().parents[2]
