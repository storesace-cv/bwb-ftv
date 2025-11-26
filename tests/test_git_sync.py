from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from utils.git_sync import FastForwardError, GitRepository


def _run_git(args: list[str], *, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _configure_user(repo: Path) -> None:
    _run_git(["config", "user.name", "Test User"], cwd=repo)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo)


def _prepare_repository(tmp_path: Path) -> tuple[Path, Path, Path]:
    remote = tmp_path / "remote.git"
    _run_git(["init", "--bare", remote.as_posix()], cwd=tmp_path)

    local = tmp_path / "local"
    local.mkdir()
    _run_git(["init", "-b", "main"], cwd=local)
    _configure_user(local)

    (local / "data.txt").write_text("base\n", encoding="utf-8")
    _run_git(["add", "data.txt"], cwd=local)
    _run_git(["commit", "-m", "base"], cwd=local)
    _run_git(["remote", "add", "origin", remote.as_posix()], cwd=local)
    _run_git(["push", "-u", "origin", "main"], cwd=local)

    clone = tmp_path / "clone"
    _run_git(["clone", "--branch", "main", remote.as_posix(), clone.as_posix()], cwd=tmp_path)
    _configure_user(clone)
    (clone / "data.txt").write_text("base\nremote\n", encoding="utf-8")
    _run_git(["add", "data.txt"], cwd=clone)
    _run_git(["commit", "-am", "remote change"], cwd=clone)
    _run_git(["push", "origin", "main"], cwd=clone)

    (local / "local.txt").write_text("local\n", encoding="utf-8")
    _run_git(["add", "local.txt"], cwd=local)
    _run_git(["commit", "-m", "local change"], cwd=local)

    return local, remote, clone


def test_pull_detects_fast_forward_error(tmp_path: Path) -> None:
    repo_path, _, _ = _prepare_repository(tmp_path)
    repo = GitRepository(repo_path)

    with pytest.raises(FastForwardError):
        repo.pull_ff_only()


def test_merge_no_ff_resolves_conflict(tmp_path: Path) -> None:
    repo_path, _, _ = _prepare_repository(tmp_path)
    repo = GitRepository(repo_path)

    with pytest.raises(FastForwardError):
        repo.pull_ff_only()

    backup_dir = repo.create_backup_snapshot()
    merge_output = repo.merge_no_ff()

    assert "Merge" in merge_output
    assert backup_dir is None or backup_dir.exists()

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert status.stdout.strip() == ""


def test_rebase_resolves_conflict(tmp_path: Path) -> None:
    repo_path, _, _ = _prepare_repository(tmp_path)
    repo = GitRepository(repo_path)

    with pytest.raises(FastForwardError):
        repo.pull_ff_only()

    repo.create_backup_snapshot()
    repo.rebase()

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert status.stdout.strip() == ""
