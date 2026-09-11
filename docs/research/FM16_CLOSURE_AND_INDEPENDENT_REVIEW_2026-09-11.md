# 🧠🔬 FM-16 Closure & Independent Review History — 2026-09-11

> **Scope:** `velantrian/Graphiti_fractal_lab` · retrieval-relevance research lane  
> **Reviewed experiment:** `FM-16 / artifacts/memoryops/run_007/`  
> **Execution commit:** `62cfa45a80ec83794b701d88873ce136b7629354`  
> **Start SHA:** `de304f120a7fdf5bbd1ac020e4333a50a541a219`  
> **Upstream pin:** `2437244149baeb0c645e2e942125be92bba3a96b`  
> **Role:** historical closure / interpretation ledger. Exact experiment truth remains subordinate to frozen artifacts, executable source, tests and exact Git state.  
> **Runtime authority:** NONE.

---

## 0. Why this file exists

FM-16 moved through several stages: protocol design, independent protocol critique, hardened task separation, actual execution, and then multiple independent forensic reviews. A future reader must not compress that history into either “CE worked” or “threshold failed.”

The useful result is more precise:

```text
PAIRWISE / RANKING SIGNAL
≠
ABSOLUTE GLOBAL QUALIFICATION
```

FM-16 produced evidence that the CrossEncoder is a stronger ranker than the embedding baseline on the frozen mixed-query fixture, while one raw global threshold is not feasible for either score family under the frozen qualification constraints.

This file records how that conclusion was established, what was later corrected, and what remains explicitly open.

---

## 1. Pre-execution history

FM-13–FM-15 narrowed the question step by step:

```text
FM-13
→ instrument the active path
→ BM25 introduces broad candidates
→ RRF preserves measured noise
→ constructed CrossEncoder was not invoked

FM-14
→ replace deterministic embeddings with real BGE embeddings
→ semantic geometry improves
→ final relevance filtering / honest EMPTY still not solved

FM-15
→ isolate real local BGE CrossEncoder pairwise scoring
→ useful query↔fact signal confirmed on the tiny frozen fixture
→ no generalization / global threshold / runtime authorization established
```

The first FM-16 protocol was then stopped before scoring because independent review found methodological problems. Important corrections included:

```text
RELEVANT ANSWER ≠ SUPPORTS POSITIVE PROPOSITION
DIRECT ANSWER ≠ MULTI-HOP COMPONENT ≠ RELATED CONTEXT
NARROW FACTOID RELEVANCE ≠ BROAD ASSOCIATIVE RELEVANCE
SCORER FAILURE ≠ HONEST EMPTY
```

The research question was split into:

- **H1 — direct ranking:** can the scorer rank direct answers above hard negatives?
- **H2 — global absolute gate:** can one calibration-derived threshold preserve answerable recall while rejecting no-answer / hard-negative cases?
- **H3 — component retrieval:** can the system preserve intermediate facts required for multi-hop/composition? H3 remained separate from primary FM-16.

---

## 2. FM-16 execution / run_007

FM-16 was subsequently executed on the research branch and produced `artifacts/memoryops/run_007/`.

### Frozen design

Per split:

- 40 facts;
- 20 queries;
- 12 answerable;
- 8 no-answer;
- 4 broad answerable;
- 4 nonexistent-entity no-answer;
- 4 unsupported-predicate no-answer;
- HN1–HN12 adversarial strata;
- entity-disjoint CAL / TEST entities;
- two score families only: BGE CrossEncoder and BGE embedding baseline.

Recorded models:

```text
CrossEncoder:
BAAI/bge-reranker-v2-m3
revision 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e
weight SHA-256 d9e3e081faff1eefb84019509b2f5558fd74c1a05a2c7db22f74174fcedb5286

Embedding:
BAAI/bge-small-en-v1.5
LocalSemanticEmbedder / fastembed
```

Frozen CAL feasibility contract:

```text
ANSWERABLE_QUERY_COVERAGE = 1.0
GOLD_PAIR_RECALL >= 0.90
NO_ANSWER_EMPTY_ACCURACY = 1.0
BROAD_QUERY_GOLD_RECALL >= 0.90
```

No forced refill was allowed.

---

## 3. Reproduced numerical result

Independent artifact-level recomputation reproduced the main metrics and threshold search.

### Ranking metrics

