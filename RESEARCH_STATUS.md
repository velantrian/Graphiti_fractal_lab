# 📊 RESEARCH_STATUS

> **Repo:** `velantrian/Graphiti_fractal_lab`  
> **Role:** 🔬 RESEARCH sandbox — full Fractal tree mirrored for experimentation; not production Fractal Memory  
> **Updated:** 2026-09-11  
> **Upstream authority:** `velantrian/Graphiti_fractal` remains separate. Lab evidence never authorizes upstream/runtime changes.

🤖 **AI routing:** start with [`docs/ai/README.md`](docs/ai/README.md).  
🔎 **Retrieval-relevance narrative:** [`docs/research/RETRIEVAL_RELEVANCE_TRACK.md`](docs/research/RETRIEVAL_RELEVANCE_TRACK.md) — historical/research narrative; for current FM-17-pre status continue to the FM-17-pre index below.  
🧭 **Long-form reasoning history:** [`docs/research/RETRIEVAL_RELEVANCE_REASONING_LOG.md`](docs/research/RETRIEVAL_RELEVANCE_REASONING_LOG.md).  
✅ **FM-16 closure + independent review reconciliation:** [`docs/research/FM16_CLOSURE_AND_INDEPENDENT_REVIEW_2026-09-11.md`](docs/research/FM16_CLOSURE_AND_INDEPENDENT_REVIEW_2026-09-11.md).  
🔐 **FM-17-pre current protocol index:** [`docs/research/fm17_pre/README.md`](docs/research/fm17_pre/README.md).  
✅ **FM-17-pre v1.3.1 final integrity review:** [`docs/research/fm17_pre/FM17_PRE_V1_3_1_FINAL_INTEGRITY_REVIEW_2026-09-11.md`](docs/research/fm17_pre/FM17_PRE_V1_3_1_FINAL_INTEGRITY_REVIEW_2026-09-11.md).

Exact experiment claims remain subordinate to exact Git state, executable artifacts under `artifacts/memoryops/run_00X/`, experiment code, tests, hashes and receipts.

---

## 🧠 Current research picture

Two lab lanes remain distinct:

1. **Graph-backend smoke / adapter lane** — LadybugDB + SQLite smoke and backend capability probing.
2. **Retrieval-relevance experiment lane** — bounded Graphiti/FalkorDBLite memory experiments with run-specific model/provider evidence.

```text
ONE REPOSITORY ≠ ONE EXPERIMENTAL CLAIM
LAB TEST ≠ UPSTREAM RUNTIME
RESEARCH RESULT ≠ PRODUCTION AUTHORIZATION
```

### 🔬 Retrieval-relevance track

| Experiment | Evidence | Result ceiling | Status |
|---|---|---|---|
| **FM-13** | `artifacts/memoryops/run_004/` | BM25 introduces broad candidates; RRF preserves measured noise; Cross-Encoder was not invoked. | ✅ COMPLETED |
| **FM-14** | `artifacts/memoryops/run_005/` | Real BGE embeddings improve semantic geometry, but active hybrid filtering remains insufficient; Zephyr false positives persist. | ✅ COMPLETED |
| **FM-15** | `artifacts/memoryops/run_006/` | Real local `BAAI/bge-reranker-v2-m3` provides a useful pairwise query↔fact signal on the frozen four-fact fixture. No runtime threshold/gate authorized. | ✅ COMPLETED |
| **FM-16** | `artifacts/memoryops/run_007/` | CE ranks better than embedding on the frozen mixed fixture, but neither score family has one feasible global threshold under the frozen qualification contract. | ✅ CLOSED · `PASS_WITH_MAJOR_INTERPRETATION_FINDINGS` |
| **FM-17-pre** | `docs/research/fm17_pre/` | Protocol/integrity gate for the combined query+fact structural-oracle ceiling. No real annotation or A0–A3 result yet. | 🔐 INTEGRITY READY · `PASS_WITH_MINOR_FINDINGS` · execution not yet authorized |

---

