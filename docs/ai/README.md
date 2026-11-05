# AI / Agent Entrypoint

Document role: machine-first repository router for **Graphiti_fractal_lab**.

This file is intentionally concise and non-narrative. Human readers should start with [`../../README.md`](../../README.md) and [`../../SYSTEM_OVERVIEW.md`](../../SYSTEM_OVERVIEW.md).

## Project identity

```yaml
project: Graphiti Fractal Lab
repository: velantrian/Graphiti_fractal_lab
architecture_role: RESEARCH sandbox — full Graphiti_fractal tree mirrored for experimentation + Ladybug/SQLite lab smoke
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
4. `docs/LAB_GRAPH_BACKEND_CAPABILITY_MATRIX.md` — lab backend roles; NOT VALIDATED honesty.
5. `docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md` — upstream-style migration contract (context only; mirrored).
6. `README.md` — human landing; do not treat prose as live runtime evidence.
7. `SYSTEM_OVERVIEW.md` — human architecture explanation and explicit non-claims.
8. `src/fractal_lab/backends/` — adapters, stubs, `ValidationStatus`.
9. `tests/` + local `pytest` / `make test-lab` / CI for the exact head under review.

Do **not** begin by scanning upstream `Graphiti_fractal` narrative and inferring that this lab implements it.

The working tree now **mirrors** upstream Fractal sources for safe edits. Presence of `core/`, `docker-compose.yml`, etc. does **not** mean Neo4j/Docker/secrets are available or that Fractal is ACTIVE in this environment. Upstream machine router preserved at [`UPSTREAM_FRACTAL_README.md`](UPSTREAM_FRACTAL_README.md).

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
  - mirrored_tree_is_not_docker_available
  - mirrored_neo4j_files_are_not_lab_active_runtime
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
  make_target: test-lab  # always-on in .github/workflows/ci.yml after test-contracts
  evidence_note: "re-run make test-lab / pytest on exact head before citing pass counts"
  mirrored_fractal_tree: present_for_experimentation_only  # Neo4j/Docker/secrets still required for full stack
```

## Research / stubs / non-active

Do not infer Fractal or lab runtime adoption from presence of:

- `kuzu_stub.py`, `postgres_stub.py`, `duckdb_stub.py`;
- Neo4j, Graphiti, `graphiti_core` as a lab-active path;
- OpenAI / embeddings / Docker compose as proven in this environment;
- dual-write, migration, rollback tooling;
- capability matrix rows marked NOT VALIDATED / NOT DESIGNED / NOT RUN.

```yaml
stubs:
  kuzu: NOT_VALIDATED
  postgres: NOT_VALIDATED
  duckdb: NOT_VALIDATED
mirrored_but_not_lab_proven:
  neo4j_compose: present_in_tree_requires_docker_and_secrets
  graphiti_core_dep: present_in_requirements_txt_not_lab_smoke_path
  openai_embeddings_modules: present_in_mirrored_tree_not_lab_smoke_path
lab_smoke_authority:
  ladybug: SMOKE_TESTED_lab_only
  sqlite_meta: SMOKE_TESTED_lab_only
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
- `docs/LAB_GRAPH_BACKEND_CAPABILITY_MATRIX.md` — lab matrix;
- `docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md` — upstream-style matrix (mirrored context).

Exact acceptance evidence belongs in tests, CI, PRs, or the research ledger — not inferred from narrative alone.
