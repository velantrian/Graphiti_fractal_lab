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

    def __init__(self, path: str | Path, *, disposable: bool = False) -> None:
        """``disposable=True`` is the smoke-test mode: the adapter may only
        create a new database file and refuses to open one that already exists.
        Smoke helpers that create tables or delete rows run only in that mode,
        so they can never touch a pre-existing (user) database file. Opening an
        existing Ladybug file rewrites it even for reads, hence the refusal
        happens before ``ladybug.Database`` is called.
        """
        self.path = Path(path)
        self.disposable = disposable
        self._owns_file = False
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

    def existing_files(self) -> list[Path]:
        """The database file and its sidecars (e.g. ``<name>.wal``) on disk."""
        if not self.path.parent.exists():
            return []
        prefix = self.path.name + "."
        return sorted(
            entry for entry in self.path.parent.iterdir()
            if entry.name == self.path.name or entry.name.startswith(prefix)
        )

    def connect(self) -> None:
        if self.disposable and not self._owns_file:
            existing = self.existing_files()
            if existing:
                raise FileExistsError(
                    "disposable Ladybug database must be a new path; refusing to open "
                    f"existing {', '.join(str(path) for path in existing)}"
                )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = lb.Database(str(self.path))
        self._conn = lb.Connection(self._db)
        if self.disposable:
            self._owns_file = True

    def _require_disposable(self, operation: str) -> None:
        if not (self.disposable and self._owns_file):
            raise PermissionError(
                f"{operation} only runs on a database this adapter created "
                "(LadybugAdapter(path, disposable=True)); refusing to modify "
                f"{self.path}"
            )

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
        # The pinned Ladybug 0.20.3 driver binds values itself. Never interpolate
        # untrusted note/source text into Cypher, including for this lab path.
        return self.conn.execute(query, parameters=parameters)

    def ensure_smoke_schema(self) -> None:
        """Create Person/Knows smoke tables; ignore only catalog-already-exists."""
        self._require_disposable("ensure_smoke_schema")
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

        Clears prior ``LabPerson`` / ``LabKnows`` rows first, so it runs only on
        a disposable database created by this adapter.
        """
        self._require_disposable("smoke_write_read")
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

