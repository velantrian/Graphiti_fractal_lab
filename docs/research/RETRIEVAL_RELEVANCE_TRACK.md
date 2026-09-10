# 🔬 Graphiti Fractal Lab — Retrieval Relevance Research Track

> **Status:** CURRENT RESEARCH TRACK  
> **Scope:** `velantrian/Graphiti_fractal_lab` · branch `experiment/falkordblite-deterministic-memory`  
> **Updated:** 2026-09-10  
> **Evidence authority:** exact Git state + executable artifacts under `artifacts/memoryops/run_00X/`  
> **Runtime authority:** NONE — this document does not activate or authorize Fractal runtime changes.

## 🤖 AI / human short rule

Read this file to understand **why the experiments exist and what they established**. For a factual experiment claim, open the linked `result.json`, score matrix, pytest receipt, model fingerprint, and exact commit. Narrative summary is navigation, not proof.

```text
RESEARCH SUMMARY ≠ EXECUTABLE EVIDENCE
LAB RESULT ≠ PRODUCTION AUTHORIZATION
RETRIEVAL ≠ RELEVANCE ≠ EVIDENCE ≠ TRUTH
NO_RELEVANT_RESULT ≠ ENTITY_PROVEN_ABSENT
```

## 🎯 Research question

The active Fractal/Graphiti retrieval family can generate broad candidates, but a nonblank query can still surface comparatively high-ranked facts that do not actually answer the query. The research track therefore asks:

```text
broad candidates
      ↓
query ↔ candidate relevance discrimination
      ↓
retain / reject
      ↓
possibly honest EMPTY
```

This is a **query-time relevance** problem. It is not a storage, provenance, Canon, belief, permission, or temporal-authority problem.

## 📍 Current frontier

| Stage | Question | Evidence-bound result | Status |
|---|---|---|---|
| FM-13 | Where does measured retrieval noise first enter? | BM25 introduces broad candidates; RRF preserves them; CE was not invoked. | ✅ COMPLETED |
| FM-14 | Are real semantic embeddings alone sufficient? | Real BGE geometry improves, but final hybrid filtering remains insufficient; Zephyr still returns four false positives. | ✅ COMPLETED |
| FM-15 | Does a real pairwise Cross-Encoder provide a useful query↔fact signal? | Yes on the frozen 4-fact fixture. Strong pairwise discrimination observed; no threshold/runtime gate authorized. | ✅ COMPLETED |
| FM-16 | Does the CE signal generalize to unseen entities/adversarial hard negatives, and can one calibration-only global threshold survive held-out test? | Not run yet. | ⏳ PLANNED / NOT_RUN |

**Current next question:** FM-16 generalization + calibration. Do not skip directly to runtime integration.

---

## FM-13 — Search-path diagnosis

**Evidence:** `artifacts/memoryops/run_004/`

Primary receipt: [`../../artifacts/memoryops/run_004/result.json`](../../artifacts/memoryops/run_004/result.json)

Observed on the frozen Q1–Q5 fixture:

- effective path was Graphiti edge hybrid BM25 + cosine → RRF;
- `cross_encoder_calls_total = 0`;
- Q4 `Who works on Project Zephyr?` had no gold-relevant facts but returned all four stored facts;
- MemoryOps was pass-through for the measured edge ordering/facts;
- artifact classification: `FIRST_DEGRADATION_LAYER = BM25_CANDIDATE_GENERATION`.

Interpretation ceiling:

> Broad BM25 candidate generation is not itself a defect; the observed failure is that later fusion/selection did not reject query-irrelevant candidates on this fixture.

The artifact labels Q5 as `MULTI_HOP`; this research ledger uses the stricter interpretation **CO_RETRIEVAL_ONLY / MULTI_HOP_REASONING_NOT_PROVEN** because no direct Alice→Python fact or executed reasoning proof was established.

---

## FM-14 — Real embedding differential

**Evidence:** `artifacts/memoryops/run_005/`

Primary receipt: [`../../artifacts/memoryops/run_005/result.json`](../../artifacts/memoryops/run_005/result.json)

One experimental variable changed from deterministic embeddings to a real local semantic embedder (`BAAI/bge-small-en-v1.5`). Extraction control passed.

Result:

