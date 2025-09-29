from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from app.server.services import report_service


def test_generate_pdf_applies_currency_overrides(monkeypatch):
    captured: dict[str, Any] = {}

    class RecordingReport:
        def __init__(self, template: Mapping[str, Any], data: Mapping[str, Any]):
            captured["template"] = deepcopy(template)
            self.errors: list[Any] = []

        def generate_pdf(self) -> bytes:
            return b"%PDF-1.4\n%server\n"

    monkeypatch.setattr(report_service, "Report", RecordingReport)

    template_path = Path("reporting/templates/ft_gestao_00_base.json")
    template_dict = json.loads(template_path.read_text(encoding="utf-8"))
    dataset = {
        "currency_symbol": "£",
        "currency_code": "GBP",
        "locale_code": "en_GB",
    }

    pdf_bytes = report_service.generate_pdf(template_dict, dataset)

    assert pdf_bytes.startswith(b"%PDF-1.4")
    template_used = captured.get("template")
    assert isinstance(template_used, Mapping)
    properties = template_used.get("documentProperties")
    assert isinstance(properties, Mapping)
    assert properties["patternCurrencySymbol"] == "£"
    assert properties["patternLocale"] == "en_GB"


def test_generate_pdf_applies_color_overrides(monkeypatch):
    captured: dict[str, Any] = {}

    class RecordingReport:
        def __init__(self, template: Mapping[str, Any], data: Mapping[str, Any]):
            captured["template"] = deepcopy(template)
            self.errors: list[Any] = []

        def generate_pdf(self) -> bytes:
            return b"%PDF-1.4\n%server\n"

    monkeypatch.setattr(report_service, "Report", RecordingReport)

    template_path = Path("reporting/templates/ft_gestao_00_base.json")
    template_dict = json.loads(template_path.read_text(encoding="utf-8"))
    dataset = {
        "FoodCost_Nivel1_Cor": "#AA0001",
        "FoodCost_Nivel2_Cor": "#AA0002",
        "FoodCost_Nivel3_Cor": "#AA0003",
        "FoodCost_Nivel4_Cor": "#AA0004",
        "FoodCost_Nivel5_Cor": "#AA0005",
    }
    expected_colors = set(dataset.values())

    pdf_bytes = report_service.generate_pdf(template_dict, dataset)

    assert pdf_bytes.startswith(b"%PDF-1.4")
    template_used = captured.get("template")
    assert isinstance(template_used, Mapping)

    seen_colors: list[str] = []

    def _collect(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                if key in {"backgroundColor", "cs_backgroundColor"} and isinstance(
                    value, str
                ):
                    seen_colors.append(value)
                _collect(value)
        elif isinstance(node, list):
            for item in node:
                _collect(item)

    _collect(template_used)

    effective_colors = [color for color in seen_colors if color]
    assert not any(
        color.startswith("${FoodCost_Nivel") for color in effective_colors
    )
    assert expected_colors.issubset(set(effective_colors))
