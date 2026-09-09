"""SQLite lab metadata store — ops/metadata only, not a graph authority."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fractal_lab.backends.base import BackendInfo, ValidationStatus


class SqliteLabMeta:
    """stdlib sqlite3 helper for lab run metadata."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._conn: sqlite3.Connection | None = None

    def info(self) -> BackendInfo:
        return BackendInfo(
            name="sqlite",
            role="lab ops/metadata (not graph authority)",
            status=ValidationStatus.SMOKE_TESTED,
            notes="stdlib sqlite3; no Neo4j/Graphiti claims",
        )

    def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("SqliteLabMeta is not connected; call connect() first")
        return self._conn

    def ensure_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lab_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backend TEXT NOT NULL,
                status TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        self.conn.commit()

    def record_run(self, backend: str, status: str, note: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO lab_runs (backend, status, note) VALUES (?, ?, ?)",
            (backend, status, note),
        )
        self.conn.commit()
        assert cur.lastrowid is not None
        return int(cur.lastrowid)

    def list_runs(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT id, backend, status, note, created_at FROM lab_runs ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
