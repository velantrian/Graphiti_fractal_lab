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
| FM-16 v1 protocol | Does the signal generalize under held-out calibration + adversarial negatives? | Independent pre-scoring audit found methodological defects in gold semantics and success criteria. No scorer was run. | 🔴 REQUEST_CHANGES_BEFORE_SCORING / SUPERSEDED |
| FM-16 hardened protocol | Same scientific question, with corrected relevance labels, explicit hard-negative rejection gates, exact metric rules, and stricter model identity checks. | Not yet written/executed. | ⏳ NEXT / NOT_RUN |

**Current next action:** revise FM-16 before preregistration or scoring. Do not run the superseded protocol text.

---

## FM-13 — Search-path diagnosis

**Evidence:** `artifacts/memoryops/run_004/`

Observed on the frozen Q1–Q5 fixture:

- effective path was Graphiti edge hybrid BM25 + cosine → RRF;
- `cross_encoder_calls_total = 0`;
- Q4 `Who works on Project Zephyr?` had no gold-relevant facts but returned all four stored facts;
- MemoryOps was pass-through for the measured edge ordering/facts;
- artifact classification: `FIRST_DEGRADATION_LAYER = BM25_CANDIDATE_GENERATION`.

Interpretation ceiling:

> Broad BM25 candidate generation is not itself a defect; the observed failure is that later fusion/selection did not reject query-irrelevant candidates on this fixture.

The artifact labels Q5 as `MULTI_HOP`; this research ledger uses the stricter interpretation **CO_RETRIEVAL_ONLY / MULTI_HOP_REASONING_NOT_PROVEN**.

---

## FM-14 — Real embedding differential

**Evidence:** `artifacts/memoryops/run_005/`

One experimental variable changed from deterministic embeddings to a real local semantic embedder (`BAAI/bge-small-en-v1.5`). Extraction control passed.

Result:

- Q1–Q3 macro `Precision@1 = 1.0`, `Recall@3 = 1.0`, `MRR = 1.0`;
- lower-rank noise remained (`Precision@3 = 0.4444`, `Precision@4 = 0.3333`);
- Q4 Zephyr still returned four unrelated facts;
- artifact conclusion: `EMBEDDING_IMPROVEMENT_CONFIRMED BUT SEARCH_PIPELINE_FILTERING_STILL_INSUFFICIENT`;
- `NEO4J_CAUSAL_EVIDENCE = NO`.

```text
REAL EMBEDDINGS IMPROVED GEOMETRY
≠
REAL EMBEDDINGS SOLVED FINAL RELEVANCE FILTERING
```

The full FM-14 pairwise cosine matrix happened to be separable for the tiny fixture, so later CE work must not claim that embeddings had zero separability.

---

## FM-15 — Real Cross-Encoder separability

**Evidence:** `artifacts/memoryops/run_006/`

Recorded scorer:

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

FM-15 established a **useful pairwise query↔fact relevance signal on this frozen fixture**. It did not establish generalization or a production threshold.

Important non-claims:

- FM-14 embeddings were also mathematically separable on this tiny pair matrix;
- cosine and CE sigmoid scores are different scales;
- `NEW_SEPARABILITY_VS_EMBEDDINGS = NOT_ESTABLISHED`;
- `PAIRWISE_CE_SIGNAL = CONFIRMED_ON_FIXTURE`.

---

## 🔴 FM-16 v1 — Independent protocol audit before scoring

**Status:** `REQUEST_CHANGES_BEFORE_SCORING / SUPERSEDED_FOR_EXECUTION`.

The independent audit was read-only. It verified the then-live branch had advanced only by documentation commits, `run_006` artifacts remained intact, `run_007` did not exist, and FM-16 had not run.

### Critical finding 1 — relevance ≠ positive support

The superseded protocol incorrectly allowed examples where a direct negative answer was labelled as a hard negative merely because it negated a proposition.

Example:

```text
Q: Does X support Y?
F1: X supports Y.      → relevant answer: YES
F2: X does not support Y. → relevant answer: NO
```

Both can be relevant to the information need. A query↔fact relevance scorer should not be punished for recognizing a direct negative answer.

New invariant:

```text
RELEVANT_ANSWER
≠
SUPPORTS_POSITIVE_PROPOSITION
```

The same issue affects conditional and numeric yes/no examples. Gold relevance must be defined by whether the candidate directly answers or contributes an allowed answer to the query, while preserving polarity/scope/conditions/attribution.

### Critical finding 2 — `GENERALIZATION_STRONG` could pass with zero useful filtering

The old success criteria allowed a counterexample where:

- all answerable queries retain gold;
- all no-answer queries become EMPTY;
- no semantic inversion occurs;
- yet every answerable query still returns all 40 candidates;
- hard-negative rejection = 0%.

Therefore `GENERALIZATION_STRONG` must include an explicit preregistered **hard-negative rejection / returned-set quality** requirement, not only recall and no-answer EMPTY.

Also distinguish:

```text
ALL_NON_GOLD_REJECTION
≠
HARD_NEGATIVE_REJECTION
```

Easy unrelated negatives must not hide failure on adversarial near-misses.

### Additional mandatory hardening

Before scoring, the revised protocol must also define:

