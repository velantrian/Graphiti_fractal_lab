"""LadybugDB on-disk smoke — primary runnable path without Docker/Neo4j."""

from __future__ import annotations

from pathlib import Path

import pytest

from fractal_lab.backends.base import ValidationStatus
from fractal_lab.backends.ladybug_adapter import LadybugAdapter


def test_ladybug_info_status_is_path_level_declaration():
    """Status is a ledger claim for the adapter path, not a live connect probe."""
    adapter = LadybugAdapter(Path("data/unused.lbdb"))
    info = adapter.info()
    assert info.name == "ladybug"
    assert info.status == ValidationStatus.SMOKE_TESTED
    assert "Path-level" in info.notes
    assert "NOT VALIDATED" in info.notes


def test_ladybug_create_write_read(tmp_path: Path):
    db_path = tmp_path / "lab_smoke.lbdb"
    with LadybugAdapter(db_path) as adapter:
        rows = adapter.smoke_write_read()
        assert rows == [["Ada", "Bob", 2020]]
    assert db_path.exists()


def test_ladybug_reopen_reads_prior_smoke_rows(tmp_path: Path):
    db_path = tmp_path / "lab_reopen.lbdb"
    with LadybugAdapter(db_path) as writer:
        assert writer.smoke_write_read() == [["Ada", "Bob", 2020]]

    with LadybugAdapter(db_path) as reader:
        rows = reader.execute(
            "MATCH (a:LabPerson)-[k:LabKnows]->(b:LabPerson) "
            "RETURN a.name, b.name, k.since ORDER BY a.name"
        )
        assert [list(row) for row in rows] == [["Ada", "Bob", 2020]]


def test_ladybug_schema_is_idempotent_and_rejects_bad_ddl(tmp_path: Path):
    with LadybugAdapter(tmp_path / "schema.lbdb") as adapter:
        adapter.ensure_smoke_schema()
        adapter.ensure_smoke_schema()
        with pytest.raises(RuntimeError, match="(?i)parser|mismatch|exception"):
            adapter.execute("CREATE NODE TABLE TotallyBroken(")


def test_ladybug_rejects_parameters(tmp_path: Path):
    with LadybugAdapter(tmp_path / "params.lbdb") as adapter:
        with pytest.raises(NotImplementedError, match="Parameterized"):
            adapter.execute("RETURN 1", {"x": 1})


def test_stubs_declare_not_validated_and_refuse_connect():
    from fractal_lab.backends.duckdb_stub import DuckDBStub
    from fractal_lab.backends.kuzu_stub import KuzuStub
    from fractal_lab.backends.postgres_stub import PostgresStub

    for stub in (KuzuStub(), PostgresStub(), DuckDBStub()):
        assert stub.info().status == ValidationStatus.STUB_NOT_VALIDATED
        with pytest.raises(NotImplementedError, match="NOT VALIDATED"):
            stub.connect()
        with pytest.raises(NotImplementedError, match="NOT VALIDATED"):
            stub.execute("RETURN 1")
