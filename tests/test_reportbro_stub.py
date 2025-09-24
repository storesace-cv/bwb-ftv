from __future__ import annotations

from ui.reportbro_stub import (
    discover_reportbro_templates,
    get_offline_reportbro_explanation,
    get_offline_reportbro_recommendations,
)


def test_discover_reportbro_templates_lists_existing_templates(tmp_path, monkeypatch):
    template_a = tmp_path / "a_template.json"
    template_b = tmp_path / "b_template.json"
    template_a.write_text("{}", encoding="utf-8")
    template_b.write_text("{}", encoding="utf-8")

    monkeypatch.setattr("ui.reportbro_stub.TEMPLATES_DIR", tmp_path)

    discovered = discover_reportbro_templates()
    assert discovered == [template_a, template_b]


def test_discover_reportbro_templates_default_directory_contains_fixture():
    discovered = discover_reportbro_templates()
    names = {path.name for path in discovered}
    assert "ft_gestao_reportbro.json" in names


def test_offline_explanation_mentions_environment_variable():
    explanation = get_offline_reportbro_explanation()
    assert "Gestor de Documentos (modo offline)" in explanation
    assert "FTV_REPORTBRO_EDITOR_URL" in explanation


def test_offline_recommendations_cover_configuration_steps():
    recommendations = get_offline_reportbro_recommendations()
    assert any("FTV_REPORTBRO_EDITOR_URL" in item for item in recommendations)
    assert any("Reinicie a aplicação" in item or "reinicie" in item.lower() for item in recommendations)