1. **No feasible calibration threshold:** `threshold = null`; thresholded test metrics = `NOT_APPLICABLE`; no fallback threshold.
2. **Model identity:** verify the actually loaded snapshot/weights/tokenizer/config/inference profile, not only a cached revision string.
3. **Exact metric definitions:** denominators, tie handling, threshold comparator (`>=` vs `>`), candidate threshold set, selected-set precision, and verdict precedence.
4. **Exact verdict table:** `BETTER`, `MIXED`, `NO_MATERIAL_GAIN`, `WORSE`, `GENERALIZATION_PARTIAL`, `FAILED`, and systematic inversion must be defined before scoring.
5. **Leakage-safe ordering:** preregistration → model fingerprint verification → calibration scoring → threshold freeze → test scoring/reporting → anchor regression.
6. **Claim ceiling:** 800 query×fact pairs are matrix entries, not 800 independent statistical observations. Success is bounded to the synthetic held-out design.
7. **Scorer failure semantics:** timeout/NaN/missing score ≠ successful EMPTY.

### Adversarial strata need semantic repair, not removal

Negation, temporal/version, scope, conditions, attribution, and numeric/unit contrasts remain useful. But labels must follow the query's information need.

Examples:

- historical fact may be irrelevant to a narrow “currently” query but relevant to a broad history query;
- conditional fact may directly answer “is it enabled by default?” with NO rather than being irrelevant;
- numeric opposite can answer a yes/no threshold question rather than being a retrieval negative;
- attributed uncertainty can be relevant context without proving the asserted event occurred.

This is an **evaluation-design correction**, not a new architecture component.

---

## 🧪 FM-16 hardened protocol — required shape

The scientific intent is retained:

- FM-15 anchor for regression only;
- calibration: 40 facts / 20 queries;
- held-out test: 40 different facts / 20 different queries;
- calibration and test entity-disjoint;
- 12 answerable + 8 no-answer per split;
- CE vs real embedding baseline;
- one global threshold per score family, calibrated only on calibration data;
- honest EMPTY with no forced refill;
- adversarial hard negatives;
- no runtime integration.

But execution is blocked until the protocol is rewritten with the audit fixes above.

The revised gold definition should be explicit, e.g.:

> `gold_relevant = candidate contains a direct answer or a preregistered admissible contribution to the answer for the query's information need, while preserving polarity, scope, temporal wording, conditions, attribution, and quantity semantics.`

Optional diagnostic labels may include support/refute/uncertain/scope mismatch/etc., but those must not silently replace the primary relevance definition.

---

## 🧩 Donor map — research context only

| Donor | Useful lesson | Boundary |
|---|---|---|
| 🗿 Titan | `selected/discarded + reason`, thresholded attention shape, typed no-signal precedent | Titan trust/confidence/risk/epistemic policy must not become Fractal relevance authority. |
| 💠 Crystal | preregistered hard-negative/no-recall-loss evaluation discipline; adversarial strata | Canon/evidence admission is not query relevance. |
| 🧬 Native Kernel | relevance/similarity/rank must not independently establish epistemic validity; UNKNOWN ≠ FALSE | invariant donor only. |
| 🦞 OpenClaw | broad candidate window, separate ranking signals, index identity; threshold-vs-recall tension | lexical fallback after failed strict score can defeat honest EMPTY; do not copy thresholds. |
| 🔬 SVL | applicability/UNKNOWN/fail-closed validation pattern | temporal applicability ≠ semantic query relevance. |
| EITI | empty-capable selectors and forced-top-k/fallback as a negative example | never refill rejected candidates merely to guarantee output count. |
| 🕸 Fractal experience applicability | `retrieved ≠ applicable`, per-candidate receipt, all-rejected output inside Fractal | tool/environment compatibility ≠ general semantic relevance. |

```text
DONOR_REFERENCE ≠ ADOPTED_RUNTIME
SIMILAR GATE SHAPE ≠ SHARED OWNER
```

## 🛡️ Research invariants

```text
RESEARCH ≠ RUNTIME
TESTED ≠ PRODUCTION AUTHORIZED
RETRIEVED ≠ RELEVANT
RELEVANT ≠ SUPPORTS_POSITIVE_PROPOSITION
RELEVANCE ≠ EVIDENCE
RELEVANCE ≠ TRUTH
EVIDENCE ≠ BELIEF
BELIEF ≠ TRUTH
MODEL/JUDGE SCORE ≠ AUTHORITY
NO_RELEVANT_RESULT ≠ FACT FALSE
NO_RELEVANT_RESULT ≠ ENTITY ABSENT
NOT RETRIEVED ≠ ABSENT
TEMPORAL APPLICABILITY ≠ SEMANTIC RELEVANCE
SCORER_FAILURE ≠ HONEST_EMPTY
```

## 📚 Evidence routing

```text
exact branch / exact commit
  > run-specific executable artifacts + pytest receipts
  > lab experiment code
  > RESEARCH_STATUS.md
  > this explanatory track
  > external/cross-project donor summaries
```

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
fm14:
  status: COMPLETED
fm15:
  status: COMPLETED
  pairwise_ce_signal: CONFIRMED_ON_FIXTURE
  new_separability_vs_embeddings: NOT_ESTABLISHED
fm16:
  status: PLANNED_NOT_RUN
  protocol_v1: REQUEST_CHANGES_BEFORE_SCORING_SUPERSEDED
  preregistration: NOT_CREATED
  run_007: NOT_CREATED
  scorer_run: false
  generalization: INCONCLUSIVE
  next: REVISE_PROTOCOL_BEFORE_PREREGISTRATION_AND_SCORING
runtime_gate: NOT_IMPLEMENTED
global_threshold: NOT_ESTABLISHED
```

## ⛔ Stop boundary

Do not execute the superseded FM-16 v1 protocol. Until a hardened preregistered version exists and is independently reviewable, do not run scoring, choose a runtime threshold, activate Cross-Encoder in Fractal search, implement `NO_RELEVANT_MEMORY`, or create a new relevance subsystem.