## ✅ FM-16 / run_007 — final bounded status

**Execution SHA:** `62cfa45a80ec83794b701d88873ce136b7629354`  
**START_SHA:** `de304f120a7fdf5bbd1ac020e4333a50a541a219`  
**Upstream pin:** `2437244149baeb0c645e2e942125be92bba3a96b`  
**Independent review verdict:** `PASS_WITH_MAJOR_INTERPRETATION_FINDINGS`

### Frozen task

Per split:

- 40 facts;
- 20 queries;
- 12 answerable + 8 no-answer;
- four broad answerable;
- four nonexistent-entity + four unsupported-predicate no-answer;
- HN1–HN12;
- CAL/TEST entity-disjoint;
- score families: BGE CrossEncoder + BGE embedding baseline.

Frozen CAL feasibility contract:

```text
ANSWERABLE_QUERY_COVERAGE = 1.0
GOLD_PAIR_RECALL >= 0.90
NO_ANSWER_EMPTY_ACCURACY = 1.0
BROAD_QUERY_GOLD_RECALL >= 0.90
```

### Independently reproduced ranking metrics

| Metric | CE CAL | Embedding CAL | CE TEST | Embedding TEST |
|---|---:|---:|---:|---:|
| MRR | 0.958333 | 0.916667 | 0.916667 | 0.861111 |
| P@1 | 0.916667 | 0.833333 | 0.833333 | 0.750000 |
| P@3 | 0.527778 | 0.527778 | 0.527778 | 0.527778 |
| R@3 | 0.884722 | 0.884722 | 0.884722 | 0.884722 |
| Perfect separation | 0.833333 | 0.666667 | 0.833333 | 0.750000 |
| Mean HN margin | 0.145467 | 0.020765 | 0.227392 | 0.031104 |

Safe bounded comparison:

```text
CE_VS_EMBEDDING_RANKING = CE_BETTER
```

This does not establish universal CrossEncoder superiority.

### Global-threshold result

| Family | Candidate thresholds | Feasible | theta |
|---|---:|---:|---:|
| CE | 1,599 | 0 | `null` |
| Embedding | 1,601 | 0 | `null` |

The candidate counts are explained by CAL score boundaries + adjacent midpoints + endpoint sentinels with duplicate collapsing.

Strongest safe claim:

> Under the frozen FM-16 corpus, score families and mixed-query feasibility constraints, neither the raw BGE CrossEncoder score nor the embedding score supports one feasible global threshold.

```text
PAIRWISE / RANKING SIGNAL USEFUL
≠
GLOBAL ABSOLUTE QUALIFICATION FEASIBLE
```

---

## 🎯 Strict H1 clarification

A later hardened interpretation defines strict H1 as positive minimum-gold minus maximum-hard-negative margin for **every** applicable answerable query.

Because perfect separation is below 1.0:

```text
RETROSPECTIVE_STRICT_H1_CE = FAIL
RETROSPECTIVE_STRICT_H1_EMBEDDING = FAIL
```

This is not evidence that CE is useless. It means useful ranking does not imply universal perfect separation. Historical `CASE B` language is semantically ambiguous across protocol versions.

---

## 🏷️ `NO_MATERIAL_GAIN` correction

The original comparator can return `NO_MATERIAL_GAIN` when both score families have `theta = null`.

That is defensible only on the global-threshold axis. It is too broad as an overall CE-vs-embedding verdict.

Use:

```text
CE_VS_EMBEDDING_RANKING = CE_BETTER
CE_VS_EMBEDDING_GLOBAL_QUALIFICATION = BOTH_INFEASIBLE
CE_VS_EMBEDDING_OVERALL = MIXED
```

---

## 🧩 CQ11 / TQ11 gold-history resolution

The initial source literals contain five broad gold facts. Later in the same executable module, before preregistration/scoring, effective gold is explicitly adjusted:

```text
CQ11 → CF21, CF22, CF24
TQ11 → TF21, TF22, TF24
```

