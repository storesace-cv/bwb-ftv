import json
import re
import sqlite3

from data.datastore import DataStore
from services import allergens as allergen_service


def test_allergens_from_db_invalid_rows():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Alergenios")
    cur.executemany(
        "INSERT INTO Alergenios (Id, Nome, NomeIngles) VALUES (?, ?, ?)",
        [
            (1, "Good", "Good"),
            (2, "", "Empty"),
            (3, "   ", "Invalid"),
        ],
    )
    ds.conn.commit()
    assert ds._allergens_from_db() == [(1, "Good")]


def test_allergens_from_db_no_connection():
    ds = DataStore(demo=True)
    assert ds._allergens_from_db() is None


def test_import_allergens_archives_source_file(tmp_path, monkeypatch):
    payload = [
        {
            "id": 1,
            "nome": "Glúten",
            "nome_ingles": "Gluten",
            "descricao": "Presente em cereais",
            "exemplos": ["Trigo"],
            "notas": "Nenhuma",
        }
    ]
    source = tmp_path / "allergens.json"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(allergen_service, "get_project_root", lambda: tmp_path)

    conn = sqlite3.connect(":memory:")
    try:
        allergen_service.import_allergens(source, conn)
    finally:
        conn.close()

    backups_dir = tmp_path / "databases" / "backups"
    files = list(backups_dir.iterdir())
    assert len(files) == 1
    archived = files[0]
    assert re.fullmatch(r"allergens\.[0-9]{14}\.json", archived.name)
    assert archived.read_text(encoding="utf-8") == json.dumps(
        payload, ensure_ascii=False
    )
    assert not source.exists()


def test_import_allergens_can_skip_archiving(tmp_path):
    payload = [
        {
            "id": 7,
            "nome": "Soja",
            "nome_ingles": "Soy",
            "descricao": "Leguminosa",
            "exemplos": ["Tofu"],
            "notas": "",
        }
    ]

    source = tmp_path / "allergens.json"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    conn = sqlite3.connect(":memory:")
    try:
        allergen_service.import_allergens(source, conn, archive=False)
        cur = conn.cursor()
        cur.execute(
            "SELECT Nome, NomeIngles FROM Alergenios WHERE Id = ?",
            (payload[0]["id"],),
        )
        row = cur.fetchone()
        assert row == (payload[0]["nome"], payload[0]["nome_ingles"])
    finally:
        conn.close()

    backups_dir = tmp_path / "databases" / "backups"
    assert not backups_dir.exists()
    assert source.exists()
