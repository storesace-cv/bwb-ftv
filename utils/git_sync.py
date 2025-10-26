"""Utilities for synchronising local Git repositories from the application."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence


LOGGER = logging.getLogger(__name__)


class GitSyncError(RuntimeError):
    """Raised when a Git command cannot be executed successfully."""

    def __init__(self, command: Sequence[str], returncode: int, stdout: str, stderr: str) -> None:
        super().__init__(
            "Comando git falhou: "
            f"{' '.join(command)} (código {returncode}).\nstdout: {stdout}\nstderr: {stderr}"
        )
        self.command = tuple(command)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FastForwardError(GitSyncError):
    """Raised when Git refuses to fast-forward a pull operation."""


@dataclass(frozen=True)
class GitChangeEntry:
    """Representation of a line from ``git status --porcelain``."""

    status: str
    path: str
    original_path: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "status": self.status,
            "path": self.path,
            "original_path": self.original_path,
        }


class GitRepository:
    """Run Git commands inside a repository path."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------
    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        command = ("git", *args)
        try:
            result = subprocess.run(
                command,
                cwd=self.path,
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:  # pragma: no cover - git executable missing
            raise GitSyncError(command, 1, "", str(exc)) from exc

        if check and result.returncode != 0:
            if "Not possible to fast-forward" in (result.stdout + result.stderr):
                raise FastForwardError(command, result.returncode, result.stdout, result.stderr)
            raise GitSyncError(command, result.returncode, result.stdout, result.stderr)
        return result

    # ------------------------------------------------------------------
    # Repository inspection
    # ------------------------------------------------------------------
    def is_repository(self) -> bool:
        return (self.path / ".git").exists()

    def current_branch(self) -> str:
        result = self._run("rev-parse", "--abbrev-ref", "HEAD")
        branch = result.stdout.strip()
        if not branch:
            raise GitSyncError(("git", "rev-parse", "--abbrev-ref", "HEAD"), 0, result.stdout, result.stderr)
        return branch

    def list_changes(self) -> list[GitChangeEntry]:
        result = self._run("status", "--porcelain", "--untracked-files")
        entries: list[GitChangeEntry] = []
        for line in result.stdout.splitlines():
            if not line:
                continue
            status = line[:2]
            path_part = line[3:]
            original_path: str | None = None
            if " -> " in path_part:
                original_path, path_part = path_part.split(" -> ", 1)
            entries.append(GitChangeEntry(status=status.strip(), path=path_part.strip(), original_path=original_path))
        return entries

    # ------------------------------------------------------------------
    # Backup helpers
    # ------------------------------------------------------------------
    def create_backup_snapshot(self) -> Path | None:
        changes = self.list_changes()
        if not changes:
            LOGGER.info("[GitSync] Nenhuma alteração local encontrada em %s", self.path)
            return None

        backup_root = self.path / "backups" / "git"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = backup_root / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "created_at": datetime.utcnow().isoformat() + "Z",
            "repository": str(self.path.resolve()),
            "entries": [entry.to_dict() for entry in changes],
        }

        for entry in changes:
            src = self.path / entry.path
            if src.exists():
                dest = backup_dir / entry.path
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(src, dest)
                except OSError as exc:  # pragma: no cover - filesystem error
                    LOGGER.warning(
                        "[GitSync] Falha ao copiar %s para %s: %s", src, dest, exc
                    )
            else:
                LOGGER.debug("[GitSync] Entrada %s não existe no disco; apenas registada.", entry.path)

        (backup_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        LOGGER.info("[GitSync] Backup de alterações locais criado em %s", backup_dir)
        return backup_dir

    # ------------------------------------------------------------------
    # Synchronisation helpers
    # ------------------------------------------------------------------
    def fetch(self, remote: str = "origin") -> None:
        self._run("fetch", remote)

    def pull_ff_only(self) -> str:
        result = self._run("pull", "--ff-only", check=False)
        if result.returncode != 0:
            if "Not possible to fast-forward" in (result.stdout + result.stderr):
                raise FastForwardError(("git", "pull", "--ff-only"), result.returncode, result.stdout, result.stderr)
            raise GitSyncError(("git", "pull", "--ff-only"), result.returncode, result.stdout, result.stderr)
        return result.stdout

    def merge_no_ff(self, *, remote: str = "origin", branch: str | None = None) -> str:
        branch = branch or self.current_branch()
        self.fetch(remote)
        result = self._run("merge", "--no-ff", f"{remote}/{branch}")
        return result.stdout

    def rebase(self, *, remote: str = "origin", branch: str | None = None) -> str:
        branch = branch or self.current_branch()
        self.fetch(remote)
        result = self._run("rebase", f"{remote}/{branch}")
        return result.stdout


__all__ = [
    "FastForwardError",
    "GitChangeEntry",
    "GitRepository",
    "GitSyncError",
]

