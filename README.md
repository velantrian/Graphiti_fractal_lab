# Graphiti_fractal_lab

> **RESEARCH lab only.** Thin multi-backend experiments adapted from
> [Graphiti_fractal](https://github.com/velantrian/Graphiti_fractal) concepts.
> This repo does **not** modify the main Fractal Memory project and does **not**
> claim Neo4j / Graphiti production parity.

## What this is

A **sandbox** for evaluating lightweight graph + metadata stores that might one
day sit under a Fractal-like memory layer — without Docker, Neo4j, or OpenAI.

| Concern | Choice in this lab | Status |
|---|---|---|
| Primary graph (smoke) | **LadybugDB** (`pip install ladybug`) | **smoke-tested** on disk |
| Ops / lab metadata | **SQLite** (stdlib) | **smoke-tested** |
| Optional | Kùzu, PostgreSQL, DuckDB | **stubs only — NOT VALIDATED** |
| Production Fractal path | Neo4j + Graphiti (upstream repo) | **out of scope here** |

## What this is not

- Not a drop-in replacement for `Graphiti_fractal`
- Not Graphiti / Neo4j parity
- Not a migration authorization
- Not dual-write / dual-authority memory

If `graphiti_core` cannot run on Ladybug, this lab stays a **thin adapter layer**
plus smoke tests — by design.

## Quick start (no Docker)

```bash
cd Graphiti_fractal_lab
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
pytest
```

Smoke path:

1. Creates an on-disk LadybugDB database
2. Writes/reads a few nodes + relationships via Cypher
3. Creates a SQLite table for lab metadata
4. Asserts both round-trips

## Layout

```text
src/fractal_lab/
  backends/
    base.py              shared Protocol / result types
    ladybug_adapter.py   primary runnable path
    sqlite_meta.py       lab ops/metadata
    kuzu_stub.py         NOT VALIDATED
    postgres_stub.py     NOT VALIDATED
    duckdb_stub.py       NOT VALIDATED
docs/
  GRAPH_BACKEND_CAPABILITY_MATRIX.md   adapted research matrix
RESEARCH_STATUS.md
tests/
  test_ladybug_smoke.py
  test_sqlite_meta.py
```

## Docs

- [`RESEARCH_STATUS.md`](RESEARCH_STATUS.md) — honest validation ledger
- [`docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md`](docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md)
  — adapted from upstream Fractal matrix; Ladybug is **evaluate only**

## Upstream relationship

- Source of concepts: https://github.com/velantrian/Graphiti_fractal
- This lab: https://github.com/velantrian/Graphiti_fractal_lab
- Upstream Neo4j remains the only **ACTIVE** durable graph authority for Fractal Memory.
- LadybugDB here is **ADJACENT / RESEARCH**.

## License

MIT (lab scaffolding). Upstream Fractal remains separately licensed/owned.