- Q1–Q3 macro `Precision@1 = 1.0`, `Recall@3 = 1.0`, `MRR = 1.0`;
- lower-rank noise remained (`Precision@3 = 0.4444`, `Precision@4 = 0.3333`);
- Q4 Zephyr still returned four unrelated facts;
- artifact conclusion: `EMBEDDING_IMPROVEMENT_CONFIRMED BUT SEARCH_PIPELINE_FILTERING_STILL_INSUFFICIENT`;
- `NEO4J_CAUSAL_EVIDENCE = NO`.

Claim boundary:

```text
REAL EMBEDDINGS IMPROVED GEOMETRY
≠
REAL EMBEDDINGS SOLVED FINAL RELEVANCE FILTERING
```

The full FM-14 pairwise cosine matrix happened to be separable for the tiny fixture, so later CE work must not claim that embeddings had zero separability. The problem was the active hybrid retrieval result and generalization, not merely existence of a possible toy threshold.

---

## FM-15 — Real Cross-Encoder separability

**Evidence:** `artifacts/memoryops/run_006/`

Primary artifacts:

- [`../../artifacts/memoryops/run_006/result.json`](../../artifacts/memoryops/run_006/result.json)
- [`../../artifacts/memoryops/run_006/cross_encoder_score_matrix.json`](../../artifacts/memoryops/run_006/cross_encoder_score_matrix.json)
- [`../../artifacts/memoryops/run_006/model_fingerprint.json`](../../artifacts/memoryops/run_006/model_fingerprint.json)
- [`../../artifacts/memoryops/run_006/pytest.txt`](../../artifacts/memoryops/run_006/pytest.txt)

Real local scorer:

```text
model: BAAI/bge-reranker-v2-m3
revision: 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e
weight_sha256: d9e3e081faff1eefb84019509b2f5558fd74c1a05a2c7db22f74174fcedb5286
Graphiti client: BGERerankerClient
pair_count: 20
runtime search CE: OFF
threshold tuning: NONE
```

Observed CE matrix highlights:

| Query | Gold / relevant behavior | Hard-negative / no-answer behavior |
|---|---|---|
| Q1 `Who works on Project Orion?` | F1 `0.974169` | best non-gold `0.030276` |
| Q2 `What language does Project Orion use?` | F2 `0.997204` | best non-gold `0.013468` |
| Q3 `What is related to Project Nova?` | F3 `0.049960`, F4 `0.032244` | best non-gold ≈ `0.000021` |
| Q4 `Who works on Project Zephyr?` | gold = ∅ | max candidate `0.007880` |

FM-15 therefore established a **useful pairwise query↔fact relevance signal on this frozen fixture**. Q4 candidates were below every Q1–Q3 gold positive, but the observed interval is fixture-only and not a production threshold.

Important correction / non-claim:

- FM-14 embeddings were also mathematically separable on this tiny pair matrix;
- CE gave much sharper Q1/Q2 discrimination, while Q3 valid broad-query scores were low in absolute terms;
- cosine and CE sigmoid scores live on different scales, so raw margin magnitude must not be compared as if directly commensurate;
- `NEW_SEPARABILITY_VS_EMBEDDINGS = NOT_ESTABLISHED`;
- `PAIRWISE_CE_SIGNAL = CONFIRMED_ON_FIXTURE`.

FM-15 test receipt: **14 passed, 1 warning** in the recorded run.

### FM-15 bookkeeping note

Implementation commit and later bookkeeping HEAD are different concepts. Do not create self-referential `END_SHA` bookkeeping. Future runs should report an externally observed `FINAL_HEAD_SHA` rather than attempting to write a commit's own SHA into itself.

---

## FM-16 — Generalization + calibration plan

**Status:** `PLANNED / NOT_RUN`.

The planned experiment must not simply re-run FM-15. It is intended to test whether the CE signal survives a larger, entity-disjoint held-out corpus and adversarial semantic near-misses.

Core design:

- FM-15 anchor for regression only;
- calibration: 40 facts / 20 queries;
- held-out test: 40 different facts / 20 different queries;
- calibration and test entities disjoint;
- each split: 12 answerable + 8 no-answer queries;
- compare exactly two score families: real BGE embedding cosine vs real BGE Cross-Encoder;
- threshold may be selected **only** on calibration and frozen before held-out test;
- no forced refill after all candidates fail qualification;
- no runtime integration in FM-16.

Required adversarial hard-negative families include:

