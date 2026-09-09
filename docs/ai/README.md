# AI / Agent Entrypoint

Document role: machine-first repository router for **Graphiti_fractal_lab**.

This file is intentionally concise and non-narrative. Human readers should start with [`../../README.md`](../../README.md) and [`../../SYSTEM_OVERVIEW.md`](../../SYSTEM_OVERVIEW.md).

## Project identity

```yaml
project: Graphiti Fractal Lab
repository: velantrian/Graphiti_fractal_lab
architecture_role: RESEARCH sandbox for lightweight multi-backend smoke outside Fractal runtime
upstream_authority: velantrian/Graphiti_fractal  # Graphiti + Neo4j ACTIVE elsewhere
primary_lab_graph_smoke: ladybug==0.20.3
primary_lab_meta: sqlite3 (stdlib)
runtime_authorization_from_docs: false
fractal_parity_claimed: false
migration_authorized: false
```

## Required reading order

1. `docs/ai/README.md` — this routing contract.
2. `AGENTS.md` — one-pager agent contract (points here).
3. `RESEARCH_STATUS.md` — honest validation ledger (lab evidence only).
4. `docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md` — backend roles; NOT VALIDATED honesty.
5. `README.md` — human landing; do not treat prose as live runtime evidence.
6. `SYSTEM_OVERVIEW.md` — human architecture explanation and explicit non-claims.
7. `src/fractal_lab/backends/` — adapters, stubs, `ValidationStatus`.
8. `tests/` + local `pytest` (or CI) for the exact head under review.

Do **not** begin by scanning upstream `Graphiti_fractal` narrative and inferring that this lab implements it.

## Authority order

For current lab behavior, prefer evidence in this order:

```text
live exact repository state / exact PR head
  > executable tests (pytest) in this repo
  > active lab code under src/fractal_lab
  > RESEARCH_STATUS.md / capability matrix
  > human README / SYSTEM_OVERVIEW narrative
  > upstream Graphiti_fractal docs (context only — not lab proof)
```

A pretty README diagram, stub file, or upstream ACTIVE claim must not override lab code/tests.

## Core invariants

```yaml
invariants:
  - lab_is_not_fractal_runtime
  - smoke_is_not_parity
  - stub_is_not_validated
  - ladybug_lab_is_not_durable_fractal_memory
  - sqlite_meta_is_not_graph_authority
  - research_is_not_runtime
  - green_pytest_is_not_production_authorization
  - green_pytest_is_not_migration_authorization
  - file_exists_is_not_tested
  - upstream_active_is_not_lab_active
  - do_not_modify_or_push_upstream_Graphiti_fractal_from_lab_tasks
```

## Active (lab-local) architecture

```yaml
active_in_this_repo:
  graph_smoke: LadybugAdapter  # on-disk Cypher node/rel round-trip
  ops_metadata: SqliteLabMeta  # lab run ledger only
  package: fractal-lab / src/fractal_lab
  tests:
    - tests/test_ladybug_smoke.py
    - tests/test_sqlite_meta.py
  evidence_note: "4 passed on Python 3.13 + ladybug 0.20.3 when last verified locally; re-run pytest on exact head"
```

## Research / stubs / non-active

Do not infer Fractal or lab runtime adoption from presence of:

- `kuzu_stub.py`, `postgres_stub.py`, `duckdb_stub.py`;
- Neo4j, Graphiti, `graphiti_core`;
- OpenAI / embeddings / Docker compose;
- dual-write, migration, rollback tooling;
- capability matrix rows marked NOT VALIDATED / NOT DESIGNED / NOT RUN.

```yaml
stubs:
  kuzu: NOT_VALIDATED
  postgres: NOT_VALIDATED
  duckdb: NOT_VALIDATED
out_of_scope_here:
  neo4j: upstream_only
  graphiti_core: upstream_only
  openai_embeddings: absent
  docker_neo4j: intentionally_absent
```

## Validation semantics

```text
📄 file exists
≠ 🧪 contract tested
≠ 🎛️ feature enabled
≠ 🔗 active Fractal path
≠ 📡 runtime observed
≠ 🚀 production / migration authorized
```

Always bind acceptance claims to the exact commit/head that was tested.

Lab `ValidationStatus.SMOKE_TESTED` ≠ upstream Fractal `ACTIVE`.

## Safe modification rules

Before changing adapters, status claims, or docs:

1. keep code changes minimal unless the task explicitly asks for code;
2. never claim Neo4j/Graphiti parity;
3. never treat lab Ladybug data as Fractal durable memory;
4. update `RESEARCH_STATUS.md` only with re-verified evidence;
5. do not push to `velantrian/Graphiti_fractal`;
6. do not convert RESEARCH into Fractal runtime via documentation side effect.

## Human-facing docs

- `README.md` — landing page;
- `SYSTEM_OVERVIEW.md` — deep human overview;
- `RESEARCH_STATUS.md` — ledger;
- `docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md` — matrix.

Exact acceptance evidence belongs in tests, CI, PRs, or the research ledger — not inferred from narrative alone.
