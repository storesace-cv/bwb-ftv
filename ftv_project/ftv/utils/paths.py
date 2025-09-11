from pathlib import Path


def get_project_root() -> Path:
    """Return the root directory of the project.

    Calculated relative to this file's location. Falls back to the current
    working directory if resolution fails.
    """
    try:
        return Path(__file__).resolve().parents[3]
    except Exception:
        return Path(".").resolve()
