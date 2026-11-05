"""LadybugDB adapter — primary runnable lab path (smoke-tested, not Graphiti parity)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import ladybug as lb

from fractal_lab.backends.base import BackendInfo, ValidationStatus


def _is_catalog_already_exists(exc: BaseException) -> bool:
    """Ladybug raises RuntimeError when CREATE NODE/REL TABLE hits an existing name."""
    if not isinstance(exc, RuntimeError):
        return False
    return "already exists" in str(exc).lower()


class LadybugAdapter:
    """Thin wrapper around ladybug.Database / Connection.

    Does **not** claim graphiti_core compatibility or Neo4j parity.

    ``info().status`` is a path-level ledger claim (backed by lab smoke tests),
    not proof that this particular instance has been exercised.
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
            notes=(
                "Path-level smoke claim only; Cypher node/rel round-trip. "
                "Graphiti parity NOT VALIDATED"
            ),
        )

    def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = lb.Database(str(self.path))
        self._conn = lb.Connection(self._db)

    def close(self) -> None:
        # Ladybug Connection/Database expose no explicit close in 0.20.3; drop refs.
        self._conn = None
        self._db = None

    def __enter__(self) -> "LadybugAdapter":
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

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
        """Create Person/Knows smoke tables; ignore only catalog-already-exists."""
        for query in (
            "CREATE NODE TABLE LabPerson(name STRING PRIMARY KEY, age INT64)",
            "CREATE REL TABLE LabKnows(FROM LabPerson TO LabPerson, since INT64)",
        ):
            try:
                self.execute(query)
            except RuntimeError as exc:
                if not _is_catalog_already_exists(exc):
                    raise

    def smoke_write_read(self) -> list[list[Any]]:
        """Write two nodes + one rel; return MATCH rows.

        Clears prior ``LabPerson`` / ``LabKnows`` rows on this database file first.
        """
        self.ensure_smoke_schema()
        self.execute("MATCH (a:LabPerson)-[r:LabKnows]->(b:LabPerson) DELETE r")
        self.execute("MATCH (p:LabPerson) DELETE p")
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
