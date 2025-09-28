"""Utilities for generating report graphics."""

from __future__ import annotations

from typing import Iterable, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  # isort:skip

from utils.paths import get_project_root


def _normalise_weight(entry: Mapping[str, object]) -> float:
    raw = entry.get("FichasTecnicas_Peso")
    if raw is None:
        raw = entry.get("peso")
    try:
        weight = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
    return float(weight)


def _normalise_label(entry: Mapping[str, object]) -> str:
    for key in ("FichasTecnicas_ComponenteNome", "nome", "codigo"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Ingrediente"


def gerar_grafico_foodcost_pie(
    ingredients: Iterable[Mapping[str, object]] | None,
) -> str:
    """Generate a pie chart for ingredient weights and return the saved path."""

    entries = list(ingredients or [])
    labels: list[str] = []
    weights: list[float] = []

    for entry in entries:
        weight = _normalise_weight(entry)
        if weight <= 0:
            continue
        labels.append(_normalise_label(entry))
        weights.append(weight)

    if not weights:
        labels = ["Sem dados"]
        weights = [1.0]

    fig, ax = plt.subplots()
    try:
        ax.pie(weights, labels=labels, autopct="%1.2f%%")
        ax.axis("equal")

        images_dir = get_project_root() / "databases" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        output_path = images_dir / "foodcost_pie.png"
        fig.savefig(output_path, bbox_inches="tight")
    finally:
        plt.close(fig)

    return str(output_path)


__all__ = ["gerar_grafico_foodcost_pie"]
