"""Thin lab MemoryOps over Graphiti.add_episode + FalkorDBLite.

Prefer high-level ingest/update. Do not use raw EntityEdge.save as normal
semantic memory update (P6/P7).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodeType, EpisodicNode, EntityNode

from fractal_lab.experiments.deterministic_temporal_llm import DeterministicTemporalLLMClient
from fractal_lab.experiments.falkor_graphiti_bootstrap import LabGraphitiStack, open_lab_graphiti
from fractal_lab.memoryops.receipts import (
    edge_to_dict,
    episode_to_dict,
    node_to_dict,
    utc_now_iso,
)


@dataclass
class MemoryReceipt:
    """Structured receipt for MEMORY INGEST / QUERY / INSPECT / REOPEN."""

    operation: str
    timestamp: str
    group_id: str | None = None
    episode_uuid: str | None = None
    entities: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    episodes: list[dict[str, Any]] = field(default_factory=list)
    query: str | None = None
    db_path: str | None = None
    notes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LabMemoryOps:
    """Executable lab MemoryOps prototype (MEMORY ≠ CANON)."""

    def __init__(self, stack: LabGraphitiStack, *, default_group_id: str = "fm_default"):
        self.stack = stack
        self.default_group_id = default_group_id
        self._llm = getattr(stack.graphiti, "llm_client", None)

    @classmethod
    async def open(
        cls,
        db_path: str | Path,
        *,
        default_group_id: str = "fm_default",
        build_indices: bool = True,
        temporal: bool = True,
    ) -> LabMemoryOps:
        llm = DeterministicTemporalLLMClient() if temporal else None
        stack = await open_lab_graphiti(
            db_path,
            database="default_db",
            build_indices=build_indices,
            llm_client=llm,
        )
        return cls(stack, default_group_id=default_group_id)

    @property
    def db_path(self) -> Path:
        return self.stack.db_path

    @property
    def graphiti(self):
        return self.stack.graphiti

    async def aclose(self) -> None:
        await self.stack.aclose()

    async def ingest(
        self,
        text: str,
        *,
        group_id: str | None = None,
        reference_time: datetime | None = None,
        name: str | None = None,
        source_description: str = "fractal_lab_memoryops",
    ) -> MemoryReceipt:
        """MEMORY INGEST via Graphiti.add_episode only."""
        gid = group_id or self.default_group_id
        ref = reference_time or datetime.now(timezone.utc)
        result = await self.graphiti.add_episode(
            name=name or f"fm_ingest_{utc_now_iso()}",
            episode_body=text,
            source_description=source_description,
            reference_time=ref,
            source=EpisodeType.text,
            group_id=gid,
        )
        episode_uuid = None
        episodes: list[dict[str, Any]] = []
        ep = getattr(result, "episode", None)
        if ep is not None:
            episode_uuid = getattr(ep, "uuid", None)
            episodes = [episode_to_dict(ep)]
        entities = [node_to_dict(n) for n in (getattr(result, "nodes", None) or [])]
        edges = [edge_to_dict(e) for e in (getattr(result, "edges", None) or [])]
        # Also capture invalidated edges if Graphiti returns them
        for attr in ("invalidated_edges", "deleted_edges"):
            for e in getattr(result, attr, None) or []:
                d = edge_to_dict(e)
                d["_from_result_attr"] = attr
                edges.append(d)
        return MemoryReceipt(
            operation="MEMORY_INGEST",
            timestamp=utc_now_iso(),
            group_id=gid,
            episode_uuid=str(episode_uuid) if episode_uuid else None,
            entities=entities,
            edges=edges,
            episodes=episodes,
            db_path=str(self.db_path),
            notes={
                "reference_time": ref.astimezone(timezone.utc).isoformat(),
                "text_preview": text[:240],
                "path": "graphiti.add_episode",
            },
        )

    async def query(
        self,
        text: str,
        *,
        group_id: str | None = None,
        num_results: int = 10,
    ) -> MemoryReceipt:
        """MEMORY QUERY via Graphiti.search (group-scoped)."""
        gid = group_id or self.default_group_id
        edges_raw = await self.graphiti.search(
            text, group_ids=[gid], num_results=num_results
        )
        edges = [edge_to_dict(e) for e in edges_raw]
        return MemoryReceipt(
            operation="MEMORY_QUERY",
            timestamp=utc_now_iso(),
            group_id=gid,
            edges=edges,
            query=text,
            db_path=str(self.db_path),
            notes={
                "hit_count": len(edges),
                "invariant": "RETRIEVED≠CURRENT — search hits may include expired facts",
            },
        )

    async def _group_driver(self, group_id: str):
        driver = self.stack.driver
        if group_id != getattr(driver, "_database", None):
            driver = driver.clone(database=group_id)
        return driver

    async def inspect(
        self,
        *,
        group_id: str | None = None,
        include_episodes: bool = True,
        include_entities: bool = True,
        include_edges: bool = True,
    ) -> MemoryReceipt:
        """MEMORY INSPECT — episodes / entity nodes / EntityEdges with temporal metadata."""
        gid = group_id or self.default_group_id
        driver = await self._group_driver(gid)
        edges: list[dict[str, Any]] = []
        entities: list[dict[str, Any]] = []
        episodes: list[dict[str, Any]] = []

        if include_edges:
            try:
                raw_edges = await EntityEdge.get_by_group_ids(driver, [gid])
                edges = [edge_to_dict(e) for e in raw_edges]
            except Exception as exc:  # noqa: BLE001 — record honestly
                edges = [{"error": type(exc).__name__, "detail": str(exc)}]

        if include_entities:
            try:
                raw_nodes = await EntityNode.get_by_group_ids(driver, [gid])
                entities = [node_to_dict(n) for n in raw_nodes]
            except Exception as exc:  # noqa: BLE001
                entities = [{"error": type(exc).__name__, "detail": str(exc)}]

        if include_episodes:
            try:
                raw_eps = await EpisodicNode.get_by_group_ids(driver, [gid])
                episodes = [episode_to_dict(e) for e in raw_eps]
            except Exception as exc:  # noqa: BLE001
                episodes = [{"error": type(exc).__name__, "detail": str(exc)}]

        return MemoryReceipt(
            operation="MEMORY_INSPECT",
            timestamp=utc_now_iso(),
            group_id=gid,
            entities=entities,
            edges=edges,
            episodes=episodes,
            db_path=str(self.db_path),
            notes={
                "driver_database": getattr(driver, "_database", None),
                "invariant": "STORED≠CURRENT; inspect dumps stored graph state",
            },
        )

    async def reopen_query(
        self,
        text: str,
        *,
        group_id: str | None = None,
        num_results: int = 10,
    ) -> MemoryReceipt:
        """Convenience: query labeled as REOPEN path (same process). Prefer CLI subprocess for FM-5."""
        receipt = await self.query(text, group_id=group_id, num_results=num_results)
        receipt.operation = "MEMORY_REOPEN_QUERY"
        receipt.notes["note"] = "same-process reopen helper; FM-5 uses subprocess"
        return receipt