1. same entity / wrong predicate;
2. same predicate / wrong entity;
3. lexical overlap / wrong answer;
4. semantically related / wrong relation;
5. near-name entity collision;
6. unrelated;
7. negation / polarity;
8. temporal or version mismatch in text;
9. scope mismatch;
10. condition mismatch;
11. attribution/source mismatch;
12. numeric/unit/direction mismatch.

This design is meant to attack the scorer with facts that look similar but are semantically wrong, not merely random negatives.

---

## 🧩 Donor map — research context only

These references inform **tests, interfaces, or failure modes**. They are not adopted Fractal runtime components.

| Donor | Useful lesson | Boundary |
|---|---|---|
| 🗿 Titan | `selected/discarded + reason`, thresholded attention shape, typed no-signal precedent, narrow FactsPack negative-control guard | Titan trust/confidence/risk/epistemic policy must not become Fractal relevance authority. |
| 💠 Crystal | preregistered hard-negative/no-recall-loss evaluation discipline; adversarial strata | Canon/evidence admission is not query relevance. |
| 🧬 Native Kernel | relevance/similarity/rank must not independently establish epistemic validity; UNKNOWN ≠ FALSE | invariant donor only. |
| 🦞 OpenClaw | broad candidate window, separate ranking signals, index identity; real recall-vs-threshold tension | lexical fallback after a failed strict score can defeat honest EMPTY; do not copy thresholds. |
| 🔬 SVL | applicability/UNKNOWN/fail-closed validation pattern | temporal applicability ≠ semantic query relevance. |
| EITI | small empty-capable selectors and forced-top-k/fallback as a negative example | never refill rejected candidates merely to guarantee output count. |
| 🕸 Fractal experience applicability | already demonstrates `retrieved ≠ applicable`, per-candidate receipt and all-rejected output inside Fractal | tool/environment compatibility predicate ≠ general semantic relevance predicate. |

```text
DONOR_REFERENCE ≠ ADOPTED_RUNTIME
SIMILAR GATE SHAPE ≠ SHARED OWNER
```

## 🛡️ Research invariants

```text
RESEARCH ≠ RUNTIME
TESTED ≠ PRODUCTION AUTHORIZED
RETRIEVED ≠ RELEVANT
RELEVANCE ≠ EVIDENCE
RELEVANCE ≠ TRUTH
EVIDENCE ≠ BELIEF
BELIEF ≠ TRUTH
MODEL/JUDGE SCORE ≠ AUTHORITY
NO_RELEVANT_RESULT ≠ FACT FALSE
NO_RELEVANT_RESULT ≠ ENTITY ABSENT
NOT RETRIEVED ≠ ABSENT
TEMPORAL APPLICABILITY ≠ SEMANTIC RELEVANCE
```

## 📚 Evidence routing

For this research family use this order:

```text
exact branch / exact commit
  > run-specific executable artifacts + pytest receipts
  > lab experiment code
  > RESEARCH_STATUS.md
  > this explanatory track
  > external/cross-project donor summaries
```

Never reverse this order because a narrative is easier to read.

## 🤖 Machine-readable current summary

```yaml
track: retrieval_relevance
scope: Graphiti_fractal_lab
status: IN_PROGRESS
upstream_runtime_changed: false
architecture_change: false
new_relevance_module_justified: false
fm13:
  status: COMPLETED
  finding: BM25_BROAD_CANDIDATES_PLUS_RRF_NO_REJECTION_ON_FIXTURE
fm14:
  status: COMPLETED
  finding: REAL_EMBEDDINGS_IMPROVED_GEOMETRY_BUT_FINAL_FILTERING_INSUFFICIENT
fm15:
  status: COMPLETED
  pairwise_ce_signal: CONFIRMED_ON_FIXTURE
  new_separability_vs_embeddings: NOT_ESTABLISHED
  runtime_gate: NOT_IMPLEMENTED
  threshold_authorized: false
fm16:
  status: PLANNED_NOT_RUN
  question: HELD_OUT_GENERALIZATION_AND_GLOBAL_THRESHOLD_FEASIBILITY
current_next_action: RUN_FM16_AFTER_RESOURCES_AVAILABLE_THEN_STOP_FOR_INDEPENDENT_REVIEW
```

## ⛔ Stop boundary

Until FM-16 evidence exists, do not infer that a Cross-Encoder should be activated in Fractal runtime, do not choose a production `reranker_min_score`, do not implement `NO_RELEVANT_MEMORY`, and do not create a new relevance subsystem merely from FM-15.
