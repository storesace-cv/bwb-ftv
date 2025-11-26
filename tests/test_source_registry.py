import sqlite3

import pytest

from data.migration import setup_database
from data.source_registry import SourceRegistry


@pytest.fixture()
def conn():
    connection = sqlite3.connect(":memory:")
    setup_database(connection)
    yield connection
    connection.close()


def test_add_source_normalises_and_prevents_duplicates(conn):
    registry = SourceRegistry(conn)
    source = registry.add_source("Teste", "example.com/api", country_code="pt", active=False)
    assert source.base_url == "https://example.com/api"
    assert source.country_code == "PT"
    assert source.active is False

    with pytest.raises(ValueError):
        registry.add_source("Duplicado", "https://example.com/api")


def test_update_and_toggle_active(conn):
    registry = SourceRegistry(conn)
    original = registry.list_sources()[0]
    updated = registry.update_source(original.id, name="Novo Nome", active=False)
    assert updated.name == "Novo Nome"
    assert updated.active is False

    toggled = registry.set_active(updated.id, True)
    assert toggled.active is True


def test_delete_source_is_idempotent(conn):
    registry = SourceRegistry(conn)
    new_source = registry.add_source("Extra", "https://extra.example/api", active=True)
    assert new_source in registry.list_sources()
    registry.delete_source(new_source.id)
    assert all(src.id != new_source.id for src in registry.list_sources())
    # deleting again should not raise
    registry.delete_source(new_source.id)
