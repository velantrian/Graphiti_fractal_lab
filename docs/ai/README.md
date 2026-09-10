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
  - relevant_is_not_supports_positive_proposition
  - direct_answer_is_not_multi_hop_component
  - multi_hop_component_is_not_related_context
  - narrow_factoid_relevance_is_not_broad_associative_relevance
  - relevance_is_not_evidence
  - relevance_is_not_truth
  - no_relevant_result_is_not_entity_absent
  - scorer_failure_is_not_honest_empty
  - gold_label_is_not_training_target
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
  fm16_protocol_v1: REQUEST_CHANGES_BEFORE_SCORING_SUPERSEDED
  fm16_preregistration: NOT_CREATED
  fm16_run_007: NOT_CREATED
  pairwise_cross_encoder_signal: CONFIRMED_ON_FM15_FIXTURE
  q5_direct_support: false
  q5_co_retrieval: YES
  q5_multi_hop_reasoning: NOT_PROVEN
  fm16_primary_target: DIRECT_ANSWER_RELEVANCE
  h1_direct_ranking: TO_TEST
  h2_global_absolute_gate: TO_TEST
  h3_multi_hop_component_retrieval: SEPARATE_HYPOTHESIS
  global_threshold: NOT_ESTABLISHED
  hard_negative_rejection_floor: TO_BE_PREREGISTERED
  runtime_gate: NOT_IMPLEMENTED
  production_authorized: false
  next: FINALIZE_HARDENED_FM16_PROTOCOL_BEFORE_PREREGISTRATION_AND_SCORING
```

### FM-16 execution guard

**Do not execute the previously drafted FM-16 protocol.** Independent pre-scoring review plus later synthesis found methodological defects and task-definition ambiguity that must be fixed first.

Required corrections before any scoring:

- primary evaluation gold = **direct-answer relevance**, not positive entailment and not generic usefulness;
- `DIRECT ANSWER ≠ MULTI-HOP COMPONENT ≠ RELATED CONTEXT`;
- Q5-like required multi-hop components must not silently enter the same primary global-threshold gold; treat them as a separate diagnostic/future hypothesis unless a new protocol explicitly changes the task;
- broad associative queries remain a challenge stratum and require explicit gold semantics;
- repair negation / conditional / numeric / temporal / scope / attribution examples according to the query's information need;
- add an explicit preregistered hard-negative rejection / returned-set quality gate for `GENERALIZATION_STRONG`;
- do **not** adopt a concrete floor such as `0.85` without preregistered rationale;
- if no feasible calibration threshold exists, use `threshold = null` and mark thresholded TEST metrics `NOT_APPLICABLE`;
- after a null threshold decision is frozen/hashed, threshold-free held-out ranking metrics may still be computed;
- freeze exact formulas, denominators, ties, comparator, verdict table, and systematic-inversion rule;
- verify actually loaded CE/embedding snapshot/weights/tokenizer/config/inference profile rather than trusting a cached revision string;
- preserve the order: preregistration → model identity check → calibration scoring → threshold/null freeze → TEST scoring/reporting → anchor regression;
- never count timeout/NaN/missing score as successful EMPTY;
- treat `GLOBAL_THRESHOLD_NOT_FEASIBLE` as a possible/predicted outcome, not a known result before FM-16.

```text
RELEVANT_ANSWER ≠ SUPPORTS_POSITIVE_PROPOSITION
DIRECT_ANSWER ≠ MULTI_HOP_COMPONENT ≠ RELATED_CONTEXT
NARROW_FACTOID_RELEVANCE ≠ BROAD_ASSOCIATIVE_RELEVANCE
ALL_NON_GOLD_REJECTION ≠ HARD_NEGATIVE_REJECTION
SCORER_FAILED ≠ NO_RELEVANT_CANDIDATES
```

Read [`../research/RETRIEVAL_RELEVANCE_TRACK.md`](../research/RETRIEVAL_RELEVANCE_TRACK.md) before making claims about FM-16 readiness.

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
8. donor pattern ≠ adoption; external/cross-project authority must not leak into Fractal relevance semantics;
9. do not run superseded FM-16 v1; protocol hardening must precede preregistration/scoring;
10. do not silently change the target from direct-answer relevance to multi-hop component retrieval.

## Human-facing docs

- `README.md` — landing page;
- `SYSTEM_OVERVIEW.md` — deep human overview;
- `RESEARCH_STATUS.md` — current lab ledger;
- `docs/research/RETRIEVAL_RELEVANCE_TRACK.md` — retrieval relevance research history/current frontier;
- `docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md` — backend matrix.

Exact acceptance evidence belongs in tests, CI, run artifacts, exact commits, or explicit research ledgers — not inferred from narrative alone.
