# FM-0 Audit — Fractal MemoryOps vs lab FalkorDBLite plug point

**Date:** 2026-09-10 (Europe/Berlin)  
**Lab checkout:** `/workspace/Graphiti_fractal_lab`  
**Branch:** `experiment/falkordblite-deterministic-memory`  
**Starting HEAD:** `7af9412c75b4ab96bba6d00f71bc477542a98738`  
**Upstream `velantrian/Graphiti_fractal`:** confirmed `2437244149baeb0c645e2e942125be92bba3a96b` (untouched)  
**Stack:** `graphiti-core==0.29.3`, `falkordblite==0.10.0` (import surface: `redislite.AsyncFalkorDB`)

## 1. Existing MemoryOps / memory interfaces (mirrored Fractal)

| Surface | Path | Role | Status |
|---|---|---|---|
| `MemoryOps` | `core/memory_ops.py` | High-level ingest (`remember_text` → `knowledge.ingest`), scoped `search_memory`, context build | **Executable** against Neo4j Graphiti client |
| Docs | `docs/memory_ops.md` | Spec for remember / search / chat / MCP | Spec matches `MemoryOps` API |
| Lifecycle | `core/memory_lifecycle.py` | Promotion / consolidation planning (no direct Falkor) | Planning only |
| Doctor | `core/memory_doctor.py` | Health checks including **Neo4j** ping | Neo4j-specific |
| Import | `core/memory_import.py` | Import plans | Neo4j-oriented |
| Knowledge ingest | `knowledge/ingest.py` | Canonical `ingest_text_document` / `add_episode` path | Uses Graphiti; Cypher episode lookup assumes Neo4j driver query shape |
| CLI | `main.py` | Fractal Memory CLI (`setup`, `seed`, search demos) | Wired to `get_graphiti_client()` → Neo4j |
| MCP / API | `mcp_server/`, `api/`, `app.py` | Product surfaces over MemoryOps | Out of scope for FM lab |

**Gaps vs FM need (ingest / query / inspect / reopen on FalkorDBLite):**

- No `inspect` API exposing episodes + EntityEdges with `valid_at` / `invalid_at` / `group_id` / provenance as a first-class MemoryOps method.
- No reopen / process-boundary helper; product path assumes long-lived Neo4j.
- `MemoryOps.search_memory` edge payload omits temporal fields (`valid_at` / `invalid_at`) — would need enrichment for FM-6/FM-8 receipts.
- Product `MemoryOps` is coupled to Fractal Neo4j client (`core/graphiti_client.py`), migrations, OpenAI LLM — **must not** be forced onto FalkorDBLite.

## 2. Neo4j-specific assumptions (do not destroy)

- `core/graphiti_client.py`: `Graphiti(uri, user, password, …)` + `neo4j.exceptions.ClientError` + migrations.
- `core/config.py`: `NEO4J_URI` / user / password / database.
- `core/memory_doctor.py`, `core/derived_graph.py`, GDS analytics docs: Neo4j substrate.
- Integration pytest marker: `integration` → isolated Neo4j/Graphiti.
- `knowledge/ingest.py` episode UUID resolution uses Cypher `MATCH (e:Episodic)` via driver — historically Neo4j-shaped.

**Conclusion:** Product MemoryOps stays Neo4j. Lab must **wrap/adapt**, not rewrite Fractal core.

## 3. Existing lab FalkorDBLite plug (reuse — do not reinvent)

Already on this branch from P0–P7 (artifacts `run_001`…`run_006` preserved):

| Module | Purpose |
|---|---|
| `src/fractal_lab/experiments/falkor_graphiti_bootstrap.py` | `open_lab_graphiti(db_path)` → `AsyncFalkorDB` + `FalkorDriver` + deterministic providers |
| `src/fractal_lab/experiments/deterministic_providers.py` | Embedder / cross-encoder / base LLM stub |
| `src/fractal_lab/experiments/deterministic_temporal_llm.py` | Temporal EdgeTimestamps + EdgeDuplicate for language contradiction |
| `tests/lab/test_falkordblite_*.py` | Persistence reopen, scope isolation, temporal contradiction, write-surface inventory |

**Known Falkor constraints (carry forward):**

- Each `group_id` is a **separate Falkor graph DB**; inspect must clone driver to `group_id` (P5 finding).
- Prefer `Graphiti.add_episode` / high-level resolve paths — **not** raw `EntityEdge.save` or SNAPSHOT_PRE restore (P6/P7).
- Invariants: `SEMANTIC≠RAW`, `RESTORED_BYTES≠APPLICABILITY`, `RETRIEVED≠CURRENT`, `STORED≠CURRENT`, `MEMORY≠CANON`.

## 4. FM-0 decision — lab-only thin layer

**Do not invent new architecture.** Add `src/fractal_lab/memoryops/` that:

1. Opens Graphiti via existing `open_lab_graphiti` (FalkorDBLite path).
2. Ingests only through `graphiti.add_episode` (+ optional bulk later).
3. Queries via `graphiti.search` with explicit `group_ids`.
4. Inspects via `EntityEdge.get_by_group_ids` / episode APIs on the **group-cloned** driver.
5. Reopens by constructing a new process/`open_lab_graphiti` on the same DB path.
6. Emits receipts (operation, timestamp, group_id, episode UUID, entities/edges, temporal fields).

Product `core.memory_ops.MemoryOps` remains the Fractal boundary for Neo4j; lab MemoryOps is an **adapter**, not Canon.

## 5. FM-0 status

**FINDINGS** — audit complete; plug point identified; no code claims yet.
