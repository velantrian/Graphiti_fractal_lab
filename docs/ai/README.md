# AI / Agent Entrypoint

Document role: machine-first repository router for **Graphiti_fractal_lab**.

This file is intentionally concise and non-narrative. Human readers should start with [`../../README.md`](../../README.md) and [`../../SYSTEM_OVERVIEW.md`](../../SYSTEM_OVERVIEW.md).

## Project identity

```yaml
project: Graphiti Fractal Lab
repository: velantrian/Graphiti_fractal_lab
architecture_role: RESEARCH sandbox — full Graphiti_fractal tree mirrored for experimentation + multiple bounded lab lanes
upstream_authority: velantrian/Graphiti_fractal
runtime_authorization_from_docs: false
fractal_parity_claimed: false
migration_authorized: false
```

## Required reading order

1. `docs/ai/README.md` — this routing contract.
2. `AGENTS.md` — one-pager agent contract (points here).
3. `RESEARCH_STATUS.md` — current honest research/validation ledger across lab lanes.
4. `docs/research/RETRIEVAL_RELEVANCE_TRACK.md` — FM-13 → FM-16 retrieval-relevance research narrative and current frontier.
5. `docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md` — backend roles; NOT VALIDATED honesty.
6. `README.md` — human landing; do not treat prose as live runtime evidence.
7. `SYSTEM_OVERVIEW.md` — human architecture explanation and explicit non-claims.
8. Relevant experiment code + `artifacts/memoryops/run_00X/` + local pytest/CI for the exact head under review.

Do **not** begin by scanning upstream `Graphiti_fractal` narrative and inferring that this lab implements or authorizes it.

## Lab lanes

This repository currently contains more than one experimental lane:

```yaml
lanes:
  graph_backend_smoke:
    examples: [LadybugDB, SQLite metadata, backend stubs]
    evidence: tests + capability matrix
  retrieval_relevance:
    examples: [FM-13, FM-14, FM-15, planned FM-16]
    evidence: artifacts/memoryops/run_00X + experiment tests + retrieval relevance track
```

A statement valid in one lane must not be generalized to another.

## Authority order

For current lab behavior, prefer evidence in this order:

```text
live exact repository state / exact branch or PR head
  > executable run artifacts + tests / CI in this repo
  > active lab experiment code
  > RESEARCH_STATUS.md
  > lane-specific research track
  > human README / SYSTEM_OVERVIEW narrative
  > upstream / external donor docs as context only
```

A pretty README diagram, donor audit, stub file, or upstream ACTIVE claim must not override lab code/tests/artifacts.

## Core invariants

```yaml
invariants:
  - lab_is_not_fractal_runtime
  - smoke_is_not_parity
  - experiment_pass_is_not_production_authorization
  - stub_is_not_validated
  - ladybug_lab_is_not_durable_fractal_memory
  - falkordblite_experiment_is_not_neo4j_parity
  - sqlite_meta_is_not_graph_authority
  - research_is_not_runtime
  - file_exists_is_not_tested
  - upstream_active_is_not_lab_active
  - do_not_modify_or_push_upstream_Graphiti_fractal_from_lab_tasks
  - retrieved_is_not_relevant
  - relevance_is_not_evidence
  - relevance_is_not_truth
  - no_relevant_result_is_not_entity_absent
  - unknown_is_not_false
```

## Retrieval-relevance current snapshot

```yaml
retrieval_relevance:
  status: IN_PROGRESS
  fm13: COMPLETED
  fm14: COMPLETED
  fm15: COMPLETED
  fm16: PLANNED_NOT_RUN
  pairwise_cross_encoder_signal: CONFIRMED_ON_FM15_FIXTURE
  global_threshold: NOT_ESTABLISHED
  runtime_gate: NOT_IMPLEMENTED
  production_authorized: false
  next: FM16_HELD_OUT_GENERALIZATION_AND_CALIBRATION
```

Read [`../research/RETRIEVAL_RELEVANCE_TRACK.md`](../research/RETRIEVAL_RELEVANCE_TRACK.md) before making claims about why FM-13–FM-16 exist or what they establish.

## Research / stubs / non-active

Do not infer Fractal or lab runtime adoption from presence of:

- `kuzu_stub.py`, `postgres_stub.py`, `duckdb_stub.py`;
- mirrored Neo4j/Graphiti/product code;
- model packages or cached model weights;
- experiment artifacts;
- Docker compose files;
- migration / dual-write / rollback ideas;
- donor references from Titan, Crystal, OpenClaw, SVL, Soul, EITI or other projects.

Important scope correction:

```text
Graphiti / embeddings / model-backed scoring are NOT globally "out of scope" for this repository anymore.
They have been exercised in the separate retrieval-relevance experiment lane.
That does NOT validate the Ladybug backend lane, Neo4j parity, or upstream runtime activation.
```

## Validation semantics

```text
📄 file exists
≠ 🧪 tested
≠ 🎛️ feature enabled
≠ 🔗 active Fractal path
≠ 📡 runtime observed
≠ 🚀 production / migration authorized
```

Always bind acceptance claims to exact commit/head and exact experiment scope.

## Safe modification rules

Before changing adapters, experiment claims, or docs:

1. keep changes bounded to the named lane and task;
2. never claim Neo4j parity from FalkorDBLite/Ladybug evidence;
3. never treat lab data as Fractal production/durable authority;
4. update `RESEARCH_STATUS.md` only with re-verified evidence;
5. use run-specific artifacts for experiment truth;
6. do not push to `velantrian/Graphiti_fractal` from lab tasks;
7. do not convert RESEARCH into Fractal runtime via documentation side effect;
8. donor pattern ≠ adoption; external/cross-project authority must not leak into Fractal relevance semantics.

## Human-facing docs

- `README.md` — landing page;
- `SYSTEM_OVERVIEW.md` — deep human overview;
- `RESEARCH_STATUS.md` — current lab ledger;
- `docs/research/RETRIEVAL_RELEVANCE_TRACK.md` — retrieval relevance research history/current frontier;
- `docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md` — backend matrix.

Exact acceptance evidence belongs in tests, CI, run artifacts, exact commits, or explicit research ledgers — not inferred from narrative alone.
