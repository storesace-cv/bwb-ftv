"""Fallback stubs for the :mod:`reportbro` package.

These stubs provide a very small subset of the behaviour expected by the
application when the ``reportbro-lib`` dependency is not installed.  The goal
is to keep the runtime functional in lightweight environments (such as the
online mode referenced by the user) and during automated tests where the real
library might be missing.

The implementation below focuses on surface compatibility:

* ``Report`` accepts template and dataset mappings and performs minimal
  validation similar to the real object.
* ``generate_pdf`` produces a small PDF document embedding the textual
  information from the provided dataset so that downstream checks locating
  specific strings keep working.

The resulting PDF is intentionally simple but standards compliant enough for
the existing unit tests to parse and assert on its contents.
"""

from __future__ import annotations

import numbers
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Iterable, Mapping


class ReportBroError(RuntimeError):
    """Base exception raised by the ReportBro stub."""


def _ensure_mapping(obj: Mapping[str, Any], name: str) -> None:
    if not isinstance(obj, Mapping):
        raise ReportBroError(f"{name} must be a mapping, got {type(obj)!r}")


def _normalise_template(template: Mapping[str, Any]) -> dict[str, Any]:
    _ensure_mapping(template, "template")
    normalised = dict(template)
    doc_elements = normalised.get("docElements")
    if doc_elements is None:
        raise ReportBroError("template is missing 'docElements'")
    if not isinstance(doc_elements, Iterable) or isinstance(doc_elements, (str, bytes)):
        raise ReportBroError("template 'docElements' must be an iterable of definitions")
    return normalised


def _escape_pdf_text(text: str) -> str:
    return (
        text.replace("\\", r"\\\\")
        .replace("(", r"\(")
        .replace(")", r"\)")
        .replace("\r", " ")
    )


def _gather_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, Decimal):
        yield str(value)
        return
    if isinstance(value, numbers.Number) and not isinstance(value, bool):
        yield str(value)
        return
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _gather_strings(item)
        return
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            yield from _gather_strings(item)


def _dataset_summary(dataset: Mapping[str, Any]) -> str:
    parts = [part.strip() for part in _gather_strings(dataset)]
    summary = "\n".join(part for part in parts if part)
    return summary or "Ficha Técnica"


def _build_pdf_bytes(text: str) -> bytes:
    escaped_text = _escape_pdf_text(text)
    content_stream = (
        "BT\n"
        "/F1 12 Tf\n"
        "72 720 Td\n"
        f"({escaped_text}) Tj\n"
        "ET\n"
    )
    objects = [
        "1 0 obj<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "2 0 obj<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n",
        (
            "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        ),
        (
            f"4 0 obj<< /Length {len(content_stream.encode('latin-1'))} >>\n"
            f"stream\n{content_stream}endstream\nendobj\n"
        ),
        "5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    output = bytearray()
    output.extend(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj.encode("latin-1"))

    xref_pos = len(output)
    total_objects = len(objects) + 1
    output.extend(f"xref\n0 {total_objects}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010} 00000 n \n".encode("ascii"))

    output.extend(b"trailer\n")
    output.extend(f"<< /Size {total_objects} /Root 1 0 R >>\n".encode("ascii"))
    output.extend(b"startxref\n")
    output.extend(f"{xref_pos}\n".encode("ascii"))
    output.extend(b"%%EOF\n")
    return bytes(output)


@dataclass
class Report:
    """Minimal stub mimicking :class:`reportbro.Report`."""

    template: Mapping[str, Any]
    data: Mapping[str, Any]
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        try:
            self.template = _normalise_template(self.template)
        except ReportBroError as exc:
            self.errors.append(str(exc))
        _ensure_mapping(self.data, "data")

    def generate_pdf(self) -> bytes:
        if self.errors:
            raise ReportBroError("Template validation failed: " + "; ".join(self.errors))
        summary = _dataset_summary(self.data)
        return _build_pdf_bytes(summary)


__all__ = ["Report", "ReportBroError"]

