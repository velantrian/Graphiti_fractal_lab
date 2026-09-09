"""Shared protocols for lab graph/metadata backends."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class ValidationStatus(str, Enum):
    """Honest status — do not promote stubs to VALIDATED without evidence."""

    SMOKE_TESTED = "smoke_tested"
    STUB_NOT_VALIDATED = "stub_not_validated"
    NOT_CLAIMED = "not_claimed"


@dataclass(frozen=True)
class BackendInfo:
    name: str
    role: str
    status: ValidationStatus
    notes: str = ""


@runtime_checkable
class GraphBackend(Protocol):
    """Minimal graph surface used by lab smoke tests."""

    def info(self) -> BackendInfo: ...

    def connect(self) -> None: ...

    def close(self) -> None: ...

    def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any: ...
