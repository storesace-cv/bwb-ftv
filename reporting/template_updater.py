"""Helpers for synchronising ReportBro template base files with updater copies."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import shutil
from typing import Iterable, Sequence

LOGGER = logging.getLogger(__name__)

_DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


@dataclass(slots=True)
class TemplateUpdateSummary:
    """Summary of template synchronisation results."""

    updated: list[Path]
    skipped: list[Path]
    missing_updater: list[Path]
    errors: list[tuple[Path, str]]

    def any_updates(self) -> bool:
        """Return ``True`` if any base files were updated."""

        return bool(self.updated)

    def all_results(self) -> Sequence[Path]:
        """Return all processed base paths regardless of outcome."""

        return (*self.updated, *self.skipped, *self.missing_updater)


def _iter_base_templates(directory: Path) -> Iterable[Path]:
    """Yield candidate base template files from ``directory``."""

    yield from sorted(path for path in directory.glob("*_base.json") if path.is_file())


def _resolve_updater_path(base_path: Path) -> Path:
    """Return the updater path for ``base_path``."""

    base_name = base_path.name
    if not base_name.endswith("_base.json"):
        return base_path
    stem = base_name[: -len("_base.json")]
    return base_path.with_name(f"{stem}_base_updater.json")


def apply_template_updaters(directory: Path | None = None) -> TemplateUpdateSummary:
    """Apply newer ``*_base_updater.json`` files over their base counterparts.

    Parameters
    ----------
    directory:
        Optional directory containing the ReportBro templates.  Defaults to the
        canonical ``reporting/templates`` folder.

    Returns
    -------
    TemplateUpdateSummary
        Summary describing which files were updated, skipped or missing.
    """

    target_dir = Path(directory) if directory is not None else _DEFAULT_TEMPLATE_DIR
    summary = TemplateUpdateSummary(updated=[], skipped=[], missing_updater=[], errors=[])

    if not target_dir.exists():
        LOGGER.info("[ReportBro] Diretório de templates inexistente para sincronização: %s", target_dir)
        return summary

    for base_path in _iter_base_templates(target_dir):
        updater_path = _resolve_updater_path(base_path)
        if updater_path == base_path:
            summary.skipped.append(base_path)
            LOGGER.debug("[ReportBro] Ficheiro base %s não segue convenção esperada; ignorado.", base_path)
            continue

        if not updater_path.exists():
            summary.missing_updater.append(base_path)
            LOGGER.info(
                "[ReportBro] Nenhum updater encontrado para %s (esperado: %s)",
                base_path.name,
                updater_path.name,
            )
            continue

        try:
            base_mtime = base_path.stat().st_mtime
        except OSError as exc:
            summary.errors.append((base_path, str(exc)))
            LOGGER.exception(
                "[ReportBro] Falha ao obter metadata de %s", base_path,
            )
            continue

        try:
            updater_mtime = updater_path.stat().st_mtime
        except OSError as exc:
            summary.errors.append((base_path, str(exc)))
            LOGGER.exception(
                "[ReportBro] Falha ao obter metadata de updater %s", updater_path,
            )
            continue

        if updater_mtime <= base_mtime:
            summary.skipped.append(base_path)
            LOGGER.debug(
                "[ReportBro] Updater %s não é mais recente que %s; ignorado.",
                updater_path.name,
                base_path.name,
            )
            continue

        try:
            shutil.copy2(updater_path, base_path)
        except OSError as exc:
            summary.errors.append((base_path, str(exc)))
            LOGGER.exception(
                "[ReportBro] Falha ao actualizar %s usando %s", base_path.name, updater_path.name
            )
            continue

        summary.updated.append(base_path)
        LOGGER.info(
            "[ReportBro] Template %s actualizado a partir de %s", base_path.name, updater_path.name
        )

    return summary


__all__ = ["TemplateUpdateSummary", "apply_template_updaters"]
