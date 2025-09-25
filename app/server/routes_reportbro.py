"""Flask routes exposing the ReportBro Designer endpoints."""

from __future__ import annotations
import json
import logging
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import secrets
import threading
import time
from typing import Any, Iterable

from flask import Blueprint, Response, current_app, jsonify, request

from .services import DataError, RenderError, TemplateError, generate_pdf, generate_xlsx

LOGGER = logging.getLogger(__name__)
reportbro_blueprint = Blueprint("reportbro", __name__)
TEMPLATE_NAME_PATTERN = re.compile(r"^[a-z0-9_-]+$")
PREVIEW_CACHE_LOCK = threading.Lock()
PREVIEW_CACHE: dict[str, dict[str, Any]] = {}
PREVIEW_KEYS = deque[str]()
PREVIEW_CACHE_SIZE = 5


@dataclass
class TemplateMetadata:
    """Metadata describing a stored template."""

    name: str
    updated_at: str
    size_bytes: int


def _get_templates_store_dir() -> Path:
    return Path(current_app.config["TEMPLATES_STORE_DIR"])


def _get_templates_runtime_dir() -> Path:
    return Path(current_app.config["TEMPLATES_RUNTIME_DIR"])


def _resolve_template_path(name: str) -> Path:
    """Return the runtime path for *name* inside the reporting directory."""

    return _get_templates_runtime_dir() / f"{name}.json"


def _resolve_store_template_path(name: str) -> Path:
    """Return the immutable template path from the template store."""

    return _get_templates_store_dir() / f"{name}.json"


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except FileNotFoundError as exc:
        raise TemplateError(f"Template '{path.stem}' não existe.") from exc
    except json.JSONDecodeError as exc:
        raise TemplateError(f"Template '{path.stem}' está corrompido: {exc}.") from exc


def _normalise_template_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and "template" in payload:
        payload = payload["template"]
    if not isinstance(payload, dict):
        raise TemplateError("O corpo do pedido deve conter um JSON de template válido.")
    return payload


def _parse_json_or_dict(payload: Any, field: str) -> dict[str, Any] | None:
    data = payload.get(field)
    if data is None:
        return None
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError as exc:
            raise DataError(f"Campo '{field}' não contém JSON válido: {exc}.") from exc
    if isinstance(data, dict):
        return data
    raise DataError(f"Campo '{field}' deve ser um objeto JSON ou uma string contendo JSON.")


def _serialize_metadata(items: Iterable[TemplateMetadata]) -> list[dict[str, Any]]:
    return [
        {
            "name": item.name,
            "updated_at": item.updated_at,
            "size_bytes": item.size_bytes,
        }
        for item in items
    ]


@reportbro_blueprint.route("/templates/list", methods=["GET"])
def list_templates() -> Response:
    runtime_dir = _get_templates_runtime_dir()
    store_dir = _get_templates_store_dir()

    combined: dict[str, Path] = {}
    for path in store_dir.glob("*.json"):
        combined[path.stem] = path
    for path in runtime_dir.glob("*.json"):
        combined[path.stem] = path

    templates: list[TemplateMetadata] = []
    for name in sorted(combined):
        path = combined[name]
        stat = path.stat()
        updated_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        templates.append(
            TemplateMetadata(
                name=name,
                updated_at=updated_at,
                size_bytes=stat.st_size,
            )
        )
    return jsonify(_serialize_metadata(templates))


@reportbro_blueprint.route("/templates/<string:name>", methods=["GET"])
def get_template(name: str) -> Response:
    _validate_template_name(name)
    runtime_path = _resolve_template_path(name)
    if runtime_path.exists():
        template = _read_json_file(runtime_path)
    else:
        template = _read_json_file(_resolve_store_template_path(name))
    return jsonify(template)


@reportbro_blueprint.route("/templates/<string:name>", methods=["POST"])
def save_template(name: str) -> Response:
    _validate_template_name(name)
    overwrite = request.args.get("overwrite") == "1"
    path = _resolve_template_path(name)
    if path.exists() and not overwrite:
        return (
            jsonify(
                {
                    "error": "Template já existe. Utilize ?overwrite=1 para confirmar a substituição.",
                    "requires_confirmation": True,
                }
            ),
            409,
        )

    payload = request.get_json(force=True, silent=False)
    try:
        template = _normalise_template_payload(payload)
    except TemplateError as exc:
        return jsonify({"error": str(exc)}), 400

    path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    stat = path.stat()
    metadata = TemplateMetadata(
        name=path.stem,
        updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        size_bytes=stat.st_size,
    )
    return jsonify({"saved": True, "template": template, "metadata": metadata.__dict__})


@reportbro_blueprint.route("/rb/preview", methods=["GET", "POST", "PUT"])
def preview_pdf() -> Response:
    if request.method == "GET":
        return _preview_download()
    if request.method == "PUT":
        return _preview_store_from_designer()
    return _preview_direct_response()


