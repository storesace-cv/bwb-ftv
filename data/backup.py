from __future__ import annotations

"""Utilities for creating and restoring backups of ``ftv.db``."""

from datetime import datetime
import shutil
from pathlib import Path

from utils.paths import get_project_root


def _db_path() -> Path:
    """Return the absolute path to ``ftv.db``."""

    return get_project_root() / "databases" / "ftv.db"


def create_backup(*, prefix: str | None = None) -> Path:
    """Create a timestamped backup of ``ftv.db``.

    Parameters
    ----------
    prefix
        Optional filename prefix. When provided, backups are stored as
        ``<prefix><timestamp>.db``. Otherwise, the legacy
        ``ftv.<timestamp>.db`` pattern is used.

    Returns
    -------
    Path
        Location of the created backup file.
    """

    db_path = _db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    backups_dir = db_path.parent / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if prefix:
        backup_name = f"{prefix}{timestamp}{db_path.suffix}"
    else:
        backup_name = f"{db_path.stem}.{timestamp}{db_path.suffix}"
    backup_path = backups_dir / backup_name

    shutil.copy2(db_path, backup_path)
    return backup_path


def restore_backup(backup_path: Path | str) -> Path:
    """Restore ``ftv.db`` from ``backup_path``.

    Parameters
    ----------
    backup_path
        Path to the backup file. If relative, it is resolved against
        ``<project_root>/databases/backups``.

    Returns
    -------
    Path
        Location of the restored database file.
    """

    db_path = _db_path()
    backups_dir = db_path.parent / "backups"

    backup_path = Path(backup_path)
    if not backup_path.is_absolute():
        backup_path = backups_dir / backup_path

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, db_path)
    return db_path
