"""Services responsible for rendering ReportBro templates."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from reporting.reportbro_normalizer import STATIC_SECTION_PARAMETER, normalise_template

try:
    from reportbro import Report, ReportBroError
except ModuleNotFoundError:  # pragma: no cover - fallback in dev without reportbro-lib
    from reporting._stubs.reportbro import Report, ReportBroError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DATA_PATH = PROJECT_ROOT / "reporting" / "samples" / "sample_data.json"


class TemplateError(ValueError):
    """Raised when a template payload is invalid."""


class DataError(ValueError):
    """Raised when the data payload is invalid."""


class RenderError(RuntimeError):
    """Raised when ReportBro fails to render a document."""


logger = logging.getLogger(__name__)


@dataclass
class RenderContext:
    """Payload passed to ReportBro."""

    template: dict[str, Any]
    data: dict[str, Any]


def _validate_template(template: dict[str, Any]) -> None:
    if "documentProperties" not in template:
        raise TemplateError("Template JSON inválido: faltam 'documentProperties'.")


def _normalise_document_properties(template: dict[str, Any]) -> None:
    properties = template.get("documentProperties")
    if not isinstance(properties, dict):
        return

    page_format = properties.get("pageFormat")
    if not isinstance(page_format, str) or not page_format.strip():
        page_size = properties.get("pageSize")
        if isinstance(page_size, str) and page_size.strip():
            properties["pageFormat"] = page_size.strip()
        else:
            properties["pageFormat"] = "A4"

    def _looks_like_point_dimension(value: Any) -> bool:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        return number > 400

    doc_elements = template.get("docElements")
    suspect_point_units = False
    if isinstance(doc_elements, Iterable):
        for element in doc_elements:
            if not isinstance(element, dict):
                continue
            if _looks_like_point_dimension(element.get("height")):
                suspect_point_units = True
                break
            content = element.get("contentData")
            if isinstance(content, dict) and _looks_like_point_dimension(
                content.get("height")
            ):
                suspect_point_units = True
                break

    unit = properties.get("unit")
    if isinstance(unit, str):
        cleaned_unit = unit.strip().lower()
    else:
        cleaned_unit = ""

    if cleaned_unit == "mm" and suspect_point_units:
        point_to_mm = 25.4 / 72.0
        dimension_keys = {
            "x",
            "y",
            "width",
            "height",
            "paddingLeft",
            "paddingRight",
            "paddingTop",
            "paddingBottom",
            "marginLeft",
            "marginRight",
            "marginTop",
            "marginBottom",
            "pageWidth",
            "pageHeight",
            "headerSize",
            "footerSize",
        }

        def _convert_entry(mapping: dict[str, Any]) -> dict[str, Any]:
            converted = dict(mapping)
            for key in dimension_keys:
                if key in converted:
                    value = converted.get(key)
                    try:
                        number = float(value)
                    except (TypeError, ValueError):
                        continue
                    if key == "height" and number <= 0:
                        converted[key] = 120.0
                        continue
                    if number <= 50:
                        continue
                    converted[key] = round(number * point_to_mm, 3)
            return converted

        updated_properties = _convert_entry(properties)
        template["documentProperties"] = updated_properties
        properties = updated_properties

        def _convert_node(node: Any) -> Any:
            if isinstance(node, dict):
                converted = _convert_entry(node)
                for key, value in list(converted.items()):
                    converted[key] = _convert_node(value)
                return converted
            if isinstance(node, Iterable) and not isinstance(node, (str, bytes, bytearray)):
                return [_convert_node(item) for item in node]
            return node

        template["docElements"] = _convert_node(doc_elements)


def _normalise_parameter_ids(template: dict[str, Any]) -> None:
    parameters = template.get("parameters")
    if not isinstance(parameters, Iterable):
        return

    def _assign_child_ids(children: Iterable[Any]) -> list[dict[str, Any]]:
        normalised_children: list[dict[str, Any]] = []
        for index, child in enumerate(children, start=1):
            if not isinstance(child, dict):
                continue

            mutable_child = child.copy()
            raw_child_id = mutable_child.get("id")
            child_id: int | None = None
            if isinstance(raw_child_id, int):
                child_id = raw_child_id
            elif isinstance(raw_child_id, str):
                digits = "".join(ch for ch in raw_child_id if ch.isdigit())
                if digits:
                    try:
                        child_id = int(digits)
                    except ValueError:
                        child_id = None

            if child_id is None:
                child_id = index

            mutable_child["id"] = child_id

            grand_children = mutable_child.get("children")
            if isinstance(grand_children, Iterable) and not isinstance(
                grand_children, (str, bytes, bytearray)
            ):
                mutable_child["children"] = _assign_child_ids(grand_children)

            normalised_children.append(mutable_child)

        return normalised_children

    normalised: list[dict[str, Any]] = []
    for index, parameter in enumerate(parameters, start=1):
        if not isinstance(parameter, dict):
            continue

        mutable = parameter.copy()

        raw_id = mutable.get("id")
        assigned: int | None = None
        if isinstance(raw_id, int):
            assigned = raw_id
        elif isinstance(raw_id, str):
            digits = "".join(ch for ch in raw_id if ch.isdigit())
            if digits:
                try:
                    assigned = int(digits)
                except ValueError:
                    assigned = None

        if assigned is None:
            assigned = index

        mutable["id"] = assigned

        children = mutable.get("children")
        if isinstance(children, Iterable) and not isinstance(children, (str, bytes, bytearray)):
            mutable["children"] = _assign_child_ids(children)

        normalised.append(mutable)

    template["parameters"] = normalised


def _normalise_image_sources(template: dict[str, Any]) -> None:
    parameters = {
        param.get("name"): param
        for param in template.get("parameters", [])
        if isinstance(param, dict)
    }

    elements = template.get("docElements")
    if not isinstance(elements, Iterable):
        return

    normalised_elements: list[dict[str, Any]] = []
    for element in elements:
        if not isinstance(element, dict):
            continue

        mutable = element.copy()
        if mutable.get("elementType") == "image":
            source = mutable.get("source")
            if isinstance(source, str):
                stripped = source.strip()
                if stripped.startswith("${") and stripped.endswith("}"):
                    pass
                else:
                    if stripped.startswith("@"):
                        stripped = stripped.lstrip("@")
                    if stripped in parameters and stripped:
                        mutable["source"] = f"${{{stripped}}}"
        normalised_elements.append(mutable)

    template["docElements"] = normalised_elements


def _ensure_title_binding(template: dict[str, Any]) -> None:
    elements = template.get("docElements")
    if not isinstance(elements, Iterable):
        return

    normalised_elements: list[dict[str, Any]] = []
    replacement_done = False
    for element in elements:
        if not isinstance(element, dict):
            continue
        mutable = element.copy()
        if not replacement_done and mutable.get("elementType") == "text":
            content = mutable.get("content")
            if isinstance(content, str):
                stripped = content.strip()
                if stripped.startswith("${") and stripped.endswith("}"):
                    replacement_done = True
                elif stripped.upper() == "FICHA DE ARTIGO":
                    mutable["content"] = "${title}"
                    replacement_done = True
        normalised_elements.append(mutable)

    if normalised_elements:
        template["docElements"] = normalised_elements


def _load_default_data() -> dict[str, Any]:
    if not SAMPLE_DATA_PATH.exists():
        raise DataError(
            "Ficheiro sample_data.json não encontrado. Execute o script de bootstrap para o criar."
        )
    try:
        return json.loads(SAMPLE_DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise DataError(f"sample_data.json inválido: {exc}.") from exc


def _normalise_data(data: dict[str, Any] | None) -> dict[str, Any]:
    if data is None:
        return _load_default_data()
    return data


def _is_invalid_size_error(entry: Any) -> bool:
    if isinstance(entry, Mapping):
        key = entry.get("msg_key")
        if isinstance(key, str) and key == "errorMsgInvalidSize":
            return True
    if isinstance(entry, str) and "errorMsgInvalidSize" in entry:
        return True
    return False


def _render_fallback_pdf(data: Mapping[str, Any]) -> bytes:
    try:
        from reporting._stubs.reportbro import _build_pdf_bytes
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive guard
        raise RenderError("Fallback renderer indisponível") from exc

    codigo = data.get("product_codigo") or data.get("Produtos_Codigo") or ""
    nome = data.get("product_nome") or data.get("Produtos_Nome") or ""
    ingredientes = list(data.get("ingredientes") or [])
    totals = data.get("totals_data") or data.get("totais_data") or {}

    lines = [
        "Ficha Técnica de Gestão (fallback)",
        f"CÓDIGO: {codigo}",
        f"NOME: {nome}",
        "Ingredientes:",
    ]

    if ingredientes:
        for entry in ingredientes:
            def _entry_value(*keys: str) -> Any:
                for key in keys:
                    if key in entry:
                        value = entry.get(key)
                        if value not in (None, ""):
                            return value
                return None

            nome_ingrediente = _entry_value(
                "FichasTecnicas_ComponenteNome",
                "ingrediente",
                "nome",
                "codigo",
            ) or "—"
            quantidade = _entry_value("FichasTecnicas_Qtd", "quantidade")
            unidade = _entry_value(
                "FichasTecnicas_Unidade",
                "um",
                "unidade",
            ) or ""
            if isinstance(quantidade, (int, float)):
                quantidade_text = f"{quantidade}"
            else:
                quantidade_text = (
                    str(quantidade) if quantidade not in (None, "") else "—"
                )
            parts = [nome_ingrediente, quantidade_text]
            if unidade:
                parts.append(unidade)
            lines.append(" - " + " ".join(parts).strip())
    else:
        lines.append(" - —")

    custo_total = totals.get("custo_total")
    lines.append(f"Custo total: {custo_total if custo_total is not None else '—'}")

    text = "\n".join(str(line) for line in lines)
    return _build_pdf_bytes(text)


def _format_errors(errors: Iterable[Any]) -> str:
    parts: list[str] = []
    for entry in errors:
        try:
            parts.append(str(entry))
        except Exception:  # pragma: no cover - defensive
            parts.append(repr(entry))
    return "; ".join(parts)


def _build_context(template: dict[str, Any], data: dict[str, Any] | None) -> RenderContext:
    if not isinstance(template, dict):
        raise TemplateError("Template JSON inválido.")
    normalised_template, _ = normalise_template(template)
    _validate_template(normalised_template)
    template = normalised_template
    _normalise_document_properties(template)
    _normalise_parameter_ids(template)
    _normalise_image_sources(template)
    _ensure_title_binding(template)
    normalised_data = _normalise_data(data)
    if not isinstance(normalised_data, dict):
        raise DataError("Dados inválidos: deve ser um objeto JSON.")
    required_parameters = {
        param.get("name")
        for param in template.get("parameters", [])
        if isinstance(param, dict)
    }
    if STATIC_SECTION_PARAMETER in required_parameters:
        normalised_data.setdefault(STATIC_SECTION_PARAMETER, [{}])
    return RenderContext(template=template, data=normalised_data)


def generate_pdf(template_dict: dict[str, Any], data_dict: dict[str, Any] | None = None) -> bytes:
    """Render the provided template and return a PDF document."""

    context = _build_context(template_dict, data_dict)
    try:
        report = Report(context.template, context.data)
    except AssertionError as exc:  # pragma: no cover - defensive
        raise RenderError(f"Template inválido: {exc}") from exc

    if getattr(report, "errors", None):
        if any(_is_invalid_size_error(error) for error in report.errors):
            logger.warning(
                "[ReportBro] Erro de dimensão inválida no servidor; fallback ativado"
            )
            return _render_fallback_pdf(context.data)
        raise RenderError(f"ReportBro falhou: {_format_errors(report.errors)}")

    try:
        return report.generate_pdf()
    except ReportBroError as exc:  # pragma: no cover - requires reportbro-lib
        message = str(exc)
        if "errorMsgInvalidSize" in message:
            logger.warning(
                "[ReportBro] Erro de dimensão inválida durante renderização no servidor; fallback ativado"
            )
            return _render_fallback_pdf(context.data)
        raise RenderError(f"Falha ao gerar PDF: {exc}.") from exc


def generate_xlsx(template_dict: dict[str, Any], data_dict: dict[str, Any] | None = None) -> bytes:
    """Render the provided template and return an XLSX document."""

    context = _build_context(template_dict, data_dict)
    try:
        report = Report(context.template, context.data)
        if hasattr(report, "generate_xlsx"):
            xlsx_bytes = report.generate_xlsx()
        else:  # pragma: no cover - fallback quando se usa o stub
            raise RenderError(
                "A biblioteca reportbro-lib instalada não suporta exportação XLSX nesta configuração."
            )
    except ReportBroError as exc:  # pragma: no cover - requires reportbro-lib
        raise RenderError(f"Falha ao gerar XLSX: {exc}.") from exc
    return xlsx_bytes


__all__ = [
    "DataError",
    "RenderError",
    "TemplateError",
    "generate_pdf",
    "generate_xlsx",
]
