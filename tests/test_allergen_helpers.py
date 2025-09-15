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
