"""Thin lab MemoryOps over Graphiti.add_episode + FalkorDBLite.

Prefer high-level ingest/update. Do not use raw EntityEdge.save as normal
semantic memory update (P6/P7).

FM-9: temporal classification is lab-layer AFTER Graphiti.search (unchanged).
FM-10: bounded provenance receipts for retrieved/inspected EntityEdges.
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
from fractal_lab.memoryops.provenance import build_edge_provenance
from fractal_lab.memoryops.receipts import (
    edge_to_dict,
    episode_to_dict,
    node_to_dict,
    utc_now_iso,
)
from fractal_lab.memoryops.temporal import classify_edge_dict, summarize_temporal


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
    query_time: str | None = None
    temporal_summary: dict[str, int] | None = None
    provenance: list[dict[str, Any]] = field(default_factory=list)

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
        llm_client: Any | None = None,
        embedder: Any | None = None,
    ) -> LabMemoryOps:
        """Open lab Graphiti stack.

        llm_client:
          - If provided, used as-is (REAL_LLM path / custom stubs).
          - Else DeterministicTemporalLLMClient when temporal=True.
          - Else DeterministicLLMClient via open_lab_graphiti default.
        embedder:
          - If provided, used as-is (FM-14 REAL semantic path).
          - Else DeterministicEmbedder via open_lab_graphiti default.
        """
        if llm_client is not None:
            llm = llm_client
        elif temporal:
            llm = DeterministicTemporalLLMClient()
        else:
            llm = None
        stack = await open_lab_graphiti(
            db_path,
            database="default_db",
            build_indices=build_indices,
            llm_client=llm,
            embedder=embedder,
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
        query_time: datetime | None = None,
        with_provenance: bool = False,
    ) -> MemoryReceipt:
        """MEMORY QUERY via Graphiti.search (group-scoped) + FM-9 temporal classify.

        Graphiti.search remains the retrieval surface unchanged.
        Classification is lab-layer AFTER retrieval against query_time.
        Historical / expired hits are NOT hidden.
        """
        gid = group_id or self.default_group_id
        # Explicit evaluation time (record even when caller omits — use current UTC)
        eval_time = query_time if query_time is not None else datetime.now(timezone.utc)
        if eval_time.tzinfo is None:
            eval_time = eval_time.replace(tzinfo=timezone.utc)
        else:
            eval_time = eval_time.astimezone(timezone.utc)
        query_time_was_explicit = query_time is not None

        edges_raw = await self.graphiti.search(
            text, group_ids=[gid], num_results=num_results
        )
        base_edges = [edge_to_dict(e) for e in edges_raw]
        classified = [classify_edge_dict(e, eval_time) for e in base_edges]
        summary = summarize_temporal([e["temporal_status"] for e in classified])

        provenance: list[dict[str, Any]] = []
        if with_provenance:
            driver = await self._group_driver(gid)
            for raw, cedge in zip(edges_raw, classified):
                # Prefer live EntityEdge objects for episode UUID list fidelity
                prov = await build_edge_provenance(driver, raw, query_text=text)
                # Align classified temporal fields onto provenance receipt
                prov["retrieved"] = True
                prov["temporal_status"] = cedge["temporal_status"]
                provenance.append(prov)

        return MemoryReceipt(
            operation="MEMORY_QUERY",
            timestamp=utc_now_iso(),
            group_id=gid,
            edges=classified,
            query=text,
            db_path=str(self.db_path),
            query_time=eval_time.isoformat(),
            temporal_summary=summary,
            provenance=provenance,
            notes={
                "hit_count": len(classified),
                "query_time_explicit": query_time_was_explicit,
                "invariant": "RETRIEVED≠CURRENT — search hits may include expired facts",
                "classification_layer": "LabMemoryOps after Graphiti.search",
                "historical_results_hidden": False,
            },
        )

    async def provenance_for_query_hits(
        self,
        text: str,
        *,
        group_id: str | None = None,
        num_results: int = 10,
        query_time: datetime | None = None,
    ) -> MemoryReceipt:
        """FM-10: query then attach bounded provenance for each retrieved edge."""
        return await self.query(
            text,
            group_id=group_id,
            num_results=num_results,
            query_time=query_time,
            with_provenance=True,
        )

    async def provenance_for_edges(
        self,
        edges: list[Any] | list[dict[str, Any]],
        *,
        group_id: str | None = None,
        query_text: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build provenance receipts for arbitrary retrieved/inspected edges."""
        gid = group_id or self.default_group_id
        driver = await self._group_driver(gid)
        out: list[dict[str, Any]] = []
        for e in edges:
            out.append(await build_edge_provenance(driver, e, query_text=query_text))
        return out

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
        with_provenance: bool = False,
    ) -> MemoryReceipt:
        """MEMORY INSPECT — episodes / entity nodes / EntityEdges with temporal metadata."""
        gid = group_id or self.default_group_id
        driver = await self._group_driver(gid)
        edges: list[dict[str, Any]] = []
        entities: list[dict[str, Any]] = []
        episodes: list[dict[str, Any]] = []
        raw_edge_objs: list[Any] = []

        if include_edges:
            try:
                raw_edges = await EntityEdge.get_by_group_ids(driver, [gid])
                raw_edge_objs = list(raw_edges or [])
                edges = [edge_to_dict(e) for e in raw_edge_objs]
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

        provenance: list[dict[str, Any]] = []
        if with_provenance and raw_edge_objs:
            for e in raw_edge_objs:
                provenance.append(await build_edge_provenance(driver, e, query_text=None))

        return MemoryReceipt(
            operation="MEMORY_INSPECT",
            timestamp=utc_now_iso(),
            group_id=gid,
            entities=entities,
            edges=edges,
            episodes=episodes,
            provenance=provenance,
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
        query_time: datetime | None = None,
        with_provenance: bool = False,
    ) -> MemoryReceipt:
        """Convenience: query labeled as REOPEN path (same process). Prefer CLI subprocess for FM-5/10C."""
        receipt = await self.query(
            text,
            group_id=group_id,
            num_results=num_results,
            query_time=query_time,
            with_provenance=with_provenance,
        )
        receipt.operation = "MEMORY_REOPEN_QUERY"
        receipt.notes["note"] = "same-process reopen helper; FM-5/10C uses subprocess"
        return receipt
