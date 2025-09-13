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


def restore_backup(
    backup_path: Path | str,
    db_path: Path | str | None = None,
) -> Path:
    """Restore a database from a backup file.

    Parameters
    ----------
    backup_path:
        Path to the backup file. If relative, it is assumed to live under
        ``<project_root>/databases/backups``.
    db_path:
        Destination database file to overwrite. If ``None`` or a relative
        path is supplied, ``<project_root>/databases/ftv.db`` is used.

    Returns
    -------
    Path
        Location of the restored database file.
    """

    project_root = get_project_root()
    databases_dir = project_root / "databases"
    backups_dir = databases_dir / "backups"

    db_path = Path(db_path) if db_path is not None else databases_dir / "ftv.db"
    if not db_path.is_absolute():
        db_path = databases_dir / db_path

    backup_path = Path(backup_path)
    if not backup_path.is_absolute():
        backup_path = backups_dir / backup_path

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, db_path)
    return db_path