| Metric | CE CAL | Embedding CAL | CE TEST | Embedding TEST |
|---|---:|---:|---:|---:|
| MRR | 0.958333 | 0.916667 | 0.916667 | 0.861111 |
| P@1 | 0.916667 | 0.833333 | 0.833333 | 0.750000 |
| P@3 | 0.527778 | 0.527778 | 0.527778 | 0.527778 |
| R@3 | 0.884722 | 0.884722 | 0.884722 | 0.884722 |
| Perfect separation | 0.833333 | 0.666667 | 0.833333 | 0.750000 |
| Mean hard-negative margin | 0.145467 | 0.020765 | 0.227392 | 0.031104 |

The safe interpretation is:

```text
CE_VS_EMBEDDING_RANKING = CE_BETTER
```

This is a bounded fixture result, not a universal claim that CrossEncoders outperform embeddings in every memory workload.

### Global threshold search

| Family | Candidate thresholds | Feasible | Selected theta |
|---|---:|---:|---:|
| CrossEncoder | 1,599 | 0 | `null` |
| Embedding | 1,601 | 0 | `null` |

Therefore:

```text
CE_GLOBAL_THRESHOLD_FEASIBLE = NO
EMBEDDING_GLOBAL_THRESHOLD_FEASIBLE = NO
THETA_CE = null
THETA_EMBEDDING = null
```

The candidate counts are explained by the executable search implementation: unique CAL score boundaries + midpoints between adjacent unique scores + two endpoint sentinels, with duplicate collapsing. The counts are not evidence that TEST scores entered threshold selection.

---

## 4. Why the global threshold failed

The conflict is not “the CrossEncoder has no signal.” It has useful ranking signal. The problem is absolute qualification across heterogeneous query classes.

On CAL, some broad-query gold facts receive very low CE scores around `0.004`, while a no-answer query can have a maximum candidate score around `0.273`.

Conceptually:

```text
raise theta enough to empty every no-answer query
→ lose some broad gold

lower theta enough to preserve broad gold
→ some no-answer candidates survive
```

Under the frozen joint constraints, no single theta satisfies both obligations.

Strongest safe claim:

> Under the frozen FM-16 corpus, score families and mixed-query feasibility constraints, neither the raw BGE CrossEncoder score nor the embedding score supports one feasible global threshold.

Do **not** generalize this into “global thresholds never work.”

---

## 5. Strict H1 clarification

A later hardened interpretation defines strict H1 as positive separation for every applicable answerable query:

```text
min(gold score) - max(primary hard-negative score) > 0
for every query
```

Observed perfect-separation rates are below 1.0, so under that later strict definition:

```text
STRICT_H1_CE = FAIL
STRICT_H1_EMBEDDING = FAIL
```

This does not contradict the useful ranking result. It means:

```text
USEFUL RANKER ≠ UNIVERSALLY PERFECT SEPARATOR
```

The original run_007 reporting treated perfect separation as a rate rather than as a binary 100% gate. Therefore old `CASE B` wording is semantically ambiguous across protocol versions and should not be read as proof that the later strict-H1 criterion passed.

---

## 6. `NO_MATERIAL_GAIN` correction

The original comparator can return `NO_MATERIAL_GAIN` when both score families have `theta = null`.

That label is valid only on the **global-threshold qualification axis**.

It is too broad if read as an overall model comparison, because CE has better ranking metrics.

Use the decomposed form:

```text
CE_VS_EMBEDDING_RANKING = CE_BETTER
CE_VS_EMBEDDING_GLOBAL_QUALIFICATION = BOTH_INFEASIBLE / NO_MATERIAL_ADVANTAGE
CE_VS_EMBEDDING_OVERALL = MIXED
```

---

## 7. CQ11 / TQ11 gold-history resolution

Several reviewers initially flagged a possible source-vs-artifact gold mismatch because the query literals are first declared with five broad gold facts.

However the same executable module later explicitly adjusts the effective gold before preregistration/scoring:

```text
CQ11 → CF21, CF22, CF24
TQ11 → TF21, TF22, TF24
```

The frozen `calibration_gold.json`, `test_gold.json`, preregistration and score `gold_relevant` flags use those adjusted sets.

Final status:

```text
INITIAL SOURCE LITERAL ≠ FINAL EFFECTIVE GOLD
FINAL EFFECTIVE GOLD = FROZEN GOLD = SCORING GOLD
```

