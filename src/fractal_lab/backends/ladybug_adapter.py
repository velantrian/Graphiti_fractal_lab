"""LadybugDB adapter — primary runnable lab path (smoke-tested, not Graphiti parity)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import ladybug as lb

from fractal_lab.backends.base import BackendInfo, ValidationStatus


class LadybugAdapter:
    """Thin wrapper around ladybug.Database / Connection.

    Does **not** claim graphiti_core compatibility or Neo4j parity.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._db: lb.Database | None = None
        self._conn: lb.Connection | None = None

    def info(self) -> BackendInfo:
        return BackendInfo(
            name="ladybug",
            role="primary on-disk property graph (lab)",
            status=ValidationStatus.SMOKE_TESTED,
            notes="Cypher node/rel round-trip only; Graphiti parity NOT VALIDATED",
        )

    def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = lb.Database(str(self.path))
        self._conn = lb.Connection(self._db)

    def close(self) -> None:
        # Ladybug Connection/Database close via GC; clear refs for tests.
        self._conn = None
        self._db = None

    @property
    def conn(self) -> lb.Connection:
        if self._conn is None:
            raise RuntimeError("LadybugAdapter is not connected; call connect() first")
        return self._conn

    def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        if parameters:
            # Ladybug prepared params vary by version; smoke path uses literal Cypher.
            raise NotImplementedError(
                "Parameterized queries not used in lab smoke; embed literals carefully"
            )
        return self.conn.execute(query)

    def ensure_smoke_schema(self) -> None:
        """Idempotent-ish schema for Person/Knows smoke (CREATE may fail if exists)."""
        try:
            self.execute(
                "CREATE NODE TABLE LabPerson(name STRING PRIMARY KEY, age INT64)"
            )
        except Exception:
            pass
        try:
            self.execute(
                "CREATE REL TABLE LabKnows(FROM LabPerson TO LabPerson, since INT64)"
            )
        except Exception:
            pass

    def smoke_write_read(self) -> list[list[Any]]:
        """Write two nodes + one rel; return MATCH rows."""
        self.ensure_smoke_schema()
        # Clear prior smoke rows if re-running on same file
        try:
            self.execute("MATCH (a:LabPerson)-[r:LabKnows]->(b:LabPerson) DELETE r")
            self.execute("MATCH (p:LabPerson) DELETE p")
        except Exception:
            pass
        self.execute(
            "CREATE (a:LabPerson {name: 'Ada', age: 36}), "
            "(b:LabPerson {name: 'Bob', age: 40}), "
            "(a)-[:LabKnows {since: 2020}]->(b)"
        )
        result = self.execute(
            "MATCH (a:LabPerson)-[k:LabKnows]->(b:LabPerson) "
            "RETURN a.name, b.name, k.since ORDER BY a.name"
        )
        return [list(row) for row in result]
