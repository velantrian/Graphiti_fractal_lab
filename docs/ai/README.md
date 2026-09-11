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
4. `docs/research/RETRIEVAL_RELEVANCE_TRACK.md` — FM-13 → FM-16 retrieval-relevance research narrative.
5. `docs/research/RETRIEVAL_RELEVANCE_REASONING_LOG.md` — long-form decision history explaining how and why the research question changed.
6. `docs/research/FM16_CLOSURE_AND_INDEPENDENT_REVIEW_2026-09-11.md` — **FM-16 execution, independent forensic review convergence, interpretation corrections, chronology limitation, and closure boundary**.
7. `docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md` — backend roles; NOT VALIDATED honesty.
8. `README.md` — human landing; do not treat prose as live runtime evidence.
9. `SYSTEM_OVERVIEW.md` — human architecture explanation and explicit non-claims.
10. Relevant experiment code + `artifacts/memoryops/run_00X/` + local pytest/CI for the exact head under review.

Do **not** begin by scanning upstream `Graphiti_fractal` narrative and inferring that this lab implements or authorizes it.

## Lab lanes

```yaml
lanes:
  graph_backend_smoke:
    examples: [LadybugDB, SQLite metadata, backend stubs]
    evidence: tests + capability matrix
  retrieval_relevance:
    examples: [FM-13, FM-14, FM-15, FM-16]
    evidence: artifacts/memoryops/run_00X + experiment tests + retrieval relevance track + reasoning log + FM16 closure ledger
```

A statement valid in one lane must not be generalized to another.

## Authority order

For current lab behavior, prefer evidence in this order:

```text
live exact repository state / exact branch or PR head
  > executable run artifacts + tests / CI in this repo
  > active lab experiment code
  > RESEARCH_STATUS.md
  > lane-specific research track / FM-16 closure ledger
  > long-form reasoning log / human explanatory docs
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
  - pairwise_ranking_signal_is_not_global_qualification
  - global_threshold_failure_is_not_ranker_uselessness
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
  status: FM16_CLOSED_BOUNDED_RESEARCH_CONTINUES
  fm13: COMPLETED
  fm14: COMPLETED
  fm15: COMPLETED
  fm16: CLOSED_BOUNDED_EXPERIMENT
  fm16_run_007: COMPLETE
  fm16_execution_sha: 62cfa45a80ec83794b701d88873ce136b7629354
  fm16_independent_review: PASS_WITH_MAJOR_INTERPRETATION_FINDINGS

  pairwise_cross_encoder_signal: STRONGER_THAN_EMBEDDING_ON_FROZEN_FM16_FIXTURE
  ce_cal_mrr: 0.9583333333
  embedding_cal_mrr: 0.9166666667
  ce_test_mrr: 0.9166666667
  embedding_test_mrr: 0.8611111111

  retrospective_strict_h1_ce: FAIL
  retrospective_strict_h1_embedding: FAIL

  ce_global_threshold_feasible: false
  embedding_global_threshold_feasible: false
  ce_threshold: null
  embedding_threshold: null
  ce_threshold_candidates: 1599
  embedding_threshold_candidates: 1601

  no_material_gain_original_label: TOO_BROAD_AS_OVERALL_VERDICT
  ce_vs_embedding_ranking: CE_BETTER
  ce_vs_embedding_global_qualification: BOTH_INFEASIBLE

  broad_query_heterogeneity: IMPORTANT_LIMITATION
  honest_empty_established: false

  threshold_selection_uses_cal_only: true
  strict_blind_test_order_satisfied: false
  test_scores_existed_before_theta_freeze: true

  runtime_gate: NOT_IMPLEMENTED
  search_recipe_changed: false
  architecture_changed: false
  upstream_changed: false
  production_authorized: false

  next: RECORD_CLOSURE_AND_STOP_BEFORE_ANY_NEW_MECHANISM_EXPERIMENT
```

### FM-16 closure guard

FM-16 is no longer `PLANNED_NOT_RUN`. The bounded run exists under `artifacts/memoryops/run_007/` and its numeric core has been independently reproduced.

Safe interpretation:

```text
CE RANKING BETTER ON FROZEN FIXTURE
≠
ONE GLOBAL CE THRESHOLD FEASIBLE

GLOBAL THRESHOLD NOT FEASIBLE ON THIS MIXED TASK
≠
GLOBAL THRESHOLDS NEVER WORK

STRICT H1 FAIL
≠
PAIRWISE SIGNAL USELESS
```

The original `NO_MATERIAL_GAIN` label must be read narrowly: both CE and embedding fail the global-threshold feasibility contract. It must not erase the observed CE ranking advantage.

