"""Tests for error handling in migration helpers."""

from __future__ import annotations

import logging
import sqlite3

import pytest

from data import migration


def test_ensure_schema_table_logs_failed_column_rename(caplog):
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE schema_version (file_name TEXT)")
        conn.commit()

        with caplog.at_level(logging.ERROR):
            table = migration._ensure_schema_table(conn)

        assert table == "SchemaVersion"
        assert any(
            "SchemaVersion" in record.getMessage() for record in caplog.records
        )
    finally:
        conn.close()


def test_seed_alergenios_raises_and_logs_on_failure(monkeypatch, caplog):
    conn = sqlite3.connect(":memory:")
    try:
        monkeypatch.setenv(migration.ALERGENIOS_SEED_FLAG, "1")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(sqlite3.Error):
                migration._seed_alergenios(conn)

        assert "Alergenios" in caplog.text
    finally:
        conn.close()


def test_seed_validade_raises_and_logs_on_failure(caplog):
    conn = sqlite3.connect(":memory:")
    try:
        with caplog.at_level(logging.ERROR):
            with pytest.raises(sqlite3.Error):
                migration._seed_validade(conn)

        assert "Validade" in caplog.text
    finally:
        conn.close()


def test_seed_temperaturas_raises_and_logs_on_failure(caplog):
    conn = sqlite3.connect(":memory:")
    try:
        with caplog.at_level(logging.ERROR):
            with pytest.raises(sqlite3.Error):
                migration._seed_temperaturas(conn)

        assert "Temperaturas" in caplog.text
    finally:
        conn.close()
