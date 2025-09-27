import os
from pathlib import Path

import pytest

from reporting.template_updater import apply_template_updaters


@pytest.fixture
def make_file(tmp_path):
    def _make_file(name: str, content: str, mtime: float) -> Path:
        path = tmp_path / name
        path.write_text(content)
        os.utime(path, (mtime, mtime))
        return path

    return _make_file


def test_apply_template_updaters_copies_only_newer(make_file, tmp_path):
    older_base = make_file("alpha_base.json", "alpha-base", 1)
    make_file("alpha_base_updater.json", "alpha-update", 10)

    newer_base = make_file("beta_base.json", "beta-base", 20)
    make_file("beta_base_updater.json", "beta-update", 5)

    summary = apply_template_updaters(tmp_path)

    assert (tmp_path / "alpha_base.json").read_text() == "alpha-update"
    assert (tmp_path / "beta_base.json").read_text() == "beta-base"

    assert older_base in summary.updated
    assert newer_base in summary.skipped
    assert not summary.errors


def test_apply_template_updaters_handles_missing_updater(make_file, tmp_path, caplog):
    caplog.set_level("INFO")
    missing_target = make_file("gamma_base.json", "gamma-base", 3)

    summary = apply_template_updaters(tmp_path)

    assert missing_target in summary.missing_updater
    assert "Nenhum updater encontrado" in caplog.text
    assert not summary.updated
    assert not summary.errors
