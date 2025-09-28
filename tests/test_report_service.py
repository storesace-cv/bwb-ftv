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

    template_path = Path("app/templates_store/templates/ft_gestao_00_base.json")
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
