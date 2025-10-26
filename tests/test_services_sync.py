import pytest
import requests

from data.datastore import DataStore
from data.source_registry import SourceRegistry
from services.sync import OnlineSynchronizer, auto_sync_datastore


@pytest.fixture()
def store():
    ds = DataStore(db_path=":memory:")
    yield ds
    if ds.conn is not None:
        ds.conn.close()


def test_auto_sync_datastore_skips_when_disabled(store):
    store.set_auto_sync_enabled(False)

    class DummySession:
        def __init__(self):
            self.calls = []

        def get(self, url, timeout):
            self.calls.append((url, timeout))
            raise AssertionError("Should not perform HTTP requests when disabled")

    session = DummySession()
    results = auto_sync_datastore(store, session=session, timeout=1)
    assert results == []
    assert session.calls == []


def test_online_synchronizer_reports_errors(store):
    registry = SourceRegistry(store.conn)
    store.register_ingestion_source("Fonte OK", "https://ok.example/api", active=True)

    class DummySession:
        def __init__(self):
            self.calls = []

        def get(self, url, timeout):
            self.calls.append((url, timeout))
            if "continente" in url:
                raise requests.exceptions.ConnectionError("DNS failure")
            return FakeResponse(200)

    class FakeResponse:
        def __init__(self, status_code):
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(response=self)

    synchronizer = OnlineSynchronizer(registry, session=DummySession(), timeout=1)
    results = synchronizer.run()
    assert len(results) >= 2
    assert any(not r.success for r in results)
    assert any(r.success for r in results)
