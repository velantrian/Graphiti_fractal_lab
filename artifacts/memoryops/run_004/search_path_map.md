# Graphiti 0.29.3 — `Graphiti.search` call-chain map (FM-13)

> Source: installed package at `/workspace/Graphiti_fractal_lab/.venv/lib/python3.13/site-packages/graphiti_core/__init__.py`  
> Mapped from live imports — not docs speculation.  
> Lab stack: FalkorDBLite + DeterministicEmbedder + DeterministicCrossEncoder.

## Entry

```
LabMemoryOps.query(text, group_ids=[gid], num_results=N)
  → Graphiti.search(query, group_ids, num_results=N, center_node_uuid=None)
```

`Graphiti.search` file: `/workspace/Graphiti_fractal_lab/.venv/lib/python3.13/site-packages/graphiti_core/graphiti.py`  
Decorator: `@handle_multiple_group_ids`  
Default limit constant: `DEFAULT_SEARCH_LIMIT=10`

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
   Else: zero vector of `EMBEDDING_DIM=1024`.
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