Frozen gold, preregistration and scoring labels use the adjusted sets.

```text
INITIAL SOURCE LITERAL ≠ FINAL EFFECTIVE GOLD
FINAL EFFECTIVE GOLD = FROZEN GOLD = SCORING GOLD
```

Therefore no critical source-vs-artifact gold mismatch is established. The mutation-based source representation is confusing and HN9 scope remains scientifically important (`PARTIAL`).

---

## ⚠️ Held-out chronology limitation

The threshold-search computation itself uses CAL only and there is no evidence that TEST scores changed theta. However executable `run_fm16()` computes TEST scores before the CAL threshold/null freeze.

Actual order:

```text
preregistration
→ CE CAL scoring
→ CE TEST scoring
→ FM-15 anchor scoring
→ embedding CAL scoring
→ embedding TEST scoring
→ write CAL/TEST score CSVs
→ compute CAL/TEST pre-threshold ranking
→ CAL-only threshold search
→ theta/null freeze
→ threshold application to TEST
```

Therefore:

```text
CAL_ONLY_THRESHOLD_SELECTION = YES
EVIDENCE_TEST_CHANGED_THETA = NO
THRESHOLD_APPLICATION_TO_TEST_AFTER_FREEZE = YES
TEST_SCORES_EXISTED_BEFORE_THETA_FREEZE = YES
STRICT_BLIND_HELDOUT_ORDER = NOT_SATISFIED
```

This does **not** invalidate the CAL-only mathematical finding that there are zero feasible thresholds. It does limit any claim that `run_007` satisfied the later hardened strict-blind sequencing rule.

---

## 🌐 Broad-query heterogeneity

FM-16 deliberately mixes:

- narrow direct-answer queries;
- paraphrases;
- broad exploratory/context queries;
- no-answer queries.

That is a valid bounded test of the mixed-task global-threshold hypothesis. It is not strong evidence that the same result must hold for a homogeneous direct-answer-only task.

```text
MIXED_TASK_EXPERIMENT_VALID = YES
GLOBAL_THRESHOLD_ON_THIS_MIXED_TASK = NOT_FEASIBLE
GENERALIZATION_TO_DIRECT_ANSWER_ONLY = LIMITED / OPEN
```

Broad-query heterogeneity is an important limitation/inference, not proof that all global thresholds are impossible.

---

## 🧪 Independent review reconciliation

- **Manus:** strongest full artifact-level review; independently recomputed frozen metrics and threshold search; verdict `PASS_WITH_MAJOR_INTERPRETATION_FINDINGS`.
- **Grok:** full repository follow-up reproduced the numerical core and ranking/global-gate split. Its statement that TEST scores were generated after theta freeze is superseded by direct executable-order inspection.
- **DeepSeek:** initial access-limited pass correctly refused to fabricate; later partial-access pass independently confirmed the calibration core.
- **Qwen:** access-limited review correctly returned `REVIEW_INCONCLUSIVE`; this is not evidence against FM-16.
- **Mistral:** broadly agreed on the main result but incorrectly promoted the initial CQ11/TQ11 source literal to a critical gold mismatch and included some metric/reproducibility errors; those claims are not adopted.

Reconciled status:

```text
FM16_REVIEW_VERDICT = PASS_WITH_MAJOR_INTERPRETATION_FINDINGS
NUMERICAL_CORE = INDEPENDENTLY_REPRODUCED
CRITICAL_INTEGRITY_FINDING = NONE ESTABLISHED
```

---

## ✅ Established / observed in bounded scope

```text
FM-13 search-path diagnosis = COMPLETED
FM-14 real-embedding differential = COMPLETED
FM-15 pairwise CE signal = CONFIRMED_ON_FIXTURE
FM-16 run_007 = CLOSED_BOUNDED_EXPERIMENT
FM-16 CE ranking vs embedding = CE_BETTER_ON_FROZEN_FIXTURE
FM-16 CE global theta = NOT_FEASIBLE
FM-16 embedding global theta = NOT_FEASIBLE
FM-16 theta values = null / null
FM-16 retrospective strict H1 = FAIL / FAIL
FM-16 Honest Empty = NOT_ESTABLISHED
```

