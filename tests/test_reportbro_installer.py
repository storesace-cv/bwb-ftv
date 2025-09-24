from __future__ import annotations

from importlib import metadata

import pytest

from utils import reportbro_installer


def test_load_reportbro_requirement_parses_version(tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("# demo\nreportbro-lib==1.2.3\n", encoding="utf-8")

    requirement = reportbro_installer.load_reportbro_requirement(requirements)

    assert requirement.requirement == "reportbro-lib==1.2.3"
    assert requirement.package == "reportbro-lib"
    assert requirement.version == "1.2.3"


def test_load_reportbro_requirement_missing(tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("pyqt5==5.15.10\n", encoding="utf-8")

    with pytest.raises(reportbro_installer.InstallationError):
        reportbro_installer.load_reportbro_requirement(requirements)


def test_is_requirement_satisfied_returns_true(monkeypatch):
    requirement = reportbro_installer.ReportBroRequirement(
        "reportbro-lib==1.2.3",
        package="reportbro-lib",
        version="1.2.3",
    )

    monkeypatch.setattr(
        reportbro_installer.metadata,
        "version",
        lambda package: "1.2.3",
    )

    assert reportbro_installer.is_requirement_satisfied(requirement) is True


def test_is_requirement_satisfied_returns_false(monkeypatch):
    requirement = reportbro_installer.ReportBroRequirement(
        "reportbro-lib==1.2.3",
        package="reportbro-lib",
        version="1.2.3",
    )

    def raise_not_found(_: str) -> str:
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(reportbro_installer.metadata, "version", raise_not_found)

    assert reportbro_installer.is_requirement_satisfied(requirement) is False


def test_ensure_reportbro_installed_invokes_pip_when_missing(monkeypatch, tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("reportbro-lib==9.9.9\n", encoding="utf-8")

    def raise_not_found(_: str) -> str:
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(reportbro_installer.metadata, "version", raise_not_found)

    captured: dict[str, list[str]] = {}

    def fake_run(command):
        captured["command"] = command

    monkeypatch.setattr(reportbro_installer, "_run_command", fake_run)

    installed = reportbro_installer.ensure_reportbro_installed(
        requirements_path=requirements,
        pip_args=("--user",),
    )

    assert installed is True
    assert captured["command"][-1] == "reportbro-lib==9.9.9"


def test_ensure_reportbro_installed_skips_when_present(monkeypatch, tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("reportbro-lib==3.3.3\n", encoding="utf-8")

    monkeypatch.setattr(
        reportbro_installer.metadata,
        "version",
        lambda package: "3.3.3",
    )

    called = False

    def fail_run(command):
        nonlocal called
        called = True

    monkeypatch.setattr(reportbro_installer, "_run_command", fail_run)

    installed = reportbro_installer.ensure_reportbro_installed(
        requirements_path=requirements,
        pip_args=("--user",),
    )

    assert installed is False
    assert called is False
