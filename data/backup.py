from __future__ import annotations

"""Utilities for creating database backups."""

from datetime import datetime
import shutil
from pathlib import Path

from utils.paths import get_project_root


def create_backup(db_path: Path | str | None = None) -> Path:
    """Create a timestamped backup of the given database file.

    Parameters
    ----------
    db_path:
        Path or filename of the database to back up. If ``None`` or a relative
        path is supplied, it is assumed to live under ``<project_root>/databases``.

    Returns
    -------
    Path
        Location of the created backup file.
    """

    project_root = get_project_root()
    databases_dir = project_root / "databases"

    db_path = Path(db_path) if db_path is not None else databases_dir / "ftv.db"
    if not db_path.is_absolute():
        db_path = databases_dir / db_path

    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    backups_dir = databases_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{db_path.stem}.{timestamp}{db_path.suffix}"
    backup_path = backups_dir / backup_name

    shutil.copy2(db_path, backup_path)
    return backup_path