Therefore there is **no critical experiment-integrity gold mismatch**. The source representation is confusing / mutation-based and is worth documenting, but it does not invalidate the run.

HN9 scope remains scientifically important: scope-mismatched facts can still outrank some intended gold, and HN9 was `PARTIAL` rather than `PASS`.

---

## 8. Held-out chronology — important methodological limitation

This is the main chronology nuance that must remain visible in the historical record.

The threshold-search function itself uses **CAL only**, and there is no evidence that TEST scores were used to select theta.

However the executable `run_fm16()` order is:

```text
preregistration
→ CE CAL scoring
→ CE TEST scoring
→ FM-15 anchor scoring
→ embedding CAL scoring
→ embedding TEST scoring
→ write CAL/TEST score CSVs
→ compute CAL/TEST pre-threshold ranking metrics
→ search threshold on CAL only
→ freeze theta/null
→ apply frozen theta/null to TEST qualification
```

Therefore:

```text
CAL_ONLY_THRESHOLD_SELECTION = YES
THRESHOLD_CHANGED_AFTER_TEST = NO EVIDENCE
THRESHOLD_APPLICATION_TO_TEST_AFTER_FREEZE = YES

BUT

TEST_SCORES_EXISTED_BEFORE_THETA_FREEZE = YES
STRICT_BLIND_HELDOUT_ORDER = NOT_SATISFIED
```

This does **not** invalidate the core mathematical statement `0 feasible CAL thresholds`, because that statement is derived from CAL only. It does limit the strength of any claim that run_007 followed the later hardened “freeze before TEST scores exist” discipline.

The one-commit packaging also means the exact historical runtime chronology is not externally/cryptographically attested by Git history alone.

---

## 9. Broad-query heterogeneity

FM-16 intentionally mixes:

- narrow direct-answer queries;
- paraphrases;
- broad exploratory/context queries;
- no-answer queries.

That is a valid bounded test of the **mixed-task global-threshold hypothesis**.

It is not strong evidence that the same result must hold for a homogeneous direct-answer-only workload.

Therefore:

```text
MIXED_TASK_EXPERIMENT_VALID = YES
GLOBAL_THRESHOLD_ON_THIS_MIXED_TASK = NOT_FEASIBLE
GENERALIZATION_TO_DIRECT_ANSWER_ONLY = LIMITED / OPEN
```

Query-intent heterogeneity is a plausible contributor to threshold failure, but it is an inference rather than a universal causal proof.

---

## 10. Independent review history

### Manus

A full read-only forensic review with frozen-score recomputation produced:

```text
PASS_WITH_MAJOR_INTERPRETATION_FINDINGS
```

It reproduced the main ranking metrics, `1599 / 1601` threshold candidates, `0 feasible` thresholds, exact FM-15 anchor, and concluded that `NO_MATERIAL_GAIN` is too broad and strict-H1 fails under the later all-query definition.

### Grok forensic follow-up

A later full-repository audit reached the same overall verdict and reproduced the numeric core. It correctly decomposed ranking versus global qualification and treated the source gold mutation as non-critical.

One statement in that report — that TEST scores were generated after theta freeze — conflicts with the executable source order. The closure record therefore uses the source-derived chronology in §8 above.

### DeepSeek

The first DeepSeek attempt correctly refused to fabricate a forensic verdict without repository access. A later partial-access pass independently confirmed the calibration core (`theta=null`, candidate counts, zero feasible thresholds) but could not inspect all raw score/evaluation artifacts. It is supporting evidence, not the primary full forensic review.

### Qwen

Qwen similarly returned `REVIEW_INCONCLUSIVE` when repository artifacts were unavailable. This was a correct access-limited result and not evidence against FM-16.

### Mistral

Mistral broadly agreed with the numerical/global-threshold conclusion and with the `NO_MATERIAL_GAIN` / strict-H1 interpretation findings, but it incorrectly elevated the CQ11/TQ11 initial source literal into a critical gold mismatch and also contained metric/reproducibility inconsistencies. Those specific claims are not adopted into the closure verdict.

### Reconciled review status

```text
FM16_REVIEW_VERDICT = PASS_WITH_MAJOR_INTERPRETATION_FINDINGS
NUMERICAL_CORE = INDEPENDENTLY_REPRODUCED
CRITICAL_INTEGRITY_FINDING = NONE ESTABLISHED
```