---

# 🔐 FM-17-pre — current frontier after FM-16

FM-17-pre is a **new bounded research hypothesis**, not a retroactive extension of FM-16 and not an architecture decision.

Its primary question is:

> If query structural interpretation plus fact structural representation were oracle-correct, would that typed structure add measurable qualification value beyond the frozen CE-only baseline, and would structural→CE residual ranking preserve useful evidence better than structure alone?

Planned arms:

```text
A0 = frozen CE baseline
A1 = structural oracle ACCEPT / REJECT / UNRESOLVED
A2 = structural qualification → CE residual ranking
A3 = ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC only
```

Scientific status remains:

```text
STRUCTURAL_VALUE = NOT_ESTABLISHED
QUERY_UNDERSTANDING = NOT_ESTABLISHED
EXTRACTION_ACCURACY = NOT_ESTABLISHED
HONEST_EMPTY = NOT_ESTABLISHED
MULTI_HOP = NOT_PROVEN
```

### Integrity-hardening lineage

```text
469fe64  initial protocol freeze
→ 8aebf70  Measurement Charter
→ bcad493  v1.1 anti-leakage / claim-boundary repair
→ 914ea5c  v1.2 fail-closed schema gate
→ f091ba2  v1.3 package completeness + A/B disagreement + actual SHA-256
→ 080e195  v1.3.1 mandatory external pre-overlay expected root
→ independent Manus final meta-gate review
```

**Final reviewed implementation SHA:** `080e1959fe6a3d996f2690059fcdc687dd5c832e`

Final independent integrity result:

```text
VERDICT = PASS_WITH_MINOR_FINDINGS
GO_FOR_OFFLINE_ABLATION = YES  [INTEGRITY / PROTOCOL VERDICT ONLY]
EXTERNAL_ROOT_REQUIRED = YES
PACKAGE_SELF_AUTHORIZATION = CLOSED
FULL_PACKAGE_PLUS_ROOT_REPLACEMENT = REJECTED
T27 = PASS
T28 = PASS
T29 = PASS
P7 = PASS
FULL_TEST_SUITE = 40 passed, 1 warning
PRE_OVERLAY_EXTERNAL_ANCHOR_PROCEDURE = SUFFICIENT
NEW_R1_R2_R3_MATERIAL_BYPASSES = []
ENFORCEMENT_COMPLEXITY_EXHAUSTED = YES
```

Final trust boundary:

```text
EXTERNAL_R0
=
PACKAGE_LOCAL_ROOT
=
ACTUAL_RECOMPUTED_ROOT
```

The package-local root is consistency/audit state only. It is not authority and cannot be used as an implicit fallback.

Required future execution order, if separately authorized:

```text
BLIND ANNOTATION
→ INDEPENDENT A/B SUBMISSION
→ ADJUDICATION
→ STRUCTURAL PACKAGE FINALIZED
→ HASH ROOT R0 COMPUTED
→ R0 RECORDED OUTSIDE PACKAGE
→ FREEZE
→ ONLY THEN EVALUATION OVERLAY
→ VALIDATE AGAINST PREVIOUSLY RECORDED EXTERNAL R0
→ A0–A3 ONLY AFTER INTEGRITY PASS
```

Accepted residual risks:

- validator cannot independently prove when/by whom `R0` was recorded;
- R0 recording/transport is procedural rather than PKI/signature/timestamp authenticated;
- unrelated pytest `asyncio_mode` warning is non-enforcement noise.

These were not classified by the final independent review as new material R1+R2+R3 bypasses for this bounded offline protocol.

Methodology findings:

```text
PASSING TEST SUITE ≠ THREAT MODEL COMPLETE
HASH FIELD PRESENT ≠ HASH VERIFIED
INTERNAL HASH CONSISTENCY ≠ PRE-OVERLAY FREEZE AUTHENTICITY
VALIDATOR PASS ≠ EXPERIMENT SUCCESS
```

