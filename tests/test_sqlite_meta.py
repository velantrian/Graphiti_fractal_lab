"""SQLite lab metadata smoke."""

from __future__ import annotations

from pathlib import Path

from fractal_lab.backends.base import ValidationStatus
from fractal_lab.backends.sqlite_meta import SqliteLabMeta


def test_sqlite_meta_roundtrip(tmp_path: Path):
    meta = SqliteLabMeta(tmp_path / "lab_meta.sqlite")
    meta.connect()
    try:
        assert meta.info().status == ValidationStatus.SMOKE_TESTED
        meta.ensure_schema()
        run_id = meta.record_run("ladybug", "pass", note="smoke")
        assert run_id >= 1
        runs = meta.list_runs()
        assert len(runs) == 1
        assert runs[0]["backend"] == "ladybug"
        assert runs[0]["status"] == "pass"
        assert runs[0]["note"] == "smoke"
    finally:
        meta.close()
