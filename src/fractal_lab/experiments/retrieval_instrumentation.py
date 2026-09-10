"""Lab-only observational hooks around Graphiti 0.29.3 search (FM-13).

Behavior-preserving wrappers / monkeypatches. Do not alter retrieval semantics,
providers, prompts, num_results, filters, or MemoryOps contracts.
No permanent site-packages patches — install/uninstall around a single run.
"""

from __future__ import annotations

import hashlib
import inspect
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable

from graphiti_core.embedder.client import EMBEDDING_DIM


def _edge_brief(edge: Any) -> dict[str, Any]:
    return {
        "uuid": getattr(edge, "uuid", None),
        "name": getattr(edge, "name", None),
        "fact": getattr(edge, "fact", None),
        "group_id": getattr(edge, "group_id", None),
        "source_node_uuid": getattr(edge, "source_node_uuid", None),
        "target_node_uuid": getattr(edge, "target_node_uuid", None),
    }


def _digest_vector(
    vec: list[float] | None, *, label: str = "DETERMINISTIC_EMBEDDING"
) -> dict[str, Any]:
    if vec is None:
        return {"label": "MISSING", "dim": None, "sha256_hex": None}
    raw = ",".join(f"{x:.8f}" for x in vec).encode("utf-8")
    return {
        "label": label,
        "dim": len(vec),
        "sha256_hex": hashlib.sha256(raw).hexdigest(),
        "embedding_dim_constant": EMBEDDING_DIM,
        "l2_norm": float(sum(x * x for x in vec)) ** 0.5,
        "head8": [float(x) for x in vec[:8]],
    }


@dataclass
class QueryTraceStore:
    """Per-query observational capture."""

    query_id: str
    query: str
    embedding: dict[str, Any] = field(default_factory=dict)
    channels: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    raw_candidates: list[dict[str, Any]] = field(default_factory=list)
    fusion: dict[str, Any] = field(default_factory=dict)
    rerank: dict[str, Any] = field(default_factory=dict)
    edge_search_result: list[dict[str, Any]] = field(default_factory=list)
    edge_search_scores: list[float] = field(default_factory=list)
    graphiti_search: list[dict[str, Any]] = field(default_factory=list)
    memoryops_query: list[dict[str, Any]] = field(default_factory=list)
    memoryops_vs_graphiti: dict[str, Any] = field(default_factory=dict)
    cross_encoder_calls: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "query": self.query,
            "embedding": self.embedding,
            "channels": self.channels,
            "raw_candidates": self.raw_candidates,
            "fusion": self.fusion,
            "rerank": self.rerank,
            "edge_search_result": self.edge_search_result,
            "edge_search_scores": self.edge_search_scores,
            "graphiti_search": self.graphiti_search,
            "memoryops_query": self.memoryops_query,
            "memoryops_vs_graphiti": self.memoryops_vs_graphiti,
            "cross_encoder_calls": self.cross_encoder_calls,
            "notes": self.notes,
        }