The meta-gate for future enforcement findings is risk-based: block only if `R1 concrete path + R2 realistic + R3 material consequence` all hold. Otherwise record residual risk rather than reopen speculative hardening.

---

## ❌ Explicitly NOT established / NOT authorized

| Claim | Status |
|---|---|
| Neo4j parity for FalkorDBLite memory experiments | ❌ NOT ESTABLISHED |
| Production/general Fractal relevance gate | ❌ NOT IMPLEMENTED / NOT AUTHORIZED |
| Production/global calibrated CE threshold | ❌ NOT AVAILABLE / NOT AUTHORIZED |
| `NO_RELEVANT_MEMORY` runtime semantics | ❌ NOT IMPLEMENTED |
| Honest Empty as solved runtime behavior | ❌ NOT ESTABLISHED |
| CrossEncoder superiority in general | ❌ NOT ESTABLISHED |
| Global thresholds never work | ❌ NOT ESTABLISHED |
| Structural filtering required | ❌ NOT ESTABLISHED |
| LLM recognition required | ❌ NOT ESTABLISHED |
| Memory-specific SLM required | ❌ NOT ESTABLISHED |
| Graph/path scoring required | ❌ NOT ESTABLISHED |
| Query routing required | ❌ NOT ESTABLISHED |
| Multi-hop reasoning | ❌ NOT PROVEN LOCALLY |
| Runtime CE / production `reranker_min_score` | ❌ NOT AUTHORIZED |
| Architecture promotion | ❌ NOT AUTHORIZED |
| Upstream/product change | ❌ NOT AUTHORIZED |
| FM-17-pre real annotation | ❌ NOT EXECUTED / NOT YET AUTHORIZED |
| FM-17-pre evaluation overlay | ❌ NOT EXPOSED |
| FM-17-pre A0–A3 scientific result | ❌ NOT EXECUTED |

---

## 🛡️ Core research invariants

```text
RESEARCH ≠ RUNTIME
TESTED ≠ PRODUCTION AUTHORIZED
RETRIEVED ≠ RELEVANT
RELEVANT ≠ SUPPORTS_POSITIVE_PROPOSITION
DIRECT ANSWER ≠ MULTI-HOP COMPONENT ≠ RELATED CONTEXT
NARROW FACTOID RELEVANCE ≠ BROAD ASSOCIATIVE RELEVANCE
PAIRWISE RANKING SIGNAL ≠ GLOBAL QUALIFICATION
GLOBAL THRESHOLD FAILURE ≠ RANKER USELESSNESS
RELEVANCE ≠ EVIDENCE ≠ TRUTH
NO_RELEVANT_RESULT ≠ ENTITY ABSENT
NOT RETRIEVED ≠ ABSENT
UNKNOWN ≠ FALSE
TEMPORAL APPLICABILITY ≠ SEMANTIC RELEVANCE
SCORER FAILURE ≠ HONEST EMPTY
VALIDATOR PASS ≠ EXPERIMENT SUCCESS
GO_FOR_OFFLINE_ABLATION ≠ ABLATION EXECUTED
LAB ≠ PRODUCT
```

---

## 🔍 Historical path and current frontier

```text
FM-13
→ diagnose actual retrieval path

FM-14
→ test real embeddings

FM-15
→ isolate real CE pairwise signal

FM-16
→ test mixed-task ranking + one-global-threshold feasibility
→ CE ranking better than embedding on frozen fixture
→ no feasible global theta for either family
→ bounded forensic closure

FM-17-pre
→ new structural-oracle ceiling hypothesis
→ protocol + anti-leakage + fail-closed integrity hardening
→ external pre-overlay root added
→ independent integrity/meta-gate review PASS_WITH_MINOR_FINDINGS
→ INTEGRITY GATE READY
→ SCIENTIFIC ABLATION STILL NOT EXECUTED
```

