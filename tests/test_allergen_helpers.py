import json
from data.datastore import DataStore


def test_allergens_from_db_invalid_rows():
    ds = DataStore(db_path=":memory:")
    cur = ds.conn.cursor()
    cur.execute("DELETE FROM Alergenios")
    cur.executemany(
        "INSERT INTO Alergenios (Id, Nome, Ativo) VALUES (?, ?, ?)",
        [
            (1, "Good", 1),
            (2, "", 1),
            (3, "Inactive", 0),
        ],
    )
    ds.conn.commit()
    assert ds._allergens_from_db() == [(1, "Good")]


def test_allergens_from_db_no_connection():
    ds = DataStore(demo=True)
    assert ds._allergens_from_db() is None


def test_allergens_from_json_missing():
    ds = DataStore(db_path=":memory:")
    assert ds._allergens_from_json() is None


def test_allergens_from_json_invalid():
    ds = DataStore(db_path=":memory:")
    ds.conn.execute("INSERT INTO Config (Key, Value) VALUES ('allergens', '{bad json')")
    ds.conn.commit()
    assert ds._allergens_from_json() is None


def test_allergens_from_json_filters_invalid():
    ds = DataStore(db_path=":memory:")
    data = {"alergenios": ["A", {"nome": "", "id": 2}, {"id": "x", "nome": "B"}]}
    ds.conn.execute(
        "INSERT INTO Config (Key, Value) VALUES (?, ?)",
        ("allergens", json.dumps(data)),
    )
    ds.conn.commit()
    assert ds._allergens_from_json() == [(1, "A"), (2, "B")]


def test_default_allergens():
    ds = DataStore(demo=True)
    items = ds._default_allergens()
    assert len(items) == 14
    assert items[0] == (1, "Glúten")