The effective CQ11/TQ11 gold used for preregistration/scoring is the adjusted three-fact set; the initial five-item source literal is later mutated before the experiment begins. Therefore there is no established critical source-vs-artifact gold mismatch, although the source representation is confusing and should not be used without reading the adjustment.

### Held-out chronology limitation

The threshold search itself is calibration-only. However the executable `run_fm16()` order computes CE TEST and embedding TEST scores before threshold/null freeze, and also writes pre-threshold TEST ranking before the CAL threshold search.

Therefore:

```text
CAL_ONLY_THRESHOLD_SELECTION = YES
EVIDENCE_TEST_CHANGED_THETA = NO
THRESHOLD_APPLICATION_TO_TEST_AFTER_FREEZE = YES
STRICT_BLIND_TEST_ORDER = NOT_SATISFIED
```

Do not claim that run_007 satisfied the later hardened rule “freeze theta/null before TEST scores exist.” This chronology limitation does not invalidate the CAL-only mathematical finding that zero feasible thresholds exist.

### What FM-16 established

Under the frozen FM-16 corpus, the two frozen score families and the mixed-query feasibility constraints:

- CE ranking is stronger than the embedding baseline on the reported CAL/TEST metrics;
- strict later all-query H1 is not satisfied by either family;
- CE: `1599` threshold candidates, `0` feasible, `theta=null`;
- embedding: `1601` threshold candidates, `0` feasible, `theta=null`;
- one global raw-score threshold is therefore not feasible for either family on this task;
- broad/narrow/no-answer query heterogeneity is an important interpretation limitation;
- Honest Empty is not established as a solved runtime property;
- no runtime, search, architecture, product or upstream change is authorized.

### What FM-16 did not establish

Do not infer any of the following:

- global thresholds never work;
- CrossEncoder is useless;
- CrossEncoder is universally superior;
- Honest Empty is solved;
- structural filtering is required;
- LLM recognition is required;
- a memory-specific SLM is required;
- graph/path scoring is required;
- query routing is required;
- multi-hop reasoning is proven;
- runtime CE gating is authorized.

Read [`../research/FM16_CLOSURE_AND_INDEPENDENT_REVIEW_2026-09-11.md`](../research/FM16_CLOSURE_AND_INDEPENDENT_REVIEW_2026-09-11.md) before proposing a follow-up mechanism.

## Historical FM-16 v1 execution guard

The previously drafted FM-16 v1 protocol remains superseded. Its pre-scoring review history is preserved because it explains why relevance was separated from positive entailment, why multi-hop components were separated from direct-answer gold, and why null-threshold behavior was required.

The later executed run_007 must not be rewritten to make it conform retroactively to the later strict-blind sequencing rule. Record the limitation; do not fabricate cleaner history.

```text
RELEVANT_ANSWER ≠ SUPPORTS_POSITIVE_PROPOSITION
DIRECT_ANSWER ≠ MULTI_HOP_COMPONENT ≠ RELATED_CONTEXT
NARROW_FACTOID_RELEVANCE ≠ BROAD_ASSOCIATIVE_RELEVANCE
ALL_NON_GOLD_REJECTION ≠ HARD_NEGATIVE_REJECTION
SCORER_FAILED ≠ NO_RELEVANT_CANDIDATES
```

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
9. do not run superseded FM-16 v1;
10. do not silently change the target from direct-answer relevance to multi-hop component retrieval;
11. preserve the reasoning chain: if changing H1/H2/H3 boundaries, explain why and cite new evidence rather than only editing the current-status table;
12. do not modify or overwrite `run_007` merely to make its chronology look cleaner;
13. do not treat `NO_MATERIAL_GAIN` as an overall CE-vs-embedding verdict;
14. do not claim a strict blind held-out sequence for FM-16; TEST scores existed before theta/null freeze in the executable order;
15. after FM-16 closure, any structural / LLM / SLM / graph-path / query-conditioned mechanism is a **new research hypothesis**, not an automatic architecture promotion.

## Human-facing docs

- `README.md` — landing page;
- `SYSTEM_OVERVIEW.md` — deep human overview;
- `RESEARCH_STATUS.md` — current lab ledger;
- `docs/research/RETRIEVAL_RELEVANCE_TRACK.md` — retrieval relevance research history/current frontier;
- `docs/research/RETRIEVAL_RELEVANCE_REASONING_LOG.md` — long-form reasoning, rejected interpretations, review synthesis and why the current frontier exists;
- `docs/research/FM16_CLOSURE_AND_INDEPENDENT_REVIEW_2026-09-11.md` — FM-16 execution + review closure and reconciled findings;
- `docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md` — backend matrix.

Exact acceptance evidence belongs in tests, CI, run artifacts, exact commits, or explicit research ledgers — not inferred from narrative alone.