For FM-16 history, read [`docs/research/FM16_CLOSURE_AND_INDEPENDENT_REVIEW_2026-09-11.md`](docs/research/FM16_CLOSURE_AND_INDEPENDENT_REVIEW_2026-09-11.md).  
For current FM-17-pre protocol state, read [`docs/research/fm17_pre/README.md`](docs/research/fm17_pre/README.md), [`docs/research/fm17_pre/STOP_BOUNDARY.md`](docs/research/fm17_pre/STOP_BOUNDARY.md), and [`docs/research/fm17_pre/FM17_PRE_V1_3_1_FINAL_INTEGRITY_REVIEW_2026-09-11.md`](docs/research/fm17_pre/FM17_PRE_V1_3_1_FINAL_INTEGRITY_REVIEW_2026-09-11.md).

---

## 🧭 Current bounded next action

The FM-16 closure itself stays closed. FM-17-pre now exists as a separate new research frontier whose integrity gate has passed independent review.

The next action, **only after separate explicit user authorization**, is:

```text
BLINDED A/B ANNOTATION
→ ADJUDICATION
→ EXTERNAL R0 FREEZE
→ POST-FREEZE EVALUATION OVERLAY
→ INTEGRITY VALIDATION AGAINST HELD R0
→ ONE-SHOT A0/A1/A2/A3 OFFLINE ABLATION
→ BOUNDED INTERPRETATION
```

Until that authorization:

```text
STOP
NO REAL ANNOTATION
NO EVALUATION OVERLAY
NO A0–A3
NO ABLATION
NO MERGE
NO PRODUCT CHANGE
```

---

## 🤖 Machine-readable snapshot

```yaml
repo: velantrian/Graphiti_fractal_lab
scope: research_sandbox
retrieval_relevance_track: FM16_CLOSED_FM17_PRE_INTEGRITY_READY
fm13: COMPLETED
fm14: COMPLETED
fm15: COMPLETED
fm16: CLOSED_BOUNDED_EXPERIMENT
fm16_run_007: COMPLETE
fm16_execution_sha: 62cfa45a80ec83794b701d88873ce136b7629354
fm16_review_verdict: PASS_WITH_MAJOR_INTERPRETATION_FINDINGS
numeric_core_independently_reproduced: true
ce_ranking_vs_embedding: CE_BETTER_ON_FROZEN_FIXTURE
ce_global_threshold_feasible: false
embedding_global_threshold_feasible: false
ce_threshold: null
embedding_threshold: null
ce_threshold_candidates: 1599
embedding_threshold_candidates: 1601
retrospective_strict_h1_ce: FAIL
retrospective_strict_h1_embedding: FAIL
no_material_gain_label: TOO_BROAD_AS_OVERALL_VERDICT
broad_query_heterogeneity: IMPORTANT_LIMITATION
honest_empty_established: false
threshold_selection_uses_cal_only: true
test_scores_existed_before_theta_freeze: true
strict_blind_test_order_satisfied: false
fm17_pre: INTEGRITY_READY_NOT_EXECUTED
fm17_pre_final_reviewed_implementation_sha: 080e1959fe6a3d996f2690059fcdc687dd5c832e
fm17_pre_integrity_verdict: PASS_WITH_MINOR_FINDINGS
fm17_pre_go_for_offline_ablation_protocol: true
fm17_pre_package_self_authorization_closed: true
fm17_pre_full_package_root_replacement_rejected: true
fm17_pre_full_test_suite: "40 passed, 1 warning"
fm17_pre_real_annotation_executed: false
fm17_pre_overlay_exposed: false
fm17_pre_ablation_executed: false
fm17_pre_structural_value_established: false
runtime_relevance_gate: NOT_IMPLEMENTED
runtime_authorized: false
search_recipe_changed: false
architecture_change: false
upstream_runtime_changed_by_research: false
product_changed: false
current_next_action: WAIT_FOR_SEPARATE_USER_AUTHORIZATION_OF_FM17_PRE_OFFLINE_ORACLE_ABLATION
```
