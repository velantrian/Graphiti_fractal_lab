"""FM-9 temporal classification on retrieved EntityEdges (lab layer AFTER search).

Does NOT change Graphiti.search. Classification is metadata-only against query_time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

TEMPORALLY_CURRENT = "TEMPORALLY_CURRENT"
TEMPORALLY_EXPIRED = "TEMPORALLY_EXPIRED"
TEMPORALLY_NOT_YET_VALID = "TEMPORALLY_NOT_YET_VALID"
TEMPORAL_UNKNOWN = "TEMPORAL_UNKNOWN"


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def parse_dt(value: datetime | str | None) -> datetime | None:
    """Parse datetime or ISO string; None stays None. Never invents."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return _as_utc(value)
    s = str(value).strip()
    if not s or s.upper() == "UNKNOWN":
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    return _as_utc(dt)


def classify_temporal_status(
    *,
    valid_at: datetime | str | None,
    invalid_at: datetime | str | None,
    query_time: datetime,
) -> str:
    """Classify edge applicability at query_time from metadata only.

    Rules (FM-9):
    - TEMPORALLY_CURRENT: valid_at <= query_time AND (invalid_at is None OR invalid_at > query_time)
    - TEMPORALLY_EXPIRED: invalid_at is not None AND invalid_at <= query_time
    - TEMPORALLY_NOT_YET_VALID: valid_at is not None AND valid_at > query_time
    - TEMPORAL_UNKNOWN: insufficient metadata
    """
    qt = _as_utc(query_time)
    if qt is None:
        return TEMPORAL_UNKNOWN
    va = parse_dt(valid_at)
    ia = parse_dt(invalid_at)

    if va is not None and va <= qt and (ia is None or ia > qt):
        return TEMPORALLY_CURRENT
    if ia is not None and ia <= qt:
        return TEMPORALLY_EXPIRED
    if va is not None and va > qt:
        return TEMPORALLY_NOT_YET_VALID
    return TEMPORAL_UNKNOWN


def summarize_temporal(statuses: list[str]) -> dict[str, int]:
    return {
        "retrieved_count": len(statuses),
        "current_count": sum(1 for s in statuses if s == TEMPORALLY_CURRENT),
        "expired_count": sum(1 for s in statuses if s == TEMPORALLY_EXPIRED),
        "not_yet_valid_count": sum(1 for s in statuses if s == TEMPORALLY_NOT_YET_VALID),
        "unknown_count": sum(1 for s in statuses if s == TEMPORAL_UNKNOWN),
    }


def classify_edge_dict(edge: dict[str, Any], query_time: datetime) -> dict[str, Any]:
    """Attach retrieved + temporal_status to an edge receipt dict (non-mutating copy)."""
    status = classify_temporal_status(
        valid_at=edge.get("valid_at"),
        invalid_at=edge.get("invalid_at"),
        query_time=query_time,
    )
    return {
        "uuid": edge.get("uuid"),
        "fact": edge.get("fact"),
        "group_id": edge.get("group_id"),
        "retrieved": True,
        "temporal_status": status,
        "valid_at": edge.get("valid_at"),
        "invalid_at": edge.get("invalid_at"),
        "expired_at": edge.get("expired_at"),
        # Keep extra provenance-friendly fields when present (not required by FM-9 response)
        "name": edge.get("name"),
        "source_node_uuid": edge.get("source_node_uuid"),
        "target_node_uuid": edge.get("target_node_uuid"),
        "episodes": edge.get("episodes") or [],
    }
