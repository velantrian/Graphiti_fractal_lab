"""Kùzu stub — HISTORICAL / NOT VALIDATED in this lab."""

from __future__ import annotations

from fractal_lab.backends.base import BackendInfo, ValidationStatus


class KuzuStub:
    """Placeholder for optional Kùzu experiments.

    Kùzu is the archived predecessor lineage of LadybugDB.
    Do not treat this stub as a working driver.
    """

    def info(self) -> BackendInfo:
        return BackendInfo(
            name="kuzu",
            role="historical embedded graph (optional)",
            status=ValidationStatus.STUB_NOT_VALIDATED,
            notes="Package not required; HISTORICAL — prefer Ladybug for new work",
        )

    def connect(self) -> None:
        raise NotImplementedError(
            "Kùzu stub only — NOT VALIDATED. Install/use ladybug for the lab path."
        )

    def close(self) -> None:
        return None

    def execute(self, query: str, parameters: dict | None = None) -> None:
        raise NotImplementedError("Kùzu stub only — NOT VALIDATED")