@reportbro_blueprint.route("/rb/export/xlsx", methods=["POST"])
def export_xlsx() -> Response:
    try:
        payload = request.get_json(force=True, silent=False)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Pedido inválido para exportação XLSX", exc_info=exc)
        return jsonify({"error": "Pedido inválido."}), 400

    if not isinstance(payload, dict):
        return jsonify({"error": "Corpo do pedido deve ser JSON."}), 400

    try:
        template = _parse_json_or_dict(payload, "templateJson")
        if template is None:
            raise TemplateError("Campo 'templateJson' é obrigatório.")
        data = _parse_json_or_dict(payload, "dataJson")
        xlsx_bytes = generate_xlsx(template, data)
    except (TemplateError, DataError) as exc:
        return jsonify({"error": str(exc)}), 400
    except RenderError as exc:
        LOGGER.exception("Erro ao gerar XLSX")
        return jsonify({"error": str(exc)}), 500

    return Response(
        xlsx_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=export.xlsx"},
    )


def _preview_store_from_designer() -> Response:
    try:
        payload = request.get_json(force=True, silent=False)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Pedido inválido para preview", exc_info=exc)
        return jsonify({"errors": [str(exc)]}), 400

    if not isinstance(payload, dict):
        return jsonify({"errors": ["Corpo do pedido deve ser JSON."]}), 400

    template = payload.get("report")
    data = payload.get("data")
    try:
        if isinstance(data, str):
            data = json.loads(data)
        pdf_bytes = generate_pdf(template, data)
    except (TemplateError, DataError) as exc:
        return jsonify({"errors": [str(exc)]}), 400
    except RenderError as exc:
        LOGGER.exception("Erro ao gerar PDF")
        return jsonify({"errors": [str(exc)]}), 500

    key = _store_preview_context(template, data)
    _store_rendered_bytes(key, "pdf", pdf_bytes)
    return Response(f"key:{key}", mimetype="text/plain")


def _preview_download() -> Response:
    key = request.args.get("key")
    if not key:
        return jsonify({"errors": ["Parâmetro 'key' é obrigatório."]}), 400
    output_format = request.args.get("outputFormat", "pdf").lower()
    context = _get_preview_context(key)
    if context is None:
        return jsonify({"errors": ["Pré-visualização expirada ou inexistente."]}), 404

    try:
        if output_format == "pdf":
            pdf_bytes = context.get("pdf")
            if pdf_bytes is None:
                pdf_bytes = generate_pdf(context["template"], context["data"])
                _store_rendered_bytes(key, "pdf", pdf_bytes)
            return Response(
                pdf_bytes,
                mimetype="application/pdf",
                headers={"Content-Disposition": "inline; filename=preview.pdf"},
            )
        if output_format == "xlsx":
            xlsx_bytes = context.get("xlsx")
            if xlsx_bytes is None:
                xlsx_bytes = generate_xlsx(context["template"], context["data"])
                _store_rendered_bytes(key, "xlsx", xlsx_bytes)
            return Response(
                xlsx_bytes,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=preview.xlsx"},
            )
    except RenderError as exc:
        LOGGER.exception("Erro ao renderizar pré-visualização")
        return jsonify({"errors": [str(exc)]}), 500

    return jsonify({"errors": ["Formato solicitado não é suportado."]}), 400


def _preview_direct_response() -> Response:
    try:
        payload = request.get_json(force=True, silent=False)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Pedido inválido para preview", exc_info=exc)
        return jsonify({"error": "Pedido inválido."}), 400

    try:
        template = _parse_json_or_dict(payload, "templateJson")
        if template is None:
            raise TemplateError("Campo 'templateJson' é obrigatório.")
        data = _parse_json_or_dict(payload, "dataJson")
        pdf_bytes = generate_pdf(template, data)
    except (TemplateError, DataError) as exc:
        return jsonify({"error": str(exc)}), 400
    except RenderError as exc:
        LOGGER.exception("Erro ao gerar PDF")
        return jsonify({"error": str(exc)}), 500

    key = _store_preview_context(template, data)
    _store_rendered_bytes(key, "pdf", pdf_bytes)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": "inline; filename=preview.pdf"},
    )


def _store_rendered_bytes(key: str, output_format: str, content: bytes) -> None:
    with PREVIEW_CACHE_LOCK:
        context = PREVIEW_CACHE.get(key)
        if context is None:
            return
        context[output_format] = content


def _store_preview_context(template: dict[str, Any], data: dict[str, Any] | None) -> str:
    key = secrets.token_urlsafe(12)
    with PREVIEW_CACHE_LOCK:
        PREVIEW_CACHE[key] = {"template": template, "data": data, "timestamp": time.time()}
        PREVIEW_KEYS.append(key)
        while len(PREVIEW_KEYS) > PREVIEW_CACHE_SIZE:
            old_key = PREVIEW_KEYS.popleft()
            PREVIEW_CACHE.pop(old_key, None)
    return key


def _get_preview_context(key: str) -> dict[str, Any] | None:
    with PREVIEW_CACHE_LOCK:
        context = PREVIEW_CACHE.get(key)
        if context:
            context["timestamp"] = time.time()
        return context


def _validate_template_name(name: str) -> None:
    if not TEMPLATE_NAME_PATTERN.match(name):
        raise TemplateError(
            "Nome do template inválido. Utilize apenas letras minúsculas, números, hífen e underscore."
        )