class RetrievalInstrumenter:
    """Install temporary monkeypatches; capture channel/fusion/rerank traces."""

    def __init__(self) -> None:
        self.active: QueryTraceStore | None = None
        self.traces: dict[str, QueryTraceStore] = {}
        self._orig: dict[str, Any] = {}

    def begin(self, query_id: str, query: str) -> QueryTraceStore:
        store = QueryTraceStore(query_id=query_id, query=query)
        self.active = store
        self.traces[query_id] = store
        return store

    def end(self) -> None:
        self.active = None

    @contextmanager
    def installed(self):
        import graphiti_core.graphiti as graphiti_mod
        import graphiti_core.search.search as search_mod
        import graphiti_core.search.search_utils as search_utils

        inst = self

        # --- embedder.create via wrapping clients inside search() ---
        orig_search = search_mod.search
        orig_edge_search = search_mod.edge_search
        orig_fulltext = search_utils.edge_fulltext_search
        orig_similarity = search_utils.edge_similarity_search
        orig_bfs = search_utils.edge_bfs_search
        orig_rrf = search_utils.rrf

        async def wrapped_fulltext(*args, **kwargs):
            edges = await orig_fulltext(*args, **kwargs)
            store = inst.active
            if store is not None:
                ranked = []
                for i, e in enumerate(edges):
                    brief = _edge_brief(e)
                    brief["channel"] = "bm25"
                    brief["rank"] = i
                    brief["score"] = "NOT_EXPOSED_ON_ENTITY_EDGE"
                    ranked.append(brief)
                store.channels["bm25"] = ranked
            return edges

        async def wrapped_similarity(*args, **kwargs):
            edges = await orig_similarity(*args, **kwargs)
            store = inst.active
            if store is not None:
                min_score = kwargs.get("min_score")
                if min_score is None and len(args) >= 8:
                    min_score = args[7]
                ranked = []
                for i, e in enumerate(edges):
                    brief = _edge_brief(e)
                    brief["channel"] = "cosine_similarity"
                    brief["rank"] = i
                    brief["score"] = "NOT_EXPOSED_ON_ENTITY_EDGE"
                    brief["sim_min_score_config"] = min_score
                    ranked.append(brief)
                store.channels["cosine_similarity"] = ranked
            return edges

        async def wrapped_bfs(*args, **kwargs):
            edges = await orig_bfs(*args, **kwargs)
            store = inst.active
            if store is not None:
                ranked = []
                for i, e in enumerate(edges):
                    brief = _edge_brief(e)
                    brief["channel"] = "bfs"
                    brief["rank"] = i
                    brief["score"] = "NOT_EXPOSED_ON_ENTITY_EDGE"
                    ranked.append(brief)
                store.channels["bfs"] = ranked
            return edges

        def wrapped_rrf(results, rank_const=1, min_score: float = 0):
            uuids, scores = orig_rrf(results, rank_const=rank_const, min_score=min_score)
            store = inst.active
            if store is not None:
                channel_names = []
                # Map result lists to known channel order from EDGE_HYBRID_SEARCH_RRF:
                # tasks appended in order: bm25 then cosine_similarity (bfs only if configured)
                configured = list(store.channels.keys())
                # Prefer stable naming by matching list contents to captured channels
                named_lists = []
                used = set()
                for result in results:
                    matched = None
                    for ch_name, ch_rows in store.channels.items():
                        if ch_name in used:
                            continue
                        ch_uuids = [r["uuid"] for r in ch_rows]
                        if list(result) == ch_uuids:
                            matched = ch_name
                            break
                    if matched is None:
                        matched = f"result_set_{len(named_lists)}"
                    else:
                        used.add(matched)
                    named_lists.append({"channel": matched, "uuids": list(result)})
                    channel_names.append(matched)

                first_entry: dict[str, dict[str, Any]] = {}
                for ch_name, ch_rows in store.channels.items():
                    for row in ch_rows:
                        uid = row["uuid"]
                        if uid not in first_entry:
                            first_entry[uid] = {
                                "first_channel": ch_name,
                                "first_channel_rank": row["rank"],
                                "fact": row.get("fact"),
                                "name": row.get("name"),
                            }
                        # also record all channels
                        first_entry[uid].setdefault("channels_present", [])
                        first_entry[uid]["channels_present"].append(
                            {"channel": ch_name, "rank": row["rank"]}
                        )

                fused = []
                for i, (uid, sc) in enumerate(zip(uuids, scores)):
                    entry = {
                        "rank": i,
                        "uuid": uid,
                        "rrf_score": sc,
                        "first_entry": first_entry.get(uid),
                    }
                    fused.append(entry)

                store.fusion = {
                    "method": "reciprocal_rank_fusion",
                    "rank_const": rank_const,
                    "min_score": min_score,
                    "input_result_sets": named_lists,
                    "channel_order_observed": channel_names,
                    "fused": fused,
                    "first_entry_by_uuid": first_entry,
                }
                # Raw candidates = union in first-seen order across channels (bm25 then cosine)
                raw = []
                seen = set()
                for ch in ("bm25", "cosine_similarity", "bfs"):
                    for row in store.channels.get(ch, []):
                        if row["uuid"] in seen:
                            continue
                        seen.add(row["uuid"])
                        raw.append(
                            {
                                **row,
                                "earliest_channel": ch,
                                "earliest_rank": row["rank"],
                            }
                        )
                store.raw_candidates = raw
            return uuids, scores

        async def wrapped_edge_search(*args, **kwargs):
            # Capture cross_encoder.rank if invoked
            store = inst.active
            cross_encoder = args[1] if len(args) > 1 else kwargs.get("cross_encoder")
            orig_rank = None
            if cross_encoder is not None and hasattr(cross_encoder, "rank"):
                orig_rank = cross_encoder.rank

                async def wrapped_rank(query: str, passages: list[str]):
                    before = list(passages)
                    ranked = await orig_rank(query, passages)
                    if store is not None:
                        before_ranks = {p: i for i, p in enumerate(before)}
                        after = []
                        for new_i, (p, sc) in enumerate(ranked):
                            after.append(
                                {
                                    "rank_after": new_i,
                                    "rank_before": before_ranks.get(p),
                                    "passage": p,
                                    "score": sc,
                                }
                            )
                        # verdict
                        before_order = before
                        after_order = [p for p, _ in ranked]
                        if after_order == before_order:
                            verdict = "NEUTRAL"
                        else:
                            # crude: did top-1 change to something that was worse before?
                            verdict = "RERANK_IMPROVES_OR_CHANGES"
                            # Without gold labels here, mark CHANGES; caller may refine
                            if after_order and before_order and after_order[0] != before_order[0]:
                                verdict = "CHANGES_TOP1"
                            else:
                                verdict = "CHANGES_ORDER"
                        store.cross_encoder_calls.append(
                            {
                                "query": query,
                                "n_passages": len(passages),
                                "before_order": before_order,
                                "after": after,
                                "verdict_local": verdict,
                            }
                        )
                        store.rerank = {
                            "reranker_type": "cross_encoder",
                            "calls": store.cross_encoder_calls,
                            "cross_encoder_verdict": verdict,
                        }
                    return ranked

                cross_encoder.rank = wrapped_rank  # type: ignore[method-assign]

            try:
                edges, scores = await orig_edge_search(*args, **kwargs)
            finally:
                if orig_rank is not None and cross_encoder is not None:
                    cross_encoder.rank = orig_rank  # type: ignore[method-assign]

            if store is not None:
                store.edge_search_result = [
                    {**_edge_brief(e), "rank": i, "edge_reranker_score": scores[i] if i < len(scores) else None}
                    for i, e in enumerate(edges)
                ]
                store.edge_search_scores = list(scores)
                # If RRF path and no cross_encoder call:
                if not store.cross_encoder_calls:
                    config = args[5] if len(args) > 5 else kwargs.get("config")
                    reranker = getattr(config, "reranker", None)
                    store.rerank = {
                        "reranker_type": getattr(reranker, "value", str(reranker)),
                        "cross_encoder_calls": 0,
                        "cross_encoder_verdict": "N/A",
                        "note": (
                            "Default Graphiti.search uses EDGE_HYBRID_SEARCH_RRF; "
                            "EdgeReranker.cross_encoder is NOT invoked on this path. "
                            "Fusion RRF scores are in fusion.fused[].rrf_score."
                        ),
                        "observed_fusion_as_rerank_slot": store.fusion.get("method"),
                    }
            return edges, scores

        async def wrapped_search(clients, query, group_ids, config, search_filter, **kwargs):
            store = inst.active
            # wrap embedder.create temporarily
            embedder = clients.embedder
            orig_create = embedder.create

            async def wrapped_create(input_data):
                vec = await orig_create(input_data)
                if store is not None:
                    text = (
                        input_data
                        if isinstance(input_data, str)
                        else (
                            " ".join(input_data)
                            if isinstance(input_data, list) and input_data and isinstance(input_data[0], str)
                            else str(input_data)
                        )
                    )
                    emb_label = getattr(
                        embedder, "embedding_label", "DETERMINISTIC_EMBEDDING"
                    )
                    store.embedding = {
                        **_digest_vector(vec, label=str(emb_label)),
                        "input_text": text,
                        "input_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        "embedder_class": type(embedder).__name__,
                    }
                return vec

            embedder.create = wrapped_create  # type: ignore[method-assign]
            try:
                results = await orig_search(
                    clients, query, group_ids, config, search_filter, **kwargs
                )
            finally:
                embedder.create = orig_create  # type: ignore[method-assign]

            if store is not None:
                store.notes.append(
                    f"SearchConfig limit={getattr(config, 'limit', None)}; "
                    f"edge_config={getattr(config, 'edge_config', None)}"
                )
            return results

        search_utils.edge_fulltext_search = wrapped_fulltext
        search_utils.edge_similarity_search = wrapped_similarity
        search_utils.edge_bfs_search = wrapped_bfs
        search_utils.rrf = wrapped_rrf
        # edge_search imports rrf / channel fns from search_utils at module level —
        # also patch names bound inside search.py
        search_mod.edge_fulltext_search = wrapped_fulltext
        search_mod.edge_similarity_search = wrapped_similarity
        search_mod.edge_bfs_search = wrapped_bfs
        search_mod.rrf = wrapped_rrf
        search_mod.edge_search = wrapped_edge_search
        search_mod.search = wrapped_search
        # Graphiti.search binds `search` at import time — patch that name too.
        orig_graphiti_search = graphiti_mod.search
        graphiti_mod.search = wrapped_search

        self._orig = {
            "fulltext": orig_fulltext,
            "similarity": orig_similarity,
            "bfs": orig_bfs,
            "rrf": orig_rrf,
            "edge_search": orig_edge_search,
            "search": orig_search,
            "graphiti_search": orig_graphiti_search,
        }
        try:
            yield self
        finally:
            search_utils.edge_fulltext_search = orig_fulltext
            search_utils.edge_similarity_search = orig_similarity
            search_utils.edge_bfs_search = orig_bfs
            search_utils.rrf = orig_rrf
            search_mod.edge_fulltext_search = orig_fulltext
            search_mod.edge_similarity_search = orig_similarity
            search_mod.edge_bfs_search = orig_bfs
            search_mod.rrf = orig_rrf
            search_mod.edge_search = orig_edge_search
            search_mod.search = orig_search
            graphiti_mod.search = orig_graphiti_search


