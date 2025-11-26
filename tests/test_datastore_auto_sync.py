import pytest

from data.datastore import DataStore


@pytest.fixture()
def store():
    ds = DataStore(db_path=":memory:")
    yield ds
    if ds.conn is not None:
        ds.conn.close()


def test_auto_sync_default_true(store):
    assert store.auto_sync_enabled() is True


def test_toggle_auto_sync(store):
    store.set_auto_sync_enabled(False)
    assert store.auto_sync_enabled() is False
    store.set_auto_sync_enabled(True)
    assert store.auto_sync_enabled() is True


def test_register_and_remove_ingestion_source(store):
    initial = store.get_ingestion_sources()
    assert initial  # default seeds exist
    new = store.register_ingestion_source(
        "Fonte Teste", "https://sync.example/api", country_code="es", active=False
    )
    assert new in store.get_ingestion_sources()
    store.set_ingestion_source_active(new.id, True)
    refreshed = [src for src in store.get_ingestion_sources() if src.id == new.id][0]
    assert refreshed.active is True
    store.delete_ingestion_source(new.id)
    assert all(src.id != new.id for src in store.get_ingestion_sources())
