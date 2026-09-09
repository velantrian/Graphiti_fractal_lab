"""PostgreSQL stub — NOT VALIDATED (relational metadata candidate only)."""

from __future__ import annotations

from fractal_lab.backends.base import BackendInfo, ValidationStatus


class PostgresStub:
    """Placeholder for optional Postgres metadata experiments."""

    def info(self) -> BackendInfo:
        return BackendInfo(
            name="postgres",
            role="optional relational metadata",
            status=ValidationStatus.STUB_NOT_VALIDATED,
            notes="Not a Fractal graph authority; stub only",
        )

    def connect(self) -> None:
        raise NotImplementedError("PostgreSQL stub only — NOT VALIDATED")

    def close(self) -> None:
        return None

    def execute(self, query: str, parameters: dict | None = None) -> None:
        raise NotImplementedError("PostgreSQL stub only — NOT VALIDATED")