def compare_memoryops_vs_graphiti(
    memoryops_facts: list[str], graphiti_facts: list[str]
) -> dict[str, Any]:
    if memoryops_facts == graphiti_facts:
        return {
            "relation": "PASS_THROUGH",
            "note": "MemoryOps.query edge order/facts match Graphiti.search (plus lab temporal classify fields only).",
            "n_memoryops": len(memoryops_facts),
            "n_graphiti": len(graphiti_facts),
        }
    return {
        "relation": "DIFFERENCES",
        "memoryops_facts": memoryops_facts,
        "graphiti_facts": graphiti_facts,
        "only_memoryops": [f for f in memoryops_facts if f not in graphiti_facts],
        "only_graphiti": [f for f in graphiti_facts if f not in memoryops_facts],
        "order_differs": memoryops_facts != graphiti_facts
        and set(memoryops_facts) == set(graphiti_facts),
    }


def build_search_path_map() -> str:
    """Document ACTUAL Graphiti 0.29.3 Graphiti.search call chain from installed package."""
    from graphiti_core.graphiti import Graphiti, DEFAULT_SEARCH_LIMIT
    from graphiti_core.search.search_config_recipes import EDGE_HYBRID_SEARCH_RRF
    from graphiti_core.embedder.client import EMBEDDING_DIM
    import graphiti_core

    pkg = inspect.getfile(graphiti_core)
    g_search = inspect.getfile(Graphiti)
    return f"""# Graphiti 0.29.3 — `Graphiti.search` call-chain map (FM-13)

> Source: installed package at `{pkg}`  
> Mapped from live imports — not docs speculation.  
> Lab stack: FalkorDBLite + DeterministicEmbedder + DeterministicCrossEncoder.

## Entry

```
LabMemoryOps.query(text, group_ids=[gid], num_results=N)
  → Graphiti.search(query, group_ids, num_results=N, center_node_uuid=None)
```

`Graphiti.search` file: `{g_search}`  
Decorator: `@handle_multiple_group_ids`  
Default limit constant: `DEFAULT_SEARCH_LIMIT={DEFAULT_SEARCH_LIMIT}`

## Recipe selection (center_node_uuid is None)

```
search_config = EDGE_HYBRID_SEARCH_RRF
search_config.limit = num_results
```

Then:

```
search(clients, query, group_ids, search_config, SearchFilters(), driver=driver)
  → results.edges
```

## `search()` (`graphiti_core.search.search.search`)

1. Validate group_ids; resolve driver / embedder / cross_encoder from `GraphitiClients`.
2. Empty query → empty `SearchResults`.
3. If any configured method needs vectors (cosine / mmr):  
   `embedder.create([query with newlines→spaces])` → `search_vector`  
   Else: zero vector of `EMBEDDING_DIM={EMBEDDING_DIM}`.
4. `semaphore_gather` of scope searches (only edge scope non-None for RRF recipe):
   - `edge_search(...)`
   - `node_search(...)` → no-op (`node_config=None`)
   - `episode_search(...)` → no-op
   - `community_search(...)` → no-op
5. Pack `SearchResults(edges, edge_reranker_scores, ...)`.

## `edge_search()` channels (EDGE_HYBRID_SEARCH_RRF)

Configured `search_methods`: **bm25**, **cosine_similarity** (BFS not in this recipe).

| Order | Method | Implementation | Candidate limit |
|---|---|---|---|
| 1 | `EdgeSearchMethod.bm25` | `edge_fulltext_search(driver, query, filter, group_ids, 2*limit)` | `2 * limit` |
| 2 | `EdgeSearchMethod.cosine_similarity` | `edge_similarity_search(..., 2*limit, sim_min_score)` | `2 * limit` |

Channel scores are computed inside Cypher (`ORDER BY score DESC`) but **discarded** when records are mapped to `EntityEdge` — only list order remains.

## Fusion / “rerank” slot

`EdgeReranker.rrf` → `rrf([[uuid,...], ...], min_score=reranker_min_score)`  
Score: `Σ 1/(rank_i + rank_const)` with default `rank_const=1`.

**Not used on this path:** `EdgeReranker.cross_encoder` / `DeterministicCrossEncoder.rank`  
(Those appear on `EDGE_HYBRID_SEARCH_CROSS_ENCODER` / `COMBINED_HYBRID_SEARCH_CROSS_ENCODER`, not default `Graphiti.search`.)

Return: `reranked_edges[:limit], edge_scores[:limit]`.

## MemoryOps post-layer (lab)

```
edges_raw = await graphiti.search(...)
base = [edge_to_dict(e) for e in edges_raw]
classified = [classify_edge_dict(e, eval_time) for e in base]  # FM-9 temporal labels
```

No reordering / filtering of search hits. Temporal status is observational.

## Diagram

```
query text
   │
   ├─ DeterministicEmbedder.create ──► search_vector (dim=1024)
   │
   ├─ BM25 fulltext (facts) ──► ordered EntityEdge[]     ─┐
   │                                                       ├─ RRF fusion ─► top-N edges
   └─ cosine similarity (fact_embedding, min_score=0.6) ─┘
                                                              │
                                                              ▼
                                                    Graphiti.search return
                                                              │
                                                              ▼
                                                    MemoryOps temporal classify
                                                              │
                                                              ▼
                                                    MemoryReceipt.edges
```
"""


