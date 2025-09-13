def test_validade_seeded_on_empty_db():
    from data.datastore import DataStore

    ds = DataStore(db_path=":memory:")
    try:
        assert ds.list_validade()[1:] == [(1, "24h"), (2, "48h")]
    finally:
        ds.close()
