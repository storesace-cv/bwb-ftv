"""Integration tests for the allergen import workflow."""

from __future__ import annotations

import json
import re
from typing import Iterator

import pytest

from data.datastore import DataStore
from services import allergens as allergen_service


@pytest.fixture()
def memory_datastore(monkeypatch: pytest.MonkeyPatch) -> Iterator[DataStore]:
    """Provide an in-memory :class:`DataStore` instance for tests."""

    monkeypatch.setattr(DataStore, "_ensure_required_tables", lambda self: None)
    ds = DataStore(db_path=":memory:")
    try:
        yield ds
    finally:
        ds.close()


def test_import_allergens_rejects_invalid_entries(
    tmp_path, memory_datastore: DataStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid payload entries should abort the import without side effects."""

    ds = memory_datastore

    payload = [
        {
            "id": 1,
            "nome": "Glúten",
            "nome_ingles": "Gluten",
            "descricao": "Presente em cereais",
            "exemplos": ["Trigo"],
            "notas": "Nenhuma",
        },
        {
            "id": 0,
            "nome": "",
            "nome_ingles": "Invalid",
            "descricao": None,
            "exemplos": None,
            "notas": None,
        },
    ]
    source = tmp_path / "allergens.json"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(allergen_service, "get_project_root", lambda: tmp_path)

    with pytest.raises(ValueError) as excinfo:
        allergen_service.import_allergens(source, ds.conn)
    assert "Invalid allergen id" in str(excinfo.value)

    cur = ds.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Alergenios")
    assert cur.fetchone()[0] == 0

    backups_dir = tmp_path / "databases" / "backups"
    assert not backups_dir.exists()
    assert source.exists()


def test_import_allergens_persists_rows_and_archives_source(
    tmp_path, memory_datastore: DataStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Successful imports should persist rows and archive the source file."""

    ds = memory_datastore

    payload = [
        {
            "id": 1,
            "nome": "  Leite  ",
            "nome_ingles": "  Milk  ",
            "descricao": "  Rico em cálcio  ",
            "exemplos": [
                {"produto": "Queijo", "origem": "Leite de vaca"},
                "Iogurte",
            ],
            "notas": "  Observação  ",
        },
        {
            "id": 2,
            "nome": "Ovos",
            "nome_ingles": "Eggs",
            "descricao": "",
            "exemplos": None,
            "notas": None,
        },
    ]
    original_text = json.dumps(payload, ensure_ascii=False)
    source = tmp_path / "allergens.json"
    source.write_text(original_text, encoding="utf-8")

    monkeypatch.setattr(allergen_service, "get_project_root", lambda: tmp_path)

    allergen_service.import_allergens(source, ds.conn)

    cur = ds.conn.cursor()
    cur.execute(
        "SELECT Id, Nome, NomeIngles, Descricao, Exemplos, Notas "
        "FROM Alergenios ORDER BY Id"
    )
    rows = [
        (
            row["Id"],
            row["Nome"],
            row["NomeIngles"],
            row["Descricao"],
            row["Exemplos"],
            row["Notas"],
        )
        for row in cur.fetchall()
    ]

    assert rows == [
        (
            1,
            "Leite",
            "Milk",
            "Rico em cálcio",
            json.dumps(payload[0]["exemplos"], ensure_ascii=False),
            "Observação",
        ),
        (2, "Ovos", "Eggs", None, None, None),
    ]

    backups_dir = tmp_path / "databases" / "backups"
    files = list(backups_dir.iterdir())
    assert len(files) == 1
    archived = files[0]
    assert re.fullmatch(r"allergens\.[0-9]{14}\.json", archived.name)
    assert archived.read_text(encoding="utf-8") == original_text
    assert not source.exists()
