"""Bootstrap helpers to install the ReportBro dependency on client machines."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Sequence

REPORTBRO_PACKAGE = "reportbro-lib"
DEFAULT_REQUIREMENTS_PATH = Path(__file__).resolve().parent.parent / "requirements.txt"


class InstallationError(RuntimeError):
    """Raised when the ReportBro installation process cannot be completed."""


@dataclass(frozen=True)
class ReportBroRequirement:
    """Representation of the ReportBro requirement specification."""

    requirement: str
    package: str
    version: str | None


def _normalise_line(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return ""
    if stripped.startswith("-"):
        return ""
    if "#" in stripped:
        stripped = stripped.split("#", 1)[0].strip()
    return stripped


def _parse_requirement(line: str) -> ReportBroRequirement:
    spec = line
    marker_split = spec.split(";", 1)
    package_part = marker_split[0].strip()
    version = None
    if "==" in package_part:
        package, version = package_part.split("==", 1)
    else:
        package = package_part
    package = package.strip()
    version = version.strip() if version is not None else None
    return ReportBroRequirement(spec, package, version)


def load_reportbro_requirement(requirements_path: Path | None = None) -> ReportBroRequirement:
    """Extract the ReportBro requirement definition from ``requirements.txt``."""

    path = requirements_path or DEFAULT_REQUIREMENTS_PATH
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:  # pragma: no cover - defensive logging
        raise InstallationError(f"Não foi possível ler {path}: {exc}") from exc

    for line in lines:
        candidate = _normalise_line(line)
        if not candidate:
            continue
        if candidate.lower().startswith(REPORTBRO_PACKAGE):
            return _parse_requirement(candidate)

    raise InstallationError(
        f"A dependência {REPORTBRO_PACKAGE} não foi encontrada em {path}."
    )


REPORTBRO_REQUIREMENT = load_reportbro_requirement()


def is_requirement_satisfied(requirement: ReportBroRequirement) -> bool:
    try:
        installed_version = metadata.version(requirement.package)
    except metadata.PackageNotFoundError:
        pass
    else:
        if requirement.version is None:
            return True
        return installed_version == requirement.version

    discovered = _discover_user_site_version(requirement.package)
    if discovered is None:
        return False

    installed_version, paths = discovered
    if requirement.version is not None and installed_version != requirement.version:
        return False

    _ensure_paths_on_sys_path(paths)
    return True


def build_pip_install_command(
    requirement: ReportBroRequirement,
    pip_args: Sequence[str] | None = None,
) -> list[str]:
    args = [sys.executable, "-m", "pip", "install"]
    if pip_args:
        args.extend(pip_args)
    args.append(requirement.requirement)
    return args


def running_inside_virtualenv() -> bool:
    """Return ``True`` when the interpreter is executing inside a virtualenv."""

    real_prefix = getattr(sys, "real_prefix", None)
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    if real_prefix is not None and real_prefix != sys.prefix:
        return True
    return sys.prefix != base_prefix


def _collect_user_site_paths() -> tuple[str, ...]:
    """Return the configured user site-packages directories if available."""

    try:
        import site  # noqa: PLC0415 - imported lazily to avoid startup cost
    except ImportError:  # pragma: no cover - site module always available normally
        return ()

    if not getattr(site, "ENABLE_USER_SITE", False):
        return ()

    try:
        user_site = site.getusersitepackages()
    except AttributeError:  # pragma: no cover - defensive guard for exotic interpreters
        return ()

    if isinstance(user_site, str):
        user_site_paths = (user_site,)
    else:
        user_site_paths = tuple(user_site)

    return tuple(
        os.path.abspath(path)
        for path in user_site_paths
        if path
    )


def _ensure_paths_on_sys_path(paths: Sequence[str]) -> None:
    """Append the provided directories to ``sys.path`` when missing."""

    normalized_sys_paths = {
        os.path.abspath(path)
        for path in sys.path
        if path
    }

    for path in paths:
        normalized_path = os.path.abspath(path)
        if normalized_path in normalized_sys_paths:
            continue
        sys.path.append(normalized_path)
        normalized_sys_paths.add(normalized_path)


def is_user_site_enabled() -> bool:
    """Return ``True`` when the user site-packages directory is active."""

    normalized_user_paths = set(_collect_user_site_paths())
    if not normalized_user_paths:
        return False

    normalized_sys_paths = {
        os.path.abspath(path)
        for path in sys.path
        if path
    }

    return bool(normalized_user_paths & normalized_sys_paths)


def _discover_user_site_version(package: str) -> tuple[str, tuple[str, ...]] | None:
    """Return the installed version from the user site when present."""

    user_site_paths = _collect_user_site_paths()
    existing_paths = tuple(path for path in user_site_paths if os.path.isdir(path))
    if not existing_paths:
        return None

    normalized_target = package.replace("_", "-").lower()

    try:
        distributions = metadata.distributions(path=existing_paths)
    except TypeError:  # pragma: no cover - compatibility with older Python versions
        return None

    for dist in distributions:
        metadata_obj = getattr(dist, "metadata", None)
        if metadata_obj is None:
            continue
        if hasattr(metadata_obj, "get"):
            dist_name = metadata_obj.get("Name") or metadata_obj.get("name")
        else:  # pragma: no cover - defensive fallback for unexpected metadata types
            dist_name = None

        if not dist_name:
            continue

        normalized_name = dist_name.replace("_", "-").lower()
        if normalized_name != normalized_target:
            continue

        return dist.version, existing_paths

    return None


def default_pip_args() -> tuple[str, ...]:
    """Return the default pip arguments for local installations."""

    return ()


def _run_command(command: Sequence[str]) -> None:
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - pip failures
        raise InstallationError(
            f"A execução do pip falhou com o código {exc.returncode}."
        ) from exc


def ensure_reportbro_installed(
    *,
    requirements_path: Path | None = None,
    pip_args: Sequence[str] | None = None,
    force: bool = False,
) -> bool:
    """Ensure that the ReportBro dependency is installed.

    Returns ``True`` when an installation or upgrade was triggered, ``False``
    when the dependency was already satisfied.
    """

    requirement = (
        load_reportbro_requirement(requirements_path)
        if requirements_path is not None
        else REPORTBRO_REQUIREMENT
    )

    if not force and is_requirement_satisfied(requirement):
        return False

    if pip_args is None:
        pip_args_tuple: tuple[str, ...] = default_pip_args()
        allow_user_fallback = True
    else:
        pip_args_tuple = tuple(pip_args)
        allow_user_fallback = False

    command = build_pip_install_command(requirement, pip_args_tuple)

    try:
        _run_command(command)
    except InstallationError:
        if not allow_user_fallback:
            raise
        if running_inside_virtualenv() or not is_user_site_enabled():
            raise
        fallback_args = ("--user",)
        fallback_command = build_pip_install_command(requirement, fallback_args)
        _run_command(fallback_command)

    return True


def _format_command(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(arg) for arg in command)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Instala automaticamente a dependência reportbro-lib.",
    )
    parser.add_argument(
        "--requirements",
        type=Path,
        default=DEFAULT_REQUIREMENTS_PATH,
        help="caminho alternativo para o ficheiro requirements.txt",
    )
    parser.add_argument(
        "--pip-arg",
        dest="pip_args",
        action="append",
        default=None,
        help="argumento adicional a passar ao pip (pode ser usado várias vezes)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="força a reinstalação mesmo que a dependência já exista",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="mostra o comando que seria executado sem instalar nada",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suprime mensagens informativas",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    pip_args: Sequence[str] | None = tuple(args.pip_args) if args.pip_args else None

    try:
        requirement = load_reportbro_requirement(args.requirements)
    except InstallationError as exc:
        parser.error(str(exc))

    command = build_pip_install_command(
        requirement,
        pip_args if pip_args is not None else default_pip_args(),
    )

    if args.dry_run:
        print(_format_command(command))
        return 0

    try:
        installed = ensure_reportbro_installed(
            requirements_path=args.requirements,
            pip_args=pip_args,
            force=args.force,
        )
    except InstallationError as exc:
        if not args.quiet:
            print(str(exc), file=sys.stderr)
        return 1

    if not args.quiet:
        if installed:
            print("Instalação concluída com sucesso.")
        else:
            print("O ReportBro já se encontra instalado.")
    return 0


__all__ = [
    "InstallationError",
    "ReportBroRequirement",
    "REPORTBRO_REQUIREMENT",
    "DEFAULT_REQUIREMENTS_PATH",
    "build_pip_install_command",
    "default_pip_args",
    "ensure_reportbro_installed",
    "is_requirement_satisfied",
    "is_user_site_enabled",
    "running_inside_virtualenv",
    "load_reportbro_requirement",
    "main",
]
