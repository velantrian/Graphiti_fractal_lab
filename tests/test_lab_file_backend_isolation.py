"""File backends: smoke/test paths never modify a pre-existing (user) database file.

Ladybug rewrites a database file even when it is only opened for reading, so
the disposable smoke mode refuses *before* opening an existing path, and the
destructive smoke helpers refuse on any adapter that did not create its file.
"""
from __future__ import annotations

import gc
import hashlib
from pathlib import Path

import pytest

from fractal_lab.backends.ladybug_adapter import LadybugAdapter

CONTROL_DDL = "CREATE NODE TABLE LabPerson(name STRING PRIMARY KEY, age INT64)"


def _fingerprint(directory: Path) -> dict[str, str]:
    return {
        entry.name: hashlib.sha256(entry.read_bytes()).hexdigest()
        for entry in sorted(directory.iterdir())
        if entry.is_file()
    }


def _user_database(path: Path) -> None:
    """A pre-existing user file with a control row, written through the normal API."""
    adapter = LadybugAdapter(path)
    adapter.connect()
    adapter.execute(CONTROL_DDL)
    adapter.execute("CREATE (:LabPerson {name: 'user-control', age: 1})")
    adapter.close()
    del adapter
    gc.collect()


def test_disposable_mode_refuses_existing_file_before_opening_it(tmp_path: Path):
    path = tmp_path / "user.lbdb"
    _user_database(path)
    before = _fingerprint(tmp_path)

    with pytest.raises(FileExistsError, match="refusing to open existing"):
        LadybugAdapter(path, disposable=True).connect()
    gc.collect()

    assert _fingerprint(tmp_path) == before  # not a single byte changed


def test_disposable_mode_also_refuses_a_leftover_sidecar(tmp_path: Path):
    (tmp_path / "fresh.lbdb.wal").write_bytes(b"leftover")
    with pytest.raises(FileExistsError):
        LadybugAdapter(tmp_path / "fresh.lbdb", disposable=True).connect()
    assert not (tmp_path / "fresh.lbdb").exists()


def test_smoke_helpers_refuse_a_file_the_adapter_did_not_create(tmp_path: Path):
    path = tmp_path / "user.lbdb"
    _user_database(path)
    adapter = LadybugAdapter(path)
    adapter.connect()
    try:
        with pytest.raises(PermissionError, match="refusing to modify"):
            adapter.smoke_write_read()
        with pytest.raises(PermissionError, match="refusing to modify"):
            adapter.ensure_smoke_schema()
        rows = [list(row) for row in adapter.execute("MATCH (p:LabPerson) RETURN p.name")]
        assert rows == [["user-control"]]
    finally:
        adapter.close()


def test_disposable_adapter_may_reconnect_to_the_file_it_created(tmp_path: Path):
    adapter = LadybugAdapter(tmp_path / "own.lbdb", disposable=True)
    adapter.connect()
    assert adapter.smoke_write_read() == [["Ada", "Bob", 2020]]
    adapter.close()
    adapter.connect()  # same owner: allowed
    try:
        assert adapter.smoke_write_read() == [["Ada", "Bob", 2020]]
    finally:
        adapter.close()