---

## 11. What FM-16 established

```yaml
fm16:
  status: CLOSED_BOUNDED_EXPERIMENT
  run: run_007
  execution_sha: 62cfa45a80ec83794b701d88873ce136b7629354
  independent_review: PASS_WITH_MAJOR_INTERPRETATION_FINDINGS

  ce_ranking_vs_embedding: CE_BETTER_ON_FROZEN_FIXTURE
  ce_global_threshold_feasible: false
  embedding_global_threshold_feasible: false
  ce_threshold: null
  embedding_threshold: null

  retrospective_strict_h1_ce: FAIL
  retrospective_strict_h1_embedding: FAIL

  no_material_gain_label: TOO_BROAD_AS_OVERALL_VERDICT
  honest_empty_established: false
  broad_query_heterogeneity: IMPORTANT_LIMITATION

  threshold_selection_uses_cal_only: true
  strict_blind_test_order_satisfied: false

  runtime_gate_implemented: false
  runtime_authorized: false
  search_recipe_changed: false
  architecture_changed: false
  upstream_changed: false
  merge: false
```

---

## 12. What FM-16 did NOT establish

FM-16 does not establish any of the following:

```text
GLOBAL THRESHOLDS NEVER WORK
CROSSENCODER IS USELESS
CROSSENCODER IS UNIVERSALLY SUPERIOR
HONEST EMPTY IS SOLVED
STRUCTURAL FILTERING IS REQUIRED
LLM RECOGNITION IS REQUIRED
MEMORY-SPECIFIC SLM IS REQUIRED
GRAPH/PATH SCORING IS REQUIRED
QUERY ROUTING IS REQUIRED
MULTI-HOP IS PROVEN
RUNTIME CE GATING IS AUTHORIZED
PRODUCTION reranker_min_score IS AUTHORIZED
ARCHITECTURE PROMOTION IS AUTHORIZED
```

---

## 13. Research consequence

FM-16 rules out one simple hypothesis **on this frozen mixed task**:

> A good generic semantic scorer plus one raw global threshold is sufficient to handle ranking, rejection and honest EMPTY across the tested query classes.

That hypothesis is **not supported by FM-16**.

The next research question is no longer “what magic threshold should we tune?” It becomes:

```text
Which minimal mechanism removes the remaining error class?
```

Candidate future mechanisms may include structural qualification, query-class-conditioned qualification, learned residual relevance, LLM/SLM recognition, graph/path reasoning, or other selective/abstention mechanisms. None is promoted by this file.

The separate research program should ask for each candidate:

```text
Which error class does it remove?
Which error class remains?
What assumptions does it add?
Can it preserve DIRECT ANSWER and COMPONENT distinctions?
Can its EMPTY decision be audited?
```

---

## 14. Closure boundary

```text
FM-16 = CLOSED AS BOUNDED EXPERIMENT

NO FM-17 FROM THIS CLOSURE
NO NEW SCORE FAMILY FROM THIS CLOSURE
NO RUNTIME CHANGE
NO SEARCH RECIPE CHANGE
NO PRODUCT CHANGE
NO UPSTREAM CHANGE
NO ARCHITECTURE PROMOTION
```

The only authorized consequence of this closure is documentation / metadata clarification of the research record.

---

## 15. Evidence routing

Primary evidence:

- `artifacts/memoryops/run_007/preregistration.json`
- `artifacts/memoryops/run_007/scores/`
- `artifacts/memoryops/run_007/calibration/`
- `artifacts/memoryops/run_007/evaluation/`
- `artifacts/memoryops/run_007/hashes/`
- `artifacts/memoryops/run_007/result.json`
- `src/fractal_lab/experiments/fm16_generalization.py`
- `tests/lab/test_memoryops_fm16_generalization.py`
- execution commit `62cfa45a80ec83794b701d88873ce136b7629354`

Context / history:

- `docs/research/RETRIEVAL_RELEVANCE_TRACK.md`
- `docs/research/RETRIEVAL_RELEVANCE_REASONING_LOG.md`
- this closure file

Authority reminder:

```text
NARRATIVE ≠ EXECUTABLE EVIDENCE
REVIEWER VERDICT ≠ RAW ARTIFACT
MODEL OUTPUT ≠ CANON
TESTED ≠ PRODUCTION AUTHORIZED
```
