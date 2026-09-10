"""Receipt helpers for lab MemoryOps (FM-8)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def dt_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def edge_to_dict(edge: Any) -> dict[str, Any]:
    episodes = getattr(edge, "episodes", None) or getattr(edge, "episode_ids", None) or []
    if episodes and hasattr(episodes[0], "uuid"):
        episode_uuids = [str(e.uuid) for e in episodes]
    else:
        episode_uuids = [str(x) for x in episodes] if episodes else []
    return {
        "uuid": getattr(edge, "uuid", None),
        "name": getattr(edge, "name", None),
        "fact": getattr(edge, "fact", None),
        "group_id": getattr(edge, "group_id", None),
        "source_node_uuid": getattr(edge, "source_node_uuid", None),
        "target_node_uuid": getattr(edge, "target_node_uuid", None),
        "valid_at": dt_iso(getattr(edge, "valid_at", None)),
        "invalid_at": dt_iso(getattr(edge, "invalid_at", None)),
        "expired_at": dt_iso(getattr(edge, "expired_at", None)),
        "created_at": dt_iso(getattr(edge, "created_at", None)),
        "episodes": episode_uuids,
    }


def node_to_dict(node: Any) -> dict[str, Any]:
    return {
        "uuid": getattr(node, "uuid", None),
        "name": getattr(node, "name", None),
        "summary": getattr(node, "summary", None),
        "group_id": getattr(node, "group_id", None),
        "created_at": dt_iso(getattr(node, "created_at", None)),
    }


def episode_to_dict(ep: Any) -> dict[str, Any]:
    return {
        "uuid": getattr(ep, "uuid", None),
        "name": getattr(ep, "name", None),
        "content": (getattr(ep, "content", None) or "")[:2000],
        "source_description": getattr(ep, "source_description", None),
        "group_id": getattr(ep, "group_id", None),
        "valid_at": dt_iso(getattr(ep, "valid_at", None)),
        "created_at": dt_iso(getattr(ep, "created_at", None)),
    }
