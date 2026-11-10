"""SQLite lab metadata smoke."""

from __future__ import annotations

from pathlib import Path

from fractal_lab.backends.base import ValidationStatus
from fractal_lab.backends.sqlite_meta import SqliteLabMeta


def test_sqlite_meta_roundtrip(tmp_path: Path):
    db_path = tmp_path / "lab_meta.sqlite"
    with SqliteLabMeta(db_path) as meta:
        assert meta.info().status == ValidationStatus.SMOKE_TESTED
        assert "Path-level" in meta.info().notes
        meta.ensure_schema()
        run_id = meta.record_run("ladybug", "pass", note="smoke")
        assert run_id >= 1
        runs = meta.list_runs()
        assert len(runs) == 1
        assert runs[0]["backend"] == "ladybug"
        assert runs[0]["status"] == "pass"
        assert runs[0]["note"] == "smoke"
    assert db_path.exists()


def test_sqlite_meta_reopen_preserves_runs(tmp_path: Path):
    db_path = tmp_path / "lab_meta_reopen.sqlite"
    with SqliteLabMeta(db_path) as writer:
        writer.ensure_schema()
        writer.record_run("ladybug", "pass", note="first")

    with SqliteLabMeta(db_path) as reader:
        runs = reader.list_runs()
        assert len(runs) == 1
        assert runs[0]["note"] == "first"