def build_search_config_json() -> dict[str, Any]:
    from graphiti_core.graphiti import DEFAULT_SEARCH_LIMIT
    from graphiti_core.search.search_config_recipes import EDGE_HYBRID_SEARCH_RRF
    from graphiti_core.embedder.client import EMBEDDING_DIM
    import graphiti_core

    ec = EDGE_HYBRID_SEARCH_RRF.edge_config
    return {
        "graphiti_core_version": "0.29.3",
        "package_path": inspect.getfile(graphiti_core),
        "entry": "Graphiti.search",
        "DEFAULT_SEARCH_LIMIT": DEFAULT_SEARCH_LIMIT,
        "recipe_when_center_node_uuid_is_None": "EDGE_HYBRID_SEARCH_RRF",
        "EDGE_HYBRID_SEARCH_RRF": {
            "limit_default_before_override": EDGE_HYBRID_SEARCH_RRF.limit,
            "reranker_min_score": EDGE_HYBRID_SEARCH_RRF.reranker_min_score,
            "node_config": EDGE_HYBRID_SEARCH_RRF.node_config,
            "episode_config": EDGE_HYBRID_SEARCH_RRF.episode_config,
            "community_config": EDGE_HYBRID_SEARCH_RRF.community_config,
            "edge_config": {
                "search_methods": [m.value for m in ec.search_methods],
                "reranker": ec.reranker.value,
                "sim_min_score": ec.sim_min_score,
                "mmr_lambda": ec.mmr_lambda,
                "bfs_max_depth": ec.bfs_max_depth,
            },
        },
        "channels_real_separation": True,
        "channels": ["bm25", "cosine_similarity"],
        "fusion": "reciprocal_rank_fusion",
        "cross_encoder_on_default_path": False,
        "EMBEDDING_DIM": EMBEDDING_DIM,
        "lab_embedder": "DeterministicEmbedder",
        "lab_cross_encoder": "DeterministicCrossEncoder (wired but unused by Graphiti.search default)",
        "memoryops_num_results_used_in_fm11_fm13": 10,
        "neo4j": False,
        "backend": "FalkorDBLite",
    }
