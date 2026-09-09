"""LadybugDB on-disk smoke — primary runnable path without Docker/Neo4j."""

from __future__ import annotations

from pathlib import Path

from fractal_lab.backends.base import ValidationStatus
from fractal_lab.backends.ladybug_adapter import LadybugAdapter


def test_ladybug_info_status():
    adapter = LadybugAdapter(Path("data/unused.lbdb"))
    info = adapter.info()
    assert info.name == "ladybug"
    assert info.status == ValidationStatus.SMOKE_TESTED


def test_ladybug_create_write_read(tmp_path: Path):
    db_path = tmp_path / "lab_smoke.lbdb"
    adapter = LadybugAdapter(db_path)
    adapter.connect()
    try:
        rows = adapter.smoke_write_read()
        assert rows == [["Ada", "Bob", 2020]]
        assert db_path.exists() or db_path.is_dir() or any(tmp_path.iterdir())
    finally:
        adapter.close()


def test_stubs_declare_not_validated():
    from fractal_lab.backends.duckdb_stub import DuckDBStub
    from fractal_lab.backends.kuzu_stub import KuzuStub
    from fractal_lab.backends.postgres_stub import PostgresStub

    for stub in (KuzuStub(), PostgresStub(), DuckDBStub()):
        assert stub.info().status == ValidationStatus.STUB_NOT_VALIDATED
