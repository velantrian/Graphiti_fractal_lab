"""FM-10 bounded provenance receipts for EntityEdges (lab layer).

Chain: INPUT → EPISODE → ENTITY EDGE → QUERY HIT.
Unavailable fields = UNKNOWN — never invent.
Show all recorded episode UUIDs; do not pick one artificially.
"""

from __future__ import annotations

from typing import Any

from fractal_lab.memoryops.receipts import dt_iso, episode_to_dict

UNKNOWN = "UNKNOWN"


def _unk(value: Any) -> Any:
    if value is None:
        return UNKNOWN
    if isinstance(value, str) and not value.strip():
        return UNKNOWN
    return value


def edge_provenance_skeleton(edge: Any | dict[str, Any]) -> dict[str, Any]:
    """Bounded edge provenance fields from an EntityEdge or edge dict."""
    if isinstance(edge, dict):
        get = edge.get
        episodes = get("episodes") or []
    else:
        get = lambda k, default=None: getattr(edge, k, default)  # noqa: E731
        raw_eps = getattr(edge, "episodes", None) or []
        if raw_eps and hasattr(raw_eps[0], "uuid"):
            episodes = [str(e.uuid) for e in raw_eps]
        else:
            episodes = [str(x) for x in raw_eps] if raw_eps else []

    valid_at = get("valid_at")
    invalid_at = get("invalid_at")
    expired_at = get("expired_at")
    # dict edges already ISO-stringed via edge_to_dict
    if not isinstance(edge, dict):
        valid_at = dt_iso(valid_at)
        invalid_at = dt_iso(invalid_at)
        expired_at = dt_iso(expired_at)

    return {
        "edge_uuid": _unk(get("uuid")),
        "fact": _unk(get("fact")),
        "relation": _unk(get("name")),
        "name": _unk(get("name")),
        "group_id": _unk(get("group_id")),
        "source_node_uuid": _unk(get("source_node_uuid")),
        "target_node_uuid": _unk(get("target_node_uuid")),
        "valid_at": _unk(valid_at),
        "invalid_at": _unk(invalid_at),
        "expired_at": _unk(expired_at),
        "episode_uuids": list(episodes) if episodes else [],
        "chain": ["INPUT", "EPISODE", "ENTITY_EDGE", "QUERY_HIT"],
    }


async def load_episode_provenance(driver: Any, episode_uuids: list[str]) -> list[dict[str, Any]]:
    """Load episode nodes when API/driver can; else UNKNOWN stubs. Never invents content."""
    from graphiti_core.nodes import EpisodicNode

    out: list[dict[str, Any]] = []
    if not episode_uuids:
        return out

    loaded_by_uuid: dict[str, Any] = {}
    # Prefer batch API when available
    try:
        nodes = await EpisodicNode.get_by_uuids(driver, list(episode_uuids))
        for n in nodes or []:
            loaded_by_uuid[str(n.uuid)] = n
    except Exception:
        for eu in episode_uuids:
            try:
                n = await EpisodicNode.get_by_uuid(driver, eu)
                if n is not None:
                    loaded_by_uuid[str(n.uuid)] = n
            except Exception:
                continue

    for eu in episode_uuids:
        node = loaded_by_uuid.get(str(eu))
        if node is None:
            out.append(
                {
                    "episode_uuid": str(eu),
                    "episode_name": UNKNOWN,
                    "content_preview": UNKNOWN,
                    "source_description": UNKNOWN,
                    "group_id": UNKNOWN,
                    "valid_at": UNKNOWN,
                    "reference_time": UNKNOWN,
                    "created_at": UNKNOWN,
                    "load_status": "UNAVAILABLE",
                }
            )
            continue
        d = episode_to_dict(node)
        content = d.get("content") or ""
        preview = content[:500] if content else UNKNOWN
        # EpisodicNode has valid_at; reference_time may be absent → UNKNOWN
        ref = dt_iso(getattr(node, "reference_time", None))
        out.append(
            {
                "episode_uuid": _unk(d.get("uuid")),
                "episode_name": _unk(d.get("name")),
                "content_preview": preview if preview else UNKNOWN,
                "source_description": _unk(d.get("source_description")),
                "group_id": _unk(d.get("group_id")),
                "valid_at": _unk(d.get("valid_at")),
                "reference_time": _unk(ref),
                "created_at": _unk(d.get("created_at")),
                "load_status": "LOADED",
            }
        )
    return out


async def build_edge_provenance(
    driver: Any,
    edge: Any | dict[str, Any],
    *,
    query_text: str | None = None,
) -> dict[str, Any]:
    """Full bounded provenance receipt for one retrieved/inspected edge."""
    base = edge_provenance_skeleton(edge)
    episodes = await load_episode_provenance(driver, list(base["episode_uuids"]))
    return {
        **base,
        "episodes": episodes,
        "query_text": query_text if query_text is not None else UNKNOWN,
        "input_preview": (query_text[:240] if query_text else UNKNOWN),
    }
