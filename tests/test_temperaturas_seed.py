from data.datastore import DataStore
from data.migration import get_pending_migrations


def test_temperaturas_seeded_after_setup():
    ds = DataStore(db_path=":memory:")
    try:
        assert get_pending_migrations(ds.conn) == []
        assert ds.list_temperaturas() == [(1, "Quente"), (2, "Frio")]
    finally:
        ds.close()
