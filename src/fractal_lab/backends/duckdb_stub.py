"""DuckDB stub — NOT VALIDATED (analytical candidate only)."""

from __future__ import annotations

from fractal_lab.backends.base import BackendInfo, ValidationStatus


class DuckDBStub:
    """Placeholder for optional DuckDB analytical experiments."""

    def info(self) -> BackendInfo:
        return BackendInfo(
            name="duckdb",
            role="optional analytical store",
            status=ValidationStatus.STUB_NOT_VALIDATED,
            notes="Not a Fractal graph authority; stub only",
        )

    def connect(self) -> None:
        raise NotImplementedError("DuckDB stub only — NOT VALIDATED")

    def close(self) -> None:
        return None

    def execute(self, query: str, parameters: dict | None = None) -> None:
        raise NotImplementedError("DuckDB stub only — NOT VALIDATED")
