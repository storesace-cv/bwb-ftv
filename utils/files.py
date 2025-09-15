"""File-related helpers for archiving and backups."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def archive_with_timestamp(
    source: Path,
    destination_dir: Path,
    *,
    prefix: str | None = None,
    suffix: str | None = None,
    timestamp: datetime | None = None,
) -> Path:
    """Move ``source`` into ``destination_dir`` with a timestamped name.

    The resulting filename follows the ``<prefix>.<YYYYMMDDHHMMSS><suffix>``
    pattern, matching the convention used by the Excel import history.

    Parameters
    ----------
    source:
        File to be moved.
    destination_dir:
        Directory where the archived copy will be stored. It will be created if
        it does not yet exist.
    prefix:
        Optional custom prefix for the archived filename. Defaults to the stem
        of ``source`` when not provided.
    suffix:
        Optional file extension (with or without leading dot). Defaults to the
        original suffix of ``source``.
    timestamp:
        Optional :class:`~datetime.datetime` instance used to generate the
        timestamp portion of the archived filename. When omitted the current
        time is used.

    Returns
    -------
    Path
        Location of the archived file.
    """

    src_path = Path(source)
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")

    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    name_prefix = prefix if prefix is not None else src_path.stem
    if suffix is None:
        name_suffix = src_path.suffix
    else:
        name_suffix = suffix if suffix.startswith(".") else f".{suffix}"

    ts = timestamp or datetime.now()
    ts_str = ts.strftime("%Y%m%d%H%M%S")

    destination = dest_dir / f"{name_prefix}.{ts_str}{name_suffix}"
    return src_path.rename(destination)


__all__ = ["archive_with_timestamp"]

